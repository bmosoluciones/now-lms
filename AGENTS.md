# AGENTS.md — Intent Solutions fork of NOW-LMS

> Context you would otherwise waste time rediscovering. Read this before touching anything. For
> estate-wide knowledge (VPS, deploy, secrets) the governed brain wins — call `brain_search` first.

## What this repo is

This is the **Intent Solutions fork** of `bmosoluciones/now-lms` (Apache-2.0 Spanish-first Flask LMS). Read [`FORK.md`](FORK.md) first — the entire governance posture is there ("use it as-is, mature it upstream; no private forks of behavior"). Two branches matter:

- `main` — thin tracking mirror of `upstream/main` + fork-local governance (`FORK.md`, `.github/CODEOWNERS`).
- `deploy/now-lms-fixed` — what the Cohort platform actually runs. Carries `intent_learn` theme + English i18n + healthcheck fix; each item has an upstream retirement path tracked in `FORK.md`.

Do not rename the `now_lms` package, do not edit core views for branding. Branding is data — use `NOW_LMS_THEMES_DIR`.

## Architecture (load-bearing)

- **Entry point**: `now_lms/__init__.py` — `create_app()` factory + module-level `lms_app`. Blueprints registered in `registrar_modulos_en_la_aplicacion_principal()`.
- **CLI**: `now_lms/cli.py` — `lmsctl` entry point. Groups: `database {init,seed,backup,restore,migrate,drop,reset,engine}`, `session {clear,stats}`, `info {system,path,routes,course}`, `settings {theme_,lang_,timezone_}{get,set,list}`, `admin {reset_password,set_admin}`, `user {new,set_password}`, `cache {info,clear,stats}`. Plus `serve` (waitress/gunicorn) via `run.py`, not `cli.py`.
- **Server**: `run.py` — auto-selects waitress (default, cross-platform) or gunicorn (Linux, `WSGI_SERVER=gunicorn`). `now_lms/worker_config.py` derives workers/threads from env + CPU. Waitress strips `X-Forwarded-*` unless `NOW_LMS_TRUSTED_PROXY` is set — see env table.
- **DB**: SQLAlchemy + flask-alembic + flask-session. Multi-backend (SQLite default, PostgreSQL via pg8000, MySQL via mysql-connector). **Production on this fork runs PostgreSQL** (`postgres:16` container, `postgresql+pg8000://...db:5432/nowlms`, see `docker-compose.yml` line 49). The SQLite path is test-only; `tests/conftest.py` forces `sqlite:///:memory:` unless `DATABASE_URL` is exported. **The PG path is the high-fidelity verification** for any code change — pre-existing SQLite fixture bugs (e.g. `ad_sense` table not populated for some tests) are SQLite-specific and not a regression signal on the production path. The fresh-PG-bootstrap fix from PR #179 is what makes the PG container boot correctly on a clean deploy. `now_lms/db/initial_data.py` ships default config/users/courses.
- **Views**: `now_lms/vistas/` (Spanish for "views"). New blueprints land next to existing siblings.
- **Models**: `now_lms/db/__init__.py`.
- **Themes**: `now_lms/templates/themes/<name>/`. The `intent_learn` theme is the fork-local one.
- **Migrations**: `now_lms/migrations/` — flat filename pattern `<unix_ts>_<slug>.py`. New ones: `alembic revision --autogenerate -m "..."`, then stamp head if needed (see "Fresh-DB gotcha" below).
- **Fork-local seeder**: `scripts/seed_cca_courses.py` — idempotent curriculum seeder for the CCA-F prep cohort. **The curriculum is NOT in this repo**: it lives in the private `intent-solutions-io/intent-curriculum` repo (publishing graded answer keys beside the courses that grade them is an assessment-integrity problem, and this fork stays public so platform fixes can go upstream). The seeder reads `<CCA_CONTENT_DIR>/banks/*.json` + `<CCA_CONTENT_DIR>/lessons/**/*.md`; point it at a checkout: `docker compose exec -T -e CCA_CONTENT_DIR=/path/to/intent-curriculum/cca app python3.12 scripts/seed_cca_courses.py`. Production is already seeded and the seeder is idempotent, so this is only for a reseed or DR rebuild.

