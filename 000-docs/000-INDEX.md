# 000-docs Index — Intent Solutions fork of NOW-LMS

Filed per the Document Filing System v4.4 (`/doc-filing`): flat `000-docs/`,
`NNN-CC-ABCD-description.ext`, one global chronological sequence. Next number =
recursive scan of this tree, highest `NNN` + 1. Per §3.1 this tree stays
**flat** — nesting into `NNN-CC-cluster-name/` folders applies only past ~50
files with an 8+ doc cluster, and we are far under both thresholds.

> **`NNN` is append-only from 2026-07-28 onward.** The 2026-07-28 backfill
> renumbered the tree **once**, chronologically, because every file then in it
> had been filed the same night — the numbers carried no historical meaning to
> preserve, and the backfilled PRD + ADRs record decisions made *before* the
> docs that already sat at low numbers. That was a one-time correction, not a
> precedent: new documents take the next free number, never a backdated slot.

## Documents

| File | What it is |
|---|---|
| [001-PP-PROD-now-lms-fork-prd.md](001-PP-PROD-now-lms-fork-prd.md) | Baseline PRD (backfilled 2026-07-28): what Intent Solutions Learn is — vision, users, shipped scope, non-functional requirements, standing risks, release strategy. The document future work diffs against. |
| [002-AT-ADEC-adopt-and-mature-upstream.md](002-AT-ADEC-adopt-and-mature-upstream.md) | ADR-1 (2026-07-21, Accepted): adopt NOW-LMS as-is and mature it upstream — no private forks of behavior. The governing rule everything else follows. |
| [003-DR-REFF-live-auth-flow.md](003-DR-REFF-live-auth-flow.md) | Verified login / roles / admin flow of the live deployment (verified 2026-07-21 against the running container). The getting-started lessons were written from it. |
| [004-BL-POLI-cca-source-reuse.md](004-BL-POLI-cca-source-reuse.md) | CCA-F prep source map & reuse policy: license-tiered reuse rules (NC/unlicensed = link only), question banks are Intent Solutions IP, Rick Hightower reuse grant context. |
| [005-BL-LICN-cca-attributions.md](005-BL-LICN-cca-attributions.md) | Attribution record for the CCA-F curriculum: MIT-licensed projects that informed structure, credited per license; lesson prose originally authored by Intent Solutions. |
| [006-AT-ADEC-rebuild-on-v2-sync.md](006-AT-ADEC-rebuild-on-v2-sync.md) | ADR-2 (2026-07-26, Accepted): execute the upstream v2.0.0 sync by cherry-picking the measured MUST-SURVIVE set rather than merging — 98% of conflicts eliminated by construction. |
| [007-OD-CHNG-upstream-v2-sync-map.md](007-OD-CHNG-upstream-v2-sync-map.md) | Upstream v2.0.0 sync migration map (2026-07-26): commit triage (MUST-SURVIVE set), corrections, DB migration analysis, sequencing, open items. Read before any upstream sync. ADR-2 is its decision record. |
| [008-AT-ADEC-curriculum-private-fork-public.md](008-AT-ADEC-curriculum-private-fork-public.md) | ADR-3 (2026-07-26, Accepted): teaching content moves to the private intent-curriculum repo; the fork stays public so the upstream lane survives. Split by content, never by repo visibility. |
| [009-AT-ADEC-native-contact-message-storage.md](009-AT-ADEC-native-contact-message-storage.md) | ADR-4 (2026-07-27, Accepted): access requests store in the native ContactMessage table with an `[ACCESS]` subject discriminator — no bespoke model, no migration, native admin surface. |
| [010-AT-ADEC-gate-courses-doctrine-teaser.md](010-AT-ADEC-gate-courses-doctrine-teaser.md) | ADR-5 (2026-07-27, Accepted): gate all courses/resources/programs; `/course/explore` becomes a doctrine-voice practice-tracks teaser; anonymous gated-course hits 302 to the intake. |
| [011-PP-PLAN-waiting-list-gated-surfaces.md](011-PP-PLAN-waiting-list-gated-surfaces.md) | Waiting-list + gated practice surfaces execution plan (locked 2026-07-27): /request-access intake, practice-tracks teaser, contact fix, course gating, security ship-gate, upstream PR queue U1–U10, founder-locked copy and decisions. |
| [012-OD-AACR-founding-members-provisioned-on-prod-2026-07-28.md](012-OD-AACR-founding-members-provisioned-on-prod-2026-07-28.md) | After-action record (2026-07-28): the founding-member cohort provisioned on production from the intent-os estate session, plus the standing constraints for this repo's sessions. **Redacted** for the public repo — the unredacted evidence lives in the private intent-os record. |
| [013-OD-AACR-v2-sync-landing-and-upstream-queue-2026-07-29.md](013-OD-AACR-v2-sync-landing-and-upstream-queue-2026-07-29.md) | After-action record (2026-07-29): the v2.0.0 sync landing on production, the cohort-wide access lockout and its fix, testing gates going from advisory to blocking, the eight upstream patches, the public-history rewrite, and what is still open. Read with 012 and 007. |
| [014-AT-ADEC-prior-credential-tracking.md](014-AT-ADEC-prior-credential-tracking.md) | ADR-7 (2026-07-31, Proposed): learner-reported prior credentials get a dedicated `prior_credentials` table with a required issuer verification URL and an optional privately-served image — a deliberate ADR-1 deviation, carried fork-local with an upstream path. |
| [015-AT-ADEC-short-answer-evaluations.md](015-AT-ADEC-short-answer-evaluations.md) | ADR-6 (2026-08-02, Accepted): add a `short_answer` question type with written-response storage, a per-question rubric, and an instructor grading queue — authored upstream per ADR-1, carried on the deploy line only while the upstream PR is open. Automated grading explicitly out of scope. |
| [016-AT-ADEC-member-dashboard.md](016-AT-ADEC-member-dashboard.md) | ADR-9 (2026-08-08, Accepted 2026-08-10): members get a fork-local dashboard at `/dashboard` instead of the upstream student panel, which cannot be themed and showed a fabricated counter while hiding the member's own stored progress. Instructors and moderators keep the upstream panel. |
| [017-AT-ADEC-community-hub-owns-content.md](017-AT-ADEC-community-hub-owns-content.md) | ADR-10 (2026-08-09, Accepted): the Community Hub owns its posts and replies outright, superseding ADR-8. The container course ADR-8 needed brought a silent data-loss path (`foro_mensaje.curso_id` cascades) and saved no table, since the sidecar simply becomes the post table. |
| [018-AT-ADEC-community-hub-storage.md](018-AT-ADEC-community-hub-storage.md) | ADR-8 (2026-08-08, Accepted, superseded by ADR-10): the Community Hub stores post bodies and replies in the native `foro_mensaje` table and adds three sidecar tables for metadata, likes and the moderation trail. Strikes the no-new-table clause of the 2026-08-02 `/feed` recommendation, which predates the likes requirement; keeps the rest of it. `ForoMensaje` is not modified. |

