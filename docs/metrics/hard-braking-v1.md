# Hard-braking and valid-exposure definition — v1

**Purpose:** demonstrate traceable hard-braking episode detection with an independent valid-distance denominator. This is an illustrative driving-event metric, not a safety or real-fleet claim. **Definition owner:** Bryan, the FleetLens project maintainer. Implementation: [hard_braking_v1.py](../../src/fleetlens/metrics/hard_braking_v1.py).

**Version and change history:** `hard-braking/v1` was first implemented on 2026-09-30 against the previously frozen `tiny-oracle/v1`; there are no earlier published metric results to restate. A change to the threshold, minimum duration, interval eligibility, integration, event boundary, population, or rate units requires a new definition version. Results computed under an earlier version retain their version and snapshot identity; any later backfill or corrected decode must identify the affected snapshots and publish restated values explicitly rather than silently replacing them.

**Validated input scope:** the current evidence covers generated `fixture-v1` samples with `canonical-sample/v1`, source schema `synthetic-template/v1`, normalization `identity-si/v1`, and synthetic origin. The generator also writes `fleet-v1-*` snapshots using those same contracts, but the metric has not been independently evaluated across a generated fleet. The pure function accepts `CanonicalSample` objects and does not enforce source versions itself; the caller must validate provenance and use a guarded logical sample read. No real-source schema or normalization version is supported by this methodology yet.

| Property | Definition |
|---|---|
| Version | `hard-braking/v1` |
| Input | `CanonicalSample` in m/s and m/s², grouped by dataset, snapshot, vehicle, drive |
| Event grain | One maximal contiguous hard-braking episode per drive |
| Event rule | Acceleration at the earlier sample applies until the next sample. Eligible adjacent intervals with acceleration ≤ −3 m/s² join one episode. Count it when duration is at least 2 seconds. A nonqualifying interval or gap ends it. The end is exclusive. |
| Exposure grain | Eligible adjacent sample interval within a drive |
| Exposure rule | Sort by event time and require strictly increasing source sequence. Reject duplicate source keys or times. An interval over 1 second is a gap and contributes no duration or distance. Other adjacent intervals contribute elapsed seconds and trapezoidal distance: `(speed_start + speed_end) × seconds / 2`. |
| Time window | The full observed span of each drive, from its first sample through the last adjacent interval ending at its final sample. Event and interval windows are half-open `[start, end)` in UTC event time. No rolling or cross-drive reporting window is implemented; a later windowed report must state how boundary-crossing episodes are assigned. |
| Rate grain and population | One result for each observed dataset/snapshot/vehicle/drive. The population is that drive's eligible sample intervals. |
| Numerator | Count of qualifying episodes on that drive |
| Denominator | Valid distance in metres, independent of episode detection |
| Units | Episodes per 100 km: `episode_count × 100000 / valid_distance_m` |
| Undefined states | No eligible intervals → `insufficient_data`; eligible intervals with zero distance → `zero_exposure`; stored source accounting missing, inconsistent, or recording rejected rows → `incomplete_source`. All have a null rate, never zero. |
| Lineage | Each episode carries the source keys of its interval endpoints; each valid exposure interval carries its two source keys. Source keys identify dataset, snapshot, vehicle, drive, and sequence. |
| Stratification | Dataset, snapshot, vehicle, and drive are retained. A bounded snapshot cohort and explicit vehicle-ID summaries are implemented; scenario, firmware, and fleet-wide strata are not. Each aggregation sums episode counts and valid distance before division, not drive rates. |
| Uncertainty | No interval or error bar is estimated. The fixture is a fixed, generated example rather than a probability sample, so a sampling confidence interval would imply unsupported population inference. `Not estimated` is distinct from zero uncertainty. |

The frozen [tiny oracle](../../tests/fixtures/tiny_expected.json) expects one [1, 3) episode, 36 m and five seconds for the brake drive, and 30 m and three seconds for the gap drive. The [2, 5) gap is excluded. The [stored cohort summary](../walkthroughs/07-stored-metric-summaries.md) gives one episode over 66 m and eight valid seconds, or `100000 / 66` episodes per 100 km. This small synthetic result is intentionally unsuitable for a fleet claim.

The fixture test reconciles `11` input samples into two drives, `5 + 4 = 9` adjacent pairs, `8` eligible intervals plus one excluded gap, one episode, and `36 + 30 = 66 m`. The pure transform assumes validated canonical inputs. The stored metric additionally requires one source-file hash per snapshot ID, matching load receipts, accepted source rows equal to logical stored rows, and zero rejected source rows before publishing a rate. Identical replay rows and matching receipts may repeat without changing the logical result. A quarantined or interrupted source remains inspectable with an undefined rate.

Event-enriched uploads would bias the numerator. This definition applies only to the complete generated source snapshot being evaluated; it does not establish event ascertainment or representativeness for real fleet data. Missing events cannot be repaired merely by knowing exposure.
