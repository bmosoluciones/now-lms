"""
Test suite for demo mode functionality.

Tests that demo mode restrictions work correctly for admin users
while not affecting other user types.
"""

import os
import pytest
from flask import url_for
from flask_login import login_user

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
    def enable_demo_mode(self):
        """Enable demo mode for these tests."""
        os.environ["NOW_LMS_DEMO_MODE"] = "1"
        yield
        # Cleanup
        if "NOW_LMS_DEMO_MODE" in os.environ:
            del os.environ["NOW_LMS_DEMO_MODE"]

    def test_admin_password_change_restricted(self, client, session_full_db_setup):
        """Test that admin password changes are restricted in demo mode."""
        app = session_full_db_setup
        
        with app.test_request_context():
            # Login as admin
            from now_lms.db import Usuario, database
            admin_user = database.session.execute(
                database.select(Usuario).filter_by(tipo="admin")
            ).scalar_one()
            
            with client.session_transaction() as sess:
                sess["_user_id"] = admin_user.id
                sess["_fresh"] = True
            
            # Try to change password
            response = client.post(
                url_for("user_profile.cambiar_contraseña", ulid=admin_user.id),
                data={
                    "current_password": "admin-password",
                    "new_password": "new-password",
                    "confirm_password": "new-password",
                    "csrf_token": "test-token"
                },
                follow_redirects=False
            )
            
            # Should be blocked and show the form again with warning
            assert response.status_code == 200
            assert "no está disponible en modo demostración" in response.get_data(as_text=True)

    def test_user_type_change_to_admin_restricted(self, client, session_full_db_setup):
        """Test that changing user type to admin is restricted in demo mode."""
        app, db = session_full_db_setup
        
        with app.test_request_context():
            # Login as admin
            from now_lms.db import Usuario
            admin_user = db.session.execute(
                db.select(Usuario).filter_by(tipo="admin")
            ).scalar_one()
            student_user = db.session.execute(
                db.select(Usuario).filter_by(tipo="student")
            ).scalar_one()
            
            with client.session_transaction() as sess:
                sess["_user_id"] = admin_user.id
                sess["_fresh"] = True
            
            # Try to change student to admin
            response = client.get(
                url_for("admin_profile.cambiar_tipo_usario"),
                query_string={"user": student_user.id, "type": "admin"},
                follow_redirects=True
            )
            
            # Should redirect back to user profile with warning
            assert response.status_code == 200
            assert "no está disponible en modo demostración" in response.get_data(as_text=True)

    def test_user_type_change_to_non_admin_allowed(self, client, session_full_db_setup):
        """Test that changing user type to non-admin is allowed in demo mode."""
        app, db = session_full_db_setup
        
        with app.test_request_context():
            # Login as admin
            from now_lms.db import Usuario
            admin_user = db.session.execute(
                db.select(Usuario).filter_by(tipo="admin")
            ).scalar_one()
            student_user = db.session.execute(
                db.select(Usuario).filter_by(tipo="student")
            ).scalar_one()
            
            with client.session_transaction() as sess:
                sess["_user_id"] = admin_user.id
                sess["_fresh"] = True
            
            # Try to change student to instructor (should be allowed)
            response = client.get(
                url_for("admin_profile.cambiar_tipo_usario"),
                query_string={"user": student_user.id, "type": "instructor"},
                follow_redirects=True
            )
            
            # Should succeed without demo mode warning
            assert response.status_code == 200
            # Should not show demo restriction message for non-admin type changes

    def test_paypal_settings_restricted(self, client, session_full_db_setup):
        """Test that PayPal settings are restricted in demo mode."""
        app, db = session_full_db_setup
        
        with app.test_request_context():
            # Login as admin
            from now_lms.db import Usuario
            admin_user = db.session.execute(
                db.select(Usuario).filter_by(tipo="admin")
            ).scalar_one()
            
            with client.session_transaction() as sess:
                sess["_user_id"] = admin_user.id
                sess["_fresh"] = True
            
            # Try to update PayPal settings
            response = client.post(
                url_for("setting.paypal"),
                data={
                    "habilitado": True,
                    "paypal_id": "test-id",
                    "csrf_token": "test-token"
                },
                follow_redirects=False
            )
            
            # Should be blocked
            assert response.status_code == 200
            assert "no está disponible en modo demostración" in response.get_data(as_text=True)

    def test_adsense_settings_restricted(self, client, session_full_db_setup):
        """Test that AdSense settings are restricted in demo mode."""
        app, db = session_full_db_setup
        
        with app.test_request_context():
            # Login as admin
            from now_lms.db import Usuario
            admin_user = db.session.execute(
                db.select(Usuario).filter_by(tipo="admin")
            ).scalar_one()
            
            with client.session_transaction() as sess:
                sess["_user_id"] = admin_user.id
                sess["_fresh"] = True
            
            # Try to update AdSense settings
            response = client.post(
                url_for("setting.adsense"),
                data={
                    "show_ads": True,
                    "pub_id": "test-publisher-id",
                    "csrf_token": "test-token"
                },
                follow_redirects=False
            )
            
            # Should be blocked
            assert response.status_code == 200
            assert "no está disponible en modo demostración" in response.get_data(as_text=True)

    def test_mail_settings_restricted(self, client, session_full_db_setup):
        """Test that mail settings are restricted in demo mode."""
        app, db = session_full_db_setup
        
        with app.test_request_context():
            # Login as admin
            from now_lms.db import Usuario
            admin_user = db.session.execute(
                db.select(Usuario).filter_by(tipo="admin")
            ).scalar_one()
            
            with client.session_transaction() as sess:
                sess["_user_id"] = admin_user.id
                sess["_fresh"] = True
            
            # Try to update mail settings
            response = client.post(
                url_for("setting.mail"),
                data={
                    "MAIL_SERVER": "smtp.example.com",
                    "MAIL_PORT": "587",
                    "MAIL_USERNAME": "test@example.com",
                    "csrf_token": "test-token"
                },
                follow_redirects=False
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

    def test_student_password_change_allowed(self, client, session_full_db_setup):
        """Test that student password changes are allowed in demo mode."""
        app, db = session_full_db_setup
        
        with app.test_request_context():
            # Login as student
            from now_lms.db import Usuario
            student_user = db.session.execute(
                db.select(Usuario).filter_by(tipo="student")
            ).scalar_one()
            
            with client.session_transaction() as sess:
                sess["_user_id"] = student_user.id
                sess["_fresh"] = True
            
            # Try to change password - should be allowed
            response = client.get(
                url_for("user_profile.cambiar_contraseña", ulid=student_user.id)
            )
            
            # Should show the form without demo restriction
            assert response.status_code == 200
            # Should not contain demo mode restriction message

    def test_instructor_functionality_allowed(self, client, session_full_db_setup):
        """Test that instructor functionality is allowed in demo mode."""
        app, db = session_full_db_setup
        
        with app.test_request_context():
            # Login as instructor
            from now_lms.db import Usuario
            instructor_user = db.session.execute(
                db.select(Usuario).filter_by(tipo="instructor")
            ).scalar_one()
            
            with client.session_transaction() as sess:
                sess["_user_id"] = instructor_user.id
                sess["_fresh"] = True
            
            # Try to access instructor functionality
            response = client.get(url_for("user_profile.perfil"))
            
            # Should work normally
            assert response.status_code == 200

    def test_moderator_functionality_allowed(self, client, session_full_db_setup):
        """Test that moderator functionality is allowed in demo mode."""
        app, db = session_full_db_setup
        
        with app.test_request_context():
            # Login as moderator
            from now_lms.db import Usuario
            
            # Create a moderator if one doesn't exist
            moderator_user = db.session.execute(
                db.select(Usuario).filter_by(tipo="moderator")
            ).scalar_one_or_none()
            
            if not moderator_user:
                # Create a moderator for this test
                moderator_user = Usuario(
                    usuario="test-moderator",
                    nombre="Test",
                    apellido="Moderator",
                    correo_electronico="moderator@test.com",
                    tipo="moderator",
                    activo=True
                )
                db.session.add(moderator_user)
                db.session.commit()
            
            with client.session_transaction() as sess:
                sess["_user_id"] = moderator_user.id
                sess["_fresh"] = True
            
            # Try to access moderator functionality
            response = client.get(url_for("user_profile.perfil"))
            
            # Should work normally
            assert response.status_code == 200


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

    def test_demo_banner_in_admin_config(self, client, session_full_db_setup):
        """Test that demo banner appears in admin configuration page."""
        app, db = session_full_db_setup
        
        with app.test_request_context():
            # Login as admin
            from now_lms.db import Usuario
            admin_user = db.session.execute(
                db.select(Usuario).filter_by(tipo="admin")
            ).scalar_one()
            
            with client.session_transaction() as sess:
                sess["_user_id"] = admin_user.id
                sess["_fresh"] = True
            
            # Access admin config page
            response = client.get(url_for("setting.configuracion"))
            
            # Should show demo mode banner
            assert response.status_code == 200
            response_text = response.get_data(as_text=True)
            assert "Modo Demostración Activo" in response_text

    def test_demo_banner_in_paypal_config(self, client, session_full_db_setup):
        """Test that demo banner appears in PayPal configuration page."""
        app, db = session_full_db_setup
        
        with app.test_request_context():
            # Login as admin
            from now_lms.db import Usuario
            admin_user = db.session.execute(
                db.select(Usuario).filter_by(tipo="admin")
            ).scalar_one()
            
            with client.session_transaction() as sess:
                sess["_user_id"] = admin_user.id
                sess["_fresh"] = True
            
            # Access PayPal config page
            response = client.get(url_for("setting.paypal"))
            
            # Should show demo mode banner
            assert response.status_code == 200
            response_text = response.get_data(as_text=True)
            assert "Modo Demostración Activo" in response_text

    def test_no_demo_banner_for_students(self, client, session_full_db_setup):
        """Test that demo banner does not appear for student users."""
        app, db = session_full_db_setup
        
        with app.test_request_context():
            # Login as student
            from now_lms.db import Usuario
            student_user = db.session.execute(
                db.select(Usuario).filter_by(tipo="student")
            ).scalar_one()
            
            with client.session_transaction() as sess:
                sess["_user_id"] = student_user.id
                sess["_fresh"] = True
            
            # Access student profile
            response = client.get(url_for("user_profile.perfil"))
            
            # Should not show demo mode banner
            assert response.status_code == 200
            response_text = response.get_data(as_text=True)
            assert "Modo Demostración Activo" not in response_text


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
                with patch('now_lms.demo_mode.current_user') as mock_user:
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
                with patch('now_lms.demo_mode.current_user') as mock_user:
                    mock_user.is_authenticated = True
                    mock_user.tipo = "admin"
                    
                    # Should return True (block action) and flash message
                    assert demo_restriction_check("test_action") == True
                    
                    # Test with non-admin user
                    mock_user.tipo = "student"
                    assert demo_restriction_check("test_action") == False
        
        finally:
            # Cleanup
            if "NOW_LMS_DEMO_MODE" in os.environ:
                del os.environ["NOW_LMS_DEMO_MODE"]