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

"""Tests for authentication functions that improve coverage."""

from unittest.mock import patch
from now_lms.auth import proteger_passwd, validar_acceso, perfil_requerido
from now_lms.db import Usuario, database


class TestAuthFunctions:
    """Test authentication utility functions."""

    def test_proteger_passwd(self):
        """Test password hashing function."""
        password = "test_password123"
        hashed = proteger_passwd(password)

        # Should return bytes
        assert isinstance(hashed, bytes)
        # Should not be the original password
        assert hashed != password.encode()
        # Should be a reasonable length for argon2 hash
        assert len(hashed) > 50

    def test_proteger_passwd_different_passwords_different_hashes(self):
        """Test that different passwords produce different hashes."""
        password1 = "password123"
        password2 = "password456"

        hash1 = proteger_passwd(password1)
        hash2 = proteger_passwd(password2)

        assert hash1 != hash2

    def test_proteger_passwd_same_password_different_hashes(self):
        """Test that same password produces different hashes (salt effect)."""
        password = "same_password"

        hash1 = proteger_passwd(password)
        hash2 = proteger_passwd(password)

        # Due to salt, same password should produce different hashes
        assert hash1 != hash2

    def test_validar_acceso_valid_user(self, session_basic_db_setup):
        """Test validar_acceso with valid user credentials."""
        app = session_basic_db_setup

        with app.app_context():
            # Create a test user
            hashed_password = proteger_passwd("test123")
            user = Usuario(
                usuario="testuser",
                acceso=hashed_password,
                nombre="Test",
                apellido="User",
                correo_electronico="test@example.com",
                tipo="user",
            )
            database.session.add(user)
            database.session.commit()

            # Test valid access
            result = validar_acceso("testuser", "test123")
            assert result is True

    def test_validar_acceso_invalid_password(self, session_basic_db_setup):
        """Test validar_acceso with invalid password."""
        app = session_basic_db_setup

        with app.app_context():
            # Create a test user
            hashed_password = proteger_passwd("correct_password")
            user = Usuario(
                usuario="testuser2",
                acceso=hashed_password,
                nombre="Test",
                apellido="User",
                correo_electronico="test2@example.com",
                tipo="user",
            )
            database.session.add(user)
            database.session.commit()

            # Test invalid password
            result = validar_acceso("testuser2", "wrong_password")
            assert result is False

    def test_validar_acceso_nonexistent_user(self, session_basic_db_setup):
        """Test validar_acceso with non-existent user."""
        app = session_basic_db_setup

        with app.app_context():
            # Test non-existent user
            result = validar_acceso("nonexistent", "any_password")
            assert result is False

    def test_validar_acceso_updates_last_access(self, session_basic_db_setup):
        """Test that validar_acceso updates last access time."""
        app = session_basic_db_setup

        with app.app_context():
            # Create a test user
            hashed_password = proteger_passwd("test123")
            user = Usuario(
                usuario="testuser3",
                acceso=hashed_password,
                nombre="Test",
                apellido="User",
                correo_electronico="test3@example.com",
                tipo="user",
            )
            database.session.add(user)
            database.session.commit()

            original_last_access = user.ultimo_acceso

            # Validate access
            validar_acceso("testuser3", "test123")

            # Refresh user from database
            database.session.refresh(user)

            # Last access should be updated
            assert user.ultimo_acceso != original_last_access

    @patch("now_lms.auth.current_user")
    def test_perfil_requerido_admin_access(self, mock_current_user):
        """Test that admin users can access any profile-restricted resource."""
        # Mock admin user
        mock_current_user.is_authenticated = True
        mock_current_user.tipo = "admin"
        mock_current_user.usuario = "admin_user"

        @perfil_requerido("instructor")
        def test_function():
            return "success"

        result = test_function()
        assert result == "success"

    @patch("now_lms.auth.current_user")
    def test_perfil_requerido_correct_profile(self, mock_current_user):
        """Test access with correct user profile."""
        # Mock user with correct profile
        mock_current_user.is_authenticated = True
        mock_current_user.tipo = "instructor"
        mock_current_user.usuario = "instructor_user"

        @perfil_requerido("instructor")
        def test_function():
            return "success"

        result = test_function()
        assert result == "success"

    @patch("now_lms.auth.current_user")
    def test_perfil_requerido_multiple_profiles(self, mock_current_user):
        """Test access with multiple allowed profiles."""
        # Mock user with one of the allowed profiles
        mock_current_user.is_authenticated = True
        mock_current_user.tipo = "moderator"
        mock_current_user.usuario = "moderator_user"

        @perfil_requerido(("instructor", "moderator"))
        def test_function():
            return "success"

        result = test_function()
        assert result == "success"

    @patch("now_lms.auth.abort")
    @patch("now_lms.auth.flash")
    @patch("now_lms.auth.current_user")
    def test_perfil_requerido_wrong_profile(self, mock_current_user, mock_flash, mock_abort):
        """Test access denied for wrong profile."""
        # Mock user with wrong profile
        mock_current_user.is_authenticated = True
        mock_current_user.tipo = "user"
        mock_current_user.usuario = "regular_user"

        @perfil_requerido("instructor")
        def test_function():
            return "success"

        test_function()

        # Should flash error message and abort
        mock_flash.assert_called_with("No se encuentra autorizado a acceder al recurso solicitado.", "error")
        mock_abort.assert_called_with(403)

    @patch("now_lms.auth.url_for")
    @patch("now_lms.auth.redirect")
    @patch("now_lms.auth.flash")
    @patch("now_lms.auth.current_user")
    def test_perfil_requerido_not_authenticated(self, mock_current_user, mock_flash, mock_redirect, mock_url_for):
        """Test redirect for unauthenticated user."""
        # Mock unauthenticated user
        mock_current_user.is_authenticated = False
        mock_url_for.return_value = "/user/login"
        mock_redirect.return_value = "redirect_response"

        @perfil_requerido("instructor")
        def test_function():
            return "success"

        result = test_function()

        # Should flash warning and redirect to login
        mock_flash.assert_called_with("Favor iniciar sesión.", "warning")
        mock_url_for.assert_called_with("user.login")
        mock_redirect.assert_called_with("/user/login")
        assert result == "redirect_response"
