"""Live ClickHouse checks, enabled with FLEETLENS_CLICKHOUSE_TEST=1."""

import json
import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import timedelta
from hashlib import sha256
from uuid import uuid4

import pytest

from fleetlens.cli import main as generate
from fleetlens.ingestion import read_snapshot
from fleetlens.metrics import cohort_summary, drive_summary
from fleetlens.storage import ClickHouseStore, StorageConflict

pytestmark = pytest.mark.skipif(
    os.environ.get("FLEETLENS_CLICKHOUSE_TEST") != "1",
    reason="requires the local ClickHouse compose service",
)


def test_replay_concurrency_and_conflict_are_visible(tmp_path):
    source = tmp_path / "fixture"
    generate(["--output", str(source), "--fixture"])
    result = read_snapshot(source)
    precise = replace(
        result.samples[0],
        event_time=result.samples[0].event_time.replace(microsecond=123456),
    )
    result = replace(result, samples=(precise, *result.samples[1:]))
    database = f"fleetlens_test_{uuid4().hex}"
    store = ClickHouseStore(database=database)
    try:
        store.migrate()
        first = store.load(result)
        second = store.load(result)
        assert (first.physical_rows, first.logical_rows) == (11, 11)
        assert (second.physical_rows, second.logical_rows) == (22, 11)
        stored_time = store._request(
            f"SELECT event_time FROM {database}.raw_samples_v1 "
            "WHERE source_sequence = 0 LIMIT 1"
        ).strip()
        assert stored_time.endswith(".123456")
        assert (
            store.read_snapshot("fleetlens-synthetic", "fixture-v1")
            .samples[0]
            .event_time
            == precise.event_time
        )

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(store.load, result) for _ in range(2)]
            for future in futures:
                assert future.result().logical_rows == 11
        assert store.raw_row_count() == 44
        assert store.logical_count() == 11

        changed = replace(result.samples[0], speed_mps=result.samples[0].speed_mps + 1)
        conflicting_result = replace(
            result,
            samples=(changed,),
            input_rows=1,
        )
        with pytest.raises(StorageConflict, match="1 source keys"):
            store.load(conflicting_result)
        assert store.conflict_key_count() == 1
        assert (
            int(
                store._request(
                    f"SELECT count() FROM {database}.logical_samples_v1"
                ).strip()
            )
            == 10
        )
        with pytest.raises(StorageConflict):
            store.logical_count()
    finally:
        store._request(f"DROP DATABASE IF EXISTS {database} SYNC")


def test_stored_fixture_metric_replay_conflict_and_bounds(tmp_path):
    source = tmp_path / "fixture"
    generate(["--output", str(source), "--fixture"])
    result = read_snapshot(source)
    database = f"fleetlens_test_{uuid4().hex}"
    store = ClickHouseStore(database=database)
    try:
        store.load(result)
        first = cohort_summary(store, "fleetlens-synthetic", "fixture-v1")
        assert (first.sample_count, first.drive_count, first.episode_count) == (
            11,
            2,
            1,
        )
        assert (first.valid_seconds, first.valid_distance_m) == (8, 66)
        assert first.episodes_per_100_km == pytest.approx(100_000 / 66)
        brake = drive_summary(
            store,
            "fleetlens-synthetic",
            "fixture-v1",
            "fixture-brake",
            "fixture-brake-brake-drive",
        )
        assert [(e.start_time.second, e.end_time.second) for e in brake.events] == [
            (1, 3)
        ]
        assert [key[-1] for key in brake.events[0].source_sample_keys] == [1, 2, 3]
        store.load(result)
        assert store.raw_row_count() == 22
        assert cohort_summary(store, "fleetlens-synthetic", "fixture-v1") == first
        with pytest.raises(ValueError, match="max_samples"):
            cohort_summary(store, "fleetlens-synthetic", "fixture-v1", max_samples=10)
        with pytest.raises(ValueError, match="max_drives"):
            cohort_summary(store, "fleetlens-synthetic", "fixture-v1", max_drives=1)
        assert (
            cohort_summary(store, "fleetlens-synthetic", "absent-v1").status
            == "insufficient_data"
        )

        changed = replace(result.samples[-1], speed_mps=11)
        conflict = replace(result, samples=(changed,), input_rows=1)
        with pytest.raises(StorageConflict):
            store.load(conflict)
        with pytest.raises(StorageConflict):
            cohort_summary(store, "fleetlens-synthetic", "fixture-v1")
        with pytest.raises(StorageConflict):
            drive_summary(
                store,
                "fleetlens-synthetic",
                "fixture-v1",
                "fixture-brake",
                "fixture-brake-brake-drive",
                max_samples=1,
            )
    finally:
        store._request(f"DROP DATABASE IF EXISTS {database} SYNC")


