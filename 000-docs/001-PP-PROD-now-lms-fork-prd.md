# Product Requirements Document — Intent Solutions Learn (NOW-LMS fork)

**Metadata**

| Field | Value |
|---|---|
| Document | PRD for the Intent Solutions fork of NOW-LMS |
| Status | Baseline (backfilled 2026-07-28; records the product as decided and shipped) |
| Maintainer | Intent Solutions (Jeremy Longshore) |
| Live at | `learn.intentsolutions.io` |
| Upstream | [`bmosoluciones/now-lms`](https://github.com/bmosoluciones/now-lms) (Apache-2.0) |
| Related | `FORK.md` (governance), ADRs 002/006/008/009/010 in this tree, `011-PP-PLAN` (waiting list plan) |

> This PRD is foundational and was backfilled: it records what the product
> *is* — decisions already made and shipped — so future work has a baseline to
> diff against. It is not an aspirational roadmap. Where a decision has its own
> ADR, the ADR is the authority and this document points at it.

---

## 1. Product Vision & Problem Statement

### 1.1 One-liner

**Intent Solutions Learn** is the invitation-only learning platform for the
Claude Partner Network cohort: one shared house method (systems thinking,
agentic delivery, evaluation, governance, production operations, peer review),
role-shaped practice tracks on top of it, and credential prep as optional proof
paths — run on NOW-LMS used as-is, matured upstream rather than forked into a
private product.

### 1.2 Problem definition

- **Who hurts today:** practitioners preparing for Claude certification and
  client delivery need structured curriculum, graded practice, and progress
  tracking. Ad-hoc doc folders and chat threads don't provide sequencing,
  enrollment, assessment, or completion state.
- **Why an LMS, why this one:** the need is a solved category. NOW-LMS ships
  courses, sections, resources, assessments, enrollment, roles
  (admin/instructor/moderator/student), theming, and multi-DB support under
  Apache-2.0. Building bespoke would be months of undifferentiated work
  (see ADR at `002-AT-ADEC`).
- **Why gated:** the curriculum includes question banks with answer keys.
  Public courses beside the assessments they grade is an assessment-integrity
  failure (see ADRs at `008-AT-ADEC` and `010-AT-ADEC`).
- **Cost of inaction:** cohort onboarding stays manual, practice work is
  unverifiable, and the public surface either leaks assessment material or
  sits empty.

## 2. Objectives

| Objective | Measure | Status at baseline |
|---|---|---|
| Cohort platform live and used | Platform serves the cohort at `learn.intentsolutions.io`; per-operator admin accounts provisioned | Shipped 2026-07-21 |
| Fork stays thin against upstream | Every fork-local change has an upstream path or a recorded permanent-exception rationale in `FORK.md` | Enforced; 4 upstream PRs merged 2026-07-26 (#214–#216, #217 direct) |
| Public surface converts without leaking | Anonymous visitors see doctrine-voice positioning + a working `/request-access` intake; zero course/vendor names, zero answer-key material public | Shipped 2026-07-27 |
| Curriculum is private IP | Teaching content lives in `intent-solutions-io/intent-curriculum` (private), seeded at deploy via `CCA_CONTENT_DIR` | Shipped 2026-07-27 |

## 3. Users

### 3.1 Cohort member (primary)

Invited practitioner in the Claude Partner Network cohort. Logs in, works
through the house core and their role-shaped track, takes graded practice
exams, earns completion. Enrolled by an admin (invite-only — there is no
self-service enrollment path into gated courses). Inside the login gate,
language rules relax; the public doctrine voice governs only public surfaces.

### 3.2 Operator / admin (secondary)

Intent Solutions staff. Provisions accounts, enrolls members, reviews
`/admin/contact-messages?q=[ACCESS]` weekly for waiting-list triage, reseeds
curriculum on DR rebuild. Uses NOW-LMS's native admin surface — the fork adds
no bespoke admin UI (native-first rule, ADR `009-AT-ADEC`).

### 3.3 Anonymous visitor (conversion path)

Arrives at the landing page or the practice-tracks teaser. Cannot see course
names, vendor names, or content. Their one action is the `/request-access`
work-sample intake; requests hold a place on the waiting list and are reviewed
by a person. Anonymous hits on gated courses 302 to the intake rather than
dead-ending at a 403.

### 3.4 Upstream maintainer (indirect)

BMO Soluciones. Not a user of the deployment, but a first-class constituency
of the fork: platform bugs and missing capabilities are contributed upstream
under their conventions (conventional commits, DCO sign-off, Crowdin for
translations), never carried as private behavior patches.

## 4. Scope

### 4.1 In scope (shipped at baseline)

1. **NOW-LMS platform, used natively** — courses, enrollment, assessment,
   roles, theming, `contact_messages`, admin surfaces, as upstream ships them.
2. **`intent_learn` theme** — the fork's entire brand layer
   (`now_lms/templates/themes/intent_learn/`), including the landing
   composition, auth pages, course detail, practice-tracks teaser, and the
   `/request-access` page template. Branding is data, not code.
3. **`/request-access` waiting-list intake** — one thin fork blueprint
   (`now_lms/vistas/request_access.py`) storing to the native
   `ContactMessage` table with an `[ACCESS] ` subject discriminator, plus a
   best-effort Slack ping (see ADR `009-AT-ADEC` and `011-PP-PLAN`).
4. **Gated courses** — `publico=false` across courses, free-preview resources,
   and programs; anonymous gated-course GETs 302 to the intake (ADR
   `010-AT-ADEC`).
5. **Private curriculum, public seeder** — `scripts/seed_cca_courses.py`
   (idempotent) reads banks + lessons from a private checkout at seed time
   (ADR `008-AT-ADEC`).
6. **English platform surface** — full i18n conversion carried fork-locally,
   offered upstream via bmosoluciones/now-lms#181.
7. **Deploy manifest + smoke** — `docker-compose.yml` for the VPS, healthcheck
   `X-Forwarded-Proto` fix, and a deploy smoke that hard-fails unless the
   gated front door is intact.

### 4.2 Explicitly out of scope

- **Bespoke LMS features** — any capability gap is an upstream contribution
  or it doesn't get built ("I'm not building custom" — the governing rule).
- **Payments/Stripe** — post-sync work, tracked separately (bead `now-lms-bc2`).
- **Panel follow-ups** (patterns library, write-ups, ritual, shepherd month) —
  each requires its own founder session before any build.
- **Public course catalog** — deliberately replaced by the doctrine teaser;
  reversal requires a founder decision, not a bug report.
- **Renaming/rebranding core source** — permanent merge-conflict tax; refused
  on sight per `AGENTS.md`.

### 4.3 Key assumptions

- Upstream remains active and accepts good contributions (validated: 4 PRs
  merged in one day, 2026-07-26).
- The cohort remains invitation-only; admissions run in small waves.
- The v2.0.0 upstream sync will land via the rebuild strategy (ADR
  `006-AT-ADEC`) and repair the currently-advisory test gate.

## 5. Functional requirements (baseline behavior)

| # | Requirement | Where it lives |
|---|---|---|
| F1 | Anonymous `/` serves the doctrine landing page; CTAs point at `/request-access` | `intent_learn` theme |
| F2 | `GET /request-access` renders the work-sample form; `POST` validates, stores a `ContactMessage` with `[ACCESS] ` subject, fires best-effort Slack ping | `vistas/request_access.py` |
| F3 | `/course/explore` serves the practice-tracks teaser to everyone — no course or vendor names | `overrides/course_list.j2` |
| F4 | Anonymous GET on a gated course 302s to `/request-access`; authenticated-without-enrollment keeps 403 | `vistas/courses/base.py` (4-line core edit) |
| F5 | `/contact` returns 404 while `enable_contact` is disabled | `vistas/static_pages.py` (disposable core edit; dies at v2.0.0 sync) |
| F6 | Members reach enrolled courses via dashboard + `/course/<code>/view`; enrollment checks are native | Upstream, unmodified |
| F7 | Admin reviews access requests at `/admin/contact-messages?q=[ACCESS]` | Upstream admin surface, unmodified |
| F8 | Curriculum seeds idempotently from `CCA_CONTENT_DIR` | `scripts/seed_cca_courses.py` |

## 6. Non-functional requirements

- **Security (ship-gate, all P0 adopted — `011-PP-PLAN` §security):** real rate
  limit on the intake POST + Caddy outer wall; autoescaped `.html` template
  (never `.j2` for user-input pages); CSRF enforced and tested with
  `WTF_CSRF_ENABLED=True`; server-side length caps before insert; honeypot +
  signed-timestamp minimum time-to-submit; `SESSION_COOKIE_SECURE`.
- **Privacy:** "We store what you submit and use it only to review your
  request." Slack pings carry name + snippet + admin deep-link, never the
  applicant's email/employer. Google Fonts CDN removed from the theme
  (self-hosted assets); ionicons vendoring tracked for the CSP change at sync.
- **Data:** production is PostgreSQL 16 (`pg8000`); SQLite is test-only. The
  fresh-DB bootstrap fix (`create_all()` + `alembic.stamp(head)`, fork commit
  `55900ed`) is load-bearing and fork-local — see `AGENTS.md` "fresh-DB gotcha".
- **Availability:** single VPS deployment behind Caddy with `FORCE_HTTPS`;
  healthcheck must send `X-Forwarded-Proto: https`. Slack being down never
  breaks a submission — the DB row is the durability.
- **Lint/CI floor:** ruff + flake8 + `pylint --fail-under=9.5` blocking on the
  deploy line (`deploy-line-ci.yml`); PostgreSQL pytest advisory until the
  v2.0.0 sync repairs the inherited suite.

## 7. Risks (standing)

| Risk | Mitigation |
|---|---|
| Upstream sync drops a fork-critical commit (the #179 bootstrap fix was merged upstream and then *lost*) | `007-OD-CHNG` measured MUST-SURVIVE set; deploy smoke physically fails if the gated front door regresses |
| Fork drifts into a private product | `FORK.md` posture + per-change upstream-path column; anti-patterns list in `AGENTS.md` |
| Assessment material leaks | Curriculum in a private repo; courses gated; free-preview resources flipped in the same deploy SQL |
| Inherited test suite masks regressions | Test gate shipped advisory (PR #18) with the 34 pre-existing PG failures documented; flips to blocking at the sync |

## 8. Success metrics

- Deploy smoke green on every deploy (`/request-access` 200, teaser serving,
  `/contact` 404).
- Zero public exposure of course names, vendor names, or bank content
  (anonymous curl sweep in `011-PP-PLAN` §verification).
- Waiting-list loop functioning: DB row + Slack ping per submission; weekly
  admin review.
- Upstream contribution lane alive: PRs accepted under upstream conventions
  (4 merged at baseline; queue U1–U10 defined).

## 9. Release strategy

Continuous on the `deploy/now-lms-fixed` branch: PR → `deploy-line-ci.yml`
(lint blocking) + AI review → merge → deploy to the VPS via docker-compose →
smoke. The next major release event is the upstream v2.0.0 sync, executed per
ADR `006-AT-ADEC` and the `007-OD-CHNG` migration map, gated on a
production-snapshot migration rehearsal.

## 10. Document management

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-07-28 | Backfilled baseline: records the product as decided 2026-07-21 → 2026-07-27 and shipped. |

Changes to what the product *is* (scope, gating, fork posture) require a new
ADR in this tree, not an edit to this document's history.
