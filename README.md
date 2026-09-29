# FleetLens

A fleet telemetry platform for reliable ingestion, driving-event analysis, and diversity-aware data selection.

**Status: Python foundation implemented and locally verified.** Installable package, canonical telemetry contracts, 59 passing validation cases, pinned development dependencies, and a Windows/Linux CI workflow. Hosted CI has not run yet. Generator, ingestion, database, and explorer remain planned.

## Purpose

Build a defensible portfolio for **Data Engineer, Fleet Data, Self-Driving**. The [captured job description](docs/jd-map.md) guides scope. AI may implement the code while Bryan learns to explain, debug, modify, and defend the entire system.

## First demonstration

A small reproducible synthetic drive dataset -> validated ingestion -> ClickHouse -> versioned hard-braking events and valid exposure -> a simple explorer with source traceability.

Later milestones add reliability and orchestration, upload admission under a byte budget, and a separate controlled real-image curation experiment. Synthetic telemetry and image datasets are not claimed to be one linked training loop without a validated mapping.

## Start here

- [AGENTS.md](AGENTS.md): persistent instructions for coding sessions.
- [Current status](docs/status.md): what exists and the next task.
- [First implementation session](docs/daily/session-01.md): the clean foundation plan.
- [Roadmap](docs/roadmap.md): job-aligned milestones and acceptance criteria.
- [Architecture](docs/architecture.md): staged design and data contracts.
- [Operating manual](docs/operating-manual.md): how AI implementation and learning work together.
- [Learning record](docs/learning/README.md): observed understanding, separate from code completion.
- [Migration record](docs/migration.md): provenance, archive, and transfer boundaries.

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

Stop if a command fails. Environment activation is optional; these commands use the environment interpreter directly. On Linux, use `python3.11` to create the environment and `.venv/bin/python` for subsequent commands; that platform is configured in CI but not locally verified.

The package has no runtime dependencies. Development and build tools, including transitive dependencies, are pinned in `requirements-dev.txt`; install those before using `--no-build-isolation`. These are version pins, not a hash-locked supply chain or byte-for-byte build guarantee. Change pins deliberately and rerun checks.

Read the [foundation walkthrough](docs/walkthroughs/01-python-foundation.md) for the sample contract and its limits. There is no generator CLI yet.

Real data remains outside this repository. Read [data/README.md](data/README.md) before configuring dataset access.
