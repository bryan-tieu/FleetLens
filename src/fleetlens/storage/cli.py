"""Load validated M0 samples into the local ClickHouse demonstration."""

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from fleetlens.ingestion import read_snapshot
from fleetlens.storage import ClickHouseStore


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Load one validated M0 snapshot")
    parser.add_argument("--input", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = read_snapshot(args.input)
        summary = ClickHouseStore().load(result)
    except (OSError, ValueError, RuntimeError) as exc:
        parser.exit(2, f"load failed: {exc}\n")
    print(json.dumps(asdict(summary), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
