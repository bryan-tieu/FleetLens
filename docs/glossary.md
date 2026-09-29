> Migrated domain reference: mentions of fleetgen/signals.py and earlier implementation describe FleetLoop, whose code was not imported. Values below are inherited design inputs, not a FleetLens implementation or measurement. Canonicalize source signals once; numeric bounds alone cannot detect every semantic error.

> **Context update 2026-09-28:** retained domain notes; historical phase and numbered hard-rule references point to the retired plan. Use [roadmap.md](roadmap.md) for sequencing and [status.md](status.md) for implementation state. Wire signals are normalized once at the adapter boundary; downstream canonical values are not repeatedly decoded. A declared numeric domain alone cannot detect every sign-convention error.

# Glossary — every concept as used in FleetLens

Terms are added the day they are first used, with the definition *as this project uses
it* plus canonical constants. Planned entries: TTC · THW · exposure · ODD · coverage
score · disengagement · engaged-miles vs total-miles · admission control · stratum.


## Privacy (first used 2026-08-25 — docs/privacy.md)

- **Endpoint truncation** — dropping the first/last 500 m or 120 s (whichever covers more) of a trip's precise trace *at ingest*, so the sensitive form never persists. The anti-home/work-inference control.
- **Geofence fuzzing** — storing trip endpoint locations only as H3 res-7 cells (neighborhood scale), endpoint times coarsened to 15-min buckets.
- **H3** — Uber's hexagonal hierarchical spatial index; resolution 7 ≈ 5 km² hexes, resolution 8 ≈ 0.7 km². Used for endpoint storage (res 7) and served aggregates (res ≤ 8).
- **k-anonymity floor** — a served hex/stratum aggregating < 5 distinct vehicles is suppressed, not rendered small. Rare cohorts are identities.

### Canonical constants (ratified 2026-08-25 — see docs/privacy.md)

| Constant | Value |
|---|---|
| `TRIP_ENDPOINT_TRUNCATION_M` / `_S` | 500 m / 120 s |
| `ENDPOINT_H3_RES` · `SERVED_MAX_H3_RES` | 7 · 8 |
| `K_ANON_MIN_VEHICLES` | 5 |
| `BRONZE_PRECISE_GPS_TTL_DAYS` · `CLIP_TTL_DAYS` | 30 · 90 |
| Endpoint time coarsening | 15 min |


## Signals (first used 2026-09-04 — [fleetgen/signals.py](migration.md#source-implementation))

**Vehicle frame — ISO 8855.** X forward, Y left, Z up, right-handed. Every sign convention below follows from it, and the consequence worth holding onto is that **a left turn is positive in all three turn signals** — steering angle, yaw rate, and lateral acceleration alike. The kinematic checks are written with no sign correction factors on purpose, so a check that would need one is reporting a *wrong convention*, not wrong physics.

- **Signal registry** — `fleetgen/signals.py`: the single definition of what each telemetry signal means (unit, sign convention, domain, wire decode). Every read resolves through `spec(name, firmware)`; a raw column read that bypasses it is a bug (hard rule 8).
- **Signal spec** — one signal's declaration: `unit`, `dtype`, `description`, `positive_means`, exactly one domain rule (`valid_range` **or** `enum_type`), and the wire decode (`scale`, `offset`). The one-domain-rule constraint is validated at import, so a signal cannot be silently exempt from the domain check.
- **Canonical value vs wire value** — *canonical* is the ISO 8855 SI value every consumer sees; *wire* is what the vehicle actually emitted. The canonical convention is invariant across firmware — positive yaw is always a left turn — and what a firmware override changes is the decode from wire to canonical, never the meaning.
- **Effective-from resolution** — a firmware override applies to its stated version **and every later one**, applied cumulatively in ascending version order. Exact-match resolution would mean the next firmware silently reverts to the old decode, which is a wrong number rather than an error. Versions compare as parsed integer tuples, never as strings (`"12.10"` sorts before `"12.3"` as text).
- **Longitudinal / lateral** — vehicle-frame axes: *longitudinal* is along X (forward/back), *lateral* is along Y (left/right). **Not** geographic longitude/latitude, which arrive as separate PII-governed columns on the route day. A field named for the wrong one of these joins cleanly and means nothing.
- **Road-wheel angle** — the steer angle of the road wheels, which is what `steering_angle_rad` carries. Distinct from *steering-wheel* angle, larger by the steering ratio (~12–16×) and what a real CAN bus typically reports. The bicycle model is defined on road-wheel angle, so a steering-wheel signal fed to it needs an explicit ratio or the check is simply wrong.
- **Yaw rate** — rate of rotation about the vertical (Z) axis; positive counterclockwise viewed from above, i.e. a left turn. Related to the other turn signals by `a_lat = v·ω` and, via the bicycle model, `ω = v·tan(δ)/L`.
- **Jerk** — the time derivative of acceleration, `da/dt`. `JERK_MAX_MPS3 × DT_S` is the acceleration change permitted per 10 Hz tick, which is what determines whether the generator can physically produce an emergency brake at all.
- **Plausibility envelope** — what `valid_range` holds: the widest value a real vehicle could produce, plus margin. It exists to fire on a sign flip, unit error, or garbled decode — **never** on aggressive driving. Distinct from two other numbers in the same units: the *behavioral norm* (what typical driving looks like — a generator regime parameter) and the *event threshold* (what counts as a hard brake — a Phase 4 metric definition). Conflating them yields a "hard-brake rate" that is really a comfort-exceedance rate: plausible-looking, and measuring something else.

### Signal definitions (as of 2026-09-04)

| Signal | Unit | Positive means | Domain |
|---|---|---|---|
| `speed_mps` | m/s | — (unsigned; direction carried by `gear`) | `[0, 60]` |
| `accel_long_mps2` | m/s² | accelerating forward (+X); negative is braking | `[-10, +6]` |
| `accel_lat_mps2` | m/s² | acceleration toward the left (+Y) | `[-9, +9]` |
| `yaw_rate_radps` | rad/s | counterclockwise from above (+Z) — a left turn | `[-1.5, +1.5]` |
| `steering_angle_rad` | rad | road wheels turned left (+Y) | `[-0.6, +0.6]` |
| `gear` | — | — (categorical) | `Gear` = P · R · N · D |

### Canonical constants (set 2026-09-04 — see [fleetgen/signals.py](migration.md#source-implementation))

| Constant | Value | Basis |
|---|---|---|
| `SAMPLE_RATE_HZ` · `DT_S` | 10 Hz · 0.1 s | High-fidelity tier; the 1 Hz always-on tier is separate |
| `JERK_MAX_MPS3` | 5 | ⚠️ Provisional. 0.5 m/s² per tick → ~1.6 s to reach −8 m/s². Refit at calibration |
| `STEER_MAX_RAD` | 0.6 | ⚠️ Provisional. ~34° of **road-wheel** angle |
| `WHEELBASE_M` | ⬜ not yet set | Required by the bicycle-model check; must land before C3 |

**Provisional vs. physics.** These bounds split into two kinds, and only one gets recalibrated. The adhesion limit behind `accel_lat` (~1 g) is *tire physics* and will not move when comma2k19 lands; top speed, peak acceleration, and both ⚠️ constants above are *fleet-dependent* and will. Anything marked provisional is a hand-set value awaiting the calibration day, not a measurement.
