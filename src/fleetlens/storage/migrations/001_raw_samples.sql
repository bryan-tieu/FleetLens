CREATE DATABASE IF NOT EXISTS {database};

CREATE TABLE IF NOT EXISTS {database}.raw_samples_v1
(
    dataset_id String,
    snapshot_id String,
    vehicle_id String,
    drive_id String,
    source_sequence UInt64,
    event_time DateTime64(6, 'UTC'),
    speed_mps Float64,
    longitudinal_accel_mps2 Float64,
    origin LowCardinality(String),
    source_ref String,
    source_schema_version LowCardinality(String),
    normalization_version LowCardinality(String),
    generation_config_id String,
    schema_version LowCardinality(String),
    content_sha256 FixedString(64),
    snapshot_sha256 FixedString(64)
)
ENGINE = MergeTree
ORDER BY (dataset_id, snapshot_id, vehicle_id, drive_id, source_sequence);
