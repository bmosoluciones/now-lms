# ADR-5 — Gate the courses; the public catalog becomes a doctrine teaser

## ADR Metadata

| Field | Value |
|---|---|
| **ADR Number** | ADR-5 |
| **Title** | Gate the courses; the public catalog becomes a doctrine teaser |
| **Status** | Accepted |
| **Date** | 2026-07-27 |
| **Author** | Jeremy Longshore (founder direction, 2026-07-27; copy locked word-by-word) |
| **Backfilled** | 2026-07-28. Shipped and live: teaser at `/course/explore`, gating SQL executed at deploy, smoke enforcing all of it. |

## 1. Decision Summary

> **We will** flip every course, free-preview resource, and program to
> `publico=false`, serve a doctrine-voice practice-tracks teaser at
> `/course/explore` to everyone, and 302 anonymous gated-course hits to
> `/request-access`, **in order to** stop leaking course/vendor names and
> outline material to anonymous visitors while giving the most-primed visitor
> a conversion path, **accepting that** the platform shows no public catalog
> at all — scarcity is presented in doctrine voice, not in course listings.

## 2. Context

The landing page was doctrine-perfect, but one click deeper broke the model:
`/course/explore` listed vendor-named courses plus demo junk to anonymous
visitors; course detail pages rendered fully without login; free-preview
resources leaked outlines with zero regard for `Curso.publico`; and
`/contact` was a zombie — disabled in settings yet still serving an off-brand
form whose submissions went nowhere.

With the curriculum private (ADR-3) and admissions invitation-only, a public
catalog had no honest function: it could only leak positioning or sit empty.

## 3. Decision Drivers

| Driver | Weight | Note |
|---|---|---|
| Assessment/IP containment | High | Course names, outlines, and preview resources telegraph the private curriculum |
| Doctrine coherence | High | Public vocabulary comes from the practice doctrine; the catalog page spoke in vendor names |
| Conversion | Medium | The anonymous visitor hitting a gated course is the most primed to convert — 302 to intake beats a bare 403 |
| Reversibility | Medium | Gating is a data change (`publico` flips), recorded at execution, reversible by the same statements |

## 4. Alternatives Considered

1. **Leave the catalog public, hide only content** — rejected: names and
   outlines are themselves the leak; free-preview resources rendered to anon
   regardless of course visibility (upstream bug, queue item U7).
2. **Kill the deeper pages entirely (404)** — rejected: wastes the
   highest-intent traffic and reads as a broken site.
3. **Auth-wall everything at the proxy** — rejected: blunt; breaks the
   landing page and intake, and hides nothing the data flip doesn't already.
4. **Gate + doctrine teaser + 302-to-intake (chosen)** — theme-only override
   for the teaser (`overrides/course_list.j2`, no core edit), a 4-line core
   edit for the 302, deploy-time SQL for the data flip.

## 5. Consequences

**Positive:** anonymous curl sweep shows zero course/vendor strings; members
are unaffected (their path is dashboard + enrollment checks, all native); the
deploy smoke hard-fails unless the teaser serves, `/request-access` is live,
and `/contact` 404s — a future deploy physically cannot regress the gate
silently.

**Negative / accepted:** members' course discovery is dashboard-only (the
member grid at `/course/explore` would have been empty anyway —
`_course_explore_query` filters on `publico` with no auth branch); the teaser
copy is founder-locked and cannot be reworded without a new approval; a
reseed must not resurrect `publico=true` (seeder idempotency guard verified).

**Residual exposure accepted at ship, tracked upstream:** `/course/
slide_show/<id>` has no access check (U8) and certificate lookup discloses
names (U9) — both queued as responsible-disclosure security PRs.

## 6. Review Triggers

- A public catalog ever becoming desirable again is a founder decision and a
  superseding ADR, not a bug report.
- Upstream landing U7/U8 → drop the corresponding deploy-scope acceptances.

## 7. Related

- ADR-3 (`008-AT-ADEC`) — why there is nothing honest to show publicly.
- ADR-4 (`009-AT-ADEC`) — the intake the 302 converts into.
- `011-PP-PLAN` — locked copy, gating SQL, security ship-gate, verification
  sweep.