## Dev commands (the ones that matter)

```bash
# Install — pin to test.lock (CI does this; do it locally too)
python3 -m venv .venv && source .venv/bin/activate
pip install --require-hashes -r test.lock       # full test deps
pip install -e .                                 # editable install

# Initialise + run
lmsctl database init                             # idempotent first-run
lmsctl serve                                     # production-mode, waitress

# Dev server (Flask debug + auto-reload) — dev/server.sh is a one-liner that
# does NOT export FLASK_APP; set it in the parent shell.
export FLASK_APP=now_lms
bash dev/server.sh

# Full pipeline (lint + typecheck + test). CI splits these — see CI section.
bash dev/test.sh

# Identical lint+typecheck, no tests. ⚠️ STILL BROKEN ON THIS BRANCH — it calls a
# missing dev/ensure_headers.py and dies on its first line. Upstream #217 removed
# the orphaned call, but that commit is NOT an ancestor of this branch; the fix
# arrives with the v2.0.0 sync. Use dev/test.sh until then.
bash dev/lint.sh

# Run a single test
pytest tests/test_auth.py -v
pytest tests/test_forum.py::TestForum::test_post_creation -v

# Fast iteration (skip slow/comprehensive markers)
pytest -m "not slow and not comprehensive"
```

Default admin after `database init`: `lms-admin` / `lms-admin`. **Never** ship this.

## Environment variables (the load-bearing ones)

| Var | Effect |
|---|---|
| `SECRET_KEY` | Flask session — **set in prod** (default `"dev"`). |
| `DATABASE_URL` | `sqlite://...` (default), `postgresql+pg8000://...`, `mysql+mysqlconnector://...`. |
| `NOW_LMS_AUTO_MIGRATE` | If truthy, run `alembic.upgrade()` on boot when DB is populated. |
| `NOW_LMS_THEMES_DIR` | Override theme directory. |
| `NOW_LMS_DATA_DIR` / `NOW_LMS_LANG` / `NOW_LMS_CURRENCY` / `NOW_LMS_TIMEZONE` | Operational overrides. **`dev/test.sh` unsets these** so config is deterministic. |
| `WSGI_SERVER` | `waitress` (default) or `gunicorn`. |
| `PORT` / `LMS_PORT` | Bind port (default 8080). |
| `NOW_LMS_TRUSTED_PROXY` | `run.py` only — Waitress `trusted_proxy` arg (e.g. Caddy). Required for `NOW_LMS_FORCE_HTTPS` to see `X-Forwarded-Proto`. |
| `NOW_LMS_FORCE_HTTPS` | Toggles HTTPS-only redirects. Depends on `NOW_LMS_TRUSTED_PROXY` to actually receive `X-Forwarded-Proto`. |
| `CI` | `True` in tests → in-memory SQLite. |
| `LOG_LEVEL` | `TRACE`/`DEBUG`/`INFO`/`WARNING`/`ERROR`. |
| `ADMIN_USER` / `ADMIN_PSWD` | Bootstrap admin credentials (release.yml uses `hello`/`world`). |

## The fresh-DB gotcha (learned the hard way)

`now_lms/__init__.py:initial_setup()` is the **single owner of schema management**. Do **not** call `alembic.upgrade()` unconditionally before `init_app()`:

- On a fresh DB, the migration chain runs from base and fails (an `op.create_table` with a FK to a not-yet-created table).
- After `database.create_all()`, an unguarded `CREATE TABLE` migration collides.

The fix is built in **on this fork**: `initial_setup()` calls `database.create_all()` then `alembic.stamp(head)` so subsequent boots only run genuinely new migrations. The comment block at `run.py:34-43` is the contract — read it before touching init.

