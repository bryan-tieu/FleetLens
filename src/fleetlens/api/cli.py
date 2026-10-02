"""Serve the read-only M1 API on loopback for the local explorer."""

import argparse
from wsgiref.simple_server import make_server

from fleetlens.api import MetricApp
from fleetlens.storage import ClickHouseStore


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Serve local FleetLens metrics")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--database", default="fleetlens")
    args = parser.parse_args(argv)
    if not 1 <= args.port <= 65535:
        parser.error("--port must be between 1 and 65535")
    try:
        store = ClickHouseStore(database=args.database)
    except ValueError as exc:
        parser.error(str(exc))
    with make_server("127.0.0.1", args.port, MetricApp(store)) as server:
        print(f"FleetLens API listening on http://127.0.0.1:{args.port}", flush=True)
        server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
