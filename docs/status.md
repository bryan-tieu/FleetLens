# Current status

Updated 2026-09-29. This is the current working handoff; dated work and evidence
live in their [history](history.md), [decision](decisions.md), and [learning](learning/README.md) folders.

## Current state

- M0 is implemented locally: installable Python 3.11 package, validated canonical
  sample/provenance contracts, stable per-vehicle scenario assignment, fixed
  two-drive fixture, and reproducible JSONL/manifest CLI.
- The [tiny oracle](../tests/fixtures/tiny_expected.json) freezes one synthetic
  hard-braking episode over [1, 3), excludes the [2, 5) gap, and expects 66 m
  valid distance over eight seconds. These are hand calculations for future M1
  metric checks, not a measured fleet result.
- M1 JSONL ingestion validation now reads the generated manifest/samples,
  checks snapshot integrity, quarantines malformed or duplicate rows with
  reasons, and writes a reconciled report. Local ClickHouse now stores accepted
  synthetic samples in an append-only raw table. A guarded logical count groups
  identical source keys and rejects changed-payload conflicts. Event/exposure
  transforms, frontend, and real-data ingestion remain unimplemented.
- Bryan's teach-backs on units, exposure, and replay are recorded in the
  [2026-09-29 learning evidence](learning/2026-09-29.md). He now identifies
  the shared source key in concurrent loads; physical versus logical counts
  and changed-payload handling remain the next learning check.
- The optional [OpenRig pair](openrig.md) was configured on this Mac. At last
  check both seats were ready and idle. The reviewer inspected this M1 slice;
  the main session implemented it, while the separate owner seat made no edits.
- The Archify v3.0.1 agent skill is vendored under
  [`.agents/skills/archify`](../.agents/skills/archify/SKILL.md) for diagrams.
  It is developer tooling, not a FleetLens product feature or JD evidence.

## Verification and limits

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
  temporary directory. No FleetLens diagram has been authored yet.

## Local resources

On this Mac, ignored `.venv`, `runs/tiny`, and `runs/fleet-10` remain. At last
check OpenRig daemon PID 67206 and tmux seats `dev-owner@fleetlens` and
  `dev-check@fleetlens` were running. The `fleetlens-clickhouse` container and
  named data volume are running locally on port 18123. See the
[OpenRig runbook](openrig.md) for stop/resume commands and the private backup
location; see the [README](../README.md) for ClickHouse stop commands. Do not
treat these Mac process IDs as the state of another machine.

Unrelated untracked `.agents/` and `.archify/` directories appeared during this
session and were left untouched; they are excluded from this increment's commit.

## Next bounded task

Define the versioned hard-braking episode and valid-exposure calculations from
the frozen two-drive fixture. Keep event counts and exposure independent; test
the hand-calculated one episode, 66 m denominator, gap exclusion, and zero
exposure behavior before adding bounded queries or an explorer.
