"""Small local ClickHouse boundary for already validated M0 snapshots.

Raw rows are append-only evidence. Logical reads group by source identity;
conflicting payloads are reported rather than arbitrarily chosen.
"""

import json
import os
import re
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from hashlib import sha256
from importlib.resources import files
from pathlib import Path
from time import monotonic, sleep
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fleetlens.contracts import CanonicalSample, DataOrigin, Provenance
from fleetlens.ingestion import IngestResult


class StorageConflict(ValueError):
    """At least one source key has multiple distinct canonical payloads."""


class SnapshotLimitExceeded(ValueError):
    """A valid selected snapshot exceeds the caller's declared read bound."""


_SELECTOR = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}\Z")


def validate_snapshot_selector(value: str) -> str:
    if not isinstance(value, str) or not _SELECTOR.fullmatch(value):
        raise ValueError(
            "dataset and snapshot identifiers must use safe ASCII characters"
        )
    return value


def _safe_hash(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
        raise ValueError("snapshot_hash must be a SHA-256 hex digest")
    return value


def _canonical_row(row: dict, dataset_id: str, snapshot_id: str) -> CanonicalSample:
    """Rebuild one logical row after the query-wide conflict and size guards."""
    try:
        if row["dataset_id"] != dataset_id or row["snapshot_id"] != snapshot_id:
            raise ValueError("stored row escaped snapshot scope")
        event_time = datetime.fromisoformat(row["event_time_utc"]).replace(tzinfo=UTC)
        provenance = Provenance(
            dataset_id=row["dataset_id"],
            snapshot_id=row["snapshot_id"],
            origin=DataOrigin(row["origin"]),
            source_ref=row["source_ref"],
            source_schema_version=row["source_schema_version"],
            normalization_version=row["normalization_version"],
            generation_config_id=row["generation_config_id"] or None,
        )
        return CanonicalSample(
            vehicle_id=row["vehicle_id"],
            drive_id=row["drive_id"],
            source_sequence=int(row["source_sequence"]),
            event_time=event_time,
            speed_mps=row["speed_mps"],
            longitudinal_accel_mps2=row["longitudinal_accel_mps2"],
            provenance=provenance,
            schema_version=row["schema_version"],
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("stored row violates canonical sample contract") from exc


@contextmanager
def _local_migration_lock(url: str, database: str) -> Iterator[None]:
    """Serialize first-run schema changes for local loaders on one host."""

    name = sha256(f"{url}|{database}".encode()).hexdigest()[:16]
    path = Path(tempfile.gettempdir()) / f"fleetlens-migrate-{name}.lock"
    deadline = monotonic() + 15
    while True:
        try:
            descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            os.close(descriptor)
            break
        except FileExistsError:
            if monotonic() >= deadline:
                raise RuntimeError(
                    f"migration lock timed out; inspect stale local lock {path}"
                ) from None
            sleep(0.1)
    try:
        yield
    finally:
        path.unlink()


@dataclass(frozen=True, slots=True)
class LoadSummary:
    input_rows: int
    accepted_rows: int
    quarantined_rows: int
    physical_rows: int
    logical_rows: int
    conflicting_keys: int


@dataclass(frozen=True, slots=True)
class SnapshotRead:
    samples: tuple[CanonicalSample, ...]
    snapshot_hash: str | None
    source_input_rows: int | None
    source_accepted_rows: int | None
    source_rejected_rows: int | None
    source_complete: bool


def _row(sample: CanonicalSample, snapshot_hash: str) -> dict:
    source = sample.provenance
    canonical = asdict(sample)
    canonical["event_time"] = sample.event_time.isoformat().replace("+00:00", "Z")
    canonical["provenance"]["origin"] = source.origin.value
    content_hash = sha256(
        json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        "dataset_id": source.dataset_id,
        "snapshot_id": source.snapshot_id,
        "vehicle_id": sample.vehicle_id,
        "drive_id": sample.drive_id,
        "source_sequence": sample.source_sequence,
        "event_time": sample.event_time.strftime("%Y-%m-%d %H:%M:%S.%f"),
        "speed_mps": sample.speed_mps,
        "longitudinal_accel_mps2": sample.longitudinal_accel_mps2,
        "origin": source.origin.value,
        "source_ref": source.source_ref,
        "source_schema_version": source.source_schema_version,
        "normalization_version": source.normalization_version,
        "generation_config_id": source.generation_config_id,
        "schema_version": sample.schema_version,
        "content_sha256": content_hash,
        "snapshot_sha256": snapshot_hash,
    }


class ClickHouseStore:
    def __init__(
        self,
        url: str = "http://127.0.0.1:18123/",
        user: str = "fleetlens",
        password: str = "local-development-only",
        database: str = "fleetlens",
    ) -> None:
        if not re.fullmatch(r"[a-z][a-z0-9_]*", database):
            raise ValueError("database must be a simple lowercase SQL identifier")
        self.url = url
        self.user = user
        self.password = password
        self.database = database

    def _request(self, sql: str) -> str:
        request = Request(
            self.url,
            data=sql.encode("utf-8"),
            headers={
                "X-ClickHouse-User": self.user,
                "X-ClickHouse-Key": self.password,
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=30) as response:
                return response.read().decode("utf-8")
        except HTTPError as exc:
            raise RuntimeError(
                f"ClickHouse rejected the request (HTTP {exc.code})"
            ) from exc
        except URLError as exc:
            raise RuntimeError("ClickHouse is unreachable") from exc

    def migrate(self) -> None:
        with _local_migration_lock(self.url, self.database):
            self._migrate_locked()

    def _migrate_locked(self) -> None:
        self._request(f"CREATE DATABASE IF NOT EXISTS {self.database}")
        self._request(
            f"CREATE TABLE IF NOT EXISTS {self.database}.schema_migrations "
            "(version String, applied_at DateTime64(3) DEFAULT now64(3)) "
            "ENGINE = MergeTree ORDER BY version"
        )
        applied = set(
            self._request(
                f"SELECT version FROM {self.database}.schema_migrations "
                "FORMAT TabSeparated"
            ).splitlines()
        )
        migrations = files("fleetlens.storage").joinpath("migrations")
        for migration in sorted(migrations.iterdir(), key=lambda path: path.name):
            if migration.name.endswith(".sql") and migration.name not in applied:
                if not re.fullmatch(r"[0-9]{3}_[a-z0-9_]+\.sql", migration.name):
                    raise ValueError("invalid migration filename")
                sql = migration.read_text(encoding="utf-8").replace(
                    "{database}", self.database
                )
                for statement in sql.split(";"):
                    if statement.strip():
                        self._request(statement)
                self._request(
                    f"INSERT INTO {self.database}.schema_migrations (version) "
                    f"VALUES ('{migration.name}')"
                )

    def raw_row_count(self) -> int:
        """Physical load rows, including identical replay copies."""

        return int(
            self._request(f"SELECT count() FROM {self.database}.raw_samples_v1").strip()
        )

    def conflict_key_count(self) -> int:
        """Diagnostic count of keys with distinct canonical payloads."""

        return int(
            self._request(
                f"SELECT count() FROM {self.database}.sample_conflicts_v1"
            ).strip()
        )

    def logical_count(self) -> int:
        """Return the stable sample count only when no source key conflicts."""

        state = self._request(
            "SELECT countIf(content_versions = 1), "
            "countIf(content_versions > 1) FROM ("
            "SELECT uniqExact(content_sha256) AS content_versions "
            f"FROM {self.database}.raw_samples_v1 "
            "GROUP BY dataset_id, snapshot_id, vehicle_id, drive_id, "
            "source_sequence) FORMAT TabSeparated"
        ).strip()
        logical, conflicts = (int(value) for value in state.split("\t"))
        if conflicts:
            raise StorageConflict(
                f"{conflicts} source keys have conflicting payloads; "
                "stop downstream reads and inspect sample_conflicts_v1"
            )
        return logical

    def read_snapshot(
        self, dataset_id: str, snapshot_id: str, *, max_samples: int = 1000
    ) -> SnapshotRead:
        """Read one bounded snapshot with conflict and source-accounting guards.

        The window totals and rows come from one ClickHouse statement. Even a
        conflict beyond the returned row limit prevents metrics from escaping.
        An absent or partial load is returned with source_complete=False.
        """
        dataset_id = validate_snapshot_selector(dataset_id)
        snapshot_id = validate_snapshot_selector(snapshot_id)
        if type(max_samples) is not int or not 1 <= max_samples <= 10_000:
            raise ValueError("max_samples must be an integer from 1 to 10000")
        sql = (
            "SELECT g.*, m.*, count() OVER () AS total_keys, "
            "sum(toUInt64(content_versions > 1)) OVER () AS conflicting_keys, "
            "min(g.snapshot_hash_min) OVER () AS snapshot_hash_first, "
            "max(g.snapshot_hash_max) OVER () AS snapshot_hash_last "
            "FROM (SELECT dataset_id, snapshot_id, vehicle_id, drive_id, "
            "source_sequence, "
            "toString(toTimeZone(any(event_time), 'UTC')) AS event_time_utc, "
            "any(speed_mps) AS speed_mps, "
            "any(longitudinal_accel_mps2) AS longitudinal_accel_mps2, "
            "any(origin) AS origin, any(source_ref) AS source_ref, "
            "any(source_schema_version) AS source_schema_version, "
            "any(normalization_version) AS normalization_version, "
            "any(generation_config_id) AS generation_config_id, "
            "any(schema_version) AS schema_version, "
            "uniqExact(content_sha256) AS content_versions, "
            "min(snapshot_sha256) AS snapshot_hash_min, "
            "max(snapshot_sha256) AS snapshot_hash_max "
            f"FROM {self.database}.raw_samples_v1 "
            f"WHERE dataset_id = '{dataset_id}' AND snapshot_id = '{snapshot_id}' "
            "GROUP BY dataset_id, snapshot_id, vehicle_id, drive_id, "
            "source_sequence) AS g CROSS JOIN "
            "(SELECT count() AS load_records, "
            "min(snapshot_sha256) AS load_hash_min, "
            "max(snapshot_sha256) AS load_hash_max, "
            "min(input_rows) AS input_min, max(input_rows) AS input_max, "
            "min(accepted_rows) AS accepted_min, "
            "max(accepted_rows) AS accepted_max, "
            "min(rejected_rows) AS rejected_min, "
            "max(rejected_rows) AS rejected_max "
            f"FROM {self.database}.snapshot_loads_v1 "
            f"WHERE dataset_id = '{dataset_id}' "
            f"AND snapshot_id = '{snapshot_id}') AS m "
            "ORDER BY vehicle_id, drive_id, source_sequence "
            f"LIMIT {max_samples + 1} FORMAT JSONEachRow"
        )
        rows = [json.loads(line) for line in self._request(sql).splitlines()]
        if not rows:
            return SnapshotRead((), None, None, None, None, False)
        if int(rows[0]["conflicting_keys"]):
            raise StorageConflict("snapshot has conflicting source payloads")
        first = rows[0]
        snapshot_hash = first["snapshot_hash_first"]
        if snapshot_hash != first["snapshot_hash_last"]:
            raise StorageConflict("snapshot ID has multiple source file hashes")
        load_records = int(first["load_records"])
        if load_records and (
            first["load_hash_min"] != snapshot_hash
            or first["load_hash_max"] != snapshot_hash
        ):
            raise StorageConflict("snapshot load accounting has conflicting hashes")
        if int(rows[0]["total_keys"]) > max_samples:
            raise SnapshotLimitExceeded("snapshot exceeds max_samples")
        counts_agree = load_records > 0 and all(
            first[low] == first[high]
            for low, high in (
                ("input_min", "input_max"),
                ("accepted_min", "accepted_max"),
                ("rejected_min", "rejected_max"),
            )
        )
        input_rows = int(first["input_min"]) if counts_agree else None
        accepted_rows = int(first["accepted_min"]) if counts_agree else None
        rejected_rows = int(first["rejected_min"]) if counts_agree else None
        complete = (
            counts_agree
            and accepted_rows == int(first["total_keys"])
            and input_rows == accepted_rows + rejected_rows
            and rejected_rows == 0
        )
        return SnapshotRead(
            samples=tuple(_canonical_row(row, dataset_id, snapshot_id) for row in rows),
            snapshot_hash=snapshot_hash,
            source_input_rows=input_rows,
            source_accepted_rows=accepted_rows,
            source_rejected_rows=rejected_rows,
            source_complete=complete,
        )

    def load(self, result: IngestResult) -> LoadSummary:
        self.migrate()
        if result.samples:
            snapshot_hash = _safe_hash(result.snapshot_hash)
            identities = {
                (sample.provenance.dataset_id, sample.provenance.snapshot_id)
                for sample in result.samples
            }
            if len(identities) != 1:
                raise ValueError("one load must contain one dataset snapshot")
            dataset_id, snapshot_id = next(iter(identities))
            dataset_id = validate_snapshot_selector(dataset_id)
            snapshot_id = validate_snapshot_selector(snapshot_id)
            payload = "".join(
                json.dumps(_row(sample, snapshot_hash), sort_keys=True) + "\n"
                for sample in result.samples
            )
            self._request(
                f"INSERT INTO {self.database}.raw_samples_v1 FORMAT JSONEachRow\n"
                + payload
            )
            self._request(
                f"INSERT INTO {self.database}.snapshot_loads_v1 "
                "(dataset_id, snapshot_id, snapshot_sha256, input_rows, "
                "accepted_rows, rejected_rows) VALUES "
                f"('{dataset_id}', '{snapshot_id}', "
                f"'{snapshot_hash}', {result.input_rows}, "
                f"{len(result.samples)}, {len(result.rejected)})"
            )
        summary = LoadSummary(
            input_rows=result.input_rows,
            accepted_rows=len(result.samples),
            quarantined_rows=len(result.rejected),
            physical_rows=self.raw_row_count(),
            logical_rows=self.logical_count(),
            conflicting_keys=0,
        )
        return summary
