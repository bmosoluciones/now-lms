# Copyright 2025 BMO Soluciones, S.A.
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

"""Smoke test that walks the URL map and ensures routes respond with HTML."""

import os

import pytest

from now_lms.db.data_test import USUARIO_ADMINISTRADOR, crear_data_para_pruebas

REDIRECT_STATUS_CODES = {301, 302, 303, 307, 308}
ADMIN_PASSWORD = os.environ.get("ADMIN_PSWD") or os.environ.get("LMS_PSWD") or "lms-admin"
ROLE_MATRIX = [
    ("anonimo", None, True),
    ("admin", {"usuario": USUARIO_ADMINISTRADOR, "acceso": ADMIN_PASSWORD}, False),
    ("instructor", {"usuario": "instructor", "acceso": "instructor"}, True),
    ("moderador", {"usuario": "moderator", "acceso": "moderator"}, True),
    ("estudiante", {"usuario": "student", "acceso": "student"}, True),
]
ADMIN_REDIRECT_ALLOWED_PATHS = {
    "/user/login",
    "/user/logout",
    "/user/logon",
    "/course/",
    "/setting/delete_site_logo",
    "/setting/mail_check",
    "/user/forgot_password",
}
EXCLUDED_PATHS = {
    "/ads.txt",
    "/admin/user/change_type",
    "/health",
    "/debug",
    "/debug/redis",
    "/debug/config",
    "/debug/session",
    "/paypal_checkout/debug_config",
    "/course/change_curse_status",
    "/course/change_curse_public",
    "/course/change_curse_seccion_public",
    "/paypal_checkout/get_client_id",
    "/user/calendar/export.ics",
    "/setting/delete_site_logo",
    "/user/logout",
}

# Excluir prefijos completos (e.g., rutas del Debug Toolbar)
EXCLUDED_PREFIXES = {
    "/__debug__",
}


def _collect_static_routes(app) -> list[str]:
    """Return GET-able routes without dynamic segments."""
    rutas: list[str] = []
    for rule in app.url_map.iter_rules():
        if "<" in rule.rule:
            continue
        if "GET" not in rule.methods:
            continue
        if rule.endpoint.startswith("static"):
            continue
        # Excluir endpoints de Flask-DebugToolbar
        if rule.endpoint.startswith("debugtoolbar"):
            continue
        if rule.rule in EXCLUDED_PATHS:
            continue
        if any(rule.rule.startswith(prefix) for prefix in EXCLUDED_PREFIXES):
            continue
        rutas.append(rule.rule)
    return sorted(set(rutas))


def _assert_response(route: str, role: str, allow_redirects: bool, response):
    if response.status_code == 403 and role != "admin":
        return
    if response.status_code in (404, 500) or response.status_code >= 500:
        pytest.fail(f"{route} para {role} devolvió un error {response.status_code}")

    if response.status_code in REDIRECT_STATUS_CODES:
        if role == "admin" and route not in ADMIN_REDIRECT_ALLOWED_PATHS:
            pytest.fail(f"{route} redirigió para admin a {response.headers.get('Location')}")
        if role != "admin" and not allow_redirects:
            pytest.fail(f"{route} no debería redirigir para {role}")
        return

    if response.status_code >= 400:
        pytest.fail(f"{route} para {role} devolvió estado {response.status_code}")

    content_type = response.headers.get("Content-Type", "").lower()
    assert "html" in content_type, f"{route} para {role} devolvió Content-Type {content_type}"


@pytest.mark.parametrize("role, credentials, allow_redirects", ROLE_MATRIX)
def test_all_registered_routes_return_html(app, db_session, role, credentials, allow_redirects):
    # Seed the database once per test run with predictable users and content.
    with app.app_context():
        crear_data_para_pruebas()

    routes = _collect_static_routes(app)
    client = app.test_client()

    if credentials:
        login_response = client.post("/user/login", data=credentials, follow_redirects=False)
        assert login_response.status_code in REDIRECT_STATUS_CODES | {200, 201}

    for route in routes:
        response = client.get(route, follow_redirects=False)
        _assert_response(route, role, allow_redirects, response)
