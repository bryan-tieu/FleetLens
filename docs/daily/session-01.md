# Session 01 — establish the FleetLens Python foundation

Status: implemented and locally verified 2026-09-29; hosted CI remains unverified. Roadmap M0 initial increment; JD rows 9 and 10. See [current status](../status.md) and [walkthrough](../walkthroughs/01-python-foundation.md).

## Outcome

A small installable package with explicit telemetry contracts and meaningful tests. AI may implement the work and must explain its decisions. No Docker, dataset download, GPU, or vehicle-simulation framework is needed.

## Implementation

1. Inspect the actual machine/interpreter and choose a supported Python version with dependency compatibility checked. Record the environment; do not inherit old pins without verification.
2. Create pyproject.toml and src/fleetlens/ with a minimal contracts module. Configure focused test/lint/format tooling and reproducible dependency resolution; document commands only after verifying them.
3. Define a small canonical telemetry/sample contract: identity, event time, source provenance, units, and valid-domain rules. Keep source decoding explicit and distinct from normalized values; defer firmware override machinery until a concrete fixture needs it.
4. Add meaningful tests for valid examples, missing/invalid identity, nonfinite values, time/unit assumptions, and real/generated provenance. Use independently specified expected values.
5. Verify installation/import and the targeted checks. No tests collected must not count as success.
6. Walk through one sample, explain what the contract can and cannot validate, and update status and the learning record honestly.

## Acceptance

- Minimal package imports in the documented environment.
- Consequential invalid inputs fail with useful errors.
- Tests exercise actual behavior; lint/format checks pass for the changed scope.
- The README contains tested setup/check commands.
- No synthetic or placeholder value is described as measured fleet behavior.
- A short walkthrough traces an example and explains one failure mode.

## Optional understanding check

Ask why a float can be structurally valid but semantically wrong, what provenance enables, and where conversion belongs. Record only answers Bryan actually provides. Do not require rewriting the implementation by hand.

## Next increment

Add deterministic fleet assignment and a small drive fixture. Preserve vehicle assignments across fleet-size/order changes; choose one explicit probability/weight contract. Use independently defined event windows and exposure expectations before building a miner.
