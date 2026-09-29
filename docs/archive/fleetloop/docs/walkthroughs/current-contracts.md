> Archived FleetLoop reference. Commands, implementation claims, and agent rules here are historical, not active FleetLens instructions. See [migration context](../../../../migration.md). Links have been relocated; source code remains in the original repository.

# Current signal and fleet contracts

Status: read-through of existing code, 2026-09-28. This is not a completed fleet generator or a passing test report.

## What the two files are for

fleetgen/signals.py describes the meaning of telemetry: units, valid domains, sign conventions, and wire-to-canonical scaling metadata. A schema that says "float" cannot tell you whether a steering value means radians or degrees; the signal contract supplies that meaning.

fleetgen/fleet.py describes synthetic vehicles and their cohort attributes. Correlated assignment makes controlled stratification experiments possible. These tables do not establish the demographics or firmware rollout of a real fleet.

## Follow a request

In signals.py, spec("steering_angle_rad") returns the canonical signal description: radians, left-positive, and the declared valid range. Passing a firmware string parses it into integer components and applies all configured overrides effective at or before that version.

Currently FIRMWARE_OVERRIDES is empty, so passing firmware does not change that description. spec returns metadata; it does not itself ingest or convert a telemetry row. A future adapter must use the scale/offset contract explicitly and preserve its version in lineage.

The tuple comparison in parse_version assumes a numeric dotted-version convention. Before accepting arbitrary version strings, define handling of malformed input and trailing zero equivalence; do not silently assume a full semantic-versioning implementation.

## The unfinished boundary

fleet.py currently cannot import because _validate_tables is incomplete. Its public construction helpers are stubs. The intended chain is region -> model -> hardware -> firmware, with stable per-vehicle randomness.

Weighted choice must agree with validation. Some declared rows sum to 1.001 and a valid zero weight exists. Decide explicitly whether the inputs are relative weights or rounded probabilities; validate finite/nonnegative values and positive totals, then normalize only under that contract. A validator allowing rounding while the sampler rejects it is a broken boundary.

## Why this matters downstream

An incorrect unit can change which samples qualify as events. Unstable assignment can change a cohort between benchmark runs. Incorrect probability validation can prevent any data generation. These are small contracts with consequences throughout the pipeline.

Next verification is specified in [session-02](../daily/session-02.md). No numerical generator or calibration result is available yet.

## Optional teach-back

1. Why can a signal have a valid numeric type but the wrong meaning?
2. What would happen if an ingestion adapter applied the steering scale twice?
3. Why should requesting a larger fleet preserve the attributes assigned to an existing vehicle ID?

Answers are pending. The assistant should record only Bryan's actual responses in the learning record.
