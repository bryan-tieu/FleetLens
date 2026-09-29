> Archived FleetLoop reference. Commands, implementation claims, and agent rules here are historical, not active FleetLens instructions. See [migration context](../../../../migration.md). Links have been relocated; source code remains in the original repository.

# Session 02 — finish the fleet assignment contract

Status: planned, not executed. Roadmap M0; JD rows 9 and 10.

## Outcome

An importable, deterministic fleet-assignment module with meaningful validation tests and an explanation of its contracts. This task needs no Docker, dataset download, GPU, or broad package migration.

## Preserve and inspect

fleet.py is existing untracked user work; signals.py and requirements.txt also have edits. Read before changing. Retain the intended models, cohort correlations, and clearly marked simulation assumptions.

## Implementation

1. Define distribution semantics: are rows rounded probabilities or arbitrary relative weights? Use explicit finite/nonnegative validation, permit zero, require positive mass, and handle rounding under one consistent policy shared by sampling.
2. Complete table validation, including expected parent/child keys, allowed firmware strings, and useful deterministic error messages. Avoid sorting Enum objects without a stable key. Bind generic return types to input key types.
3. Implement model_spec, assign_vehicle, and build_fleet. Validate supported seed/ID/count inputs. Derive independent per-vehicle randomness without Python's process-randomized hash; vehicle assignment must not depend on fleet construction order or requested fleet size.
4. Add focused tests for malformed/empty/nonfinite distributions, intentional zero weights, model lookups, reproducibility, fleet-size stability, and relevant firmware-resolution boundaries. Test observable contracts rather than reproducing private implementation.
5. Run pytest, Ruff, and formatting checks on the changed scope. Report real results. Explain any pre-existing issue outside that scope; avoid reformatting unrelated user work.
6. Update the contracts walkthrough and status; offer a brief teach-back.

## Acceptance

- Module imports; public helpers return valid declared objects.
- Same seed/ID returns the same assignment; fleet expansion preserves earlier assignments.
- Invalid rows fail clearly, valid rounded rows follow the declared policy, and zero-probability choices are not selected.
- No empty-suite success claim; targeted tests and checks pass.
- Firmware assumptions remain explicitly simulated; no real fleet-demographic claim.
- Bryan receives an example trace and knows where to revisit the explanation.

## Learning checkpoint

Ask why normalization must agree with validation, why per-vehicle random streams matter, and what correlated cohorts let us investigate. Record answers only if provided. No requirement to reimplement the module by hand.

## Follow-on

Build a small deterministic drive fixture and independently specified expected event/exposure outputs. The full state machine and comparison proposed in original Day 01 are not prerequisites for finishing this contract.
