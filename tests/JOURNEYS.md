# JOURNEYS.md — user journeys and per-step test mapping

Scaffolded 2026-07-28 from the PRD and the locked plan's verification sweep
(`000-docs/011-PP-PLAN` §verification). Steps link to RTM requirements;
untested steps are flagged with the linked REQ's MoSCoW severity.

## J1 — Anonymous visitor converts to the waiting list (P3)

| Step | Layer | Exercised by | Status |
|---|---|---|---|
| 1. Land on `/` (doctrine landing) | L3/L6 | `test_intent_learn_front_door.py`, smoke | covered |
| 2. Click deeper → `/course/explore` teaser (REQ-004) | L3/L6 | front-door tests, `gating_boundary.feature`, smoke | covered |
| 3. Hit a gated course link → 302 to intake (REQ-005) | L3/L6 | `gating_boundary.feature`, front-door tests | covered |
| 4. `GET /request-access` form (REQ-001) | L3/L7 | `test_request_access.py`, smoke | covered |
| 5. Submit → row + best-effort ping (REQ-001/002/003) | L3/L4 | `test_request_access.py` | covered |
| 6. Post-submit confirmation copy (founder-locked) | L3 | `test_request_access.py` | covered |

## J2 — Member works a course (P1)

| Step | Layer | Exercised by | Status |
|---|---|---|---|
| 1. Log in (branded auth pages) | L3 | `test_auth.py` | covered |
| 2. Dashboard → enrolled course (REQ-012) | L3 | inherited courses suite | covered |
| 3. Work resources / slides | L3 | `test_resources_*` — note `/course/slide_show/<id>` auth gap is an accepted-at-ship upstream item (U8) | covered (gap accepted + tracked) |
| 4. Evaluation → completion → certificate | L3 | evaluations + certificates suites | covered |

## J3 — Operator triages an access request (P2)

| Step | Layer | Exercised by | Status |
|---|---|---|---|
| 1. Slack ping arrives in #leads-contact | L4 | manual (one real end-to-end submission verified at ship; not CI-automatable — external service) | partial, accepted |
| 2. Review `/admin/contact-messages?q=[ACCESS]` | L3 | `test_static_pages_admin.py` | covered |
| 3. Status workflow (new → reviewing → resolved) | L3 | inherited contact-messages suite | covered |
| 4. Outreach (manual email until MXroute wiring, bead `now-lms-kyv`) | — | out of test scope (human step) | n/a |

## J4 — Operator rebuilds from nothing (DR)

| Step | Layer | Exercised by | Status |
|---|---|---|---|
| 1. Fresh PostgreSQL boot (REQ-009) | L4 | `test_alembic_upgrade.py` + fork commit `55900ed`; fuller test on the rescued branch | covered |
| 2. Seed curriculum from private checkout (REQ-008) | L4 | `test_cca_seed.py` | covered |
| 3. Deploy smoke (REQ-011) | L7 | `scripts/deploy-smoke.sh` | covered (at deploy) |

## Flagged

- J3 step 1 is manual-by-nature (external Slack); accepted, documented here so
  it is a decision, not an oversight.
