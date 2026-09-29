> Archived FleetLoop reference. Commands, implementation claims, and agent rules here are historical, not active FleetLens instructions. See [migration context](../../migration.md). Links have been relocated; source code remains in the original repository.

# FleetLoop

An AI-assisted portfolio project for fleet data engineering: collect driving telemetry, validate and query it, discover driving events, and make the resulting metrics explainable.

Target: **Data Engineer, Fleet Data, Self-Driving**, using the posting captured in [the JD map](docs/jd-map.md). Bryan owns the project's decisions and develops the ability to explain, debug, and extend the system while AI assists with implementation.

## Current capability

**Early implementation; no end-to-end demo yet.** The signal registry exists; fleet assignment is unfinished and currently has a syntax error. No tests are present yet. There is no working ingestion service, database deployment, explorer, calibrated simulator, or measured performance result.

See [current status](docs/status.md) for verification details and the next task. Planned architecture below must not be read as shipped functionality.

## First demonstration

A small reproducible synthetic drive dataset flows through validation into ClickHouse. A versioned hard-braking definition produces event counts and an exposure-based rate. A simple explorer shows the cohort summary, a drive trace, and the records behind an event.

The first demo will establish correctness and traceability. Later milestones add recovery and orchestration, diversity-aware upload selection under a byte budget, and a separately evaluated real-image curation experiment.

Synthetic telemetry and BDD100K images are separate data sources. We will only claim a connected telemetry-to-training loop if an explicit, validated mapping links selected scenarios to training examples.

## What this project will demonstrate

| Capability | Planned evidence |
|---|---|
| End-to-end pipeline | Reproducible source-to-metric-to-explorer demo |
| Reliability | Duplicate, replay, late-data, quarantine, and recovery checks |
| Useful metrics | Explicit exposure, stratification, hand-computed fixtures, limitations |
| Inflow control | FIFO/random/coverage-aware comparison at equal bytes |
| Dataset curation | Held-out per-slice comparison with controlled training conditions |
| Engineering ownership | Decisions, failure investigations, walkthroughs, learning evidence |

No result is claimed until its report exists. A negative experiment is still evidence.

## Development

Existing tooling is configured in pyproject.toml and requirements files. From the repository root, with a virtual environment activated:

```text
python -m pip install -r requirements.txt -r requirements-dev.txt
python -m pytest tests/
python -m ruff check .
python -m black --check .
```

These are development checks, not a demo launcher. At the latest review, pytest collected zero tests and fleet.py could not parse. Dependency reproducibility and a common Python version remain M0 work.

Docker Compose and application CLI commands will be documented after they exist and have been verified. No dataset download or GPU is required for the next task.

## Start reading

- [AGENTS.md](AGENTS.reference.md): instructions for future coding sessions.
- [Operating manual](docs/operating-manual.md): how implementation and learning work together.
- [Roadmap](docs/roadmap.md): ordered milestones and completion criteria.
- [Architecture](docs/architecture.md): data boundaries and technology choices.
- [JD map](docs/jd-map.md): role responsibilities and evidence.
- [Learning record](docs/learning/README.md): what has been explained and demonstrated.
- [Experiment rules](docs/experiments.md): how claims become defensible results.

Data stays outside version control. Real-source provenance, privacy, and usage restrictions apply; see [data/README.md](data/README.md) and [privacy design](docs/privacy.md).
