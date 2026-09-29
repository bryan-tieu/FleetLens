ALTER TABLE {database}.raw_samples_v1
MODIFY COLUMN event_time DateTime64(6, 'UTC');
