> **Design status — 2026-09-28:** these are planned controls, not implemented guarantees. No privacy module or enforcement checks exist yet. Retain the declared constants as design inputs, validate the threat model when implementing, and do not present fuzzing or a k-floor as proof of anonymity. Consult [architecture.md](architecture.md) for the staged code layout. Dataset availability alone does not establish consent or permission for public display.

# Privacy design — GPS is PII, and video is worse

*Written 2026-08-25, before any ingestion exists (hard rule 9). Constants **ratified 2026-08-25** — recorded in [decisions.md](decisions.md); adjustments later are fine, but only through a new decisions entry.*

## Why this exists when the fleet is synthetic

Three reasons, in honesty order:

1. **comma2k19 is real people's real driving.** Real GPS traces of real commuters, published for research — public does not mean carefree. It gets handled with the same controls as the synthetic data.
2. **The design is a deliverable.** "How would you handle fleet location data?" is a guaranteed interview question for this role, and a written threat model beats an improvised answer.
3. **Practicing on synthetic data proves the pipeline enforces the controls** — enforcement code that has never run is a policy, not a control.

## Threat model

The adversary is anyone with read access to a served surface (API, Explorer, MCP tool, exported chart) — or, at scale, an insider with warehouse access.

| Threat | Mechanism | Severity |
|---|---|---|
| **Home/work inference** (primary) | Trip endpoints cluster at residence and workplace; a handful of trips re-identifies a person even from "anonymous" vehicle ids | High — this is *the* threat the controls are built around |
| Trajectory re-identification | A route is a fingerprint; one unusual trip can identify a driver even with endpoints removed | Medium |
| Temporal pattern leakage | Departure/arrival times reveal schedules, religious attendance, medical visits | Medium |
| Linkage / k-anonymity erosion | `region` × rare `hw_gen` × `firmware_version` narrows a "cohort" to one vehicle | Medium |
| **Video** | Worse than GPS: faces, plates, house frontages — and it captures *bystanders who never consented*, not just the driver | Highest |

## Data classification

| Data | Class | Standing rule |
|---|---|---|
| Precise GPS (10 Hz lat/lon) | **PII** | Never on a served surface raw; bronze-only, TTL-bound |
| Trip endpoints (start/end location) | **PII, highest sensitivity** | Truncated + fuzzed at the bronze boundary; precise form never stored past ingest |
| Fuzzed / hex-binned location | Reduced | Servable, subject to the k-anonymity floor |
| Kinematics without location (speed, accel, steering…) | Low | Freely usable |
| Video clips | **PII+** | See Video section |
| `vehicle_id` | Pseudonymous identifier | Synthetic pseudonym; joins yield cohort dims only, never a stable real-world identity |
| Timestamps | Sensitive in combination | Fine at drive grain; endpoint times coarsened with endpoint locations |

## Controls

All fuzzing/truncation logic lives in **one library — `a shared privacy module (location to be decided when implemented)`** — a single choke point. A second implementation anywhere is a defect.

### 1. Endpoint truncation (at the bronze boundary, Phase 2 ingest)
The first and last `TRIP_ENDPOINT_TRUNCATION_M` = **500 m** *or* `TRIP_ENDPOINT_TRUNCATION_S` = **120 s** of every trip (whichever covers more) are dropped from the precise trace before anything persists to bronze. The precise endpoint never lands on disk — truncation happens in the ingest path, not as a later scrub. (A scrub-later design leaves a window where the sensitive form exists; ingest-time truncation has no window.)

### 2. Geofence fuzzing of stored endpoints
Trip start/end *locations* (needed for trip-level analytics) are stored only as **H3 cells at `ENDPOINT_H3_RES` = 7** (~5 km² hexes — neighborhood scale, not address scale). Endpoint *times* are coarsened to 15-minute buckets. Both raw forms discarded at ingest.

