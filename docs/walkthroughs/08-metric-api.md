# M1 bounded metric API

## Purpose and contract

The [WSGI app](../../src/fleetlens/api/app.py) gives the local explorer three read-only JSON routes. `GET /api/v1/cohort` returns a snapshot summary and compact drive list; `GET /api/v1/drive` returns one drive's events and valid intervals; `GET /api/v1/event` returns one episode with source sample keys. All three require dataset and snapshot IDs. Drive and event routes also require vehicle and drive IDs; event detail uses the first source sequence in the episode as its stable selector. `max_samples` defaults to 1,000 and is capped at 10,000. Cohort `max_drives` defaults to 100 and is capped at 1,000. The [local server command](../../src/fleetlens/api/cli.py) binds to `127.0.0.1` only.

The API calls the guarded [stored summaries](../../src/fleetlens/metrics/stored_v1.py). It cannot issue arbitrary SQL or request an unbounded source feed. Cohort JSON includes source-file hash, input/accepted/rejected counts, `source_complete`, episode numerator, valid-distance denominator, definition version, status, and nullable rate. `data_origin` is explicitly `synthetic` for the currently supported source contract. Each request uses a fresh guarded snapshot read; there is no cross-request transaction or cache.

## Trace one fixture event

After loading `fixture-v1`, the cohort route returns 11 logical samples, two drives, one episode, 66 m valid distance, and `100000 / 66` episodes per 100 km. The brake drive route exposes the [1, 3) episode and five valid exposure intervals. The event route with `start_sequence=1` returns its definition version, UTC start/end times, and source keys for sequences 1, 2, and 3. A viewer can follow that key to the stored canonical sample and its source reference. The API serializes UTC datetimes with `Z`.

## Failure handling and choice

A changed-payload or mixed-file-hash snapshot returns HTTP 409 with a fixed `snapshot_conflict` code. Missing drive/event returns 404; invalid selectors return 400 `invalid_or_oversized_request`; a valid snapshot exceeding caller-selected read bounds returns 400 `snapshot_exceeds_limit`; unsupported stored contracts or nonfinite metric results return 422 `snapshot_invalid`; unavailable storage returns 503. A loaded but incomplete source is a successful read with `incomplete_source`, its row accounting, and a null rate. Error responses do not echo source rows or exception text. Cohort drive entries are compact so sample interval arrays appear only when a drive is requested. Vehicle-ID strata are calculated from the same guarded read.

Standard-library WSGI keeps this local API dependency-free and lets tests call the request contract without opening a port. FastAPI would provide richer typed routing and generated OpenAPI as the API grows. The current server is synchronous, has no authentication, pagination, or measured concurrency capacity, and is bound to loopback for the local demo. A later deployment would need an explicit security and serving design.

## Verification and learning check

[API tests](../../tests/test_api.py) exercise cohort/drive/event JSON, source keys, incomplete and conflict states, request bounds, and missing events without a database. The stored-query integration tests cover the data boundary underneath. Exact current check results are in [status](../status.md).

Optional teach-back: Why does the API return HTTP 200 with a null rate for an incomplete source, but HTTP 409 for a conflicting source-file hash? Which source keys support the fixture's [1, 3) episode?

## Production analogue

These routes form a bounded **semantic API** over guarded analytical reads: clients ask for a defined cohort, drive, or event instead of writing SQL. The [production bridge](../learning/production-bridge.md) describes the underlying snapshot and metric guarantees. FleetLens currently serves one local synchronous process and does not claim production API capacity.