def test_disjoint_keys_with_two_source_hashes_block_metrics(tmp_path):
    source = tmp_path / "fixture"
    generate(["--output", str(source), "--fixture"])
    result = read_snapshot(source)
    database = f"fleetlens_test_{uuid4().hex}"
    store = ClickHouseStore(database=database)
    try:
        store.load(result)
        last = result.samples[-1]
        extra = replace(
            last,
            source_sequence=last.source_sequence + 1,
            event_time=last.event_time + timedelta(seconds=1),
            provenance=replace(
                last.provenance,
                source_ref=f"{last.drive_id}/{last.source_sequence + 1}",
            ),
        )
        second = replace(
            result,
            samples=(extra,),
            input_rows=1,
            snapshot_hash="b" * 64,
        )
        store.load(second)
        assert store.logical_count() == 12  # No same-key payload conflict.
        with pytest.raises(StorageConflict, match="multiple source file hashes"):
            cohort_summary(store, "fleetlens-synthetic", "fixture-v1")
        with pytest.raises(StorageConflict):
            drive_summary(
                store,
                "fleetlens-synthetic",
                "fixture-v1",
                "fixture-brake",
                "fixture-brake-brake-drive",
            )
    finally:
        store._request(f"DROP DATABASE IF EXISTS {database} SYNC")


def test_quarantined_source_has_no_reported_rate(tmp_path):
    source = tmp_path / "fixture"
    generate(["--output", str(source), "--fixture"])
    lines = (source / "samples.jsonl").read_text().splitlines()
    bad = json.loads(lines[0])
    bad["speed_mps"] = -1
    lines[0] = json.dumps(bad, sort_keys=True)
    payload = ("\n".join(lines) + "\n").encode()
    (source / "samples.jsonl").write_bytes(payload)
    manifest = json.loads((source / "manifest.json").read_text())
    manifest["sha256_samples_jsonl"] = sha256(payload).hexdigest()
    (source / "manifest.json").write_text(json.dumps(manifest))
    result = read_snapshot(source)
    assert (len(result.samples), len(result.rejected)) == (10, 1)
    database = f"fleetlens_test_{uuid4().hex}"
    store = ClickHouseStore(database=database)
    try:
        store.load(result)
        cohort = cohort_summary(store, "fleetlens-synthetic", "fixture-v1")
        assert (
            cohort.source_input_rows,
            cohort.source_accepted_rows,
            cohort.source_rejected_rows,
        ) == (11, 10, 1)
        assert cohort.source_complete is False
        assert cohort.status == "incomplete_source"
        assert cohort.episodes_per_100_km is None
        assert all(drive.episodes_per_100_km is None for drive in cohort.drives)
    finally:
        store._request(f"DROP DATABASE IF EXISTS {database} SYNC")


def test_missing_load_receipt_keeps_stored_rate_undefined(tmp_path):
    source = tmp_path / "fixture"
    generate(["--output", str(source), "--fixture"])
    result = read_snapshot(source)
    database = f"fleetlens_test_{uuid4().hex}"
    store = ClickHouseStore(database=database)
    try:
        store.load(result)
        store._request(f"TRUNCATE TABLE {database}.snapshot_loads_v1")
        cohort = cohort_summary(store, "fleetlens-synthetic", "fixture-v1")
        assert cohort.sample_count == 11
        assert cohort.source_complete is False
        assert cohort.status == "incomplete_source"
        assert cohort.episodes_per_100_km is None
    finally:
        store._request(f"DROP DATABASE IF EXISTS {database} SYNC")


def test_concurrent_first_load_records_each_migration_once(tmp_path):
    source = tmp_path / "fixture"
    generate(["--output", str(source), "--fixture"])
    result = read_snapshot(source)
    database = f"fleetlens_test_{uuid4().hex}"
    store = ClickHouseStore(database=database)
    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(store.load, result) for _ in range(2)]
            assert [future.result().conflicting_keys for future in futures] == [0, 0]
        assert store.raw_row_count() == 22
        assert store.logical_count() == 11
        versions = store._request(
            f"SELECT version, count() FROM {database}.schema_migrations "
            "GROUP BY version ORDER BY version FORMAT TabSeparated"
        ).splitlines()
        assert versions == [
            "001_raw_samples.sql\t1",
            "002_logical_samples.sql\t1",
            "003_event_time_microseconds.sql\t1",
            "004_snapshot_loads.sql\t1",
        ]
    finally:
        store._request(f"DROP DATABASE IF EXISTS {database} SYNC")
