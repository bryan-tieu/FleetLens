# M1 local ClickHouse storage and replay

## Purpose and input/output contract

The [JSONL reader](../../src/fleetlens/ingestion/jsonl.py) returns validated canonical samples and quarantined line numbers. The [storage boundary](../../src/fleetlens/storage/clickhouse.py) sends only accepted samples to local ClickHouse. It prints input, accepted, quarantined, physical, and logical counts. The [compose file](../../infra/clickhouse/compose.yaml) runs a pinned ClickHouse image on localhost; the [versioned migrations](../../src/fleetlens/storage/migrations/001_raw_samples.sql) define the schema and [logical views](../../src/fleetlens/storage/migrations/002_logical_samples.sql).

The raw table grain is **one accepted row from one load**. Its sort order starts with the stable source key: dataset, snapshot, vehicle, drive, and source sequence. That order supports the upcoming drive/source lookup and groups duplicates near each other, but ClickHouse's sort key does not enforce uniqueness. Event time is stored at microsecond precision, matching the Python contract. Canonical speed/acceleration, source/normalization versions, source pointer, synthetic origin, row content hash, and snapshot hash remain available for traceability.

The logical sample grain is **one source key with one canonical payload**. `logical_samples_v1` groups identical raw copies but is an internal building block, not a safe standalone metric source. `sample_conflicts_v1` lists keys with distinct canonical payload hashes. The public Python `logical_count()` checks both counts in one grouped query and raises `StorageConflict` if any key disagrees. Future metric queries must implement the same conflict guard; directly counting the raw table would double-count replays, and directly reading the unguarded logical view could omit a disputed key.

## Trace the fixture and one failure

For the fixed synthetic fixture, the first row has dataset `fleetlens-synthetic`, snapshot `fixture-v1`, a vehicle and drive ID, and source sequence 0. The reader validates it and gives the storage layer a `CanonicalSample`. The storage layer hashes the complete canonical payload, writes the row with its source key and provenance, then queries the grouped logical state.

On the first load, 11 accepted samples yield 11 physical and 11 logical rows. Loading the same snapshot again appends 11 more physical rows; the logical count stays 11 because each repeated key has the same content hash. In the isolated live test, two additional concurrent loads made 44 physical rows while the logical count stayed 11. The loaders did not need a separate read-before-insert check, which could race.

If a row arrives with the same source key but a changed speed, it has a different content hash. The raw table preserves both versions, the conflict view exposes that key, and `logical_count()` raises instead of picking a winner. The unguarded view would omit that key, which is why the Python API does not expose a general logical-view `count()` method. The conflicting insert is already in the raw table; this is a visible fail-stop condition, not a transaction that rolled back. A future explicit correction/revision protocol must decide which version is authoritative.

## Choice, alternative, and limits

This small local slice favors an append-only audit trail plus a guarded logical read. A pre-insert existence check could avoid some physical copies but needs concurrency control and a changed-value policy. `ReplacingMergeTree` could eventually collapse duplicate rows, but its background merging is not a query-time uniqueness guarantee; using `FINAL` or another explicit query rule would still be required. The current view uses exact grouping and is appropriate for the tiny demonstration, not a measured high-volume design.

Applied migration filenames are recorded in `schema_migrations`. The third migration upgrades an already-created local table from milliseconds to microseconds without deleting rows. A temporary-file lock serializes migration setup for local loaders on the same host; a crashed process can leave a stale lock that an operator must inspect and remove. This is not a distributed migration coordinator and has no rollback. The HTTP client sends one batch per load and does not provide a distributed transaction; a crash or timeout can leave an uncertain physical write. Logical replay remains stable for identical rows, while partial failures, corrections, larger datasets, and query latency remain to be exercised. The service uses local development credentials and only synthetic data. No real fleet data, event detector, exposure calculation, or rate is stored here.

## Verification and teach-back

The integration tests use isolated temporary databases and remove them after testing. They check first and repeated loads, two concurrent loads, concurrent first-load migration, a microsecond timestamp round trip, and a same-key changed payload. Exact local check results and the ClickHouse version are in [current status](../status.md). ClickHouse documentation describes why a [primary key is for query performance rather than uniqueness](https://clickhouse.com/blog/a-simple-guide-to-clickhouse-query-optimization-part-1) and why [background replacement needs an explicit query-time rule](https://clickhouse.com/resources/engineering/clickhouse-optimize-table-final).

Optional teach-back: after two fixture loads, why can `count()` on the raw table be 22 while the guarded logical count is 11? What would happen if one of those 22 rows had the same source key but a different speed?

## Production analogue

Append-only raw rows with a guarded logical read are **at-least-once delivery with an idempotent consumer** and a **bronze/silver** layer split; refusing to choose between conflicting payloads is **fail-closed deduplication**. Skipping read-before-insert avoids a **check-then-act race**, and the migration table mirrors Flyway/Alembic history. See [B10](../learning/production-bridge.md#b10-append-only-raw-storage-with-a-guarded-logical-read), [B11](../learning/production-bridge.md#b11-concurrency-and-the-check-then-act-race), and [B12](../learning/production-bridge.md#b12-versioned-schema-migrations).
