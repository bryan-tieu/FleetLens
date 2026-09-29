"""Validate a generated snapshot and write an accounting/quarantine report."""

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from fleetlens.ingestion import read_snapshot


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate an M0 synthetic snapshot")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = read_snapshot(args.input)
    except (OSError, ValueError) as exc:
        parser.exit(2, f"snapshot rejected: {exc}\n")
    args.output.mkdir(parents=True, exist_ok=True)
    quarantine = "".join(
        json.dumps(asdict(row), sort_keys=True) + "\n" for row in result.rejected
    )
    (args.output / "quarantine.jsonl").write_text(quarantine, encoding="utf-8")
    report = {
        "input_rows": result.input_rows,
        "accepted_rows": len(result.samples),
        "rejected_rows": len(result.rejected),
        "snapshot_hash": result.snapshot_hash,
    }
    (args.output / "validation.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        f"Validated {result.input_rows} rows: {len(result.samples)} accepted, "
        f"{len(result.rejected)} quarantined"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
