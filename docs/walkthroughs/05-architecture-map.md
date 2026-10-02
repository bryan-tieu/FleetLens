# FleetLens source-to-explorer map

The [interactive Archify diagram](../../.archify/architecture-fleetlens-end-to-end-20260929-154317/fleetlens-end-to-end.html) maps committed FleetLens code at `14f4b6d3ee5c968ac5b44b4695c7d6e704ef1b55` and labels the unfinished M1 path **PLANNED**. Its [editable JSON](../../.archify/architecture-fleetlens-end-to-end-20260929-154317/candidate.json) contains source file and line references. Source links are local-only because the pinned commit's availability on the remote was not verified.

## Current inputs and outputs

1. [`fleetlens.cli`](../../src/fleetlens/cli.py) generates explicitly synthetic canonical samples. The scenario assignment hashes seed and vehicle ID, so adding vehicles does not reassign an existing one. It writes exact UTF-8 `samples.jsonl` bytes and a `manifest.json` with count, source and normalization versions, generation parameters, and a SHA-256 of the JSONL bytes.
2. [`read_snapshot`](../../src/fleetlens/ingestion/jsonl.py) checks the manifest and whole-file hash before examining rows. It then enforces exact v1 fields, canonical units and provenance, and a unique source key within the file. It returns accepted samples, rejected line numbers with allowlisted safe reasons, and reconciled counts. A bad manifest, hash, or declared row count rejects the entire snapshot.
3. The [standalone validation command](../../src/fleetlens/ingestion/cli.py) writes `quarantine.jsonl` and `validation.json`. The separate [ClickHouse loader](../../src/fleetlens/storage/cli.py) calls the same reader, inserts accepted samples, and prints rejected counts; it does **not** write a quarantine file. Run the standalone command when a persisted row-level rejection report is needed.
4. [`ClickHouseStore`](../../src/fleetlens/storage/clickhouse.py) applies versioned migrations and inserts JSONEachRow over local HTTP. [`raw_samples_v1`](../../src/fleetlens/storage/migrations/001_raw_samples.sql) retains each physical load. The [logical view](../../src/fleetlens/storage/migrations/002_logical_samples.sql) groups copies by dataset, snapshot, vehicle, drive, and source sequence when their content hashes agree. `logical_count()` rejects a source key with changed payload rather than choosing a value. The local Compose service is in [`infra/clickhouse/compose.yaml`](../../infra/clickhouse/compose.yaml).

## One record through the path

The fixed fixture's `fixture-brake` drive has a source-sequence 1 sample at `2026-01-01T00:00:01Z`, speed 12 m/s, and longitudinal acceleration −4 m/s². The generator marks it synthetic and writes it with snapshot `fixture-v1`. The reader checks the enclosing file hash and versioned fields, then constructs a `CanonicalSample` with the source key `(fleetlens-synthetic, fixture-v1, fixture-brake, fixture-brake-brake-drive, 1)`. The loader writes one raw row with that key and a content hash. Loading the same snapshot again creates another physical row, while the guarded logical count still treats the identical copies as one source observation. If a later row reuses that key with changed canonical content, the guarded read raises `StorageConflict`.

## Planned continuation and metric meaning

The dashed path after logical samples is design, not running code. Hard-braking detection will turn consecutive qualifying samples into **episodes**, so sample count will not masquerade as event count. Valid exposure will independently integrate eligible time and distance, excluding gaps. A versioned stratified metric will join an event numerator to a valid-exposure denominator; zero exposure must be undefined. The fixture's one episode and 66 m of valid distance are hand-calculated expectations for future tests, not computed results today. A bounded API and React explorer will then expose cohort summary, drive timeline, and source-traceable event detail.

## Why these boundaries

Canonical units and provenance are set before storage so downstream code does not reinterpret the same wire values. Whole-snapshot checks prevent a corrupt file from producing trusted rows; row quarantine still salvages valid rows from an intact snapshot. Append-only raw storage preserves replay evidence, while the logical boundary handles identical retries and detects changed-payload conflicts. A simpler read-before-insert dedupe would race under concurrent loaders. This design currently targets a small local synthetic dataset: repeated physical rows consume space, logical grouping costs query work, the load is not a distributed transaction, and event ascertainment or real-fleet representativeness has not been established.

## Verification and learning

Archify `finalize` passed schema/layout validation, delivery, strict artifact check, and Chrome browser check with no diagnostics. A separate visual check passed containment, readability, viewer chrome, theme states, and captures; the light desktop capture was inspected. The [final receipt](../../.archify/architecture-fleetlens-end-to-end-20260929-154317/review-3/fleetlens-end-to-end.finalize-summary.json) is bound to the HTML artifact. This verifies the diagram's structure and browser presentation, not the planned metric or API. Bryan's architecture teach-back remains unassessed.

Optional teach-back: trace where an invalid row is persisted in each CLI path, then explain why two identical raw rows count as one logical sample while two changed payloads with one key stop the guarded read.

## Production analogue

The map's stages line up with production pipeline layers: adapter, data contract, dead-letter quarantine, bronze raw storage, idempotent logical read, functional-core metric, and a semantic metrics layer. The [pipeline overview](../learning/production-bridge.md#the-pipeline-named-in-production-terms) names each one and links to its card.
