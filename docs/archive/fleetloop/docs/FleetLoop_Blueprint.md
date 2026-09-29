> Archived FleetLoop reference. Commands, implementation claims, and agent rules here are historical, not active FleetLens instructions. See [migration context](../../../migration.md). Links have been relocated; source code remains in the original repository.

> **Historical design — superseded 2026-09-28.** The active scope and sequencing are in [roadmap.md](roadmap.md); agent behavior is in [../AGENTS.md](../AGENTS.reference.md). The original twelve-week schedule, mandatory stack, hand-coding rules, and cut order below are retained as history, not instructions. Planned claims and numbers are not achieved results.

# FleetLoop Blueprint — the 12-week design

*Scoped 2026-08-25 · build window Aug 25 → Nov 20, 2026.*

This is the **design of record**. Deviations are allowed — but they get logged in [decisions.md](decisions.md) with a reason, not silently absorbed here. The condensed version lives in CLAUDE.md → Milestones; this doc holds the full shape of each phase so day planning (`/plan-day`) has something to cut from.

## Premise

- **The purpose is employability against one job description** (Data Engineer, Fleet Data — Self-Driving), not shipping a product. Every design choice optimizes for *defensible interview claims backed by measurements* — see [jd-map.md](jd-map.md).
- **The three-way bet:** Bryan separately has DE infrastructure (DevPulse), CV/ML (PyTorch/OpenCV/YOLOv8), and frontend (React/TS), and has never combined them. The role sits at that intersection; almost no candidate has all three. Every phase must pull on at least two.
- **The governing rule (hard rule 1):** every phase ends in a measured number — a baseline, a comparison, and the chart that shows it. A phase without a number is not complete, whatever works.

## The system

```
fleetgen (N vehicles @10Hz) ──┐
comma2k19 / nuScenes / BDD100K ┼─► TRIGGERS (on-device budget) ─► ADMISSION CONTROL (byte budget + coverage)
NHTSA SGO / FARS / FHWA VMT ──┘                                             │
                                                                            ▼
   CLICKHOUSE (signals, 1–2B rows) ◄── PySpark (drive segmentation) ◄── BRONZE (clips + raw signals)
        │                    ▲
        │                    └── POSTGRES control plane (fleet registry · clip catalog · trigger defs · METRIC REGISTRY)
        ├─► SAFETY METRICS (versioned defs, exposure denominators, stratified, Poisson CIs) ─► Fleet Safety Report
        ├─► SCENARIO MINERS (TTC/THW/jerk) + EMBEDDING MINING ─► COVERAGE SELECTION ─► train YOLOv8 ─► EVAL SLICES
        └─► FastAPI ─► Fleet Explorer (React + deck.gl) · MCP server (typed tools over the semantic layer)
```

One loop: **generate → trigger → admit → store → measure → mine → curate → retrain → evaluate → serve**. The loop closing (a curated dataset measurably moving a model on named eval slices) is the single most valuable claim in the project.

Design constraints that shape everything (full list: CLAUDE.md → Hard rules): honest synthetic data (rule 2) · ground truth before miners (rule 3) · explicit denominators (rule 4) · idempotency proven by re-run (rule 6) · GPS is PII, designed before ingestion (rule 9) · build the ingestion and selection yourself, no dataset-loader shortcuts (rule 10) · $0 local-first (rule 13).

---

## Week 0 · Aug 25–28 — Close DevPulse, prepare the ground

Not FleetLoop work, but it gates everything: DevPulse Day 17 (GitHub Actions CI), README, architecture diagram, 3-minute demo video, onto the resume. **DevPulse Phase 4 (Kafka over GitHub events) is cut** — streaming gets built here, over vehicle telemetry, where it's on-target. Log that scope decision in DevPulse.

FleetLoop-side in Week 0: repo scaffold ✅ (2026-08-25) · these three docs ✅ · **start the big dataset downloads** (the Phase-1 long pole, see Data acquisition below) · build the project skills from DevPulse's `.claude/skills/` template.

## Phase 1 · Weeks 1–2 · Aug 31 – Sep 11 — The fleet and the firehose

**JD rows:** substrate for rows 1–5 ([jd-map.md](jd-map.md)).
**Goal:** a configurable N-vehicle synthetic fleet whose statistics are defensible, plus the ground-truth manifest every later measurement depends on.

Build:
- **`fleetgen` vehicle state machine** emitting 10 Hz CAN-like signals: speed, steering angle, long/lat accel, yaw rate, GPS, `autopilot_state`, driver torque, brake pressure, gear, SoC. Drive-cycle regimes (urban / highway / suburban) with realistic transitions.
- **Fleet dimensions**, fixed now because they are Phase 4's stratification variables: `hw_gen` (HW3/HW4) · `firmware_version` · `market`/`region` · `vehicle_model`. Getting these wrong here poisons Phase 4.
- **Calibration against comma2k19:** match speed / accel / jerk / heading-change distributions; the calibration check is a distribution-distance measurement (e.g. KS statistic per signal), reported per regime.
- **Planted ground-truth scenario manifest** (hard rule 3): hard brakes, cut-ins, disengagements, near-misses — injected with exact vehicle + timestamp + parameters, so Phase 5 miners get real precision/recall. The manifest is the exam key; it is never read by any miner.
- **Protobuf schema + Redpanda producer** — the firehose interface Phase 2 consumes.

