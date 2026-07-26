# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""
Tests validating that security headers are applied correctly to responses.
"""

from unittest.mock import patch


def test_standard_security_headers(client):
    """Verify that standard HTTP security headers are set on responses."""
    response = client.get("/")

    # Check X-Frame-Options
    assert response.headers.get("X-Frame-Options") == "SAMEORIGIN"

    # Check X-Content-Type-Options
    assert response.headers.get("X-Content-Type-Options") == "nosniff"

    # Check X-XSS-Protection
    assert response.headers.get("X-XSS-Protection") == "1; mode=block"

    # Check Referrer-Policy
    assert response.headers.get("Referrer-Policy") == "no-referrer-when-downgrade"

    # Check Content-Security-Policy
    assert "default-src 'self'" in response.headers.get("Content-Security-Policy", "")


def test_hsts_header_when_force_https(client, app):
    """Verify that Strict-Transport-Security is present when FORCE_HTTPS is enabled."""
    with patch.dict(app.config, {"FORCE_HTTPS": True}):
        # Mock request is secure or config FORCE_HTTPS is true.
        # Since we patched app.config["FORCE_HTTPS"] to True, HSTS header should be added.
        response = client.get("/")
        assert response.headers.get("Strict-Transport-Security") == "max-age=31536000; includeSubDomains"


def test_hsts_header_not_present_by_default(client):
    """Verify HSTS header is not present by default under HTTP test mode."""
    response = client.get("/")
    assert "Strict-Transport-Security" not in response.headers
