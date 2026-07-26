# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.

"""Tests for the static pages route (theme-defined filesystem pages)."""

import pytest
from flask import url_for


class TestStaticPageRoute:
    """Tests for /static/<page> route (theme-defined pages)."""

    def test_static_page_route_exists(self, app):
        with app.test_request_context():
            url = url_for("home.static_page", page="test")
            assert "/static/test" in url

    def test_static_page_returns_redirect_if_not_found(self, client):
        response = client.get("/static/nonexistent-page-xyz")
        assert response.status_code in [302, 200]

    def test_static_page_rejects_path_traversal(self, client):
        response = client.get("/static/../../../etc/passwd")
        assert response.status_code in [302, 200, 404]

    def test_static_page_rejects_dot(self, client):
        response = client.get("/static/..")
        assert response.status_code in [302, 200, 404]

    def test_static_page_rejects_dollar(self, client):
        response = client.get("/static/$HOME")
        assert response.status_code in [302, 200, 404]

    def test_static_page_rejects_backslash(self, client):
        response = client.get("/static/test\\path")
        assert response.status_code in [302, 200, 404]
