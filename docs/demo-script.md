# M1 demo capture script (about 90 seconds)

The [recorded 45-second M1 explorer demo](../reports/m1-demo-2026-10-01.mp4)
is silent and captioned. It was made on 2026-10-01 from the local served app on
an Apple M2 MacBook Air using
[`scripts/render_m1_demo.swift`](../scripts/render_m1_demo.swift). After starting
the demo server, run `swift scripts/render_m1_demo.swift` on macOS to capture
an offscreen WebKit view. The recording shows five inspected scenes: cohort,
vehicle strata, braking timeline, source sequences, and gap drive. The CLI
measurements are recorded separately in the [local run report](../reports/m1-local-run-2026-10-01.md).

For a narrated terminal-and-browser walkthrough, follow this longer outline:

Prepared environment: Python dependencies installed, `cd explorer && npm ci` completed, and local ClickHouse compose running. From the repository root run `.venv/bin/python -m fleetlens.demo` (PowerShell: `.\.venv\Scripts\python.exe -m fleetlens.demo`). Record the terminal and `http://127.0.0.1:5173/` browser tab. No real location or video appears in this fixture.

1. **Source and load (0–20 s).** Show the command output: 11 generated synthetic samples, dataset bytes, load time, three cohort query times, and 11 logical rows. Point out that physical rows rise on replay while logical rows stay 11. Say these are local tiny-fixture observations.
2. **Cohort and strata (20–40 s).** Show `fixture-v1`, synthetic origin, `source_complete`, 1 hard-braking episode, 66 m valid distance, and 1,515.2 episodes per 100 km. Show vehicle strata: 1/36 m for `fixture-brake`, 0/30 m for `fixture-gap`. Explain that cohort rate is a ratio of sums.
3. **Drive and source lineage (40–65 s).** Select `fixture-brake`; show eligible interval bars, [1, 3) event, and source sequence chips #1, #2, #3. Explain that acceleration at a source sample applies until the next eligible sample.
4. **Gap and limits (65–90 s).** Select `fixture-gap`; show the blank [2, 5) exposure gap and no event. Say the gap contributes no valid distance, generated telemetry is not a real fleet safety estimate, and M2 will address operational recovery and real-source validation.

Stop the demo with Ctrl+C. The runner should close its API and Vite listeners. Record the capture date, machine, exact command, and link or filename in [status](status.md).
