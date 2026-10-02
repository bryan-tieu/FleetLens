export type SampleKey = [string, string, string, string, number];
export type DriveKey = [string, string, string, string];
export type MetricStatus =
  | "ok"
  | "insufficient_data"
  | "zero_exposure"
  | "incomplete_source";

export interface DriveSummary {
  drive_key: DriveKey;
  sample_count: number;
  episode_count: number;
  valid_seconds: number;
  valid_distance_m: number;
  status: MetricStatus;
  episodes_per_100_km: number | null;
}

export interface Cohort {
  dataset_id: string;
  snapshot_id: string;
  snapshot_hash: string | null;
  definition_version: string;
  data_origin: "synthetic";
  source_input_rows: number | null;
  source_accepted_rows: number | null;
  source_rejected_rows: number | null;
  source_complete: boolean;
  sample_count: number;
  drive_count: number;
  episode_count: number;
  valid_seconds: number;
  valid_distance_m: number;
  excluded_gap_count: number;
  status: MetricStatus;
  episodes_per_100_km: number | null;
  drives: DriveSummary[];
  vehicles: {
    vehicle_id: string;
    drive_count: number;
    episode_count: number;
    valid_distance_m: number;
    status: MetricStatus;
    episodes_per_100_km: number | null;
  }[];
}

export interface Event {
  drive_key: DriveKey;
  definition_version: string;
  start_time: string;
  end_time: string;
  source_sample_keys: SampleKey[];
}

export interface ValidInterval {
  start_time: string;
  end_time: string;
  distance_m: number;
  source_sample_keys: [SampleKey, SampleKey];
}

export interface Drive {
  drive_key: DriveKey;
  definition_version: string;
  sample_count: number;
  events: Event[];
  exposure: {
    definition_version: string;
    valid_seconds: number;
    valid_distance_m: number;
    valid_intervals: ValidInterval[];
    excluded_gap_count: number;
  };
  status: MetricStatus;
  episodes_per_100_km: number | null;
}

export interface EventDetail {
  data_origin: "synthetic";
  drive_status: MetricStatus;
  event: Event;
}
