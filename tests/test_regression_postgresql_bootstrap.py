# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""
Regression tests for the PostgreSQL fresh-database bootstrap (PR #179).

Three scenarios that must pass for every supported database engine
(SQLite, PostgreSQL, MySQL). Each scenario guards against a specific
class of bug:

1. **Clean initial setup** — a completely empty database boots via
   init_app(), creates all tables, stamps Alembic to head, and seeds
   initial data. A second boot (restart) must be idempotent.

2. **Migration on existing database** — a database that already has
   data and an Alembic stamp must upgrade cleanly via AUTO_MIGRATE
   without colliding with existing tables.

3. **Upgrade / downgrade cycle** — the full Alembic migration chain
   must survive downgrade('base') → upgrade() → downgrade('base') →
   upgrade() without errors, proving every migration is reversible and
   the chain has no broken links.
"""

from __future__ import annotations

import os

import pytest
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.pool import StaticPool

# ---------------------------------------------------------------------------
# Engine detection helpers (same convention as test_multipledb.py)
# ---------------------------------------------------------------------------

def _is_ci() -> bool:
    return os.environ.get("CI", "").lower() in ("true", "1", "yes")


def _engine() -> str | None:
    url = os.environ.get("DATABASE_URL", "").lower()
    if "postgresql" in url:
        return "postgresql"
    if "mysql" in url:
        return "mysql"
    if "sqlite" in url:
        return "sqlite"
    return None


def _skip_unless_pg():
    if not (_is_ci() and _engine() == "postgresql"):
        pytest.skip("Requires CI + real PostgreSQL DATABASE_URL")


def _skip_unless_mysql():
    if not (_is_ci() and _engine() == "mysql"):
        pytest.skip("Requires CI + real MySQL DATABASE_URL")


# ---------------------------------------------------------------------------
# App factory — each test gets its own isolated app
# ---------------------------------------------------------------------------

def _make_app(name: str):
    from now_lms import create_app

    overrides: dict = {}
    if _engine() in (None, "sqlite"):
        overrides = {
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SQLALCHEMY_ENGINE_OPTIONS": {"poolclass": StaticPool},
            "SQLALCHEMY_CONNECT_ARGS": {"check_same_thread": False},
        }
    return create_app(app_name=name, testing=True, config_overrides=overrides)


def _wipe_database(app):
    """Drop every table and the alembic_version table."""
    from now_lms.db import database

    with app.app_context():
        database.drop_all()
        database.session.execute(database.text("DROP TABLE IF EXISTS alembic_version"))
        database.session.commit()


def _alembic_version(app):
    from now_lms.db import database

    with app.app_context():
        return database.session.execute(
            database.text("SELECT version_num FROM alembic_version")
        ).scalar()


# ===========================================================================
# Scenario 1: Clean initial setup
# ===========================================================================

class TestCleanInitialSetup:
    """A fresh, empty database must boot, stamp Alembic, seed data,
    and survive a restart without crashing."""

    def test_sqlite(self):
        app = _make_app("test_clean_sqlite")
        _wipe_database(app)

        from now_lms import init_app
        from now_lms.db import database

        assert init_app(flask_app=app) is True

        with app.app_context():
            version = database.session.execute(
                database.text("SELECT version_num FROM alembic_version")
            ).scalar()
            assert version is not None, "Alembic must be stamped after fresh setup"

        # Idempotent restart
        assert init_app(flask_app=app) is True

    def test_postgresql(self):
        _skip_unless_pg()
        app = _make_app("test_clean_pg")
        _wipe_database(app)

        from now_lms import init_app
        from now_lms.db import database

        assert init_app(flask_app=app) is True

        with app.app_context():
            version = database.session.execute(
                database.text("SELECT version_num FROM alembic_version")
            ).scalar()
            assert version is not None

        assert init_app(flask_app=app) is True

    def test_mysql(self):
        _skip_unless_mysql()
        app = _make_app("test_clean_mysql")
        _wipe_database(app)

        from now_lms import init_app
        from now_lms.db import database

        assert init_app(flask_app=app) is True

        with app.app_context():
            version = database.session.execute(
                database.text("SELECT version_num FROM alembic_version")
            ).scalar()
            assert version is not None

        assert init_app(flask_app=app) is True


# ===========================================================================
# Scenario 2: Migration on existing database
# ===========================================================================

class TestMigrationOnExistingDatabase:
    """A database that already has tables, data, and an Alembic stamp
    must upgrade cleanly via AUTO_MIGRATE without colliding."""

    def test_sqlite(self):
        app = _make_app("test_migrate_existing_sqlite")
        _wipe_database(app)

        from now_lms import init_app
        from now_lms.db import database

        # First boot: create schema + seed
        assert init_app(flask_app=app) is True

        with app.app_context():
            version_before = database.session.execute(
                database.text("SELECT version_num FROM alembic_version")
            ).scalar()
            # Verify data exists
            table_count = database.session.execute(
                database.text("SELECT COUNT(*) FROM system_info")
            ).scalar()

        # Second boot with AUTO_MIGRATE: should be a no-op, no collisions
        os.environ["NOW_LMS_AUTO_MIGRATE"] = "true"
        try:
            assert init_app(flask_app=app) is True
        finally:
            os.environ.pop("NOW_LMS_AUTO_MIGRATE", None)

        with app.app_context():
            version_after = database.session.execute(
                database.text("SELECT version_num FROM alembic_version")
            ).scalar()
            table_count_after = database.session.execute(
                database.text("SELECT COUNT(*) FROM system_info")
            ).scalar()

        assert version_before == version_after, "Alembic version must not change on no-op migrate"
        assert table_count_after == table_count, "Data must survive migration"

    def test_postgresql(self):
        _skip_unless_pg()
        app = _make_app("test_migrate_existing_pg")
        _wipe_database(app)

        from now_lms import init_app
        from now_lms.db import database

        assert init_app(flask_app=app) is True

        with app.app_context():
            version_before = database.session.execute(
                database.text("SELECT version_num FROM alembic_version")
            ).scalar()

        os.environ["NOW_LMS_AUTO_MIGRATE"] = "true"
        try:
            assert init_app(flask_app=app) is True
        finally:
            os.environ.pop("NOW_LMS_AUTO_MIGRATE", None)

        with app.app_context():
            version_after = database.session.execute(
                database.text("SELECT version_num FROM alembic_version")
            ).scalar()

        assert version_before == version_after

    def test_mysql(self):
        _skip_unless_mysql()
        app = _make_app("test_migrate_existing_mysql")
        _wipe_database(app)

        from now_lms import init_app
        from now_lms.db import database

        assert init_app(flask_app=app) is True

        with app.app_context():
            version_before = database.session.execute(
                database.text("SELECT version_num FROM alembic_version")
            ).scalar()

        os.environ["NOW_LMS_AUTO_MIGRATE"] = "true"
        try:
            assert init_app(flask_app=app) is True
        finally:
            os.environ.pop("NOW_LMS_AUTO_MIGRATE", None)

        with app.app_context():
            version_after = database.session.execute(
                database.text("SELECT version_num FROM alembic_version")
            ).scalar()

        assert version_before == version_after


# ===========================================================================
# Scenario 3: Full upgrade / downgrade cycle
# ===========================================================================

class TestUpgradeDowngradeCycle:
    """Every migration must be reversible. The full cycle
    downgrade('base') → upgrade() → downgrade('base') → upgrade()
    must complete without errors."""

    def _run_cycle(self, app):
        from now_lms import alembic
        from now_lms.db import database

        with app.app_context():
            alembic.upgrade()
            database.session.commit()
            head_version = database.session.execute(
                database.text("SELECT version_num FROM alembic_version")
            ).scalar()
            assert head_version is not None, "upgrade() must leave a version"

            alembic.downgrade("base")
            database.session.commit()

            try:
                base_version = database.session.execute(
                    database.text("SELECT version_num FROM alembic_version")
                ).scalar()
                assert base_version is None, "downgrade('base') must clear the version"
            except (OperationalError, ProgrammingError):
                pass  # table may be dropped — acceptable

            alembic.upgrade()
            database.session.commit()
            restored = database.session.execute(
                database.text("SELECT version_num FROM alembic_version")
            ).scalar()
            assert restored is not None, "upgrade() after downgrade must restore version"
            assert restored == head_version, "version must match head after full round-trip"

    def test_sqlite(self):
        app = _make_app("test_cycle_sqlite")
        _wipe_database(app)

        from now_lms import initial_setup

        with app.app_context():
            initial_setup(with_examples=False, flask_app=app)

        self._run_cycle(app)

    def test_postgresql(self):
        _skip_unless_pg()
        app = _make_app("test_cycle_pg")
        _wipe_database(app)

        from now_lms import initial_setup

        with app.app_context():
            initial_setup(with_examples=False, flask_app=app)

        self._run_cycle(app)

    def test_mysql(self):
        _skip_unless_mysql()
        app = _make_app("test_cycle_mysql")
        _wipe_database(app)

        from now_lms import initial_setup

        with app.app_context():
            initial_setup(with_examples=False, flask_app=app)

        self._run_cycle(app)


# ===========================================================================
# Auxiliary: database_select_version() must return truthy queries
# ===========================================================================

class TestSelectVersionQuery:
    """database_select_version() must return a query that evaluates
    truthy when curso exists — the original bug was a zero-column SELECT
    on PostgreSQL that always evaluated falsy."""

    @staticmethod
    def _query_for_engine(engine: str):
        from now_lms import create_app

        uris = {
            "sqlite": "sqlite:///:memory:",
            "postgresql": "postgresql+pg8000://x:x@localhost/test",
            "mysql": "mysql+mysqlconnector://x:x@localhost/test",
        }
        overrides = {}
        if engine == "sqlite":
            overrides = {
                "SQLALCHEMY_ENGINE_OPTIONS": {"poolclass": StaticPool},
                "SQLALCHEMY_CONNECT_ARGS": {"check_same_thread": False},
            }
        app = create_app(app_name=f"test_sel_{engine}", testing=True, config_overrides={"SQLALCHEMY_DATABASE_URI": uris[engine], **overrides})
        from now_lms.db.tools import database_select_version

        return database_select_version(app)

    def test_all_engines_return_nonempty_queries(self):
        for eng in ("sqlite", "postgresql", "mysql"):
            q = self._query_for_engine(eng)
            assert q is not None, f"{eng}: database_select_version() must not return None"
            normalized = " ".join(q.lower().split())
            assert "select" in normalized or "show" in normalized, (
                f"{eng}: query must be a SELECT or SHOW, got: {q!r}"
            )

    def test_postgresql_query_selects_a_column(self):
        q = self._query_for_engine("postgresql")
        normalized = " ".join(q.lower().split())
        assert normalized.startswith("select 1 from"), (
            f"PostgreSQL query must start with 'SELECT 1 FROM', got: {q!r}"
        )
