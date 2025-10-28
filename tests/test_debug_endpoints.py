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
#

"""Tests for debug endpoints for session troubleshooting."""

import os
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def enable_debug_endpoints(monkeypatch):
    """Enable debug endpoints for testing."""
    monkeypatch.setenv("NOW_LMS_DEBUG_ENDPOINTS", "1")


def test_debug_session_disabled_by_default(client):
    """Test that debug endpoints are disabled by default."""
    response = client.get("/debug/session")
    assert response.status_code == 403
    data = response.get_json()
    assert "error" in data
    assert "not enabled" in data["error"]


def test_debug_session_enabled(client, enable_debug_endpoints, full_db_setup):
    """Test debug session endpoint when enabled."""
    # Login first
    client.post("/user/login", data={"usuario": "lms-admin", "acceso": "lms-admin"}, follow_redirects=True)

    response = client.get("/debug/session")
    assert response.status_code == 200

    data = response.get_json()
    assert "worker" in data
    assert "session_backend" in data
    assert "session_data" in data
    assert "current_user" in data
    assert "authenticated" in data

    # Check worker info
    assert "pid" in data["worker"]
    assert isinstance(data["worker"]["pid"], int)

    # Check user info (should be authenticated)
    assert data["authenticated"] is True
    assert data["current_user"] is not None
    assert data["current_user"]["usuario"] == "lms-admin"


def test_debug_session_anonymous(client, enable_debug_endpoints):
    """Test debug session endpoint for anonymous users."""
    response = client.get("/debug/session")
    assert response.status_code == 200

    data = response.get_json()
    assert data["authenticated"] is False
    assert data["current_user"] is None


def test_debug_session_multiple_calls(client, enable_debug_endpoints, full_db_setup):
    """Test that session data persists across multiple debug calls."""
    # Login first
    client.post("/user/login", data={"usuario": "lms-admin", "acceso": "lms-admin"}, follow_redirects=True)

    # Make multiple requests
    pids = set()
    users = set()

    for _ in range(5):
        response = client.get("/debug/session")
        assert response.status_code == 200

        data = response.get_json()
        pids.add(data["worker"]["pid"])
        if data["current_user"]:
            users.add(data["current_user"]["usuario"])

    # Should have same user across all requests
    assert len(users) == 1
    assert "lms-admin" in users

    # In testing, PID should be the same (single process)
    # In production with multiple workers, PIDs would vary
    assert len(pids) >= 1


def test_debug_config_disabled_by_default(client):
    """Test that debug config endpoint is disabled by default."""
    response = client.get("/debug/config")
    assert response.status_code == 403


def test_debug_config_enabled(client, enable_debug_endpoints):
    """Test debug config endpoint when enabled."""
    response = client.get("/debug/config")
    assert response.status_code == 200

    data = response.get_json()
    assert "config" in data
    assert "environment" in data
    assert "warnings" in data
    assert "recommendations" in data

    # Check config info
    config = data["config"]
    assert "secret_key" in config
    assert "session_type" in config
    assert "session_permanent" in config

    # Secret key should be masked
    assert config["secret_key"] != "test-secret-key-for-testing"
    assert "****" in config["secret_key"] or "..." in config["secret_key"]


def test_debug_config_warnings_for_default_secret(client, enable_debug_endpoints):
    """Test that warnings are shown for default SECRET_KEY."""
    response = client.get("/debug/config")
    assert response.status_code == 200

    data = response.get_json()
    # In testing mode, we use a test secret key
    assert data["config"]["secret_key_is_default"] is True


def test_debug_redis_disabled_by_default(client):
    """Test that debug redis endpoint is disabled by default."""
    response = client.get("/debug/redis")
    assert response.status_code == 403


def test_debug_redis_not_configured(client, enable_debug_endpoints, monkeypatch):
    """Test debug redis endpoint when Redis is not configured."""
    # Clear any Redis URL env vars
    monkeypatch.delenv("REDIS_URL", raising=False)
    monkeypatch.delenv("CACHE_REDIS_URL", raising=False)
    monkeypatch.delenv("SESSION_REDIS_URL", raising=False)

    response = client.get("/debug/redis")
    assert response.status_code == 200

    data = response.get_json()
    assert data["status"] == "not_configured"


