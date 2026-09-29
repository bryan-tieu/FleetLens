> Archived FleetLoop reference. Commands, implementation claims, and agent rules here are historical, not active FleetLens instructions. See [migration context](../../../migration.md). Links have been relocated; source code remains in the original repository.

> **Historical acquisition record — context updated 2026-09-28.** M0 and the synthetic M1 demo require no downloads. Reverify existing files before acquiring anything. Past capacity, endpoint availability, and checksums are dated evidence; an archive checksum is not itself a license check or proof of publisher authenticity. See [status.md](status.md), [roadmap.md](roadmap.md), and [../data/README.md](../data/README.md).

# Data acquisition runbook — the Phase-1 long pole

*Written 2026-08-25. Start these before the first build day, not during it (CLAUDE.md → Current status). Everything lands under `data/` per `data/README.md` — all of it gitignored.*

## Disk plan (updated 2026-08-25 — D: available)

**Datasets live on `D:\FleetLoop-data\` (502 GB free), junctioned into repo `data/` — the junctions exist, destinations below are ready.** C: (76 GB free) stays clear for the repo + Docker. Sizing:

| Dataset | Take | ~Size | Running total |
|---|---|---|---|
| comma2k19 | chunks 1–2 **first** (Phase 1), rest in background — full set fits now | ~100 GB | 100 GB |
| BDD100K | 100k *images* + det labels (**not** the 1.8 TB videos) | ~7 GB | 107 GB |
| nuScenes | mini split only | ~4 GB | 111 GB |
| NHTSA SGO / FARS / FHWA VMT | full — they're small CSVs | <1 GB | ~112 GB |

~390 GB headroom remains on D: after downloads. The one open disk question: Docker Desktop's WSL2 disk (ClickHouse volume) lives on C: — moving it to D: vs bind-mounting is a Phase 3 decision (see `docs/decisions.md`, 2026-08-25 D: entry).

## The checklist (≈ 15 minutes of clicking, then background downloads)

### 1. comma2k19 — chunks 1–2 first, full ~100 GB in background · needed by Phase 1 (calibration)
- Official torrent (linked from the README at https://github.com/commaai/comma2k19): https://academictorrents.com/details/65a2fbc964078aff62076ff4e103f18b951c5ddb — infohash `65a2fbc964078aff62076ff4e103f18b951c5ddb` is the trust anchor (reached us over HTTPS from comma's GitHub; BitTorrent verifies every piece against it). Client: qBittorrent from https://www.qbittorrent.org exactly. ~100 GB, 10 chunks, 2019 one-minute segments.
- ✅ **DONE 2026-08-26 — the FULL dataset, all 10 chunks** (the prioritize-1-and-2 plan proved unnecessary; the whole 88 GiB came down in one session). Phase 1 gets full calibration substrate and Phase 5 the entire real-driving corpus.
- ⚠️ **Actual path is nested:** `data/comma2k19/comma2k19/Chunk_N.zip` (qBittorrent's move created the extra level). **Do not flatten it in Explorer** — the client seeds from that path and would lose track. Phase 1 code points at the nested path, or the torrent is removed from qBittorrent first (keeping files) and then flattened.
- ✅ **Verified 2026-08-26:** all 10 chunks byte-exact vs the torrent manifest (94,622,767,664 bytes = 88.12 GiB total) and **250/250 randomly sampled 2 MiB pieces SHA-1-valid after the C:→D: move** — authenticated against infohash `65a2fbc9…` from comma's official GitHub. Chunks still zipped; extraction is a Phase 1 decision (they may be readable in place).
- ⬜ Segment counts per chunk: record in Phase 1's day log when the calibration set is pinned.

### 2. BDD100K — ~7 GB · needed by Phase 5, registration is the slow part so do it now
- ⚠️ **The portal's HTTPS is broken (checked 2026-08-25): `https://` connections fail, but the site is up over plain `http://bdd-data.berkeley.edu`.** Type the `http://` URL explicitly; if the browser force-upgrades to https, allow the insecure fallback for this site (public dataset — fine, but verify file sizes after download). The old ETH mirror (`dl.cv.ethz.ch`) no longer exists — don't chase it.
- **No registration gate as of 2026-08-25** — the portal serves downloads directly (so no credentials ever cross the insecure connection). The license still applies regardless: research/portfolio use, no redistribution. Download **"100K Images"** and the **detection labels (det_20)**. **Do not download the videos** (1.8 TB).
- If the portal stays broken for days: access issues get handled at https://github.com/bdd100k/bdd100k/discussions — ask there rather than using unofficial re-uploads (license).
- Destination: `data/bdd100k/`.
- ✅ **Images DONE 2026-08-26:** `bdd100k_images_100k.zip` (5.67 GB) verified — exactly 70k/10k/20k by split, full CRC pass over every file + 60-image random sample structurally valid JPEG at the documented 1280×720 (plain-HTTP integrity concern closed as far as physically possible without a trusted reference hash). Kept zipped; extraction happens in Phase 5 prep. **Still needed: the det_20 labels zip** ("Detection 2020 Labels", ~50 MB) — images alone can't train the detector.

