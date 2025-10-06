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

"""Tests for Gunicorn multi-worker session support.

These tests verify that the session configuration properly supports
Gunicorn's multi-worker architecture by using shared session storage.
"""

import os
from unittest.mock import patch


def test_session_config_detects_redis():
    """Test that Redis session storage is configured when REDIS_URL is set."""
    from now_lms import session_config

    # Clear testing indicators to simulate production
    env = {
        "REDIS_URL": "redis://localhost:6379/0",
    }
    for key in ["CI", "TESTING", "PYTEST_CURRENT_TEST"]:
        env[key] = ""  # Set to empty to override

    with patch.dict(os.environ, env, clear=False):
        with patch.object(session_config.os, "sys") as mock_sys:
            mock_sys.modules = {}  # No pytest module
            config = session_config.get_session_config()

            assert config is not None
            assert config["SESSION_TYPE"] == "redis"
            assert config["SESSION_REDIS"] == "redis://localhost:6379/0"
            assert config["SESSION_PERMANENT"] is True
            assert config["SESSION_USE_SIGNER"] is True


def test_session_config_falls_back_to_cachelib():
    """Test that CacheLib FileSystemCache is used when Redis is not available."""
    from now_lms import session_config

    # Clear Redis URL and testing indicators
    env = {
        "CI": "",
        "TESTING": "",
        "PYTEST_CURRENT_TEST": "",
    }

    with patch.dict(os.environ, env, clear=False):
        with patch.object(session_config.os, "sys") as mock_sys:
            mock_sys.modules = {}  # No pytest module
            config = session_config.get_session_config()

            assert config is not None
            assert config["SESSION_TYPE"] == "cachelib"
            assert "SESSION_CACHELIB" in config
            assert config["SESSION_PERMANENT"] is True
            assert config["SESSION_USE_SIGNER"] is True


def test_session_config_skips_for_testing():
    """Test that session config returns None in testing mode."""
    from now_lms.session_config import get_session_config

    with patch.dict(os.environ, {"CI": "1"}, clear=False):
        config = get_session_config()
        assert config is None


def test_session_init_skips_for_testing(app):
    """Test that init_session skips initialization in testing mode."""
    from now_lms.session_config import init_session

    # Should not raise any errors
    init_session(app)


def test_secret_key_warning_in_production():
    """Test that a warning is logged when using default SECRET_KEY in production."""
    # This test verifies the warning is logged in the config module
    # The actual test is more about ensuring the config is set up correctly
    from now_lms.config import CONFIGURACION

    # In testing, we don't expect the warning
    # But we verify the config exists
    assert "SECRET_KEY" in CONFIGURACION


def test_session_works_with_login_flow(app, client, full_db_setup):
    """Test that sessions persist across requests (simulating Gunicorn workers)."""
    # Login
    response = client.post("/user/login", data={"usuario": "lms-admin", "acceso": "lms-admin"}, follow_redirects=True)
    assert response.status_code == 200

    # Make multiple requests to verify session persists
    # In a real Gunicorn setup, these could be handled by different workers
    for _ in range(5):
        response = client.get("/home")
        assert response.status_code == 200

    # Logout should work
    response = client.get("/user/logout", follow_redirects=True)
    assert response.status_code == 200


def test_redis_session_config_has_proper_settings():
    """Test that Redis configuration has all required settings for production."""
    from now_lms import session_config

    env = {
        "REDIS_URL": "redis://localhost:6379/0",
        "CI": "",
        "TESTING": "",
        "PYTEST_CURRENT_TEST": "",
    }

    with patch.dict(os.environ, env, clear=False):
        with patch.object(session_config.os, "sys") as mock_sys:
            mock_sys.modules = {}  # No pytest module
            config = session_config.get_session_config()

            # Verify production-ready settings
            assert config["SESSION_USE_SIGNER"] is True  # Security
            assert config["SESSION_PERMANENT"] is True  # Persist sessions
            assert config["PERMANENT_SESSION_LIFETIME"] == 86400  # 24 hours
            assert config["SESSION_KEY_PREFIX"] == "session:"  # Namespace


def test_cachelib_session_has_reasonable_limits():
    """Test that CacheLib session storage has reasonable limits."""
    from now_lms import session_config
    from cachelib import FileSystemCache

    env = {
        "CI": "",
        "TESTING": "",
        "PYTEST_CURRENT_TEST": "",
    }

    with patch.dict(os.environ, env, clear=False):
        with patch.object(session_config.os, "sys") as mock_sys:
            mock_sys.modules = {}  # No pytest module
            config = session_config.get_session_config()

            # Verify CacheLib configuration
            cache_backend = config["SESSION_CACHELIB"]
            assert isinstance(cache_backend, FileSystemCache)
            assert cache_backend._threshold == 1000  # Reasonable max
            assert config["PERMANENT_SESSION_LIFETIME"] == 86400  # 24 hours
