import json
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path

import pytest

from fleetlens.cli import main
from fleetlens.simulation import (
    GenerationConfig,
    assign_scenario,
    generate_fixture,
    generate_fleet,
)


def test_assignment_stays_stable_as_fleet_grows_or_order_changes():
    config = GenerationConfig(seed=42)
    small_ids = ["vehicle-7", "vehicle-2"]
    small = generate_fleet(small_ids, config)
    large = generate_fleet(["vehicle-9", *reversed(small_ids)], config)
    assert small == generate_fleet(list(reversed(small_ids)), config)
    for vehicle in small_ids:
        assert [
            s.longitudinal_accel_mps2 for s in small if s.vehicle_id == vehicle
        ] == [s.longitudinal_accel_mps2 for s in large if s.vehicle_id == vehicle]
        assert [s.event_time for s in small if s.vehicle_id == vehicle] == [
            s.event_time for s in large if s.vehicle_id == vehicle
        ]


def test_weight_boundaries_and_invalid_distributions():
    assert assign_scenario("v", GenerationConfig(weights=(1, 0, 0))) == "steady"
    assert assign_scenario("v", GenerationConfig(weights=(0, 1, 0))) == "brake"
    assert assign_scenario("v", GenerationConfig(weights=(0, 0, 1))) == "gap"
    for weights in [
        (0.5, 0.5),
        (-0.1, 0.5, 0.6),
        (0.2, 0.2, 0.2),
        (float("nan"), 0, 1),
        (True, 0, 0),
    ]:
        with pytest.raises(ValueError, match="weights"):
            GenerationConfig(weights=weights)
    with pytest.raises(ValueError, match="seed"):
        GenerationConfig(seed=-1)
    with pytest.raises(ValueError, match="unique"):
        generate_fleet(["v", "v"], GenerationConfig())


def test_fixture_matches_independent_oracle():
    expected = json.loads(
        (Path(__file__).parent / "fixtures" / "tiny_expected.json").read_text()
    )
    samples = generate_fixture()
    assert len(samples) == 11
    assert {s.provenance.snapshot_id for s in samples} == {expected["snapshot_id"]}
    assert len({s.sample_key for s in samples}) == len(samples)
    brake = [s for s in samples if s.drive_id == "fixture-brake-brake-drive"]
    gap = [s for s in samples if s.drive_id == "fixture-gap-gap-drive"]
    assert [s.source_sequence for s in brake] == expected["drives"][brake[0].drive_id][
        "source_sequences"
    ]
    assert [s.source_sequence for s in gap] == expected["drives"][gap[0].drive_id][
        "source_sequences"
    ]
    origin = datetime(2026, 1, 1, tzinfo=UTC)
    assert [(s.event_time - origin).total_seconds() for s in brake] == [
        0,
        1,
        2,
        3,
        4,
        5,
    ]
    assert [s.longitudinal_accel_mps2 for s in brake] == [0, -4, -4, 0, 0, 0]
    assert [s.speed_mps for s in brake] == [12, 12, 8, 4, 4, 4]
    assert [(s.event_time - origin).total_seconds() for s in gap] == [0, 1, 2, 5, 6]
    assert expected["drives"][brake[0].drive_id]["event_windows_seconds"] == [[1, 3]]
    assert (
        expected["drives"][brake[0].drive_id]["valid_distance_m"] == 12 + 10 + 6 + 4 + 4
    )
    assert expected["drives"][gap[0].drive_id]["valid_distance_m"] == 10 + 10 + 10
    assert expected["total_valid_distance_m"] == 66


def test_cli_repeated_output_is_byte_identical_and_has_hash(tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    assert main(["--output", str(first), "--vehicles", "9", "--seed", "12"]) == 0
    assert main(["--output", str(second), "--vehicles", "9", "--seed", "12"]) == 0
    assert (first / "samples.jsonl").read_bytes() == (
        second / "samples.jsonl"
    ).read_bytes()
    assert (first / "manifest.json").read_bytes() == (
        second / "manifest.json"
    ).read_bytes()
    rows = [
        json.loads(line) for line in (first / "samples.jsonl").read_text().splitlines()
    ]
    manifest = json.loads((first / "manifest.json").read_text())
    assert len(rows) == manifest["sample_count"]
    assert (
        manifest["sha256_samples_jsonl"]
        == sha256((first / "samples.jsonl").read_bytes()).hexdigest()
    )
    assert rows[0]["provenance"]["origin"] == "synthetic"
    assert rows[0]["event_time"].endswith("Z")


def test_cli_fixture_is_reproducible(tmp_path):
    assert main(["--output", str(tmp_path), "--fixture"]) == 0
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    assert manifest["snapshot_id"] == "fixture-v1"
    assert manifest["sample_count"] == 11
