> Archived FleetLoop reference. Commands, implementation claims, and agent rules here are historical, not active FleetLens instructions. See [migration context](../../../migration.md). Links have been relocated; source code remains in the original repository.

# Decisions — every non-obvious choice, and why

Append-only. Honest negative results belong here too (hard rule / teaching contract 6) —
"X didn't beat Y" is worth more in an interview than a clean win.

Format per entry:

```
## YYYY-MM-DD — <decision, imperative mood>
- **Choice:**
- **Why:**
- **Alternative rejected & why:**
- **What changes at real scale:**
- **Status:** active | superseded by <entry>
```

## 2026-08-25 — adopt privacy constants v0 as proposed

- **Choice:** ratify the `docs/privacy.md` defaults unchanged — endpoint truncation 500 m / 120 s, `ENDPOINT_H3_RES` 7, `SERVED_MAX_H3_RES` 8, `K_ANON_MIN_VEHICLES` 5, precise-GPS TTL 30 d, clip TTL 90 d, endpoint time coarsening 15 min.
- **Why:** neighborhood-scale fuzzing defeats the home/work-inference threat while keeping trip-level analytics usable, and the enforcement design (single `fleetkit.privacy` choke point + asset checks) makes any value cheap to change later. Bryan's call: keep as proposed, adjust down the road if needed.
- **Alternative rejected & why:** deferring ratification into Phase 2 — rejected because the ingest path must be built against fixed constants; tune by measurement later, not by stalling now.
- **What changes at real scale:** published aggregates move from a k-floor to differential privacy; residency becomes physical (separate buckets/clusters per jurisdiction); a deletion/DSAR workflow becomes mandatory.
- **Status:** active — any adjustment gets a new entry here, never a silent edit.

## 2026-08-25 — calibrate on a comma2k19 subset (2 of 10 chunks), not the full 100 GB

- **Choice:** download only chunks 1–2 (~20 GB, ~6 h of real driving) for Phase-1 calibration.
- **Why:** C: has **76 GB free** (measured 2026-08-25); the full ~100 GB dataset doesn't fit alongside BDD100K, nuScenes mini, and the ClickHouse volume to come. Calibration needs distributional coverage (speed/accel/jerk/heading per regime), not volume — ~6 h is ample to fit those distributions.
- **Alternative rejected & why:** full download to an external drive — deferred, not rejected. If Phase 1's calibration check (per-regime distribution distance) shows the subset is unrepresentative, pull more chunks then, with the evidence in hand.
- **What changes at real scale:** moot — at real scale the calibration source is the fleet itself, and the constraint inverts (which *sample* of the fleet do you trust as reference).
- **Status:** superseded 2026-08-25 (same day) — D: has 502 GB free; see the next entry.

## 2026-08-25 — datasets live on D: via junctions; comma2k19 uncapped

- **Update 2026-08-26:** the full 100 GB comma2k19 came down in one session, so the chunk-subset question never bit — the entire real corpus is local and verified. D: sits at 400 GB free.
- **Choice:** all datasets download to `D:\FleetLoop-data\<dataset>` (502 GB free, measured), with directory junctions from repo `data/<dataset>` → D:, so every code path stays repo-relative. comma2k19: chunks 1–2 first (Phase 1 needs them soonest), remaining chunks queued in the background — full 100 GB now fits.
- **Why:** the 2-chunk cap existed only because C: had 76 GB free; D: removes the constraint. More real driving data also strengthens Phase 5 (miner validation on real signals, embedding search substrate). Junctions over path config: zero code changes, `data/` layout stays canonical, and the gitignore already covers it.
- **Alternative rejected & why:** configuring per-dataset paths via env/config — more moving parts for no benefit at this scale; revisit only if the repo ever runs on a machine without a D:.
- **What changes at scale / watchouts:** Docker Desktop's WSL2 disk still lives on C: — where the ClickHouse volume goes (move the vhdx to D: vs bind-mount a D: path, with Windows bind-mount I/O overhead) is a **Phase 3 decision**, logged in CLAUDE.md open decisions. Docker bind sources through junctions: verify on first mount (hard rule 14's silent-empty-dir trap).
- **Status:** active on Windows; **amended 2026-09-01** — the env/config path rejection above no longer holds (see the two-machine entry below).

## 2026-09-01 — split development across two machines: Windows primary, macOS secondary

