"""Boundary cases that do not require a running ClickHouse service."""

import json
from dataclasses import replace

import pytest

from fleetlens.metrics.stored_v1 import cohort_summary, drive_summary
from fleetlens.simulation.generator import generate_fixture
from fleetlens.storage import ClickHouseStore, SnapshotRead, StorageConflict


def _stored_row(**changes):
    row = {
        "dataset_id": "fleetlens-synthetic",
        "snapshot_id": "fixture-v1",
        "vehicle_id": "fixture-brake",
        "drive_id": "fixture-brake-brake-drive",
        "source_sequence": "0",
        "event_time_utc": "2026-01-01 00:00:00.123456",
        "speed_mps": 12.0,
        "longitudinal_accel_mps2": 0.0,
        "origin": "synthetic",
        "source_ref": "fixture-brake-brake-drive/0",
        "source_schema_version": "synthetic-template/v1",
        "normalization_version": "identity-si/v1",
        "generation_config_id": "fixture-config/v1",
        "schema_version": "canonical-sample/v1",
        "content_versions": "1",
        "total_keys": "1",
        "conflicting_keys": "0",
        "snapshot_hash_first": "a" * 64,
        "snapshot_hash_last": "a" * 64,
        "load_records": "1",
        "load_hash_min": "a" * 64,
        "load_hash_max": "a" * 64,
        "input_min": "1",
        "input_max": "1",
        "accepted_min": "1",
        "accepted_max": "1",
        "rejected_min": "0",
        "rejected_max": "0",
    }
    return {**row, **changes}


def test_selector_and_bound_are_checked_before_sql(monkeypatch):
    store = ClickHouseStore()
    monkeypatch.setattr(store, "_request", lambda sql: pytest.fail("SQL was sent"))
    for dataset, snapshot in [
        ("fleetlens'; DROP TABLE raw_samples_v1;--", "fixture-v1"),
        ("fleetlens-synthetic", "fixture-v1' OR 1=1"),
        ("", "fixture-v1"),
    ]:
        with pytest.raises(ValueError, match="identifier"):
            store.read_snapshot(dataset, snapshot)
    for bound in (0, 10_001, True):
        with pytest.raises(ValueError, match="max_samples"):
            store.read_snapshot("fleetlens-synthetic", "fixture-v1", max_samples=bound)


def test_guard_rejects_conflict_or_oversize_before_reconstruction(monkeypatch):
    store = ClickHouseStore()
    for changes, error in [
        ({"conflicting_keys": "1", "content_versions": "2"}, StorageConflict),
        ({"snapshot_hash_last": "b" * 64}, StorageConflict),
        ({"total_keys": "2"}, ValueError),
    ]:
        monkeypatch.setattr(
            store,
            "_request",
            lambda sql, changes=changes: json.dumps(_stored_row(**changes)) + "\n",
        )
        with pytest.raises(error):
            store.read_snapshot("fleetlens-synthetic", "fixture-v1", max_samples=1)


def test_microsecond_utc_reconstruction_and_empty_summary(monkeypatch):
    store = ClickHouseStore()
    observed = []

    def respond(sql):
        observed.append(sql)
        return json.dumps(_stored_row()) + "\n"

    monkeypatch.setattr(store, "_request", respond)
    sample = store.read_snapshot("fleetlens-synthetic", "fixture-v1").samples[0]
    assert sample.event_time.isoformat() == "2026-01-01T00:00:00.123456+00:00"
    assert sample.provenance.source_ref == "fixture-brake-brake-drive/0"
    assert "WHERE dataset_id = 'fleetlens-synthetic'" in observed[0]
    assert "snapshot_id = 'fixture-v1'" in observed[0]
    assert "toTimeZone(any(event_time), 'UTC')" in observed[0]
    assert "snapshot_loads_v1" in observed[0]
    assert "OVER ()" in observed[0]

    monkeypatch.setattr(store, "_request", lambda sql: "")
    summary = cohort_summary(store, "fleetlens-synthetic", "fixture-v1")
    assert summary.status == "insufficient_data"
    assert summary.episodes_per_100_km is None
    with pytest.raises(LookupError, match="drive"):
        drive_summary(
            store,
            "fleetlens-synthetic",
            "fixture-v1",
            "fixture-brake",
            "fixture-brake-brake-drive",
        )


def test_cohort_zero_exposure_and_unsupported_source(monkeypatch):
    store = ClickHouseStore()
    samples = generate_fixture()[:2]
    stationary = tuple(replace(sample, speed_mps=0) for sample in samples)
    monkeypatch.setattr(
        store,
        "read_snapshot",
        lambda *args, **kwargs: SnapshotRead(stationary, "a" * 64, 2, 2, 0, True),
    )
    summary = cohort_summary(store, "fleetlens-synthetic", "fixture-v1")
    assert summary.status == "zero_exposure"
    assert summary.valid_seconds == 1
    assert summary.valid_distance_m == 0
    assert summary.episodes_per_100_km is None
    assert summary.zero_exposure_drive_count == 1

    wrong_version = replace(
        stationary[0],
        provenance=replace(
            stationary[0].provenance, normalization_version="unknown/v2"
        ),
    )
    monkeypatch.setattr(
        store,
        "read_snapshot",
        lambda *args, **kwargs: SnapshotRead((wrong_version,), "a" * 64, 1, 1, 0, True),
    )
    with pytest.raises(ValueError, match="M0 synthetic contracts"):
        cohort_summary(store, "fleetlens-synthetic", "fixture-v1")


def test_missing_load_accounting_marks_source_incomplete(monkeypatch):
    store = ClickHouseStore()
    monkeypatch.setattr(
        store,
        "_request",
        lambda sql: json.dumps(_stored_row(load_records="0")) + "\n",
    )
    read = store.read_snapshot("fleetlens-synthetic", "fixture-v1")
    assert read.source_complete is False
    assert read.source_input_rows is None
    cohort = cohort_summary(store, "fleetlens-synthetic", "fixture-v1")
    assert cohort.status == "incomplete_source"
    assert cohort.episodes_per_100_km is None
    assert cohort.drives[0].episodes_per_100_km is None
