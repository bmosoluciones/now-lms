"""
Simplified test suite for demo mode functionality.

Tests the core demo mode functionality without complex database interactions.
"""

import os
from unittest.mock import patch

from now_lms import create_app
from now_lms.demo_mode import (
    check_demo_admin_restriction,
    demo_restriction_check,
    is_demo_mode,
    is_admin_user,
)


class TestDemoModeCore:
    """Test core demo mode functionality."""

    def test_demo_mode_disabled_by_default(self):
        """Test that demo mode is disabled by default."""
        if "NOW_LMS_DEMO_MODE" in os.environ:
            del os.environ["NOW_LMS_DEMO_MODE"]

        assert not is_demo_mode()

    def test_demo_mode_enabled_with_env_var(self):
        """Test that demo mode is enabled when environment variable is set."""
        os.environ["NOW_LMS_DEMO_MODE"] = "1"
        assert is_demo_mode()
        del os.environ["NOW_LMS_DEMO_MODE"]

    def test_is_admin_user_without_context(self):
        """Test that is_admin_user returns False outside request context."""
        assert not is_admin_user()

    @patch("now_lms.demo_mode.current_user")
    def test_is_admin_user_with_admin(self, mock_user):
        """Test that is_admin_user returns True for authenticated admin."""
        mock_user.is_authenticated = True
        mock_user.tipo = "admin"
        assert is_admin_user()

    @patch("now_lms.demo_mode.current_user")
    def test_is_admin_user_with_student(self, mock_user):
        """Test that is_admin_user returns False for student."""
        mock_user.is_authenticated = True
        mock_user.tipo = "student"
        assert not is_admin_user()

    def test_check_demo_admin_restriction_disabled(self):
        """Test that restriction check returns False when demo mode is disabled."""
        if "NOW_LMS_DEMO_MODE" in os.environ:
            del os.environ["NOW_LMS_DEMO_MODE"]

        assert not check_demo_admin_restriction()

    @patch("now_lms.demo_mode.current_user")
    def test_check_demo_admin_restriction_enabled_admin(self, mock_user):
        """Test that restriction check returns True for admin in demo mode."""
        os.environ["NOW_LMS_DEMO_MODE"] = "1"
        mock_user.is_authenticated = True
        mock_user.tipo = "admin"

        assert check_demo_admin_restriction()

        del os.environ["NOW_LMS_DEMO_MODE"]

    @patch("now_lms.demo_mode.current_user")
    def test_check_demo_admin_restriction_enabled_student(self, mock_user):
        """Test that restriction check returns False for student in demo mode."""
        os.environ["NOW_LMS_DEMO_MODE"] = "1"
        mock_user.is_authenticated = True
        mock_user.tipo = "student"

        assert not check_demo_admin_restriction()

        del os.environ["NOW_LMS_DEMO_MODE"]

    @patch("now_lms.demo_mode.current_user")
    @patch("now_lms.demo_mode.flash")
    def test_demo_restriction_check_blocks_admin(self, mock_flash, mock_user):
        """Test that demo_restriction_check blocks admin actions."""
        os.environ["NOW_LMS_DEMO_MODE"] = "1"
        mock_user.is_authenticated = True
        mock_user.tipo = "admin"

        # Should return True (block action) and call flash
        result = demo_restriction_check("test_action")
        assert result is True
        mock_flash.assert_called_once()

        del os.environ["NOW_LMS_DEMO_MODE"]

    @patch("now_lms.demo_mode.current_user")
    @patch("now_lms.demo_mode.flash")
    def test_demo_restriction_check_allows_student(self, mock_flash, mock_user):
        """Test that demo_restriction_check allows student actions."""
        os.environ["NOW_LMS_DEMO_MODE"] = "1"
        mock_user.is_authenticated = True
        mock_user.tipo = "student"

        # Should return False (allow action) and not call flash
        result = demo_restriction_check("test_action")
        assert result is False
        mock_flash.assert_not_called()

        del os.environ["NOW_LMS_DEMO_MODE"]


class TestDemoModeIntegration:
    """Test demo mode integration with Flask app."""

    def test_jinja_global_available(self):
        """Test that demo mode function is available in Jinja2 templates."""
        app = create_app(testing=True)

        with app.app_context():
            # Check that demo_mode function is available in Jinja2 globals
            assert "demo_mode" in app.jinja_env.globals
            assert callable(app.jinja_env.globals["demo_mode"])

    def test_demo_mode_jinja_function_works(self):
        """Test that the Jinja2 demo_mode function works correctly."""
        # Test with demo mode disabled
        if "NOW_LMS_DEMO_MODE" in os.environ:
            del os.environ["NOW_LMS_DEMO_MODE"]

        app = create_app(testing=True)

        with app.app_context():
            demo_mode_func = app.jinja_env.globals["demo_mode"]
            assert not demo_mode_func()

        # Test with demo mode enabled
        os.environ["NOW_LMS_DEMO_MODE"] = "1"
        app = create_app(testing=True)

        with app.app_context():
            demo_mode_func = app.jinja_env.globals["demo_mode"]
            assert demo_mode_func()

        del os.environ["NOW_LMS_DEMO_MODE"]


class TestDemoModeEnvironmentVariableSupport:
    """Test various environment variable formats for demo mode."""

    def test_truthy_values(self):
        """Test that various truthy values enable demo mode."""
        truthy_values = ["1", "true", "yes", "on", "True", "TRUE", "YES", "ON"]

        for value in truthy_values:
            os.environ["NOW_LMS_DEMO_MODE"] = value
            assert is_demo_mode(), f"Demo mode should be enabled with value: {value}"

        del os.environ["NOW_LMS_DEMO_MODE"]

    def test_falsy_values(self):
        """Test that various falsy values disable demo mode."""
        falsy_values = ["0", "false", "no", "off", "False", "FALSE", "NO", "OFF", ""]

        for value in falsy_values:
            os.environ["NOW_LMS_DEMO_MODE"] = value
            assert not is_demo_mode(), f"Demo mode should be disabled with value: {value}"

        del os.environ["NOW_LMS_DEMO_MODE"]

    def test_undefined_variable(self):
        """Test that undefined environment variable disables demo mode."""
        if "NOW_LMS_DEMO_MODE" in os.environ:
            del os.environ["NOW_LMS_DEMO_MODE"]

        assert not is_demo_mode()


# Additional test to verify the demo mode configuration constant works
def test_demo_mode_config_constant():
    """Test that the DEMO_MODE config constant is properly set."""
    from now_lms.config import DEMO_MODE

    # Test with demo mode disabled
    if "NOW_LMS_DEMO_MODE" in os.environ:
        del os.environ["NOW_LMS_DEMO_MODE"]

    # The constant is set at import time, so we need to reload the module
    # to test different values. For this test, we'll just check that it exists.
    assert isinstance(DEMO_MODE, bool)
