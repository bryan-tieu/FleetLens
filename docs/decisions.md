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
- **Status:** locally verified. Hosted CI, physical realism, deduplication, and all source-adapter behavior remain unverified/unimplemented.
