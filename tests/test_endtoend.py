# Copyright 2021 -2023 William José Moreno Reyes
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

import pytest
from now_lms.db import database

"""
Casos de uso mas comunes.
"""


def test_user_registration_to_free_course_enroll(full_db_setup, client):
    """Test user registration to free course enrollment."""
    app = full_db_setup
    from now_lms.db import database, Usuario

    # Test user registration
    post = client.post(
        "/user/logon",
        data={
            "nombre": "Brenda",
            "apellido": "Mercado",
            "correo_electronico": "bmercado@nowlms.com",
            "acceso": "bmercado",
        },
        follow_redirects=True,
    )
    assert post.status_code == 200

    with app.app_context():
        # User must be created
        user = database.session.execute(database.select(Usuario).filter_by(correo_electronico="bmercado@nowlms.com")).first()[
            0
        ]
        assert user is not None
        assert user.activo is False

        # User must be able to verify his account by email
        from now_lms.auth import generate_confirmation_token, validate_confirmation_token, send_confirmation_email

        token = generate_confirmation_token("bmercado@nowlms.com")
        # Create a request context for email sending
        with app.test_request_context():
            send_confirmation_email(user)  # Just to cover the code
        assert validate_confirmation_token(token) is True
        assert user.activo is True

    # User must be able to navigate to the free course
    client.get("/course/free/view", follow_redirects=True)
    assert b"Free Course" in client.get("/course/free/view").data
    assert b"Iniciar Sesi" in client.get("/course/free/view").data
    assert b"Crear Cuenta" in client.get("/course/free/view").data

    # Once active, user must be able to login
    login_response = client.post("/user/login", data={"usuario": "bmercado@nowlms.com", "acceso": "bmercado"})
    assert login_response.status_code == 302  # Successful login redirect

    # User must be able to enroll to a free course
    view_course = client.get("/course/free/view", follow_redirects=True)
    assert view_course.status_code == 200
    assert b"Free Course" in view_course.data
    assert b"Inscribirse al Curso" in view_course.data
    assert b"/course/free/enroll" in view_course.data
    enroll_view = client.get("/course/free/enroll")
    assert enroll_view.status_code == 200
    assert b"Esta a punto de inscribirse al curso FREE - FREE COURSE" in enroll_view.data
    assert b"Free Course" in enroll_view.data
    assert b"This is a free course." in enroll_view.data
    assert b"Inscribirse al curso" in enroll_view.data
    enroll = client.post(
        "/course/free/enroll",
        data={
            "nombre": "Brenda",
            "apellido": "Mercado",
            "correo_electronico": "bmercado@nowlms.com",
            "direccion1": "Calle Falsa 123",
            "direccion2": "Apto. 456",
            "pais": "Mexico",
            "provincia": "CDMX",
            "codigo_postal": "01234",
        },
        follow_redirects=True,
    )
    assert enroll.status_code == 200

    with app.app_context():
        # A payment must be created
        from now_lms.db import Pago

        payment = database.session.execute(
            database.select(Pago).filter_by(usuario="bmercado@nowlms.com", curso="free")
        ).first()[0]
        assert payment is not None
        assert payment.estado == "completed"

        # User must be enrolled to the course
        from now_lms.db import EstudianteCurso

        enrollment = database.session.execute(
            database.select(EstudianteCurso).filter_by(usuario="bmercado@nowlms.com", curso="free")
        ).first()[0]
        assert enrollment is not None
        assert enrollment.vigente is True

    # User must be able to see the course
    course_view = client.get("/course/free/view", follow_redirects=True)
    assert course_view.status_code == 200
    assert b"Free Course" in course_view.data
    assert b"Inscribirse al Curso" not in course_view.data

    # User must be able to access the course content
    content_view = client.get("/course/free/resource/youtube/02HPB3AP3QNVK9ES6JGG5YK7CA", follow_redirects=True)
    assert content_view.status_code == 200
    assert b"Free Course" in content_view.data
    assert b"Contenido del Curso" in content_view.data
    assert b"Marcar Completado" in content_view.data

    # User must be able to mark the content as completed
    complete_resource = client.get("/course/free/resource/youtube/02HPB3AP3QNVK9ES6JGG5YK7CA/complete", follow_redirects=True)
    assert complete_resource.status_code == 200
    assert b"Recurso marcado como completado" in complete_resource.data

    with app.app_context():
        # Recurso must be marked as completed
        from now_lms.db import CursoRecursoAvance

        resource_progress = database.session.execute(
            database.select(CursoRecursoAvance).filter_by(
                usuario="bmercado@nowlms.com", curso="free", recurso="02HPB3AP3QNVK9ES6JGG5YK7CA"
            )
        ).first()[0]
        assert resource_progress is not None
        assert resource_progress.completado is True

    recurso = client.get("/course/free/resource/youtube/02HPB3AP3QNVK9ES6JGG5YK7CA", follow_redirects=True)
    assert recurso.status_code == 200
    assert b"Recurso Completado" in recurso.data

    with app.app_context():
        # User must be able to complete the course
        from now_lms.db import CursoUsuarioAvance

        course_progress = database.session.execute(
            database.select(CursoUsuarioAvance).filter_by(usuario="bmercado@nowlms.com", curso="free")
        ).first()[0]
        assert course_progress is not None
        assert course_progress.completado is True

        # A certificate must be issued
        from now_lms.db import Certificacion

        certificate = database.session.execute(
            database.select(Certificacion).filter_by(usuario="bmercado@nowlms.com", curso="free")
        ).first()[0]
        assert certificate is not None
        assert certificate.certificado == "horizontal"


