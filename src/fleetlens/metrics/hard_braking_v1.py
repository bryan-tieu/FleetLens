"""hard-braking/v1: adjacent-sample episodes and independent valid exposure.

The acceleration at a sample applies until the next sample. Intervals longer
than one second are ineligible for both episodes and exposure. This definition
is for canonical SI samples and makes no claim about real-fleet ascertainment.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from fleetlens.contracts import CanonicalSample

SampleKey = tuple[str, str, str, str, int]
DriveKey = tuple[str, str, str, str]


@dataclass(frozen=True, slots=True)
class MetricDefinition:
    version: str
    threshold_mps2: float
    minimum_episode_seconds: float
    maximum_interval_seconds: float
    rate_distance_m: float


DEFINITION = MetricDefinition(
    version="hard-braking/v1",
    threshold_mps2=-3.0,
    minimum_episode_seconds=2.0,
    maximum_interval_seconds=1.0,
    rate_distance_m=100_000.0,  # episodes per 100 km
)


class MetricStatus(StrEnum):
    OK = "ok"
    INSUFFICIENT_DATA = "insufficient_data"
    ZERO_EXPOSURE = "zero_exposure"
    INCOMPLETE_SOURCE = "incomplete_source"


@dataclass(frozen=True, slots=True)
class Episode:
    drive_key: DriveKey
    definition_version: str
    start_time: datetime
    end_time: datetime
    source_sample_keys: tuple[SampleKey, ...]


@dataclass(frozen=True, slots=True)
class ValidInterval:
    start_time: datetime
    end_time: datetime
    distance_m: float
    source_sample_keys: tuple[SampleKey, SampleKey]


@dataclass(frozen=True, slots=True)
class Exposure:
    definition_version: str
    valid_seconds: float
    valid_distance_m: float
    valid_intervals: tuple[ValidInterval, ...]
    excluded_gap_count: int


@dataclass(frozen=True, slots=True)
class DriveMetric:
    drive_key: DriveKey
    definition_version: str
    sample_count: int
    events: tuple[Episode, ...]
    exposure: Exposure
    status: MetricStatus
    episodes_per_100_km: float | None


def _drive_key(sample: CanonicalSample) -> DriveKey:
    return (
        sample.provenance.dataset_id,
        sample.provenance.snapshot_id,
        sample.vehicle_id,
        sample.drive_id,
    )


def _evaluate_drive(
    key: DriveKey, samples: list[CanonicalSample], definition: MetricDefinition
) -> DriveMetric:
    ordered = sorted(samples, key=lambda item: (item.event_time, item.source_sequence))
    if any(
        later.event_time <= earlier.event_time
        or later.source_sequence <= earlier.source_sequence
        for earlier, later in zip(ordered[:-1], ordered[1:], strict=True)
    ):
        raise ValueError("drive event times and source sequences must increase")

    intervals: list[ValidInterval] = []
    events: list[Episode] = []
    episode_keys: list[SampleKey] = []
    episode_start: datetime | None = None
    episode_end: datetime | None = None
    excluded_gaps = 0

    def finish_episode() -> None:
        nonlocal episode_start, episode_end, episode_keys
        if (
            episode_start is not None
            and episode_end is not None
            and (episode_end - episode_start).total_seconds()
            >= definition.minimum_episode_seconds
        ):
            events.append(
                Episode(
                    key,
                    definition.version,
                    episode_start,
                    episode_end,
                    tuple(episode_keys),
                )
            )
        episode_start = None
        episode_end = None
        episode_keys = []

    for earlier, later in zip(ordered[:-1], ordered[1:], strict=True):
        seconds = (later.event_time - earlier.event_time).total_seconds()
        if seconds > definition.maximum_interval_seconds:
            excluded_gaps += 1
            finish_episode()
            continue
        distance = (earlier.speed_mps + later.speed_mps) * seconds / 2
        intervals.append(
            ValidInterval(
                earlier.event_time,
                later.event_time,
                distance,
                (earlier.sample_key, later.sample_key),
            )
        )
        if earlier.longitudinal_accel_mps2 <= definition.threshold_mps2:
            if episode_start is None:
                episode_start = earlier.event_time
                episode_keys = [earlier.sample_key]
            episode_end = later.event_time
            episode_keys.append(later.sample_key)
        else:
            finish_episode()
    finish_episode()

    valid_seconds = sum(
        (interval.end_time - interval.start_time).total_seconds()
        for interval in intervals
    )
    valid_distance_m = sum(interval.distance_m for interval in intervals)
    exposure = Exposure(
        definition.version,
        valid_seconds,
        valid_distance_m,
        tuple(intervals),
        excluded_gaps,
    )
    if not intervals:
        status = MetricStatus.INSUFFICIENT_DATA
        rate = None
    elif valid_distance_m == 0:
        status = MetricStatus.ZERO_EXPOSURE
        rate = None
    else:
        status = MetricStatus.OK
        rate = len(events) * definition.rate_distance_m / valid_distance_m
    return DriveMetric(
        key, definition.version, len(ordered), tuple(events), exposure, status, rate
    )


def evaluate_drives(
    samples: tuple[CanonicalSample, ...] | list[CanonicalSample],
) -> tuple[DriveMetric, ...]:
    """Return one deterministic result per drive; reject duplicate source keys.

    A zero-distance drive has an undefined rate. A drive without eligible
    intervals has insufficient data, even if it contains multiple samples.
    """
    grouped: dict[DriveKey, list[CanonicalSample]] = {}
    seen: set[SampleKey] = set()
    for sample in samples:
        if not isinstance(sample, CanonicalSample):
            raise TypeError("samples must be CanonicalSample objects")
        if sample.sample_key in seen:
            raise ValueError("duplicate sample key")
        seen.add(sample.sample_key)
        grouped.setdefault(_drive_key(sample), []).append(sample)
    return tuple(
        _evaluate_drive(key, grouped[key], DEFINITION) for key in sorted(grouped)
    )