**Deliverable / the number:** fleet runs at configurable N; calibration table (distance vs comma2k19 per signal); manifest counts pinned; **canonical test slice** (one date + one cohort) pinned in CLAUDE.md → Reference values.
**What this phase must teach:** generative modeling of telemetry honestly (what's easy to fake, what isn't), Protobuf schema evolution, Kafka-API mechanics.

## Phase 2 · Weeks 3–4 · Sep 14–25 — Ingest & inflow control ⭐ the differentiator

**JD row:** 1 — the bullet almost no other candidate will have built anything for.
**Goal:** decide, under an explicit byte budget, *which* data is worth uploading — and prove the decision policy matters.

Build:
- **Two-tier ingest:** 1 Hz always-on aggregate tier + on-demand 10 Hz clips.
- **On-device trigger runtime:** YAML → predicate DSL, evaluated under a compute budget (a trigger that's too expensive doesn't ship — that's the real constraint on-vehicle).
- **Upload budget manager:** per-vehicle quota, priority queue, WiFi-vs-cellular cost model, backpressure.
- **Diversity-aware admission control:** stratum histograms over weather × road type × speed band × maneuver × region × firmware; coverage-scored admission; near-duplicate rejection.
- **Privacy gate (hard rule 9):** the [privacy.md](privacy.md) controls — endpoint truncation, fuzzing, retention tags, region partitioning — are implemented at the bronze boundary *in this phase, before location lands anywhere*.

**Deliverable / the number:** the measured comparison — FIFO vs random vs coverage-weighted at an equal byte budget, scored on scenario entropy + rare-event yield. A negative or mixed result is publishable (teaching contract 6).
**What this phase must teach:** admission/budget thinking as a first-class DE problem; why diversity must be enforced at ingest, not recovered downstream.

## Phase 3 · Weeks 5–6 · Sep 28 – Oct 9 — The platform

**JD row:** 2.
**Goal:** the query layer that makes 1–2B rows explorable on one machine, with orchestration that shows its work.

Build:
- **ClickHouse:** `ORDER BY` design (with the rationale in a comment — it's the single biggest lever), codecs (`DoubleDelta`/`Gorilla`/`LowCardinality`) with **measured** compression, `AggregatingMergeTree` MVs for per-drive/per-day rollups, projections, skip indexes, TTL (also enforces privacy retention), dictionaries, async inserts. **Deliberately trigger "too many parts", then fix it** — the war story is the point.
- **The benchmark:** ClickHouse vs Postgres vs BigQuery on the same queries — Bryan has real BQ experience, so this is a genuine comparison → [tradeoffs.md](tradeoffs.md).
- **Postgres control plane:** fleet registry, clip catalog, trigger definitions, upload quotas, the **metric definition registry** (Phase 4's foundation).
- **Dagster:** software-defined assets, partitions, asset checks, sensors — plus the honest Airflow→Dagster comparison.
- **PySpark drive/session segmentation** with out-of-order and gap handling.
- **The firmware trap (hard rule 8):** fw 12.3 flips the `steering_angle` sign convention. The naive pipeline silently corrupts a metric; the signal registry catches it. Built as a deliberate exercise; never live outside it.

**Deliverable / the numbers:** compression ratio · benchmark table · idempotent re-run proof at every layer (`/verify-pipeline`).
**What this phase must teach:** columnar storage internals; the platform-as-product mindset the JD asks for; schema evolution as a semantic (not structural) problem.

## Phase 4 · Weeks 7–8 · Oct 12–23 — Safety metrics ⭐⭐ highest signal for this req

**JD row:** 3.
**Goal:** measurement science with receipts — the anti-pattern this phase refuses to reproduce is a headline rate without its stratified view.

Build:
- **Versioned metric registry** (in the control plane): SQL, grain, explicit exposure denominator, owner, changelog, restatement policy. Metrics compute *from* the registry, never hardcoded (hard rule 5).
- **Core metrics:** miles between disengagements / critical interventions, hard-brake rate per 1k mi, collision-proxy rate per M mi — each with its denominator named (engaged-miles vs total-miles vs hours).
- **Stratification** by the Phase-1 fleet dimensions + a **deliberately constructed Simpson's paradox** (the fleet-wide rate reverses under stratification) as the teaching artifact.
- **Adjustment:** direct standardization / propensity weighting; what was corrected *and what wasn't* goes in the methodology memo ([metrics/](metrics)).
- **Uncertainty:** Poisson & negative-binomial rate CIs, overdispersion tests; **power analysis** — fleet-miles to detect a 10% regression at 80% power.
- **Firmware rollout as a natural experiment** (DiD / RDD). Benchmark context from FARS / SGO / VMT.

**Deliverable / the number:** the **Fleet Safety Report**, reproducible from a pinned commit + frozen snapshot, methodology appendix included; the power-analysis number.
**What this phase must teach:** denominators, confounding, and uncertainty as engineering disciplines — the zero-prior-evidence gap this project most needs to close.

## Phase 5 · Weeks 9–10 · Oct 26 – Nov 6 — The data engine ⭐⭐

**JD rows:** 4 and 5.
**Prerequisite (do NOT enter the phase without it):** local CUDA + PyTorch confirmed working; BDD100K downloaded.
**Goal:** close the loop — mining validated against ground truth, curation validated against the model.

Build:
- **Kinematic miners:** cut-in, cut-out, hard brake, unprotected left, lane-change abort, near-miss by TTC, construction zone. Each ships its kinematic definition ([glossary.md](glossary.md)), **precision/recall vs the planted manifest**, and threshold sensitivity.
- **Embedding mining:** CLIP vs DINOv2 over keyframes — *decided by measurement, not preference* — ANN index, "find more like this", embedding dedup.
- **Coverage selection:** random vs stratified vs greedy submodular, at equal budget.
- **Close the loop:** train YOLOv8 on BDD100K; eval slices (night, rain, pedestrian-dense, small objects); 5k random vs 5k coverage-selected; **per-slice delta reported, wins and losses both**.

**Deliverable / the numbers:** per-miner P/R table · per-slice eval delta.
**What this phase must teach:** the data-engine loop as the core AV-fleet idea; honest ML evaluation.

## Phase 6 · Weeks 11–12 · Nov 9–20 — Serving

**JD rows:** 6 and 7.

**6a · Fleet Explorer** — React + TypeScript + deck.gl over MapLibre: hex-binned fleet map with drill-down; **time-synchronized drive detail** (speed/steering/accel/autopilot traces + clip video + map trace locked to one timeline — the fleet-data tool archetype); scenario search. Arrow over the wire; server-side aggregation; a stated point budget per view. Served surfaces obey [privacy.md](privacy.md) (no raw precise coordinates without the fuzzing layer).

**6b · The agentic layer** — MCP server exposing typed tools (`search_scenarios`, `compute_metric`, `describe_schema`) over the semantic layer. **Text-to-metric, not text-to-SQL** (hard rule 11). Guardrails: cost caps, row limits, read-only, grain validation, no raw coordinates in tool output.

**Deliverable / the numbers:** point budget + interaction latency for 6a · **40-question golden-set eval for 6b, failures characterized, not hidden**.
**What this phase must teach:** visualization engineering at a real bar; agent tool design as API design.

---

## Cross-cutting workstreams (never a phase of their own)

Observability (JD row 11 — per-asset freshness/volume/distribution SLOs, alerting, run metadata — port the DevPulse pattern) · GitHub Actions CI · `fleetkit` as an installable package (JD row 9) · the privacy design · the docs culture ([decisions.md](decisions.md), [tradeoffs.md](tradeoffs.md), [jd-map.md](jd-map.md), [interview/](interview)).

## The cut order (decided now, so it isn't decided under pressure)

| Priority | Scope | Why |
|---|---|---|
| **Never cut** | Phase 4, Phase 5 | The two Tier-1 differentiators. These *are* the job. |
| **Never cut** | Phase 2 | Explicit JD bullet nobody else will have built |
| Trim | Phase 3 | Keep ClickHouse + Dagster; drop PySpark if needed |
| Trim | Phase 6a | Ship 3 polished views, not 8 |
| Cut first | Phase 6b agent eval harness | The MCP server alone still tells the story |
| Cut first | Phase 5 embedding mining | Kinematic miners + coverage selection carry the loop alone |

## Data acquisition (the Phase-1 long pole — start in Week 0)

| Dataset | Size | Needed by | Notes |
|---|---|---|---|
| comma2k19 | ~100 GB | Phase 1 (calibration) | Start first; only a subset needed for calibration if the full pull drags |
| BDD100K | large (registration required) | Phase 5 (training) | Register + start early; images + labels for detection |
| nuScenes mini | ~4 GB | Phase 1–5 (labeled scenes) | Mini first; full only if a measurement demands it |
| NHTSA SGO / FARS / FHWA VMT | small CSVs | Phase 4 | Trivial; grab in Week 0 |

All under `data/` (gitignored — see `data/README.md`).

## Risks

- **Dataset acquisition slips** → only Phase 5 hard-depends on BDD100K; Phases 1–4 proceed regardless.
- **GPU/CUDA breakage** → confirmed *before* Phase 5 entry, not during.
- **Windows/Docker gotchas** → the carried list in CLAUDE.md hard rule 14; they cost real hours in DevPulse.
- **Tutorial drift** (building features instead of proving numbers) → hard rule 1 + `/measure` is the antidote.
- **Behind schedule** → the cut order above; never improvise cuts.

## What done looks like (Nov 20)

Six resume bullets, each a claim + a number, no adjectives — one per scoreboard row in the README: admission-control yield · compression ratio + benchmark · the safety report + power analysis · miner P/R · per-slice curation delta · agent golden-set score. Plus the interview bank ([interview/](interview)) covering every row of [jd-map.md](jd-map.md).
