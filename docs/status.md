# Current status

Updated 2026-09-29. Repository: FleetLens. This is the single session handoff.

## Current state

- M0 implemented locally: installable Python 3.11 package, validated immutable sample/provenance contracts, stable per-vehicle scenario assignment, a fixed two-drive fixture, and a reproducible JSONL/manifest CLI.
- The [tiny oracle](../tests/fixtures/tiny_expected.json) freezes one synthetic hard-braking episode over [1, 3), excludes the gap [2, 5), and expects 66 m of valid distance over eight seconds. These are independent hand calculations for future M1 metric tests, not miner output or real-fleet evidence.
- Local macOS 3.11.16 checks pass (64 tests). The previous foundation passed hosted Windows/Linux CI run 36535425818 on b95a2af; the new generator has not yet had a hosted CI run.
- No ingestion/quarantine, database, event/exposure transforms, frontend, or services exist. Sample identity is defined; storage replay/deduplication is not implemented.
- [Generator walkthrough](walkthroughs/02-synthetic-fixture.md) delivered. Bryan supplied a partial teach-back on units and exposure; the [learning ledger](learning/README.md) records his actual answer and the remaining corrections.
- OpenRig development pair configured on this Mac: owner and independent reviewer, both using Codex/GPT-6-Sol. [Runbook](openrig.md) covers use, approvals, stop/resume and boundaries. Both reached ready/idle; no M1 task was assigned.

## Verification

This session on macOS Python 3.11.16, in a new `.venv`:

- Pinned development dependencies installed and editable package installed successfully.
- `.venv/bin/python -m pytest -q`: 64 passed.
- `.venv/bin/python -m ruff check .`: passed.
- `.venv/bin/python -m black --check src tests`: passed after formatting.
- `.venv/bin/python -m pip check`: no broken requirements.
- `git diff --check`: passed.
- `.venv/bin/python -m fleetlens.cli --output runs/tiny --fixture`: wrote 11 synthetic samples and a manifest. Before commit, changed JSONL writing to bytes so the manifest hash matches the file on Windows; rerun checks are recorded below.
- Initial system-Python checks could not run because pytest/Ruff/Black were absent; initial sandboxed dependency install could not reach PyPI. An approved network install into the local `.venv` succeeded.

No real dataset was read. No throughput, fleet behavior, or cloud performance was measured. CLI output is tested for same-machine byte identity, not cross-platform byte identity.

OpenRig setup verification later this session:

- Installed Node 22.23.3 alongside the existing Node 24 default, tmux 3.7c, OpenRig 0.6.1 and standalone Codex CLI 0.159.0. Existing ChatGPT login worked.
- Launch plan passed. Initial plan rejected an obsolete empty `hooks` field from installed example documentation; changing it to `plugins` fixed validation before launch.
- `./scripts/openrig doctor --spec openrig/rig.yaml --json`: healthy, matching one pod/two seats. Optional warnings: cmux absent and tmux mouse mode disabled.
- Both native terminals report GPT-6-Sol and both sessions read project instructions. Owner-to-reviewer setup message delivered; reviewer ACK stored in owner mailbox `inbox-20260929175138-33734288`.
- Native sandbox blocked local daemon access. One-time approvals completed the setup checks. Direct ACK delivery encountered the owner's permission prompt; mailbox delivery succeeded. No permanent allow rules or broader network access were configured.
- Full implementation/review queue lifecycle and reboot recovery are not tested. The setup is supervised; local coordination may require prompts.
- `bash -n scripts/openrig` and `git diff --check`: passed after removing generated trailing blank lines. Backup comparison confirmed original AGENTS.md prefix, existing MCP settings and native model retained. Codex also recorded its TUI screen-reader detection flag during first launch.
- Expanded M0 walkthrough teaching points. Bryan later supplied a partial assessment answer; Python product code did not change during OpenRig setup or that assessment. The 64-test result above is from the preceding M0 verification.

Pre-push verification after the Windows newline fix: `.venv/bin/python -m pytest -q` (64 passed), Ruff (passed), Black check (passed), `git diff --check` (passed), and wheel build (passed; wheel contains the CLI entry point and simulation package). Local macOS checks do not substitute for the pending hosted Windows/Linux CI run on the new commit.

## Local resources

Ignored `.venv`, `runs/tiny`, and `runs/fleet-10` remain for development. OpenRig daemon PID 67206 is listening on `127.0.0.1:7433`; tmux seats `dev-owner@fleetlens` and `dev-check@fleetlens` remain running and idle. No support/kernel agents or containers were started. Private prelaunch backups are under `~/.local/state/fleetlens-openrig-backups/20260929T174450Z/`. OpenRig's generated AGENTS.md additions were removed before commit; its managed Codex hooks/workspace trust remain in local user settings.

## Next bounded task

Begin M1 with explicit JSONL ingestion validation and quarantine: parse the CLI's sample/manifest format, reconcile accepted and rejected rows, preserve source identity and reasons, and test malformed rows and replay inputs. Then introduce local ClickHouse with a schema designed around the validated sample grain and bounded queries.

## Source reference

[Migration record](migration.md) documents independent initial commit f733f84 and preserved FleetLoop context. No source code or Git ancestry was copied from FleetLoop. Archived behavior and hardware/dataset observations remain historical.
