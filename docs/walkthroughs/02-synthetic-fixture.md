# Synthetic fleet fixture and assignment

**Scope:** M0, JD rows 9 and 10. Implemented locally on 2026-09-29. All telemetry here is invented; these templates are not calibrated to or representative of any real fleet.

## Input and output

`GenerationConfig` takes a nonnegative integer seed and three finite, nonnegative scenario probabilities in steady/brake/gap order that sum to one. `assign_scenario(vehicle_id, config)` hashes the seed and vehicle ID into a draw, so one vehicle's assignment does not consume randomness needed by another. `generate_fleet` sorts vehicle IDs before output and rejects duplicates. A fleet-size change creates a new snapshot ID but preserves the existing vehicle's scenario and signal timeline.

`fleetlens --output runs/tiny --fixture` writes fixed two-drive samples. `fleetlens --output runs/fleet-10 --vehicles 10 --seed 20260929 --weights 0.5 0.3 0.2` writes a weighted fleet. Both commands write canonical SI values as JSONL and a manifest with the synthetic origin, source and normalization versions, configuration, count, and SHA-256 of the sample file. The files contain no actual vehicle observations.

## Trace one record

The first fixture-brake record has source sequence 0 at 2026-01-01T00:00:00Z, speed 12 m/s, and longitudinal acceleration 0 m/s². Its provenance identifies `fleetlens-synthetic`, snapshot `fixture-v1`, `synthetic-template/v1`, and `identity-si/v1`. The next record is one second later with acceleration -4 m/s², a value applying over the following one-second interval in this fixture's frozen rule. The immutable `CanonicalSample` contract validates each generated record. The CLI serializes UTC as `Z`; a downstream adapter will have to validate the JSONL again at ingestion.

## Independent expected result

The [oracle](../../tests/fixtures/tiny_expected.json) is stored separately from the generator and fixes the future metric interpretation before any miner exists. An acceleration at a sample applies until the next sample. Two consecutive one-second intervals at or below -3 m/s² produce one episode over seconds [1, 3). Valid distance uses trapezoidal speed integration across adjacent samples no more than one second apart. The brake drive has 36 m of valid distance. The gap drive excludes [2, 5), leaving 30 m. Together the fixture expects one episode and 66 m over eight valid seconds. These are hand calculations for invented data, not an observed event rate.

## Choice and limits

Hashing identity is simpler and more stable under fleet growth than using one shared seeded random stream. The scenario templates are intentionally small and discrete. Assignment probabilities define a generated cohort, not a measured fleet distribution. A 64-bit hash draw is stable under the tested Python environment; byte-identical output is verified on this machine, not promised across all runtimes. A malformed probability or duplicate vehicle ID fails before output. Since this M0 increment, [ingestion validation](03-jsonl-ingestion.md), [storage replay handling](04-clickhouse-storage.md), and [event/exposure transforms](06-hard-braking-metric.md) were added; the missing interval is now tested as excluded exposure.

**Verified at M0 completion:** 64 local tests passed; Ruff, Black, pip dependency check, and `git diff --check` passed. Repeated CLI generation yielded byte-identical output in the test. A hosted result for this generator increment has not been recorded.

**Optional teach-back:** Why would a single `random.Random(seed)` loop change vehicle 7 when earlier vehicles are inserted? What should happen to the [2, 5) gap when calculating distance?

## M0 engineering takeaways

The goal is to be able to explain, diagnose and change this small pipeline. You
do not need to memorize its Python syntax. Read these files in flow order:
`contracts/sample.py` → `simulation/generator.py` → `cli.py` →
`tests/fixtures/tiny_expected.json` and `tests/test_simulation.py`.

### 1. Define the grain and meaning before storing data

**Grain** means what one row represents: here, one source observation for one
vehicle in one drive. Speed is a nonnegative magnitude in m/s; acceleration is
in m/s², with braking during forward motion negative. A dataclass groups those
fields; `frozen=True` prevents normal reassignment after construction, and
`__post_init__` checks invariants, meaning conditions that must always hold.
An enum limits origin to the supported synthetic/real categories.

