# Learning record

This records Bryan's demonstrated understanding separately from implementation progress. AI writing code is expected. Reading an explanation or passing tests does not automatically establish understanding.

The [M0 learning guide](m0-concepts.md) gathers every concept available from the implemented foundation, with examples, code links, limits, and optional checks.

The [M1 learning guide](m1-concepts.md) gives a short reading order from ingestion and replay through the metric, guarded summaries, API, and explorer, followed by three source-to-screen checks.

The [production bridge](production-bridge.md) connects every implemented M0–M1 concept to the production pattern it corresponds to (for example append-only raw storage → at-least-once delivery with an idempotent consumer), states where FleetLens's version stops, and gives an evidence-bounded interview claim. Its **bridge checks** are the preferred way to move a row from explained to demonstrated: the answer must connect the FleetLens mechanism, the production pattern, and one difference between them.

## States

**Not assessed** -> **explained** -> **demonstrated** -> **independent**.
"Explained" means a walkthrough was delivered; "demonstrated" requires Bryan's own correct explanation or diagnosis; "independent" requires a bounded change/debugging task with the assistance level recorded. States can be revisited when evidence exposes a gap.

## Competency ledger

| Competency | Relevant milestone | Current state | Evidence / next check | Production bridge |
|---|---|---|---|---|
| Data grain, source identity, provenance | M0 | Explained | M0 guide and record trace delivered; trace one fixture key and distinguish identity from values | [B1](production-bridge.md#b1-grain-and-source-identity), [B2](production-bridge.md#b2-provenance-and-lineage) |
| Dataclasses, enums, validation invariants | M0 | Explained | Foundation walkthrough delivered; diagnose a valid number with the wrong unit versus an invalid field | [B4](production-bridge.md#b4-contracts-and-runtime-invariants), [B7](production-bridge.md#b7-safe-diagnostics-and-strict-parsing) |
| Seeded assignment and random streams | M0 | Explained | Generator walkthrough delivered; explain why fleet growth does not shift an existing assignment | [B3](production-bridge.md#b3-deterministic-hash-assignment-and-snapshot-identity) |
| Pure transforms versus I/O, reproducibility | M0 | Explained | Generator/CLI boundary and byte-identity check documented; trace object -> JSONL -> manifest and name crash limit | [B13](production-bridge.md#b13-pure-transformations-separated-from-io), [B8](production-bridge.md#b8-manifests-content-hashes-and-snapshot-integrity), [B18](production-bridge.md#b18-reproducible-builds-and-verification-evidence) |
| Independent test oracle and fixture arithmetic | M0–M1 | Explained | Hand-calculated episode and 66 m frozen; independently recompute both drives before M1 metric assessment | [B17](production-bridge.md#b17-independent-test-oracle) |
| Signal units and firmware semantics | M0–M2 | Explained | Bryan located conversion while reading but has not independently named the adapter-before-sample boundary; trace 36 km/h -> 10 m/s next | [B5](production-bridge.md#b5-units-and-the-normalize-once-boundary), [B6](production-bridge.md#b6-time-utc-event-time-and-precision) |
| SQL grain and event episodes | M1 | Explained | [M1 guide](m1-concepts.md), episode transform, and grouped stored read delivered; explain sample counts versus event counts and why a many-to-many join can duplicate either | [B10](production-bridge.md#b10-append-only-raw-storage-with-a-guarded-logical-read), [B14](production-bridge.md#b14-event-episodes-from-interval-data) |
| Exposure and vehicle strata | M1 | Explained | [M1 guide](m1-concepts.md) and cohort sum-before-division delivered; recompute valid distance, gap effect, and vehicle versus cohort rates | [B15](production-bridge.md#b15-exposure-normalized-rates-and-undefined-denominators), [B16](production-bridge.md#b16-versioned-metric-definitions) |
| Uncertainty and event ascertainment | M1–M2 | Not assessed | No uncertainty estimate or real event-collection validation exists; explain why this fixture cannot support a fleet-safety claim | [B15](production-bridge.md#b15-exposure-normalized-rates-and-undefined-denominators) |
| ClickHouse schema and queries | M1–M2 | Explained | Storage walkthrough delivered; trace raw versus logical grain and defend source-key sorting against a drive lookup | [B10](production-bridge.md#b10-append-only-raw-storage-with-a-guarded-logical-read), [B12](production-bridge.md#b12-versioned-schema-migrations) |
| Replay, backfill, late data, quarantine | M1–M2 | Explained | Bryan now identifies that concurrent loaders share the same source key; next trace physical/logical counts and changed-payload conflicts | [B9](production-bridge.md#b9-validation-quarantine-and-reconciliation), [B10](production-bridge.md#b10-append-only-raw-storage-with-a-guarded-logical-read), [B11](production-bridge.md#b11-concurrency-and-the-check-then-act-race) |
| Dagster assets and operational checks | M2 | Not assessed | Trace a failed upstream check to downstream behavior | [Planned](production-bridge.md#next-bridges-planned-not-implemented) |
| Admission budgets and selection bias | M3 | Not assessed | Explain how selection changes observed event prevalence | [Planned](production-bridge.md#next-bridges-planned-not-implemented) |
| Training/evaluation isolation | M4 | Not assessed | Find leakage in a proposed selection experiment | [Planned](production-bridge.md#next-bridges-planned-not-implemented) |
| Bounded API contracts and source traceability | M1 | Explained | [API walkthrough](../walkthroughs/08-metric-api.md) delivered; trace the fixture event response to sequences 1, 2, and 3 | [B19](production-bridge.md#b19-bounded-read-api-and-client-views) |
| Explorer/UI traceability | M1–M5 | Explained | [Explorer walkthrough](../walkthroughs/09-explorer-and-demo.md) delivered; Bryan has not yet traced a displayed chart value himself | [B19](production-bridge.md#b19-bounded-read-api-and-client-views) |
| Architecture and interview ownership | Throughout | Explained | [Source-to-explorer map](../walkthroughs/05-architecture-map.md) delivered; explain one boundary, its alternative, and its limitation | [Pipeline overview](production-bridge.md#the-pipeline-named-in-production-terms) |

The M0 rows marked **explained** record delivered material, not independent mastery. Bryan's actual partial teach-backs on units, gap effects, and replay are preserved in the dated evidence; none establishes every M0 skill independently.

## Record evidence by day

Add actual learning interactions to `YYYY-MM-DD.md` in this folder. For each interaction record:
- Date, feature/commit or working-tree snapshot, question/task.
- Bryan's answer (quote only words he actually supplied), assistance level.
- What was correct, what needs correction, and a concise explanation.
- State change justified by that evidence.
- One next exercise and when to revisit it.

Keep this concise. Detailed Q&A belongs in ../interview/; feature explanations belong in ../walkthroughs/. Do not record hypothetical model answers as Bryan's responses.

## Review rhythm

After a feature: one short explanation, diagnostic, or bridge check. At a milestone: trace the full data path and investigate one failure. Before an interview: revisit weak areas and practice a bounded Python/SQL change without generated scaffolding if Bryan wants that practice. Do not quiz after every trivial edit.

Dated evidence: [2026-09-29](2026-09-29.md), [2026-09-30](2026-09-30.md).
