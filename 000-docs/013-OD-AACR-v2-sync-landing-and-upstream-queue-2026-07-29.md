# Landing the v2.0.0 sync, unblocking the cohort, and opening the upstream queue — 2026-07-29

**Read this with `012-OD-AACR` (the provisioning record) and `007-OD-CHNG` (the sync map).**
This is the record of the day the fork stopped being a snapshot and became a
maintained line: the upstream sync landed on production, a cohort-wide lockout
was found and fixed, the testing gates went from advisory to blocking, and eight
patches went upstream.

Current production commit at time of writing: **`daf35ce`** (post-history-rewrite).
Every SHA quoted below is from the rewritten history; anything older is void.

---

## 1. What shipped to production

| Change | Commit | Evidence |
|---|---|---|
| Upstream v2.0.0 sync | PR #41 → `6b2a7d6` | rehearsed against a post-provisioning prod snapshot; `SMOKE OK` |
| App-level HTTPS redirect disabled | `980093c` | v2.0.0's in-container Caddy rewrites `X-Forwarded-Proto`; app-level `FORCE_HTTPS` 301-looped the whole site |
| Redis for sessions + view cache | `deeb5b4` | `redis=healthy`, `Using Redis for session storage`, 19 keys |
| **Free-course access fix (U12)** | `c760c05` | the cohort lockout — see §2 |
| Per-user view-cache key (U10) | `c760c05` | keys were `auth`/`anon` only; with Redis live that would serve one member's cached page to another |
| Browser E2E layer | `a203d3c` | Playwright, 6 tests, real app boot |
| PG suite + E2E flipped to **blocking** | `dedbd01` | [run 30418204899](https://github.com/intent-solutions-io/now-lms/actions/runs/30418204899) |
| Public history rewritten | `daf35ce` | curriculum + PII purged from every commit; tip tree byte-identical |

## 2. The finding that mattered: every member was locked out

`verifica_estudiante_asignado_a_curso` required the enrollment's `Pago` row to
exist and be `completed`/`audit` — with no exception for free courses. Every
provisioned enrollment has `pago=NULL`, so **all 49 founding members were locked
out of both courses** from the moment they were provisioned.

It presented as a working page. The course outline rendered, every lesson link
was suppressed, and an *Enroll* button appeared instead — because the take
template sets `permitir_estudiante` from that helper, overriding anything the
route passes. Clicking Enroll added another enrollment row and still granted
nothing, so a member could stack duplicates while remaining locked out. Nothing
errored and nothing logged.

**It also explains the cohort's zero progress rows.** The 0 evaluation attempts
recorded before the sync were not members being slow to start; they could not
start.

Three things had to be true for this to stay invisible for a day:

1. 51 test files, all green — none walked *member logs in → opens course → opens lesson*.
2. `deploy-smoke.sh` checks status codes and served bytes. The broken page was a **200**.
3. The PostgreSQL test step was `continue-on-error`.

All three are now closed: the browser E2E layer walks that journey, and both the
PG suite and the E2E job block.

## 3. Testing posture — before and after

| Layer | Before 2026-07-29 | After |
|---|---|---|
| Lint (ruff/flake8/pylint 9.5) | blocking | blocking |
| PostgreSQL suite | **advisory** (`continue-on-error`) | **blocking** |
| Browser E2E | **did not exist** | **blocking** (Playwright, `e2e/`) |
| Test-audit grade | C+ (70/100) | B− (78/100) |

The flip paid for itself immediately: it surfaced that bare `pytest` had been
dying at `e2e/` collection since the E2E commit — invisible precisely because the
step was advisory — and that the last "flake" was deterministic (v2.0.0 added
`alembic.stamp()` to `initial_setup`; the test's mock app never mocked alembic).

Deliberate remaining gaps: coverage is measured, not gated; 96 smoke-only
(`is not None`) assertions await burn-down.

## 4. The upstream queue — eight patches out

Fork policy is unchanged: platform bugs go upstream, not into the fork. As of
today the fork has **six merged upstream PRs** and **seven open**.

| PR | What | Note |
|---|---|---|
| #226 (was #223) | mail TLS/SSL boolean coercion | **merged** — maintainer cherry-picked our commit *and* our 63-line test file |
| #227 | free-course access with no payment record | the cohort lockout, generalised |
| #228 | country field rendered as a dead dropdown | `StringField` styled `form-select` |
| #229 | free enrollment demanding a billing address | conditional `requires_billing` |
| #231 | form labels lazy + **extraction gap** | see below |
| #232 | dead ionicons CDN loads, 9 themes | 18 tags, 0 `<ion-icon>` usages |
| #233 | duplicate enrollment rows | mirrors the paypal upsert |
| #234 | unique constraint + dedup migration | verified on real PostgreSQL |
| issue #230 | should `/contact` honour `enable_contact`? | **filed as a question, not a PR** |

Two judgment calls worth preserving:

**#231 turned up a second bug.** Converting labels to `_l()` would have made them
*untranslatable*, because `dev/lang.sh` never passed `-k _l` and `_l` is not a
Babel default keyword. Measured: a label existing only as `_l()` extracts to
**zero msgids** with upstream's own command. Upstream's existing 77 `_l()` strings
are already absent from the catalogue and cannot be translated by anyone. Both
halves are in that PR.

**U1 became a question rather than a PR.** Adding the `enable_contact` 404 reddens
4 of upstream's 11 contact tests, and `is_contact_enabled()`'s docstring says
"enabled in navigation" — so nav-only gating may be deliberate. Sending a
behaviour change that breaks a maintainer's suite is how you lose standing.

**Still parked:** U7–U10, the access-control set, until `GHSA-3w27-xggq-j59p`
moves out of triage. No public PRs on those.

## 5. Verification standard used for every upstream patch

Each PR is single-purpose (the lesson of #223, which was closed in favour of a
cherry-pick), and each one is **mutation-checked**: revert the fix, prove the new
test fails, prove the boundary tests stay green. Two cases where that caught real
problems:

- The lazy-label test walks every form class rather than sampling, and **caught
  six labels a mechanical pass had missed** (a module-level constant reused by six forms).
- The `#234` migration was verified against **real PostgreSQL**, not SQLite —
  SQLite is too permissive about constraints and FKs for a green run to mean
  anything. That run proved the FK repoint (a naive dedup would violate
  `remote_enrollment_requests`), idempotency, and downgrade.

**Standing rule from this:** any schema or constraint work is verified on
PostgreSQL. SQLite passing proves nothing about it. That permissiveness is what
produced the ~34 pre-sync test failures in the first place.

## 6. Data repair on production

The rollout audit found `matt@intentsolutions.io` holding three `CCA-F`
enrollments — the app-level duplicate bug above, not a provisioning fault.
Removed 2 surplus enrollment rows, 2 orphan `pago` rows and 20 surplus
`curso_recurso_avance` rows, with the deleted rows dumped to CSV first. Verified
49/49 per course, zero duplicate `(usuario, curso)` pairs, zero orphan payments.

## 7. Estate tooling moved into this repo

By owner order the LMS provisioning and digest tooling now lives here at
`ops/lms/`, with the audit findings fixed: reactivation is opt-in and reversible
(prior hash and role captured), rollback covers all three user paths, the digest
covers all 49 members rather than 44 (`tipo='student'` had silently excluded the
lead admins), and its read-only posture is enforced with
`PGOPTIONS=-c default_transaction_read_only=on` rather than merely named.

## 8. Public-history rewrite

Owner-executed `git filter-repo` purged `content/cca/` (curriculum plus 696
answer keys and rationales) from every commit, and replaced the pre-redaction
revision of `012-OD-AACR` with its redacted text. The deploy tip's tree came out
**byte-identical** — history only, no working content changed — and production
was rebuilt and re-verified (`SMOKE OK` at `daf35ce`).

Curriculum now lives only in the private `intent-curriculum` repo; the seeder
reads it via `CCA_CONTENT_DIR` and the platform serves from PostgreSQL, so
removing it from this repo changes nothing for members.

**Residual:** GitHub keeps unreachable commits fetchable by exact SHA, and public
forks share the parent's object store. A Support purge request is drafted and
pending the owner's submission.

## 9. What is still open

| Item | Where |
|---|---|
| Theme reverts after sign-in — **no root cause yet** | issue #38, bead `now-lms-mf2` |
| Fork still carries the country/billing/duplicate symptoms until the next sync | #39, #40 |
| No forced password change exists for the credentials emailed to members | bead `now-lms-fzf` |
| U7–U10 disclosure | bead `now-lms-m9p`, GHSA in triage |
| Coverage ratchet + 96 smoke-only assertions | `tests/TESTING.md` |
| GitHub Support purge for cached SHAs and fork objects | owner action |
| `IS-START` curriculum is seeded but thin — the onboarding path is not authored | new work |

- Jeremy Longshore
intentsolutions.io