### 3. nuScenes mini — ~4 GB · labeled-scene substrate
- Register: https://www.nuscenes.org/nuscenes#download → under **Full dataset (v1.0) → Mini**, take **"Metadata and sensor file blobs [US]" (3.88 GB)** — that single archive is v1.0-mini, annotations included. Ignore Trainval (10× ~28 GB blobs) and Test entirely.
- Destination: `data/nuscenes/`.
- ✅ **DONE 2026-08-25:** extracted + verified — 10 scenes, 13 metadata tables, 4,848 samples + 26,358 sweeps (~5.1 GB on D:). Original `v1.0-mini.tgz` kept beside it (re-extract insurance; delete if D: ever needs the 3.9 GB).
- Full nuScenes only if a Phase-5 measurement demands it (Blueprint rule).

### 4. NHTSA + FHWA — ✅ DONE 2026-08-25 (downloaded + verified, 69 MB on D:)
- **SGO incident reports** (`data/nhtsa/sgo/`, from static.nhtsa.gov/odi/ffdd/sgo-2021-01/): ADAS **2,513 rows** · ADS **5,319 rows** · OTHER **36 rows** (data rows excl. header; live files — NHTSA updates them monthly, re-pull + re-record before Phase 4 freezes its snapshot).
- **FARS** (`data/nhtsa/fars/`): `FARS2023NationalCSV.zip` (34.2 MB) + `FARS2024NationalCSV.zip` (32.7 MB) — both zip-validated, 34 files each incl. `accident.csv`. 2024 is the newer annual release; treat 2023 as the stabler vintage until checked.
- **FHWA VMT** (`data/nhtsa/vmt/`): `26juntvt.xlsx` (June 2026 Travel Volume Trends, latest monthly) · `historicvmt.xlsx` (1970–present annual VMT) · `tvtarchive02-20.xlsx` (monthly archive 2002–2020). Note: files served from `www.fhwa.dot.gov` (the `highways.dot.gov` mirror 403s non-browser clients).

## Rules

- **Download hygiene:** comma2k19's magnet link comes **only from the official GitHub README** (BitTorrent then hash-verifies every chunk); torrent client from its official site only. For the BDD100K http:// workaround: verify the portal's MD5s if listed (`Get-FileHash -Algorithm MD5`), else compare sizes — plain HTTP has no integrity guarantee. Never "Enable Content" on downloaded spreadsheets; never blind-run code bundled inside a data archive. (BDD portal turned out to need no login — no credential exposure.) Remove the browser's insecure-content exception once downloads finish.

- **Licenses:** all four are research datasets — use here is personal research/portfolio, which fits, but read the terms at registration (nuScenes is explicitly non-commercial). Nothing from `data/` is ever committed or served raw (privacy.md applies to comma2k19's real GPS).
- **Record what you got:** when a download lands, note date, size, and counts in this file — downloads are provenance, and Phase 1 pins its calibration subset from what's recorded here.
- **comma2k19 is real driver data** — the [privacy.md](privacy.md) controls apply to it exactly as to fleetgen output (it's reason #1 the privacy doc exists).

## Status

| Dataset | Registered | Downloaded | Verified |
|---|---|---|---|
| comma2k19 (**all 10 chunks**) | n/a (torrent) | ✅ 2026-08-26 | ✅ sizes + 250 piece hashes |
| BDD100K 100k images | n/a (no gate) | ✅ 2026-08-26 | ✅ census + full CRC |
| BDD100K det_20 labels | n/a (no gate) | ⬜ | ⬜ |
| nuScenes v1.0-mini | ✅ 2026-08-25 | ✅ 2026-08-25 | ✅ 10 scenes, counts recorded |
| NHTSA SGO | n/a | ✅ 2026-08-25 | ✅ row counts recorded |
| NHTSA FARS | n/a | ✅ 2026-08-25 (2023+2024) | ✅ zips validated |
| FHWA VMT | n/a | ✅ 2026-08-25 (3 files) | ✅ xlsx validated |
