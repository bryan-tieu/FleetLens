# FleetLens

A fleet telemetry platform for reliable ingestion, driving-event analysis, and diversity-aware data selection.

**Status: documentation foundation only.** This repository starts with fresh code and Git history independent of FleetLoop. No generator, pipeline, database deployment, tests, or explorer has been implemented here yet.

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

There is no application or development environment to run yet. M0 will establish an installable Python package, supported interpreter, reproducible dependencies, tests, and verified setup commands. Do not copy old virtual environments or treat archived commands as current instructions.

Real data remains outside this repository. Read [data/README.md](data/README.md) before configuring dataset access.