## Architecture Decisions (the ADR log)

One immutable file per decision (Nygard pattern): an accepted ADR is never
edited — it is superseded by a new one and the old stays readable. Two number
sequences coexist and mean different things: `NNN` is the document's position
in the project's global timeline; `ADR-N` (in each file's metadata table) is
the decision number, contiguous within the ADR set. This section is the log's
table of contents, in decision order.

| ADR | Doc | Decided | Status | Decision |
|---|---|---|---|---|
| ADR-1 | [002](002-AT-ADEC-adopt-and-mature-upstream.md) | 2026-07-21 | Accepted | Adopt NOW-LMS as-is; mature it upstream; no private forks of behavior |
| ADR-2 | [006](006-AT-ADEC-rebuild-on-v2-sync.md) | 2026-07-26 | Accepted | Rebuild on upstream v2.0.0 by cherry-picking the must-survive set, not merging |
| ADR-3 | [008](008-AT-ADEC-curriculum-private-fork-public.md) | 2026-07-26 | Accepted | Curriculum moves to a private repo; the fork stays public |
| ADR-4 | [009](009-AT-ADEC-native-contact-message-storage.md) | 2026-07-27 | Accepted | Store access requests in the native ContactMessage table, not a bespoke model |
| ADR-5 | [010](010-AT-ADEC-gate-courses-doctrine-teaser.md) | 2026-07-27 | Accepted | Gate the courses; the public catalog becomes a doctrine teaser |
| ADR-6 | [015](015-AT-ADEC-short-answer-evaluations.md) | 2026-08-02 | Accepted | Add a `short_answer` question type with instructor grading, authored upstream |
| ADR-7 | [014](014-AT-ADEC-prior-credential-tracking.md) | 2026-07-31 | Proposed | Dedicated `prior_credentials` table; verification URL required, image optional and privately served |
| ADR-8 | [018](018-AT-ADEC-community-hub-storage.md) | 2026-08-08 | **Superseded by ADR-10** | Community Hub on native `foro_mensaje` bodies and replies, plus three sidecar tables for metadata, likes and the moderation trail |
| ADR-9 | [016](016-AT-ADEC-member-dashboard.md) | 2026-08-10 | Accepted | Fork-local member dashboard at `/dashboard`; the upstream student panel stays for instructors and moderators |
| ADR-10 | [017](017-AT-ADEC-community-hub-owns-content.md) | 2026-08-09 | Accepted | The Community Hub owns its posts and replies; no container course. Supersedes ADR-8 |

