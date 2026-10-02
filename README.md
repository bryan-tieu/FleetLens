# FleetLens

A fleet telemetry platform for reliable ingestion, driving-event analysis, and diversity-aware data selection.

**Status: M0 and the local M1 source-to-explorer demonstration are implemented.** The synthetic fixture feeds validating JSONL ingestion and local ClickHouse storage. A guarded snapshot read collapses identical replay rows and checks source hash and completeness before a rate is exposed. Versioned hard-braking and valid-exposure calculations feed bounded JSON routes and a React/TypeScript explorer. The demonstration uses invented data and does not measure real fleet safety.

## Purpose

Build a defensible portfolio for **Data Engineer, Fleet Data, Self-Driving**. The [captured job description](docs/jd-map.md) guides scope. AI may implement the code while Bryan learns to explain, debug, modify, and defend the entire system.

## First demonstration

A small reproducible synthetic drive dataset -> validated ingestion -> ClickHouse -> versioned hard-braking events and valid exposure -> a simple explorer with source traceability.

Later milestones add reliability and orchestration, upload admission under a byte budget, and a separate controlled real-image curation experiment. Synthetic telemetry and image datasets are not claimed to be one linked training loop without a validated mapping.

## Start here

- [AGENTS.md](AGENTS.md): persistent instructions for coding sessions ([CLAUDE.md](CLAUDE.md) imports it for Claude Code).
- [Current status](docs/status.md): what exists and the next task.
- Dated records: [history](docs/history.md), [decisions](docs/decisions.md), [learning evidence](docs/learning/README.md), and [session plans](docs/sessions/README.md).
- [Roadmap](docs/roadmap.md): job-aligned milestones and acceptance criteria.
- [Architecture](docs/architecture.md): staged design and data contracts.
- [Operating manual](docs/operating-manual.md): how AI implementation and learning work together.
- [OpenRig pair](docs/openrig.md): optional local implementer/reviewer workflow and operating commands.
- [Learning record](docs/learning/README.md): observed understanding, separate from code completion.
- [M0 learning guide](docs/learning/m0-concepts.md): concepts, examples, and optional checks from the completed foundation.
- [M1 learning guide](docs/learning/m1-concepts.md): a reading order and three checks for the source-to-explorer implementation.
- [Production bridge](docs/learning/production-bridge.md): each implemented concept mapped to the production data-engineering pattern it corresponds to, its limits here, and a bridge check.
- [Migration record](docs/migration.md): provenance, archive, and transfer boundaries.

## Architecture diagrams

