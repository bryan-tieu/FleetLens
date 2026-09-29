# Learning record

This records Bryan's demonstrated understanding separately from implementation progress. AI writing code is expected. Reading an explanation or passing tests does not automatically establish understanding.

## States

**Not assessed** -> **explained** -> **demonstrated** -> **independent**.
"Explained" means a walkthrough was delivered; "demonstrated" requires Bryan's own correct explanation or diagnosis; "independent" requires a bounded change/debugging task with the assistance level recorded. States can be revisited when evidence exposes a gap.

## Competency ledger

| Competency | Relevant milestone | Current state | Evidence / next check |
|---|---|---|---|
| Python contracts, validation, random streams | M0 | Not assessed | Explain why changing fleet size should not change vehicle 7 |
| Signal units and firmware semantics | M0–M2 | Not assessed | Trace wire value -> canonical value; detect double normalization |
| SQL grain, joins, event episodes | M1 | Not assessed | Explain sample counts versus event counts and a duplicating join |
| Exposure, strata, uncertainty | M1–M2 | Not assessed | Compute a tiny rate including zero exposure and a missing interval |
| ClickHouse schema and queries | M1–M2 | Not assessed | Defend ordering against a real query and inspect its plan |
| Replay, backfill, late data, quarantine | M1–M2 | Not assessed | Diagnose duplicates after an interrupted load |
| Dagster assets and operational checks | M2 | Not assessed | Trace a failed upstream check to downstream behavior |
| Admission budgets and selection bias | M3 | Not assessed | Explain how selection changes observed event prevalence |
| Training/evaluation isolation | M4 | Not assessed | Find leakage in a proposed selection experiment |
| API/UI traceability and bounded queries | M1–M5 | Not assessed | Trace a chart value to its source records |
| Architecture and interview ownership | Throughout | Not assessed | Explain one choice, its alternative, and its limitation |

No assessment has been completed during the documentation migration.

## Append evidence here

For each actual learning interaction record:
- Date, feature/commit or working-tree snapshot, question/task.
- Bryan's answer (quote only words he actually supplied), assistance level.
- What was correct, what needs correction, and a concise explanation.
- State change justified by that evidence.
- One next exercise and when to revisit it.

Keep this concise. Detailed Q&A belongs in ../interview/; feature explanations belong in ../walkthroughs/. Do not record hypothetical model answers as Bryan's responses.

## Review rhythm

After a feature: one short explanation or diagnostic task. At a milestone: trace the full data path and investigate one failure. Before an interview: revisit weak areas and practice a bounded Python/SQL change without generated scaffolding if Bryan wants that practice. Do not quiz after every trivial edit.

## 2026-09-29 — foundation walkthrough delivered

- Artifact: [Python foundation walkthrough](../walkthroughs/01-python-foundation.md), current working tree.
- AI implemented the environment and contracts and traced one canonical sample with its source key and units.
- Contract/validation and canonical-unit separation explanations delivered. Combined M0 competency remains not assessed: random streams have not been implemented or explained.
- Bryan has not supplied a teach-back answer or debugging result. No demonstrated/independent assessment is claimed.
- Next optional check: explain why speed_mps=36 could be valid structurally but wrong semantically, and identify the correct conversion boundary.
