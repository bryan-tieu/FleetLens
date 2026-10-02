"""Small WSGI API over the guarded M1 snapshot summaries.

Every request is snapshot scoped and capped by the storage/metric boundaries.
The API does not expose raw SQL, arbitrary filters, or an unbounded row feed.
"""

import json
from dataclasses import asdict
from datetime import datetime
from typing import Any
from urllib.parse import parse_qs

from fleetlens.metrics import cohort_summary, drive_summary
from fleetlens.storage import (
    ClickHouseStore,
    SnapshotLimitExceeded,
    StorageConflict,
    validate_snapshot_selector,
)

_ROUTES = {
    "/api/v1/cohort": ("dataset_id", "snapshot_id"),
    "/api/v1/drive": ("dataset_id", "snapshot_id", "vehicle_id", "drive_id"),
    "/api/v1/event": (
        "dataset_id",
        "snapshot_id",
        "vehicle_id",
        "drive_id",
        "start_sequence",
    ),
}
_OPTIONAL = {"max_samples", "max_drives"}


def _json_default(value: Any) -> str:
    if isinstance(value, datetime):
        return value.isoformat().replace("+00:00", "Z")
    raise TypeError(f"cannot serialize {type(value).__name__}")


def _integer_bound(raw: str, name: str, minimum: int, maximum: int) -> int:
    if not raw.isascii() or not raw.isdecimal() or not minimum <= int(raw) <= maximum:
        raise ValueError(f"invalid {name}")
    return int(raw)


class MetricApp:
    """Inject the ClickHouse boundary for direct WSGI testing and local serving."""

    def __init__(self, store: ClickHouseStore | None = None) -> None:
        self.store = store or ClickHouseStore()

    def __call__(self, environ: dict, start_response: Any) -> list[bytes]:
        if environ.get("REQUEST_METHOD") != "GET":
            return self._reply(
                start_response,
                "405 Method Not Allowed",
                {"error": "method_not_allowed"},
            )
        path = environ.get("PATH_INFO", "")
        if path == "/api/v1/health":
            return self._reply(start_response, "200 OK", {"status": "process_ready"})
        if path not in _ROUTES:
            return self._reply(start_response, "404 Not Found", {"error": "not_found"})
        try:
            query = parse_qs(
                environ.get("QUERY_STRING", ""),
                keep_blank_values=True,
                max_num_fields=8,
            )
            allowed = set(_ROUTES[path]) | _OPTIONAL
            if set(query) - allowed or any(
                len(values) != 1 for values in query.values()
            ):
                raise ValueError("unknown or repeated query parameter")
            params = {name: query[name][0] for name in _ROUTES[path]}
            if any(not value or len(value) > 128 for value in params.values()):
                raise ValueError("missing or oversized query parameter")
            validate_snapshot_selector(params["dataset_id"])
            validate_snapshot_selector(params["snapshot_id"])
            max_samples = _integer_bound(
                query.get("max_samples", ["1000"])[0], "max_samples", 1, 10_000
            )
            if path == "/api/v1/cohort":
                max_drives = _integer_bound(
                    query.get("max_drives", ["100"])[0], "max_drives", 1, 1_000
                )
            elif "max_drives" in query:
                raise ValueError("max_drives applies only to cohort")
            if path == "/api/v1/event":
                sequence = _integer_bound(
                    params["start_sequence"], "start_sequence", 0, 2**64 - 1
                )
        except (KeyError, ValueError):
            return self._reply(
                start_response,
                "400 Bad Request",
                {"error": "invalid_or_oversized_request"},
            )
        try:
            if path == "/api/v1/cohort":
                result = cohort_summary(
                    self.store,
                    params["dataset_id"],
                    params["snapshot_id"],
                    max_samples=max_samples,
                    max_drives=max_drives,
                )
                body = asdict(result)
                body["data_origin"] = "synthetic"
                body["drives"] = [
                    {
                        "drive_key": drive.drive_key,
                        "sample_count": drive.sample_count,
                        "episode_count": len(drive.events),
                        "valid_seconds": drive.exposure.valid_seconds,
                        "valid_distance_m": drive.exposure.valid_distance_m,
                        "status": drive.status,
                        "episodes_per_100_km": drive.episodes_per_100_km,
                    }
                    for drive in result.drives
                ]
            else:
                drive = drive_summary(
                    self.store,
                    params["dataset_id"],
                    params["snapshot_id"],
                    params["vehicle_id"],
                    params["drive_id"],
                    max_samples=max_samples,
                )
                if path == "/api/v1/drive":
                    body = asdict(drive)
                    body["data_origin"] = "synthetic"
                else:
                    events = [
                        event
                        for event in drive.events
                        if event.source_sample_keys[0][-1] == sequence
                    ]
                    if not events:
                        raise LookupError("event absent")
                    body = {
                        "data_origin": "synthetic",
                        "drive_status": drive.status,
                        "event": asdict(events[0]),
                    }
        except StorageConflict:
            return self._reply(
                start_response, "409 Conflict", {"error": "snapshot_conflict"}
            )
        except SnapshotLimitExceeded:
            return self._reply(
                start_response,
                "400 Bad Request",
                {"error": "snapshot_exceeds_limit"},
            )
        except ValueError:
            return self._reply(
                start_response,
                "422 Unprocessable Content",
                {"error": "snapshot_invalid"},
            )
        except LookupError:
            return self._reply(start_response, "404 Not Found", {"error": "not_found"})
        except RuntimeError:
            return self._reply(
                start_response,
                "503 Service Unavailable",
                {"error": "storage_unavailable"},
            )
        try:
            return self._reply(start_response, "200 OK", body)
        except (ValueError, OverflowError):
            return self._reply(
                start_response,
                "422 Unprocessable Content",
                {"error": "snapshot_invalid"},
            )

    @staticmethod
    def _reply(start_response: Any, status: str, body: dict) -> list[bytes]:
        payload = (
            json.dumps(body, default=_json_default, sort_keys=True, allow_nan=False)
            + "\n"
        ).encode("utf-8")
        start_response(
            status,
            [
                ("Content-Type", "application/json; charset=utf-8"),
                ("Content-Length", str(len(payload))),
                ("Cache-Control", "no-store"),
            ],
        )
        return [payload]