> ⚠️ **This fix is fork-local, not upstream.** It came from our PR
> [bmosoluciones/now-lms#179](https://github.com/bmosoluciones/now-lms/pull/179), which reports
> `merged` — but its merge commit is not an ancestor of `upstream/main`, `alembic.stamp` appears
> nowhere in upstream `now_lms/**`, and the test file it added is absent upstream. It was merged and
> then lost. Do **not** drop fork commit `55900ed` during an upstream sync on the assumption that
> upstream carries it; dropping it reintroduces the fresh-PostgreSQL boot failure. Re-offer branch
> `fix/postgresql-fresh-database-bootstrap` (`ecc85d5`) upstream instead.

When adding a new migration to a populated DB, do `alembic upgrade` not `create_all`.

## CI vs `dev/test.sh` — these are NOT the same

- **`deploy-line-ci.yml` — the gate that actually fires on this branch** (`push` + `PR` to `deploy/now-lms-fixed`, Py 3.12): ruff + flake8 + `pylint --fail-under=9.5`, the PostgreSQL pytest suite, AND the Playwright browser-E2E job (`e2e/`) are all **blocking** since the v2.0.0 sync landed (2026-07-29, bead `now-lms-dbq`). It exists because upstream's `python.yml` never runs here. A green deploy-line PR proves lint + tests + the member browser journey.
- **`ai-code-review.yml`**: the MiniMax reviewer on deploy-line PRs (fork-local, commit `c897582`). Greptile reviews via its GitHub App.
- **`python.yml`** (`push` + `PR` to `main`/`development`, Py 3.11–3.14): `pip install --require-hashes -r test.lock` → `python -m build` + `twine check` → `pybabel compile` → `pytest`. **No lint.** ⚠️ Never fires on the deploy line, and half its trigger is dead — this fork has no `development` branch.
- **`release.yml`** (PR to `main` + `workflow_run` after CI): `test.lock` install → SQLite + Postgres + MySQL pytest runs (multi-DB paths NOT covered locally) → lint gate (`flake8`, `mypy`, `ruff`, `pylint --fail-under=9`). Codecov gate.
- **`dev/test.sh`**: flake8 + ruff + pylint (9.5) + mypy + pybabel compile + pytest. Stricter pylint than `release.yml` — expects 9.5 not 9.0.
- **`dev/lint.sh`**: black + pylint (9.5) + prettier + (broken) `ensure_headers.py`. Not run in CI, and broken on this branch — see the dev-commands note.

A green `python.yml` is **not** enough — Postgres/MySQL paths are only exercised in `release.yml` against live containers. On the deploy line, `python.yml` does not run at all (upstream deleted it at v2.0.0); `deploy-line-ci.yml` is the gate, and its test half is blocking.

## Testing

- **Fixture taxonomy** (`tests/conftest.py`):
  - `app` (function-scoped, in-memory SQLite, PRAGMA MEMORY/OFF) — the default quick-check path. Fine for smoke testing on this fork's dev box, but **the SQLite fixture has known bugs** (e.g. `ad_sense` table not populated for some tests) that do **not** reproduce on Postgres. **For any code change that touches the DB, model, or migration path, run the full pytest against Postgres** as the high-fidelity verification (see "Postgres test path" below).
  - `client`, `db_session` — derived from `app`.
  - There are **no session-scoped `session_*` fixtures** — `@.github/copilot-instructions.md` lists some but they don't exist in `conftest.py`. Add them if you actually need them.
- **Postgres test path** (high-fidelity; mirrors production):
  - The production path uses `postgres:16` + `pg8000`. The same backend is exercised in `release.yml` against a live container.
  - Local repro: set `DATABASE_URL=postgresql+pg8000://USER:PASS@HOST:5432/nowlms` before running `pytest`. The conftest fixture will respect it (the in-memory SQLite override only fires when `DATABASE_URL` is unset).
  - Pre-existing SQLite failures (e.g. `ad_sense` "no such table" errors) **do not** predict Postgres behavior. Don't act on SQLite-only failures — either re-run on Postgres to confirm, or note them as SQLite-specific and move on.
- **Markers** (`pytest.ini`): `slow`, `comprehensive`, `integration`, `unit`, `benchmark`. Skip slow stuff with `pytest -m "not slow"`.
- **Coverage**: `pytest --cov=now_lms` is the default; Codecov gate on `release.yml`.
- **Translations**: `pybabel compile -d now_lms/translations` is part of the test pipeline. New `.po` catalogs are **not** PR'd raw — upstream feeds them via the [Crowdin project](https://crowdin.com/project/now-lms) (source Spanish). Mark new strings for translation before committing.

## Lint thresholds (CI gate)

- `flake8` — max-line-length 120, ignore `E501,E203,E266,W503,E722` (differs from project default 127 used by black/pylint).
- `ruff check --fix now_lms`
- `pylint now_lms --score=yes --fail-under=9.5` local / `9.0` in `release.yml`. Score drift below 9.5 after small changes is a common CI failure — silence with explicit `# pylint: disable=...` + a reason comment.
- `mypy now_lms --ignore-missing-imports` (`.mypy.ini` disables `union-attr, name-defined, attr-defined`).
- `black` (line-length 127) and `prettier` (jinja templates) are formatter-only, run via `dev/lint.sh`, **not enforced in CI**.

## Conventions (the ones that bit us)

- **Spanish identifiers everywhere in source**: `inicializa_extenciones_terceros`, `cargar_sesion`, `registrar_modulos_en_la_aplicacion_principal`. Don't rename "to English" — that is a permanent merge-conflict tax against upstream.
- **Headers**: every Python file gets `SPDX-License-Identifier: Apache-2.0` + `SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.`. `dev/lint.sh` was supposed to enforce this via `dev/ensure_headers.py`, but the script is missing — this is a real gap; add or upstream the enforcer. **Do not** put intent-solutions attribution in source files — only `FORK.md` is the fork's voice.
- **Commit messages**: conventional commits (`type(scope): imperative subject`), signed (`git commit -s`). See `docs/CONTRIBUTING.md` and `FORK.md`.
- **CHANGELOG.md is upstream's** — do not add fork entries. Fork changelog lives in `FORK.md`.
- **i18n**: all user-facing strings go through `_()` / `_l()` (flask-babel). Source-of-truth language is Spanish; English catalog lives in `now_lms/translations/en/`. See upstream #181 for translation status.
- **Migrations**: filename `<unix_ts>_<slug>.py` (e.g. `1780403775_add_public_api_*.py`). Use `alembic revision --autogenerate` and inspect the generated file before committing.

## Reference docs in this repo

- [`FORK.md`](FORK.md) — fork governance, branches, downstream patch list, retirement criteria. **Read first.**
- [`.github/copilot-instructions.md`](.github/copilot-instructions.md) — verbose setup + commands; **verify against the source before trusting** (the session-fixture list and several commands are stale).
- [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md) — upstream contributing conventions.
- [`docs/test-performance.md`](docs/test-performance.md) — test suite performance tuning.
- `dev/test.sh`, `dev/lint.sh`, `dev/server.sh` — the actual scripts you run.
- `.github/workflows/python.yml` — CI on PR/push to `main`/`development` (3.11–3.14): build + pytest, no lint.
- `.github/workflows/release.yml` — multi-DB (Postgres + MySQL) + lint + coverage gate.

## Anti-patterns — refuse on sight

- ❌ Renaming `now_lms` package, modules, or CSS classes for branding.
- ❌ Adding `intent-solutions`/`@jeremylongshore`/Anthropic marketing strings into source files or the user-facing UI.
- ❌ Putting intent-solutions attribution in code comments, headers, or `pyproject.toml` — only `FORK.md` and commit footers.
- ❌ Editing `CHANGELOG.md` for fork-local changes.
- ❌ Calling `alembic.upgrade()` unconditionally before `init_app()` in custom code paths.
- ❌ Submitting raw `.po` translation PRs — upstream intakes via Crowdin.
- ❌ Suppressing pylint without a comment explaining why.
- ❌ Skipping `pybabel compile` before running `pytest` — string-comparison tests will fail.
- ❌ Skipping `pip install --require-hashes -r test.lock` — CI installs from the lockfile, and you want your local env to match.
