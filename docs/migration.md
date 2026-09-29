# Migration from FleetLoop

Date: 2026-09-28. Destination: C:\Users\Bryan\Downloads\FleetLens.

## Decisions and provenance

Bryan requested fresh Git history and explicitly chose **documentation with fresh code**.
FleetLens already had its own README-only initial commit, f733f8429fa6e8f3af0d885f042b2de861c8a688.
That commit is preserved; migration is a new local commit, not an imported history or an amended root.

Source: C:\Users\Bryan\Downloads\FleetLoop\FleetLoop.
Documentation baseline: 9ed0e58aa53a7268bd4307955dc6815bfe1cbf40.
The source working-tree documentation was captured, including previously uncommitted additions to the Day 01 note and glossary. See [the snapshot manifest](archive/fleetloop/manifest.json) for source/archive hashes. Archived links were relocated and a historical notice added, so source and archive hashes differ intentionally.

## What transferred

- Active AI-assisted collaboration guidance, roadmap, architecture, job mapping, experiment rules, privacy/domain notes, learning and interview workflow.
- A reference snapshot of all tracked Markdown outside .claude/, including the original captured job posting, status, decisions, history, and acquisition/environment records.
- New FleetLens status, README, first-session plan, migration record, and safe ignore/line-ending rules.

Names, package paths, and current-state claims were updated in active documents. Historical material is clearly marked and retained under docs/archive/fleetloop/. AGENTS.reference.md and CLAUDE.reference.md are inert archive names, not active instruction files. Archive claims and dates must not be treated as current implementation.

## Source implementation

No .py files, unfinished modules, dependency pins, packaging configuration, .venv, caches, datasets, directory junctions, or old .git were copied. Claude-specific skills were not installed; the source repo retains them.

The unfinished fleetgen/fleet.py, fleetgen/signals.py edits, requirements.txt edits, and original learning-note changes remain in FleetLoop. Relevant source paths and hashes are in the manifest; code contents are not copied. References to source modules in the archived glossary point here because those modules are intentionally absent.

The old repository and its working tree remain untouched. Do not delete or clean them up automatically. Existing datasets stay in their original location and require verification before any adapter uses them.

## Active starting point

Read [../AGENTS.md](../AGENTS.md), [status.md](status.md), and the [first session plan](daily/2026-09-29.md#session-plan).
There is no runnable FleetLens application yet. The first task is an installable Python foundation and explicit telemetry contracts.

All learning states remain not assessed. Use future walkthroughs, debugging, and bounded changes to establish understanding. Do not infer understanding or professional experience from this transfer.

## Verification

- Checked local link targets across 49 Markdown files: none missing.
- Confirmed the captured job-posting appendix is unchanged.
- Confirmed all 26 archive hashes match the manifest.
- Confirmed source file hashes and source working-tree status remain unchanged.
- Confirmed no Python modules, environments, dependency pins, or Claude skill files were copied.
- Confirmed the independent destination root remains f733f84.
- Checked Git diff whitespace; no runtime test or benchmark is claimed for a documentation-only repository.

The migration is committed locally; no push is performed by this migration.
