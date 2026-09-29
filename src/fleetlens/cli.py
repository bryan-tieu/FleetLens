"""Write reproducible, explicitly synthetic JSONL samples and a manifest."""

import argparse
import json
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path

from fleetlens.contracts import CanonicalSample
from fleetlens.simulation import GenerationConfig, generate_fixture, generate_fleet


def _record(sample: CanonicalSample) -> dict:
    record = asdict(sample)
    record["event_time"] = sample.event_time.isoformat().replace("+00:00", "Z")
    record["provenance"]["origin"] = sample.provenance.origin.value
    return record


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate invented fleet telemetry")
    parser.add_argument("--output", type=Path, required=True, help="output directory")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument(
        "--fixture", action="store_true", help="fixed two-drive oracle fixture"
    )
    source.add_argument("--vehicles", type=int, help="number of synthetic vehicles")
    parser.add_argument("--seed", type=int, default=20260929)
    parser.add_argument(
        "--weights",
        type=float,
        nargs=3,
        default=(0.5, 0.3, 0.2),
        metavar=("STEADY", "BRAKE", "GAP"),
    )
    args = parser.parse_args(argv)
    if args.fixture:
        samples = generate_fixture()
        config_id = "fixture-config/v1"
        snapshot_id = "fixture-v1"
        generation_parameters = {"mode": "fixed-fixture"}
    else:
        if args.vehicles < 1:
            parser.error("--vehicles must be positive")
        try:
            config = GenerationConfig(seed=args.seed, weights=tuple(args.weights))
        except ValueError as exc:
            parser.error(str(exc))
        samples = generate_fleet(
            [f"vehicle-{number:06d}" for number in range(args.vehicles)], config
        )
        config_id = config.config_id
        snapshot_id = samples[0].provenance.snapshot_id
        generation_parameters = {
            "mode": "weighted-fleet",
            "seed": config.seed,
            "weights": dict(
                zip(("steady", "brake", "gap"), config.weights, strict=True)
            ),
            "vehicle_count": args.vehicles,
        }
    payload = "".join(json.dumps(_record(s), sort_keys=True) + "\n" for s in samples)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "samples.jsonl").write_bytes(payload.encode("utf-8"))
    manifest = {
        "dataset_id": "fleetlens-synthetic",
        "snapshot_id": snapshot_id,
        "origin": "synthetic",
        "source_schema_version": "synthetic-template/v1",
        "normalization_version": "identity-si/v1",
        "generation_config_id": config_id,
        "generation_parameters": generation_parameters,
        "sample_count": len(samples),
        "sha256_samples_jsonl": sha256(payload.encode()).hexdigest(),
    }
    (args.output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"Wrote {len(samples)} synthetic samples to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
