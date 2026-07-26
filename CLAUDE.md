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

⚠️ PRs into `deploy/now-lms-fixed` currently run **no test job** — `python.yml`
triggers only on `main`/`development`. Run `dev/test.sh` locally before trusting
a green PR.

## Task tracking — beads

This repo uses **bd (beads)**. Run `bd prime` for the full workflow, and prefer
`bd` over ad-hoc TODO lists.

### ⚠️ Do NOT run `bd dolt push` from this repository yet

The beads database here is **not** a clean project database:

1. It is a **clone of the Intent Solutions umbrella database** — 1,207 issues
   under the `bd_000-projects` prefix, sharing the umbrella's `project_id`. There
   are no `now-lms`-prefixed issues, so now-lms work is indistinguishable from
   estate-wide work.
2. `sync.remote` in `.beads/config.yaml` points at a **different project's**
   DoltHub database (`jeremylongshore/Intent-eval-platform`). A push from here
   would file now-lms beads against the Intent Eval Platform.
3. **This repository is public.** Beads sync can also travel as `refs/dolt/data`
   on the git remote, which would publish estate-wide issues.

`.beads/` is git-ignored in the tracked `.gitignore` for the same reason — that
stops the *file* from being committed, but it does **not** stop a Dolt push.

Nothing has been pushed yet: there are no `refs/dolt/*` refs on `origin` and none
locally. Keep it that way until the sync design is settled, then update this
section. Ask before wiring up beads sync.