These checks catch negative speed or missing provenance. They cannot detect a
valid number with the wrong meaning: 36 km/h must become 10 m/s at the source
adapter boundary, but a mislabeled `speed_mps=36` still passes numeric checks.
This boundary becomes essential when real data starts in M2.

### 2. Identity and values answer different questions

The source key is `(dataset, snapshot, vehicle, drive, source_sequence)`. It
answers which observation this is. Speed and normalization version describe
its decoded values and interpretation. Fixing a unit conversion should retain
the source key. A different snapshot changes the key deliberately. Identity
provides a basis for replay handling; it does not itself prevent duplicate
database rows. That behavior still needs an ingestion/storage policy and tests.

### 3. A seed alone does not guarantee stable assignment

With a shared random stream, each loop iteration consumes the next draw. If
vehicle A gets draw 1 and B gets draw 2, inserting X first makes A get draw 2
and B get draw 3. The seed is unchanged, but existing assignments shift.

Our draw depends on SHA-256 of the seed and vehicle ID, so changing caller
order or adding other vehicles does not affect it. Sorting IDs stabilizes
output order. Changing the seed or scenario probabilities may still change
assignment. The snapshot hash also includes the complete set of vehicle IDs,
so fleet growth creates a different snapshot even when A's signals stay equal.

### 4. Keep transformation separate from file operations

The generator returns validated sample objects; it does not write files. The
CLI parses arguments, invokes generation, serializes UTC timestamps and enums,
and writes the samples and manifest. This separation makes transformations
easy to exercise in tests and reuse later in ingestion or orchestration.

The current CLI constructs everything in memory and writes two files in
sequence. At larger scale we would stream batches and publish a manifest only
after a complete write, with a recovery policy for interrupted output. Current
reproducibility tests do not establish crash-safe publishing.

### 5. Expected answers must come from independent reasoning

An **oracle** is the expected answer used to judge a result. If the future
event detector also computes its own expected test result, a shared bug could
make both agree. Our tiny expected-results file freezes hand calculations
before that detector exists. It is an input to future metric tests; M0 does
not yet prove a working detector or exposure computation.

For seconds 1→2, speed falls from 12 to 8 m/s. Trapezoidal integration uses
average speed times elapsed time: `(12 + 8) / 2 × 1 = 10 m`. The brake drive's
five intervals contribute `12 + 10 + 6 + 4 + 4 = 36 m`. Two braking intervals
are one continuous episode, not two events. The gap drive contributes 30 m
because its three-second missing interval exceeds the one-second gap limit.
We do not invent observations to fill it.

### 6. Evidence has a scope

The manifest records provenance (where data came from), generation parameters,
versions, row count and a hash of serialized samples. A hash helps detect changed
bytes; it does not prove the data is realistic, complete or correctly decoded.
Passing tests establish the cases they exercised. They do not establish real
fleet prevalence, production scale, replay recovery, or Bryan's understanding.

**Two optional diagnostic checks:**

1. A source reports 36 km/h and the output has `speed_mps=36`. Why can the
   current contract accept it, and where should the repair happen?
2. Someone computes 96 m for the tiny fixture by filling its missing interval
   at 10 m/s. Which frozen rule did they violate, and why would that affect a
   braking event rate?

These explanations were delivered on 2026-09-29. Answers and independent
modification evidence remain pending in the learning ledger.

## Production analogue

Per-vehicle hashing is **deterministic bucketing**, the same technique A/B platforms use to keep users in stable experiment groups. The frozen oracle is a **test oracle / reference answer**, the basis of differential testing between a reference and an optimized implementation. See [B3](../learning/production-bridge.md#b3-deterministic-hash-assignment-and-snapshot-identity), [B13](../learning/production-bridge.md#b13-pure-transformations-separated-from-io), and [B17](../learning/production-bridge.md#b17-independent-test-oracle).
