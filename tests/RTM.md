# RTM.md — Requirements Traceability Matrix

Scaffolded 2026-07-28 from the PRD (`000-docs/001-PP-PROD` §5), the ADR set,
and the locked plan (`000-docs/011-PP-PLAN`). MoSCoW tags are
**engineer-owned**: the AI never lowers a MUST. Upstream-inherited platform
behavior is deliberately NOT enumerated here — this matrix traces the
**fork's** requirements only; the inherited suite covers the platform.

| REQ | Requirement | MoSCoW | Source | Covered by |
|---|---|---|---|---|
| REQ-001 | `/request-access` GET renders the intake; POST stores a `ContactMessage` with `[ACCESS] ` subject prefix | MUST | ADR-4, PRD F2 | `tests/test_request_access.py`, `features/request_access.feature`, `scripts/deploy-smoke.sh` |
| REQ-002 | Slack ping is best-effort: webhook failure never loses the DB row | MUST | ADR-4, 011-PP-PLAN §slack | `tests/test_request_access.py`, `features/request_access.feature` |
| REQ-003 | Intake defenses: CSRF enforced (tested with `WTF_CSRF_ENABLED=True`), honeypot pretends success storing nothing, min-time-to-submit token, server-side length caps | MUST | 011-PP-PLAN §ship-gate | `tests/test_request_access.py`, `features/request_access.feature` |
| REQ-004 | `/course/explore` serves the doctrine teaser to everyone — zero course/vendor names | MUST | ADR-5, PRD F3 | `tests/test_intent_learn_front_door.py`, `features/gating_boundary.feature`, `scripts/deploy-smoke.sh` |
| REQ-005 | Anonymous GET on a gated course 302s to `/request-access`; authenticated-unenrolled keeps 403 | MUST | ADR-5, PRD F4 | `features/gating_boundary.feature`, `tests/test_intent_learn_front_door.py` |
| REQ-006 | `/contact` returns 404 while `enable_contact` is disabled | MUST | ADR-5, PRD F5 | `tests/test_end_to_end_contact.py`, `scripts/deploy-smoke.sh`, `features/gating_boundary.feature` |
| REQ-007 | Landing CTAs point at `/request-access`, never a raw `mailto:` (mailto stays as the secondary path on the intake page) | MUST | 011-PP-PLAN §C | `tests/test_intent_learn_front_door.py`, `scripts/deploy-smoke.sh` |
| REQ-008 | Curriculum seeds idempotently from `CCA_CONTENT_DIR` (private checkout); a reseed cannot resurrect `publico=true` | MUST | ADR-3, PRD F8 | `tests/test_cca_seed.py` |
| REQ-009 | Fresh-PostgreSQL boot succeeds (`create_all()` + `alembic.stamp(head)` — fork commit `55900ed`) | MUST | AGENTS.md §fresh-DB | `tests/test_alembic_upgrade.py`; fuller test preserved on `fix/postgresql-fresh-database-bootstrap` |
| REQ-010 | Theme serves no external CDN assets (fonts self-hosted; ionicons/Alpine CDN loads removed as dead code 2026-07-26, commit `a63a47c`) | SHOULD | 007-OD-CHNG §7, bead `now-lms-fzl` (closed) | front-door contract tests: no-CDN guards over `header.j2`/`base.j2`/`js.j2` + `scripts/deploy-smoke.sh` CDN grep |
| REQ-011 | Deploy smoke hard-fails unless the gated front door is intact (intake serves, teaser live, contact 404) | MUST | ADR-5, PRD §8 | `scripts/deploy-smoke.sh` (runs at deploy) |
| REQ-012 | Members reach enrolled courses via dashboard + native enrollment checks | MUST | PRD F6 | inherited suite (courses/enrollment tests), `features/gating_boundary.feature` |

## Uncovered / partial

None. (The scaffold-time entry here claimed REQ-010/ionicons was uncovered —
stale: it was resolved 2026-07-26 by removing the dead CDN loads, commit
`a63a47c`, with two-direction no-CDN test guards. Corrected 2026-07-28.)

## Orphans

None flagged at scaffold time — the fork-local test files
(`test_request_access.py`, `test_intent_learn_front_door.py`,
`test_cca_seed.py`) all trace to REQs above. The inherited upstream suite is
out of scope for orphan analysis by policy (see header).
