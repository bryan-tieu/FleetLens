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
from hashlib import sha256
from importlib.resources import files
from pathlib import Path
from time import monotonic, sleep
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fleetlens.contracts import CanonicalSample
from fleetlens.ingestion import IngestResult


class StorageConflict(ValueError):
    """At least one source key has multiple distinct canonical payloads."""


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

    def load(self, result: IngestResult) -> LoadSummary:
        self.migrate()
        if result.samples:
            payload = "".join(
                json.dumps(_row(sample, result.snapshot_hash), sort_keys=True) + "\n"
                for sample in result.samples
            )
            self._request(
                f"INSERT INTO {self.database}.raw_samples_v1 FORMAT JSONEachRow\n"
                + payload
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
