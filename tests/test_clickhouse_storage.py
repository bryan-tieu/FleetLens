"""Live ClickHouse checks, enabled with FLEETLENS_CLICKHOUSE_TEST=1."""

import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from uuid import uuid4

import pytest

from fleetlens.cli import main as generate
from fleetlens.ingestion import read_snapshot
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
        ]
    finally:
        store._request(f"DROP DATABASE IF EXISTS {database} SYNC")
