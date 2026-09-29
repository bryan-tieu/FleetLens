> Archived FleetLoop reference. Commands, implementation claims, and agent rules here are historical, not active FleetLens instructions. See [migration context](../../../migration.md). Links have been relocated; source code remains in the original repository.

> **Context update 2026-09-28:** this is a historical environment/setup record, not current verification. Follow [../AGENTS.md](../AGENTS.reference.md) and [roadmap.md](roadmap.md); no Claude-specific setup or full-stack launch is required. Windows Python 3.11.9 was observed in the review; reconcile the recorded Mac version during M0. Recheck disk, GPU, dataset availability, commands, and dependency compatibility before relying on old readings. Use controlled, recorded environments for comparisons; Windows remains the canonical benchmark host.

# Environments — Windows primary, macOS secondary

*Written 2026-08-26. **Windows is unchanged** and stays the reference machine — CLAUDE.md hard rule 14 remains its operating guide. This document is the macOS one. Split model decided 2026-08-26; see [decisions.md](decisions.md).*

## The split

| | **Windows 10 · Docker Desktop · local NVIDIA GPU** | **macOS · Apple Silicon · Docker Desktop** |
|---|---|---|
| Role | **Primary — authoritative** | **Secondary — development** |
| Runs | Everything | Phases 1–4 code · unit tests · `fleetgen` at reduced scale · Phase 6 frontend |
| Holds | All datasets (`D:\FleetLoop-data`, ~112 GB) · the full 1–2B-row ClickHouse store | Repo + a small regenerated slice only |
| Never runs | — | comma2k19 / any real driving data · Phase 5 training · **any canonical measurement** |

### The rule that matters most

> **No number that lands in `Reference values`, [jd-map.md](jd-map.md), or the Fleet Safety Report may be measured on the Mac.**

Hard rule 1 makes every phase end in a measured number, and most of those numbers are hardware-sensitive: Phase 3's ClickHouse-vs-Postgres-vs-BigQuery benchmark, Phase 2's admission-control throughput, the "too many parts" war story, any latency figure. A number produced on Apple Silicon and compared against one produced on the Windows box is not a comparison — it is an artifact of two different CPUs, memory ceilings, and disk paths. That failure is *especially* embarrassing here, because measurement discipline is the thing Phase 4 exists to demonstrate.

**The Mac proves correctness. The Windows box proves numbers.**

Narrow exception: results that are ratios of the same deterministic computation — miner precision/recall against the planted manifest, a codec compression ratio on identical input — are machine-independent in principle. Even for those, record the run from the primary machine so provenance stays single-sourced and no reader has to ask which box a figure came from.

## Setup

### 1. Toolchain

*Verified on this machine 2026-09-01 — macOS 15.6.1, arm64.*

- **Docker Desktop** — ✅ 29.7.2 via the `docker-desktop` Homebrew cask; engine `aarch64`/linux, **native arm64, no emulation** (verified with `docker run --rm alpine uname -m` → `aarch64`).
- **Python** — ✅ 3.10.6 (python.org framework build at `/Library/Frameworks`, not the system Python). ⬜ *Must be reconciled against the Windows version — see Open items.*
- **Node** — ✅ v20.16.0 / npm 10.8.1. Needed only from Phase 6.
- **git** — ✅ 2.39.5 (Apple Git-154). Homebrew ✅ 6.0.1 also present.
- **Docker Compose** — ✅ v5.5.0 (bundled plugin; invoke as `docker compose`, never `docker-compose`).

### 2. Repo

```bash
git clone https://github.com/bryan-tieu/FleetLoop.git
cd FleetLoop
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt   # requirements.txt fills in per phase
```

Open Claude Code **at the repo root** — the folder containing `CLAUDE.md` and `.claude/`. Same trap as the Windows inner/outer folder note in Reference values: a session started one level up loads no skills.

### 3. Docker Desktop resources

Docker on macOS runs a Linux VM with a **fixed CPU / memory / disk allocation**, and the defaults are not sized for ClickHouse. Set these in *Settings → Resources* before the first `docker compose up`:

