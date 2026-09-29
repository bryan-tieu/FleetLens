# FleetLens history

## 2026-09-28 — migrate context with fresh code and independent history

- Preserved the destination's README-only initial commit f733f84; imported no FleetLoop Git ancestry.
- Transferred the revised AI-assisted engineering/learning guidance and job-aligned roadmap.
- Reset implementation status and the first session plan to reflect a documentation-only repository.
- Archived source documentation with provenance and hashes, including the pre-existing learning-note edits, while leaving FleetLoop untouched.
- Did not copy source modules, datasets, junctions, caches, virtual environments, dependency pins, or Claude-specific workflows.
- No engineering performance result or learning assessment is claimed.
- See migration.md for transfer and verification details.
- Migration verification passed: 49 Markdown files with resolving local links, 26 matching archive hashes, unchanged posting/source files, and no transferred implementation or source Git ancestry.

## 2026-09-29 — implement the first executable foundation

- Added installable Python 3.11 package, canonical sample/provenance contracts, and 59 passing validation cases.
- Pinned development/build dependencies; added Windows/Linux CI configuration, README setup commands, and a sample walkthrough.
- Verified fresh editable install, lint/format, dependency consistency, wheel build, and isolated wheel import on Windows 3.11.9.
- Hosted CI and Linux remain unverified; no data services started or external publication performed.
- Learning walkthrough delivered; teach-back pending. M0 generator/CLI/independent fixture expectations are next.

## 2026-09-29 — record hosted CI and add Claude Code orientation

- Confirmed via the public GitHub API that Actions run 36535425818 on b95a2af passed on windows-latest and ubuntu-latest; updated README, status, decisions, JD row 9, walkthrough, and session notes that still said hosted CI was unverified.
- Added CLAUDE.md, which imports AGENTS.md and adds a code map, contract invariants, and commands for fresh Claude Code sessions. It is not a new workflow and does not own status or roadmap.
- Corrected stale environment, walkthrough-index, and session-index text. No code or behavior changed; local checks rerun: 59 passed, Ruff and Black clean.