## Renames & moves (references in old commit messages resolve here)

| Old location | Current name | When / why |
|---|---|---|
| `001-OD-PLAN-upstream-v2-sync-migration-map.md` | `001-OD-CHNG-upstream-v2-sync-map.md` | 2026-07-27 — doc-filing v4.4 compliance (`PLAN` is a PP type; a migration map is OD change management; 4-word description cap). |
| `002-OD-PLAN-waiting-list-and-gated-practice-surfaces.md` | `002-PP-PLAN-waiting-list-gated-surfaces.md` | 2026-07-27 — same pass (an execution plan is PP-PLAN; 4-word cap). |
| `content/cca/AUTH-FLOW.md` | `003-DR-REFF-live-auth-flow.md` | 2026-07-27 — fork-local document filed; nothing in code consumed it. |
| `content/cca/SOURCES.md` | `004-BL-POLI-cca-source-reuse.md` | 2026-07-27 — same pass. |
| `content/cca/ATTRIBUTIONS.md` | `005-BL-LICN-cca-attributions.md` | 2026-07-27 — same pass; internal cross-reference updated. |
| `001-OD-CHNG-upstream-v2-sync-map.md` | `007-OD-CHNG-upstream-v2-sync-map.md` | 2026-07-28 — one-time chronological backfill (see the append-only note above): the sync map is a 07-26 document and slots after the 07-21 block and the backfilled ADRs it postdates. `FORK.md` citations updated in the same commit. |
| `002-PP-PLAN-waiting-list-gated-surfaces.md` | `011-PP-PLAN-waiting-list-gated-surfaces.md` | 2026-07-28 — same backfill: the newest document (07-27) takes the highest slot. `FORK.md` citations updated in the same commit. |

## md files that deliberately stay OUTSIDE this tree (the fork boundary)

Filing organizes *project documents*. These classes are excluded on purpose —
do not "fix" them into 000-docs:

- **Root governance files** — `README.md`, `CLAUDE.md`, `AGENTS.md`, `FORK.md`,
  `CHANGELOG.md`. The standard's own scan excludes this class; they work by
  being discoverable at their conventional names/paths.
- **Upstream-owned material** — everything under `docs/` (upstream's mkdocs
  site source), `replit.md`, `.github/copilot-instructions.md`,
  `tests/README.md`, and the 8 upstream theme `README.md` files. Moving any of
  it is permanent sync-conflict surface against `bmosoluciones/now-lms`.
- **Curriculum** — teaching content (question banks + lesson prose) is **not in
  this repository**. It lives in the private `intent-solutions-io/intent-curriculum`
  repo and is read at seed time via `CCA_CONTENT_DIR`
  (see `scripts/seed_cca_courses.py`). It is program input, not documentation, and
  it never returns here. `now_lms/templates/themes/intent_learn/README.md`
  documents the theme package in place.
- **Tool artifacts** — `.beads/README.md`, `.pytest_cache/README.md`
  (generated; the latter is gitignored), `.audit-harness/*.md` (vendored
  harness).
- **Testing traceability** — `tests/{TESTING,RTM,PERSONAS,JOURNEYS}.md` and
  the transient `TEST_AUDIT.md` are owned by the testing SOP
  (`/audit-tests` / `/implement-tests`) and live beside the tests they
  govern; filing them here would break the tooling's contract.

## Quick reference

Category codes (CC) and document types (ABCD) come from the canonical standard —
`~/.claude/skills/doc-filing/references/000-DR-STND-document-filing-system.md`.
Used here: `PP-PROD` (PRD), `PP-PLAN` (plans), `AT-ADEC` (architecture
decision records), `OD-CHNG` (ops change management), `OD-AACR` (after-action
records), `DR-REFF` (reference docs), `BL-POLI` (policy), `BL-LICN`
(licensing/attribution).
