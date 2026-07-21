# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""
Regression tests for booting NOW LMS against a completely fresh, empty
database (the scenario fix(db) "bootstrap a fresh PostgreSQL database
correctly on first boot" addresses).

That fix corrected three linked defects, all invisible on SQLite/MySQL,
which is why they shipped unnoticed:

1. run.py called alembic.upgrade() unconditionally *before* init_app(). On
   an empty database the migration chain runs from base and fails (a
   migration creates course_library with a FK to the not-yet-created curso
   table). init_app()/initial_setup() is the correct sole owner of schema
   management.
2. initial_setup() never stamped Alembic after create_all(), so a later
   boot saw a populated database and ran alembic.upgrade() from base,
   colliding with tables create_all() already made.
3. database_is_populated() used `SELECT FROM pg_tables WHERE ...` on
   PostgreSQL -- a zero-column SELECT whose result row is always falsy --
   so it always reported "not populated" and re-ran initial_setup() on
   every boot, crashing on a duplicate key the second time.

This file proves, end to end, that a fresh database boots cleanly and that
a second boot against the now-populated database (a container restart) is
idempotent -- the exact scenario the original bug broke.

Two database engines are covered:

* SQLite ":memory:" always runs (it's the suite's default database) and
  exercises init_app()/initial_setup() directly -- the code path defects 2
  and 3 live in. It also incidentally guards against a *second*, closely
  related bug this test suite found while adding this coverage: Alembic's
  Flask wrapper caches the connection it stamps with and invalidates it on
  app-context teardown, which destroys the sole connection to a SQLite
  ":memory:" (StaticPool) database the moment any later code opens a new
  app context for this app -- exactly what happens right after
  init_app() returns. fix(db) now stamps with a short-lived, explicitly
  scoped connection instead of Alembic's cached one, so this suite's
  ordinary fixtures keep working.
* PostgreSQL is the engine the original bug was reported against. It only
  runs when DATABASE_URL points at a real PostgreSQL server (matching this
  project's existing tests/test_multipledb.py convention -- CI provisions
  Postgres via a real service, not a container spun up by the test itself).
  Verified locally against a disposable `docker run postgres:16` container
  (see this commit's message for the exact commands and results); the
  container is not part of the test itself so the suite has no Docker
  dependency.
"""

from __future__ import annotations

import os

import pytest
from sqlalchemy.pool import StaticPool


def _is_ci_environment() -> bool:
    return os.environ.get("CI", "").lower() in ("true", "1", "yes")


def _database_url_engine() -> str | None:
    db_url = os.environ.get("DATABASE_URL", "")
    if "postgresql" in db_url.lower():
        return "postgresql"
    if "mysql" in db_url.lower():
        return "mysql"
    if "sqlite" in db_url.lower():
        return "sqlite"
    return None


def _fresh_boot_then_idempotent_restart(app):
    """Shared assertions for both engines: fresh boot succeeds, /health and
    admin login work, and a second boot (restart-equivalent) is idempotent."""
    from now_lms import init_app
    from now_lms.auth import validar_acceso
    from now_lms.db.initial_data import ADMIN_USER_WITH_FALLBACK

    assert init_app(flask_app=app) is True, "init_app() must succeed against a completely fresh, empty database"

    with app.app_context():
        client = app.test_client()
        response = client.get("/health")
        assert response.status_code == 200
        payload = response.get_json()
        assert payload["status"] == "ok"
        assert payload["database"] == "ok"

        assert validar_acceso(ADMIN_USER_WITH_FALLBACK, "lms-admin") is True, (
            "the default administrator account created during a fresh boot must be able to log in"
        )

    # Second boot: the exact "container restart" scenario. Must not crash
    # (defect 3's duplicate-key symptom: "duplicate key value violates
    # unique constraint ix_system_info_param") and must not silently wipe
    # or re-seed data.
    assert init_app(flask_app=app) is True, "a second boot against an already-populated database (a restart) must be idempotent"

    with app.app_context():
        assert validar_acceso(ADMIN_USER_WITH_FALLBACK, "lms-admin") is True, (
            "the admin account must still be able to log in after a second, idempotent boot"
        )


def test_fresh_sqlite_boot_then_idempotent_restart():
    """SQLite ":memory:" is this suite's default database. Uses
    create_app() with an explicit StaticPool (matching
    tests/test_alembic_upgrade.py's established pattern for keeping a
    single connection alive across app-context boundaries) rather than the
    shared `app` fixture, because the shared fixture already calls
    init_app() once -- this test needs to observe the *first* boot itself,
    plus a controlled second boot, not a pre-booted app."""
    from now_lms import create_app

    config_overrides = {
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SQLALCHEMY_ENGINE_OPTIONS": {"poolclass": StaticPool},
        "SQLALCHEMY_CONNECT_ARGS": {"check_same_thread": False},
    }
    app = create_app(app_name="test_fresh_sqlite_boot", testing=True, config_overrides=config_overrides)

    _fresh_boot_then_idempotent_restart(app)


pytestmark_pg = pytest.mark.skipif(
    not (_is_ci_environment() and _database_url_engine() == "postgresql"),
    reason="Fresh-PostgreSQL bootstrap test only runs in CI with a real PostgreSQL DATABASE_URL configured "
    "(matches tests/test_multipledb.py's convention). Verify locally with a disposable "
    "`docker run --rm -d -e POSTGRES_PASSWORD=x -e POSTGRES_DB=x -e POSTGRES_USER=x -p 55432:5432 postgres:16` "
    "and DATABASE_URL=postgresql+pg8000://x:x@127.0.0.1:55432/x.",
)


@pytestmark_pg
def test_fresh_postgresql_boot_then_idempotent_restart():
    """The exact scenario originally reported: a truly empty PostgreSQL
    database (all tables dropped, including alembic_version) must boot
    cleanly via init_app(), and a second boot against the now-populated
    database must not crash."""
    from now_lms import create_app
    from now_lms.db import database

    app = create_app(app_name="test_fresh_postgresql_boot", testing=True)

    with app.app_context():
        database.drop_all()
        database.session.execute(database.text("DROP TABLE IF EXISTS alembic_version"))
        database.session.commit()

    _fresh_boot_then_idempotent_restart(app)


@pytestmark_pg
def test_premature_alembic_upgrade_on_empty_postgresql_fails_the_way_the_original_bug_did():
    """Documents *why* run.py's old unconditional `alembic.upgrade()` call
    before init_app() was wrong: on a truly empty database the migration
    chain runs from base and fails, because an early migration
    (20260109_152634_add_missing_tables) creates course_library with a FK
    to the curso table, which no migration creates -- curso is a
    create_all()-only table. This is a negative control: it proves the
    *old* run.py ordering was broken, so run.py deferring entirely to
    init_app()/initial_setup() (which runs create_all() before any
    migration decision) is the correct fix, not an incidental one."""
    from now_lms import alembic, create_app
    from now_lms.db import database

    app = create_app(app_name="test_premature_alembic_upgrade", testing=True)

    with app.app_context():
        database.drop_all()
        database.session.execute(database.text("DROP TABLE IF EXISTS alembic_version"))
        database.session.commit()

    with pytest.raises(Exception, match=r'"?curso"? does not exist|relation "curso"'):
        with app.app_context():
            alembic.upgrade()
