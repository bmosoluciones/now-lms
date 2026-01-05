# Copyright 2022 - 2024 BMO Soluciones, S.A.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
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

    # Forzar SQLite en memoria a menos que DATABASE_URL esté configurada
    if "DATABASE_URL" not in os.environ:
        os.environ["DATABASE_URL"] = "sqlite:///:memory:"

    # Importar y obtener la aplicación
    import now_lms
    from now_lms import init_app
    from now_lms.db import database

    # init_app() inicializa la base de datos, devuelve True/False
    # La aplicación Flask real está en now_lms.lms_app
    init_app()
    app = now_lms.lms_app

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
