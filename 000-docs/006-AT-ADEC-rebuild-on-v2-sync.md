# ADR-2 — Rebuild on upstream v2.0.0 by cherry-picking the must-survive set, not merging

## ADR Metadata

| Field | Value |
|---|---|
| **ADR Number** | ADR-2 |
| **Title** | Rebuild on upstream v2.0.0 by cherry-picking the must-survive set, not merging |
| **Status** | Accepted |
| **Date** | 2026-07-26 |
| **Author** | Measured analysis, `007-OD-CHNG-upstream-v2-sync-map.md`; adopted as the strategy of record |
| **Backfilled** | 2026-07-28. The sync itself has NOT executed; this ADR fixes the *strategy*, which the migration map argues from measurement. |

## 1. Decision Summary

> **We will** execute the upstream v2.0.0 sync by branching `sync/v2.0.0` from
> `upstream/main` and cherry-picking only the measured MUST-SURVIVE commit set
> (26 commits + later additions recorded in `007-OD-CHNG` §2), **in order to**
> make the 60 conflicts owned by the retired i18n layer impossible *by
> construction*, **accepting that** every surviving commit must be explicitly
> enumerated — an omission loses work silently rather than loudly.

## 2. Context

Measured 2026-07-26 (fork @ `4755503` vs `upstream/main` @ `b7bc8cf`):
divergence 41 ahead / 111 behind; a test merge produces **61 conflicted
files**, of which **60 (98%)** are touched by the four dead fork i18n commits
that upstream v2.0.0's own catalogs supersede. The conflict count for work we
actually keep is zero.

The obvious path — merge, then revert the dead commits — was tested and fails:
three of the four i18n commits conflict on revert because later fork commits
build on them. A merge-then-drop leaves 56 conflicts to hand-resolve, each
resolution an opportunity to reintroduce a Spanish string or drop an upstream
fix.

## 3. Decision Drivers

| Driver | Weight | Note |
|---|---|---|
| Conflict elimination | High | Un-replayed commits cannot conflict; 98% of the surface vanishes by construction |
| Resolution error risk | High | 60 hand-resolutions ≈ 60 chances to regress; zero resolutions ≈ zero |
| Auditability | Medium | A cherry-pick list is reviewable line-by-line against the triage table |
| History linearity | Low | The deploy branch is already fork-local; preserving its merge topology has no consumer |

## 4. Alternatives Considered

1. **Plain merge** — rejected: 61 conflicts, 98% in files where we want
   upstream's version verbatim; resolving them by hand is pure risk with no
   benefit.
2. **Merge then revert the dead commits** — rejected by measurement: the
   reverts themselves conflict (`9cf46a2`, `8abbee2`, `1bd8cfd`); 56 conflicts
   remain.
3. **`git rebase --onto`** — rejected: rebase *replays* commits; the dead
   commits need *dropping*, and interactive-drop of 4-of-35 with heavy overlap
   reproduces the same conflict storm.
4. **Cherry-pick rebuild (chosen)** — replay only what survives, oldest first.

## 5. Consequences

**Positive:** the sync becomes mechanical; the dead i18n layer can never
half-survive; upstream's security-headers series merges clean over the result
(measured: zero new conflicts).

**Negative / accepted:** the MUST-SURVIVE list is a single point of failure —
mitigated three ways: (a) the triage table in `007-OD-CHNG` §2 was
re-verified commit-by-commit and its corrections are recorded inline (two
hashes were shuffled in the earlier plan — `a3af0c4` vs `e457135`, and
`55900ed` mis-bucketed); (b) later work appends its hashes to the map
(`011-PP-PLAN` §sync-survival makes this a step); (c) the deploy smoke
hard-fails if the gated front door regresses, so a dropped front-door commit
cannot deploy.

**Hard gates before execution (from `007-OD-CHNG` §5–6):** migration rehearsal
against a restored production snapshot (the `csrf_seed` rename can invalidate
sessions); deploy provability (#14) resolved first.

## 6. Review Triggers

- Upstream lands anything that changes the conflict surface materially →
  re-measure before executing (the map records its measurement SHAs).
- If the sync executes differently than specified here, the executor writes a
  superseding ADR — silent strategy drift is the failure mode this record
  exists to prevent.

## 7. Related

- `007-OD-CHNG-upstream-v2-sync-map.md` — the full measured analysis, commit
  triage, migration analysis, and sequencing. This ADR is its decision record.
- ADR-1 (`002-AT-ADEC`) — the posture that kept the conflict surface this
  small in the first place.
