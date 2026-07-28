# PERSONAS.md — test personas

Scaffolded 2026-07-28 from the PRD (`000-docs/001-PP-PROD` §3). Each persona
lists its key flows and where they are exercised. Fork-scoped: personas of the
Intent Solutions deployment, not of the generic upstream LMS.

## P1 — Cohort member (primary)

Invited practitioner, admin-enrolled (invite-only; no self-service enrollment
into gated courses). Works inside the login gate.

| Key flow | Exercised by |
|---|---|
| Log in, land on dashboard | `tests/test_auth.py`, `tests/test_intent_learn_front_door.py` (auth pages) |
| Open an enrolled course and its resources | inherited courses/resources suite (`test_courses_*`, `test_resources_*`) |
| Take a graded evaluation | `tests/test_evaluations_routes.py`, `tests/test_evaluation_helpers.py` |
| Completion / certificate | `tests/test_certificates_comprehensive.py`, `tests/test_end_to_end_certificates.py` |

Coverage: adequate via the inherited suite; PG path is the honest signal.

## P2 — Operator / admin (secondary)

Intent Solutions staff running the platform.

| Key flow | Exercised by |
|---|---|
| Review access requests (`/admin/contact-messages?q=[ACCESS]`) | `tests/test_static_pages_admin.py` (admin contact list + `?q=` filter) |
| Enroll a member into a gated course | inherited enrollment/admin suite |
| Reseed curriculum (idempotent, cannot un-gate) | `tests/test_cca_seed.py` |
| Deploy + smoke | `scripts/deploy-smoke.sh` (production) |

Coverage: adequate; the `?q=` filter is a fork-local 3-line edit with test.

## P3 — Anonymous visitor (conversion path)

Highest-intent stranger; must never see course/vendor names or content.

| Key flow | Exercised by |
|---|---|
| Landing page → Request access CTA | `tests/test_intent_learn_front_door.py`, smoke |
| Practice-tracks teaser at `/course/explore` | `tests/test_intent_learn_front_door.py`, `features/gating_boundary.feature`, smoke |
| Gated-course hit → 302 to intake | `features/gating_boundary.feature` |
| Submit the intake (happy path + defenses) | `tests/test_request_access.py`, `features/request_access.feature` |

Coverage: strongest persona — it carries the real user data and the deploy
smoke enforces it in production.

## P4 — Upstream maintainer (indirect; no test flows)

Constituency, not a user: their conventions gate our upstream PRs
(`dev/test.sh` green, conventional commits, DCO). No fork test flows.