def test_user_password_change(basic_config_setup, client):
    """Test password change functionality for users."""
    app = basic_config_setup
    from now_lms.db import database, Usuario
    from now_lms.auth import proteger_passwd, validar_acceso

    with app.app_context():
        # Create a test user
        test_user = Usuario(
            usuario="testuser@nowlms.com",
            acceso=proteger_passwd("oldpassword"),
            nombre="Test",
            apellido="User",
            correo_electronico="testuser@nowlms.com",
            tipo="student",
            activo=True,
            correo_electronico_verificado=True,
        )
        database.session.add(test_user)
        database.session.commit()
        test_user_id = test_user.id  # Get the ID before leaving the context

    # User logs in with old password
    login = client.post("/user/login", data={"usuario": "testuser@nowlms.com", "acceso": "oldpassword"})
    assert login.status_code == 302  # Redirect after successful login

    # Access password change page
    password_change_page = client.get(f"/perfil/cambiar_contraseña/{test_user_id}")
    assert password_change_page.status_code == 200
    assert "Cambiar Contraseña".encode("utf-8") in password_change_page.data
    assert "Contraseña Actual".encode("utf-8") in password_change_page.data
    assert "Nueva Contraseña".encode("utf-8") in password_change_page.data

    # Try to change password with wrong current password
    wrong_password_change = client.post(
        f"/perfil/cambiar_contraseña/{test_user_id}",
        data={
            "current_password": "wrongpassword",
            "new_password": "newpassword123",
            "confirm_password": "newpassword123",
        },
    )
    assert wrong_password_change.status_code == 200
    assert "La contraseña actual es incorrecta".encode("utf-8") in wrong_password_change.data

    # Try to change password with mismatched new passwords
    mismatched_change = client.post(
        f"/perfil/cambiar_contraseña/{test_user_id}",
        data={
            "current_password": "oldpassword",
            "new_password": "newpassword123",
            "confirm_password": "differentpassword",
        },
    )
    assert mismatched_change.status_code == 200
    assert "Las nuevas contraseñas no coinciden".encode("utf-8") in mismatched_change.data

    # Successfully change password
    successful_change = client.post(
        f"/perfil/cambiar_contraseña/{test_user_id}",
        data={
            "current_password": "oldpassword",
            "new_password": "newpassword123",
            "confirm_password": "newpassword123",
        },
        follow_redirects=True,
    )
    assert successful_change.status_code == 200
    assert "Contraseña actualizada exitosamente".encode("utf-8") in successful_change.data

    with app.app_context():
        # Verify password was actually changed in database
        updated_user = database.session.execute(
            database.select(Usuario).filter_by(correo_electronico="testuser@nowlms.com")
        ).first()[0]
        assert validar_acceso("testuser@nowlms.com", "newpassword123")
        assert not validar_acceso("testuser@nowlms.com", "oldpassword")


