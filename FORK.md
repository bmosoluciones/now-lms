# Intent Solutions fork of NOW-LMS

This repository is [Intent Solutions](https://intentsolutions.io)' fork of
[`bmosoluciones/now-lms`](https://github.com/bmosoluciones/now-lms) (Apache-2.0). We run NOW-LMS
as the learning platform for the Claude Partner Network cohort.

## Posture: use it as-is, mature it **upstream** — no private forks of behavior

Our governing rule is **we do not build custom.** We use NOW-LMS's native features, and where
something is missing or broken we fix it **upstream** as a real contribution — maintained by the
project, benefiting everyone — rather than carrying a private patch. This keeps our fork a thin
tracking mirror of upstream, not a divergent product.

Concretely:

- **Branding is data, not code.** User-facing name/logo/colors come from NOW-LMS's native
  theme/config layer (`NOW_LMS_THEMES_DIR`). We do **not** rename the `now_lms` package or edit
  core views for branding — renaming is a permanent merge-conflict tax on every upstream sync.
- **Fixes and features go upstream.** Bug fixes and missing capabilities are PR'd to
  `bmosoluciones/now-lms`. We only keep in this fork what is genuinely fork-local (deploy manifest,
  this file, CI wiring) and never touches core source.
- **`main` tracks `upstream/main`.** We keep our `main` in sync with upstream and branch fixes off
  it.

## Branches

- **`main`** — thin tracking mirror of `upstream/main`, plus fork-local governance (this file,
  `.github/CODEOWNERS`). Fixes destined for upstream branch off here.
- **`deploy/now-lms-fixed`** — the branch our platform deploys from. It carries `main` plus the
  fork-local changes listed under "Fork-local changes carried on `deploy`" below. Each of those has
  an upstream path and retires from the fork once upstream accepts it.

## Working the fork

```bash
# one-time
git clone git@github.com:intent-solutions-io/now-lms.git
cd now-lms
git remote add upstream https://github.com/bmosoluciones/now-lms.git

# keep main current with upstream
git fetch upstream
git checkout main && git merge --ff-only upstream/main && git push origin main

# author a fix (destined for upstream)
git checkout -b fix/<short-description> upstream/main
# ...change only what's needed, match upstream conventions (conventional commits, dev/lint.sh, dev/test.sh)...
git commit -s -m "fix(scope): imperative subject"
git push -u origin fix/<short-description>
gh pr create --repo bmosoluciones/now-lms --base main \
  --head intent-solutions-io:fix/<short-description>
```

Include in every upstream PR: **what** changed, **why**, and **how it was verified** (link the
proving artifact — a test run or a reproduced-then-fixed behavior), so a maintainer can accept it
without re-deriving it.

## Contributing conventions (inherited from upstream)

Follow `docs/CONTRIBUTING.md`: conventional-commit messages (`type(scope): subject`),
`python dev/lint.sh` clean, and `python dev/test.sh` green (PostgreSQL/MySQL/SQLite paths). Sign
commits off (`git commit -s`). Translations do **not** go in as raw `.po` PRs — upstream intakes
them through the [Crowdin project](https://crowdin.com/project/now-lms) (source Spanish). The
`CHANGELOG.md` at the repo root is **upstream's** — do not add fork entries to it (merge tax); the
fork's own change record is this file.

## Upstream contributions

**Merged (6).** `#179` fresh-PostgreSQL bootstrap · `#214` `ProxyFix` used an undefined
`app` · `#215` `NOW_LMS_TRUSTED_PROXY` · `#216` assets populate under a custom data dir ·
`#217` dangling `ensure_headers.py` call in `dev/lint.sh` · **`#226`** mail
`MAIL_USE_TLS`/`MAIL_USE_SSL` boolean coercion — the maintainer closed our `#223` and
cherry-picked the commit *plus* our 63-line test file into his own PR.

**Open (7), all sent 2026-07-29.** Each is single-purpose and mutation-checked — the
lesson of `#223`, which was closed in favour of a cherry-pick because it bundled more
than the mail fix.

| PR | What |
|---|---|
| [#227](https://github.com/bmosoluciones/now-lms/pull/227) | free-course access denied when the enrollment carries no payment record — the defect that locked out our whole cohort |
| [#228](https://github.com/bmosoluciones/now-lms/pull/228) | `PagoForm.pais` is a `StringField` rendered with `form-select`, so the country field reads as a broken dropdown |
| [#229](https://github.com/bmosoluciones/now-lms/pull/229) | a free course demands a full billing address before it will enroll anyone |
| [#231](https://github.com/bmosoluciones/now-lms/pull/231) | 129 form labels resolve at import time; **and** `dev/lang.sh` never declared `-k _l`, so lazily-labelled strings are absent from the catalogue entirely |
| [#232](https://github.com/bmosoluciones/now-lms/pull/232) | nine themes load ionicons from a CDN on every page; no template uses `<ion-icon>` |
| [#233](https://github.com/bmosoluciones/now-lms/pull/233) | re-submitting the enrollment form adds a second enrollment row (the paid path already upserts) |
| [#234](https://github.com/bmosoluciones/now-lms/pull/234) | unique constraint on `(usuario, curso)` plus a dedup migration, verified on real PostgreSQL |

**Filed as a question, not a PR** —
[#230](https://github.com/bmosoluciones/now-lms/issues/230): should `/contact` honour
`enable_contact`, or is the flag navigation-only by design? Adding the 404 reddens 4 of
his 11 contact tests and `is_contact_enabled()`'s docstring says "in navigation", so the
current behaviour may be deliberate. The patch is ready and offered pending his call.

**Also open, older.**
[`#181`](https://github.com/bmosoluciones/now-lms/issues/181) — offer of a complete
English catalog routed through the maintainer's Crowdin project rather than a raw `.po`
PR.

**Held deliberately.** The four access-control findings (U7–U10) stay private until
`GHSA-3w27-xggq-j59p` moves out of triage. No public PRs on those, and no write-ups.

**Standing rule learned here:** anything touching schema or constraints is verified
against **PostgreSQL**, not SQLite. SQLite's permissiveness is what let ~34 strictness
bugs hide in the suite before the v2.0.0 sync.

## Fork-local changes carried on `deploy/now-lms-fixed`

Per the posture above we avoid private patches, but `deploy` temporarily carries the changes below
so the cohort can use the platform today. Each has an upstream path and its retirement condition is
noted — when upstream accepts it, we drop the fork-local copy and let `main` carry it.

| Change | Layer | Upstream path / retire when |
|---|---|---|
| `intent_learn` theme (home, course-list, **course-detail**, auth pages — Charcoal-Slate branding) | Native theme layer (`now_lms/templates/themes/intent_learn/`), **no core edit** | Permitted permanently — branding is data, not a core patch. |
| English internationalization: `_()`/`_l()` wrapping of ~62 templates + 83 WTForms labels + ~190 view messages, and the completed `en` catalog | **Core source** (the one intentional core patch) | Offered upstream via **#181** (Crowdin + wrapping PR-if-wanted). Retire from the fork once upstream accepts. |
| Healthcheck fix — send `X-Forwarded-Proto: https` so `NOW_LMS_FORCE_HTTPS` doesn't 301-hang the probe | Deploy manifest (`docker-compose.yml`) | Fork-local deploy wiring; not core. Stays. |
| `/request-access` intake — new blueprint (`now_lms/vistas/request_access.py`) storing to the native `contact_messages` table, plus themed page (`themes/intent_learn/pages/request_access.html`) | Fork blueprint + theme layer; zero imports from `static_pages.py` so it survives the v2.0.0 split | Positioning/page is fork-permanent (like the theme). The ~40-line Slack ping inside it retires when a generic `CONTACT_WEBHOOK_URL` feature is accepted upstream. |
| Practice-tracks teaser replacing the anonymous course catalog (`overrides/course_list.j2`) | Native theme layer, no core edit | Permitted permanently — branding is data. |
| `contact` route honors `enable_contact` (404 while disabled) | Core edit in `vistas/static_pages.py` (file dies at v2.0.0 — upstream split it into `contact.py`, which carries the same bug) | Offered upstream (U1 in `000-docs/011-PP-PLAN-waiting-list-gated-surfaces.md`); at the sync, re-apply against upstream `contact.py` unless merged. |
| Anonymous GET on a gated course 302s to `/request-access` instead of a bare 403 (`vistas/courses/base.py`) | Core edit, 4 lines | Fork conversion path; re-apply at sync. Not offered upstream (product decision, not a bug). |
| Admin contact list accepts a `?q=` subject filter (`vistas/static_pages.py`) | Core edit, 3 lines | Candidate for upstream once the contact-webhook PR lands; until then re-apply at sync. |
| Self-registration is **closed at the ingress layer** — in host-level configuration on the production VPS, *not* in this repo. `/user/login` stays reachable for members; anonymous signup routes to the `/request-access` intake instead. | Host config (zero repo files) | **Permanent while the platform is invite-only.** ⚠️ Because it lives outside the repo, nothing here re-applies it: regenerating host ingress config without consulting the private intent-os ops record silently reopens self-signup. Any session touching host ingress must read that record first. |
| Testing enforcement layer — vendored `@intentsolutions/audit-harness` (`.audit-harness/` + `scripts/audit-harness` + `.harness-hash`), L1 pre-commit lint gate (`scripts/pre-commit-lint.sh` chained into the beads hook by `scripts/install-git-hooks.sh`), acceptance specs (`features/*.feature`), traceability (`tests/{TESTING,RTM,PERSONAS,JOURNEYS}.md`), coverage visibility in `deploy-line-ci.yml` | Fork tooling + fork CI, **zero core edits** | **Permanent fork-local, deliberately.** This is Intent Solutions' engineering standard, not a platform bug — it has NO upstream path. At the v2.0.0 sync these files carry over on purpose; do not treat them as drift. |

## Fork changelog

Fork-relevant, most recent first. (Upstream feature history lives in the root `CHANGELOG.md`; this
section records only what is Intent-Solutions-fork-specific.)

- **2026-07-28** — Backfilled the blueprint baseline docs and installed the fork's testing
  enforcement layer. Docs: baseline PRD + five accepted ADRs filed chronologically in `000-docs/`
  (one-time renumber: sync map `001→007`, waiting-list plan `002→011`; `NNN` append-only from
  here). Testing: vendored audit-harness v1.3.1, L1 pre-commit lint gate chained with the beads
  hooks (beads' 5 hooks untouched), coverage made visible (not gated) on the deploy-line CI,
  engineer-owned `features/*.feature` acceptance specs for the intake and the gating boundary,
  and RTM/personas/journeys traceability. All fork-local with no upstream path — see the
  fork-local table above.
- **2026-07-27** — Gated the practice surfaces and opened a real waiting list. New `/request-access`
  intake (vetting-grade work-sample form → native `contact_messages` rows with an `[ACCESS] `
  subject discriminator, best-effort Slack ping, CSRF + honeypot + timed-token + rate-limit +
  length-cap defenses); anonymous `/course/explore` now serves a doctrine-voice practice-tracks
  teaser (zero course/vendor names); landing CTAs moved from raw `mailto:` to the intake (mailto
  stays as the secondary path on the intake page); `/contact` honors `enable_contact` (404 while
  disabled); anonymous gated-course links 302 to the intake; deploy smoke extended to enforce all
  of it. Full plan + security audit: `000-docs/011-PP-PLAN-waiting-list-gated-surfaces.md`.
- **2026-07-23** — Reset the `intent_learn` front-door composition after real iPad review: replaced
  the oversized black/orange poster treatment with a bright working-studio system, restrained the
  type scale, removed decorative numbering/card shells, restored continuous reading flow, and
  added breakpoint-specific phone/tablet layouts. Aligned the footer with the Intent Solutions
  estate using the canonical GetTerms-backed Terms of Service, Privacy Policy, and Acceptable Use
  destinations.
- **2026-07-23** — Rebuilt the `intent_learn` homepage around the Selective Implementation Practice
  doctrine: model-agnostic practitioner positioning, one house method, optional role-shaped proof
  paths, and an invitation-only deeper arena. Replaced the generic course-led acquisition copy and
  mutable vanity-stat strip. Added fork-local front-door contract tests and verified 375/390/768/
  1024/1440px layouts with zero horizontal overflow and 44px minimum interactive targets.
- **2026-07-21** — Full English conversion of the platform (catalog + templates + form labels +
  view messages) landed on `deploy`; offered upstream via #181. Branded course-detail page
  (`intent_learn/overrides/course_view.j2`). Healthcheck `X-Forwarded-Proto` fix. Fork governance
  added (this file + `.github/CODEOWNERS`, PR #1). Per-operator admin accounts provisioned for the
  team. `gh-pages` retired; `delete_branch_on_merge` enabled.
