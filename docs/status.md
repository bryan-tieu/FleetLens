# Current status

Updated 2026-09-29. Repository: FleetLens. This is the single session handoff.

## Current state

- Initial M0 increment implemented: installable `src/fleetlens/` package and immutable, validated signal/sample/provenance contracts.
- Python 3.11 is the initial supported minor version; local interpreter verified as 3.11.9 on Windows.
- Runtime has no third-party dependencies. Development/build dependencies are fully version-pinned in requirements-dev.txt; pins are not artifact hashes.
- 59 validation cases pass. GitHub Actions workflow covers Windows/Linux installation, tests, Ruff, Black, dependency consistency, and wheel build. Hosted execution is not verified.
- No generator, application CLI, ingestion/quarantine, database, event/exposure calculations, frontend, or services exist yet. M0 remains incomplete.
- Source identity is defined; storage replay/deduplication is not implemented.
- Walkthrough delivered in [walkthroughs/01-python-foundation.md](walkthroughs/01-python-foundation.md). Learning assessment remains pending; no answers from Bryan recorded.

## Verification

Executed locally with `.venv/Scripts/python.exe`:

- `-m pip install -r requirements-dev.txt`: successful in a newly created environment.
- `-m pip install --no-build-isolation --no-deps -e .`: successful.
- `-m pytest`: 59 passed.
- `-m ruff check .`: all checks passed.
- `-m black --check src tests`: four files unchanged after formatting.
- `-m pip check`: no broken requirements.
- `-m pip wheel --no-build-isolation --no-deps . --wheel-dir dist`: successful.
- Wheel installed offline with `--no-index --no-deps` into a second fresh environment at runs/package-check. Its interpreter with `-I` imported version 0.1.0 from site-packages, including public contract exports.
- First smoke-test one-liner failed because PowerShell stripped embedded quotes; rerunning the same assertions through literal stdin passed. No package failure was found.

Pre-commit verification on 2026-09-29: `-B -m pytest -p no:cacheprovider` (59 passed), `-m ruff check --no-cache .`, `-m black --check src tests`, `-m pip check`, and `git diff --check` all passed. Bryan authorized committing and pushing this foundation to origin/main.

No real dataset was read. No throughput, fleet behavior, or cloud performance was measured. Hosted CI and Linux checks remain unavailable locally.

## Local resources

Ignored .venv, dist/build packaging artifacts, and runs/package-check remain for development and inspection. No background services or containers were started.

## Next bounded task

Complete the next M0 increment: stable per-vehicle random assignment, a tiny synthetic drive fixture, independent event-window/exposure expectations, and a reproducible CLI. Test stability across fleet-size and ordering changes; keep evaluation truth separate from selection inputs.

Then introduce local ClickHouse for M1's validated loading and query requirements.

## Source reference

[Migration record](migration.md) documents the independent initial commit f733f84 and preserved FleetLoop context. No source code or Git ancestry was copied from FleetLoop. Archived behavior and hardware/dataset observations remain historical.
