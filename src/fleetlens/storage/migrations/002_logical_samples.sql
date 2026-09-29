CREATE VIEW IF NOT EXISTS {database}.sample_conflicts_v1 AS
SELECT dataset_id, snapshot_id, vehicle_id, drive_id, source_sequence,
       uniqExact(content_sha256) AS content_versions, count() AS physical_rows
FROM {database}.raw_samples_v1
GROUP BY dataset_id, snapshot_id, vehicle_id, drive_id, source_sequence
HAVING content_versions > 1;

CREATE VIEW IF NOT EXISTS {database}.logical_samples_v1 AS
SELECT dataset_id, snapshot_id, vehicle_id, drive_id, source_sequence,
       any(event_time) AS event_time,
       any(speed_mps) AS speed_mps,
       any(longitudinal_accel_mps2) AS longitudinal_accel_mps2,
       any(origin) AS origin,
       any(source_ref) AS source_ref,
       any(source_schema_version) AS source_schema_version,
       any(normalization_version) AS normalization_version,
       any(generation_config_id) AS generation_config_id,
       any(schema_version) AS schema_version,
       any(content_sha256) AS canonical_content_sha256,
       count() AS physical_copies
FROM {database}.raw_samples_v1
GROUP BY dataset_id, snapshot_id, vehicle_id, drive_id, source_sequence
HAVING uniqExact(content_sha256) = 1;
