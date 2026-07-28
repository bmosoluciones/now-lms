# 000-docs Index — Intent Solutions fork of NOW-LMS

Filed per the Document Filing System v4.4 (`/doc-filing`): flat `000-docs/`,
`NNN-CC-ABCD-description.ext`, one global chronological sequence. Next number:
recursive scan of this tree, highest `NNN` + 1.

**Fork boundary:** only fork-local documents are filed here. Upstream-owned
material (`docs/`, `CHANGELOG.md`, `README.md`, requirement/lock files) is never
moved into this tree — that would be permanent sync-conflict surface.

## Documents

| File | What it is |
|---|---|
| [001-OD-CHNG-upstream-v2-sync-map.md](001-OD-CHNG-upstream-v2-sync-map.md) | Upstream v2.0.0 sync migration map: commit triage (MUST-SURVIVE set), corrections, DB migration analysis, sequencing, open items. Read before any upstream sync. |
| [002-PP-PLAN-waiting-list-gated-surfaces.md](002-PP-PLAN-waiting-list-gated-surfaces.md) | Waiting-list + gated practice surfaces execution plan (locked 2026-07-27): /request-access intake, practice-tracks teaser, contact fix, course gating, security ship-gate, upstream PR queue U1–U10, founder-locked copy and decisions. |

## Renames (references in old commit messages resolve here)

| Old name | Current name | When / why |
|---|---|---|
| `001-OD-PLAN-upstream-v2-sync-migration-map.md` | `001-OD-CHNG-upstream-v2-sync-map.md` | 2026-07-27 — doc-filing v4.4 compliance (`PLAN` is a PP type; a migration map is OD change management; description capped at 4 words). |
| `002-OD-PLAN-waiting-list-and-gated-practice-surfaces.md` | `002-PP-PLAN-waiting-list-gated-surfaces.md` | 2026-07-27 — same pass (an execution plan is PP-PLAN; description capped at 4 words). |

## Quick reference

Category codes (CC) and document types (ABCD) come from the canonical standard —
`~/.claude/skills/doc-filing/references/000-DR-STND-document-filing-system.md`.
Common here: `PP-PLAN` (product/planning plans), `OD-CHNG` (ops change
management), `AA-AACR` (after-action reviews), `TQ-SECU` (security audits).
