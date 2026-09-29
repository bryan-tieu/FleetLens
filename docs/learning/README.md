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

## 2026-09-29 — synthetic generator walkthrough delivered

- Artifact: [synthetic fixture walkthrough](../walkthroughs/02-synthetic-fixture.md), current working tree.
- AI implemented the generator and explained identity-derived random assignment, the independent oracle, and the gap policy. The combined M0 competency is now **explained**; Bryan has not yet supplied a teach-back or debugging answer.
- Next optional check: explain why adding earlier vehicles changes assignments with a shared random stream but not this hash scheme, and why the [2, 5) interval contributes no exposure.

## 2026-09-29 — M0 takeaways and agent workflow

- Bryan asked what engineering he should take away from M0 while using agents.
- Expanded the [generator walkthrough](../walkthroughs/02-synthetic-fixture.md) with row grain, immutable dataclasses and validation, source identity versus decoded values, per-vehicle hashing, pure transforms versus I/O, independent expected results, and evidence limits.
- Configured the OpenRig pair to teach each increment and request an independent candidate review. Its setup does not establish review quality or Bryan's understanding.
- Actual teach-back answers remain absent; no demonstrated/independent competency state is added.
- Next optional checks: diagnose a 36 km/h → `speed_mps=36` error and explain why filling the fixture's missing interval would violate the frozen exposure policy.

## 2026-09-29 — M0 teach-back on units and the missing interval

- Prompt: identify the repair point for a 36 km/h source value mislabeled as `speed_mps=36`, and explain how filling the missing interval would affect the braking rate.
- Bryan's answer (unassisted): "You would fix it at the boundary which in this case is between the sample and the piece of code that actually reads the data coming from the sample. It could distort the braking rate because the detector and fixture don't have ground truth. They both have different calculations for braking distance"
- Correct insight: he located unit repair at a data boundary and recognized that a distance error changes the reported rate.
- Correction: the source adapter converts 36 km/h to 10 m/s **before** constructing a `CanonicalSample`; consumers of that sample read canonical values. The fixture does have frozen synthetic ground truth from hand calculation; the event detector and exposure transform do not exist yet. Adding 30 m across [2, 5) changes the valid-distance denominator from 66 m to 96 m while the one episode numerator stays fixed, lowering the rate. This is exposure distance, not braking distance.
- Assessment: partial reasoning on both checks; neither full signal semantics nor exposure competency is marked demonstrated. No code/debugging change was attempted.
- Next optional check: trace `36 km/h -> 10 m/s` through the source adapter into the canonical sample, then compare `1/66` with `1/96` episodes per meter and explain which rate is smaller. Revisit during the M1 ingestion and exposure increments.

## 2026-09-29 — rate denominator clarification

- After a plain-language example of one event over a shorter versus longer distance, Bryan answered: "Events per distance drops."
- Correct: with a fixed event count, increasing the distance denominator lowers the rate. This demonstrates the direction of the denominator effect with assistance from the example.
- Exposure competency remains **not assessed** overall: this answer does not yet establish that Bryan can apply the gap exclusion or compute valid exposure independently.
- Next check during M1: given the fixture timestamps, identify which intervals count toward 66 m and explain why [2, 5) is excluded.
