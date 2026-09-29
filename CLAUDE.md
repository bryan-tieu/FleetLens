# FleetLens — Claude Code entry point

@AGENTS.md

AGENTS.md (imported above) is the authoritative, tool-neutral instruction file. This file only adds a fast orientation map so a fresh session does not have to rediscover the repo. It does not own status, roadmap, or decisions — follow the ownership table in AGENTS.md and update those files, not this one, when state changes. Update this file only when the repo map, commands, or core invariants change.

## Orientation in 60 seconds

- **What it is:** a solo, AI-assisted portfolio project targeting Tesla's *Data Engineer, Fleet Data, Self-Driving* role (req. 279540, captured in docs/jd-map.md). Bryan (junior engineer, CSULB CS May 2026) owns decisions and learns to explain/debug/defend; the assistant implements as a staff data engineer and teaches.
- **Where it is:** end of the first M0 increment. Only the canonical telemetry contract exists. There is no generator, CLI, ingestion, database, metric, API, or frontend yet. Read docs/status.md for the live state and next task — it overrides anything here.
- **Lineage:** FleetLens is a fresh-code restart of an earlier repo, FleetLoop (C:\Users\Bryan\Downloads\FleetLoop\FleetLoop, untouched). Only documentation was migrated. Everything in docs/archive/fleetloop/ is historical — never follow its commands, 12-week schedule, "hard rule N" references, `/plan-day`-style skills, or assume its `fleetgen/` code exists here.

## Code map (everything that currently runs)

| Path | What it is |
|---|---|
| src/fleetlens/contracts/sample.py | `DataOrigin` (StrEnum synthetic/real), `Provenance`, `CanonicalSample` — frozen, slotted dataclasses validated in `__post_init__`, raising field-named `ValueError`s |
| src/fleetlens/contracts/\_\_init\_\_.py | Public exports of the three names above |
| tests/test_contracts.py | 59 parametrized cases (valid fixture, invalid identity/numbers/time/lineage, origin rules, identity semantics, immutability) |
| pyproject.toml | setuptools src-layout, Python `>=3.11,<3.12`, zero runtime deps; pytest/Ruff/Black config (line length 88) |
| requirements-dev.txt | Fully pinned dev/build toolchain (pins, not hashes) |
| .github/workflows/ci.yml | Windows + Ubuntu matrix mirroring the local check commands |

Target layout for later modules (simulation/, ingestion/, selection/, metrics/, api/, migrations/, explorer/, …) is in docs/architecture.md. Do not create empty modules ahead of a consumer.

## Contract invariants worth remembering

- Canonical units: `speed_mps` is nonnegative ground-speed magnitude (m/s); `longitudinal_accel_mps2` is positive forward, negative when braking (m/s²). Values are never rescaled inside the contract — decoding/unit conversion belongs to a future source adapter, done exactly once.
- `event_time` must be a timezone-aware datetime with zero UTC offset. `source_sequence` is a strict nonnegative `int` (bools rejected). Numbers reject bools, strings, NaN, and ±inf.
- Synthetic provenance requires `generation_config_id`; real provenance must not have one. `schema_version` is fixed at `canonical-sample/v1`.
- `sample_key` = (dataset_id, snapshot_id, vehicle_id, drive_id, source_sequence). It deliberately excludes values and normalization_version, so a decode correction keeps the same logical identity. It is an identity definition, not deduplication — replay/revision policy is an open ingestion decision.
- The contract cannot catch semantically wrong but structurally valid values (e.g. km/h passed as m/s); that is the adapter's test responsibility.

## Commands (PowerShell, repo root, Python 3.11)

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pip install --no-build-isolation --no-deps -e .
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m black --check src tests
```

A local `.venv` already exists. Invoke its interpreter directly rather than activating. The Bash tool also works (`.venv/Scripts/python.exe …`). `gh` is not installed; the repo is public at github.com/bryan-tieu/FleetLens, so CI runs can be read from `https://api.github.com/repos/bryan-tieu/FleetLens/actions/runs`.

## Working norms that are easy to miss

- Keep **planned / implemented / verified / measured** distinct in every doc and claim. Never record an answer or understanding Bryan did not actually give (docs/learning/README.md).
- Session finish: update docs/status.md (changes, exact check results, next step), add a docs/history.md entry, add docs/decisions.md entries for consequential choices, and write a walkthrough in docs/walkthroughs/ for substantial features.
- Commit or push only when Bryan asks. Real datasets live outside the repo (data/ is git-ignored); read docs/privacy.md before touching real GPS or video.
