> Archived FleetLoop reference. Commands, implementation claims, and agent rules here are historical, not active FleetLens instructions. See [migration context](../../../migration.md). Links have been relocated; source code remains in the original repository.

# History — day-by-day journal of what landed

## 2026-08-25 — Week 0: repo scaffold
- Scaffolded the repo: package skeletons (`fleetgen/`, `ingest/`, `metrics/`, `fleetkit/`),
  docs tree, `migrations/{clickhouse,postgres}/`, `tests/`, `explorer/` placeholder,
  dev tooling config (ruff/black/pytest via `pyproject.toml`, `requirements-dev.txt`),
  `.gitignore`, `data/` (gitignored) and the real README.
- Structure only — no code, no measurements. Every ⬜ in CLAUDE.md remains open.
- Wrote the three pre-Phase-1 docs: `jd-map.md` (9-row JD map + named-gap tracker, seeded
  from CLAUDE.md; verbatim posting still TODO), `FleetLoop_Blueprint.md` (full 12-week
  design of record), `privacy.md` (threat model, controls, enforcement, proposed canonical
  constants — **not yet ratified**). Privacy terms + constants mirrored into `glossary.md`.
- Captured the verbatim JD (req 279540, Palo Alto) into `jd-map.md`'s appendix; extended
  the map to 11 rows (added: end-to-end pipelines, infra health/observability) + a
  "What You'll Bring → evidence" table. All four JD-named technologies (Postgres,
  ClickHouse, PySpark, Dagster) land in Phase 3.
- Privacy constants ratified as proposed — first real entry in `decisions.md`.
- Built all 10 project skills (`.claude/skills/`), adapted from DevPulse's; `/warmup`
  deliberately dropped (coach mode from Day 1). New gates: `/measure` (hard rule 1),
  `/jd-check` (aim), `/metric-review` (Phase-4 ship gate). Wrote `docs/operating-manual.md`.
- Wrote `docs/data-acquisition.md` sized to measured disk: 76 GB free → comma2k19 capped at
  2 chunks (~20 GB), BDD100K images-only (~7 GB), nuScenes mini — decision logged. Logged the
  DevPulse Phase-4 cut in DevPulse's decisions.md. **Week 0 FleetLoop-side: done.** Remaining:
  Bryan's downloads/registrations + DevPulse close-out (Day 17 CI, README, diagram, video).
- D: drive surfaced (502 GB free): datasets moved to `D:\FleetLoop-data\` via `data/`
  junctions (created); comma2k19 uncapped (2-chunk decision superseded same day, honestly
  logged). ClickHouse-volume-location becomes a Phase 3 decision.
- Downloaded + verified the Phase-4 benchmark data to D: (69 MB): NHTSA SGO incident CSVs
  (ADAS 2,513 / ADS 5,319 / OTHER 36 rows), FARS 2023+2024 National CSV zips (validated),
  FHWA VMT (June-2026 TVT, historic 1970–present, 2002–20 archive). Counts + gotchas
  (SGO files are living documents; highways.dot.gov 403s curl) recorded in the runbook.
- BDD100K portal triaged: HTTPS/TLS broken but the site is alive over plain http:// (DNS +
  HTTP 200 verified); old ETH mirror is NXDOMAIN — runbook updated with the http:// path and
  the GitHub-discussions fallback. nuScenes pick clarified in runbook: Mini 3.88 GB archive.
- nuScenes v1.0-mini landed on D:, extracted + verified (10 scenes, 13 metadata tables,
  4,848 samples / 26,358 sweeps; archive byte-exact vs advertised size). Runbook ticked.
- Environment ready: `.venv` created, dev tooling installed (ruff 0.16.4, black 26.5.1,
  pytest 9.1.1, sqlfluff 4.3.0), lint smoke-test green. Week 0 work committed and pushed.

## 2026-08-26 — Week 0, day 2
- BDD100K 100k images landed + verified (5.67 GB zip: 70k/10k/20k exact, full CRC pass —
  the plain-HTTP integrity risk is closed for this file). det_20 labels zip still to grab.
- **comma2k19 complete: all 10 chunks (88.12 GiB), not just the planned 2.** Landed on C:
  first (dropped it to 4.8 GB free), moved to D: via qBittorrent; re-verified after the move —
  byte-exact sizes + 250/250 sampled SHA-1 piece hashes vs the official infohash. C: back to
  93 GB free. Path is nested (`data/comma2k19/comma2k19/`) because of the client move; left
  as-is so seeding survives, documented in the runbook. **Phase 1's data gate is met 5 days
  early, and the 2-chunk subset decision is now moot.**

## 2026-09-28 — migrate project guidance to AI-assisted implementation

- Added AGENTS.md as the project-wide agent entry point and reduced CLAUDE.md to a compatibility pointer. No Claude-specific slash command is required.
- Replaced public scope with an honest early-implementation README; added the active roadmap, staged architecture, current-state handoff, and experiment contract.
- Reworked the JD evidence table while preserving the captured posting appendix; all engineering evidence remains unproven.
- Added learning competencies, walkthrough guidance, an existing-code walkthrough, and a bounded next-session plan. No Bryan answers or mastery claims were invented.
- Preserved original Day 01 and glossary edits with context notices; marked historical plans/environment/acquisition records and legacy Claude workflows as non-operative where superseded.
- Updated metric/privacy guidance to separate design intent from implementation and kept runtime code untouched. Existing fleet.py syntax/sampling issues and the absent test suite remain M0 work.
- Verification: checked local link targets across 27 Markdown files (none missing), confirmed the captured posting appendix is unchanged against Git HEAD, and ran git diff --check (no whitespace errors). Runtime tests were not rerun for this documentation-only revision.
