# ADR-9 — Serve members a fork-local dashboard instead of the upstream student panel

## ADR Metadata

| Field | Value |
|---|---|
| **ADR Number** | ADR-9 |
| **Title** | Serve members a fork-local dashboard instead of the upstream student panel |
| **Status** | Accepted |
| **Date** | 2026-08-08 (proposed) · 2026-08-10 (accepted) |
| **Author** | Filed with the implementation on `feat/member-dashboard` |
| **Decision needed from** | Repo owner — accept, amend, or reject |
| **Note on numbering** | ADR-6 is claimed by open PR #37, ADR-7 is `014-AT-ADEC`, ADR-8 is `015-AT-ADEC`. This takes ADR-9 and document number `016`. |

## 1. Decision Summary

> **We will** serve `tipo == "student"` a fork-local dashboard at `/dashboard`
> (`now_lms/vistas/member_dashboard.py` plus a themed page), leaving the
> upstream `inicio/panel_user.html` in place for instructors and moderators,
> **in order to** show a member the things the platform already knows about them
> and stop showing them things that are not true, **accepting that** this is
> another fork-local surface to re-apply at each upstream sync, and that the
> upstream panel now has fewer callers exercising it.

## 2. Context

The upstream student panel is the first thing a cohort member sees after
logging in, and an audit of it against this tree found the following, all
verified in source rather than reported:

- **It cannot be branded.** `home.py` renders the literal string
  `"inicio/panel_user.html"`, and `themes.py` has no resolver for it, so unlike
  home / course-list / course-view / course-take there is no override slot. Its
  largest element is a hardcoded `linear-gradient(135deg, #007bff …)`, which
  `brand.css` cannot reach. Of the eight destinations reachable from the panel,
  eight render in upstream styling.
- **It showed a member almost nothing true about themselves.**
  `CursoUsuarioAvance.avance` is a maintained 0-100 percentage updated on every
  completed resource. No member-facing template read it. Meanwhile
  `ops/lms/lms-progress-digest.sh` selects that same column and mails a
  per-member progress table to staff weekly. Staff could see a learner's
  completion; the learner could not.
- **It fabricated a counter.** `panel_user.html:109` is the literal character
  `0` with the caption "Soon", permanently, including for a member actually
  enrolled in a master class.
- **Its empty state was a closed loop.** The only call to action pointed at
  `/course/explore`, which filters `publico=True`, while every course on this
  deployment is gated and the fork's own `course_list.j2` override renders no
  course data at all.
- **It disagreed with `/my_courses`.** The panel counted `EstudianteCurso` rows
  without the `vigente` filter that `courses/base.py:529` applies, so a member
  with a lapsed enrolment saw different course counts on two pages.
- **Built surfaces had no entry point.** `/my-credentials` — a themed, tested,
  working member page — was referenced from nowhere in the entire template tree.

## 3. Decision Drivers

| Driver | Weight | Note |
|---|---|---|
| Member trust | High | A dashboard that shows a fabricated zero and hides real progress teaches members not to read it |
| Branding without core edits | High | No override slot exists, so the choice is a core edit or a new surface |
| Blast radius | High | Instructors and moderators keep the upstream panel untouched, so the change reaches only students |
| Sync cost | Medium | One more fork-local blueprint to carry, plus ~10 lines of core edits |
| Reuse over rebuild | Medium | Every value shown already had a helper or a column; nothing new was computed |

## 4. Alternatives Considered

### 4.1 Edit `home.panel` and `inicio/panel_user.html` in place — rejected

The obvious move, and it needs stating plainly: it is the smallest diff by line
count and adds no new file.

Rejected because `home.py` and `panel_user.html` are upstream files upstream
actively maintains, and a test merge of `upstream/main` into
`deploy/now-lms-fixed` already produces 61 conflicted files. A large diff
against a function and a template that upstream also edits is the most
expensive possible place to carry a fork change. The `prior_credentials` and
`request_access` precedents both chose a new module with no imports from the
file being replaced, specifically so an upstream restructure cannot orphan them.

### 4.2 Add a theme-override resolver for the panel, then override it — deferred

`themes.py` already has seven resolvers of identical shape; an eighth for the
panel is ~12 lines and is genuinely upstream-eligible, since every NOW-LMS
deployment would benefit from a themable dashboard.

Deferred rather than rejected because it solves only the *branding* half. The
panel's content problems — the fabricated counter, the missing progress, the
catalog loop, the `vigente` mismatch — live in the view's context dict, not the
template, so a theme override would still need `home.panel` to pass different
data. **This is the piece to offer upstream if this work is ever contributed**,
and §6 names the trigger.

### 4.3 A fork-local blueprint at `/dashboard` (chosen)

One new module, one themed page, three core edits totalling about ten lines.

## 5. Consequences

**Positive:** a member sees their own progress, their credentials link, what is
coming up, and pinned announcements. The page is branded through the theme's
Bootstrap token remap rather than by fighting an inline gradient. Instructors
and moderators are untouched, so the blast radius is students only. Query count
is flat in the number of enrolled courses, asserted by a test that adds four
courses and requires the count not to move.

**Negative / accepted:** another fork-local surface to re-apply at each sync.
The upstream panel keeps its instructor and moderator branches, so it is not
dead code, but its student branch now has no caller in this deployment and will
rot quietly. The three core edits are small but real and are recorded in
`FORK.md`.

**One channel for announcements.** `/dashboard/announcements` redirects to the
dashboard instead of rendering a second reader for the same global
announcements. This is a product decision — members should have one place to
look — and deliberately does **not** touch the native `Announcement` model, the
admin or instructor CRUD, or the per-course announcements page. Keeping the
native model is what lets staff pin something to the top of the member's home
with the admin UI they already have.

**Two upstream bugs fixed in passing**, both worth offering upstream: a
`log.warning(mis_cursos)` that dumped ORM objects into production logs at
WARNING level on every student dashboard load, and the global announcements
filter comparing `expires_at` against `datetime.now()` (local time) when the
column is stored as naive UTC.

## 6. Review Triggers

- **Offer §4.2 upstream** when any of these fires: upstream shows interest in a
  themable member panel; a second fork surface needs the same override
  machinery; or the next sync makes the cost of carrying this blueprint visible.
- The Community Hub feed lands (ADR-8) → the dashboard's main column becomes the
  feed. That is an additive change to this page, not a superseding decision.
- Instructors or moderators ask for the same treatment → extend this blueprint
  rather than adding a third panel, and supersede this ADR.
- The upstream panel's student branch is confirmed unreachable for a full
  release cycle → propose removing it upstream rather than carrying a dead
  branch.

## 7. Related

- ADR-1 (`002-AT-ADEC`) — the native-first rule this deviates from.
- ADR-5 (`010-AT-ADEC`) — the gating posture that makes `/course/explore` empty
  for members, which is why the old empty state was a closed loop.
- ADR-7 (`014-AT-ADEC`) — the fork-local blueprint precedent this follows.
- ADR-8 (`015-AT-ADEC`) — the Community Hub, whose feed lands on this page.
- `FORK.md` — the divergence row with its layer and retirement condition.