- **Choice:** Windows stays the **authoritative** machine — it holds every dataset (`D:\FleetLoop-data`), the local NVIDIA GPU, the full 1–2B-row ClickHouse store, and **every canonical measurement**. The macOS box (Apple Silicon, macOS 15.6.1) is a **development-only secondary**: Phase 1–4 code, unit tests, `fleetgen` at reduced scale, and the Phase 6 frontend. Operating guide: [environments.md](environments.md).
- **Why:** Bryan is away from the primary PC often enough that losing those hours costs more than the setup does, and the cost is near-zero *right now* — at the time of the decision the repo was a scaffold with no compose file, no `Makefile`, and no platform-specific code, so nothing needed porting. The whole stack is Docker + Python + Node, all cross-platform by construction (hard rule 13). The enabling property is that `fleetgen` is a **seeded generator**: the secondary machine regenerates its data from a commit rather than syncing it, so no dataset and no database ever has to travel.
- **The binding constraint — no canonical number is measured on the Mac.** Hard rule 1 makes every phase end in a measured number, and most are hardware-sensitive (the Phase 3 ClickHouse-vs-Postgres-vs-BigQuery benchmark, Phase 2 throughput, any latency). A figure produced on Apple Silicon and compared against one from the Windows box is an artifact of two machines, not a comparison. **The Mac proves correctness; the Windows box proves numbers.** Deterministic ratios (miner precision/recall, compression ratios) are machine-independent in principle but are still recorded from the primary machine so provenance is single-sourced.
- **Alternative rejected & why:** *true peer machines* — duplicating all ~112 GB of datasets (including the comma2k19 torrent) to both boxes. Rejected on three grounds: the disk and download cost, the ongoing sync discipline, and — decisively — comma2k19 is **real people's real driving**, so confining it to one machine keeps real GPS under one set of controls (hard rule 9, [privacy.md](privacy.md)). *Migrating fully to macOS* was also rejected: Phase 5 trains YOLOv8 and CUDA is not replaceable by MPS for that workload.
- **Amends the 2026-08-25 D:-junctions entry:** that entry rejected env/config path indirection, "revisit only if the repo ever runs on a machine without a D:". That condition has now fired. The junctions remain correct on Windows; a `FLEETLOOP_DATA_DIR` indirection (default: repo-relative `data/`) is now scheduled, deferred until the first code path actually reads `data/` — building it before there is a caller means guessing at the interface.
- **What changes at real scale:** moot as stated — at scale nobody develops against the production store, and the equivalent discipline is a dev/staging/prod split with measurements pinned to a controlled benchmark environment. The underlying rule is the durable one: *a benchmark is only a benchmark if the hardware is held constant.*
- **Status:** active.

## 2026-09-28 — adopt AI-assisted implementation and evidence-driven milestones

- **Choice:** AGENTS.md is the project-wide entry point; CLAUDE.md delegates to it. AI may implement all layers while teaching decisions, tracing examples, and providing focused practice. Learning is assessed from Bryan's actual explanations/debugging/modifications, separately from engineering completion.
- **Why:** Bryan explicitly requested a move from Claude Code coach-only work to an AI-assisted portfolio project. Typing ownership is not a useful proxy for technical understanding.
- **Alternative rejected & why:** continuing hint-only restrictions or requiring every generated feature to be rebuilt by hand would obstruct the requested workflow. Large unexplained code drops would also miss the learning objective.
- **Scope:** roadmap.md replaces the six calendar phases with an early end-to-end demo, reliability/orchestration, admission evaluation, real-image curation, and portfolio readiness. Keep useful evidence; defer services and scale targets until justified.
- **Measurement corrections:** separate synthetic telemetry from BDD100K curation unless a real link exists; protect exposure and report ascertainment; freeze evaluation rules; never force a baseline to lose. Public incident reports do not establish fleet-demographic distributions.
- **Documentation:** status.md owns current facts, the JD map owns evidence, and the learning ledger owns demonstrated understanding. Legacy blueprint/day plan/Claude workflows remain historical. Approved privacy design inputs remain; implementation is not claimed.
- **What changes at real scale:** service boundaries, distributed compute, operational controls, and deployment choices must be justified by workload/team needs; none are inferred from a local portfolio demo.
- **Status:** active; supersedes coach-only rules, the old timetable/cut order, blanket custom-reader requirement, mandatory mutation checks for every suite, and the assumption that all planned datasets form one linked loop.