def test_debug_redis_configured_but_unavailable(client, enable_debug_endpoints, monkeypatch):
    """Test debug redis endpoint when Redis URL is set but server is unavailable."""
    monkeypatch.setenv("REDIS_URL", "redis://localhost:9999/0")

    response = client.get("/debug/redis")
    assert response.status_code == 503

    data = response.get_json()
    assert data["status"] == "error"
    assert "connection failed" in data["message"].lower()


@patch("redis.from_url")
def test_debug_redis_success(mock_redis_from_url, client, enable_debug_endpoints, monkeypatch):
    """Test debug redis endpoint when Redis is available."""
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")

    # Mock Redis client
    mock_client = MagicMock()
    mock_client.ping.return_value = True
    mock_client.info.return_value = {
        "redis_version": "7.0.0",
        "uptime_in_seconds": 12345,
        "connected_clients": 5,
    }
    mock_client.keys.return_value = [b"session:abc123", b"session:def456"]
    mock_redis_from_url.return_value = mock_client

    response = client.get("/debug/redis")
    assert response.status_code == 200

    data = response.get_json()
    assert data["status"] == "ok"
    assert "stats" in data
    assert data["stats"]["redis_version"] == "7.0.0"
    assert data["session_keys_count"] == 2


def test_debug_session_sanitizes_csrf_tokens(client, enable_debug_endpoints, full_db_setup):
    """Test that CSRF tokens and other sensitive data are hidden."""
    # Login
    client.post("/user/login", data={"usuario": "lms-admin", "acceso": "lms-admin"}, follow_redirects=True)

    response = client.get("/debug/session")
    assert response.status_code == 200

    data = response.get_json()
    session_data = data["session_data"]

    # Any keys starting with underscore should be hidden
    for key, value in session_data.items():
        if key.startswith("_"):
            assert value == "[hidden]"


def test_debug_config_recommendations(client, enable_debug_endpoints):
    """Test that debug config includes helpful recommendations."""
    response = client.get("/debug/config")
    assert response.status_code == 200

    data = response.get_json()
    recommendations = data["recommendations"]

    # Should have recommendations
    assert len(recommendations) > 0

    # Check for key recommendations
    recommendations_text = " ".join(recommendations).lower()
    assert "redis" in recommendations_text
    assert "secret_key" in recommendations_text


def test_is_debug_enabled_function():
    """Test the is_debug_enabled helper function."""
    from now_lms.vistas.debug import is_debug_enabled

    # Test with various values
    with patch.dict(os.environ, {"NOW_LMS_DEBUG_ENDPOINTS": "0"}):
        assert is_debug_enabled() is False

    with patch.dict(os.environ, {"NOW_LMS_DEBUG_ENDPOINTS": "1"}):
        assert is_debug_enabled() is True

    with patch.dict(os.environ, {"NOW_LMS_DEBUG_ENDPOINTS": "true"}):
        assert is_debug_enabled() is True

    with patch.dict(os.environ, {"NOW_LMS_DEBUG_ENDPOINTS": "yes"}):
        assert is_debug_enabled() is True

    with patch.dict(os.environ, {}):
        assert is_debug_enabled() is False


def test_debug_endpoints_work_after_logout(client, enable_debug_endpoints, full_db_setup):
    """Test that debug endpoints work even after logout."""
    # Login
    client.post("/user/login", data={"usuario": "lms-admin", "acceso": "lms-admin"}, follow_redirects=True)

    # Verify logged in
    response = client.get("/debug/session")
    data = response.get_json()
    assert data["authenticated"] is True

    # Logout
    client.get("/user/logout", follow_redirects=True)

    # Debug endpoint should still work (but show anonymous user)
    response = client.get("/debug/session")
    assert response.status_code == 200
    data = response.get_json()
    assert data["authenticated"] is False


def test_debug_config_detects_multi_worker_warnings(client, enable_debug_endpoints, monkeypatch):
    """Test that debug config warns about multi-worker configuration issues."""
    # Simulate multi-worker environment
    monkeypatch.setenv("NOW_LMS_WORKERS", "4")

    response = client.get("/debug/config")
    assert response.status_code == 200

    data = response.get_json()
    warnings = data["warnings"]

    # Should have warnings about session storage
    # (In testing mode, session_type is 'default', so it should warn)
    # At minimum should warn about default secret or session config
    assert len(warnings) > 0