### 3. Serving rules (Explorer, FastAPI, MCP — Phase 6, enforced from Phase 2)
- **No raw precise coordinate on any served surface.** The only exception: the single-drive detail view may render the *truncated* mid-trip trace (endpoints already gone by construction).
- **Fleet-level / multi-vehicle views:** hex-binned aggregates only, at **H3 res ≤ `SERVED_MAX_H3_RES` = 8**, with a **k-anonymity floor**: any hex/stratum aggregating fewer than `K_ANON_MIN_VEHICLES` = **5** distinct vehicles is suppressed, not rendered small.
- **Agents get no coordinates at all:** MCP tool outputs carry H3 cells and segment ids, never lat/lon. (Hard rule 11's guardrails extend to privacy.)

### 4. Retention (implemented as ClickHouse TTL + MinIO lifecycle in Phase 3)
| Data | Retention | Then |
|---|---|---|
| Bronze precise 10 Hz GPS | `BRONZE_PRECISE_GPS_TTL_DAYS` = **30** | Deleted; only truncated/fuzzed derived products persist |
| Clips | `CLIP_TTL_DAYS` = **90** | Deleted unless *promoted* into a curated dataset — promotion is an explicit, logged decision, and a promoted clip's location metadata is fuzzed |
| 1 Hz aggregate tier | Long-lived | Fuzzed at ingest, so retention is not the control |

### 5. Regional residency
`region` is a partition column end to end: MinIO bucket prefix, ClickHouse partition key component, Dagster partition dimension. The simulated constraint: a region's precise-GPS data never leaves its partition; cross-region queries run over fuzzed aggregates only. **Simplified vs production:** locally this is one machine and the residency is a convention enforced by code + asset checks; at scale it's separate buckets/clusters per jurisdiction. Articulating that gap is part of the design.

### 6. Video
Real media may contain identifying information about bystanders. Before processing or displaying a public dataset, verify its actual usage and redistribution terms; research availability does not establish individual consent. The synthetic generator creates no real video. If new real capture is introduced, design and verify face/plate treatment before persisting or serving it, and apply the location controls to metadata. Explorer may display only media whose use is permitted and whose required controls have been verified.

### 7. Identifiers
`vehicle_id` is a synthetic pseudonym with no real-world referent. Registry joins expose cohort dimensions (`hw_gen`, `firmware_version`, `market`, `vehicle_model`) — and any served cohort breakdown obeys the same k = 5 floor, because rare cohorts are identities.

## Enforcement — what makes this a control, not a policy

- **One choke point:** `a shared privacy module (location to be decided when implemented)` owns truncation, fuzzing, coarsening, and the k-floor. Reviewed once, tested once, used everywhere.
- **Unit tests with planted endpoints:** synthetic trips with known precise endpoints; tests assert the persisted bronze trace contains no point within the truncation window. Mutation-checked like every suite (break the truncation, watch the test redden).
- **Asset checks (Dagster):** every served-layer asset asserts (a) no lat/lon columns outside the allowed drive-detail path, (b) H3 res within bounds, (c) k-floor applied. A failing check gates the build.
- **API/MCP schema validation:** response models simply have no raw-coordinate fields; the type system enforces what discipline would forget.
- **The standing defect definition:** a raw precise coordinate observed on any served surface is a bug of the same severity as a dropped row (hard rule 7) — quarantine, fix, and log in [decisions.md](decisions.md).

## Simplified vs production (stated, per teaching contract 2)

| Not built here | What production adds |
|---|---|
| Encryption at rest / in transit locally | KMS-managed encryption, TLS everywhere |
| Access control & audit logging (single user) | Role-based access with per-query audit trails; location access is its own privilege tier |
| Deletion / DSAR workflow | Per-vehicle deletion path — which is why `vehicle_id` must be a partition-prunable dimension from day one |
| Differential privacy | For *published* aggregates (like a public safety report), DP noise is the stronger tool than a k-floor; k-anonymity chosen here for legibility and because no aggregate is truly published |

## Canonical constants (ratified 2026-08-25 — mirrored in [glossary.md](glossary.md))

| Constant | Value |
|---|---|
| `TRIP_ENDPOINT_TRUNCATION_M` | 500 m |
| `TRIP_ENDPOINT_TRUNCATION_S` | 120 s |
| `ENDPOINT_H3_RES` | 7 |
| `SERVED_MAX_H3_RES` | 8 |
| `K_ANON_MIN_VEHICLES` | 5 |
| `BRONZE_PRECISE_GPS_TTL_DAYS` | 30 |
| `CLIP_TTL_DAYS` | 90 |
| Endpoint time coarsening | 15 min |

---

**Interview evidence:** these controls are currently a design. Describe them as planned until the relevant code and checks exist; later cite actual tests and limitations rather than claiming that location processing guarantees anonymity.
