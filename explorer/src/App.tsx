import { useEffect, useState } from "react";
import { api } from "./api";
import type {
  Cohort,
  Drive,
  DriveSummary,
  Event,
  EventDetail,
  MetricStatus,
} from "./types";

const initialSource = {
  dataset: "fleetlens-synthetic",
  snapshot: "fixture-v1",
};

const metres = (value: number) =>
  new Intl.NumberFormat("en-US", { maximumFractionDigits: 1 }).format(value);

function rate(value: number | null) {
  return value === null
    ? "Undefined"
    : new Intl.NumberFormat("en-US", { maximumFractionDigits: 1 }).format(value);
}

function statusLabel(status: MetricStatus) {
  return {
    ok: "Complete",
    insufficient_data: "Insufficient data",
    zero_exposure: "Zero exposure",
    incomplete_source: "Incomplete source",
  }[status];
}

function secondsBetween(start: string, end: string) {
  return (new Date(end).getTime() - new Date(start).getTime()) / 1000;
}

function Timeline({ drive, onEvent }: { drive: Drive; onEvent: (event: Event) => void }) {
  const intervals = drive.exposure.valid_intervals;
  const allTimes = [
    ...intervals.flatMap((interval) => [interval.start_time, interval.end_time]),
    ...drive.events.flatMap((event) => [event.start_time, event.end_time]),
  ];
  if (!allTimes.length) {
    return <div className="empty-timeline">No eligible intervals in this drive.</div>;
  }
  const origin = allTimes.reduce((a, b) => (a < b ? a : b));
  const last = allTimes.reduce((a, b) => (a > b ? a : b));
  const duration = Math.max(1, secondsBetween(origin, last));
  const x = (time: string) => 48 + (secondsBetween(origin, time) / duration) * 804;

  return (
    <div className="timeline-wrap">
      <svg
        viewBox="0 0 900 154"
        role="img"
        aria-label="Valid exposure intervals and hard-braking episodes over event time"
      >
        <line x1="48" y1="124" x2="852" y2="124" className="axis" />
        {[0, 0.5, 1].map((fraction) => (
          <g key={fraction}>
            <line
              x1={48 + fraction * 804}
              y1="118"
              x2={48 + fraction * 804}
              y2="130"
              className="tick"
            />
            <text x={48 + fraction * 804} y="148" textAnchor="middle" className="axis-text">
              +{metres(duration * fraction)}s
            </text>
          </g>
        ))}
        <text x="48" y="24" className="row-label">VALID EXPOSURE</text>
        <text x="48" y="78" className="row-label">BRAKING EPISODE</text>
        {intervals.map((interval, index) => (
          <rect
            key={`${interval.start_time}-${index}`}
            x={x(interval.start_time)}
            y="34"
            width={Math.max(2, x(interval.end_time) - x(interval.start_time) - 2)}
            height="26"
            rx="5"
            className="exposure-bar"
          >
            <title>{`${metres(interval.distance_m)} m · ${interval.start_time} to ${interval.end_time}`}</title>
          </rect>
        ))}
        {drive.events.map((event) => (
          <rect
            key={event.start_time}
            x={x(event.start_time)}
            y="87"
            width={Math.max(3, x(event.end_time) - x(event.start_time) - 2)}
            height="25"
            rx="5"
            className="event-bar"
            onClick={() => onEvent(event)}
          >
            <title>{`Episode starting at ${event.start_time}`}</title>
          </rect>
        ))}
      </svg>
      <div className="timeline-key">
        <span><i className="swatch swatch-exposure" /> Eligible interval</span>
        <span><i className="swatch swatch-event" /> Hard braking</span>
        <span className="muted">Blank space is excluded from valid exposure.</span>
      </div>
    </div>
  );
}

