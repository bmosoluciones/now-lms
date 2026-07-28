# ADR-3 — Curriculum moves to a private repo; the fork stays public

## ADR Metadata

| Field | Value |
|---|---|
| **ADR Number** | ADR-3 |
| **Title** | Curriculum moves to a private repo; the fork stays public |
| **Status** | Accepted |
| **Date** | 2026-07-26 |
| **Author** | Jeremy Longshore (founder decision: "make private what should be private, but the framework to help the codeowner upstream should remain public") |
| **Backfilled** | 2026-07-28. The split shipped 2026-07-27 (seeder reads the private repo; commit `a3d323f`). |

## 1. Decision Summary

> **We will** move all teaching content (question banks and lesson prose) to
> the private `intent-solutions-io/intent-curriculum` repository, read at seed
> time via `CCA_CONTENT_DIR`, while this fork remains public, **in order to**
> protect assessment integrity and curriculum IP without closing the upstream
> contribution lane, **accepting that** deploys and DR rebuilds now require a
> second (private) checkout, and that the curriculum's history is no longer
> visible beside the platform's.

## 2. Context

The fork carried ~960 KB of curriculum — question banks *with answer keys*
beside the very courses that grade them, in a public repository. Publishing
graded answer keys next to the assessments they grade is an
assessment-integrity failure regardless of licensing: mock exams become
reproducible and completion signals lose meaning. The curriculum is also
Intent Solutions' own IP (source-reuse policy and attributions filed at
`004-BL-POLI` / `005-BL-LICN`) and is the paid substance of the program.

The naive fix — make the whole fork private — is structurally unavailable:

- `intent-solutions-io/now-lms` is a true GitHub fork, and GitHub forbids
  flipping a fork of a public repository to private.
- A private head repository cannot open PRs against a public upstream, which
  would end the upstream lane that ADR-1 makes load-bearing.

So the split is by **content**, never by repo visibility.

## 3. Decision Drivers

| Driver | Weight | Note |
|---|---|---|
| Assessment integrity | High | Public answer keys make graded practice meaningless |
| Upstream lane survival | High | The public fork is the only vehicle for upstream PRs |
| IP boundary | Medium | Teaching content is the product; platform fixes are contributions |
| Naming | Medium | `intent-curriculum`, not a vendor-named repo — the curriculum is Intent Solutions' own; CCA-F is only the first credential it preps for (founder call, 2026-07-27) |

## 4. Alternatives Considered

1. **Keep content public, add licensing** — considered first, superseded the
   same day: a license header does not stop answer-key circulation; the
   integrity problem is exposure, not permission.
2. **Make the fork private** — structurally impossible (GitHub fork rule) and
   strategically wrong (kills the upstream PR lane).
3. **Encrypt content in-repo** — rejected: key management theater; git history
   still grows; seed-time read of a private checkout is simpler and honest.
4. **Private `intent-curriculum` repo + seed-time read (chosen)** — the public
   repo keeps the platform fixes, `intent_learn` theme (already served
   publicly), the idempotent seeder, and governance; teaching content never
   returns here.

## 5. Consequences

**Positive:** the fork boundary becomes crisp and teachable — *platform bugs
go upstream; teaching content never does* (now stated in `CLAUDE.md`,
`AGENTS.md`, and the `000-INDEX.md` exclusion list). Public repo carries no
answer keys going forward.

**Negative / accepted:** seeding requires `CCA_CONTENT_DIR` pointed at a
private checkout (documented in `AGENTS.md`); prior history still contains
content commits — a history rewrite was measured feasible (0 forks, 2
touching commits) but is parked as the founder's call (bead `now-lms-xvr`),
explicitly out of scope here.

## 6. Review Triggers

- Any proposal to file teaching content in this repo → refuse, cite this ADR.
- The parked history-rewrite decision (bead `now-lms-xvr`) resolving either
  way does not change this ADR — it governs where content lives *now on*.

## 7. Related

- ADR-1 (`002-AT-ADEC`) — why the public upstream lane is worth protecting.
- `004-BL-POLI` / `005-BL-LICN` — source-reuse policy and attributions.
- `AGENTS.md` §fork-local seeder — the operational seeding procedure.
