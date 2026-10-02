CREATE TABLE IF NOT EXISTS {database}.snapshot_loads_v1
(
    dataset_id String,
    snapshot_id String,
    snapshot_sha256 FixedString(64),
    input_rows UInt64,
    accepted_rows UInt64,
    rejected_rows UInt64,
    completed_at DateTime64(3, 'UTC') DEFAULT now64(3)
)
ENGINE = MergeTree
ORDER BY (dataset_id, snapshot_id, snapshot_sha256);
