# Current status

Updated 2026-10-01. This is the current working handoff; dated work and evidence
live in their [history](history.md), [decision](decisions.md), and [learning](learning/README.md) folders.

## Current state

- **M1 engineering is complete locally (2026-10-01).** The
  [45-second silent, captioned recording](../reports/m1-demo-2026-10-01.mp4)
  shows the served synthetic explorer's cohort metrics, vehicle strata,
  braking timeline/source keys, and excluded-gap drive. A macOS helper captured
  only an offscreen WebKit view of the loopback app; it did not access Chrome or
  the desktop screen. Bryan's M1 teach-back remains a separate learning task.
- M0 is implemented locally: installable Python 3.11 package, validated canonical
  sample/provenance contracts, stable per-vehicle scenario assignment, fixed
  two-drive fixture, and reproducible JSONL/manifest CLI.
- The [M0 learning guide](learning/m0-concepts.md) now gathers the concepts
  available from that code: grain/identity/provenance, dataclasses/enums and
  invariants, units, random streams, pure transforms versus I/O, the independent
  oracle, and reproducibility limits. The [ledger](learning/README.md) tracks
  each separately as explained; Bryan's demonstrated understanding still
  depends on his own answers or debugging work.
- A [production bridge](learning/production-bridge.md) now maps 19 implemented
  M0–M1 concepts to production data-engineering patterns (for example idempotent
  consumers, dead-letter queues, Iceberg-style manifests, gaps-and-islands,
  exposure-adjusted rates). Each card also gives the FleetLens limit, an
  evidence-bounded interview claim, and a bridge check. The ledger links each
  row to its cards, and walkthroughs 01–06 have a *Production analogue*
  section. No bridge check has been answered yet; no demonstrated or independent
  learning state is claimed from reading alone.
- The [M1 learning guide](learning/m1-concepts.md) now gives a reading order and
  three checks for replay, event/exposure arithmetic, and source-to-screen
  traceability. The ledger now correctly labels delivered M1 explanations as
  explained and separates unimplemented uncertainty and event-ascertainment
  work. Bryan has not yet demonstrated those M1 checks.
- The M1 concept-navigation update is documentation only: local links resolved
  across 45 active Markdown files and `git diff --check` passed. The code test
  suite was not rerun for this guide.
- The [tiny oracle](../tests/fixtures/tiny_expected.json) freezes one synthetic
  hard-braking episode over [1, 3), excludes the [2, 5) gap, and expects 66 m
  valid distance over eight seconds. These independent hand calculations now
  check the pure M1 metric transform; they are not a measured fleet result.
- M1 JSONL ingestion validation now reads the generated manifest/samples,
  checks snapshot integrity, quarantines malformed or duplicate rows with
  reasons, and writes a reconciled report. Local ClickHouse now stores accepted
  synthetic samples in an append-only raw table. A guarded logical count groups
  identical source keys and rejects changed-payload conflicts. Pure versioned
  hard-braking and valid-exposure transforms now produce per-drive results from
  canonical samples. A guarded, bounded snapshot read reconstructs samples and
  serves Python cohort and drive summaries. Source-file hash and persisted
  load-accounting guards now prevent a mixed or incomplete stored snapshot from
  yielding a rate. A bounded read-only API serves cohort, drive, and event JSON
  from that guard. A React/TypeScript explorer displays cohort and vehicle
  strata, drive intervals, and event source keys. A one-command local demo
  prepares the fixture and serves the API and explorer. Real-data ingestion
  remains unimplemented.
- Bryan's teach-backs on units, exposure, and replay are recorded in the
  [2026-09-29 learning evidence](learning/2026-09-29.md). He now identifies
  the shared source key in concurrent loads; physical versus logical counts
  and changed-payload handling remain the next learning check.
- The optional [OpenRig pair](openrig.md) was configured on this Mac. The owner
  seat implemented the pure metric and guarded stored-summary increments;
  dev-check independently reviewed them and the API. Its API review found two
  response-contract defects, and its focused recheck found a caller-limit
  classification defect; all three have regression coverage in the current
  working tree.
- The Archify v3.0.1 agent skill is vendored under
  [`.agents/skills/archify`](../.agents/skills/archify/SKILL.md) for diagrams.
  It is developer tooling, not a FleetLens product feature or JD evidence.
- A [source-backed architecture map](../.archify/architecture-fleetlens-end-to-end-20260929-154317/fleetlens-end-to-end.html)
  traces the 2026-09-29 synthetic JSONL, validation, quarantine, and
  ClickHouse paths; its planned labels for metrics, API, and explorer are
  historical and the implementation now exists. See its
  [walkthrough](walkthroughs/05-architecture-map.md).

## Verification and limits

