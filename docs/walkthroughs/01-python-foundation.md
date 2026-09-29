# Python foundation: from values to a validated sample

Implemented 2026-09-29. Roadmap M0, initial contracts/development-environment increment.

## Purpose and inputs

Before ingestion stores telemetry, every consumer needs the same meaning for a sample. A canonical value uses the project's common unit and sign convention. Provenance means the recorded history of where a value came from and how it was transformed.

The public API is in [contracts/__init__.py](../../src/fleetlens/contracts/__init__.py); validation lives in [sample.py](../../src/fleetlens/contracts/sample.py). Construction returns an immutable object or raises a field-specific ValueError. This is an in-memory Python contract, not yet a JSON parser or quarantine pipeline.

## Trace one observation

The test fixture in [test_contracts.py](../../tests/test_contracts.py) constructs:

- Dataset `synthetic-demo`, snapshot `fixture-v1`, synthetic origin, generation config `fixture-config/v1`.
- Source record `drive-7/record-0`, source schema `fixture/v1`, normalization `identity-si/v1`.
- Vehicle `vehicle-7`, drive `drive-7`, source sequence 0, UTC timestamp 2026-09-28T00:00:00Z.
- Speed 10 m/s and longitudinal acceleration -4 m/s².

Provenance checks require identifiers and the synthetic generation configuration reference. Sample checks require valid identity, integer sequence, UTC time, finite numbers, and nonnegative speed. Negative acceleration is allowed. The result preserves 10 and -4 exactly: construction does not decode or rescale them.

Its logical key is `("synthetic-demo", "fixture-v1", "vehicle-7", "drive-7", 0)`. A later decode correction keeps this source key, while another snapshot has a different key. This is a definition of identity, not proof of deduplication. Ingestion must later define revisions and replay explicitly.

## One failure mode and the alternative

If a source reports 36 km/h, an adapter must convert it to 10 m/s before constructing the canonical sample and record its conversion version. Passing 36 as `speed_mps` succeeds structurally but is semantically wrong. An independently specified adapter test must catch that mistake; applying conversion again downstream would introduce another error.

Frozen dataclasses provide typed records and explicit checks without runtime dependencies. A schema library is a useful alternative when external JSON validation becomes necessary. At scale, use the same semantics with batch validation and reconciliation, rather than assuming Python object construction is an ingestion architecture.

## Boundaries

Speed is ground-speed magnitude, not signed longitudinal velocity. Acceleration is positive forward and negative for braking during forward motion; reverse-driving event interpretation is not defined here. Only UTC-aware datetimes are accepted; timezone conversion belongs at the source boundary.

The contract rejects missing/blank identifiers, unsupported schema versions, booleans as numeric values, negative speed, NaN/infinity, and synthetic records missing a config reference. Real records cannot carry a synthetic config reference. Real-origin tests use invented metadata; no real dataset was accessed.

It does not verify that referenced snapshots/configs exist, infer physically realistic trajectories, enforce record ordering, detect duplicates, evaluate braking episodes, or measure valid exposure. No dataset, event miner, or rate claim is delivered by this increment.

## Engineering evidence and learning

Local Python 3.11.9: 59 test cases pass; Ruff, Black, pip dependency checks, editable installation, wheel build, and isolated wheel import pass. Windows/Linux hosted CI passed on the committed foundation. Setup commands are in the [README](../../README.md).

Walkthrough delivered; Bryan's understanding remains unassessed. Optional teach-back: why could `speed_mps=36` pass validation and still be wrong, and where should the correction happen?
