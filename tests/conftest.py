# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""
Configuración de pytest para NOW LMS.

Fixtures simples y claras para facilitar los tests.
Soporta SQLite, MySQL y PostgreSQL.

Estrategia:
- SQLite (memoria): app y base de datos frescas por test (overhead mínimo).
  Si DATABASE_URL no está definido, siempre se fuerza SQLite en memoria.
- MySQL/PostgreSQL: app y tablas se crean una vez por sesión; entre tests
  se limpian las tablas con TRUNCATE y se re-pueblan los datos iniciales.
  Esto evita el costo de DROP/CREATE TABLE por test.
"""

import os

import pytest


def _set_env():
    """Configura variables de entorno para tests.

    Si DATABASE_URL no está definido, siempre se fuerza SQLite en memoria.
    """
    os.environ["CI"] = "True"
    os.environ["SECRET_KEY"] = "test-secret-key"
    os.environ["LOG_LEVEL"] = "ERROR"
    if "DATABASE_URL" not in os.environ:
        os.environ["DATABASE_URL"] = "sqlite:///:memory:"


def _is_sqlite(url: str) -> bool:
    """Retorna True si la URL corresponde a SQLite."""
    return "sqlite" in url


def _drop_all(app):
    """Elimina todas las tablas."""
    from now_lms.db import database

    url = app.config.get("SQLALCHEMY_DATABASE_URI", "")
    with app.app_context():
        database.session.remove()
        try:
            with database.engine.connect() as conn:
                if url.startswith("mysql"):
                    conn.execute(database.text("SET FOREIGN_KEY_CHECKS=0"))
                database.metadata.drop_all(conn)
                if url.startswith("mysql"):
                    conn.execute(database.text("SET FOREIGN_KEY_CHECKS=1"))
                conn.commit()
        except Exception:
            pass


def _truncate_all(app):
    """Elimina todos los datos de todas las tablas sin borrar el esquema."""
    from now_lms.db import database

    url = app.config.get("SQLALCHEMY_DATABASE_URI", "")
    with app.app_context():
        database.session.remove()
        with database.engine.connect() as conn:
            if url.startswith("mysql"):
                conn.execute(database.text("SET FOREIGN_KEY_CHECKS=0"))
                for table in reversed(database.metadata.sorted_tables):
                    conn.execute(database.text(f"TRUNCATE TABLE {table.name}"))
                conn.execute(database.text("SET FOREIGN_KEY_CHECKS=1"))
            elif "postgresql" in url:
                table_names = ", ".join(f'"{t.name}"' for t in database.metadata.tables.values())
                if table_names:
                    conn.execute(database.text(f"TRUNCATE TABLE {table_names} RESTART IDENTITY CASCADE"))
            conn.commit()


def _configure_sqlite_pragmas(app):
    """Aplica pragmas de rendimiento para SQLite en memoria."""
    from now_lms.db import database

    with app.app_context():
        database.session.execute(database.text("PRAGMA journal_mode=MEMORY"))
        database.session.execute(database.text("PRAGMA synchronous=OFF"))
        database.session.execute(database.text("PRAGMA cache_size=-10000"))
        database.session.execute(database.text("PRAGMA temp_store=MEMORY"))
        database.session.commit()


# ---------------------------------------------------------------------------
# Fixture de sesión para motores reales: crea app y tablas una sola vez
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def _session_real_app():
    """Crea app y tablas una sola vez para MySQL/PostgreSQL."""
    _set_env()
    url = os.environ.get("DATABASE_URL", "sqlite:///:memory:")

    if _is_sqlite(url):
        yield None
        return

    from now_lms import create_app, init_app
    from now_lms.db import database

    app = create_app()
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    init_app(flask_app=app)

    yield app

    _drop_all(app)
    with app.app_context():
        database.engine.dispose()


# ---------------------------------------------------------------------------
# Fixture principal: selecciona estrategia según el motor
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def app(_session_real_app):
    """
    Proporciona una aplicación aislada para cada test.

    - SQLite: app fresca por test (overhead mínimo en memoria).
    - MySQL/PostgreSQL: app de sesión con limpieza TRUNCATE entre tests.
    """
    _set_env()
    url = os.environ.get("DATABASE_URL", "sqlite:///:memory:")

    if _is_sqlite(url):
        # SQLite en memoria: app y base de datos frescas por test.
        from now_lms import create_app, init_app
        from now_lms.db import database

        new_app = create_app()
        new_app.config["TESTING"] = True
        new_app.config["WTF_CSRF_ENABLED"] = False
        init_app(flask_app=new_app)
        _configure_sqlite_pragmas(new_app)

        yield new_app

        with new_app.app_context():
            try:
                database.session.rollback()
            except Exception:
                pass
            database.session.remove()
            database.engine.dispose()
    else:
        # MySQL/PostgreSQL: limpiar tablas con TRUNCATE y re-poblar datos.
        from now_lms import init_app
        from now_lms.db import database

        _truncate_all(_session_real_app)
        # init_app detecta que la DB no está poblada y re-carga datos iniciales
        init_app(flask_app=_session_real_app)

        yield _session_real_app

        with _session_real_app.app_context():
            try:
                database.session.rollback()
            except Exception:
                pass
            database.session.remove()


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
        try:
            database.session.rollback()
        except Exception:
            pass
        database.session.remove()
