# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""
Configuración de pytest para NOW LMS.

Fixtures simples y claras para facilitar los tests.
Soporta SQLite, MySQL y PostgreSQL.
"""

import os

import pytest


@pytest.fixture(scope="function")
def app():
    """
    Crea una aplicación Flask limpia para cada test.

    La aplicación y base de datos se destruyen automáticamente
    después de cada test.
    """
    os.environ["CI"] = "True"
    os.environ["SECRET_KEY"] = "test-secret-key"
    os.environ["LOG_LEVEL"] = "ERROR"

    if "DATABASE_URL" not in os.environ:
        os.environ["DATABASE_URL"] = "sqlite:///:memory:"

    import now_lms
    from now_lms import init_app
    from now_lms.db import database

    init_app()
    app = now_lms.lms_app

    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False

    if "sqlite" in app.config.get("SQLALCHEMY_DATABASE_URI", ""):
        with app.app_context():
            database.session.execute(database.text("PRAGMA journal_mode=MEMORY"))
            database.session.execute(database.text("PRAGMA synchronous=OFF"))
            database.session.execute(database.text("PRAGMA cache_size=-10000"))
            database.session.execute(database.text("PRAGMA temp_store=MEMORY"))
            database.session.commit()

    yield app

    with app.app_context():
        database.session.rollback()
        database.session.remove()
        database.engine.dispose()
        url = app.config.get("SQLALCHEMY_DATABASE_URI", "")
        with database.engine.connect() as conn:
            if url.startswith("mysql"):
                conn.execute(database.text("SET FOREIGN_KEY_CHECKS=0"))
            database.metadata.drop_all(conn)
            if url.startswith("mysql"):
                conn.execute(database.text("SET FOREIGN_KEY_CHECKS=1"))
            conn.commit()


@pytest.fixture(scope="function")
def client(app):
    """Cliente HTTP para hacer requests a la aplicación."""
    return app.test_client()


@pytest.fixture(scope="function")
def db_session(app):
    """
    Sesión de base de datos para el test.

    init_app() ya creó tablas y datos iniciales.
    Este fixture solo limpia al final del test.
    """
    from now_lms.db import database

    with app.app_context():
        yield database.session
        database.session.rollback()
        database.session.remove()
