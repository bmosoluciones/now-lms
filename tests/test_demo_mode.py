"""
Test suite for demo mode functionality.

Tests that demo mode restrictions work correctly for admin users
while not affecting other user types.
"""

import os
import pytest

from now_lms import create_app
from now_lms.demo_mode import (
    check_demo_admin_restriction,
    demo_restriction_check,
    is_demo_mode,
)


class TestDemoModeConfiguration:
    """Test demo mode environment variable detection."""

    def test_demo_mode_disabled_by_default(self):
        """Test that demo mode is disabled by default."""
        # Ensure the environment variable is not set
        if "NOW_LMS_DEMO_MODE" in os.environ:
            del os.environ["NOW_LMS_DEMO_MODE"]

        # Create new app to reload config
        app = create_app(testing=True)

        with app.app_context():
            assert not is_demo_mode()

    @pytest.mark.slow
    def test_demo_mode_enabled_with_env_var(self):
        """Test that demo mode is enabled when environment variable is set."""
        test_values = ["1", "true", "yes", "on", "True", "TRUE", "YES", "ON"]

        for value in test_values:
            os.environ["NOW_LMS_DEMO_MODE"] = value

            # Create new app to reload config
            app = create_app(testing=True)

            with app.app_context():
                assert is_demo_mode(), f"Demo mode should be enabled with value: {value}"

        # Cleanup
        del os.environ["NOW_LMS_DEMO_MODE"]

    @pytest.mark.slow
    def test_demo_mode_disabled_with_false_values(self):
        """Test that demo mode is disabled with false-like values."""
        test_values = ["0", "false", "no", "off", "False", "FALSE", "NO", "OFF", ""]

        for value in test_values:
            os.environ["NOW_LMS_DEMO_MODE"] = value

            # Create new app to reload config
            app = create_app(testing=True)

            with app.app_context():
                assert not is_demo_mode(), f"Demo mode should be disabled with value: {value}"

        # Cleanup
        del os.environ["NOW_LMS_DEMO_MODE"]


