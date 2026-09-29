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
  reasons, and writes a reconciled report. Database storage, cross-load replay,
  event/exposure transforms, frontend, and services remain unimplemented.
- Bryan's teach-backs on units, exposure, and replay are recorded in the
  [2026-09-29 learning evidence](learning/2026-09-29.md).
- The optional [OpenRig pair](openrig.md) was configured on this Mac. At last
  check both seats were ready and idle. The reviewer inspected this M1 slice;
  the main session implemented it, while the separate owner seat made no edits.

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

## Local resources

On this Mac, ignored `.venv`, `runs/tiny`, and `runs/fleet-10` remain. At last
check OpenRig daemon PID 67206 and tmux seats `dev-owner@fleetlens` and
`dev-check@fleetlens` were running. No containers were started. See the
[OpenRig runbook](openrig.md) for stop/resume commands and the private backup
location. Do not treat these Mac process IDs as the state of another machine.

## Next bounded task

Add local ClickHouse storage for validated samples, with a schema based on
the source-key grain and a tested replay rule. Prove that two loads of the
same snapshot leave logical counts unchanged before adding event/exposure
transforms and bounded queries.
