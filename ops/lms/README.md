# ops/lms — member provisioning + progress digest (now-lms-owned)

These tools were authored in intent-os for the 2026-07-28 founding-members
rollout and **moved here 2026-07-29 by owner order**: this repo owns the LMS
estate tooling. The intent-os copies are historical; change these.

| Tool | Purpose |
|---|---|
| `provision-founding-members.py` | Create/enroll members on prod through the app's own ORM, over SSH stdin. Dry-run by default; `--live` writes; `--rollback FILE` reverses a run. |
| `lms-progress-digest.sh` | Weekly cohort digest (Mon 07:30 CT cron on the dev box) mailed via the estate MXroute sender. Read-only against prod, server-enforced. |

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