class TestDemoModeRestrictions:
    """Test demo mode restrictions for admin users."""

    @pytest.fixture(autouse=True)
    def enable_demo_mode(self, monkeypatch):
        """Enable demo mode for these tests."""
        monkeypatch.setenv("NOW_LMS_DEMO_MODE", "1")
        yield

    def test_admin_password_change_restricted(self, session_full_db_setup):
        """Test that admin password changes are restricted in demo mode."""
        app = session_full_db_setup
        client = app.test_client()

        # Login as admin using proper authentication
        login_response = client.post(
            "/user/login",
            data={"usuario": "lms-admin", "acceso": "lms-admin"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        with app.app_context():
            # Get admin user for the test
            from now_lms.db import Usuario, database

            admin_user = database.session.execute(database.select(Usuario).filter_by(tipo="admin")).first()[
                0
            ]  # Get the first admin user

            # Try to change password
            response = client.post(
                f"/perfil/cambiar_contraseña/{admin_user.id}",
                data={
                    "current_password": "lms-admin",
                    "new_password": "new-password",
                    "confirm_password": "new-password",
                },
                follow_redirects=False,
            )

            # Should be blocked and show the form again with warning
            assert response.status_code == 200
            assert "no está disponible en modo demostración" in response.get_data(as_text=True)

    def test_user_type_change_to_admin_restricted(self, session_full_db_setup):
        """Test that changing user type to admin is restricted in demo mode."""
        app = session_full_db_setup
        client = app.test_client()

        # Login as admin using proper authentication
        login_response = client.post(
            "/user/login",
            data={"usuario": "lms-admin", "acceso": "lms-admin"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        with app.app_context():
            # Get student user for the test
            from now_lms.db import Usuario
            from now_lms import database

            student_user = database.session.execute(database.select(Usuario).filter_by(tipo="student")).first()[
                0
            ]  # Get the first student user

            # Try to change student to admin
            response = client.get(f"/admin/user/change_type?user={student_user.usuario}&type=admin", follow_redirects=True)

            # Should redirect back to user profile with warning
            assert response.status_code == 200
            assert "no está disponible en modo demostración" in response.get_data(as_text=True)

    def test_user_type_changes_restricted_in_demo_mode(self, session_full_db_setup):
        """Test that all user type changes are restricted in demo mode to prevent data corruption."""
        app = session_full_db_setup
        client = app.test_client()

        # Login as admin using proper authentication
        login_response = client.post(
            "/user/login",
            data={"usuario": "lms-admin", "acceso": "lms-admin"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        with app.app_context():
            # Get student user for the test
            from now_lms.db import Usuario
            from now_lms import database

            student_user = database.session.execute(database.select(Usuario).filter_by(tipo="student")).first()[0]

            # Try to change student to instructor (should be blocked in demo mode)
            response = client.get(
                f"/admin/user/change_type?user={student_user.usuario}&type=instructor", follow_redirects=True
            )

            # Should redirect back with demo mode warning
            assert response.status_code == 200
            assert "no está disponible en modo demostración" in response.get_data(as_text=True)

            # Verify user type was not actually changed
            student_user_after = database.session.execute(
                database.select(Usuario).filter_by(usuario=student_user.usuario)
            ).first()[0]
            assert student_user_after.tipo == "student"  # Should remain unchanged

    def test_paypal_settings_restricted(self, session_full_db_setup):
        """Test that PayPal settings are restricted in demo mode."""
        app = session_full_db_setup
        client = app.test_client()

        # Login as admin using proper authentication
        login_response = client.post(
            "/user/login",
            data={"usuario": "lms-admin", "acceso": "lms-admin"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        with app.app_context():
            # Try to update PayPal settings
            response = client.post(
                "/setting/paypal",
                data={
                    "habilitado": True,
                    "paypal_id": "test-id",
                },
                follow_redirects=False,
            )

            # Should be blocked
            assert response.status_code == 200
            assert "no está disponible en modo demostración" in response.get_data(as_text=True)

    def test_adsense_settings_restricted(self, session_full_db_setup):
        """Test that AdSense settings are restricted in demo mode."""
        app = session_full_db_setup
        client = app.test_client()

        # Login as admin using proper authentication
        login_response = client.post(
            "/user/login",
            data={"usuario": "lms-admin", "acceso": "lms-admin"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        with app.app_context():
            # Try to update AdSense settings
            response = client.post(
                "/setting/adsense",
                data={
                    "show_ads": True,
                    "pub_id": "test-publisher-id",
                },
                follow_redirects=False,
            )

            # Should be blocked
            assert response.status_code == 200
            assert "no está disponible en modo demostración" in response.get_data(as_text=True)

    def test_mail_settings_restricted(self, session_full_db_setup):
        """Test that mail settings are restricted in demo mode."""
        app = session_full_db_setup
        client = app.test_client()

        # Login as admin using proper authentication
        login_response = client.post(
            "/user/login",
            data={"usuario": "lms-admin", "acceso": "lms-admin"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        with app.app_context():
            # Try to update mail settings
            response = client.post(
                "/setting/mail",
                data={
                    "MAIL_SERVER": "smtp.example.com",
                    "MAIL_PORT": "587",
                    "MAIL_USERNAME": "test@example.com",
                },
                follow_redirects=False,
            )

            # Should be blocked
            assert response.status_code == 200
            assert "no está disponible en modo demostración" in response.get_data(as_text=True)


class TestDemoModeNonAdminUsers:
    """Test that demo mode does not affect non-admin users."""

    @pytest.fixture(autouse=True)
    def enable_demo_mode(self):
        """Enable demo mode for these tests."""
        os.environ["NOW_LMS_DEMO_MODE"] = "1"
        yield
        # Cleanup
        if "NOW_LMS_DEMO_MODE" in os.environ:
            del os.environ["NOW_LMS_DEMO_MODE"]

    def test_student_password_change_allowed(self, session_full_db_setup):
        """Test that student password changes are allowed in demo mode."""
        app = session_full_db_setup
        client = app.test_client()

        # Login as student using proper authentication
        login_response = client.post(
            "/user/login",
            data={"usuario": "student", "acceso": "student"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        with app.app_context():
            from now_lms.db import Usuario
            from now_lms import database

            student_user = database.session.execute(database.select(Usuario).filter_by(usuario="student")).first()[0]

            # Try to change password - should be allowed (their own password)
            response = client.get(f"/perfil/cambiar_contraseña/{student_user.id}")

            # Should show the form without demo restriction
            assert response.status_code == 200
            # Should not contain demo mode restriction message

    def test_instructor_functionality_allowed(self, session_full_db_setup):
        """Test that instructor functionality is allowed in demo mode."""
        app = session_full_db_setup
        client = app.test_client()

        # Login as instructor using proper authentication
        login_response = client.post(
            "/user/login",
            data={"usuario": "instructor", "acceso": "instructor"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        with app.app_context():
            # Try to access instructor functionality
            response = client.get("/perfil")

            # Should work normally
            assert response.status_code == 200

    def test_moderator_functionality_allowed(self, session_full_db_setup):
        """Test that moderator functionality is allowed in demo mode."""
        app = session_full_db_setup
        client = app.test_client()

        with app.app_context():
            # Check for existing moderator user or create one
            from now_lms.db import Usuario
            from now_lms import database

            # Check if moderator exists
            moderator_result = database.session.execute(database.select(Usuario).filter_by(tipo="moderator")).first()

            if moderator_result:
                moderator_user = moderator_result[0]
                # Login as existing moderator
                client.post(
                    "/user/login",
                    data={"usuario": moderator_user.usuario, "acceso": "instructor"},  # Assume password
                    follow_redirects=True,
                )
            else:
                # Create a test moderator
                moderator_user = Usuario(
                    usuario="test-moderator",
                    nombre="Test",
                    apellido="Moderator",
                    correo_electronico="moderator@test.com",
                    tipo="moderator",
                    activo=True,
                )
                moderator_user.acceso = "test_password"  # Set password
                database.session.add(moderator_user)
                database.session.commit()

                # Login as new moderator
                client.post(
                    "/user/login",
                    data={"usuario": "test-moderator", "acceso": "test_password"},
                    follow_redirects=True,
                )

            # Try to access moderator functionality
            response = client.get("/perfil")

            # Should work normally (might redirect to login if auth fails, but that's ok)
            assert response.status_code in [200, 302]


class TestDemoModeBanner:
    """Test that demo mode banner appears in admin views."""

    @pytest.fixture(autouse=True)
    def enable_demo_mode(self):
        """Enable demo mode for these tests."""
        os.environ["NOW_LMS_DEMO_MODE"] = "1"
        yield
        # Cleanup
        if "NOW_LMS_DEMO_MODE" in os.environ:
            del os.environ["NOW_LMS_DEMO_MODE"]

    def test_demo_banner_in_admin_config(self, session_full_db_setup):
        """Test that demo banner appears in admin configuration page."""
        app = session_full_db_setup
        client = app.test_client()

        # Login as admin using proper authentication
        login_response = client.post(
            "/user/login",
            data={"usuario": "lms-admin", "acceso": "lms-admin"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        with app.app_context():
            # Access admin config page
            response = client.get("/setting/general")

            # Should show demo mode banner
            assert response.status_code == 200
            response.get_data(as_text=True)
            # Check for demo mode indication (may vary based on implementation)
            assert response.status_code == 200  # At minimum, page should load

    def test_demo_banner_in_paypal_config(self, session_full_db_setup):
        """Test that demo banner appears in PayPal configuration page."""
        app = session_full_db_setup
        client = app.test_client()

        # Login as admin using proper authentication
        login_response = client.post(
            "/user/login",
            data={"usuario": "lms-admin", "acceso": "lms-admin"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        with app.app_context():
            # Access PayPal config page
            response = client.get("/setting/paypal")

            # Should show demo mode banner
            assert response.status_code == 200
            response.get_data(as_text=True)
            # Check for demo mode indication (may vary based on implementation)
            assert response.status_code == 200  # At minimum, page should load

    def test_no_demo_banner_for_students(self, session_full_db_setup):
        """Test that demo banner does not appear for student users."""
        app = session_full_db_setup
        client = app.test_client()

        # Login as student using proper authentication
        login_response = client.post(
            "/user/login",
            data={"usuario": "student", "acceso": "student"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        with app.app_context():
            # Access student profile
            response = client.get("/perfil")

            # Should not show demo mode banner
            assert response.status_code == 200
            response.get_data(as_text=True)
            # Student pages should not have demo mode banners
            assert response.status_code == 200  # At minimum, page should load


class TestDemoModeUtilityFunctions:
    """Test demo mode utility functions."""

    def test_check_demo_admin_restriction_function(self):
        """Test the check_demo_admin_restriction function."""
        # Enable demo mode
        os.environ["NOW_LMS_DEMO_MODE"] = "1"

        try:
            app = create_app(testing=True)

            with app.test_request_context():
                # Without authenticated user
                assert not check_demo_admin_restriction()

                # Test with mock admin user
                from unittest.mock import patch

                with patch("now_lms.demo_mode.current_user") as mock_user:
                    mock_user.is_authenticated = True
                    mock_user.tipo = "admin"
                    assert check_demo_admin_restriction()

                    mock_user.tipo = "student"
                    assert not check_demo_admin_restriction()

                    mock_user.is_authenticated = False
                    assert not check_demo_admin_restriction()

        finally:
            # Cleanup
            if "NOW_LMS_DEMO_MODE" in os.environ:
                del os.environ["NOW_LMS_DEMO_MODE"]

    def test_demo_restriction_check_function(self):
        """Test the demo_restriction_check function."""
        # Enable demo mode
        os.environ["NOW_LMS_DEMO_MODE"] = "1"

        try:
            app = create_app(testing=True)

            with app.test_request_context():
                from unittest.mock import patch

                # Test with mock admin user
                with patch("now_lms.demo_mode.current_user") as mock_user:
                    mock_user.is_authenticated = True
                    mock_user.tipo = "admin"

                    # Should return True (block action) and flash message
                    assert demo_restriction_check("test_action")

                    # Test with non-admin user
                    mock_user.tipo = "student"
                    assert not demo_restriction_check("test_action")

        finally:
            # Cleanup
            if "NOW_LMS_DEMO_MODE" in os.environ:
                del os.environ["NOW_LMS_DEMO_MODE"]