- 2026-10-01 M1 closure recheck: 90 regular tests passed with six service-gated
  skips; all six live ClickHouse tests passed; Ruff, Black, TypeScript/Vite
  build, and wheel build passed. An independent dev-check review reproduced a
  malformed dataset/snapshot selector returning HTTP 422; the API now applies
  the shared storage selector validator during request parsing and returns 400
  before any store call. Focused API/stored tests passed (11); dev-check's
  focused recheck reproduced both 400 responses and found no remaining issue
  in that correction. The [local run report](../reports/m1-local-run-2026-10-01.md)
  records 5,967 generated bytes, 0.162 s load time, three 0.0085–0.0118 s
  guarded reads, 88 cumulative physical rows, 11 logical rows, one episode,
  and 66 m on the small synthetic fixture. These are local observations.
- The recorded explorer demo was encoded as a 45-second, 1280×720 silent MP4
  (1,315,054 bytes). Five extracted frames were inspected for the cohort,
  strata, event timeline, source sequences, and gap state. The actual served
  app supplied the images; captions were overlaid during capture. This is a
  visual walkthrough, not a usability or interaction-latency measurement.
  Recording exposed a drive-switch race: the gap drive briefly requested the
  prior brake event and received 404. Clearing the selected event/detail before
  changing drives fixed it; a re-recording showed only the intended cohort,
  brake-drive/event, and gap-drive requests. The TypeScript/Vite build passed
  after the fix.
- M1 explorer/demo increment: Chrome inspection against the one-command local
  demo confirmed cohort provenance/accounting, vehicle strata, timeline, event
  sequences 1–3, and the zero-event gap drive. The TypeScript/Vite build passed.
  The served demo on an Apple M2 MacBook Air (8 cores, 16 GB, arm64 macOS)
  generated 5,967 bytes, loaded the fixture in
  0.0357 s, and measured three guarded cohort reads at 0.01665, 0.01482, and
  0.02158 s. Six cumulative loads left 66 physical rows, 11 logical rows,
  one episode, and 66 m. These tiny local observations are not throughput or
  fleet-safety measurements. Full regular suite: 90 passed, six service-gated
  skips; Ruff, Black, and `git diff --check` passed. Dev-check's API findings
  were fixed with regression tests; stored-data contract and nonfinite
  output errors now return fixed HTTP 422 JSON, while a caller-selected read
  limit exceeded by a valid snapshot returns HTTP 400 `snapshot_exceeds_limit`.
  All six live ClickHouse
  integration tests passed after this increment. A wheel build passed, and
  local links resolved across 43 active Markdown files. The final demo command
  started both servers and Ctrl+C closed both loopback listeners.
- M1 API increment: three focused WSGI contract tests passed without a socket
  or database. They cover fixture summary/event lineage, incomplete and conflict
  states, request bounds, and missing events. The full regular suite passed
  (87 tests, 6 service-gated skips); Ruff, Black, and `git diff --check`
  passed. An isolated live ClickHouse fixture produced API `200 OK`, 11 samples,
  one episode, 66 m, and `source_complete=true`. The wheel built with the
  `fleetlens-api` entry point, API module, and fourth SQL migration. The API has
  no measured concurrency or external deployment claim.
- Stored metric increment: initial live isolated ClickHouse checks passed, but
  independent dev-check review found mixed source hashes and absent source
  completeness reporting. Those were corrected with a source-hash guard and
  load receipts. Six live integration tests passed, including the reviewer
  regressions and a missing-receipt case. The 2026-09-30 regular suite passed
  (84 tests, 6 service-gated skips); Ruff, Black, and `git diff --check` passed.
  Dev-check independently reran all six live tests and probed inconsistent
  receipt counts and hashes; its re-review found no remaining issue in those
  corrected paths. The complete fixture cohort produces one
  episode, 66 m, eight seconds, and `100000 / 66` episodes per 100 km; this is
  generated-data arithmetic, not a fleet measurement.
- M1 metric increment: `.venv/bin/python -m pytest -q` passed (79 passed,
  2 ClickHouse-service-gated skips); Ruff, Black, and `git diff --check`
  passed. The 6 metric tests cover the frozen fixture and edge cases. No real
  data, ClickHouse metric query, or cohort rate has been measured. Independent
  review found no code or metric-behavior defect. A subsequent documentation
  gap was corrected in the versioned definition; focused metric tests (6),
  local links, and `git diff --check` passed after that docs-only change.
  Dev-check's focused recheck found no inconsistency in the affected definition.
- 2026-09-30 production bridge (docs only): every local link and heading
  anchor resolved across 45 active Markdown files, and `git diff --check` passed.
  No code changed, so the test suite was not rerun for this update.
