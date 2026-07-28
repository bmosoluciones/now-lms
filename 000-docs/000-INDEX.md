# 000-docs Index — Intent Solutions fork of NOW-LMS

Filed per the Document Filing System v4.4 (`/doc-filing`): flat `000-docs/`,
`NNN-CC-ABCD-description.ext`, one global chronological sequence. Next number =
recursive scan of this tree, highest `NNN` + 1. Per §3.1 this tree stays
**flat** — nesting into `NNN-CC-cluster-name/` folders applies only past ~50
files with an 8+ doc cluster, and we are far under both thresholds.

> **`NNN` is append-only from 2026-07-28 onward.** The 2026-07-28 backfill
> renumbered the tree **once**, chronologically, because every file then in it
> had been filed the same night — the numbers carried no historical meaning to
> preserve, and the backfilled PRD + ADRs record decisions made *before* the
> docs that already sat at low numbers. That was a one-time correction, not a
> precedent: new documents take the next free number, never a backdated slot.

## Documents

| File | What it is |
|---|---|
| [001-PP-PROD-now-lms-fork-prd.md](001-PP-PROD-now-lms-fork-prd.md) | Baseline PRD (backfilled 2026-07-28): what Intent Solutions Learn is — vision, users, shipped scope, non-functional requirements, standing risks, release strategy. The document future work diffs against. |
| [003-DR-REFF-live-auth-flow.md](003-DR-REFF-live-auth-flow.md) | Verified login / roles / admin flow of the live deployment (verified 2026-07-21 against the running container). The getting-started lessons were written from it. |
| [004-BL-POLI-cca-source-reuse.md](004-BL-POLI-cca-source-reuse.md) | CCA-F prep source map & reuse policy: license-tiered reuse rules (NC/unlicensed = link only), question banks are Intent Solutions IP, Rick Hightower reuse grant context. |
| [005-BL-LICN-cca-attributions.md](005-BL-LICN-cca-attributions.md) | Attribution record for the CCA-F curriculum: MIT-licensed projects that informed structure, credited per license; lesson prose originally authored by Intent Solutions. |
| [007-OD-CHNG-upstream-v2-sync-map.md](007-OD-CHNG-upstream-v2-sync-map.md) | Upstream v2.0.0 sync migration map (2026-07-26): commit triage (MUST-SURVIVE set), corrections, DB migration analysis, sequencing, open items. Read before any upstream sync. |
| [011-PP-PLAN-waiting-list-gated-surfaces.md](011-PP-PLAN-waiting-list-gated-surfaces.md) | Waiting-list + gated practice surfaces execution plan (locked 2026-07-27): /request-access intake, practice-tracks teaser, contact fix, course gating, security ship-gate, upstream PR queue U1–U10, founder-locked copy and decisions. |

## Renames & moves (references in old commit messages resolve here)

| Old location | Current name | When / why |
|---|---|---|
| `001-OD-PLAN-upstream-v2-sync-migration-map.md` | `001-OD-CHNG-upstream-v2-sync-map.md` | 2026-07-27 — doc-filing v4.4 compliance (`PLAN` is a PP type; a migration map is OD change management; 4-word description cap). |
| `002-OD-PLAN-waiting-list-and-gated-practice-surfaces.md` | `002-PP-PLAN-waiting-list-gated-surfaces.md` | 2026-07-27 — same pass (an execution plan is PP-PLAN; 4-word cap). |
| `content/cca/AUTH-FLOW.md` | `003-DR-REFF-live-auth-flow.md` | 2026-07-27 — fork-local document filed; nothing in code consumed it. |
| `content/cca/SOURCES.md` | `004-BL-POLI-cca-source-reuse.md` | 2026-07-27 — same pass. |
| `content/cca/ATTRIBUTIONS.md` | `005-BL-LICN-cca-attributions.md` | 2026-07-27 — same pass; internal cross-reference updated. |
| `001-OD-CHNG-upstream-v2-sync-map.md` | `007-OD-CHNG-upstream-v2-sync-map.md` | 2026-07-28 — one-time chronological backfill (see the append-only note above): the sync map is a 07-26 document and slots after the 07-21 block and the backfilled ADRs it postdates. `FORK.md` citations updated in the same commit. |
| `002-PP-PLAN-waiting-list-gated-surfaces.md` | `011-PP-PLAN-waiting-list-gated-surfaces.md` | 2026-07-28 — same backfill: the newest document (07-27) takes the highest slot. `FORK.md` citations updated in the same commit. |

## md files that deliberately stay OUTSIDE this tree (the fork boundary)

Filing organizes *project documents*. These classes are excluded on purpose —
do not "fix" them into 000-docs:

- **Root governance files** — `README.md`, `CLAUDE.md`, `AGENTS.md`, `FORK.md`,
  `CHANGELOG.md`. The standard's own scan excludes this class; they work by
  being discoverable at their conventional names/paths.
- **Upstream-owned material** — everything under `docs/` (upstream's mkdocs
  site source), `replit.md`, `.github/copilot-instructions.md`,
  `tests/README.md`, and the 8 upstream theme `README.md` files. Moving any of
  it is permanent sync-conflict surface against `bmosoluciones/now-lms`.
- **Curriculum** — teaching content (question banks + lesson prose) is **not in
  this repository**. It lives in the private `intent-solutions-io/intent-curriculum`
  repo and is read at seed time via `CCA_CONTENT_DIR`
  (see `scripts/seed_cca_courses.py`). It is program input, not documentation, and
  it never returns here. `now_lms/templates/themes/intent_learn/README.md`
  documents the theme package in place.
- **Tool artifacts** — `.beads/README.md`, `.pytest_cache/README.md`
  (generated; the latter is gitignored).

## Quick reference

Category codes (CC) and document types (ABCD) come from the canonical standard —
`~/.claude/skills/doc-filing/references/000-DR-STND-document-filing-system.md`.
Used here: `PP-PROD` (PRD), `PP-PLAN` (plans), `AT-ADEC` (architecture
decision records), `OD-CHNG` (ops change management), `DR-REFF` (reference
docs), `BL-POLI` (policy), `BL-LICN` (licensing/attribution).
