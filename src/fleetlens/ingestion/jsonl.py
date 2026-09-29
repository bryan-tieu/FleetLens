"""Read the M0 synthetic JSONL contract and account for every input line.

The manifest checks the bytes and snapshot metadata. A bad manifest or
hash aborts the whole snapshot; a bad record is quarantined by line number.
No raw record is retained in rejection diagnostics.
"""

import json
from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from typing import Any

from fleetlens.contracts import CanonicalSample, DataOrigin, Provenance

_SAMPLE_FIELDS = {
    "vehicle_id",
    "drive_id",
    "source_sequence",
    "event_time",
    "speed_mps",
    "longitudinal_accel_mps2",
    "provenance",
    "schema_version",
}
_PROVENANCE_FIELDS = {
    "dataset_id",
    "snapshot_id",
    "origin",
    "source_ref",
    "source_schema_version",
    "normalization_version",
    "generation_config_id",
}
_MANIFEST_FIELDS = {
    "dataset_id",
    "snapshot_id",
    "origin",
    "source_schema_version",
    "normalization_version",
    "generation_config_id",
    "generation_parameters",
    "sample_count",
    "sha256_samples_jsonl",
}
_SAFE_REASONS = {
    "duplicate JSON field",
    "sample must have exactly the v1 fields",
    "provenance must have exactly the v1 fields",
    "event_time must be an ISO UTC Z string",
    "event_time must be a valid ISO UTC timestamp",
    "duplicate sample_key in snapshot",
    "vehicle_id must be a nonempty string without outer whitespace",
    "drive_id must be a nonempty string without outer whitespace",
    "source_sequence must be a nonnegative integer",
    "event_time must be a timezone-aware UTC datetime",
    "speed_mps must be a finite number, not a boolean or string",
    "speed_mps must be a finite number",
    "speed_mps must be nonnegative",
    "longitudinal_accel_mps2 must be a finite number, not a boolean or string",
    "longitudinal_accel_mps2 must be a finite number",
    "provenance must be a validated Provenance",
    "unsupported schema_version",
    "dataset_id must be a nonempty string without outer whitespace",
    "snapshot_id must be a nonempty string without outer whitespace",
    "source_ref must be a nonempty string without outer whitespace",
    "source_schema_version must be a nonempty string without outer whitespace",
    "normalization_version must be a nonempty string without outer whitespace",
    "generation_config_id must be a nonempty string without outer whitespace",
}
_SAFE_REASONS.update(
    f"provenance {field} differs from manifest"
    for field in (
        "dataset_id",
        "snapshot_id",
        "origin",
        "source_schema_version",
        "normalization_version",
        "generation_config_id",
    )
)


@dataclass(frozen=True, slots=True)
class RejectedRow:
    line_number: int
    reason: str


@dataclass(frozen=True, slots=True)
class IngestResult:
    samples: tuple[CanonicalSample, ...]
    rejected: tuple[RejectedRow, ...]
    input_rows: int
    snapshot_hash: str

    def __post_init__(self) -> None:
        if self.input_rows != len(self.samples) + len(self.rejected):
            raise ValueError("input accounting does not reconcile")


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    obj: dict[str, Any] = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError("duplicate JSON field")
        obj[key] = value
    return obj


def _json(raw: str) -> Any:
    return json.loads(raw, object_pairs_hook=_unique_object)


def _fields(value: Any, expected: set[str], name: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != expected:
        raise ValueError(f"{name} must have exactly the v1 fields")
    return value


def _manifest(path: Path, payload: bytes) -> dict[str, Any]:
    try:
        manifest = _fields(
            _json(path.read_text(encoding="utf-8")), _MANIFEST_FIELDS, "manifest"
        )
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("invalid manifest JSON") from exc
    for field in (
        "dataset_id",
        "snapshot_id",
        "source_schema_version",
        "normalization_version",
        "generation_config_id",
    ):
        if not isinstance(manifest[field], str) or not manifest[field]:
            raise ValueError(f"invalid manifest {field}")
    if manifest["origin"] != "synthetic":
        raise ValueError("only synthetic M0 snapshots are supported")
    if manifest["source_schema_version"] != "synthetic-template/v1":
        raise ValueError("unsupported source_schema_version")
    if manifest["normalization_version"] != "identity-si/v1":
        raise ValueError("unsupported normalization_version")
    if not isinstance(manifest["generation_parameters"], dict):
        raise ValueError("invalid manifest generation_parameters")
    if type(manifest["sample_count"]) is not int or manifest["sample_count"] < 0:
        raise ValueError("invalid manifest sample_count")
    digest = sha256(payload).hexdigest()
    if manifest["sha256_samples_jsonl"] != digest:
        raise ValueError("samples hash does not match manifest")
    return manifest


def _sample(raw: bytes, manifest: dict[str, Any]) -> CanonicalSample:
    try:
        record = _fields(_json(raw.decode("utf-8")), _SAMPLE_FIELDS, "sample")
        source = _fields(record["provenance"], _PROVENANCE_FIELDS, "provenance")
        for field in (
            "dataset_id",
            "snapshot_id",
            "origin",
            "source_schema_version",
            "normalization_version",
            "generation_config_id",
        ):
            if source[field] != manifest[field]:
                raise ValueError(f"provenance {field} differs from manifest")
        event_time = record["event_time"]
        if not isinstance(event_time, str) or not event_time.endswith("Z"):
            raise ValueError("event_time must be an ISO UTC Z string")
        try:
            parsed_time = datetime.fromisoformat(event_time)
        except ValueError as exc:
            raise ValueError("event_time must be a valid ISO UTC timestamp") from exc
        provenance = Provenance(**{**source, "origin": DataOrigin(source["origin"])})
        return CanonicalSample(
            **{
                **record,
                "event_time": parsed_time,
                "provenance": provenance,
            }
        )
    except (UnicodeError, json.JSONDecodeError, TypeError, OverflowError) as exc:
        raise ValueError(
            f"invalid sample encoding or value: {type(exc).__name__}"
        ) from exc


def read_snapshot(directory: Path) -> IngestResult:
    """Validate one immutable M0 snapshot; first valid source key wins in a file.

    Re-reading the same snapshot gives the same result. Persisted replay across
    loads is intentionally a storage-layer contract, not claimed here.
    """

    payload = (directory / "samples.jsonl").read_bytes()
    manifest = _manifest(directory / "manifest.json", payload)
    lines = payload.splitlines()
    if len(lines) != manifest["sample_count"]:
        raise ValueError("sample_count does not match input line count")
    accepted: list[CanonicalSample] = []
    rejected: list[RejectedRow] = []
    seen: set[tuple[str, str, str, str, int]] = set()
    for number, raw in enumerate(lines, start=1):
        try:
            sample = _sample(raw, manifest)
            if sample.sample_key in seen:
                raise ValueError("duplicate sample_key in snapshot")
            seen.add(sample.sample_key)
            accepted.append(sample)
        except ValueError as exc:
            reason = str(exc)
            rejected.append(
                RejectedRow(
                    number, reason if reason in _SAFE_REASONS else "invalid sample"
                )
            )
    return IngestResult(
        tuple(accepted), tuple(rejected), len(lines), sha256(payload).hexdigest()
    )
