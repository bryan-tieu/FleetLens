from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone

import pytest

from fleetlens.contracts import CanonicalSample, DataOrigin, Provenance


@pytest.fixture
def provenance():
    return Provenance(
        dataset_id="synthetic-demo",
        snapshot_id="fixture-v1",
        origin=DataOrigin.SYNTHETIC,
        source_ref="drive-7/record-0",
        source_schema_version="fixture/v1",
        normalization_version="identity-si/v1",
        generation_config_id="fixture-config/v1",
    )


@pytest.fixture
def sample(provenance):
    return CanonicalSample(
        vehicle_id="vehicle-7",
        drive_id="drive-7",
        source_sequence=0,
        event_time=datetime(2026, 9, 28, tzinfo=UTC),
        speed_mps=10.0,
        longitudinal_accel_mps2=-4.0,
        provenance=provenance,
    )


def test_canonical_values_are_preserved_without_rescaling(sample):
    assert sample.speed_mps == 10.0
    assert sample.longitudinal_accel_mps2 == -4.0
    assert sample.sample_key == (
        "synthetic-demo",
        "fixture-v1",
        "vehicle-7",
        "drive-7",
        0,
    )
    assert replace(sample, speed_mps=0.0).speed_mps == 0.0


@pytest.mark.parametrize("field", ["vehicle_id", "drive_id"])
@pytest.mark.parametrize("value", ["", " ", " padded", None, 7])
def test_invalid_identity_rejected(sample, field, value):
    with pytest.raises(ValueError, match=field):
        replace(sample, **{field: value})


@pytest.mark.parametrize("value", [-1, 0.5, True, "0", None])
def test_sequence_is_strict_nonnegative_integer(sample, value):
    with pytest.raises(ValueError, match="source_sequence"):
        replace(sample, source_sequence=value)


@pytest.mark.parametrize("field", ["speed_mps", "longitudinal_accel_mps2"])
@pytest.mark.parametrize(
    "value", [float("nan"), float("inf"), -float("inf"), True, "10", None]
)
def test_invalid_numbers_rejected(sample, field, value):
    with pytest.raises(ValueError, match=field):
        replace(sample, **{field: value})


def test_negative_speed_rejected(sample):
    with pytest.raises(ValueError, match="speed_mps"):
        replace(sample, speed_mps=-0.1)


@pytest.mark.parametrize(
    "value",
    [
        datetime(2026, 9, 28),
        datetime(2026, 9, 28, tzinfo=timezone(timedelta(hours=-7))),
        "2026-09-28T00:00:00Z",
        None,
    ],
)
def test_time_requires_explicit_utc(sample, value):
    with pytest.raises(ValueError, match="event_time"):
        replace(sample, event_time=value)


@pytest.mark.parametrize(
    "field",
    [
        "dataset_id",
        "snapshot_id",
        "source_ref",
        "source_schema_version",
        "normalization_version",
    ],
)
@pytest.mark.parametrize("value", ["", None, " padded "])
def test_lineage_required(provenance, field, value):
    with pytest.raises(ValueError, match=field):
        replace(provenance, **{field: value})


@pytest.mark.parametrize("value", [None, "", " "])
def test_synthetic_requires_generation_config(provenance, value):
    with pytest.raises(ValueError, match="generation_config_id"):
        replace(provenance, generation_config_id=value)


def test_real_origin_has_no_synthetic_config(provenance, sample):
    real = replace(provenance, origin=DataOrigin.REAL, generation_config_id=None)
    assert replace(sample, provenance=real).provenance.origin is DataOrigin.REAL
    with pytest.raises(ValueError, match="real data"):
        replace(provenance, origin=DataOrigin.REAL)


@pytest.mark.parametrize("value", ["synthetic", "unknown", None])
def test_origin_requires_explicit_enum(provenance, value):
    with pytest.raises(ValueError, match="origin"):
        replace(provenance, origin=value)


def test_schema_and_provenance_types_are_checked(sample):
    with pytest.raises(ValueError, match="schema_version"):
        replace(sample, schema_version="v2")
    with pytest.raises(ValueError, match="provenance"):
        replace(sample, provenance={})


def test_identity_survives_decode_correction_but_scopes_snapshots(sample):
    corrected = replace(
        sample,
        speed_mps=12.0,
        provenance=replace(sample.provenance, normalization_version="fixed/v2"),
    )
    assert corrected.sample_key == sample.sample_key
    other_snapshot = replace(
        sample, provenance=replace(sample.provenance, snapshot_id="fixture-v2")
    )
    assert other_snapshot.sample_key != sample.sample_key
    assert replace(sample, source_sequence=1).sample_key != sample.sample_key


def test_sample_and_lineage_are_immutable(sample):
    with pytest.raises(FrozenInstanceError):
        sample.speed_mps = 12.0
    with pytest.raises(FrozenInstanceError):
        sample.provenance.snapshot_id = "changed"


def test_unit_mistakes_require_source_adapter_evidence(sample):
    # 36 km/h is 10 m/s; a mislabeled 36 is still a valid number.
    # The canonical contract cannot discover an upstream unit mistake.
    assert replace(sample, speed_mps=36.0).speed_mps == 36.0
