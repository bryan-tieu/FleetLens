# Working with AI on FleetLens

Effective 2026-09-28. This replaces coach-only mode and all typing-based accounting.

## Your role and the assistant's role

You own the goal, judge the tradeoffs, review the evidence, and learn to operate and change the system. The assistant acts as a staff data engineer: it proposes a bounded approach, implements authorized work, verifies it, and teaches the reasoning. AI can write most of the code.

Understanding is built in layers. First explain the purpose and data flow, then trace an example, then inspect the critical code/SQL, then diagnose a failure and make a small change. You do not need to memorize every line or rewrite every component.

## A normal session

1. Read status and choose the next roadmap acceptance criterion. Name the job responsibility it supports.
2. Explain the contract and one consequential tradeoff before coding.
3. Implement a small useful increment with appropriate verification.
4. Walk through actual input, transformation, and output. Explain relevant code, checks, and remaining limitations.
5. Offer a short teach-back or diagnostic exercise. Continue independent authorized work if you have not answered.
6. Record engineering results, learning evidence, and the next step in the repo.

A documentation/refactoring session may prove consistency rather than produce a performance number. Experiments need honest measurements; ordinary work need not invent comparisons to justify itself.

Decisions are recorded when an increment makes them, not held until a milestone ends. A consequential choice goes into the day's [decision file](decisions.md) with its reason, a viable alternative, the limit of the current approach, and the condition for revisiting it. A substantial feature gets a [walkthrough](walkthroughs/README.md) that follows one real project record through the relevant code or SQL, explains the invariants and failure path, and names what has actually been verified. Milestone summaries can point back to these records; they do not replace them.

## Prompts you can use

- "Continue the next task in docs/status.md. Implement it and explain the important decisions as you go."
- "Trace one example through this feature and show me where each value comes from."
- "Explain the SQL grain and why this join cannot double-count the metric."
- "Give me a small debugging exercise on what we just built."
- "Check what I can explain from memory; record the gaps without assuming I understood."
- "Prepare an interview explanation using only results we have actually measured."

These are ordinary requests. No slash commands or Claude-specific skills are required.

## Optional OpenRig pair

The [OpenRig runbook](openrig.md) describes the local implementer/reviewer pair.
The owner implements and teaches; the reviewer checks the actual candidate and
returns findings. Use one bounded task at a time. The same learning contract
applies: agent agreement and passing checks do not demonstrate Bryan's
understanding. Startup is orientation only; task assignment is explicit.

## Learning check

After a feature, aim to answer: What problem does it solve? What are its inputs and outputs? What makes the result correct? How can it fail? Why this design? What would change at larger scale?

Competency states are recorded in [learning/README.md](learning/README.md), with dated answers in [learning/](learning/README.md) and optional Q&A in [interview/](interview/README.md). Missing understanding is a review item, not a failure or a reason to stop all implementation. Targeted Python/SQL practice should strengthen independence. Each implemented concept also has a card in the [production bridge](learning/production-bridge.md) naming the production pattern it corresponds to; a *bridge check* asks Bryan to connect the FleetLens mechanism, that pattern, and one difference between them.

## Ending or switching sessions

The assistant updates [status.md](status.md), dated [history](history.md), [decisions](decisions.md), and [learning evidence](learning/README.md), plus a feature walkthrough when useful. It records actual check results, pending questions, and existing user edits. In a fresh session, start from AGENTS.md and status.md.

Do not paste private dataset rows, credentials, or identifying traces into a walkthrough. Do not call planned functionality complete. The migration archive contains historical reference only; old workflows are not installed.
