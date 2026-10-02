# M1 JSONL validation and quarantine

## Purpose and contract

Roadmap M1 requires explicit validation and input accounting before samples reach ClickHouse. The M0 generator writes `samples.jsonl` and `manifest.json`. The [reader](../../src/fleetlens/ingestion/jsonl.py) returns validated `CanonicalSample` objects and rejected line numbers/reasons. The [report command](../../src/fleetlens/ingestion/cli.py) writes `validation.json` and `quarantine.jsonl` without copying raw record content into diagnostics. The later [load command](04-clickhouse-storage.md) uses this reader to store accepted samples.

The manifest declares the dataset snapshot, synthetic origin, schema/normalization versions, generation config, row count, and SHA-256 of the exact JSONL bytes. A bad manifest, hash, row count, or unsupported version rejects the snapshot. The hash detects a mismatch between the supplied files; it does not protect against someone changing both. Within a checked snapshot, a malformed row is quarantined while valid rows continue. Every input line is accepted once or rejected once.

## Trace one record

Run `python -m fleetlens.cli --output runs/tiny --fixture`, then `python -m fleetlens.ingestion.cli --input runs/tiny --output runs/tiny-validation` in the installed environment. The first fixture line decodes as one sample with dataset `fleetlens-synthetic`, snapshot `fixture-v1`, a vehicle and drive ID, and source sequence 0. Those five values form `sample_key`; speed and acceleration remain the already canonical m/s and m/s² values. The reader checks the row's provenance against the manifest before constructing the immutable sample. For the unmodified fixture, 11 input rows become 11 accepted and zero quarantined.

If the second line has `speed_mps: -1` and the manifest hash is updated to describe that changed input, line 2 is rejected with `speed_mps must be nonnegative`. The other valid lines remain accepted. If the JSONL is edited without updating the manifest, ingestion aborts on the hash mismatch, since the snapshot identity cannot be trusted. A second occurrence of the same source key within one file is rejected as a duplicate; first valid occurrence wins.

## Choice and limit

The reader validates into the existing canonical dataclass instead of adding a second schema library. That keeps the wire boundary small and reuses M0 domain rules; a schema library may help when more source formats arrive. The reader currently loads the small snapshot into memory and supports only the M0 synthetic manifest. It checks duplicates within one file and repeated reads return the same result. The standalone validator does not persist accepted rows or make writes atomic across report files. A later [M1 load path](04-clickhouse-storage.md) stores accepted rows and guards logical reads against duplicate or conflicting payloads.

## Verification and learning check

Local macOS Python 3.11.16: checks are recorded in [current status](../status.md). Tests cover fixture round trip, malformed/domain/provenance/duplicate rows, accounting, safe diagnostic reasons, unsupported versions, hash and count gates, and report output. Hosted CI for this increment is not yet recorded.

Optional teach-back: If a retry reads the same 11 valid lines, why does `read_snapshot` returning the same 11 samples **not** prove that ClickHouse would still contain only 11 rows after two loads? Identify the boundary that must enforce that rule.

## Production analogue

Quarantine with reconciled counts is a **dead-letter queue plus control totals**; the manifest hash is a small version of the snapshot manifests used by Apache Iceberg and Delta Lake, without their atomic commit. See [B7 strict parsing](../learning/production-bridge.md#b7-safe-diagnostics-and-strict-parsing), [B8 manifests](../learning/production-bridge.md#b8-manifests-content-hashes-and-snapshot-integrity), and [B9 quarantine](../learning/production-bridge.md#b9-validation-quarantine-and-reconciliation).
