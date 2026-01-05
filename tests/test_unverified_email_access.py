# Copyright 2026 BMO Soluciones, S.A.
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

"""Tests for configurable restricted access for unverified email users."""

import pytest
from flask import url_for

from now_lms.auth import proteger_passwd, usuario_requiere_verificacion_email
from now_lms.db import Configuracion, Usuario, database


class TestUnverifiedEmailAccess:
    """Test suite for unverified email access configuration."""

    def test_allow_unverified_email_login_field_exists(self, isolated_db_session):
        """Test that allow_unverified_email_login field exists in Configuracion model."""
        # Get or create configuration
        config = isolated_db_session.execute(database.select(Configuracion)).scalar_one_or_none()

        # Field should exist and be accessible
        assert hasattr(config, "allow_unverified_email_login")

        # Default value should be False for backward compatibility
        assert config.allow_unverified_email_login is False

    def test_usuario_requiere_verificacion_email_not_authenticated(self, app):
        """Test that function returns False when user is not authenticated."""
        with app.test_request_context():
            result = usuario_requiere_verificacion_email()
            assert result is False

    def test_usuario_requiere_verificacion_email_verified_email(self, app, session_full_db_setup):
        """Test that function returns False when user has verified email."""
        from flask_login import login_user

        with app.app_context():
            # Create user with verified email
            hashed_password = proteger_passwd("test123")
            user = Usuario(
                usuario="verified_user_test",
                acceso=hashed_password,
                nombre="Verified",
                apellido="User",
                correo_electronico="verified_test@example.com",
                correo_electronico_verificado=True,
                tipo="student",
                activo=True,
            )
            database.session.add(user)
            database.session.commit()

            with app.test_request_context():
                # Reload user from database
                user = database.session.execute(database.select(Usuario).filter_by(usuario="verified_user_test")).scalar_one()
                login_user(user)
                result = usuario_requiere_verificacion_email()
                assert result is False

    def test_usuario_requiere_verificacion_email_unverified_with_config_disabled(self, app, session_full_db_setup):
        """Test that function returns False when config options are disabled."""
        from flask_login import login_user

        with app.app_context():
            # Create user with unverified email
            hashed_password = proteger_passwd("test123")
            user = Usuario(
                usuario="unverified_user_disabled",
                acceso=hashed_password,
                nombre="Unverified",
                apellido="User",
                correo_electronico="unverified_disabled@example.com",
                correo_electronico_verificado=False,
                tipo="student",
                activo=True,
            )
            database.session.add(user)

            # Ensure config has both options disabled
            config = database.session.execute(database.select(Configuracion)).scalar_one_or_none()
            if config:
                config.verify_user_by_email = False
                config.allow_unverified_email_login = False

            database.session.commit()

            with app.test_request_context():
                # Reload user from database
                user = database.session.execute(
                    database.select(Usuario).filter_by(usuario="unverified_user_disabled")
                ).scalar_one()
                login_user(user)
                result = usuario_requiere_verificacion_email()
                assert result is False

    def test_usuario_requiere_verificacion_email_unverified_with_verify_enabled(self, app, session_full_db_setup):
        """Test that function returns True when verify_user_by_email is enabled."""
        from flask_login import login_user

        with app.app_context():
            # Get or create config
            config = database.session.execute(database.select(Configuracion)).scalar_one_or_none()
            if not config:
                # Create config if it doesn't exist
                from os import urandom

                config = Configuracion(
                    titulo="Test LMS",
                    descripcion="Test Description",
                    moneda="USD",
                    r=urandom(16),
                )
                database.session.add(config)
                database.session.flush()

            # Enable verification requirement
            config.verify_user_by_email = True
            config.allow_unverified_email_login = False
            database.session.commit()

            # Create user with unverified email
            hashed_password = proteger_passwd("test123")
            user = Usuario(
                usuario="unverified_user2_verify",
                acceso=hashed_password,
                nombre="Unverified",
                apellido="User",
                correo_electronico="unverified2_verify@example.com",
                correo_electronico_verificado=False,
                tipo="student",
                activo=True,
            )
            database.session.add(user)
            database.session.commit()

            with app.test_request_context():
                # Reload user from database
                user = database.session.execute(
                    database.select(Usuario).filter_by(usuario="unverified_user2_verify")
                ).scalar_one()
                login_user(user)
                result = usuario_requiere_verificacion_email()
                assert result is True

    def test_usuario_requiere_verificacion_email_unverified_with_restricted_access_enabled(self, app, session_full_db_setup):
        """Test that function returns True when allow_unverified_email_login is enabled."""
        from flask_login import login_user

        with app.app_context():
            # Get or create config
            config = database.session.execute(database.select(Configuracion)).scalar_one_or_none()
            if not config:
                # Create config if it doesn't exist
                from os import urandom

                config = Configuracion(
                    titulo="Test LMS",
                    descripcion="Test Description",
                    moneda="USD",
                    r=urandom(16),
                )
                database.session.add(config)
                database.session.flush()

            # Enable restricted access for unverified users
            config.verify_user_by_email = False
            config.allow_unverified_email_login = True
            database.session.commit()

            # Create user with unverified email
            hashed_password = proteger_passwd("test123")
            user = Usuario(
                usuario="unverified_user3_restricted",
                acceso=hashed_password,
                nombre="Unverified",
                apellido="User",
                correo_electronico="unverified3_restricted@example.com",
                correo_electronico_verificado=False,
                tipo="student",
                activo=True,
            )
            database.session.add(user)
            database.session.commit()

            with app.test_request_context():
                # Reload user from database
                user = database.session.execute(
                    database.select(Usuario).filter_by(usuario="unverified_user3_restricted")
                ).scalar_one()
                login_user(user)
                result = usuario_requiere_verificacion_email()
                assert result is True

    def test_login_with_unverified_email_config_disabled(self, client, isolated_db_session):
        """Test that login fails for unverified inactive users when config is disabled."""
        # Create inactive user with unverified email
        hashed_password = proteger_passwd("test123")
        user = Usuario(
            usuario="inactive_user",
            acceso=hashed_password,
            nombre="Inactive",
            apellido="User",
            correo_electronico="inactive@example.com",
            correo_electronico_verificado=False,
            tipo="student",
            activo=False,
        )
        isolated_db_session.add(user)

        # Disable the new config option
        config = isolated_db_session.execute(database.select(Configuracion)).scalar_one_or_none()
        if config:
            config.allow_unverified_email_login = False

        isolated_db_session.commit()

        # Try to login
        response = client.post("/user/login", data={"usuario": "inactive_user", "acceso": "test123"}, follow_redirects=True)

        # Should show inactive message
        assert response.status_code == 200
        assert "inactiva" in response.data.decode("utf-8").lower()

    def test_login_with_unverified_email_config_enabled(self, client, isolated_db_session):
        """Test that login succeeds for unverified inactive users when config is enabled."""
        # Create inactive user with unverified email
        hashed_password = proteger_passwd("test123")
        user = Usuario(
            usuario="restricted_user",
            acceso=hashed_password,
            nombre="Restricted",
            apellido="User",
            correo_electronico="restricted@example.com",
            correo_electronico_verificado=False,
            tipo="student",
            activo=False,
        )
        isolated_db_session.add(user)

        # Enable the new config option
        config = isolated_db_session.execute(database.select(Configuracion)).scalar_one_or_none()
        if config:
            config.allow_unverified_email_login = True

        isolated_db_session.commit()

        # Try to login
        response = client.post("/user/login", data={"usuario": "restricted_user", "acceso": "test123"}, follow_redirects=True)

        # Should be successful with warning message
        assert response.status_code == 200
        response_text = response.data.decode("utf-8").lower()
        # Should show warning about unverified email
        assert "correo" in response_text or "email" in response_text or "verificad" in response_text

    def test_config_form_has_new_field(self, app):
        """Test that ConfigForm has the new allow_unverified_email_login field."""
        from now_lms.forms import ConfigForm

        with app.app_context():
            form = ConfigForm()

            # Field should exist
            assert hasattr(form, "allow_unverified_email_login")

    def test_migration_adds_column(self, app, session_full_db_setup):
        """Test that migration adds the column correctly."""
        # This test assumes the migration has been run
        from sqlalchemy import inspect

        with app.app_context():
            inspector = inspect(database.engine)
            columns = [col["name"] for col in inspector.get_columns("configuracion")]

            assert "allow_unverified_email_login" in columns
