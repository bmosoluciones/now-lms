# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""
Configuración de pytest para NOW LMS.

Fixtures simples y claras para facilitar el testing.
Todos los tests usan base de datos en memoria para máxima velocidad.
"""

import os

import pytest


@pytest.fixture(scope="function")
def app():
    """
    Crea una aplicación Flask limpia para cada test.

    Configuración:
    - Base de datos en memoria (SQLite)
    - CSRF deshabilitado para facilitar tests
    - Logging reducido

    La aplicación y base de datos se destruyen automáticamente
    después de cada test.
    """
    # Configurar entorno de testing
    os.environ["CI"] = "True"
    os.environ["SECRET_KEY"] = "test-secret-key"
    os.environ["LOG_LEVEL"] = "ERROR"

    # Force file-based SQLite for testing to ensure perfect transaction isolation and database sharing
    if "DATABASE_URL" not in os.environ:
        os.environ["DATABASE_URL"] = "sqlite:///test_now_lms.db"

    # Importar y obtener la aplicación
    import now_lms
    from sqlalchemy.pool import StaticPool
    now_lms.lms_app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "poolclass": StaticPool,
        "echo": True,
    }
    from now_lms import init_app
    from now_lms.db import database

    # init_app() inicializa la base de datos, devuelve True/False
    # La aplicación Flask real está en now_lms.lms_app
    init_app()
    app = now_lms.lms_app

    import logging
    logging.basicConfig()
    logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False

    # Optimizaciones SQLite para velocidad en memoria
    if "sqlite" in app.config.get("SQLALCHEMY_DATABASE_URI", ""):
        with app.app_context():
            database.session.execute(database.text("PRAGMA journal_mode=MEMORY"))
            database.session.execute(database.text("PRAGMA synchronous=OFF"))
            database.session.execute(database.text("PRAGMA cache_size=-10000"))
            database.session.execute(database.text("PRAGMA temp_store=MEMORY"))
            database.session.commit()

    yield app

    # Limpieza
    with app.app_context():
        database.session.remove()
        database.drop_all()


@pytest.fixture(scope="function")
def client(app):
    """Cliente HTTP para hacer requests a la aplicación."""
    return app.test_client()


@pytest.fixture(scope="function")
def db_session(app):
    """
    Sesión de base de datos para el test.

    Crea todas las tablas automáticamente.
    Los cambios se limpian después del test.
    """
    from now_lms.db import database

    with app.app_context():
        database.create_all()
        yield database.session
        database.session.rollback()
        database.session.remove()
        database.drop_all()