- 2026-09-30 documentation audit: `.venv/bin/python -m pytest -q` passed
  (73 passed, 2 ClickHouse-service-gated skips). M0 acceptance artifacts and
  test coverage were checked against the working tree. The learning guide is
  an explanation, not a new learning assessment or metric implementation.
- Local macOS Python 3.11.16, last checked before the prior push:
  `.venv/bin/python -m pytest -q` (64 passed), Ruff and Black (passed),
  `pip check` (no broken requirements), and wheel build (passed). The wheel
  contains the CLI entry point and simulation package. JSONL now writes exact
  UTF-8 bytes so its manifest hash is valid across newline conventions.
- M1 ingestion local check: `.venv/bin/python -m pytest -q` (73 passed),
  `.venv/bin/ruff check src tests` (passed), and
  `.venv/bin/black --check src tests` (passed). A wheel build passed and its
  `fleetlens-validate` entry point was inspected. The fixture round trip and
  invalid-row/accounting cases are covered. Hosted CI for this change is pending.
- Local ClickHouse 26.3.36.6 ran in Docker for the storage increment. The
  isolated integration test passed: first fixture load 11 physical/11 logical,
  second load 22 physical/11 logical; two concurrent additional loads retained
  11 logical; a same-key changed payload raised a conflict. With the service
  enabled, two focused integration tests passed, including concurrent first-load
  migration serialization. The regular suite passed (73 tests, 2 service-gated
  skips); Ruff, Black, and `git diff --check`
  passed. The wheel built with all three SQL migrations and `fleetlens-load`.
  The existing local table was upgraded without deleting rows, and the live
  test confirmed a `123456` microsecond timestamp round trip.
  Local links resolved in 33 active Markdown files. Independent OpenRig review
  found a bypassable logical count and concurrent migration markers; both were
  fixed, and its second pass found no remaining issue in this bounded slice.
- Independent OpenRig review found unsupported wire versions and potentially
  revealing parser diagnostics. Both were fixed with strict version gates and
  safe rejection reasons; regression tests pass. The second reviewer pass found
  no remaining issue in this bounded candidate.
- Earlier foundation GitHub Actions run 36535425818 on b95a2af passed on
  Windows and Linux. A hosted result for the generator commit has not been
  recorded here. Same-machine CLI byte identity was tested; cross-platform
  identity, real fleet behavior, throughput, and cloud performance were not.
- OpenRig 0.6.1 doctor reported healthy with one pod/two seats. An independent
  candidate review and second pass completed for this increment. A full queue
  cycle and reboot recovery remain unverified.
- Dated entries are partitioned by topic and day: history, decisions, learning,
  and session plans each have their own folder. The [dated history](history/2026-09-29.md)
  records the documentation checks: all six prior topic/date sections were
  preserved, links in 31 active Markdown files resolved, and `git diff --check`
  passed. No code checks were needed for this documentation change.
- The project instructions now explicitly require engineering explanations,
  decision rationale, and a concrete record walkthrough during each substantial
  increment, rather than waiting for a milestone recap. This docs-only update
  passed `git diff --check` and a local-link scan of 32 active Markdown files.
- Archify package setup passed `node .agents/skills/archify/bin/archify.mjs doctor`
  on local Node.js 24.21.0; its demo command generated standalone HTML in a
  temporary directory. The FleetLens architecture map is pinned to commit
  `14f4b6d3ee5c968ac5b44b4695c7d6e704ef1b55`; Archify showcase
  `finalize` passed validation, delivery, strict check, and browser check with
  no diagnostics. Its visual check passed automated layout/theme checks and
  the light desktop capture was inspected. Planned components were not run.

## Local resources

On this Mac, ignored `.venv`, `runs/tiny`, and `runs/fleet-10` remain. On
2026-09-30, the FleetLens OpenRig daemon and both existing seats were restored
after a mistaken permission cleanup; `status` reported one rig with two nodes.
FleetLens trust and four OpenRig activity hooks are present in the local Codex
config. Separately, macOS ScreenCapture, Accessibility, and AppleEvents grants
were reset for ChatGPT/Codex computer-use apps; Codex's Chrome and computer-use
plugins and the Google Chrome native bridge were disabled. The
`fleetlens-clickhouse` container and named data volume were last observed
running locally on port 18123. See the
[OpenRig runbook](openrig.md) for stop/resume commands and the private backup
location; see the [README](../README.md) for ClickHouse stop commands.

The `.agents/` skill and `.archify/` diagram directories are committed
separately from the ClickHouse storage commit.
The local M1 demo API and Vite processes started for the recording were stopped
with Ctrl+C after the final capture.

## Next bounded task

Plan the first bounded M2 reliability increment: a reproducible interrupted
load/recovery case with explicit run state and reconciliation. Bryan's
source-to-rate teach-back remains pending and should be assessed separately
from completed M1 engineering.
