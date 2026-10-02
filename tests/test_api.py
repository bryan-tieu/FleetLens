"""HTTP contract checks without binding a port or requiring ClickHouse."""

import json
from dataclasses import replace
from urllib.parse import urlencode

from fleetlens.api import MetricApp
from fleetlens.simulation.generator import generate_fixture
from fleetlens.storage import SnapshotLimitExceeded, SnapshotRead, StorageConflict


class FakeStore:
    def __init__(self, read: SnapshotRead | Exception):
        self.read = read
        self.calls = 0

    def read_snapshot(self, dataset_id, snapshot_id, *, max_samples):
        self.calls += 1
        if isinstance(self.read, Exception):
            raise self.read
        assert (dataset_id, snapshot_id) == ("fleetlens-synthetic", "fixture-v1")
        assert max_samples <= 10_000
        return self.read


def _complete_read():
    return SnapshotRead(generate_fixture(), "a" * 64, 11, 11, 0, True)


def _request(app, path, **query):
    statuses = []

    def respond(status, headers):
        statuses.append((status, dict(headers)))

    payload = b"".join(
        app(
            {
                "REQUEST_METHOD": "GET",
                "PATH_INFO": path,
                "QUERY_STRING": urlencode(query),
            },
            respond,
        )
    )
    assert statuses[0][1]["Content-Type"].startswith("application/json")
    return statuses[0][0], json.loads(payload)


def test_cohort_drive_and_event_are_bounded_and_traceable():
    store = FakeStore(_complete_read())
    app = MetricApp(store)
    base = {"dataset_id": "fleetlens-synthetic", "snapshot_id": "fixture-v1"}
    status, cohort = _request(app, "/api/v1/cohort", **base)
    assert status == "200 OK"
    assert (cohort["sample_count"], cohort["episode_count"]) == (11, 1)
    assert cohort["source_complete"] is True
    assert cohort["valid_distance_m"] == 66
    assert cohort["episodes_per_100_km"] == 100_000 / 66
    assert len(cohort["drives"]) == 2
    assert [
        (v["vehicle_id"], v["episode_count"], v["valid_distance_m"])
        for v in cohort["vehicles"]
    ] == [
        ("fixture-brake", 1, 36),
        ("fixture-gap", 0, 30),
    ]
    assert "valid_intervals" not in cohort["drives"][0]

    drive_params = {
        **base,
        "vehicle_id": "fixture-brake",
        "drive_id": "fixture-brake-brake-drive",
    }
    status, drive = _request(app, "/api/v1/drive", **drive_params)
    assert status == "200 OK"
    assert drive["events"][0]["start_time"] == "2026-01-01T00:00:01Z"
    assert len(drive["exposure"]["valid_intervals"]) == 5

    status, detail = _request(app, "/api/v1/event", **drive_params, start_sequence="1")
    assert status == "200 OK"
    assert [key[-1] for key in detail["event"]["source_sample_keys"]] == [1, 2, 3]
    assert detail["event"]["definition_version"] == "hard-braking/v1"
    assert store.calls == 3


def test_incomplete_source_and_conflict_never_publish_a_rate():
    partial = replace(_complete_read(), source_rejected_rows=1, source_complete=False)
    base = {"dataset_id": "fleetlens-synthetic", "snapshot_id": "fixture-v1"}
    status, cohort = _request(MetricApp(FakeStore(partial)), "/api/v1/cohort", **base)
    assert status == "200 OK"
    assert cohort["status"] == "incomplete_source"
    assert cohort["episodes_per_100_km"] is None
    assert cohort["source_rejected_rows"] == 1

    status, body = _request(
        MetricApp(FakeStore(StorageConflict("do not leak row content"))),
        "/api/v1/cohort",
        **base,
    )
    assert status == "409 Conflict"
    assert body == {"error": "snapshot_conflict"}


def test_invalid_parameters_and_missing_event_are_explicit():
    store = FakeStore(_complete_read())
    app = MetricApp(store)
    base = {"dataset_id": "fleetlens-synthetic", "snapshot_id": "fixture-v1"}
    for query in (
        {**base, "max_samples": "10001"},
        {**base, "unknown": "x"},
        {**base, "dataset_id": "bad'"},
        {**base, "snapshot_id": "bad snapshot"},
        {"dataset_id": "fleetlens-synthetic"},
    ):
        status, _ = _request(app, "/api/v1/cohort", **query)
        assert status == "400 Bad Request"
    assert store.calls == 0

    status, _ = _request(
        app,
        "/api/v1/event",
        **base,
        vehicle_id="fixture-brake",
        drive_id="fixture-brake-brake-drive",
        start_sequence="99",
    )
    assert status == "404 Not Found"


def test_stored_contract_error_is_not_a_client_error():
    read = _complete_read()
    sample = read.samples[0]
    wrong = replace(
        sample,
        provenance=replace(sample.provenance, normalization_version="unknown/v2"),
    )
    read = replace(read, samples=(wrong, *read.samples[1:]))
    status, body = _request(
        MetricApp(FakeStore(read)),
        "/api/v1/cohort",
        dataset_id="fleetlens-synthetic",
        snapshot_id="fixture-v1",
    )
    assert status == "422 Unprocessable Content"
    assert body == {"error": "snapshot_invalid"}


def test_nonfinite_rate_is_never_serialized_as_json_infinity():
    read = _complete_read()
    tiny = tuple(replace(sample, speed_mps=1e-310) for sample in read.samples)
    status, body = _request(
        MetricApp(FakeStore(replace(read, samples=tiny))),
        "/api/v1/cohort",
        dataset_id="fleetlens-synthetic",
        snapshot_id="fixture-v1",
    )
    assert status == "422 Unprocessable Content"
    assert body == {"error": "snapshot_invalid"}


def test_valid_snapshot_exceeding_caller_bound_has_distinct_error():
    base = {"dataset_id": "fleetlens-synthetic", "snapshot_id": "fixture-v1"}
    status, body = _request(
        MetricApp(FakeStore(_complete_read())),
        "/api/v1/cohort",
        **base,
        max_drives="1",
    )
    assert status == "400 Bad Request"
    assert body == {"error": "snapshot_exceeds_limit"}

    status, body = _request(
        MetricApp(FakeStore(SnapshotLimitExceeded("snapshot exceeds max_samples"))),
        "/api/v1/cohort",
        **base,
    )
    assert status == "400 Bad Request"
    assert body == {"error": "snapshot_exceeds_limit"}
