> Archived FleetLoop reference. Commands, implementation claims, and agent rules here are historical, not active FleetLens instructions. See [migration context](../../../../migration.md). Links have been relocated; source code remains in the original repository.

> **Historical plan — superseded 2026-09-28; original content preserved.** Continue with [session-02.md](session-02.md), [../roadmap.md](../roadmap.md), and [../../AGENTS.md](../../AGENTS.reference.md). The coach-only rules, prerequisite status, forced baseline-loss target, and completed-tense interview script below are obsolete and must not guide current work. The numerical results below were targets/examples, not measurements. AI-authored code is no longer a mandatory reimplementation assignment.

# Day 01 — Build the fleetgen vehicle state machine: coherent time series, not plausible histograms

> **Phase 1 · Week 1 · JD row 10:** *"Design and implement data pipelines from ingestion to visualization to unlock the full potential of Tesla's fleet data by **sourcing**, transforming, and serving new datasets"* — today is the sourcing end. Substrate for rows 1 and 4, which cannot be measured until a fleet exists to measure.
>
> **The day's number:** **kinematic consistency violation rate**, state machine vs. a naive marginal sampler, on identical signal specs and an identical seed. Pre-registered win condition: **state machine ≤ 0.1%, marginal sampler ≥ 50%.** Plus a determinism gate: same seed, same machine → identical output hash. `/measure` enforces both before the day closes.
>
> First build day — nothing precedes it. Week 0 delivered the scaffold, the docs, the skills, and three of four datasets; comma2k19 is still downloading and **today does not need it** (see Prerequisites).
>
> **Scope call (read first).**
> **IN:** the signal spec + unit/sign conventions · fleet dimensions · the three-regime state machine over six kinematic signals · seeded determinism · the consistency checker · the strawman comparison.
> **OUT, and where each goes:** GPS/position → the route day (it wants a road model *and* [privacy.md](../privacy.md)'s endpoint controls; both deserve their own day) · `autopilot_state` + `driver_torque` → Day 2, they're event-driven, not dynamics-driven · `brake_pressure`, SoC → Day 2 · calibration vs comma2k19 → its own day once chunks 1–2 land · planted ground-truth manifest → its own day (hard rule 3) · Protobuf + Redpanda → its own day.
>
> **The day's central decision, stated up front: integrate state forward; never sample signals independently.**
> A vehicle's signals are not eleven parallel random variables — they are one physical state observed eleven ways. `speed`, `a_long`, `yaw_rate`, and `steering_angle` are bound by kinematics at every 10 Hz tick, and the *only* honest way to produce them is to hold state and step it. Sampling each signal from its own marginal distribution produces data whose histograms look perfect and whose physics is incoherent — and every downstream thing this project does (miners keyed on TTC and jerk, metrics keyed on hard-brake events) reads the *transitions*, not the marginals.
> **Alternative rejected — marginal/i.i.d. sampling per signal:** it wins when you only need volume and marginal realism, e.g. load-testing a schema or benchmarking a storage engine, where nobody reads the physics. It's built today anyway, as the strawman that makes the number decidable.
> **Alternative rejected — replay/resample real comma2k19 traces:** genuinely tempting and much easier, but it caps the fleet at 33 h of real behavior, can't be dialed to N vehicles, and — fatally — can't have ground truth *planted* in it, which hard rule 3 requires before any miner exists. Revisit only for a validation set, never the fleet.
> **Production vs simplified:** real telemetry comes off a CAN bus with per-ECU rates, dropouts, sensor noise, and clock skew. Today's generator is noiseless, perfectly clocked, and single-rate. Out-of-order and gap handling is deliberately Phase 3's problem (PySpark segmentation); noise arrives with calibration. Saying that gap out loud is the skill (teaching contract 2).

## Environment notes (macOS secondary · no containers today)

**Today is pure Python — no Docker, no dataset, no GPU.** That makes it the ideal first day for the Mac; see [environments.md](../environments.md) for the split. Nothing today produces a hardware-sensitive number, so the "measure on Windows only" rule does not bind — the violation rate is a deterministic ratio.

- Working machine: either. `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements-dev.txt`.
- New in `requirements.txt` today: `numpy` (state integration), `pytest` already in dev. Nothing else — resist adding a simulation framework.
- **Prerequisites check.** comma2k19 is ⬜ not downloaded. **Today proceeds without it, deliberately:** calibration is a separate Phase 1 item ([Blueprint:48](../FleetLoop_Blueprint.md#L48)), and you cannot calibrate a generator that doesn't exist. Build the machine with hand-set parameters today; fit them to real distributions on the calibration day. Blueprint risk register already sanctions this — *"only Phase 5 hard-depends on BDD100K; Phases 1–4 proceed regardless."*
- **Privacy (hard rule 9): does not bind today.** No location, no video, no vehicle-identifying data is generated. That is precisely why GPS is deferred — the day that emits position is the day that must implement truncation and fuzzing at the same time, not after.

## Steps

**1. 🧑‍💻 Pin the signal spec — units, ranges, sign conventions.** `fleetgen/signals.py`, plus a Signals block in [glossary.md](../glossary.md).
Six signals today: `speed_mps`, `accel_long_mps2`, `accel_lat_mps2`, `yaw_rate_radps`, `steering_angle_rad`, `gear`. For each: unit, valid range, and **the sign convention, written down** (is positive steering left or right? is positive `a_long` acceleration or deceleration?). This is not bookkeeping — hard rule 8's firmware trap in Phase 3 is *exactly* a sign convention flipping under you, and the registry that catches it starts as this file. Also pin `DT_S = 0.1`, `WHEELBASE_M`, `JERK_MAX_MPS3`, `STEER_MAX_RAD` as canonical constants.
*Pitfall:* picking conventions implicitly by writing code first. Decide, write them down, then code.
→ commit: `pin fleetgen signal spec and sign conventions (JD row 10)`

**2. 🧑‍💻 Fleet dimensions and vehicle identity.** `fleetgen/fleet.py`.
`hw_gen` (HW3/HW4) · `firmware_version` · `market`/`region` · `vehicle_model`. The Blueprint is blunt about why these are fixed *now*: they are Phase 4's stratification variables, and **getting them wrong here poisons Phase 4**. Give them non-uniform, non-independent distributions — HW4 skews newer firmware, regions skew models — because a Simpson's paradox needs correlated strata to exist at all, and Phase 4 has to construct one.
Assignment must be a pure function of `(seed, vehicle_id)`, so vehicle 37 is identical on any machine, any run.
*Pitfall:* `random` module global state. Use an explicit `numpy.random.Generator` per vehicle, derived from the seed.
→ commit: `add fleet dimension model with correlated strata (JD row 10)`

**3. 🧑‍💻 The state machine — this is the day's lesson.** `fleetgen/vehicle.py`.
Hold a state (speed, accel, heading, steering, regime); step it at `DT_S`. Three drive-cycle regimes — urban / highway / suburban — with a transition model between them and regime-conditional target behavior (urban: low speed, frequent stops, high steering variance; highway: high speed, rare large steering, long dwell).
The shape: `step(state, rng) -> state` as a **pure function**, with the loop and any I/O outside it (Conventions: pure-transform / I/O split, so this is unit-testable without a cluster). Derive what can be derived — `a_lat` from `v·ω`, `yaw_rate` from the bicycle model — rather than sampling it. Every derived signal is one fewer chance to be incoherent.
*Pitfalls to expect:* speed going negative on hard decel (clamp, and make the clamp a state transition to `stopped`, not a silent `max(0,·)`); jerk discontinuities at regime boundaries; steering that integrates into an unbounded heading spiral.
→ commit: `add fleetgen vehicle state machine with three drive-cycle regimes (JD row 10)`

**4. 🧑‍💻 The consistency checker — the measuring instrument.** `fleetgen/checks.py`.
Five checks over consecutive samples, each reporting its own violation rate plus an overall:
- **C1 longitudinal:** `|v[t+1] − (v[t] + a_long[t]·DT)| ≤ ε_v`
- **C2 lateral:** `|a_lat[t] − v[t]·ω[t]| ≤ ε_a`
- **C3 steering↔yaw (bicycle):** `|ω[t] − v[t]·tan(δ[t])/L| ≤ ε_ω`
- **C4 jerk bound:** `|a[t+1] − a[t]|/DT ≤ JERK_MAX`
- **C5 domain:** `v ≥ 0`, `gear` consistent with `v`, `|δ| ≤ STEER_MAX`
Write this as a *reusable* checker, not a test: it becomes a Dagster asset check in Phase 3 and it is the shape of hard rule 7 (fail loudly, never drop silently).
*Pitfall:* choosing ε to make the number pretty. Set ε from float precision (~1e-9 scale), not from what passes. A check that can't fail is the exact failure mode `/measure` and mutation-checking exist to catch.
→ commit: `add kinematic consistency checker for generated signals`

**5. 🤖 The strawman + comparison harness.** `fleetgen/baselines.py` — a marginal sampler drawing each signal independently from a plausible per-regime distribution, deliberately naive, ~20 lines. Claude writes this: it mirrors no lesson and exists only to be beaten.
→ commit: `add marginal-sampler baseline for consistency comparison`

**6. 🧑‍💻 Run the measurement.** `/measure`. Both generators, same seed, same duration, same signal spec. Report the per-check table and the overall rate for each. Then the determinism gate: same seed twice → identical hash.
**Pre-registered, before any result exists:** state machine ≤ 0.1% overall (ideally 0.00%); marginal sampler ≥ 50%. **If the state machine is not ~0, the integrator is wrong — that is a bug to fix, not a result to report.** If the marginal sampler somehow scores well, the checks are too loose; tighten ε and say so.
**Known risk, pre-registered:** cross-machine byte-identity may fail on trig — `tan`/`cos` can differ in the last ULP between x86 and ARM libm. Same-machine determinism must pass today. Cross-machine is a **carried checkbox** for the next Windows session: if hashes differ but a tolerance comparison passes, that is a real finding about the two-machine strategy and goes in [decisions.md](../decisions.md) — the fix is tolerance comparison, not hash equality.
→ commit: `measure kinematic consistency: state machine vs marginal sampler`

**7. 🤖 Chores.** `.gitattributes` (`* text=auto`, `eol=lf` on `.sh`/`.sql`/Dockerfiles) — open item from [environments.md](../environments.md), and Day 1 is the cheapest moment. Add `numpy` to `requirements.txt`. Pytest fixtures + the mutation check on the new suite (break the integrator, confirm C1 reddens).
→ commit: `add gitattributes and fleetgen test scaffold`

## Done criteria

- [ ] Signal spec written down with sign conventions; canonical constants in [glossary.md](../glossary.md)
- [ ] Fleet dimensions fixed, with correlated strata and seed-deterministic assignment
- [ ] State machine steps three regimes at 10 Hz; `step()` is pure and unit-tested
- [ ] Consistency checker reports all five checks independently
- [ ] **The day's number measured via `/measure`**: violation rate, state machine vs marginal sampler, against the pre-registered thresholds
- [ ] Determinism proven same-machine (identical hash); cross-machine check **carried** to the next Windows session
- [ ] Mutation check passed — breaking the integrator reddens C1
- [ ] `ruff check . && black --check .` green; `python -m pytest tests/` green
- [ ] Docs routed via `/end-session`; `/verify-pipeline` **N/A today** — no pipeline step exists yet, state this rather than skipping silently
- [ ] Honest note: **today closes no ⬜ in [jd-map.md](../jd-map.md)** — Phase 1 is substrate. Row 10 moves to 🟡 only when the fleet is calibrated and streaming.

## Solved for me — revisit

- **Step 2 · `FIRMWARE_BY_HWGEN` + `FIRMWARE_VERSIONS`** (2026-09-15) — Claude wrote these
  on explicit request (hint ladder 4). The *reasoning* Bryan should be able to reproduce
  unaided: NHTSA SGO redacts `Automation Feature Version` in 1729/1729 rows, so the table
  is hand-set rather than derived; HW3 and HW4 are modelled as two *overlapping* version
  windows (HW3 low floor / capped ceiling, HW4 higher floor / newest ceiling) rather than
  one nested in the other; and **both rows straddle firmware 12.3 deliberately** — 32% of
  HW3's mass and 12% of HW4's sit below the cut — so firmware and `hw_gen` are correlated
  but not collinear. If they were collinear, the sign flip signals.py plants at 12.3 would
  be indistinguishable from a real hardware effect and Phase 4 could not stratify on one
  while holding the other fixed. Weights are rollout-shaped, never uniform.
- **Revisit trigger:** re-derive this table from scratch before the Phase 3 firmware-trap
  exercise — that exercise's validity depends on the straddle, so it is the moment the
  reasoning has to be owned rather than read.

## Interview version

"The fleet generator isn't a random-number generator with a schema on top — it's a vehicle state machine. I integrate one physical state forward at 10 Hz and derive the correlated signals from it, because everything downstream reads transitions, not marginals: my miners key on TTC and jerk, and my safety metrics key on hard-brake events. To prove that mattered I built the naive version too — independent per-signal sampling — and measured kinematic consistency on both. The state machine violates its own physics on under 0.1% of transitions; the naive sampler violates on more than half. That checker then became a Dagster asset check, so the property is enforced continuously rather than assumed."
