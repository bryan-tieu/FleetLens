"""Bounded stored-snapshot summaries using the pure hard-braking/v1 reference."""

from dataclasses import dataclass, replace

from fleetlens.contracts import CanonicalSample, DataOrigin
from fleetlens.metrics.hard_braking_v1 import (
    DEFINITION,
    DriveMetric,
    MetricStatus,
    evaluate_drives,
)
from fleetlens.storage import ClickHouseStore, SnapshotLimitExceeded


@dataclass(frozen=True, slots=True)
class CohortSummary:
    dataset_id: str
    snapshot_id: str
    snapshot_hash: str | None
    definition_version: str
    source_input_rows: int | None
    source_accepted_rows: int | None
    source_rejected_rows: int | None
    source_complete: bool
    sample_count: int
    drive_count: int
    episode_count: int
    valid_seconds: float
    valid_distance_m: float
    excluded_gap_count: int
    insufficient_drive_count: int
    zero_exposure_drive_count: int
    status: MetricStatus
    episodes_per_100_km: float | None
    drives: tuple[DriveMetric, ...]
    vehicles: tuple["VehicleSummary", ...]


@dataclass(frozen=True, slots=True)
class VehicleSummary:
    vehicle_id: str
    drive_count: int
    episode_count: int
    valid_distance_m: float
    status: MetricStatus
    episodes_per_100_km: float | None


def _vehicle_summaries(drives: tuple[DriveMetric, ...]) -> tuple[VehicleSummary, ...]:
    """Stratify on an explicit source field; sum exposure before division."""
    grouped: dict[str, list[DriveMetric]] = {}
    for drive in drives:
        grouped.setdefault(drive.drive_key[2], []).append(drive)
    summaries = []
    for vehicle_id, group in sorted(grouped.items()):
        distance = sum(d.exposure.valid_distance_m for d in group)
        seconds = sum(d.exposure.valid_seconds for d in group)
        events = sum(len(d.events) for d in group)
        if any(d.status is MetricStatus.INCOMPLETE_SOURCE for d in group):
            status = MetricStatus.INCOMPLETE_SOURCE
        elif seconds == 0:
            status = MetricStatus.INSUFFICIENT_DATA
        elif distance == 0:
            status = MetricStatus.ZERO_EXPOSURE
        else:
            status = MetricStatus.OK
        summaries.append(
            VehicleSummary(
                vehicle_id,
                len(group),
                events,
                distance,
                status,
                (
                    events * DEFINITION.rate_distance_m / distance
                    if status is MetricStatus.OK
                    else None
                ),
            )
        )
    return tuple(summaries)


def _check_source_versions(samples: tuple[CanonicalSample, ...]) -> None:
    if any(
        sample.provenance.origin is not DataOrigin.SYNTHETIC
        or sample.provenance.source_schema_version != "synthetic-template/v1"
        or sample.provenance.normalization_version != "identity-si/v1"
        or sample.schema_version != "canonical-sample/v1"
        for sample in samples
    ):
        raise ValueError(
            "hard-braking/v1 stored metric supports M0 synthetic contracts"
        )


def cohort_summary(
    store: ClickHouseStore,
    dataset_id: str,
    snapshot_id: str,
    *,
    max_samples: int = 1000,
    max_drives: int = 100,
) -> CohortSummary:
    """Summarize one bounded snapshot; sum counts and metres before division."""
    if type(max_drives) is not int or not 1 <= max_drives <= 1000:
        raise ValueError("max_drives must be an integer from 1 to 1000")
    read = store.read_snapshot(dataset_id, snapshot_id, max_samples=max_samples)
    samples = read.samples
    _check_source_versions(samples)
    pure_drives = evaluate_drives(samples)
    drives = (
        pure_drives
        if read.source_complete or not samples
        else tuple(
            replace(
                drive,
                status=MetricStatus.INCOMPLETE_SOURCE,
                episodes_per_100_km=None,
            )
            for drive in pure_drives
        )
    )
    if len(drives) > max_drives:
        raise SnapshotLimitExceeded("snapshot exceeds max_drives")
    events = sum(len(drive.events) for drive in drives)
    seconds = sum(drive.exposure.valid_seconds for drive in drives)
    distance = sum(drive.exposure.valid_distance_m for drive in drives)
    if samples and not read.source_complete:
        status = MetricStatus.INCOMPLETE_SOURCE
        rate = None
    elif seconds == 0:
        status = MetricStatus.INSUFFICIENT_DATA
        rate = None
    elif distance == 0:
        status = MetricStatus.ZERO_EXPOSURE
        rate = None
    else:
        status = MetricStatus.OK
        rate = events * DEFINITION.rate_distance_m / distance
    return CohortSummary(
        dataset_id=dataset_id,
        snapshot_id=snapshot_id,
        snapshot_hash=read.snapshot_hash,
        definition_version=DEFINITION.version,
        source_input_rows=read.source_input_rows,
        source_accepted_rows=read.source_accepted_rows,
        source_rejected_rows=read.source_rejected_rows,
        source_complete=read.source_complete,
        sample_count=len(samples),
        drive_count=len(drives),
        episode_count=events,
        valid_seconds=seconds,
        valid_distance_m=distance,
        excluded_gap_count=sum(d.exposure.excluded_gap_count for d in drives),
        insufficient_drive_count=sum(
            d.status is MetricStatus.INSUFFICIENT_DATA for d in pure_drives
        ),
        zero_exposure_drive_count=sum(
            d.status is MetricStatus.ZERO_EXPOSURE for d in pure_drives
        ),
        status=status,
        episodes_per_100_km=rate,
        drives=drives,
        vehicles=_vehicle_summaries(drives),
    )


def drive_summary(
    store: ClickHouseStore,
    dataset_id: str,
    snapshot_id: str,
    vehicle_id: str,
    drive_id: str,
    *,
    max_samples: int = 1000,
) -> DriveMetric:
    """Return one drive only after guarding the entire bounded snapshot."""
    if not isinstance(vehicle_id, str) or not vehicle_id:
        raise ValueError("vehicle_id must be nonempty")
    if not isinstance(drive_id, str) or not drive_id:
        raise ValueError("drive_id must be nonempty")
    cohort = cohort_summary(
        store, dataset_id, snapshot_id, max_samples=max_samples, max_drives=1000
    )
    selected = [
        drive
        for drive in cohort.drives
        if drive.drive_key[2:] == (vehicle_id, drive_id)
    ]
    if not selected:
        raise LookupError("drive is absent from the selected snapshot")
    return selected[0]