export default function App() {
  const [draft, setDraft] = useState(initialSource);
  const [source, setSource] = useState(initialSource);
  const [cohort, setCohort] = useState<Cohort | null>(null);
  const [selectedDrive, setSelectedDrive] = useState<DriveSummary | null>(null);
  const [drive, setDrive] = useState<Drive | null>(null);
  const [selectedEvent, setSelectedEvent] = useState<Event | null>(null);
  const [detail, setDetail] = useState<EventDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);
    setCohort(null);
    setSelectedDrive(null);
    setDrive(null);
    setSelectedEvent(null);
    setDetail(null);
    api.cohort(source.dataset, source.snapshot)
      .then((result) => {
        if (!active) return;
        setCohort(result);
        setSelectedDrive(result.drives.find((item) => item.episode_count > 0) ?? result.drives[0] ?? null);
      })
      .catch((cause: Error) => { if (active) setError(cause.message); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [source]);

  useEffect(() => {
    if (!selectedDrive) return;
    let active = true;
    setDrive(null);
    setSelectedEvent(null);
    setDetail(null);
    api.drive(source.dataset, source.snapshot, selectedDrive.drive_key[2], selectedDrive.drive_key[3])
      .then((result) => {
        if (!active) return;
        setDrive(result);
        setSelectedEvent(result.events[0] ?? null);
      })
      .catch((cause: Error) => { if (active) setError(cause.message); });
    return () => { active = false; };
  }, [source, selectedDrive]);

  useEffect(() => {
    if (!selectedDrive || !selectedEvent) return;
    let active = true;
    setDetail(null);
    api.event(
      source.dataset,
      source.snapshot,
      selectedDrive.drive_key[2],
      selectedDrive.drive_key[3],
      selectedEvent.source_sample_keys[0][4],
    )
      .then((result) => { if (active) setDetail(result); })
      .catch((cause: Error) => { if (active) setError(cause.message); });
    return () => { active = false; };
  }, [source, selectedDrive, selectedEvent]);

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand"><span className="brand-mark">FL</span><span>FleetLens</span></div>
        <span className="topbar-note">TELEMETRY EXPLORER <span>·</span> M1 LOCAL DEMO</span>
      </header>

      <main>
        <section className="hero">
          <div className="hero-copy">
            <div className="eyebrow"><span className="live-dot" /> SYNTHETIC DATA · VERSIONED METRIC</div>
            <h1>From a signal to a <em>traceable event.</em></h1>
            <p>Inspect hard-braking episodes and the valid distance behind their rate. Every result stays linked to a source snapshot and sample sequence.</p>
          </div>
          <form
            className="source-form"
            onSubmit={(event) => {
              event.preventDefault();
              setSelectedDrive(null);
              setDrive(null);
              setSelectedEvent(null);
              setDetail(null);
              setError(null);
              setSource({ dataset: draft.dataset.trim(), snapshot: draft.snapshot.trim() });
            }}
          >
            <div className="form-title">OPEN SNAPSHOT <span>01 / SOURCE</span></div>
            <label>Dataset ID<input value={draft.dataset} onChange={(event) => setDraft({ ...draft, dataset: event.target.value })} required /></label>
            <label>Snapshot ID<input value={draft.snapshot} onChange={(event) => setDraft({ ...draft, snapshot: event.target.value })} required /></label>
            <button type="submit">Load snapshot <span aria-hidden="true">↗</span></button>
          </form>
        </section>

        {error && <div className="alert error" role="alert">Request failed: {error}. Check that the API and local ClickHouse are running, and that the snapshot was loaded.</div>}
        {loading && <div className="loading" role="status">Reading guarded snapshot…</div>}

        {cohort && <>
          <section className="snapshot-bar" aria-label="Snapshot provenance">
            <div><span className="small-label">SOURCE</span><strong>{cohort.dataset_id} / {cohort.snapshot_id}</strong></div>
            <div><span className="small-label">DEFINITION</span><strong>{cohort.definition_version}</strong></div>
            <div><span className="small-label">ORIGIN</span><strong className="origin-pill">Generated · synthetic</strong></div>
            <div className={`snapshot-status ${cohort.source_complete ? "complete" : "incomplete"}`}>
              <span className="status-dot" /> {cohort.source_complete ? "Source complete" : "Source incomplete"}
            </div>
          </section>

          {!cohort.source_complete && <div className="alert warning" role="status">
            The stored source is incomplete or contains quarantined rows. Counts below describe available samples; the rate is undefined.
          </div>}

          <section className="metrics-grid" aria-label="Cohort metrics">
            <article className="metric-card metric-primary"><span className="small-label">HARD-BRAKING EPISODES</span><strong>{cohort.episode_count}</strong><span>Distinct episode windows</span></article>
            <article className="metric-card"><span className="small-label">VALID DISTANCE</span><strong>{metres(cohort.valid_distance_m)}<small>m</small></strong><span>Eligible sample intervals only</span></article>
            <article className="metric-card"><span className="small-label">RATE / 100 KM</span><strong>{rate(cohort.episodes_per_100_km)}</strong><span>{statusLabel(cohort.status)} · synthetic example</span></article>
            <article className="metric-card"><span className="small-label">SOURCE ACCOUNTING</span><strong>{cohort.source_accepted_rows ?? "—"}<small> / {cohort.source_input_rows ?? "—"}</small></strong><span>Accepted / input · {cohort.source_rejected_rows ?? "—"} rejected</span></article>
          </section>

          <section className="panel strata-panel" aria-label="Vehicle strata">
            <div className="panel-heading"><div><span className="section-index">BY VEHICLE</span><h2>Source strata</h2></div><span className="count-pill">{cohort.vehicles.length} vehicles</span></div>
            <p className="panel-intro">Each vehicle rate divides its total episodes by its own valid distance. These synthetic vehicles are illustrative strata, not a representative fleet.</p>
            <div className="strata-list">
              {cohort.vehicles.map((item) => <div className="strata-row" key={item.vehicle_id}>
                <strong>{item.vehicle_id}</strong>
                <span>{item.episode_count} episode{item.episode_count === 1 ? "" : "s"}</span>
                <span>{metres(item.valid_distance_m)} m valid</span>
                <span>{rate(item.episodes_per_100_km)} / 100 km</span>
              </div>)}
            </div>
          </section>

          <div className="content-grid">
            <section className="panel drive-list-panel">
              <div className="panel-heading"><div><span className="section-index">02 / COHORT</span><h2>Drives</h2></div><span className="count-pill">{cohort.drive_count} drives</span></div>
              <p className="panel-intro">Select a drive to inspect its valid intervals and event windows.</p>
              <div className="drive-list">
                {cohort.drives.map((item) => (
                  <button
                    key={item.drive_key.join("/")}
                    className={`drive-item ${selectedDrive?.drive_key.join("/") === item.drive_key.join("/") ? "selected" : ""}`}
                    onClick={() => {
                      setSelectedEvent(null);
                      setDetail(null);
                      setError(null);
                      setSelectedDrive(item);
                    }}
                    type="button"
                  >
                    <span className="drive-name">{item.drive_key[3]}<small>{item.drive_key[2]}</small></span>
                    <span className="drive-meta"><strong>{item.episode_count}</strong> event{item.episode_count === 1 ? "" : "s"}<small>{metres(item.valid_distance_m)} m valid</small></span>
                    <span className="chevron" aria-hidden="true">›</span>
                  </button>
                ))}
              </div>
            </section>

            <section className="panel timeline-panel">
              <div className="panel-heading"><div><span className="section-index">03 / DRIVE</span><h2>Event timeline</h2></div>{drive && <span className="count-pill">{drive.sample_count} samples</span>}</div>
              {drive ? <>
                <div className="drive-context"><strong>{drive.drive_key[3]}</strong><span>{statusLabel(drive.status)} · {drive.exposure.valid_seconds}s valid · {drive.exposure.excluded_gap_count} excluded gap{drive.exposure.excluded_gap_count === 1 ? "" : "s"}</span></div>
                <Timeline drive={drive} onEvent={setSelectedEvent} />
                <div className="event-buttons">
                  {drive.events.length ? drive.events.map((event) => (
                    <button key={event.start_time} className={`event-button ${selectedEvent?.start_time === event.start_time ? "active" : ""}`} onClick={() => setSelectedEvent(event)} type="button">
                      <span className="event-dot" /> Episode · sequence {event.source_sample_keys[0][4]} <span>↗</span>
                    </button>
                  )) : <span className="muted">No qualifying hard-braking episode in this drive.</span>}
                </div>
              </> : <div className="panel-loading">Select a drive to load its timeline.</div>}
            </section>
          </div>

          <section className="panel detail-panel">
            <div className="panel-heading"><div><span className="section-index">04 / TRACE</span><h2>Event detail</h2></div><span className="count-pill">SOURCE LINEAGE</span></div>
            {detail ? <div className="detail-grid">
              <div className="detail-main"><span className="small-label">HARD-BRAKING WINDOW</span><strong>{detail.event.start_time.slice(11, 19)} <span>→</span> {detail.event.end_time.slice(11, 19)} <small>UTC</small></strong><p>Definition {detail.event.definition_version}. Acceleration at each source sample applies until the next eligible sample.</p></div>
              <div className="lineage"><span className="small-label">SUPPORTING SOURCE SEQUENCES</span><div>{detail.event.source_sample_keys.map((key) => <span className="sequence-chip" key={key.join("/")}>#{key[4]}</span>)}</div><p>{detail.event.drive_key[0]} / {detail.event.drive_key[1]} / {detail.event.drive_key[3]}</p></div>
            </div> : <p className="empty-detail">Choose an episode to inspect its source keys. A drive without events has no event detail.</p>}
          </section>

          <footer><span>FleetLens · Local portfolio demonstration</span><span>Generated telemetry is not a real fleet safety measurement.</span></footer>
        </>}
      </main>
    </div>
  );
}
