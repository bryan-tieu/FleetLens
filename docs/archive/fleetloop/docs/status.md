> Archived FleetLoop reference. Commands, implementation claims, and agent rules here are historical, not active FleetLens instructions. See [migration context](../../../migration.md). Links have been relocated; source code remains in the original repository.

# Current status

Updated 2026-09-28. This is the single session handoff; inspect the working tree before continuing.

## Active objective

Build a small, reliable fleet-data demonstration for the captured Tesla role, using AI-assisted implementation with explanations and observed learning checkpoints. Active milestone: **M0 — executable foundation** in [roadmap.md](roadmap.md).

## Observed implementation

- fleetgen/signals.py contains signal specifications and effective-from firmware resolution. FIRMWARE_OVERRIDES is empty; no planted sign change is configured.
- fleetgen/fleet.py contains fleet dimensions and weights, but _validate_tables has an unfinished statement; assign_vehicle, build_fleet, and model_spec are stubs.
- There is no generator CLI, ingestion pipeline, Compose deployment, metrics implementation, explorer, or CI workflow.
- Tests directory contains only its placeholder. No performance, calibration, selection, or model-training results exist.
- 2026-09-28 review: AST parsing failed at fleet.py line 253; an isolated sampling probe rejected Northeast weights totaling 1.001; pytest collected 0 items.
- The review used Windows Python 3.11.9. The Mac version was historically recorded as 3.10.6; a supported common version and dependency resolution remain to be verified.
- This documentation revision changes project guidance, not runtime behavior. The known code failures remain open.

## Existing work to preserve

At the start of this revision, docs/daily/day-01.md, docs/glossary.md, fleetgen/signals.py, and requirements.txt had uncommitted edits; fleetgen/fleet.py was untracked. Do not reset or overwrite that work. The old Day 01 plan is preserved with a superseded notice; the glossary retains its domain content.

## Data / environment

History records comma2k19, nuScenes mini, BDD100K images, and NHTSA/FHWA downloads on Windows; BDD100K detection-label readiness is unresolved. Their current presence, completeness, permitted use, GPU availability, and free disk have not been reverified in this revision. Do not redownload automatically or repeat historical disk readings as current facts. The next task needs none of those datasets.

## Next bounded task

Follow [daily/session-02.md](daily/session-02.md): finish and test the fleet assignment contract in the existing layout. Explain probability validation, per-vehicle deterministic randomness, and the distinction between simulated assumptions and measured fleet demographics.

Then implement a small generated drive fixture, independently defined expected events, and a CLI before introducing ClickHouse. Do not start by migrating every package or launching the whole proposed stack.

## Learning / verification handoff

No understanding assessment has been performed in this revision. Every competency remains **not assessed** in [learning/README.md](learning/README.md). The existing-code walkthrough is reading material, not evidence of mastery.

Documentation verification: all local link targets resolved across 27 Markdown files; the captured job-posting appendix matches its pre-revision Git version; git diff --check reported no whitespace errors. Active guidance was reviewed for superseded coach-only restrictions. Runtime tests were not rerun for this documentation-only revision; the previously observed failures remain M0 work.