def test_password_recovery_functionality(basic_config_setup):
    """Test the complete password recovery flow."""

    from now_lms.db import Usuario, MailConfig
    from now_lms.auth import proteger_passwd, validar_acceso

    with basic_config_setup.app_context():

        # Update the default mail configuration to enable email verification
        mail_config = database.session.execute(database.select(MailConfig)).first()[0]
        mail_config.MAIL_SERVER = "smtp.test.com"
        mail_config.MAIL_PORT = "587"
        mail_config.MAIL_USERNAME = "test@nowlms.com"
        mail_config.MAIL_DEFAULT_SENDER = "test@nowlms.com"
        mail_config.MAIL_DEFAULT_SENDER_NAME = "Test LMS"
        mail_config.MAIL_USE_TLS = True
        mail_config.email_verificado = True

        # Create a test user with verified email
        test_user = Usuario(
            usuario="testuser2",
            correo_electronico="testuser2@nowlms.com",
            acceso=proteger_passwd("originalpassword"),
            nombre="Test",
            apellido="User",
            tipo="student",
            activo=True,
            correo_electronico_verificado=True,
            creado_por="system",
        )
        database.session.add(test_user)
        database.session.commit()

    with basic_config_setup.test_client() as client:

        # Test that forgot password link shows on login page when email is configured
        login_response = client.get("/user/login")
        assert login_response.status_code == 200
        assert "¿Olvidaste tu contraseña?".encode("utf-8") in login_response.data

        # Test forgot password form
        forgot_password_response = client.get("/user/forgot_password")
        assert forgot_password_response.status_code == 200
        assert "Recuperar Contraseña".encode("utf-8") in forgot_password_response.data

        # Test submitting forgot password form with valid email
        from unittest.mock import patch

        with patch("now_lms.mail.send_mail") as mock_send_mail:
            mock_send_mail.return_value = True
            forgot_post = client.post("/user/forgot_password", data={"email": "testuser2@nowlms.com"}, follow_redirects=True)
            assert forgot_post.status_code == 200
            assert "Se ha enviado un correo".encode("utf-8") in forgot_post.data
            mock_send_mail.assert_called_once()

        # Test submitting forgot password form with unverified email
        with basic_config_setup.app_context():
            unverified_user = Usuario(
                usuario="unverified",
                correo_electronico="unverified@nowlms.com",
                acceso=proteger_passwd("password"),
                nombre="Unverified",
                apellido="User",
                tipo="student",
                activo=True,
                correo_electronico_verificado=False,
                creado_por="system",
            )
            database.session.add(unverified_user)
            database.session.commit()

        forgot_unverified = client.post(
            "/user/forgot_password", data={"email": "unverified@nowlms.com"}, follow_redirects=True
        )
        assert forgot_unverified.status_code == 200
        # Should still show success message for security
        assert "Se ha enviado un correo".encode("utf-8") in forgot_unverified.data

        # Test password reset with valid token
        with basic_config_setup.app_context():
            from now_lms.auth import generate_password_reset_token

            reset_token = generate_password_reset_token("testuser2@nowlms.com")

        reset_form_response = client.get(f"/user/reset_password/{reset_token}")
        assert reset_form_response.status_code == 200
        assert "Restablecer Contraseña".encode("utf-8") in reset_form_response.data

        # Test password reset with mismatched passwords
        reset_mismatch = client.post(
            f"/user/reset_password/{reset_token}",
            data={"new_password": "newpassword123", "confirm_password": "differentpassword"},
        )
        assert reset_mismatch.status_code == 200
        assert "Las nuevas contraseñas no coinciden".encode("utf-8") in reset_mismatch.data

        # Test successful password reset
        reset_success = client.post(
            f"/user/reset_password/{reset_token}",
            data={"new_password": "newpassword456", "confirm_password": "newpassword456"},
            follow_redirects=True,
        )
        assert reset_success.status_code == 200
        assert "Contraseña actualizada exitosamente".encode("utf-8") in reset_success.data

        # Verify password was actually changed
        with basic_config_setup.app_context():
            updated_user = database.session.execute(
                database.select(Usuario).filter_by(correo_electronico="testuser2@nowlms.com")
            ).first()[0]
            assert validar_acceso("testuser2@nowlms.com", "newpassword456")
            assert not validar_acceso("testuser2@nowlms.com", "originalpassword")

        # Test password reset with invalid token
        invalid_token_response = client.get("/user/reset_password/invalidtoken")
        assert invalid_token_response.status_code == 302  # Redirect to login

        # Test that token validation works
        with basic_config_setup.app_context():
            from now_lms.auth import validate_password_reset_token, generate_password_reset_token

            valid_token = generate_password_reset_token("testuser2@nowlms.com")
            email = validate_password_reset_token(valid_token)
            assert email == "testuser2@nowlms.com"  # Fresh token should work


