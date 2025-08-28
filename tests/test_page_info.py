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

"""Tests for page_info view."""

import os
from unittest.mock import patch


def test_page_info_without_ci_env_redirects_to_home(session_basic_db_setup):
    """Test that page_info redirects to home when CI environment variable is not set."""
    app = session_basic_db_setup

    with app.test_client() as client:
        # Ensure CI is not set
        with patch.dict(os.environ, {}, clear=False):
            if "CI" in os.environ:
                del os.environ["CI"]

            response = client.get("/page_info")
            assert response.status_code == 302
            assert response.location.endswith("/")


def test_page_info_with_ci_env_returns_200(session_basic_db_setup):
    """Test that page_info returns 200 when CI environment variable is set."""
    app = session_basic_db_setup

    with app.test_client() as client:
        # Set CI environment variable
        with patch.dict(os.environ, {"CI": "1"}):
            response = client.get("/page_info")
            assert response.status_code == 200
            assert b"Development Information" in response.data
            assert b"CI Environment Only" in response.data


def test_page_info_content_structure(session_basic_db_setup):
    """Test that page_info displays expected information sections."""
    app = session_basic_db_setup

    with app.test_client() as client:
        with patch.dict(os.environ, {"CI": "true"}):
            response = client.get("/page_info")
            assert response.status_code == 200

            # Check for main content sections
            assert b"Application" in response.data
            assert b"System" in response.data
            assert b"Configuration" in response.data
            assert b"LMS Statistics" in response.data
            assert b"Environment Variables" in response.data
            assert b"Routes" in response.data

            # Check for specific information
            assert b"Version" in response.data
            assert b"Python Version" in response.data
            assert b"Database Engine" in response.data


def test_page_info_filters_sensitive_env_vars(session_basic_db_setup):
    """Test that page_info filters out sensitive environment variables."""
    app = session_basic_db_setup

    test_env = {
        "CI": "1",
        "SECRET_KEY": "secret_value",
        "DATABASE_URL": "sqlite:///:memory:",
        "API_KEY": "api_secret",
        "SAFE_VAR": "safe_value",
        "PASSWORD": "password123",
    }

    with app.test_client() as client:
        # Temporarily disable debug toolbar for this test
        with app.app_context():
            original_debug_enabled = app.config.get("DEBUG_TB_ENABLED", True)
            app.config["DEBUG_TB_ENABLED"] = False
            app.config["DEBUG_TB_INTERCEPT_REDIRECTS"] = False
            try:
                with patch.dict(os.environ, test_env, clear=False):
                    response = client.get("/page_info")
                    assert response.status_code == 200

                    response_text = response.data.decode("utf-8")

                    # Extract only the main content, excluding debug toolbar content
                    if "flDebuggPanel" in response_text:
                        # Split at debug toolbar content and only check the main content
                        main_content = response_text.split("flDebuggPanel")[0]
                    else:
                        main_content = response_text

                    # Should include safe variables
                    assert "SAFE_VAR" in main_content
                    assert "safe_value" in main_content

                    # Should exclude sensitive variables from main content
                    assert "SECRET_KEY" not in main_content
                    assert "secret_value" not in main_content
                    assert "DATABASE_URL" not in main_content
                    assert "API_KEY" not in main_content
                    assert "PASSWORD" not in main_content
            finally:
                # Restore original debug toolbar setting
                app.config["DEBUG_TB_ENABLED"] = original_debug_enabled


def test_page_info_ci_values(session_basic_db_setup):
    """Test that various CI environment variable values work."""
    app = session_basic_db_setup

    with app.test_client() as client:
        # Test different truthy values for CI
        ci_values = ["1", "true", "yes", "on", "development", "dev"]

        for ci_value in ci_values:
            with patch.dict(os.environ, {"CI": ci_value}):
                response = client.get("/page_info")
                assert response.status_code == 200, f"Failed for CI={ci_value}"

        # Test falsy values
        falsy_values = ["0", "false", "no", "off", ""]

        for ci_value in falsy_values:
            with patch.dict(os.environ, {"CI": ci_value}, clear=True):
                response = client.get("/page_info")
                assert response.status_code == 302, f"Should redirect for CI={ci_value}"
                assert response.location.endswith("/"), f"Should redirect to home for CI={ci_value}"
