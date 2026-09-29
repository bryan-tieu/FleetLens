# Current status

Updated 2026-09-29. This is the current working handoff; dated work and evidence
live in the [daily record](daily/README.md).

## Current state

- M0 is implemented locally: installable Python 3.11 package, validated canonical
  sample/provenance contracts, stable per-vehicle scenario assignment, fixed
  two-drive fixture, and reproducible JSONL/manifest CLI.
- The [tiny oracle](../tests/fixtures/tiny_expected.json) freezes one synthetic
  hard-braking episode over [1, 3), excludes the [2, 5) gap, and expects 66 m
  valid distance over eight seconds. These are hand calculations for future M1
  metric checks, not a measured fleet result.
- No ingestion/quarantine, database, event/exposure transforms, frontend, or
  services exist. Source identity is defined; storage replay and deduplication
  remain unimplemented.
- Bryan's partial teach-back on units and exposure is recorded in the
  [2026-09-29 learning evidence](daily/2026-09-29.md#learning-evidence).
- The optional [OpenRig pair](openrig.md) was configured on this Mac. At last
  check both seats were ready and idle; no M1 task was assigned.

## Verification and limits

- Local macOS Python 3.11.16, last checked before the prior push:
  `.venv/bin/python -m pytest -q` (64 passed), Ruff and Black (passed),
  `pip check` (no broken requirements), and wheel build (passed). The wheel
  contains the CLI entry point and simulation package. JSONL now writes exact
  UTF-8 bytes so its manifest hash is valid across newline conventions.
- Earlier foundation GitHub Actions run 36535425818 on b95a2af passed on
  Windows and Linux. A hosted result for the generator commit has not been
  recorded here. Same-machine CLI byte identity was tested; cross-platform
  identity, real fleet behavior, throughput, and cloud performance were not.
- OpenRig 0.6.1 doctor reported healthy with one pod/two seats. Startup and
  message/mailbox delivery were exercised with one-time approvals; a full
  implementation-to-review queue cycle and reboot recovery remain unverified.
- This session moved 6 history, 5 decision, and 5 learning entries into one
  dated file per day, together with the completed first session plan. Content
  preservation, active Markdown link targets, and diff whitespace were checked;
  results are in the [dated entry](daily/2026-09-29.md#partition-daily-entries-by-date).

## Local resources

On this Mac, ignored `.venv`, `runs/tiny`, and `runs/fleet-10` remain. At last
check OpenRig daemon PID 67206 and tmux seats `dev-owner@fleetlens` and
`dev-check@fleetlens` were running. No containers were started. See the
[OpenRig runbook](openrig.md) for stop/resume commands and the private backup
location. Do not treat these Mac process IDs as the state of another machine.

## Next bounded task

Begin M1 with explicit JSONL ingestion validation and quarantine. Parse the
CLI's sample/manifest format, reconcile accepted and rejected rows, preserve
source identity and rejection reasons, and test malformed rows and replay
inputs. Then introduce local ClickHouse with a schema based on the validated
sample grain and bounded queries.
