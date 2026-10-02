# Active roadmap

Effective 2026-09-28; adapted from FleetLoop's revised scope for a fresh-code FleetLens repository. Milestones are dependency-ordered, not promises tied to old dates. Start from [status.md](status.md), not an assumed completed phase.

## M0 — executable foundation

**JD rows:** 9, 10. Start an installable package at src/fleetlens/, establish signal/sample contracts, then implement fleet assignment and a small synthetic drive generator. Add a reproducible CLI, fixed configuration/seed, schema/provenance metadata, explicit signal semantics, and meaningful tests. Resolve Python/dependency reproducibility and add lightweight CI once the checks actually pass.

**Acceptance:** fresh environment setup documented and tested; same-machine repeated generation yields the same logical records; assignment for a vehicle is stable when fleet size changes; invalid distributions fail clearly; no import errors or empty test suite. Keep a tiny fixture with expected event windows and exposure computed independently of the miner.

**Learn:** dataclasses/enums, invariants, random streams, units, test oracles, transforms versus I/O. No requirement to build a comprehensive vehicle simulator or download data first.

## M1 — first source-to-explorer demonstration

**Current evidence (2026-10-01):** M1 local synthetic implementation and
acceptance checks are verified, including a [short recorded explorer demo](../reports/m1-demo-2026-10-01.mp4).
See [status](status.md) and the [local run report](../reports/m1-local-run-2026-10-01.md).

**JD rows:** 2, 3, 4, 6, 10. Load the small dataset into a local ClickHouse instance through explicit validation and quarantine. Define sample identity, table grain, ordering, provenance, and replay behavior. Store the metric definition in a versioned file initially. Implement hard-braking episodes, valid exposure, and stratified summaries.

Expose bounded queries through a small API and React/TypeScript explorer: cohort summary, drive timeline, event detail. Coordinates and video are optional; do not block the demo on a map.

**Acceptance:** one documented demo command from a prepared environment; source-to-event traceability; fixture counts/rates agree with hand calculations; a repeated load does not change logical counts or rates; invalid rows reconcile to quarantine; zero exposure and insufficient data are explicit. Record dataset size, load time, query latency, hardware, and limitations without inventing performance targets after the run.

**Learn:** SQL grain, storage ordering, event-versus-sample counting, exposure integration, API contracts, server-side aggregation. Create a walkthrough and short recorded demo.

## M2 — reliability, orchestration, and real-data validation

**JD rows:** 2, 3, 9, 10, 11. Introduce Dagster once the source, normalization, events, exposure, and report assets exist. Test duplicates, missing intervals, out-of-order data, interrupted loads, and backfills. Implement a controlled synthetic firmware-semantic change and verify normalization. Add structured run metadata, freshness/quality checks, and an observable failure with a recovery runbook.

Adapt a small real telemetry subset with recorded provenance and usage checks. Inspect available fields and meanings before mapping them. Validate generator behavior on held-out drives if making calibration claims; an unavailable signal remains unavailable.

**Acceptance:** deterministic replay/recovery reconciles counts and metrics; the semantic-change fixture catches a deliberately wrong decode; an operator can diagnose and recover from a failed run. Publish a metric methodology report with population, uncertainty assumptions, stratification, and unresolved biases.

**Learn:** event time, watermarks/gap policy, idempotency boundaries, asset lineage, observability, calibration versus internal consistency.

## M3 — admission control under a byte budget

**JD rows:** 1, 4, 11. Compare FIFO, seeded random, and coverage-aware policies on the same ordered candidate stream and byte budget. Define observable features, variable clip costs, duplicate handling, quotas, and bounded queues. Keep independent exposure accounting and event-collection coverage.

Start with a reproducible offline replay. Add Redpanda/Protobuf when demonstrating sustained rate mismatch, backpressure, consumer recovery, and durable delivery; an offline policy experiment must not be called a streaming system.

**Acceptance:** versioned protocol plus multiple seeded runs; budget never exceeded; report rare-event yield, coverage, rejected bytes, throughput, and uncertainty/variation. Hidden evaluation labels never enter policy features. Include a failure/recovery experiment for any claimed streaming implementation.

**Learn:** constrained selection, sampling bias, queue behavior, budget accounting, precision/recall. Admission success alone does not establish a fleet safety rate.

## M4 — real-image dataset curation

**JD rows:** 4, 5, 8. Confirm image-label pairing and permitted use. Freeze disjoint training, validation, and final evaluation partitions, grouped by source sequence where available. Compare random, stratified, and a justified coverage method at equal data/training budgets. Use existing dataset readers and training libraries.

**Acceptance:** record source identities, selection manifests, seeds, model/training settings, slice definitions and sizes, per-slice outcomes, variation across feasible repeated runs, and losses as well as wins. Use validation for tuning; do not select against final evaluation results.

**Learn:** dataset leakage, correlated examples, confounding, controlled experiments, model/data limitations. Synthetic telemetry and BDD100K remain separate demonstrations unless a real, validated link is established. A shared label or invented join is not such a link.

## M5 — portfolio and interview readiness

**JD rows:** all demonstrated rows. Polish the explorer and setup; produce a short demo, architecture explanation, operational incident walkthrough, and concise measured-results report. Turn only supported findings into resume bullets.

**Acceptance:** another person can follow the runbook; Bryan traces a record through the system, explains the metric, diagnoses an injected defect, modifies a bounded query/transform, and defends key choices. Record actual evidence, not assumed mastery. M5 preparation happens throughout; no need to postpone applications until optional work ships.

## Optional extensions and cut order

Keep correctness, traceability, honest metrics, admission evaluation, and a visible demo. Reduce dataset size and scenario count before removing their validation.

Defer Postgres until mutable control metadata needs transactions/concurrent editing; MinIO until object-storage semantics are exercised; PySpark until a measured workload justifies distributed processing; Terraform/cloud until a real deployment need and approved budget exist. Billion-row targets and cross-database benchmarks are optional experiments, not entry requirements.

Embedding mining, advanced causal inference, power analysis, map/video synchronization, and agent-facing tools follow a demonstrated need. If an agent interface is built, retain a small evaluation set and bounded semantic tools; cut the feature before cutting its validation. AI-assisted development does not require an AI feature in the product.
