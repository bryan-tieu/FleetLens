# M1 explorer and one-command demo

## Purpose and contract

The local React/TypeScript explorer presents the bounded API's synthetic cohort, vehicle strata, drive timeline, and event source keys. From a prepared repository with Python dependencies, ClickHouse, and `explorer/node_modules`, `.venv/bin/python -m fleetlens.demo` regenerates the fixed fixture, validates and loads it, measures three guarded cohort reads, then serves the API and explorer on loopback. Ctrl+C stops the two servers. `--no-serve` prepares and measures without serving.

The browser receives only API JSON. It never queries ClickHouse or calculates the metric. `cohort_summary` groups drives by the explicit `vehicle_id` field, sums episodes and valid metres within each vehicle, then divides. The strata are descriptive for two invented vehicles; they do not establish a fleet population or uncertainty.

## Concrete source-to-screen trace

The fixture's `fixture-brake` drive has six source samples. Samples with source sequences 1, 2, and 3 support the hard-braking interval [00:00:01, 00:00:03) UTC. The metric produces one episode and 36 m of valid distance for that drive. The second drive contributes 30 m, with its [2, 5) gap excluded. The cohort API therefore returns 1 episode / 66 m = 1,515.1515 episodes per 100 km. The explorer displays 1, 66 m, and 1,515.2; selecting the event shows sequence chips #1, #2, #3. Its timeline draws eligible intervals and the event window; blank space represents excluded exposure.

The vehicle strata show `fixture-brake`: 1 / 36 m = 2,777.8 per 100 km; `fixture-gap`: 0 / 30 m = 0. A zero rate is shown only with positive exposure. A missing receipt, rejected source rows, no eligible intervals, or zero exposure leaves the corresponding rate undefined.

## Checks, failure handling, and design

The TypeScript/Vite production build passed. The page was inspected in Chrome against the live one-command demo: cohort provenance/accounting, two vehicle strata, drive selection, event lineage, and the gap drive's zero-event state rendered. The API tests cover request bounds, source conflicts, unsupported stored versions, and nonfinite results; nonfinite numbers are never emitted as JSON `Infinity`.

The demo reports generated file bytes, generation/load seconds, three individual cohort query seconds, host OS/architecture, source completeness, and physical versus logical rows. Physical rows accumulate with each replay; logical rows and the rate stay fixed. These local tiny-fixture times do not predict throughput. The demo assumes a prepared local ClickHouse service and installed frontend dependencies. It provides no external deployment, authentication, representative fleet inference, or real-data validation.

The alternative is to compute and chart metrics in the browser. Keeping the metric in the Python boundary gives one versioned definition and lets the API enforce source integrity before publishing a rate. At larger scale, the full snapshot read and single-process WSGI server would need measured redesign, likely persisted aggregates and pagination.

## Teach-back

Starting from source sequence 1, explain why the episode uses sequences 1–3 while the cohort denominator includes valid metres from both drives. Then explain why the two vehicle rates must not be averaged to get the cohort rate. Bryan's answer has not yet been assessed.

**Evidence-bounded interview wording:** “I built a local synthetic source-to-explorer demo with guarded ClickHouse reads, a versioned event/exposure metric, bounded API routes, and a traceable React timeline; the fixed 11-sample fixture and replay invariants were tested.”

## Production analogue

The [bounded API and client-view bridge](../learning/production-bridge.md#b19-bounded-read-api-and-client-views) corresponds to a read model serving a fixed client contract. FleetLens stops at a loopback, single-process server and a tiny snapshot.
