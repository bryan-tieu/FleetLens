"""Version 1 canonical samples; source adapters own decoding into these units.

One sample is one observation from a dataset snapshot, vehicle and drive.
Speed is nonnegative ground-speed magnitude in m/s. Longitudinal acceleration
is in m/s^2, positive forward and negative during forward-motion braking.
No inference of events, physical realism, ordering or completeness occurs here.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from math import isfinite


class DataOrigin(StrEnum):
    SYNTHETIC = "synthetic"
    REAL = "real"


def _text(name: str, value: str) -> None:
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError(f"{name} must be a nonempty string without outer whitespace")


def _finite(name: str, value: float) -> None:
    if type(value) not in (int, float):
        raise ValueError(f"{name} must be a finite number, not a boolean or string")
    try:
        finite = isfinite(value)
    except OverflowError:
        finite = False
    if not finite:
        raise ValueError(f"{name} must be a finite number")


@dataclass(frozen=True, slots=True)
class Provenance:
    """Source history; identifiers refer to versioned external manifests.

    source_ref is an opaque record pointer, not raw media or a secret URL.
    Synthetic records require a generation configuration identifier. Real
    records must not carry one. The referenced manifests are not loaded here.
    """

    dataset_id: str
    snapshot_id: str
    origin: DataOrigin
    source_ref: str
    source_schema_version: str
    normalization_version: str
    generation_config_id: str | None = None

    def __post_init__(self) -> None:
        for name in (
            "dataset_id",
            "snapshot_id",
            "source_ref",
            "source_schema_version",
            "normalization_version",
        ):
            _text(name, getattr(self, name))
        if not isinstance(self.origin, DataOrigin):
            raise ValueError("origin must be a DataOrigin enum")
        if self.origin is DataOrigin.SYNTHETIC:
            _text("generation_config_id", self.generation_config_id)
        elif self.generation_config_id is not None:
            raise ValueError("real data must not have generation_config_id")


@dataclass(frozen=True, slots=True)
class CanonicalSample:
    """Validated, immutable in-memory values, already in canonical units.

    event_time must be timezone-aware UTC. source_sequence is a stable,
    nonnegative integer assigned by the source within a drive, not load order.
    sample_key excludes values and normalization version: correcting a decode
    does not create another source observation. Storage revision/replay policy
    will be defined at ingestion; this class does not deduplicate.
    """

    vehicle_id: str
    drive_id: str
    source_sequence: int
    event_time: datetime
    speed_mps: float
    longitudinal_accel_mps2: float
    provenance: Provenance
    schema_version: str = "canonical-sample/v1"

    def __post_init__(self) -> None:
        _text("vehicle_id", self.vehicle_id)
        _text("drive_id", self.drive_id)
        if type(self.source_sequence) is not int or self.source_sequence < 0:
            raise ValueError("source_sequence must be a nonnegative integer")
        if not isinstance(
            self.event_time, datetime
        ) or self.event_time.utcoffset() != timedelta(0):
            raise ValueError("event_time must be a timezone-aware UTC datetime")
        _finite("speed_mps", self.speed_mps)
        if self.speed_mps < 0:
            raise ValueError("speed_mps must be nonnegative")
        _finite("longitudinal_accel_mps2", self.longitudinal_accel_mps2)
        if not isinstance(self.provenance, Provenance):
            raise ValueError("provenance must be a validated Provenance")
        if self.schema_version != "canonical-sample/v1":
            raise ValueError("unsupported schema_version")

    @property
    def sample_key(self) -> tuple[str, str, str, str, int]:
        """Logical source identity; tuple components avoid delimiter collisions."""
        return (
            self.provenance.dataset_id,
            self.provenance.snapshot_id,
            self.vehicle_id,
            self.drive_id,
            self.source_sequence,
        )
