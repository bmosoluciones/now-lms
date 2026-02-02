# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
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
