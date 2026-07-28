# CLAUDE.md

Guidance for Claude Code and other AI agents working in this repository.

## Read `AGENTS.md` first

`AGENTS.md` is the fork brief and the single source of truth for this repo:
architecture, CLI groups, environment variables, the fresh-DB gotcha, the
difference between CI and `dev/test.sh`, lint thresholds, and the fork's
anti-patterns. Everything an agent needs in order to avoid breaking this
deployment is there. This file exists mainly so agents that look for `CLAUDE.md`
by name are pointed at it rather than starting from nothing.

## What this repository is

A fork of [`bmosoluciones/now-lms`](https://github.com/bmosoluciones/now-lms)
(Apache-2.0), deployed as Intent Solutions Learn at `learn.intentsolutions.io`.

The fork maintains a deliberate boundary, and it matters:

- **Platform layer** — the maintainer's LMS. Bugs here get contributed
  **upstream**, not carried locally. See `FORK.md` for the workflow and the
  record of what has been sent.
- **Ours** — the `intent_learn` theme, the front-door positioning, and the
  curriculum. These are Intent Solutions' own work and are **never** offered
  upstream.

Practical rule, restated from `AGENTS.md`: **do not put Intent Solutions
attribution or branding into shared `now_lms/**` source files.** `FORK.md` is the
fork's voice. Branding belongs in the theme layer
(`now_lms/templates/themes/intent_learn/`, `now_lms/static/themes/intent_learn/`).

## Branches

- `deploy/now-lms-fixed` — the deployed line. Base PRs here.
- `main` — tracks upstream (currently well behind; see `FORK.md`).

⚠️ PRs into `deploy/now-lms-fixed` are gated by `deploy-line-ci.yml` ("Deploy line
CI"), which exists precisely because upstream's `python.yml` never runs on this
branch. **Lint is blocking** there (ruff + flake8 + `pylint --fail-under=9.5`);
the PostgreSQL pytest run is **advisory** (`continue-on-error: true`) until the
v2.0.0 sync repairs the suite. So a green PR proves lint, not tests — run the
Postgres pytest path locally before trusting one. Note `dev/lint.sh` is itself
broken on this branch (it calls the missing `dev/ensure_headers.py`; upstream
#217 fixed that, and the fix arrives with the sync) — use `dev/test.sh`.

## Task tracking — beads

This repo uses **bd (beads)**. Run `bd prime` for the full workflow, and prefer
`bd` over ad-hoc TODO lists.

Issues are prefixed `now-lms` (e.g. `now-lms-0oy`). The database is **local only**
— see below before pushing anything.

### ⚠️ Do NOT run `bd dolt push` from this repository yet

The database is now clean, but no sync route has been chosen. Until one is,
there is nowhere correct to push.

**What was wrong (fixed 2026-07-26):**

1. `.beads/` here was a **clone of the Intent Solutions umbrella database** —
   1,205 issues under the `bd_000-projects` prefix, sharing the umbrella's
   `project_id`. now-lms work was indistinguishable from estate work. Cause:
   `bd init` walks *up* the directory tree, finds `~/000-projects/.beads`, and
   adopts it.
2. `sync.remote` pointed at a **different project's** DoltHub database
   (`jeremylongshore/Intent-eval-platform`). Any push would have filed now-lms
   beads against the Intent Eval Platform.
3. `bd init --reinit-local --discard-remote` — the documented cleanup — would
   have made the next push a **history-replacing force-push** against that IEP
   database. It was not run, and must never be run against a remote another
   project owns.

**What is true now:** a fresh database was minted *outside* `~/000-projects` (so
`bd init` could not adopt the umbrella), then installed here. Prefix is
`now-lms`; the IEP remote is removed (`bd dolt remote list` → "No remotes
configured"); the epic and its children were migrated with descriptions intact;
the old clone is preserved, not deleted.

**What is still needed:** pick a sync route — a dedicated DoltHub database, or
`refs/dolt/data` on the git remote. ⚠️ This repository is **public**, so option
two makes every bead world-readable. Nothing is pushed today:
`git ls-remote origin 'refs/dolt/*'` is empty.

Tracked as bead `now-lms-7e4`. Update this section once the route is chosen.

### Regenerating boilerplate

`bd init` **overwrites `AGENTS.md` and `CLAUDE.md`** in the working tree with
generic boilerplate, without warning. If these files suddenly look generic, that
is what happened — restore them from git rather than re-writing them.