*Measured 2026-09-01: host is 16 GB RAM / 8 CPU; Docker is allocated **7.7 GiB and 8 CPUs** (Desktop's ~50% default).*

- **Memory — 7.7 GiB, and that is effectively the ceiling.** On a 16 GB host you cannot give Docker much more without starving macOS. It is adequate for this machine's role (reduced-scale `fleetgen` slice, unit tests) and **independently confirms the split**: a 1–2B-row ClickHouse store and its benchmark cannot fit here regardless of the comparability rule. Capacity and comparability point the same way.
- **Disk — `Docker.raw` is a sparse file** (460 GB apparent, 27 MB actual). The real constraint is **host free space: 120 GB**, not the VM cap. This is the counterpart of the Windows WSL2-disk-on-C: issue and fails the same silent way partway through a large ingest — watch host free space, not the Docker setting.
- **VirtioFS** — leave it on if offered; substantially faster than the older file-sharing backends for any bind mount.

### 4. Data

Datasets stay on Windows. This machine gets **synthetic data only**, regenerated from seed — `fleetgen` is deterministic, so the fleet is reproducible from a commit rather than synced from a disk.

```bash
python -m fleetgen.run --vehicles <reduced> --hours <reduced> --seed 42
```

⬜ *The reduced-scale slice is TBD until Phase 1 pins the canonical test slice. Sizing constraint to carry into that decision: the slice must regenerate on this machine in minutes, not hours, or the Mac stops being useful for the verification work it exists to do.*

Path indirection (`FLEETLOOP_DATA_DIR`, defaulting to repo-relative `data/`) is ⬜ **not yet built** — it supersedes the junction-based decision at [decisions.md:37](decisions.md#L37), which explicitly deferred this until "the repo ever runs on a machine without a D:". That condition has now fired.

## macOS gotchas — the counterpart to hard rule 14

Recorded the same way the Windows list was, because these cost time exactly once each:

- **Case sensitivity is a lie on both hosts.** APFS and NTFS are both case-*insensitive*; the Linux containers and CI are case-*sensitive*. `Fleet_Signals.sql` referenced as `fleet_signals.sql` works on both your machines and fails in the container. Treat every path as case-sensitive even though nothing local will correct you.
- **Line endings.** Files authored on Windows arrive with CRLF; a CRLF shell script inside a Linux container fails with an unreadable error. ✅ Handled by `.gitattributes` (2026-09-01): repo normalizes to LF, `.sh`/`.sql`/`.yml`/`.proto`/Dockerfiles forced LF, `.ps1`/`.bat`/`.cmd` forced CRLF.
- **`sed -i` differs.** BSD `sed` requires an argument: `sed -i ''` on macOS, `sed -i` on Linux/GNU. Same for `date`, `stat`, and `readlink`. Any script that has to run in both places should be Python, not shell.
- **Bind mounts are slow, named volumes are not.** Container↔host file sharing carries real overhead on macOS. Prefer **named volumes** for ClickHouse/Postgres data — which also sidesteps hard rule 14's silent-empty-bind-mount trap on the Windows side. This is a compose-file convention to set once, when Phase 3 writes it.
- **`.DS_Store`** — already gitignored. Leave it that way.
- **Architecture.** ✅ **Verified 2026-09-01 by manifest inspection** (no image pulled) — every stack image publishes `linux/arm64`, so no emulation and no `platform:` pinning is needed:

  | Image | Architectures |
  |---|---|
  | `clickhouse/clickhouse-server:latest` | amd64, **arm64** |
  | `postgres:16` | 386, amd64, arm, **arm64**, ppc64le, riscv64, s390x |
  | `redpandadata/redpanda:latest` | amd64, **arm64** |
  | `minio/minio:latest` | amd64, **arm64**, ppc64le |

  Re-check with `docker manifest inspect <image>` if Phase 3 pins different tags — multi-arch coverage is per-image *and* per-tag. Rosetta in Docker Desktop is the fallback if one ever turns out to be amd64-only.
- **AirPlay Receiver binds ports 5000 and 7000.** Nothing in the current stack collides (8123/9000 ClickHouse · 5432 Postgres · 9092 Redpanda · 9000/9001 MinIO · 3000 Dagster), but Phase 6's FastAPI should avoid 5000.
- **ClickHouse native (9000) and MinIO API (9000) collide** — platform-independent, but it surfaces the first time the full stack comes up. Remap one in compose.

## Working across two machines

- **Push before you switch.** The two machines share exactly one synchronization mechanism — `main` on GitHub. There is no other channel; the data, the ClickHouse store, and the Docker volumes are per-machine and do not travel.
- **The Mac's stack is disposable.** If its containers get into a strange state, tear down and regenerate rather than debugging — the data is reproducible from seed and nothing authoritative lives here.
- **`/end-session` still applies on both.** Never leave containers running or terraform applied on either box.
- **A measurement taken here is a smoke test, not a result.** If a number is interesting, re-run it on Windows before it goes anywhere near a doc.

### Reconciling divergent branches — `pull.rebase true`, on **both** machines

Set once per machine:

```
git config --global pull.rebase true
```

**Why rebase, not merge.** One person on two machines diverges constantly and trivially — "committed on the Mac, then committed on Windows." Merging mints a merge commit for each, and over twelve weeks the history becomes a braid of `Merge branch 'main'` that tells a reader nothing. Rebase replays local commits on top of the remote and keeps history linear, which is also what makes `git log` usable as the project journal [history.md](history.md) refers back to.

The standard caution against rebasing does not apply here: it only bites when rewriting commits someone else has already pulled. Divergent branches means the local commits are *unpushed by definition*, so replaying them is safe.

**Set it identically on both boxes.** A reconciliation strategy that differs per machine is precisely the drift this whole document exists to prevent.

**Before reconciling, look:**

```
git log --oneline --graph --left-right origin/main...HEAD
git status
```

`<` is remote-only, `>` is local-only. Stash any uncommitted work first (`git stash` → reconcile → `git stash pop`).

### Line-ending renormalization after `.gitattributes`

The first pull that brings `.gitattributes` onto a machine can make git decide a pile of existing files need renormalizing — a wave of modifications nobody made. That is expected, not damage. **After** the rebase lands, not during:

```
git add --renormalize .
git status
```

If anything shows up, commit it on its own (`normalize line endings after gitattributes`). This should happen exactly once per machine; if it recurs, `.gitattributes` and the checked-in content disagree and that is worth investigating rather than re-committing.

## Privacy note (hard rule 9)

Keeping comma2k19 on one machine is not just a disk decision — it is the smaller-blast-radius one. It is **real people's real driving**, and confining it to the primary box means real GPS exists in exactly one place, under one set of controls. Do not copy it here "just to test something"; generate a synthetic fixture instead. See [privacy.md](privacy.md).

## Verification checklist — "the Mac is ready"

*Run 2026-09-01.*

| Check | Command | Result |
|---|---|---|
| Python env | `.venv/bin/python -V` · `pip list` | ✅ 3.10.6 · ruff 0.16.5, black 26.5.1, pytest 9.1.1, sqlfluff 4.3.0 |
| Lint clean | `ruff check . && black --check .` | ✅ both pass (5 files) |
| Tests run | `python -m pytest tests/` | ✅ runs; **no tests exist yet** — Day 1 adds the first |
| Line endings | `git check-attr eol -- x.sh x.ps1` | ✅ `lf` / `crlf` as intended |
| Skills load | Claude Code opened at repo root | ✅ this session |
| Docker up, arm64 native | `docker run --rm alpine uname -m` → `aarch64` | ✅ engine 29.7.2, native arm64 |
| Docker resources | Settings → Resources | ✅ 7.7 GiB / 8 CPU — the practical max on a 16 GB host |
| Stack comes up | `docker compose up -d clickhouse postgres redpanda minio` | ⬜ blocked — no compose file until Phase 3 |

## Open items

| Item | Why it matters | Status |
|---|---|---|
| `.gitattributes` | CRLF churn in diffs; broken scripts in containers | ✅ 2026-09-01 |
| CLAUDE.md hard rule 14 companion + macOS repo root in Reference values | Rule 14 read as if Windows were the only environment | ✅ 2026-09-01 |
| `decisions.md` entry for the split; amend the D:-junctions entry | The record contradicted the machine being worked on | ✅ 2026-09-01 |
| Install Docker Desktop (Apple Silicon) | The entire platform layer | ✅ 2026-09-01 — 29.7.2, native arm64 |
| Pin dev dependency versions | Unpinned `black`/`ruff` across two machines makes `black --check` fail on the other machine's formatting — each box reformats the other's work into the diff | ✅ 2026-09-01 |
| Verify arm64 for the Phase 3 stack images | Emulation would make any Mac-side timing meaningless and some images simply don't ship arm64 | ✅ 2026-09-01 — all four multi-arch |
| **Reconcile Python version with Windows** | Mac is on 3.10.6; a silent drift becomes a phantom bug that only reproduces on one machine. 3.10 also reaches EOL ~Oct 2026, inside this project's timeline | ⬜ **needs your call — see below** |
| `FLEETLOOP_DATA_DIR` + `fleetkit/paths.py` | Removes the last `D:`-shaped assumption from code | ⬜ deferred until a code path reads `data/` (calibration day) |
| Canonical test slice sized to regenerate on this machine | Phase 1 decision — see Data above | ⬜ |
| Cross-machine determinism of `fleetgen` (x86 vs ARM trig ULP) | The whole regenerate-from-seed strategy rests on it | ⬜ carried from [day-01](daily/day-01.md) to the next Windows session |

### The one open decision

**Python version.** This Mac is on 3.10.6; the Windows version is unrecorded. Both machines must match, and the target should probably be **3.12** — 3.10 reaches end-of-life around October 2026, which lands mid-Phase-5, and pinning a training environment to an unsupported interpreter is a bad trade for zero benefit. Deliberately *not* set unilaterally: `requires-python` in `pyproject.toml` stays unwritten until the Windows version is known, because a wrong pin is worse than an absent one.
