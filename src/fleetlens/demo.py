"""Prepare and serve the local synthetic source-to-explorer demonstration."""

import argparse
import json
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path

from fleetlens.cli import main as generate
from fleetlens.ingestion import read_snapshot
from fleetlens.metrics import cohort_summary
from fleetlens.storage import ClickHouseStore


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the M1 synthetic local demo")
    parser.add_argument("--output", type=Path, default=Path("runs/m1-demo"))
    parser.add_argument(
        "--no-serve", action="store_true", help="measure without serving"
    )
    args = parser.parse_args(argv)

    started = time.perf_counter()
    generate(["--output", str(args.output), "--fixture"])
    generated_seconds = time.perf_counter() - started
    result = read_snapshot(args.output)
    store = ClickHouseStore()
    started = time.perf_counter()
    load = store.load(result)
    load_seconds = time.perf_counter() - started
    query_times = []
    cohort = None
    for _ in range(3):
        started = time.perf_counter()
        cohort = cohort_summary(store, "fleetlens-synthetic", "fixture-v1")
        query_times.append(time.perf_counter() - started)
    assert cohort is not None
    report = {
        "data_origin": "synthetic",
        "dataset_id": cohort.dataset_id,
        "snapshot_id": cohort.snapshot_id,
        "sample_count": cohort.sample_count,
        "episode_count": cohort.episode_count,
        "valid_distance_m": cohort.valid_distance_m,
        "episodes_per_100_km": cohort.episodes_per_100_km,
        "source_complete": cohort.source_complete,
        "physical_rows_after_load": load.physical_rows,
        "logical_rows_after_load": load.logical_rows,
        "dataset_bytes": sum(
            (args.output / name).stat().st_size
            for name in ("samples.jsonl", "manifest.json")
        ),
        "generation_seconds": generated_seconds,
        "load_seconds": load_seconds,
        "query_seconds_each": query_times,
        "host": {"system": platform.system(), "machine": platform.machine()},
        "limitation": (
            "Tiny generated fixture; local timings are not throughput benchmarks."
        ),
    }
    print(json.dumps(report, indent=2, sort_keys=True), flush=True)
    if args.no_serve:
        return 0

    explorer = Path.cwd() / "explorer"
    if not (explorer / "node_modules").is_dir() or not shutil.which("npm"):
        parser.exit(2, "Install explorer dependencies with `cd explorer && npm ci`.\n")
    processes: list[subprocess.Popen] = []
    try:
        processes.append(
            subprocess.Popen(
                [sys.executable, "-m", "fleetlens.api.cli"], start_new_session=True
            )
        )
        processes.append(
            subprocess.Popen(
                [
                    "npm",
                    "run",
                    "dev",
                    "--",
                    "--port",
                    "5173",
                    "--strictPort",
                ],
                cwd=explorer,
                start_new_session=True,
            )
        )
        print(
            "Explorer: http://127.0.0.1:5173/  (Ctrl+C stops both servers)", flush=True
        )
        while all(process.poll() is None for process in processes):
            time.sleep(0.2)
        return 1
    except KeyboardInterrupt:
        return 0
    finally:
        for process in processes:
            if process.poll() is None:
                process.terminate()
        for process in processes:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


if __name__ == "__main__":
    raise SystemExit(main())
