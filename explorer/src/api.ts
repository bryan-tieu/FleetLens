import type { Cohort, Drive, EventDetail } from "./types";

async function get<T>(path: string, params: Record<string, string>): Promise<T> {
  const query = new URLSearchParams(params);
  const response = await fetch(`${path}?${query}`, { cache: "no-store" });
  const body = await response.json();
  if (!response.ok) {
    throw new Error(body.error ?? `Request failed (${response.status})`);
  }
  return body as T;
}

export const api = {
  cohort: (dataset: string, snapshot: string) =>
    get<Cohort>("/api/v1/cohort", {
      dataset_id: dataset,
      snapshot_id: snapshot,
    }),
  drive: (dataset: string, snapshot: string, vehicle: string, drive: string) =>
    get<Drive>("/api/v1/drive", {
      dataset_id: dataset,
      snapshot_id: snapshot,
      vehicle_id: vehicle,
      drive_id: drive,
    }),
  event: (
    dataset: string,
    snapshot: string,
    vehicle: string,
    drive: string,
    startSequence: number,
  ) =>
    get<EventDetail>("/api/v1/event", {
      dataset_id: dataset,
      snapshot_id: snapshot,
      vehicle_id: vehicle,
      drive_id: drive,
      start_sequence: String(startSequence),
    }),
};
