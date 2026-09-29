# FleetLens

A fleet telemetry platform for reliable ingestion, driving-event analysis, and diversity-aware data selection.

**Status: M0 complete locally; M1 ingestion and local storage underway.** The synthetic fixture feeds a validating JSONL reader and a local ClickHouse raw/logical sample model. Repeated and concurrent loads preserve the logical sample count in a live integration test. Event/exposure metrics and the explorer remain planned.

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
- [Migration record](docs/migration.md): provenance, archive, and transfer boundaries.

## Architecture diagrams

The repository includes the [Archify agent skill](.agents/skills/archify/SKILL.md) for source-backed architecture, workflow, sequence, data-flow, and lifecycle diagrams. Ask your coding agent to use Archify for a diagram; the skill creates a checked, standalone HTML file from typed JSON. Node.js 18 or newer is required. To check the local package, run `node .agents/skills/archify/bin/archify.mjs doctor` from the repository root. The vendored package is upstream v3.0.1; update it deliberately from its [source repository](https://github.com/tt-a1i/archify), rather than changing its files in place.

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

Each command writes `samples.jsonl` and `manifest.json` with a content hash, source/normalization versions, and generation parameters. Repeating a command in the same environment yields identical files. The [fixed fixture oracle](tests/fixtures/tiny_expected.json) records hand-calculated event windows and exposure for future M1 checks; no miner or metric computation exists yet. See the [generator walkthrough](docs/walkthroughs/02-synthetic-fixture.md).

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

Real data remains outside this repository. Read [data/README.md](data/README.md) before configuring dataset access.
