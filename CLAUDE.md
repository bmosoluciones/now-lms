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
branch. Since the v2.0.0 sync landed (2026-07-29, PR #41) **everything blocks**:
lint (ruff + flake8 + `pylint --fail-under=9.5`), the PostgreSQL pytest suite,
and the Playwright browser-E2E job (`e2e/` — the member journey; see
`tests/TESTING.md`). A green PR now proves lint + tests + the browser journey.
The advisory era is over (bead `now-lms-dbq`).

## Task tracking — beads

This repo uses **bd (beads)**. Run `bd prime` for the full workflow, and prefer
`bd` over ad-hoc TODO lists.

Issues are prefixed `now-lms` (e.g. `now-lms-0oy`). The database is **local only**
— see below before pushing anything.

### The three-way circle: bead ↔ GitHub issue ↔ Plane issue (MANDATORY)

Every tracked unit of work exists in **three** places, and **each record carries
the other two IDs**. Not a chain — a circle. Given any one of the three you can
reach the other two without searching.

| Layer | Where | Must contain |
|---|---|---|
| **Bead** (source of truth) | local `bd`, prefix `now-lms` | `GitHub:` line + `Plane:` line |
| **GitHub issue** | `intent-solutions-io/now-lms` | `**Beads:**` line + `**Plane:**` line |
| **Plane issue** | project **LEARN** (`projects.intentsolutions.io`) | `Beads:` line + `GitHub:` line |

Current set (verified 2026-07-27):

| Bead | GitHub | Plane |
|---|---|---|
| `now-lms-bdv` | #22 | LEARN-1 |
| `now-lms-wy6` | #23 | LEARN-2 |
| `now-lms-maa` | #24 | LEARN-3 |
| `now-lms-xvr` | #27 | LEARN-4 |

**Creating work:** (1) `bd create` → (2) `gh issue create` with the `**Beads:**`
line → (3) Plane issue in LEARN with `Beads:` + `GitHub:` → (4)
`bd-sync link <bead> --gh intent-solutions-io/now-lms#N --plane LEARN-N` to plant
the cross-refs. `bd-sync link` **requires `--gh`** — `--plane` alone is rejected,
so create the GitHub issue even when the work feels Plane-shaped.

**Changing state:** always `bd-sync note` / `bd-sync close`, never raw `bd close`
— raw closes are mirror-blind and leave GitHub and Plane stale-open.

**Granularity:** one GitHub issue per logical cluster (an epic), never one per
task bead. Task beads live under their parent epic and get no issue of their own.

**Plane structure** follows the Kobiton pattern: **modules are dated milestones**
(M1…M4), each grouping its issues, and each module's description carries the
*reasoning* — why this approach over the alternative — not just a title. Modules
are off by default on API-created projects; enable with a REST
`PATCH {"module_view": true}` (the Plane MCP has no `update_project`).

### Beads sync route — CHOSEN and live (2026-07-28): `refs/dolt/data` on origin

`bd dolt remote list` → `origin  git+ssh://git@github.com/intent-solutions-io/now-lms.git`.
`bd dolt push` / `bd dolt pull` sync the Dolt history through the git remote's
`refs/dolt/data` (verify: `git ls-remote origin 'refs/dolt/*'`). World-readability
was the open question — accepted, because the three-way circle already mirrors
every bead note into public GitHub issues, so this route adds no new exposure.
Bead `now-lms-7e4` closed with the evidence.

The history below is retained because it explains why the remote was ever
missing, and what must never be repeated:

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

**Resolution (2026-07-28):** the `refs/dolt/data`-on-origin route was chosen
and executed (see the header of this section). The world-readable caveat was
weighed and accepted — bead content is already public by design via the
three-way circle's GitHub mirroring.

### Regenerating boilerplate

`bd init` **overwrites `AGENTS.md` and `CLAUDE.md`** in the working tree with
generic boilerplate, without warning. If these files suddenly look generic, that
is what happened — restore them from git rather than re-writing them.
