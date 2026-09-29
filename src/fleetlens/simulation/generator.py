"""Version 1 synthetic scenarios in canonical SI units.

Assignment hashes seed and vehicle identity, rather than advancing a shared
random stream. Templates are illustrative and make no fleet-realism claim.
"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from json import dumps
from math import isfinite

from fleetlens.contracts import CanonicalSample, DataOrigin, Provenance

SCENARIOS = ("steady", "brake", "gap")
START = datetime(2026, 1, 1, tzinfo=UTC)
# (seconds since drive start, speed m/s, longitudinal acceleration m/s²)
TEMPLATES: dict[str, tuple[tuple[int, float, float], ...]] = {
    "steady": ((0, 10, 0), (1, 10, 0), (2, 10, 0), (3, 10, 0), (4, 10, 0), (5, 10, 0)),
    "brake": ((0, 12, 0), (1, 12, -4), (2, 8, -4), (3, 4, 0), (4, 4, 0), (5, 4, 0)),
    "gap": ((0, 10, 0), (1, 10, 0), (2, 10, 0), (5, 10, 0), (6, 10, 0)),
}


@dataclass(frozen=True, slots=True)
class GenerationConfig:
    seed: int = 20260929
    weights: tuple[float, float, float] = (0.5, 0.3, 0.2)

    def __post_init__(self) -> None:
        if type(self.seed) is not int or self.seed < 0:
            raise ValueError("seed must be a nonnegative integer")
        if not isinstance(self.weights, tuple) or len(self.weights) != len(SCENARIOS):
            raise ValueError("weights must contain steady, brake, gap probabilities")
        if (
            any(
                type(weight) not in (int, float) or not isfinite(weight) or weight < 0
                for weight in self.weights
            )
            or abs(sum(self.weights) - 1.0) > 1e-12
        ):
            raise ValueError(
                "weights must be finite nonnegative probabilities summing to 1"
            )

    @property
    def config_id(self) -> str:
        weights = ",".join(format(w, ".17g") for w in self.weights)
        payload = f"fleet-generator/v1|{self.seed}|{weights}"
        return f"fleet-generator/v1/{sha256(payload.encode()).hexdigest()[:16]}"


def assign_scenario(vehicle_id: str, config: GenerationConfig) -> str:
    if (
        not isinstance(vehicle_id, str)
        or not vehicle_id
        or vehicle_id != vehicle_id.strip()
    ):
        raise ValueError(
            "vehicle_id must be a nonempty string without outer whitespace"
        )
    if not isinstance(config, GenerationConfig):
        raise ValueError("config must be GenerationConfig")
    digest = sha256(f"{config.seed}:{vehicle_id}".encode()).digest()
    draw = int.from_bytes(digest[:8], "big") / 2**64
    cumulative = 0.0
    for scenario, weight in zip(SCENARIOS, config.weights, strict=True):
        cumulative += weight
        if draw < cumulative:
            return scenario
    return SCENARIOS[-1]  # Only possible at floating-point rounding boundary.


def _drive(
    vehicle_id: str, scenario: str, snapshot_id: str, config_id: str
) -> tuple[CanonicalSample, ...]:
    drive_id = f"{vehicle_id}-{scenario}-drive"
    return tuple(
        CanonicalSample(
            vehicle_id=vehicle_id,
            drive_id=drive_id,
            source_sequence=sequence,
            event_time=START + timedelta(seconds=second),
            speed_mps=speed,
            longitudinal_accel_mps2=accel,
            provenance=Provenance(
                dataset_id="fleetlens-synthetic",
                snapshot_id=snapshot_id,
                origin=DataOrigin.SYNTHETIC,
                source_ref=f"{drive_id}/{sequence}",
                source_schema_version="synthetic-template/v1",
                normalization_version="identity-si/v1",
                generation_config_id=config_id,
            ),
        )
        for sequence, (second, speed, accel) in enumerate(TEMPLATES[scenario])
    )


def generate_fleet(
    vehicle_ids: list[str], config: GenerationConfig
) -> tuple[CanonicalSample, ...]:
    if not vehicle_ids or len(set(vehicle_ids)) != len(vehicle_ids):
        raise ValueError("vehicle_ids must be nonempty and unique")
    if any(not isinstance(v, str) or not v or v != v.strip() for v in vehicle_ids):
        raise ValueError(
            "vehicle_ids must be nonempty strings without outer whitespace"
        )
    if not isinstance(config, GenerationConfig):
        raise ValueError("config must be GenerationConfig")
    # Sorted input yields identical serialized records regardless of caller order.
    snapshot_payload = dumps([sorted(vehicle_ids), config.config_id])
    snapshot = f"fleet-v1-{sha256(snapshot_payload.encode()).hexdigest()[:16]}"
    return tuple(
        sample
        for vehicle_id in sorted(vehicle_ids)
        for sample in _drive(
            vehicle_id, assign_scenario(vehicle_id, config), snapshot, config.config_id
        )
    )


def generate_fixture() -> tuple[CanonicalSample, ...]:
    """Two fixed drives; expected events/exposure live outside this module."""
    return _drive("fixture-brake", "brake", "fixture-v1", "fixture-config/v1") + _drive(
        "fixture-gap", "gap", "fixture-v1", "fixture-config/v1"
    )
