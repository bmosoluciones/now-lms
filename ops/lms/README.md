# ops/lms — member provisioning + progress digest (now-lms-owned)

These tools were authored in intent-os for the 2026-07-28 founding-members
rollout and **moved here 2026-07-29 by owner order**: this repo owns the LMS
estate tooling. The intent-os copies are historical; change these.

| Tool | Purpose |
|---|---|
| `provision-founding-members.py` | Create/enroll members on prod through the app's own ORM, over SSH stdin. Dry-run by default; `--live` writes; `--rollback FILE` reverses a run. |
| `lms-progress-digest.sh` | Weekly cohort digest (Mon 07:30 CT cron on the dev box) mailed via the estate MXroute sender. Read-only against prod, server-enforced. Carries the member table, the most-missed-questions ranking, certificates, and the nudge list. |

## Honest capability claims (corrected 2026-07-29 after audit)

The original intent-os README overstated three things. Current truth:

1. **Idempotency**: re-runs are safe for *active* users (skip) and, by default,
   for *inactive* users (skip — reactivation now requires `--allow-reactivate`).
   With that flag, a reactivation resets the password and is captured for
   reversal (`prior_hash_b64`/`prior_tipo` in the result CSV).
2. **Rollback coverage**: rollback removes created users entirely, restores
   reactivated users (prior hash + role + deactivation + un-enrollment of this
   run's courses), and un-enrolls already-active users from courses this run
   added. It still refuses any user with a login or completed progress. Runs
   recorded by the OLD CSV format (the 2026-07-28 run) can only be rolled back
   with the old semantics: created users deleted, reactivated users
   re-deactivated *without* credential restore (the prior hash was never
   captured — it is unrecoverable).
3. **Digest coverage**: the digest now covers **every active member including
   admins** (the old `tipo='student'` filter dropped the lead admins from
   their own cohort report). System accounts excluded via `LMS_DIGEST_EXCLUDE`
   (default `intentadmin`).

## Most-missed questions (added 2026-07-31) — what it does and does not claim

The digest ranks questions by the share of submitted attempts that got them
wrong, so lesson and video priorities can be set from measured confusion rather
than guesswork. What the number means, precisely:

- **Grading is replicated from the app**, not re-invented:
  `now_lms/vistas/evaluations.py::_answer_is_correct`. A `boolean` question is
  correct when exactly one option was selected and that option is correct. A
  `multiple` question is correct only when the selected set **exactly equals**
  the correct set — partial answers and supersets both score zero, because the
  app gives no partial credit. Null, empty, and non-array payloads are misses.
  **If that function changes, this query is wrong until it is changed to match.**
- **The denominator is submitted attempts of the evaluation, not answer rows.**
  A question a learner skipped never gets an `answer` row at all, but
  `calculate_score` divides by the question count, so a skip is a miss for the
  learner's score and is a miss here. The `Answered/Attempts` column exposes the
  difference: answered well below attempts means the question is being skipped,
  which is a different problem from being failed.
- **In-progress attempts are excluded** (`submitted_at IS NULL`), otherwise an
  abandoned attempt with no answers would push every question toward 100%.
- **Only each member's FIRST submitted attempt at an evaluation counts**
  (`DISTINCT ON (user_id, evaluation_id)`, ordered by `submitted_at` then `id`
  so ties resolve deterministically). Attempts are unlimited on the practice
  exams, so counting every one lets a single member who retakes an exam five
  times contribute five times the weight, and a question people deliberately
  drill looks harder than one they meet once and fail. First-attempt share is
  also the number that answers the question the digest exists to answer: what
  did people not know *before* the material taught it to them. The consequence
  worth naming: a question that is missed first time and mastered on the retake
  still ranks high here, which is correct for prioritising teaching and wrong
  for measuring mastery. This table is not a mastery report.
- **System accounts are excluded** via the same `LMS_DIGEST_EXCLUDE` list the
  member table uses, so staff test runs do not move the cohort's numbers.
- **The table is capped at 25 rows and says so**, printing "Top 25 of N" with
  the full count, so a truncated list can never read as a complete one.
- It ranks *what* is missed. It does not explain *why*, and it cannot see a
  question nobody has reached yet — a question on an evaluation with zero
  submitted attempts is absent from the table rather than shown at 0%.

Verified 2026-07-31 against an embedded PostgreSQL fixture, not against prod:
single-correct and multi-correct questions, partial and superset answers, a
skipped question, empty/non-JSON/empty-array payloads, an unsubmitted attempt,
an excluded system account, and an evaluation with no attempts. Removing either
the submitted filter or the exclusion list changes every row, so both guards
were confirmed load-bearing rather than decorative. The one thing a local
fixture cannot prove is that prod's column names match the models; confirm with

```sql
SELECT table_name, column_name FROM information_schema.columns
WHERE table_name IN ('answer','question','question_option','evaluation','evaluation_attempt','curso_seccion')
ORDER BY table_name, column_name;
```

## Standing rules

- The result CSV contains plaintext passwords and prior password hashes:
  mode 600, outside any repo, never mailed, never committed. It is also the
  only rollback key for its run — back it up somewhere durable.
- Account/enrollment writes on prod go through this tool only. Coordinate via
  `~/000-projects/CROSS-SESSION-LOG.md` before running `--live`.
- The digest's read-only posture is enforced with
  `PGOPTIONS='-c default_transaction_read_only=on'` — a write added to it by
  mistake will fail loudly instead of mutating prod.
- Progress note: seeded `curso_recurso_avance` rows are placeholders
  (`completado=false`). `curso_usuario_avance` (what the digest's progress
  table reads) is created lazily by the app on a member's first real progress
  event — an empty progress section early on is expected, not a bug.
