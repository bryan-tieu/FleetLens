# FleetLens pair

The repository's AGENTS.md is the project authority. Read docs/status.md,
docs/roadmap.md and docs/operating-manual.md before doing assigned work.
Preserve all existing changes in the working tree.

There are exactly two project roles: dev-owner implements; dev-check reviews.
Do not create additional seats or delegate to additional agents. Work only on
an explicitly assigned, bounded outcome. Startup is orientation only: identify
your role, read the project instructions, report readiness, then wait. A next
task listed in status is context, not a startup work order.

The owner explains the problem, input/output contract and a useful alternative,
then implements a coherent increment and runs appropriate checks. Only the
owner edits product code and shared project status during an implementation.
The checker reviews the exact candidate without changing product code. State
the candidate commit or diff plus untracked files, reproduce consequential
behavior, and report concrete findings with file/line evidence. The owner
addresses findings; changed candidates require review of affected behavior.

Use OpenRig's queue for assigned work and handoffs. Learn current syntax with
`rig queue --help` and `rig queue handoff --help`. Terminal messages initiate
communication; they do not prove a durable task or a completed review. Include
the repository path, candidate identity, acceptance criteria, executed checks,
findings and unresolved limits in the handoff. Keep the user's authoritative
project history in the existing docs rather than generating another roadmap.

Each completed increment must teach Bryan: trace one real record/request through
the changed code, explain correctness and one failure mode, and offer at most
two optional teach-back questions. Passing tests and agent agreement do not
demonstrate Bryan's understanding. Record only his actual answers in the ledger.

Keep changes local. Commits, pushes, publication, external messages, spending
and starting additional services need specific task authorization. Do not
change native permissions to bypass a prompt. Normal workspace permissions
apply; report a blocking prompt with its exact command and purpose.
