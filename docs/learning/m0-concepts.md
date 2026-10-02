# M0 learning guide: executable foundation

M0 is **implemented and locally verified**; this page is the set of concepts its code can teach. Reading it is an explanation, not evidence that Bryan has demonstrated each skill. The [competency ledger](README.md) and [dated answers](2026-09-29.md) track assessment separately. Start with the [foundation](../walkthroughs/01-python-foundation.md) and [fixture](../walkthroughs/02-synthetic-fixture.md) record traces. The [production bridge](production-bridge.md) connects each section below to the production pattern it corresponds to.

## 1. Data grain, identity, and provenance

One `CanonicalSample` represents one source observation for a vehicle in a drive. Its `sample_key` is `(dataset, snapshot, vehicle, drive, source_sequence)`. That key identifies the observation; speed and acceleration are values of it. A corrected decode retains the key and needs an explicit revision/conflict policy. Provenance records synthetic versus real origin, source pointer, schema version, normalization version, and generation configuration. The manifest adds row count and a hash of the serialized JSONL bytes. A matching hash proves consistency with that manifest, not publisher authenticity or physical realism.

**Trace:** fixture-brake sequence 1 belongs to `fixture-v1` and has speed 12 m/s and acceleration -4 m/s². Its source key stays the same if a decoder correction changes a value. See [sample.py](../../src/fleetlens/contracts/sample.py) and [cli.py](../../src/fleetlens/cli.py). M1 storage now has an explicit identical-replay and changed-payload rule; M0's key alone does not enforce it.

## 2. Dataclasses, enums, and invariants

A dataclass groups named, typed fields. `frozen=True` prevents normal reassignment after construction; `slots=True` limits dynamic attributes. `__post_init__` enforces runtime **invariants**, conditions every constructed value must satisfy: nonempty identifiers, nonnegative integer sequence, UTC-aware event time, finite numbers, and nonnegative speed. `DataOrigin` is an enum so origin is one of the supported categories. Type annotations communicate intent but do not replace these checks. Synthetic provenance requires a generation configuration ID; real provenance forbids one.

**Failure example:** `speed_mps=-1` raises `ValueError`; `speed_mps=36` can pass while still meaning the wrong thing if the source value was 36 km/h. See [contract tests](../../tests/test_contracts.py). Object validation does not establish ordering, completeness, realistic motion, or a fleet event.

## 3. Units and normalization boundary

Canonical speed is a nonnegative magnitude in m/s. Longitudinal acceleration is m/s², positive forward and negative for braking during forward motion. A source adapter must convert 36 km/h to 10 m/s **before** constructing `CanonicalSample` and record the decoder version. Consumers then read the canonical value without rescaling it. The M0 generator already emits SI values, so it records `identity-si/v1`; it does not implement a km/h or firmware adapter. A numeric domain check cannot detect every semantically wrong unit.

**Check:** identify the input unit, conversion, canonical field, and place where a second conversion would create an error. A real-data adapter and changed firmware semantics remain M2 work.

## 4. Seeded assignment and random streams

A seed only reproduces a **particular sequence of draws**. With one shared stream, inserting a vehicle early consumes a draw and shifts later assignments. M0 hashes `seed:vehicle_id`, converts the first 64 digest bits to a draw in `[0, 1)`, and walks cumulative scenario weights. Each vehicle's draw is independent of iteration order and fleet size. `generate_fleet` sorts IDs for stable output. Changing the seed or weights may change assignments; adding a vehicle changes the snapshot ID even if old vehicles' signals stay the same. The weights are invented scenario probabilities, not measured fleet prevalence.

**Check:** compare vehicle 7's scenario before and after adding vehicle 2; then explain why a shared `random.Random(seed)` loop could change it. See [generator.py](../../src/fleetlens/simulation/generator.py) and [simulation tests](../../tests/test_simulation.py).

## 5. Pure transformations versus file I/O

`assign_scenario`, `generate_fleet`, and `generate_fixture` return values without writing files. The CLI parses arguments, serializes records, and writes `samples.jsonl` plus `manifest.json`. This boundary lets tests exercise the transformation without a filesystem and lets another caller reuse it. The CLI writes UTF-8 bytes explicitly so the manifest hashes the exact bytes. Repeating generation with the same inputs yields byte-identical output on the checked machine; the current two-file write is not an atomic publication or crash-recovery protocol.

**Trace:** `--fixture` creates 11 `CanonicalSample` objects, serializes each as one JSONL line with UTC `Z`, hashes the bytes, then writes the manifest. In weighted-fleet mode, a malformed weight fails before output. See [CLI](../../src/fleetlens/cli.py).

## 6. Independent test oracle and exposure arithmetic

An **oracle** is the expected answer against which an implementation is checked. [tiny_expected.json](../../tests/fixtures/tiny_expected.json) freezes hand calculations separately from the generator and before the M1 event/exposure transforms. Acceleration at a sample applies until the next sample. On the brake drive, intervals [1, 2) and [2, 3) both meet the -3 m/s² threshold and form **one** episode [1, 3). Valid distance uses average endpoint speed times elapsed seconds only when adjacent samples are at most one second apart: `12 + 10 + 6 + 4 + 4 = 36 m` on the brake drive. The gap drive contributes `10 + 10 + 10 = 30 m`; [2, 5) is excluded. Total valid exposure is 66 m over eight seconds. This is synthetic expected truth, not a measured fleet rate, and M0 does not compute the metric.

**Failure example:** filling [2, 5) at 10 m/s incorrectly adds 30 m. If the numerator remains one episode, that changes `1/66` to `1/96` episodes/m and lowers the reported rate. The M1 transform must be tested against the frozen oracle, not calculate its own expected answer.

## 7. Reproducibility and evidence limits

The supported setup pins Python 3.11 and development/build dependencies, builds an installable wheel, and runs pytest, Ruff, Black, and dependency checks. CI is configured for Windows and Linux. The recorded hosted pass covers the earlier foundation commit; later M0 generator behavior has local verification, not a recorded hosted result. The tests establish the specified examples and invariants, not cross-platform byte identity, calibrated vehicle physics, fleet representativeness, or production throughput. See [environment setup](../environments.md) and [current status](../status.md).

## Optional M0 teach-back

1. Trace fixture-brake sequence 1 from generator to JSONL: state its key, values, units, and provenance. Which checks run before it is written?
2. Explain why adding a vehicle leaves an existing vehicle's assignment stable but changes the snapshot ID.
3. Diagnose a source value of 36 km/h written as `speed_mps=36`, and explain why object validation can pass it.
4. Recompute the brake and gap distances and identify the exact interval excluded from the 66 m oracle.

These are prompts, not recorded answers. An independent explanation or bounded code/debugging change should be added to the dated learning evidence only after Bryan supplies it.
