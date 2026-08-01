# ADR-7 — Store learner-reported prior credentials in a dedicated table, and require a verification link rather than an image

## ADR Metadata

| Field | Value |
|---|---|
| **ADR Number** | ADR-7 |
| **Title** | Store learner-reported prior credentials in a dedicated table, and require a verification link rather than an image |
| **Status** | Proposed |
| **Date** | 2026-07-31 |
| **Author** | Filed with the implementation on `feat/prior-credential-tracking` |
| **Note on numbering** | ADR-6 (short-answer evaluations) is claimed by the open PR #37 and is not yet merged; this decision takes ADR-7 so the two cannot collide. |

## 1. Decision Summary

> **We will** record the credentials a learner earned elsewhere in a new
> `prior_credentials` table, with a **required** issuer verification URL and an
> **optional** image stored under the private files directory and served through
> an authorization-checked route, **in order to** give the team one reviewable
> record of who has completed which preliminary courses, **accepting that** this
> is a bespoke model and therefore a deliberate deviation from ADR-1's
> native-first rule, carried fork-local until upstream accepts it.

Nothing in the application gates on these records. Enrollment, course access and
evaluations are unaffected by what a learner does or does not record.

## 2. Context

Learners preparing for the Claude Certified Architect (Foundations) exam
complete free Anthropic Academy courses first. The team wants one place to see
who has done which, with the certificate ID and, where the learner has one, an
image of the certificate.

The platform has no surface for this. `Certificacion` and `Certificado` model
certificates the platform **issues**; there is no concept of a credential a
learner brings in. `Question.type` accepts only `multiple` or `boolean`, so an
evaluation cannot carry a written answer or a file. `ContactMessage` is text
with no attachment. And the only student-facing upload anywhere in the codebase
is the profile photo (`vistas/profiles/user.py`).

## 3. Decision Drivers

| Driver | Weight | Note |
|---|---|---|
| Evidence quality | High | Skilljar credentials carry a public verification URL. A reviewer can open a link; an image only shows what the learner chose to upload |
| Personal data exposure | High | A certificate image carries a real name and credential number, and `UPLOADS_AUTOSERVE` publishes every UploadSet file at `/_uploads/<set>/<filename>` with no authorization |
| Native-first rule (ADR-1) | High | Argues against this decision. See §4.1 — no native table can hold a per-credential file reference |
| Reviewability | Medium | Staff want per-learner completeness at a glance, which semi-structured text cannot give |
| Sync cost | Medium | A new model and migration must be re-applied at each upstream sync until upstream accepts the feature |

## 4. Alternatives Considered

### 4.1 Native `ContactMessage` + subject discriminator (the ADR-4 pattern) — rejected

This is the strongest argument against the decision and deserves stating
plainly: ADR-4 chose exactly this for the waiting list, and the same reasoning
applies here — zero tables, zero migrations, a native admin surface, nothing to
re-apply at a sync.

It was rejected on two grounds. First, `ContactMessage` has no file column and
no attachment concept, so the image requirement has nowhere to live; adding one
would modify a native model, which is a larger deviation than adding a new one.
Second, the useful output here is a per-learner completeness view across a fixed
set of eight courses, and computing that from a `LIKE '[CREDENTIAL] %'` query
over a text template is materially worse than a typed row — the waiting list
never needed to aggregate, and this does.

### 4.2 Image-first, verification link optional — rejected

This is what was originally asked for. It was inverted deliberately: an image is
trivially fabricated and proves nothing, while an issuer URL can be checked. The
image is kept as an optional attachment because a learner may hold a credential
whose issuer has no public verification page.

### 4.3 Off-platform (a form plus a spreadsheet) — rejected

Zero code and would ship the same afternoon, but the records live outside the
platform, cannot be shown back to the learner, and cannot later become a gate
without redoing the work.

### 4.4 A dedicated `prior_credentials` table (chosen)

One model, one guarded Alembic revision, one blueprint, two themed pages.

## 5. Consequences

**Positive:** typed rows support the completeness view; the learner sees their
own record; uploads are not publicly reachable; nothing about course access
changes, so the blast radius of a defect here is confined to this feature.

**Negative / accepted:** this is a bespoke model, the thing ADR-1 exists to
prevent. It must be re-applied at every upstream sync until upstream takes it.
The credential catalog is a module constant in shared source
(`vistas/prior_credentials.py`), which is the specific thing blocking an
upstream contribution — upstream would need it admin-configurable.

**Security posture shipped with it:**

- Uploads land in `DIRECTORIO_ARCHIVOS_PRIVADOS/credenciales`, never an
  UploadSet, because the autoserve route has no authorization.
- The stored filename is derived from the record id, never from the
  client-supplied filename.
- `GET /my-credentials/<id>/image` serves only to the owner or to
  admin/instructor; everyone else gets 403, anonymous gets the login redirect.
- 5 MB cap enforced in the route, since this deployment sets no
  `MAX_CONTENT_LENGTH`.
- Extension allow-list (`png`, `jpg`, `jpeg`, `webp`, `pdf`).
- The verification URL must be `https` with a hostname, so a `javascript:` value
  cannot reach a rendered anchor.
- Both mutating routes go through a `FlaskForm` and `validate_on_submit()`.
  This application does not install `CSRFProtect`, so `csrf_token()` is not a
  template global and a hand-rolled POST form would carry no CSRF protection at
  all.
- Deleting someone else's record returns 404 rather than 403, so the response
  does not confirm the record exists.

**Compliance note.** The eight Academy courses are Intent Solutions
recommendations, not prerequisites set by the certification provider. The
learner-facing copy says so, per the standing rule that a course is not an
official requirement unless the page says so and cites a verified source.

## 6. Review Triggers

- The team wants this to actually gate enrollment → superseding ADR, because
  that changes the compliance wording as much as the code.
- Upstream accepts a recognition-of-prior-learning feature → drop the
  fork-local copy and make the catalog configurable.
- The catalog needs to change per cohort → move it out of source before it is
  edited a third time.

## 7. Related

- ADR-1 (`002-AT-ADEC`) — the native-first rule this decision deviates from.
- ADR-4 (`009-AT-ADEC`) — the native-reuse precedent argued against in §4.1.
- `FORK.md` — the fork-local carries table, where this feature is registered
  with its upstream path.
