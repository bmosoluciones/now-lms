# ADR-4 — Store access requests in the native ContactMessage table, not a bespoke WaitingList model

## ADR Metadata

| Field | Value |
|---|---|
| **ADR Number** | ADR-4 |
| **Title** | Store access requests in the native `ContactMessage` table, not a bespoke `WaitingList` model |
| **Status** | Accepted |
| **Date** | 2026-07-27 |
| **Author** | Design superseded during the Explore sweep; adopted under the ADR-1 native-first rule |
| **Backfilled** | 2026-07-28. Shipped in the `feat/request-access` series (fork PR #25). |

## 1. Decision Summary

> **We will** store `/request-access` submissions as rows in NOW-LMS's native
> `contact_messages` table, discriminated by an ASCII subject prefix
> `[ACCESS] `, with the vetting fields composed into `message` as a fixed
> labeled template, **in order to** ship a durable waiting list with zero new
> tables, zero migrations, and the platform's existing admin surface and
> status workflow, **accepting that** vetting fields are semi-structured text
> rather than columns, and the canonical query is
> `WHERE subject LIKE '[ACCESS] %'` rather than a typed filter.

## 2. Context

The waiting-list feature needed durable storage, an admin review surface, and
a status workflow. The original design (preserved as the do-not-build Appendix
A of `011-PP-PLAN`) created a dedicated `WaitingList` model, an Alembic
migration, a `waitlist` blueprint, and a cloned admin surface.

The Explore sweep then found the platform already ships the exact pattern:
contact submissions store to `contact_messages` (status workflow
new → reviewing → resolved, admin notes) with a complete admin surface at
`/admin/contact-messages` plus a dashboard unseen-badge. Under ADR-1's
governing rule — native features as they ship, never bespoke one-offs — a
bespoke model duplicating a native one is exactly the anti-pattern.

## 3. Decision Drivers

| Driver | Weight | Note |
|---|---|---|
| Native-first rule (ADR-1) | High | The platform ships the pattern; duplicating it is a private fork of behavior |
| Migration risk | High | Zero migrations = nothing to rehearse, nothing to conflict at the v2.0.0 sync |
| Sync survival | High | The route lives in a NEW file with zero imports from `static_pages.py` (which dies at v2.0.0), so the split cannot orphan it |
| Admin surface | Medium | Reviewers use `/admin/contact-messages?q=[ACCESS]` — no new UI to build or maintain |
| Query ergonomics | Low | A `LIKE` prefix query is crude but sufficient at waiting-list volume |

## 4. Alternatives Considered

1. **Bespoke `WaitingList` model + migration + admin clone (original design)**
   — superseded: new table, guarded migration, and a cloned admin surface to
   maintain across syncs, all duplicating what `contact_messages` already
   does. Recorded verbatim in `011-PP-PLAN` Appendix A so it is never
   re-derived.
2. **Relay through the VPS `forms-api` service** — rejected: loopback bind,
   a 3/hour/IP rate limit shared across one egress IP, and a schema that
   cannot carry the vetting fields.
3. **Email-only (`mailto:`)** — the status quo ante; rejected by the panel
   finding that the mailto was "the right question wired to the wrong pipe" —
   no durability, no review workflow. The mailto survives only as the
   secondary "prefer email?" path on the intake page.
4. **Native `ContactMessage` + discriminator subject (chosen)** — one thin
   fork route (`now_lms/vistas/request_access.py`) renders the themed page
   and on POST writes the row + fires a best-effort Slack ping.

## 5. Consequences

**Positive:** no schema change ever; the model, admin, and status workflow are
upstream-maintained; the Slack ping is the only fork-owned moving part and
retires when a generic `CONTACT_WEBHOOK_URL` feature is accepted upstream
(queue item U2).

**Negative / accepted:** `[ACCESS] ` must never be gettext-wrapped (it is a
data discriminator, not UI copy) and the name is truncated to fit
`String(200)`; parsing vetting fields back out of `message` relies on the
fixed labeled template. Both are documented in `011-PP-PLAN` §governing-rule.

**Security posture shipped with it** (the P0 ship-gate): real rate limiter,
autoescaped `.html` template, CSRF enforced-and-tested, server-side length
caps, honeypot + signed-timestamp minimum time-to-submit.

## 6. Review Triggers

- Upstream accepts the generic webhook feature → drop the fork's ping code.
- Waiting-list volume makes the `LIKE` query or text-template parsing a real
  operational cost → revisit with a superseding ADR (not a quiet migration).

## 7. Related

- ADR-1 (`002-AT-ADEC`) — the rule this decision applies.
- ADR-5 (`010-AT-ADEC`) — the gating that makes the intake the conversion path.
- `011-PP-PLAN` — full plan, locked copy, security ship-gate, Appendix A.
