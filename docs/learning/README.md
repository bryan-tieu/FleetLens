# Learning record

This records Bryan's demonstrated understanding separately from implementation progress. AI writing code is expected. Reading an explanation or passing tests does not automatically establish understanding.

## States

**Not assessed** -> **explained** -> **demonstrated** -> **independent**.
"Explained" means a walkthrough was delivered; "demonstrated" requires Bryan's own correct explanation or diagnosis; "independent" requires a bounded change/debugging task with the assistance level recorded. States can be revisited when evidence exposes a gap.

## Competency ledger

| Competency | Relevant milestone | Current state | Evidence / next check |
|---|---|---|---|
| Python contracts, validation, random streams | M0 | Explained | Foundation and generator walkthroughs delivered; explain why changing fleet size should not change vehicle 7 |
| Signal units and firmware semantics | M0–M2 | Not assessed | Bryan identified a boundary for unit repair, but placed it downstream of the canonical sample; trace wire value -> adapter -> canonical value next |
| SQL grain, joins, event episodes | M1 | Not assessed | Explain sample counts versus event counts and a duplicating join |
| Exposure, strata, uncertainty | M1–M2 | Not assessed | Bryan identified that the gap could distort the rate; next compute the valid-distance denominator and direction of the distortion |
| ClickHouse schema and queries | M1–M2 | Not assessed | Defend ordering against a real query and inspect its plan |
| Replay, backfill, late data, quarantine | M1–M2 | Explained | Bryan independently diagnosed append-only duplicates; next explain concurrent loads and same-key changed values at the storage boundary |
| Dagster assets and operational checks | M2 | Not assessed | Trace a failed upstream check to downstream behavior |
| Admission budgets and selection bias | M3 | Not assessed | Explain how selection changes observed event prevalence |
| Training/evaluation isolation | M4 | Not assessed | Find leakage in a proposed selection experiment |
| API/UI traceability and bounded queries | M1–M5 | Not assessed | Trace a chart value to its source records |
| Architecture and interview ownership | Throughout | Not assessed | Explain one choice, its alternative, and its limitation |

No assessment has been completed during the documentation migration.

## Record evidence by day

Add actual learning interactions to `YYYY-MM-DD.md` in this folder. For each interaction record:
- Date, feature/commit or working-tree snapshot, question/task.
- Bryan's answer (quote only words he actually supplied), assistance level.
- What was correct, what needs correction, and a concise explanation.
- State change justified by that evidence.
- One next exercise and when to revisit it.

Keep this concise. Detailed Q&A belongs in ../interview/; feature explanations belong in ../walkthroughs/. Do not record hypothetical model answers as Bryan's responses.

## Review rhythm

After a feature: one short explanation or diagnostic task. At a milestone: trace the full data path and investigate one failure. Before an interview: revisit weak areas and practice a bounded Python/SQL change without generated scaffolding if Bryan wants that practice. Do not quiz after every trivial edit.

Dated evidence: [2026-09-29](2026-09-29.md).
