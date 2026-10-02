# OpenRig development pair

OpenRig is optional development tooling, separate from FleetLens's telemetry
runtime. Installed on this Mac on 2026-09-29: OpenRig 0.6.1, Node 22.23.3,
Codex CLI 0.159.0, and tmux 3.7c. Node 24 remains the user's default. The
repository wrapper selects Node 22 for OpenRig, including the standalone Codex
binary installed alongside it. Both seats currently inherit GPT-6-Sol from the
user's Codex configuration; the rig does not pin or replace the user's model.

## Roles and boundaries

- `dev-owner@fleetlens`: implements one assigned increment, verifies it, explains
  it, and requests review of the exact candidate.
- `dev-check@fleetlens`: independently inspects that candidate and returns
  concrete findings. The reviewer follows a no-product-edits instruction; both
  sessions use the normal workspace sandbox, so this is a role boundary, not
  a separate filesystem access control.

Definitions live in [../openrig/rig.yaml](../openrig/rig.yaml). The
[culture](../openrig/CULTURE.md) preserves the project's teaching contract,
requires an explicit task, and prevents startup from automatically starting M1.
Only the owner edits shared product files during assigned implementation. The
reviewer must identify the reviewed commit or diff, including untracked files;
agreement alone is not a correctness check.

## Open the existing sessions

From the FleetLens repository in a normal terminal:

```bash
./scripts/openrig status
./scripts/openrig ps --nodes --rig fleetlens
./scripts/openrig tui
tmux attach -t dev-owner@fleetlens
```

Attach to `dev-check@fleetlens` to inspect the reviewer instead. In tmux,
**Ctrl-b, then d** detaches and leaves the session running. Closing a viewing
terminal does not stop the agents. This setup has no support/kernel agents,
so use plain `tui`, not `tui --shared` (which expects a kernel terminal).

The `scripts/openrig` wrapper requires `fnm` on PATH and Node 22 installed via
fnm. Direct `rig` commands are available after `fnm use 22`; the wrapper lets
you leave your default Node version alone. This setup is verified on this Mac;
native Windows is not supported by OpenRig 0.6.1.

## Assign a bounded task

Talk to the owner's terminal or send a message from a normal terminal. Example
for the next engineering increment (this command has not been executed):

```bash
./scripts/openrig send dev-owner@fleetlens 'From Bryan: implement the M1 JSONL validation and quarantine increment in docs/status.md. Preserve existing M0 edits. Define accepted/rejected input accounting and test malformed rows. Keep changes local. Track the task in the queue, ask dev-check for independent review of the exact candidate, and explain one record through the result. Do not introduce ClickHouse in this increment.'
```

Inspect actual work through:

```bash
./scripts/openrig queue list --destination dev-owner@fleetlens
./scripts/openrig queue list --destination dev-check@fleetlens
```

Queue entries hold durable task state; a successful send only means terminal
delivery. Review the artifact and evidence before treating a task as complete.

## Permissions and pauses

The launch uses `workspace-write`, with the native default approval behavior.
The sandbox blocks the local daemon just as it blocks other network access.
When a `rig` call returns unreachable/partial identity from inside a seat, the
agent should request a one-time native approval for the intended coordination
command, rather than assume the healthy host daemon has stopped. Inspect the
command and approve it in that agent's terminal. No persistent allow rules or
broader network permissions were added in setup.

On 2026-09-30, the FleetLens pair and daemon were briefly stopped and their
Codex trust/hooks removed after a misunderstanding about which permissions
Bryan meant. They were restored from the saved rig state and exact hook
configuration; the daemon and two seats are running again. The FleetLens trust
entry was already present in the prelaunch backup, so it was not a new M1
approval. One-time M1 command approvals did not create persistent allow rules.
The screen/Chrome permissions were revoked separately: macOS ScreenCapture,
Accessibility, and AppleEvents approvals for the ChatGPT and computer-use apps
were reset, Codex Chrome/computer-use plugins disabled, and the Google Chrome
native-messaging bridge disabled. Those changes do not remove OpenRig access.

OpenRig refuses normal sends to a seat awaiting a permission decision, so
resolve that prompt before retrying delivery. Do not relaunch duplicate seats
to fix a pending prompt. This initial setup is supervised, not an unattended
automation claim. Ordinary permission handling can add coordination overhead.

## Stop and resume

To stop this pair after its assigned work is finished:

```bash
./scripts/openrig down fleetlens --snapshot
```

If stopping OpenRig entirely, then run `./scripts/openrig daemon stop`. This
does not uninstall the tools. For a stopped daemon and pair, resume with:

```bash
./scripts/openrig daemon start --no-kernel --host 127.0.0.1
./scripts/openrig up fleetlens --existing --cwd .
```

Use `status` first; do not restart an already running daemon or pair. Retain
`--no-kernel` when starting the daemon to keep this setup at two agents. Snapshot
recovery across a machine reboot has not been tested.

## Local changes and evidence

The daemon listens on `127.0.0.1:7433`, with state under `~/.openrig`. Its
managed hooks and FleetLens trust entry were added to `~/.codex/config.toml`.
Codex also recorded its TUI screen-reader detection completion during startup.
During launch, OpenRig appended marked generated guidance blocks to `AGENTS.md`.
Those generated blocks were removed before commit; the original FleetLens
instructions remain in Git. Future local launches may append them again. The
wrapper, agent definitions, culture
and this runbook are project source; `.openrig/` generated files are ignored.

Prelaunch settings backups are private, outside the repo:
`~/.local/state/fleetlens-openrig-backups/20260929T174450Z/`. Restore only a
specific setup change after checking for later edits; copying the whole backup
over a newer config could discard unrelated work. No credentials were printed
or added to Git. No extra external MCP services were selected by this rig.

OpenRig's `doctor --spec openrig/rig.yaml --json` reports healthy and confirms
the live one-pod/two-seat topology. Optional warnings remain for absent cmux
and disabled tmux mouse support. The two agents reached native prompts and read
the project instructions. The owner delivered a setup message to the reviewer.
The reviewer's direct ACK met an owner permission prompt, so it successfully
used the owner's mailbox instead (`inbox-20260929175138-33734288`). Both seats
then became idle with no assigned project work. That informational ACK remains
in the mailbox. Later on 2026-09-29, the reviewer inspected the uncommitted
M1 ingestion increment. It found unsupported wire-version acceptance and raw
value leakage in rejection reasons; the main coding session fixed both. The
reviewer rechecked the candidate and found no remaining issue. The separate
owner seat made no product edits. A complete queue-driven implementation and
review cycle, and reboot recovery, remain unverified.

References: [OpenRig getting started](https://github.com/mvschwarz/openrig/blob/main/docs/reference/getting-started.md)
and [Codex CLI](https://learn.chatgpt.com/docs/codex/cli). Installed behavior is
the evidence above; repository documentation may describe a different release.
