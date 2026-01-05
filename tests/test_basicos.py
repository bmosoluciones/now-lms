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
Tests básicos de la aplicación.

Tests simples que verifican que la aplicación está correctamente configurada.
"""


def test_aplicacion_se_puede_importar():
    """La aplicación debe poder importarse sin errores."""
    import now_lms

    assert now_lms is not None


def test_aplicacion_se_puede_inicializar(app):
    """La aplicación debe poder inicializarse."""
    assert app is not None
    assert app.config["TESTING"] is True


def test_base_de_datos_usa_sqlite_en_tests(app):
    """En tests, la base de datos debe usar SQLite."""
    db_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")

    assert "sqlite" in db_uri.lower()


def test_cliente_puede_hacer_request(client):
    """El cliente de test debe poder hacer requests."""
    # Intentar acceder a la página de health check
    response = client.get("/health")

    # Debe responder (cualquier código es válido aquí)
    assert response.status_code in (200, 404, 302)
