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

"""
Tests for email verification route `/user/check_mail/<token>`.

This module provides comprehensive testing for the email verification endpoint,
covering various token scenarios including valid tokens, invalid tokens,
expired tokens, and edge cases.
"""

import jwt
from datetime import datetime, timedelta, timezone


class TestEmailVerificationRoute:
    """Test the /user/check_mail/<token> route functionality."""

    def test_check_mail_with_valid_token(self, basic_config_setup):
        """Test email verification with a valid token."""
        from now_lms.auth import generate_confirmation_token, proteger_passwd
        from now_lms.db import Usuario, database

        app = basic_config_setup
        client = app.test_client()

        with app.app_context():
            # Create a test user
            user = Usuario(
                usuario="testuser",
                correo_electronico="test@example.com",
                acceso=proteger_passwd("password123"),
                nombre="Test",
                apellido="User",
                tipo="student",
                activo=False,  # User starts inactive
                correo_electronico_verificado=False,  # Email not verified
                creado_por="system",
            )
            database.session.add(user)
            database.session.commit()

            # Generate a valid confirmation token
            token = generate_confirmation_token("test@example.com")

        # Test the route with valid token
        response = client.get(f"/user/check_mail/{token}", follow_redirects=True)

        assert response.status_code == 200
        # Should redirect to login page with success message
        assert "Correo verificado exitosamente".encode("utf-8") in response.data

        # Verify user is now active and email verified
        with app.app_context():
            updated_user = database.session.execute(
                database.select(Usuario).filter_by(correo_electronico="test@example.com")
            ).first()[0]
            assert updated_user.activo is True
            assert updated_user.correo_electronico_verificado is True

    def test_check_mail_with_invalid_token(self, basic_config_setup):
        """Test email verification with an invalid token."""
        app = basic_config_setup
        client = app.test_client()

        # Test with completely invalid token
        response = client.get("/user/check_mail/invalid_token", follow_redirects=True)

        assert response.status_code == 200
        # Should redirect to logout with warning message
        assert "Token de verificación invalido".encode("utf-8") in response.data

    def test_check_mail_with_expired_token(self, basic_config_setup):
        """Test email verification with an expired token."""
        from now_lms.auth import proteger_passwd
        from now_lms.db import Usuario, database

        app = basic_config_setup
        client = app.test_client()

        with app.app_context():
            # Create a test user
            user = Usuario(
                usuario="expireduser",
                correo_electronico="expired@example.com",
                acceso=proteger_passwd("password123"),
                nombre="Expired",
                apellido="User",
                tipo="student",
                activo=False,
                correo_electronico_verificado=False,
                creado_por="system",
            )
            database.session.add(user)
            database.session.commit()

            # Create an expired token manually
            expired_time = datetime.now(timezone.utc) - timedelta(hours=1)  # 1 hour ago
            data = {"exp": expired_time, "confirm_id": "expired@example.com"}
            expired_token = jwt.encode(data, app.secret_key, algorithm="HS512")

        # Test the route with expired token
        response = client.get(f"/user/check_mail/{expired_token}", follow_redirects=True)

        assert response.status_code == 200
        # Should redirect to logout with warning message
        assert "Token de verificación invalido".encode("utf-8") in response.data

        # Verify user remains inactive
        with app.app_context():
            user_check = database.session.execute(
                database.select(Usuario).filter_by(correo_electronico="expired@example.com")
            ).first()[0]
            assert user_check.activo is False
            assert user_check.correo_electronico_verificado is False

    def test_check_mail_with_wrong_signature(self, basic_config_setup):
        """Test email verification with a token signed with wrong secret."""
        from now_lms.auth import proteger_passwd
        from now_lms.db import Usuario, database

        app = basic_config_setup
        client = app.test_client()

        with app.app_context():
            # Create a test user
            user = Usuario(
                usuario="wrongsiguser",
                correo_electronico="wrongsig@example.com",
                acceso=proteger_passwd("password123"),
                nombre="Wrong",
                apellido="Signature",
                tipo="student",
                activo=False,
                correo_electronico_verificado=False,
                creado_por="system",
            )
            database.session.add(user)
            database.session.commit()

            # Create a token with wrong secret
            data = {"confirm_id": "wrongsig@example.com"}
            wrong_token = jwt.encode(data, "wrong_secret", algorithm="HS512")

        # Test the route with wrong signature token
        response = client.get(f"/user/check_mail/{wrong_token}", follow_redirects=True)

        assert response.status_code == 200
        # Should redirect to logout with warning message
        assert "Token de verificación invalido".encode("utf-8") in response.data

        # Verify user remains inactive
        with app.app_context():
            user_check = database.session.execute(
                database.select(Usuario).filter_by(correo_electronico="wrongsig@example.com")
            ).first()[0]
            assert user_check.activo is False
            assert user_check.correo_electronico_verificado is False

    def test_check_mail_with_missing_confirm_id(self, basic_config_setup):
        """Test email verification with a token missing confirm_id field."""
        app = basic_config_setup
        client = app.test_client()

        with app.app_context():
            # Create a token without confirm_id field
            data = {"other_field": "some_value"}
            token_no_id = jwt.encode(data, app.secret_key, algorithm="HS512")

        # Test the route with token missing confirm_id
        response = client.get(f"/user/check_mail/{token_no_id}", follow_redirects=True)

        assert response.status_code == 200
        # Should redirect to logout with warning message
        assert "Token de verificación invalido".encode("utf-8") in response.data

    def test_check_mail_with_nonexistent_user(self, basic_config_setup):
        """Test email verification with a token for a user that doesn't exist."""
        from now_lms.auth import generate_confirmation_token

        app = basic_config_setup
        client = app.test_client()

        with app.app_context():
            # Generate token for non-existent user
            token = generate_confirmation_token("nonexistent@example.com")

        # Test the route with token for non-existent user
        response = client.get(f"/user/check_mail/{token}", follow_redirects=True)

        assert response.status_code == 200
        # Should redirect to logout with warning message
        assert "Token de verificación invalido".encode("utf-8") in response.data

    def test_check_mail_route_without_token(self, basic_config_setup):
        """Test the route behavior when accessed without a token parameter."""
        app = basic_config_setup
        client = app.test_client()

        # Test accessing the route without token path - should result in 404
        response = client.get("/user/check_mail/")
        assert response.status_code == 404

        # Test accessing the route without token - redirects (handled by global error handler)
        response = client.get("/user/check_mail")
        assert response.status_code == 302  # Redirects to login due to global error handling
