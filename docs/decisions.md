# FleetLens decisions

Each consequential choice records why, the alternative, its limitations, and what would change at real scale.

## 2026-09-28 — restart with documentation and fresh code

- **Choice:** preserve FleetLens's independent initial commit and import project context without FleetLoop Git history or implementation.
- **Why:** Bryan requested fresh Git history and explicitly chose documentation with fresh code.
- **Alternative:** copying the unfinished modules would preserve progress but also import incomplete implementation and implicit contracts. Those files remain available in the unchanged source repo.
- **Scope:** keep the first complete demo, reliability, admission evaluation, and controlled image curation. Start one installable package at src/fleetlens/.
- **Learning:** AI can implement all layers; understanding is demonstrated through explanations, diagnosis, bounded changes, and defended tradeoffs. No typing quotas or mandatory rewrites.
- **Inherited design inputs:** existing domain/privacy notes remain hypotheses or planned controls where appropriate. Historical hardware, downloads, and results require verification; simulation assumptions do not establish real fleet behavior.
- **Status:** active. Prior decision history is retained in the migration archive.

## 2026-09-28 — retain a small initial stack

- **Choice:** begin with Python contracts/fixtures; introduce ClickHouse/API/explorer for M1 and Dagster for M2.
- **Why:** prove a usable source-to-insight path before adding operational complexity.
- **Alternative:** instantiate every technology named in the job description immediately; rejected because it delays evidence without establishing a workload need.
- **What changes at scale:** add distributed processing, transactional control metadata, object storage, and streaming based on measured workload and operational requirements.
- **Status:** active; no services are implemented yet.

## 2026-09-29 — Python environment and canonical contract foundation

- **Choice:** Python 3.11 initially, src-layout setuptools package, no runtime dependencies, pinned pytest/Ruff/Black/build dependencies, and GitHub Actions for Windows/Linux. Local 3.11.9 install and checks passed.
- **Why:** establish a reproducible small environment with a validated package boundary before M1 storage. Restrict support to one tested minor version until a broader matrix is needed.
- **Alternative:** a new environment manager or containers could improve environment standardization, but standard venv/pip already satisfies this increment. Version pins do not guarantee identical artifacts; dependency hashes remain a future improvement.
- **Contract:** immutable dataclasses reject invalid types/domains; canonical speed uses m/s and forward longitudinal acceleration uses m/s². Source decoding is a separate future adapter responsibility.
- **Identity:** dataset + snapshot + vehicle + drive + source sequence; decoding corrections retain source identity. Revision and replay behavior remain an ingestion decision.
- **Alternative:** a runtime schema library is appropriate when JSON/API ingestion warrants it. At larger volume, batch validation must preserve these semantics and reconcile rejected records.
- **Status:** locally verified; hosted Windows/Linux CI passed 2026-09-29 (run 36535425818). Physical realism, deduplication, and all source-adapter behavior remain unverified/unimplemented.

## 2026-09-29 — stable synthetic assignment and frozen tiny oracle

- **Choice:** derive each scenario draw from SHA-256 of seed and vehicle ID, sort output IDs, and use fixed small SI-unit templates. The two-drive oracle is a separate checked-in JSON file with event/exposure rules and hand calculations.
- **Why:** fleet growth and caller order do not perturb an existing vehicle; the oracle can test future metrics without asking the generator or miner for its own answer.
- **Alternative:** a shared seeded random stream is simpler but shifts every later assignment when an earlier vehicle is inserted. A complex physics simulator would add unvalidated assumptions before an ingestion and metric path exists.
- **Limits:** the scenario weights and shapes are invented. A 64-bit hash draw gives deterministic assignment but no claim about real fleet prevalence. The fixture's acceleration interval and gap rules are frozen for future M1 evaluation; any change requires an explicit version and restatement.
- **Status:** implemented and locally verified on macOS Python 3.11.16; hosted CI for this increment is pending.

## 2026-09-29 — supervised OpenRig development pair

- **Choice:** at Bryan's request, install OpenRig 0.6.1 with two Codex seats: an implementer and an independent reviewer. Use a local FleetLens rig with the existing teaching contract and inherited native model, leaving support/kernel agents off.
- **Why:** try independent review on bounded increments while preserving Bryan's record tracing and design explanations. Tooling is separate from the FleetLens product and is not evidence of an agent-facing analytics feature.
- **Alternative:** use one coding session with an occasional separate review. That remains simpler if native prompts and coordination consume more effort than the review saves.
- **Permissions:** retain workspace sandbox and ordinary approval prompts; no persistent command allowlist or broader network permission was added. One-time local-daemon approvals exposed a prompt/message collision; the built-in mailbox accepted the ACK.
- **Limits:** two ready seats and a delivered setup acknowledgement prove startup/communication, not review quality or faster development. A complete implementation/review queue cycle and recovery after reboot remain unverified.
- **Status:** running locally. See [OpenRig runbook](openrig.md) for installed versions, backup location, operating commands, and how to stop the pair.
