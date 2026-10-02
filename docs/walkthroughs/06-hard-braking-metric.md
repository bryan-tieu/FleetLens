# M1 hard-braking and valid exposure

## Purpose and contract

The first metric transform consumes validated `CanonicalSample` values and returns one `DriveMetric` per source drive. It detects episodes, integrates valid distance, and reports a drive rate only when distance is positive. [Definition v1](../metrics/hard-braking-v1.md) fixes the units, population, threshold, gap policy, and grain. The code is pure: it reads no file or database and writes nothing.

## Trace one fixture record

In the brake drive, sequence 1 is at second 1 with speed 12 m/s and acceleration −4 m/s². Its acceleration applies to the [1, 2) interval; sequence 2 also has −4 m/s² for [2, 3). Both are valid one-second intervals, so [metrics/hard_braking_v1.py](../../src/fleetlens/metrics/hard_braking_v1.py) joins them into one [1, 3) episode. The event retains source keys for sequences 1, 2, and 3. Sequence 3 closes the episode; its acceleration is 0 for [3, 4).

Exposure is calculated on every eligible adjacent interval, regardless of acceleration. The brake drive's speeds yield `12 + 10 + 6 + 4 + 4 = 36 m` over five seconds. In the other drive, [2, 5) is a three-second gap, so it adds neither exposure nor an event interval; its remaining three one-second intervals add 30 m. The two-drive fixture therefore has one episode, 66 m, and eight valid seconds. [test_metrics.py](../../tests/test_metrics.py) compares these values to the independently frozen oracle.

## Choice, alternative, and failure mode

The transform sorts samples by event time, then rejects duplicate times or source sequences that contradict time order. A caller can pass rows in any order without changing the result. Trusting caller order would be simpler, but an unordered database read could change episodes and distance. A duplicated source key is rejected rather than silently counted twice. An interval over one second ends an episode and is excluded from exposure. If all intervals are gaps, the status is `insufficient_data`; if valid intervals cover zero distance, the status is `zero_exposure`. Both rates are undefined.

This code does not query ClickHouse, aggregate cohorts, estimate uncertainty, correct event ascertainment, or validate real telemetry. Storage callers must use the guarded logical-read boundary before invoking it; physical replay rows or changed-payload conflicts would invalidate a metric. At larger scale, the same definition can be implemented in bounded SQL or batches, with equality tests against this small pure reference.

## Learning check

Optional teach-back: Why does the [2, 5) gap add no metres or seconds, even though the speeds on either side are 10 m/s? If a drive has one valid stationary second, why is its event rate undefined rather than zero?

## Production analogue

Episode merging is the SQL **gaps-and-islands** pattern and a stream processor's **session window**. The rate is an **exposure-adjusted rate** like per-VMT road-safety statistics; undefined results match SQL `NULLIF` division, and cohort rates must be a ratio of sums, not a mean of ratios. The written definition is a small **metrics layer** entry. See [B14](../learning/production-bridge.md#b14-event-episodes-from-interval-data), [B15](../learning/production-bridge.md#b15-exposure-normalized-rates-and-undefined-denominators), and [B16](../learning/production-bridge.md#b16-versioned-metric-definitions).
