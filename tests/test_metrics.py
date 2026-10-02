import json
from dataclasses import replace
from datetime import timedelta
from pathlib import Path

import pytest

from fleetlens.metrics import MetricStatus, evaluate_drives
from fleetlens.simulation.generator import generate_fixture

ORACLE = json.loads(
    (Path(__file__).parent / "fixtures" / "tiny_expected.json").read_text()
)


def test_frozen_fixture_episode_exposure_and_lineage():
    samples = generate_fixture()
    results = evaluate_drives(samples)
    assert len(results) == 2
    assert results == evaluate_drives(list(reversed(samples)))
    by_drive = {result.drive_key[-1]: result for result in results}
    assert sum(len(item.events) for item in results) == ORACLE["total_event_episodes"]
    assert (
        sum(item.exposure.valid_seconds for item in results)
        == ORACLE["total_valid_exposure_seconds"]
    )
    assert (
        sum(item.exposure.valid_distance_m for item in results)
        == ORACLE["total_valid_distance_m"]
    )
    for drive_id, expected in ORACLE["drives"].items():
        result = by_drive[drive_id]
        start = min(
            sample.event_time for sample in samples if sample.drive_id == drive_id
        )
        assert [
            [
                (event.start_time - start).total_seconds(),
                (event.end_time - start).total_seconds(),
            ]
            for event in result.events
        ] == expected["event_windows_seconds"]
        assert result.exposure.valid_seconds == expected["valid_exposure_seconds"]
        assert result.exposure.valid_distance_m == expected["valid_distance_m"]
        assert result.status is MetricStatus.OK
    brake = by_drive["fixture-brake-brake-drive"]
    gap = by_drive["fixture-gap-gap-drive"]
    assert [key[-1] for key in brake.events[0].source_sample_keys] == [1, 2, 3]
    assert all(
        key[:2] == ("fleetlens-synthetic", "fixture-v1")
        for key in brake.events[0].source_sample_keys
    )
    assert brake.events[0].definition_version == "hard-braking/v1"
    assert brake.episodes_per_100_km == pytest.approx(100_000 / 36)
    assert gap.exposure.excluded_gap_count == 1
    assert [
        tuple(key[-1] for key in interval.source_sample_keys)
        for interval in gap.exposure.valid_intervals
    ] == [(0, 1), (1, 2), (3, 4)]
    assert gap.episodes_per_100_km == 0


def test_single_sample_and_all_gap_drive_are_insufficient():
    samples = generate_fixture()
    single = evaluate_drives([samples[0]])[0]
    assert single.status is MetricStatus.INSUFFICIENT_DATA
    assert single.episodes_per_100_km is None
    gap_only = evaluate_drives([samples[6], samples[9]])[0]
    assert gap_only.exposure.valid_seconds == 0
    assert gap_only.exposure.excluded_gap_count == 1
    assert gap_only.status is MetricStatus.INSUFFICIENT_DATA


def test_stationary_valid_interval_has_undefined_rate():
    first, second = generate_fixture()[:2]
    results = evaluate_drives(
        [replace(first, speed_mps=0), replace(second, speed_mps=0)]
    )
    result = results[0]
    assert result.exposure.valid_seconds == 1
    assert result.exposure.valid_distance_m == 0
    assert result.status is MetricStatus.ZERO_EXPOSURE
    assert result.episodes_per_100_km is None


def test_gap_breaks_braking_episode_and_minimum_duration_is_inclusive():
    samples = generate_fixture()[:4]
    assert len(evaluate_drives(list(samples))[0].events) == 1
    shifted = [*samples]
    shifted[2] = replace(
        shifted[2], event_time=shifted[2].event_time + timedelta(seconds=2)
    )
    shifted[3] = replace(
        shifted[3], event_time=shifted[3].event_time + timedelta(seconds=2)
    )
    result = evaluate_drives(shifted)[0]
    assert result.events == ()
    assert result.exposure.excluded_gap_count == 1


def test_threshold_is_inclusive_but_one_second_is_too_short():
    samples = generate_fixture()[:3]
    threshold_samples = [
        replace(samples[0], longitudinal_accel_mps2=-3),
        replace(samples[1], longitudinal_accel_mps2=-3),
        samples[2],
    ]
    assert len(evaluate_drives(threshold_samples)[0].events) == 1
    assert evaluate_drives(threshold_samples[:2])[0].events == ()


def test_duplicate_key_and_conflicting_time_order_fail():
    samples = generate_fixture()
    with pytest.raises(ValueError, match="duplicate sample key"):
        evaluate_drives([samples[0], samples[0]])
    with pytest.raises(ValueError, match="event times and source sequences"):
        evaluate_drives(
            [samples[0], replace(samples[1], event_time=samples[0].event_time)]
        )
    with pytest.raises(ValueError, match="event times and source sequences"):
        evaluate_drives(
            [samples[1], replace(samples[2], event_time=samples[0].event_time)]
        )
