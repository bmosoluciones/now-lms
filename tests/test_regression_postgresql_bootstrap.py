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
   must survive downgrade('base') -> upgrade() without errors,
   proving every migration is reversible and the chain has no broken
   links.
"""

from __future__ import annotations

import os
import tempfile

import pytest
from sqlalchemy.exc import OperationalError, ProgrammingError


# ---------------------------------------------------------------------------
# Engine detection
# ---------------------------------------------------------------------------

def _engine() -> str | None:
    url = os.environ.get("DATABASE_URL", "").lower()
    if "postgresql" in url:
        return "postgresql"
    if "mysql" in url:
        return "mysql"
    if "sqlite" in url:
        return "sqlite"
    return None


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

def _make_app(name: str, uri: str | None = None):
    from now_lms import create_app

    if uri is None:
        if _engine() == "postgresql":
            uri = os.environ["DATABASE_URL"]
        elif _engine() == "mysql":
            uri = os.environ["DATABASE_URL"]
        else:
            fd, path = tempfile.mkstemp(suffix=".db", prefix=f"{name}_")
            os.close(fd)
            uri = f"sqlite:///{path}"

    overrides = {"SQLALCHEMY_DATABASE_URI": uri}
    return create_app(app_name=name, testing=True, config_overrides=overrides)


def _wipe_database(app):
    from now_lms.db import database

    with app.app_context():
        database.drop_all()
        database.session.execute(database.text("DROP TABLE IF EXISTS alembic_version"))
        database.session.commit()


# ===========================================================================
# Scenario 1: Clean initial setup
# ===========================================================================

class TestCleanInitialSetup:

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

        assert init_app(flask_app=app) is True

    def test_postgresql(self):
        if _engine() != "postgresql":
            pytest.skip("DATABASE_URL not set to PostgreSQL")
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
        if _engine() != "mysql":
            pytest.skip("DATABASE_URL not set to MySQL")
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

    def _run(self, name):
        app = _make_app(name)
        _wipe_database(app)

        from now_lms import init_app
        from now_lms.db import database

        assert init_app(flask_app=app) is True

        with app.app_context():
            version_before = database.session.execute(
                database.text("SELECT version_num FROM alembic_version")
            ).scalar()
            table_count = database.session.execute(
                database.text("SELECT COUNT(*) FROM system_info")
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
            table_count_after = database.session.execute(
                database.text("SELECT COUNT(*) FROM system_info")
            ).scalar()

        assert version_before == version_after, "Alembic version must not change on no-op migrate"
        assert table_count_after == table_count, "Data must survive migration"

    def test_sqlite(self):
        self._run("test_migrate_sqlite")

    def test_postgresql(self):
        if _engine() != "postgresql":
            pytest.skip("DATABASE_URL not set to PostgreSQL")
        self._run("test_migrate_pg")

    def test_mysql(self):
        if _engine() != "mysql":
            pytest.skip("DATABASE_URL not set to MySQL")
        self._run("test_migrate_mysql")


# ===========================================================================
# Scenario 3: Full upgrade / downgrade cycle
# ===========================================================================

class TestUpgradeDowngradeCycle:

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

        with app.app_context():
            alembic.downgrade("base")
            database.session.commit()
            database.session.remove()

            try:
                base_version = database.session.execute(
                    database.text("SELECT version_num FROM alembic_version")
                ).scalar()
                assert base_version is None, "downgrade('base') must clear the version"
            except (OperationalError, ProgrammingError):
                pass

        with app.app_context():
            alembic.upgrade()
            database.session.commit()
            restored = database.session.execute(
                database.text("SELECT version_num FROM alembic_version")
            ).scalar()
            assert restored is not None, "upgrade() after downgrade must restore version"
            assert restored == head_version, "version must match head after round-trip"

    def test_sqlite(self):
        app = _make_app("test_cycle_sqlite")
        _wipe_database(app)

        from now_lms import initial_setup

        with app.app_context():
            initial_setup(with_examples=False, flask_app=app)

        self._run_cycle(app)

    def test_postgresql(self):
        if _engine() != "postgresql":
            pytest.skip("DATABASE_URL not set to PostgreSQL")
        app = _make_app("test_cycle_pg")
        _wipe_database(app)

        from now_lms import initial_setup

        with app.app_context():
            initial_setup(with_examples=False, flask_app=app)

        self._run_cycle(app)

    def test_mysql(self):
        if _engine() != "mysql":
            pytest.skip("DATABASE_URL not set to MySQL")
        app = _make_app("test_cycle_mysql")
        _wipe_database(app)

        from now_lms import initial_setup

        with app.app_context():
            initial_setup(with_examples=False, flask_app=app)

        self._run_cycle(app)


# ===========================================================================
# Auxiliary: database_select_version() returns truthy queries
# ===========================================================================

class TestSelectVersionQuery:

    def test_postgresql_query_selects_a_column(self):
        if _engine() != "postgresql":
            pytest.skip("DATABASE_URL not set to PostgreSQL")
        app = _make_app("test_sel_pg")
        from now_lms.db.tools import database_select_version

        q = database_select_version(app)
        normalized = " ".join(q.lower().split())
        assert normalized.startswith("select 1 from"), (
            f"PostgreSQL query must start with 'SELECT 1 FROM', got: {q!r}"
        )