The repository includes the [Archify agent skill](.agents/skills/archify/SKILL.md) for source-backed architecture, workflow, sequence, data-flow, and lifecycle diagrams. Ask your coding agent to use Archify for a diagram; the skill creates a checked, standalone HTML file from typed JSON. Node.js 18 or newer is required. To check the local package, run `node .agents/skills/archify/bin/archify.mjs doctor` from the repository root. The vendored package is upstream v3.0.1; update it deliberately from its [source repository](https://github.com/tt-a1i/archify), rather than changing its files in place.

Open the [2026-09-29 source-to-explorer map](.archify/architecture-fleetlens-end-to-end-20260929-154317/fleetlens-end-to-end.html) and its [engineering walkthrough](docs/walkthroughs/05-architecture-map.md). Its M1 planned labels predate the implementation described here.

## Running the project

The initial supported interpreter is Python 3.11 (verified locally on Windows with 3.11.9). From the repository root in PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pip install --no-build-isolation --no-deps -e .
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m black --check src tests
.\.venv\Scripts\python.exe -m pip wheel --no-build-isolation --no-deps . --wheel-dir dist
```

Stop if a command fails. Environment activation is optional; these commands use the environment interpreter directly. On Linux, use `python3.11` to create the environment and `.venv/bin/python` for subsequent commands; that platform passes in hosted CI but has not been verified on a local Linux machine.

The package has no runtime dependencies. Development and build tools, including transitive dependencies, are pinned in `requirements-dev.txt`; install those before using `--no-build-isolation`. These are version pins, not a hash-locked supply chain or byte-for-byte build guarantee. Change pins deliberately and rerun checks.

Read the [foundation walkthrough](docs/walkthroughs/01-python-foundation.md) for the sample contract and its limits.

Generate invented samples from the repository root after installing the package:

```powershell
.\.venv\Scripts\python.exe -m fleetlens.cli --output runs/tiny --fixture
.\.venv\Scripts\python.exe -m fleetlens.cli --output runs/fleet-10 --vehicles 10 --seed 20260929 --weights 0.5 0.3 0.2
```

On macOS/Linux, use `.venv/bin/python` in place of `.\.venv\Scripts\python.exe`. The installed `fleetlens` entry point accepts the same arguments.

Each command writes `samples.jsonl` and `manifest.json` with a content hash, source/normalization versions, and generation parameters. Repeating a command in the same environment yields identical files. The [fixed fixture oracle](tests/fixtures/tiny_expected.json) records hand-calculated event windows and exposure used to check the M1 metric transform. See the [generator walkthrough](docs/walkthroughs/02-synthetic-fixture.md).

Validate the generated snapshot and write a row accounting/quarantine report:

```powershell
.\.venv\Scripts\python.exe -m fleetlens.ingestion.cli --input runs/tiny --output runs/tiny-validation
```

On macOS/Linux, use `.venv/bin/python`. The installed `fleetlens-validate` entry point accepts the same arguments. The report contains `input_rows`, `accepted_rows`, `rejected_rows`, and the snapshot hash; `quarantine.jsonl` contains line numbers and reasons without raw records. A manifest/hash mismatch rejects the whole snapshot. See the [ingestion walkthrough](docs/walkthroughs/03-jsonl-ingestion.md) for replay limits.

For the local ClickHouse slice, start Docker Desktop and run:

```powershell
docker compose -f infra/clickhouse/compose.yaml up -d
.\.venv\Scripts\python.exe -m fleetlens.storage.cli --input runs/tiny
.\.venv\Scripts\python.exe -m fleetlens.storage.cli --input runs/tiny
```

On macOS/Linux, substitute `.venv/bin/python`. The installed `fleetlens-load` entry point accepts the same `--input` argument. The command applies versioned SQL migrations and prints input, accepted, quarantined, physical, logical, and conflict counts. Two loads of the 11-row fixture leave **11 logical samples** while the append-only raw table may contain 22 physical rows. This local compose binds HTTP only to `127.0.0.1:18123` and uses a visible development-only credential; do not use it for real or restricted data. Run `docker compose -f infra/clickhouse/compose.yaml down` to stop the service; add `-v` only if you intend to delete its stored data. See the [storage walkthrough](docs/walkthroughs/04-clickhouse-storage.md).

After loading the fixture, start the read-only API in another terminal:

```powershell
.\.venv\Scripts\python.exe -m fleetlens.api.cli --port 8765
```

The installed `fleetlens-api` entry point is equivalent. On macOS/Linux, use `.venv/bin/python`. It listens on loopback only. Request `http://127.0.0.1:8765/api/v1/cohort?dataset_id=fleetlens-synthetic&snapshot_id=fixture-v1` for the bounded synthetic cohort; the [API walkthrough](docs/walkthroughs/08-metric-api.md) specifies drive and event routes and their error behavior.

For the **single-command M1 demo** from the repository root, first install Node.js/npm and frontend dependencies with `cd explorer && npm ci`, then return to the root. Start the local ClickHouse compose service as above. On macOS/Linux run:

```sh
.venv/bin/python -m fleetlens.demo
```

On Windows PowerShell use `.\.venv\Scripts\python.exe -m fleetlens.demo`. The equivalent installed entry point is `fleetlens-demo`. The command regenerates the fixed synthetic fixture in `runs/m1-demo`, validates/loads it, prints bytes, load time, three query times, hardware summary, and logical/physical row counts, then serves the API and explorer at `http://127.0.0.1:5173/` until Ctrl+C. `--no-serve` runs preparation and measurements only. Repeating the command appends physical raw rows while preserving 11 logical samples and the rate. Measurements are local observations on 11 invented samples, not throughput claims. See the [explorer walkthrough](docs/walkthroughs/09-explorer-and-demo.md).

The [2026-10-01 local run report](reports/m1-local-run-2026-10-01.md) records one observed run and its limits. The [45-second M1 demo](reports/m1-demo-2026-10-01.mp4) shows the actual local explorer with captions; it was captured from an isolated offscreen WebKit view by [the macOS helper](scripts/render_m1_demo.swift). The [capture script](docs/demo-script.md) also supports a narrated walkthrough.

Real data remains outside this repository. Read [data/README.md](data/README.md) before configuring dataset access.
