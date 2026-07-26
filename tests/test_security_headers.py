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

    # Check Content-Security-Policy. Third-party sources are explicitly scoped
    # to the integrations the application uses rather than allowing all HTTP(S).
    csp = response.headers.get("Content-Security-Policy", "")
    assert "default-src 'self'" in csp
    assert "object-src 'none'" in csp
    assert "http:" not in csp
    assert "'unsafe-eval'" not in csp
    assert "https://www.paypal.com" in csp
    assert "https://cdnjs.cloudflare.com" in csp


def test_hsts_header_when_force_https(client):
    """Verify that Strict-Transport-Security is present when FORCE_HTTPS is enabled."""
    with patch("now_lms.FORCE_HTTPS", True):
        response = client.get("/")
        assert response.headers.get("Strict-Transport-Security") == "max-age=31536000; includeSubDomains"


def test_hsts_header_when_request_is_secure(client):
    """Verify that HTTPS requests receive HSTS without the force flag."""
    response = client.get("/", base_url="https://localhost.localdomain")
    assert response.headers.get("Strict-Transport-Security") == "max-age=31536000; includeSubDomains"


def test_hsts_header_not_present_by_default(client):
    """Verify HSTS header is not present by default under HTTP test mode."""
    response = client.get("/")
    assert "Strict-Transport-Security" not in response.headers
