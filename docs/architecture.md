# Architecture and boundaries

This describes the M1 local implementation and staged target boundaries. [status.md](status.md) owns current verification and remaining work.

## Implemented M1 path

The [synthetic generator](../src/fleetlens/simulation/generator.py) writes canonical JSONL and a manifest. The [ingestion reader](../src/fleetlens/ingestion/jsonl.py) validates the snapshot, quarantines invalid rows with safe reasons, and reconciles input counts. The [ClickHouse loader](../src/fleetlens/storage/clickhouse.py) appends accepted rows and load receipts. A bounded logical read collapses identical replay copies, rejects changed payloads or mixed source-file hashes, and marks missing/inconsistent receipts or quarantined source rows incomplete.

The [pure metric](../src/fleetlens/metrics/hard_braking_v1.py) turns ordered canonical samples into hard-braking episodes and independently calculated valid exposure. [Stored summaries](../src/fleetlens/metrics/stored_v1.py) aggregate counts and metres by snapshot and explicit vehicle ID before calculating rates. The [fixed API](../src/fleetlens/api/app.py) returns cohort, drive, and event JSON; the [explorer](../explorer/src/App.tsx) displays those results and episode source keys. The browser does not compute or rescale the metric. The local [demo runner](../src/fleetlens/demo.py) prepares the fixture, measures guarded reads, and starts the API and explorer from a prepared environment.

This implementation supports the M0 synthetic contract only. It reads a bounded snapshot into Python and uses a single-process loopback server. Real telemetry normalization, operational recovery orchestration, and representative fleet inference are M2 or later work.

## Initial data path

```text
seeded synthetic fixture (later: a separately adapted real telemetry subset)
  -> immutable input + provenance
  -> schema validation / canonical units ----> quarantine + reason
  -> ClickHouse canonical samples
       -> independently tracked valid exposure
       -> versioned driving-event detection
       -> stratified metric report
       -> bounded API -> cohort summary / drive timeline / event detail
```

The first demo uses Python, local files, ClickHouse, a small API, and React/TypeScript. Dagster follows when there are dependent assets to orchestrate. Streaming is added for M3 transport experiments, not as a prerequisite to proving the metric.

## Contracts and target decisions

| Object | Required decisions |
|---|---|
| Source snapshot | Dataset/version, content hash or manifest, real/generated flag, license/use notes, generation config where applicable |
| Canonical sample | Dataset-scoped vehicle/drive identity, event time and units, stable source sequence/sample identity, schema version, normalization version, source pointer |
| Invalid record | Run/source identity, rejection reason, safe diagnostic details, replay path |
| Driving event | Drive, event definition/version, start/end, merge/debounce rules, source sample references |
| Exposure | Eligible population/intervals, valid duration and distance, gap/exclusion rules, source snapshot and calculation version |
| Metric result | Definition/version, numerator and denominator, strata, units, uncertainty method, run/snapshot, data completeness |
| Selection manifest | Policy/version, observable features, candidates, chosen/rejected identities, byte costs, seed, evaluation split |

M1 sample, load-receipt, event, exposure, and metric contracts are implemented in the linked code and [versioned definition](metrics/hard-braking-v1.md). Selection manifests and broader uncertainty/recovery rules remain target decisions. Repeated loads preserve logical identity through guarded reads; ClickHouse engine choice alone is not a proof of idempotency.

## Measurement boundaries

Canonicalization happens at the source adapter boundary. Preserve the original encoding/version in lineage; consumers must not apply a wire conversion twice. Firmware overrides in the simulator are controlled fixtures, not assertions about actual vehicle behavior.

Hard braking is an episode, not every consecutive below-threshold sample. Define minimum duration, gaps, and episode merging. Integrate distance only across eligible intervals with an explicit method. The initial target is a driving-event metric, not evidence that an autonomous system is safe.

Retain exposure independently of expensive clip admission. Also account for event ascertainment: a denominator does not fix events missed by sampling or transmission. Show completeness and exclusions with the reported rate.

TTC needs relative distance/closing speed; cut-ins need neighboring-object/lane context; construction scenes need suitable scene evidence. Do not infer those labels from ego speed alone.

## Separate data products

Telemetry experiments establish ingest, event definitions, and upload policies. Image curation establishes training-data selection and held-out detector evaluation. Record each data product's own identities and lineage. No current mapping connects synthetic drives to BDD100K images, so the architecture does not claim that loop.

Public incident reports may inform a discussion of reporting limitations; they are not fleet-population weights or directly comparable rates without compatible exposure, definitions, and population. Synthetic cohort weights remain declared assumptions unless a suitable source supports them.

## Package structure, introduced incrementally

No implementation is carried over. Begin with one installable Python package and only the contracts needed for M0; add modules as consumers appear:

```text
src/fleetlens/
    contracts/       # schema, signal meaning, provenance
    simulation/      # synthetic fleet and scenario fixtures
    ingestion/       # source adapters, normalization, quarantine, replay
    selection/       # planned M3 trigger and admission policies
    metrics/         # events, exposure, versioned metric evaluation
    api/             # bounded serving interfaces
orchestration/       # Dagster definitions when M2 needs them
    storage/migrations/ # versioned ClickHouse DDL
explorer/            # frontend
tests/               # unit and focused integration tests
experiments/         # executable comparisons/configurations when built
reports/             # small shareable results; no restricted/raw data
```

This is a target layout, not a request to create empty modules now. Shared signal/sample contracts belong in fleetlens.contracts from their first implementation. Avoid a generic utility bucket or separate deployable services without a consumer.

## Technology decisions

ClickHouse demonstrates the role's analytical-storage requirement; document schema ordering against actual queries. Use versioned metric files before a database-backed registry. Plain local storage is sufficient until object-store behavior matters. Existing dataset adapters are allowed; implement and test project-specific meaning and policy.

A new service requires a concrete need, a failure/operating model, a useful acceptance check, and an entry in decisions.md. Benchmark reports include row/byte counts, hardware, cache conditions, query shape, and repetitions. Larger data volume is not itself proof of better engineering.
