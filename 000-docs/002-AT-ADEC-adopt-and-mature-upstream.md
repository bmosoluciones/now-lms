# ADR-1 — Adopt NOW-LMS as-is and mature it upstream; no private forks of behavior

## ADR Metadata

| Field | Value |
|---|---|
| **ADR Number** | ADR-1 |
| **Title** | Adopt NOW-LMS as-is and mature it upstream; no private forks of behavior |
| **Status** | Accepted |
| **Date** | 2026-07-21 |
| **Author** | Jeremy Longshore (founder decision) |
| **Backfilled** | 2026-07-28, from the decision record quoted in `011-PP-PLAN` and the posture shipped in `FORK.md` |

## 1. Decision Summary

> **We will** run NOW-LMS's native features exactly as upstream ships them and
> contribute every fix or missing capability to `bmosoluciones/now-lms` as a
> real upstream PR, **in order to** keep this fork a thin tracking mirror whose
> every divergence has a retirement path, **accepting that** we wait on a
> maintainer for fixes we could land locally in an afternoon, and that some
> gaps go unfilled rather than built bespoke.

The founder's phrasing, 2026-07-21, is the governing rule: *"Use the native
features as they ship. Gaps → upstream contributions (maturing the project),
never bespoke one-offs. 'I'm not building custom' is the governing rule."*

## 2. Context

Intent Solutions needed a learning platform for the Claude Partner Network
cohort. NOW-LMS (Apache-2.0, Flask, multi-DB, themed, with courses /
enrollment / assessment / roles built in) covers the need. The strategic
question was posture: consume it as a product, or own a divergent copy.

Forks of active projects die one of two deaths: the merge-tax death (every
upstream sync fights every local patch) or the abandonment death (the fork
stops syncing and quietly becomes an unmaintained private product). Both are
downstream of the same choice — carrying behavior changes privately.

## 3. Decision Drivers

| Driver | Weight | Note |
|---|---|---|
| Sync cost over time | High | Every private core patch is a permanent conflict tax on every upstream pull |
| Team size | High | One founder-operator; no capacity to maintain a divergent LMS |
| Upstream health | Medium | Active maintainer; validated later — 4 fork PRs merged in one day (2026-07-26) |
| Brand needs | Medium | Full rebrand required — but NOW-LMS ships a native theme layer (`NOW_LMS_THEMES_DIR`), so branding never needs core edits |
| Contribution posture | Medium | Upstream work is public proof-of-practice, aligned with the practice doctrine |

## 4. Alternatives Considered

1. **Hard fork as a private product** — rejected: permanent maintenance of an
   entire LMS for a cohort-sized deployment; every upstream improvement must be
   ported by hand or lost.
2. **Bespoke platform build** — rejected: months of undifferentiated work
   (auth, enrollment, assessment, admin) that NOW-LMS already ships.
3. **SaaS LMS** — rejected: no theming depth for the doctrine front door, no
   self-host on the estate VPS, recurring per-seat cost, and no upstream lane.
4. **Adopt as-is + upstream contributions (chosen)** — the fork carries only:
   the theme layer (data, not code), deploy wiring, and temporarily any fix
   whose upstream PR hasn't merged yet.

## 5. Consequences

**Positive:** the fork stays syncable (proven by the v2.0.0 sync analysis in
`007-OD-CHNG`: the entire conflict surface traces to one retired layer);
platform fixes benefit everyone and are maintained by upstream; `FORK.md` can
list every divergence in one table with a retirement condition per row.

**Negative / accepted:** dependent on maintainer responsiveness (mitigated by
carrying merged-pending fixes fork-locally with the PR as the retirement
trigger); the one intentional core-source exception (English i18n wrapping)
must be tracked until upstream #181 resolves; product gaps that upstream would
not want are simply not built.

**Enforcement:** `FORK.md` is the posture document; `AGENTS.md` carries the
refuse-on-sight anti-patterns (no package renames, no branding in core source,
no fork entries in upstream's `CHANGELOG.md`).

## 6. Review Triggers

- Upstream goes dormant (no merges for ~6 months) → reconsider posture.
- A required capability is rejected upstream on direction (not quality)
  grounds → per-case founder decision, recorded as a new ADR.

## 7. Related

- `FORK.md` — the operational form of this decision.
- ADR-2 (`006-AT-ADEC`) — the sync strategy this posture makes cheap.
- ADR-4 (`009-AT-ADEC`) — native-first applied to the waiting list.
- `011-PP-PLAN` — quotes the governing rule verbatim.