def test_theme_functionality_comprehensive(basic_config_setup):
    """Test comprehensive theme functionality including overrides and custom pages."""

    from now_lms import database, initial_setup
    from now_lms.db import eliminar_base_de_datos_segura
    from now_lms.themes import (
        get_home_template,
        get_course_list_template,
        get_program_list_template,
        get_course_view_template,
        get_program_view_template,
    )

    with basic_config_setup.app_context():

        # Test default template returns
        assert get_home_template() == "inicio/home.html"
        assert get_course_list_template() == "inicio/cursos.html"
        assert get_program_list_template() == "inicio/programas.html"
        assert get_course_view_template() == "learning/curso/curso.html"
        assert get_program_view_template() == "learning/programa.html"

        # Test theme configuration change
        from now_lms.db import Style

        config = database.session.execute(database.select(Style)).first()[0]
        original_theme = config.theme

        # Change to Harvard theme
        config.theme = "harvard"
        database.session.commit()

        # Test template override detection
        expected_harvard_home = "themes/harvard/overrides/home.j2"

        assert get_home_template() == expected_harvard_home

        # Test Cambridge theme
        config.theme = "cambridge"
        database.session.commit()

        assert get_home_template() == "themes/cambridge/overrides/home.j2"

        # Test Oxford theme
        config.theme = "oxford"
        database.session.commit()

        assert get_home_template() == "themes/oxford/overrides/home.j2"

        # Test all other themes have override templates
        themes_to_test = ["classic", "corporative", "finance", "oxford", "cambridge", "harvard"]

        for theme in themes_to_test:
            config.theme = theme
            database.session.commit()

            # All themes should have override templates
            assert get_home_template() == f"themes/{theme}/overrides/home.j2"

        # Restore original theme
        config.theme = original_theme
        database.session.commit()

    with basic_config_setup.test_client() as client:
        # Test custom pages functionality

        # Test valid custom page access with Harvard theme
        with basic_config_setup.app_context():
            config = database.session.execute(database.select(Style)).first()[0]
            config.theme = "harvard"
            database.session.commit()

        # Test invalid page name security
        invalid_page_response = client.get("/custom/../../etc/passwd")
        assert invalid_page_response.status_code == 404

        # Test invalid characters in page name
        invalid_chars_response = client.get("/custom/test$page")
        assert invalid_chars_response.status_code == 302

        # Test non-existent custom page
        nonexistent_response = client.get("/custom/nonexistent")
        assert nonexistent_response.status_code == 302

        # Test theme access to home page with override
        home_response = client.get("/")
        assert home_response.status_code == 200

        # Test course listing with theme override
        course_list_response = client.get("/course/explore")
        assert course_list_response.status_code == 200

        # Test program listing with theme override
        program_list_response = client.get("/program/explore")
        assert program_list_response.status_code == 200

        # Test CSS file loading for Harvard theme
        css_response = client.get("/static/themes/harvard/theme.min.css")
        assert css_response.status_code == 200
        assert "harvard-primary" in css_response.data.decode("utf-8")

        # Test other academic theme CSS files
        cambridge_css = client.get("/static/themes/cambridge/theme.min.css")
        assert cambridge_css.status_code == 200
        assert "cambridge-primary" in cambridge_css.data.decode("utf-8")

        oxford_css = client.get("/static/themes/oxford/theme.min.css")
        assert oxford_css.status_code == 200
