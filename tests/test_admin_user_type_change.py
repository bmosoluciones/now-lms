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

"""Tests for admin user type change functionality."""

import os
from flask import url_for

from now_lms.db import Usuario, database


class TestAdminUserTypeChange:
    """Test admin user type change functionality."""

    def test_admin_users_list_shows_change_type_dropdown(self, session_full_db_setup):
        """Test that admin users list shows change user type dropdown."""
        app = session_full_db_setup
        with app.app_context():
            with app.test_client() as client:
                # Login as admin
                login_response = client.post(
                    "/user/login",
                    data={"usuario": "lms-admin", "acceso": "lms-admin"},
                    follow_redirects=True,
                )
                assert login_response.status_code == 200

                # Access admin users list
                response = client.get("/admin/users/list")
                assert response.status_code == 200

                html_content = response.get_data(as_text=True)

                # Check that change user type dropdown elements are present
                assert "dropdown-toggle" in html_content
                assert "Cambiar Tipo de Usuario" in html_content or "Cambiar Tipo" in html_content
                assert "dropdown-menu" in html_content

    def test_change_user_type_functionality(self, session_full_db_setup):
        """Test the actual user type change functionality."""
        app = session_full_db_setup
        with app.app_context():
            # Create a test user
            test_user = Usuario(
                usuario="test-user-change",
                acceso=b"fake_password",
                nombre="Test",
                apellido="User",
                correo_electronico="test@example.com",
                tipo="user",
                activo=True,
                visible=True,
            )
            database.session.add(test_user)
            database.session.commit()

            with app.test_client() as client:
                # Login as admin
                login_response = client.post(
                    "/user/login",
                    data={"usuario": "lms-admin", "acceso": "lms-admin"},
                    follow_redirects=True,
                )
                assert login_response.status_code == 200

                # Change user type from user to instructor with redirect to list
                response = client.get(
                    url_for(
                        "admin_profile.cambiar_tipo_usario", type="instructor", user="test-user-change", redirect_to="list"
                    ),
                    follow_redirects=True,
                )
                assert response.status_code == 200

                # Verify user type was changed
                updated_user = database.session.execute(
                    database.select(Usuario).where(Usuario.usuario == "test-user-change")
                ).scalar_one()
                assert updated_user.tipo == "instructor"

                # Verify we're redirected back to the users list
                assert b"Lista de usuarios" in response.data or b"Usuarios registrados" in response.data

    def test_change_user_type_demo_mode_blocked(self, session_full_db_setup):
        """Test that user type change is blocked in demo mode."""
        app = session_full_db_setup

        # Enable demo mode
        os.environ["NOW_LMS_DEMO_MODE"] = "1"

        try:
            with app.app_context():
                # Create a test user
                test_user = Usuario(
                    usuario="test-user-demo",
                    acceso=b"fake_password",
                    nombre="Test",
                    apellido="Demo",
                    correo_electronico="demo@example.com",
                    tipo="user",
                    activo=True,
                    visible=True,
                )
                database.session.add(test_user)
                database.session.commit()
                original_type = test_user.tipo

                with app.test_client() as client:
                    # Login as admin
                    login_response = client.post(
                        "/user/login",
                        data={"usuario": "lms-admin", "acceso": "lms-admin"},
                        follow_redirects=True,
                    )
                    assert login_response.status_code == 200

                    # Try to change user type - should be blocked
                    response = client.get(
                        url_for(
                            "admin_profile.cambiar_tipo_usario", type="instructor", user="test-user-demo", redirect_to="list"
                        ),
                        follow_redirects=True,
                    )
                    assert response.status_code == 200

                    # Verify user type was NOT changed
                    unchanged_user = database.session.execute(
                        database.select(Usuario).where(Usuario.usuario == "test-user-demo")
                    ).scalar_one()
                    assert unchanged_user.tipo == original_type

                    # Should have demo mode restriction message
                    html_content = response.get_data(as_text=True)

        finally:
            # Clean up demo mode
            if "NOW_LMS_DEMO_MODE" in os.environ:
                del os.environ["NOW_LMS_DEMO_MODE"]

    def test_change_user_type_dropdown_disabled_in_demo_mode(self, session_full_db_setup):
        """Test that dropdown is disabled in demo mode."""
        app = session_full_db_setup

        # Enable demo mode
        os.environ["NOW_LMS_DEMO_MODE"] = "1"

        try:
            with app.app_context():
                with app.test_client() as client:
                    # Login as admin
                    login_response = client.post(
                        "/user/login",
                        data={"usuario": "lms-admin", "acceso": "lms-admin"},
                        follow_redirects=True,
                    )
                    assert login_response.status_code == 200

                    # Access admin users list
                    response = client.get("/admin/users/list")
                    assert response.status_code == 200

                    html_content = response.get_data(as_text=True)

                    # Check that dropdown button is disabled in demo mode
                    assert "dropdown-toggle" in html_content
                    assert "disabled" in html_content  # Button should be disabled

        finally:
            # Clean up demo mode
            if "NOW_LMS_DEMO_MODE" in os.environ:
                del os.environ["NOW_LMS_DEMO_MODE"]

    def test_user_type_display_uses_correct_values(self, session_full_db_setup):
        """Test that user types are displayed correctly (user, not student)."""
        app = session_full_db_setup
        with app.app_context():
            # Create users with different types
            test_users = [
                Usuario(
                    usuario="test-admin",
                    acceso=b"fake_password",
                    tipo="admin",
                    activo=True,
                    visible=True,
                    correo_electronico="test-admin@example.com",
                ),
                Usuario(
                    usuario="test-instructor",
                    acceso=b"fake_password",
                    tipo="instructor",
                    activo=True,
                    visible=True,
                    correo_electronico="test-instructor@example.com",
                ),
                Usuario(
                    usuario="test-moderator",
                    acceso=b"fake_password",
                    tipo="moderator",
                    activo=True,
                    visible=True,
                    correo_electronico="test-moderator@example.com",
                ),
                Usuario(
                    usuario="test-user",
                    acceso=b"fake_password",
                    tipo="user",
                    activo=True,
                    visible=True,
                    correo_electronico="test-user@example.com",
                ),
            ]

            for user in test_users:
                database.session.add(user)
            database.session.commit()

            with app.test_client() as client:
                # Login as admin
                login_response = client.post(
                    "/user/login",
                    data={"usuario": "lms-admin", "acceso": "lms-admin"},
                    follow_redirects=True,
                )
                assert login_response.status_code == 200

                # Access admin users list
                response = client.get("/admin/users/list")
                assert response.status_code == 200

                html_content = response.get_data(as_text=True)

                # Check that all user types are properly displayed
                # Should show badges for each type
                assert "Admin" in html_content
                assert "Instructor" in html_content
                assert "Moderador" in html_content
                # Check for both translated and untranslated forms
                assert "Estudiante" in html_content or "Usuario" in html_content  # This should be shown for type "user"

                # Should NOT contain references to "student" type in conditions
                # (This was the bug - template was checking for "student" instead of "user")
                # We can't easily check the template source, but we ensure "user" type displays properly
