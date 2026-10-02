# Production bridge: FleetLens concepts in real systems

Every concept FleetLens implements is a small, inspectable version of a pattern that production data platforms depend on. This guide connects each one to its production counterpart so Bryan can explain **why the pattern exists**, which **guarantee it provides**, and **where the FleetLens version stops**, in terms another engineer recognizes.

**Evidence status.** This is explanation material, like the [M0 guide](m0-concepts.md). Reading it does not change a [ledger](README.md) state; a *bridge check* answered by Bryan does (see [How bridge checks are assessed](#how-bridge-checks-are-assessed)). The production patterns described here are public, widely documented industry practice. Nothing here describes Tesla's internal systems, and FleetLens has not been run at production scale.

## The pipeline, named in production terms

```text
 source bytes ──► adapter ──► contract ──► validate / quarantine ──► append-only raw ──► guarded logical read ──► pure metric ──► versioned rate
 (JSONL +         (units,      (value        (dead-letter queue,        (bronze / at-least-     (idempotent consumer,    (functional    (metrics / semantic
  manifest)        decoded      object,       reconciliation,            once landing zone)      fail-closed dedup)       core)           layer)
                   once)        data          write-audit-publish)
                                contract)
 ─────────────── lineage: dataset · snapshot · source key · schema/normalization versions · content hash travel with every row ───────────────
```

Each stage below is one *bridge card*. The cards are grouped by pipeline stage and numbered for linking from the ledger and walkthroughs.

### Card format

| Line | Meaning |
|---|---|
| **In FleetLens** | What is implemented, with the file that implements it |
| **Production name** | The pattern name an interviewer or teammate would use |
| **How production systems do it** | Established tools and practices that provide the same guarantee |
| **Where FleetLens stops** | The gap between this local slice and a production deployment |
| **Defensible claim** | One interview sentence bounded by actual evidence |
| **Bridge check** | A question that requires connecting both sides; answers go in dated evidence |

---

## Stage 1: Identity and lineage

### B1. Grain and source identity

- **In FleetLens:** one `CanonicalSample` is one source observation. `sample_key` = (dataset, snapshot, vehicle, drive, source_sequence) identifies it independent of its values ([sample.py](../../src/fleetlens/contracts/sample.py)).
- **Production name:** *declaring the grain* (Kimball dimensional modeling); *natural / business keys*; *idempotency keys*.
- **How production systems do it:** warehouse teams write down the grain of every fact table before choosing columns, because a join at the wrong grain silently multiplies rows. Payment APIs such as Stripe accept a client-supplied idempotency key so a retried request is recognized as the same logical operation. Streaming systems key messages by entity so all events for a vehicle stay ordered in one partition.
- **Where FleetLens stops:** the key is defined and enforced within a file and at the logical read, but there is no revision/correction protocol that declares which of two versions of a key is authoritative.
- **Defensible claim:** "I defined an explicit source key that excludes signal values, so a decoder correction keeps the same logical identity rather than looking like a new observation."
- **Bridge check:** Why does a payment idempotency key deliberately *not* include the amount, and which part of `sample_key` design follows the same reasoning?

### B2. Provenance and lineage

- **In FleetLens:** every sample carries origin (synthetic/real), source pointer, source schema version, normalization version, and generation config ID; storage adds row content hash and snapshot hash ([clickhouse.py](../../src/fleetlens/storage/clickhouse.py)).
- **Production name:** *data lineage* and *dataset versioning*.
- **How production systems do it:** lineage standards such as OpenLineage emit run-level metadata from each job so a catalog can answer "which inputs and code produced this table?" Column-level lineage in data catalogs lets an engineer find every dashboard affected by a bad upstream decode. Regulated and ML teams tag training data with source and version so a model result can be traced to exact inputs.
- **Where FleetLens stops:** lineage lives on each row, not in a queryable lineage graph. No orchestrator records run IDs yet (planned M2).
- **Defensible claim:** "Each stored sample records whether it is synthetic or real, and which schema and normalization versions produced it, so a metric can be traced back to its snapshot."
- **Bridge check:** A decode bug is found in normalization `v3`. Using only FleetLens's per-row fields, how would you find every affected row, and what does a lineage graph add on top of that?

### B3. Deterministic hash assignment and snapshot identity

- **In FleetLens:** each vehicle's scenario comes from `sha256(seed:vehicle_id)`, not a shared random stream, so adding a vehicle never shifts another vehicle's assignment. The snapshot ID is a hash of the generation inputs ([generator.py](../../src/fleetlens/simulation/generator.py)).
- **Production name:** *deterministic bucketing* (experiment assignment); *hash partitioning*; *content-derived identifiers*.
- **How production systems do it:** feature-flag and A/B platforms commonly assign a user to a variant by hashing (experiment salt + user ID), so assignment is stable across servers and restarts without storing it. Distributed databases and Kafka place a record in a partition by hashing its key. Container images and Git objects are named by the hash of their content.
- **Where FleetLens stops:** weights are invented scenario probabilities, not measured prevalence, and the hash-to-float conversion is only used for a small categorical choice.
- **Defensible claim:** "I used per-entity hashing instead of a shared RNG so the fleet can grow without changing existing vehicles' scenarios, and tested that directly."
- **Bridge check:** An A/B platform uses `hash(user_id)` with no experiment salt for every experiment. What correlation problem appears, and how does FleetLens's `seed` play the salt's role?

---

## Stage 2: Contracts and the wire boundary

### B4. Contracts and runtime invariants

- **In FleetLens:** frozen, slotted dataclasses validate every field in `__post_init__`: nonempty IDs, nonnegative integer sequence, UTC-aware time, finite numbers, origin-specific provenance rules ([sample.py](../../src/fleetlens/contracts/sample.py), [contract tests](../../tests/test_contracts.py)).
- **Production name:** *data contracts*; *value objects*; *"parse, don't validate"*; *schema registry compatibility*.
- **How production systems do it:** teams publish schemas (Avro, Protobuf, JSON Schema) to a registry such as Confluent Schema Registry, which rejects a producer change that breaks the declared compatibility mode (backward, forward, full). Services use validation libraries such as Pydantic to turn untrusted input into a typed object once, so downstream code never sees an invalid value. Data contracts add ownership and semantic expectations to the schema.
- **Where FleetLens stops:** the contract is a Python class, not a published, cross-language schema, and there is no automated compatibility check between versions.
- **Defensible claim:** "Invalid samples cannot be constructed: the contract rejects bools-as-ints, NaN, non-UTC times, and inconsistent provenance at the boundary."
- **Bridge check:** Schema registries check *structure*. Name one error FleetLens's contract would accept that no schema registry would catch either, and which stage must catch it.

### B5. Units and the normalize-once boundary

- **In FleetLens:** canonical speed is m/s and longitudinal acceleration is m/s² (positive forward). Conversion belongs to a source adapter that runs once before a sample is constructed and records its normalization version. The contract never rescales values.
- **Production name:** *anti-corruption layer* (domain-driven design); *canonical data model*; *coordinate and unit conventions*.
- **How production systems do it:** robotics stacks standardize SI units and a body frame; ROS REP 103 specifies SI units and x-forward, y-left, z-up, and ISO 8855 defines the vehicle axis system. Integration layers translate each external format into one internal model at the edge. NASA's Mars Climate Orbiter was lost in 1999 when one team's software produced pound-force seconds while the consumer expected newton-seconds; both values were structurally valid numbers.
- **Where FleetLens stops:** the generator already emits SI (`identity-si/v1`). No real-source or firmware-version adapter exists yet (M2).
- **Defensible claim:** "I designed normalization to happen exactly once at the adapter and recorded its version on each row, so downstream code never rescales a canonical signal."
- **Bridge check:** Trace 36 km/h through a correct adapter and through a pipeline that converts twice. Which Mars Climate Orbiter–style check would catch each, and why can't the contract?

### B6. Time: UTC, event time, and precision

- **In FleetLens:** `event_time` must be timezone-aware with zero UTC offset; the metric sorts by event time, not arrival order. Storage was migrated to microsecond precision and a live round trip of `123456` µs was tested ([003 migration](../../src/fleetlens/storage/migrations/003_event_time_microseconds.sql)).
- **Production name:** *event time versus processing time*; *timestamp precision and type mapping*.
- **How production systems do it:** stream processors such as Apache Flink and Apache Beam window data by when an event happened, using watermarks to decide when late data is too late. Platforms store UTC and convert only for display, avoiding daylight-saving ambiguities. Columnar formats declare timestamp units (Parquet supports milliseconds, microseconds, or nanoseconds), and a mismatch silently truncates precision when data moves between systems.
- **Where FleetLens stops:** batch only. There are no watermarks or late-arrival policy, and ordering is established per drive in memory.
- **Defensible claim:** "The metric orders samples by event time and rejects contradictory sequence order, so it produces the same result for any read order."
- **Bridge check:** At 10 Hz, why would millisecond storage be enough while a 1 kHz IMU needs microseconds? What result changes if precision is silently truncated?

### B7. Safe diagnostics and strict parsing

- **In FleetLens:** quarantine records contain line numbers and reasons, never raw row content. The JSON reader rejects duplicate field names and requires exactly the v1 field set. Unsupported wire versions reject the snapshot ([jsonl.py](../../src/fleetlens/ingestion/jsonl.py)).
- **Production name:** *log redaction / PII-safe diagnostics*; *strict parsing and version gates*.
- **How production systems do it:** logging pipelines redact or hash sensitive fields before logs reach shared systems, because logs are often retained longer and read more widely than the source data. RFC 8259 leaves duplicate JSON keys implementation-defined, so two parsers can read different values from the same bytes; security-conscious services reject them. Protocol consumers refuse an unknown major version rather than guessing.
- **Where FleetLens stops:** there is no real location data to redact yet. [privacy.md](../privacy.md) controls are planned, not implemented.
- **Defensible claim:** "Rejection reasons are designed to be safe to share: they identify the line and the rule, not the record."
- **Bridge check:** A future real GPS row fails validation. Which fields could leak through an error message that echoes input, and why is a duplicate `speed_mps` key a correctness problem as well as a security problem?

---

## Stage 3: Ingestion and accounting

### B8. Manifests, content hashes, and snapshot integrity

- **In FleetLens:** `manifest.json` declares snapshot identity, versions, row count, and SHA-256 of the exact JSONL bytes. A mismatch rejects the whole snapshot. Storage hashes a canonical JSON form of each sample (sorted keys, fixed separators), records a load receipt with source-file hash and row accounting, and guards against two hashes under one snapshot ID ([cli.py](../../src/fleetlens/cli.py), [jsonl.py](../../src/fleetlens/ingestion/jsonl.py), [clickhouse.py](../../src/fleetlens/storage/clickhouse.py)).
- **Production name:** *table format manifests and snapshots*; *checksums*; *canonical serialization*.
- **How production systems do it:** Apache Iceberg and Delta Lake track a table as immutable data files listed by metadata files. A commit atomically swaps a pointer to new metadata, so readers see a whole snapshot or none of it, and can time-travel to older ones. Object stores such as S3 support end-to-end checksums on upload. Hashing structured data requires one canonical byte form, since `{"a":1,"b":2}` and `{"b":2,"a":1}` are equal but hash differently.
- **Where FleetLens stops:** the two output files are not written atomically, and a hash proves consistency with the manifest, not authenticity; someone can change both. No signing exists.
- **Defensible claim:** "Ingestion refuses a snapshot whose bytes don't match its manifest hash or row count, so a truncated or edited file can't be partially loaded as if it were complete."
- **Bridge check:** A crash happens after `samples.jsonl` is written but before `manifest.json`. What does a reader see today, and how does Iceberg's pointer-swap commit prevent the equivalent state?

### B9. Validation, quarantine, and reconciliation

- **In FleetLens:** within a trusted snapshot, a malformed row is quarantined with a reason while valid rows continue. The report enforces `input = accepted + rejected` and raises if accounting does not reconcile.
- **Production name:** *dead-letter queue (DLQ)*; *data quality tests*; *reconciliation / control totals*; *write-audit-publish*.
- **How production systems do it:** message systems (Kafka Connect, SQS) route unprocessable messages to a DLQ so one bad record does not block the stream. dbt tests and Great Expectations assert data expectations in the pipeline. Finance ETL reconciles control totals between source and target. The write-audit-publish pattern writes to a staging branch, runs checks, then publishes atomically; Iceberg branches support it.
- **Where FleetLens stops:** no quarantine replay or reprocessing workflow, no alert thresholds (for example "fail if more than 1% quarantined"), and whole-file in-memory reads.
- **Defensible claim:** "Every input line is accounted for exactly once, as accepted or quarantined with a reason, and the report fails if the counts don't reconcile."
- **Bridge check:** A DLQ is quietly receiving 30% of messages and nobody notices. Which FleetLens number would reveal the equivalent, and what policy is missing to turn it into an alert?

---

## Stage 4: Storage, replay, and schema change

### B10. Append-only raw storage with a guarded logical read

- **In FleetLens:** the raw table's grain is one accepted row per load; replays append. `logical_samples_v1` groups identical payloads; `sample_conflicts_v1` exposes a key with more than one content hash; `logical_count()` raises `StorageConflict` rather than picking a winner ([002 migration](../../src/fleetlens/storage/migrations/002_logical_samples.sql)). The bounded [stored metric read](../../src/fleetlens/storage/clickhouse.py) checks payload conflicts, source-file hash consistency, and persisted load accounting in one statement before returning a rate. A live test loaded concurrently to 44 physical and 11 logical rows; a separate fixture replay test kept its cohort result unchanged after 22 physical rows.
- **Production name:** *at-least-once delivery with an idempotent consumer*; *medallion (bronze/silver) layering*; *fail-closed deduplication*.
- **How production systems do it:** most pipelines deliver at least once, since retries after timeouts resend data. Exactly-once *outcomes* come from idempotent writes keyed on a stable ID, not from the transport. Lakehouse designs land raw data untouched in a bronze layer and derive a cleaned silver layer, so a bug can be fixed by recomputing rather than re-ingesting. ClickHouse's `ReplacingMergeTree` collapses duplicates only during background merges, so queries still need `FINAL` or explicit grouping for correct counts.
- **Where FleetLens stops:** grouping every selected snapshot key at query time is fine for 11 rows and unmeasured beyond that. The response is capped, but no query-latency result or revision protocol exists; a conflicting insert is visible but not rolled back.
- **Defensible claim:** "I kept the raw layer append-only and made logical reads fail closed on same-key payload conflicts. A local concurrent-load test kept 11 logical rows while physical rows grew to 44."
- **Bridge check:** Kafka redelivers a batch after a consumer crash. Map each FleetLens object (raw table, logical view, conflict view, `logical_count()`) to what the consumer would need, and explain why a read-before-insert check is not enough under concurrency.

### B11. Concurrency and the check-then-act race

- **In FleetLens:** loaders do not check "does this key exist?" before inserting. Correctness comes from the read-side guard, and a local file lock serializes first-time migrations ([clickhouse.py](../../src/fleetlens/storage/clickhouse.py)).
- **Production name:** *TOCTOU (time-of-check to time-of-use) race*; *optimistic versus pessimistic concurrency*; *leases and distributed locks*.
- **How production systems do it:** two writers that both check "not present" and then insert both succeed. Databases avoid this with unique constraints or conditional writes (for example a DynamoDB conditional put). Distributed coordination uses leases with expiry (via etcd, ZooKeeper, or a database row) so a crashed holder does not block others forever.
- **Where FleetLens stops:** the migration lock is a same-host temp file with no expiry; a crashed process leaves a stale lock that an operator must remove. It is not a distributed coordinator.
- **Defensible claim:** "I avoided a read-before-insert race by making duplicates harmless at read time instead of trying to prevent them at write time."
- **Bridge check:** Two hosts run `fleetlens-load` for the first time at once. Which guarantee breaks, and what would a lease with expiry change?

### B12. Versioned schema migrations

- **In FleetLens:** numbered SQL files are applied in order and recorded in `schema_migrations`; migration 003 widened timestamp precision without deleting rows ([migrations/](../../src/fleetlens/storage/migrations/)).
- **Production name:** *schema migration tooling*; *expand/contract (parallel change)*.
- **How production systems do it:** Flyway records applied versions in `flyway_schema_history`, and Alembic in `alembic_version`. Zero-downtime changes use expand/contract: add the new form, backfill and dual-write, move readers, then remove the old form, so old and new code can run at the same time.
- **Where FleetLens stops:** no rollback, no checksum of already-applied files, and no multi-version reader period.
- **Defensible claim:** "Schema changes are versioned files recorded in a history table, and I upgraded an existing table's precision in place without losing rows."
- **Bridge check:** Someone edits `001_raw_samples.sql` after it was applied. Why does FleetLens not notice, and what does Flyway's stored checksum do about it?

---

## Stage 5: Transformation and metrics

### B13. Pure transformations separated from I/O

- **In FleetLens:** `assign_scenario`, `generate_fleet`, and `evaluate_drives` take values and return values. CLIs and the storage layer do all file and network work ([hard_braking_v1.py](../../src/fleetlens/metrics/hard_braking_v1.py)).
- **Production name:** *functional core, imperative shell*; *hexagonal (ports and adapters) architecture*.
- **How production systems do it:** a pure core can be unit-tested without databases, reused from batch jobs, APIs, and notebooks, and rerun to reproduce a result. Spark separates lazy transformations from actions that trigger I/O; dbt models are SELECT statements while the tool handles materialization.
- **Where FleetLens stops:** the metric runs in memory per drive. The next task reads guarded ClickHouse rows into it and must show that SQL results equal this reference.
- **Defensible claim:** "The metric is a pure function over canonical samples, so the same code is testable in isolation and reusable against files or the database."
- **Bridge check:** Where exactly is the shell/core line in the load path? Name one bug that would be hard to test if `evaluate_drives` opened the ClickHouse connection itself.

### B14. Event episodes from interval data

- **In FleetLens:** acceleration applies until the next sample; adjacent qualifying intervals merge into one maximal episode; a gap over one second or a nonqualifying interval ends it. Fixture: one [1, 3) episode.
- **Production name:** *gaps-and-islands*; *sessionization / session windows*; *debouncing and hysteresis*.
- **How production systems do it:** analytics SQL groups consecutive qualifying rows into "islands" using window functions (`LAG`, running sums). Web analytics defines a session by an inactivity gap. Flink and Beam provide session windows keyed by gap duration. Embedded and alerting systems debounce signals so one noisy condition does not fire many times.
- **Where FleetLens stops:** Python only; the equivalent SQL is not yet written. The thresholds (≤ −3 m/s², at least 2 s) are an illustrative definition, not calibrated against real driving.
- **Defensible claim:** "The detector counts one hard-braking episode per contiguous run, not one per sample, and the gap policy ends episodes instead of bridging missing data."
- **Bridge check:** Write the gaps-and-islands idea in words for the brake drive: which rows start a new island, and which SQL window function finds them?

### B15. Exposure-normalized rates and undefined denominators

- **In FleetLens:** the rate is episodes per 100 km of *valid* distance. Gaps add neither distance nor time; no eligible intervals → `insufficient_data`; zero distance → `zero_exposure`; incomplete stored source accounting → `incomplete_source`. All have a null rate. The bounded snapshot [cohort summary](../../src/fleetlens/metrics/stored_v1.py) sums counts and distance before dividing; the complete frozen fixture yields one episode over 66 m ([hard-braking-v1](../metrics/hard-braking-v1.md)).
- **Production name:** *exposure-adjusted rates*; *ratio of sums versus mean of ratios*; *NULL-safe division*; *Simpson's paradox*.
- **How production systems do it:** road safety statistics are stated per vehicle miles traveled (NHTSA reports fatalities per 100 million VMT). California DMV autonomous-testing reports pair disengagements with miles driven. Warehouse SQL guards division with `NULLIF(denominator, 0)` so zero exposure yields NULL, not 0 or an error. Rates are compared within strata (road type, weather, speed band), because a pooled comparison can reverse when groups have different mixes.
- **Where FleetLens stops:** vehicle-ID strata exist for one synthetic snapshot, but there are no scenario/firmware strata, confidence intervals, or event-ascertainment correction. The fixture is too small for a fleet claim.
- **Defensible claim:** "The rate uses an independent valid-distance denominator, excludes gaps from exposure, and reports undefined rather than zero when there is no exposure."
- **Bridge check:** Drive A: 1 episode / 1 km. Drive B: 0 episodes / 99 km. Compare the mean of per-drive rates with the ratio of sums, and say which one a fleet dashboard should show.

### B16. Versioned metric definitions

- **In FleetLens:** `hard-braking/v1` fixes units, grain, population, numerator, denominator, gap policy, undefined states, and lineage in one [definition](../metrics/hard-braking-v1.md) that matches `MetricDefinition` in code.
- **Production name:** *metrics layer / semantic layer*; *metric changelog*.
- **How production systems do it:** tools such as the dbt Semantic Layer (MetricFlow) and Looker's LookML define a metric once so every dashboard computes it the same way. Mature teams version a definition when its threshold or population changes and annotate charts at the change, so a trend break is not mistaken for a real-world shift.
- **Where FleetLens stops:** one version exists; no cross-version comparison or backfill has been done.
- **Defensible claim:** "The metric has a written, versioned definition, including what counts as undefined, before any dashboard consumes it."
- **Bridge check:** A teammate changes the threshold to −2.5 m/s² in place. What happens to last month's chart, and what should `v2` include to prevent that confusion?

---

## Stage 6: Verification and reproducibility

### B17. Independent test oracle

- **In FleetLens:** [tiny_expected.json](../../tests/fixtures/tiny_expected.json) froze hand-calculated answers (one episode, 66 m, eight seconds, [2, 5) excluded) *before* the metric code existed, and [test_metrics.py](../../tests/test_metrics.py) checks against it.
- **Production name:** *test oracle*; *golden files*; *differential testing*; *reference implementation*.
- **How production systems do it:** a slow, obviously correct reference implementation checks a fast, optimized one on the same inputs. Database projects run the same query against multiple engines to find disagreements (SQLancer is one research tool for this). Data migrations run old and new pipelines in parallel (*shadow mode*) and compare outputs before cutover.
- **Where FleetLens stops:** one tiny fixture; no property-based tests or generated input comparison yet.
- **Defensible claim:** "Expected results were fixed independently before the implementation, so the test can't pass by recomputing the implementation's own answer."
- **Bridge check:** The next task writes the metric in SQL. Describe the differential test between SQL and `evaluate_drives`, and name one input where they would plausibly disagree.

### B18. Reproducible builds and verification evidence

- **In FleetLens:** pinned development dependencies, Python pinned to 3.11, installable wheel, Ruff/Black/pytest, a Windows + Linux CI matrix, and same-machine byte-identical generation ([environments.md](../environments.md)).
- **Production name:** *lockfiles and hermetic builds*; *CI matrices*; *build provenance*.
- **How production systems do it:** lockfiles with hashes pin exact artifacts; hermetic build systems such as Bazel limit a build to declared inputs; supply-chain frameworks like SLSA attach provenance describing how an artifact was built.
- **Where FleetLens stops:** pins without hashes; cross-platform byte identity untested; the hosted CI pass on record predates the generator.
- **Defensible claim:** "Generation is byte-identical on the machine where I tested it; I haven't verified cross-platform identity."
- **Bridge check:** Why is "requirements pinned" weaker than "requirements hash-locked"? Give one attack or accident each one does or doesn't stop.

---

## Stage 7: Serving and exploration

### B19. Bounded read API and client views

- **In FleetLens:** the [fixed WSGI routes](../../src/fleetlens/api/app.py) serve cohort, drive, and event JSON after a guarded stored read; the [React explorer](../../explorer/src/App.tsx) displays source accounting, vehicle strata, eligible intervals, and event source keys. The [demo command](../../src/fleetlens/demo.py) prepares the fixture and starts both local servers.
- **Production name:** *read model*; *backend for frontend*; *aggregate-to-detail drill-down*; *query cost guardrail*.
- **How production systems do it:** a serving layer gives clients stable domain operations instead of database access, bounds expensive scans, and lets users trace aggregate values to contributing records. Larger systems often precompute read models, paginate detail, authenticate requests, and monitor request cost and latency.
- **Where FleetLens stops:** loopback-only single-process WSGI, a small bounded snapshot, no authentication or pagination, and no representative fleet data. The frontend does not prove the displayed rate is useful for real decisions.
- **Defensible claim:** “I served a validated synthetic metric through fixed bounded routes and traced a displayed episode to its source sample keys.”
- **Bridge check:** Follow the displayed 1,515.2 rate and the event chip #1 to their API responses and stored source keys. Why should the browser not recompute exposure from the timeline rectangles?

---

## Scale ladder: what changes as volume grows

| Stage | FleetLens now | First thing that breaks at larger scale | Typical production response |
|---|---|---|---|
| Ingestion | Whole snapshot in memory | Memory, single-file throughput | Streaming or chunked reads; parallel workers per file |
| Snapshot commit | Two separate file writes | Partial snapshots after a crash | Atomic metadata commit (Iceberg/Delta) |
| Quarantine | Report file | Nobody reads it | Quarantine table, rate alerts, replay tooling |
| Raw storage | One batch per load, local HTTP | Insert size, retries with unknown outcome | Batched async inserts, insert deduplication tokens |
| Logical read | Group every key at query time | Query latency on large tables | Pre-deduplicated materialization, partition pruning by snapshot/date |
| Migrations | Same-host file lock | Multiple hosts | Migration job with leases; expand/contract rollouts |
| Metric | In-memory Python per drive | Fleet-wide scans | Same definition in SQL or Spark, differentially tested against the Python reference |
| Rates | Per drive | Small-sample noise, mixed strata | Stratified rates with uncertainty intervals |

These rows are expected pressures from common practice, not measured FleetLens limits. Measure before claiming one.

## Next bridges (planned, not implemented)

These ledger rows have no FleetLens code yet. Their cards are written when the feature exists, so the "In FleetLens" line is never invented.

| Planned FleetLens concept | Production counterpart to cover |
|---|---|
| Dagster assets and checks (M2) | Asset-based orchestration, freshness/quality checks that block downstream materialization |
| Real-data adapter and firmware semantics (M2) | Schema evolution, effective-from decoder versioning, backfills |
| Admission budgets and selection (M3) | Trigger-based data collection, sampling bias, reservoir and stratified sampling |
| Training/evaluation isolation (M4) | Data leakage, time- and entity-based splits, dataset cards |

## How bridge checks are assessed

A bridge check is a new kind of learning evidence, recorded like any other interaction in the dated [learning files](README.md#record-evidence-by-day). A strong answer has three parts:

1. **Mechanism:** what FleetLens actually does, with the concrete record or number (for example 22 physical / 11 logical rows).
2. **Pattern:** the production pattern and the guarantee it provides.
3. **Difference:** one way the FleetLens version is weaker or scoped differently, and what would have to change.

An answer with all three, in Bryan's own words, supports **demonstrated** for the matching ledger row. An answer that names the pattern but not the mechanism stays at **explained**. Record the answer and its assessment only if Bryan actually gives it; model answers never go in the evidence log.

## Maintaining this guide

When a new walkthrough is written, add or update its bridge card in the same increment, and fill in the walkthrough's *Production analogue* section (see the [walkthrough template](../walkthroughs/README.md)). Keep every "In FleetLens" line tied to code that exists and every "Defensible claim" within the verified evidence in [status](../status.md).
