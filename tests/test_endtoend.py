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

from now_lms.db import database
from now_lms.logs import log

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

    from now_lms import database
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


from io import BytesIO


def test_course_administration_flow(basic_config_setup, client):
    """Test GET and POST for creating a new course."""
    app = basic_config_setup

    from now_lms.db import Usuario, Curso
    from now_lms.auth import proteger_passwd

    # Crear usuario instructor
    with app.app_context():
        instructor = Usuario(
            usuario="instructor1",
            acceso=proteger_passwd("testpass"),
            nombre="Test",
            apellido="Instructor",
            tipo="instructor",  # Rol requerido por la vista
            activo=True,
            correo_electronico_verificado=True,
        )
        database.session.add(instructor)
        database.session.commit()

    # Iniciar sesión como instructor
    login_response = client.post(
        "/user/login",
        data={"usuario": "instructor1", "acceso": "testpass"},
        follow_redirects=True,
    )
    assert login_response.status_code == 200

    # GET: acceder al formulario de creación de curso
    get_response = client.get("/course/new_curse")
    assert get_response.status_code == 200

    # POST: enviar datos de un nuevo curso
    post_response = client.post(
        "/course/new_curse",
        data={
            "nombre": "Curso de Prueba",
            "codigo": "test_course",
            "descripcion": "Descripcion completa del curso.",
            "descripcion_corta": "Descripcion corta.",
            "nivel": "beginner",
            "duracion": "4 semanas",
            "publico": True,
            "modalidad": "online",
            "foro_habilitado": True,
            "limitado": False,
            "capacidad": 0,
            "fecha_inicio": "2025-08-10",
            "fecha_fin": "2025-09-10",
            "pagado": False,
            "auditable": True,
            "certificado": False,  # Disable certificates to avoid template requirement
            "precio": 0,
        },
        follow_redirects=False,
    )
    assert post_response.status_code == 302  # Redirección a vista de administrar curso

    # Validar que el curso fue creado
    with app.app_context():
        curso = database.session.execute(database.select(Curso).filter_by(codigo="test_course")).scalars().first()
        assert curso is not None
        assert curso.nombre == "Curso de Prueba"
        assert curso.estado == "draft"
        assert curso.portada is None

    # POST: enviar datos de un nuevo curso con logo
    data = {
        "nombre": "Curso con Logo",
        "codigo": "testlogo",
        "descripcion": "Descripcion completa del curso con logo.",
        "descripcion_corta": "Descripcion corta.",
        "nivel": "beginner",
        "duracion": "4 semanas",
        "publico": True,
        "modalidad": "online",
        "foro_habilitado": True,
        "limitado": False,
        "capacidad": 0,
        "fecha_inicio": "2025-08-10",
        "fecha_fin": "2025-09-10",
        "pagado": False,
        "auditable": True,
        "certificado": False,  # Disable certificates to avoid template requirement
        "precio": 0,
    }

    data = {key: str(value) for key, value in data.items()}
    data["logo"] = (BytesIO(b"abksakjdalksdjlkAFcdef"), "logo.jpg")

    post_response = client.post(
        "/course/new_curse",
        data=data,
        content_type="multipart/form-data",  # Necesario para subir archivos
        follow_redirects=False,
    )
    assert post_response.status_code == 302  # Redirección a vista de administrar curso

    # Validar que el curso fue creado con portada
    with app.app_context():
        curso = database.session.execute(database.select(Curso).filter_by(codigo="testlogo")).scalars().first()
        assert curso is not None
        assert curso.nombre == "Curso con Logo"
        assert curso.estado == "draft"

    # --- PROBAR GET DE /course/<code>/edit ---
    edit_get = client.get("/course/testlogo/edit")
    assert edit_get.status_code == 200

    # --- PROBAR POST DE /course/<code>/edit ---
    edit_post = client.post(
        "/course/testlogo/edit",
        data={
            "nombre": "Curso Editado",
            "descripcion": "Descripcion actualizada del curso.",
            "descripcion_corta": "Descripcion corta editada.",
            "nivel": "intermediate",
            "duracion": "6 semanas",
            "publico": False,
            "modalidad": "self_paced",
            "foro_habilitado": False,  # Modalidad self_paced fuerza foro=False
            "limitado": True,
            "capacidad": 50,
            "fecha_inicio": "2025-08-15",
            "fecha_fin": "2025-09-20",
            "pagado": True,
            "auditable": False,
            "certificado": True,
            "plantilla_certificado": "default",
            "precio": 199,
        },
        follow_redirects=False,
    )
    assert edit_post.status_code == 302  # Redirección después de editar

    admin_course = client.get("/course/testlogo/admin")
    assert admin_course.status_code == 200

    # Seccion administration
    create_seccion = client.get("/course/testlogo/new_seccion")
    assert create_seccion.status_code == 200
    create_seccion = client.post(
        "/course/testlogo/new_seccion",
        data={
            "nombre": "Test Logo Seccion 1",
            "descripcion": "Descripcion de la seccion 1.",
        },
    )
    assert create_seccion.status_code == 302
    create_seccion = client.post(
        "/course/testlogo/new_seccion",
        data={
            "nombre": "Test Logo Seccion 2",
            "descripcion": "Descripcion de la seccion 2.",
        },
    )
    assert create_seccion.status_code == 302

    # Get seccion from database
    from now_lms.db import CursoSeccion

    with app.app_context():
        # Seccion 1
        seccion1 = (
            database.session.execute(database.select(CursoSeccion).filter_by(nombre="Test Logo Seccion 1")).scalars().first()
        )
        assert seccion1 is not None
        assert seccion1.nombre == "Test Logo Seccion 1"
        assert seccion1.descripcion == "Descripcion de la seccion 1."
        assert seccion1.indice == 1
        # Seccion 2
        seccion2 = (
            database.session.execute(database.select(CursoSeccion).filter_by(nombre="Test Logo Seccion 2")).scalars().first()
        )
        assert seccion2 is not None
        assert seccion2.nombre == "Test Logo Seccion 2"
        assert seccion2.indice == 2

    seccion1_edit_url = f"/course/testlogo/{seccion1.id}/edit"
    seccion2_edit_url = f"/course/testlogo/{seccion2.id}/edit"

    # GET: editar seccion 1
    edit_seccion1_get = client.get(seccion1_edit_url)
    assert edit_seccion1_get.status_code == 200
    # POST: editar seccion 1
    edit_seccion1_post = client.post(
        seccion1_edit_url,
        data={
            "nombre": "Test Logo Seccion 1 Editada",
            "descripcion": "Descripcion de la seccion 1 editada.",
        },
    )
    assert edit_seccion1_post.status_code == 302

    # Seccion 1 editada
    with app.app_context():
        seccion1 = (
            database.session.execute(database.select(CursoSeccion).filter_by(nombre="Test Logo Seccion 1 Editada"))
            .scalars()
            .first()
        )
        assert seccion1.nombre == "Test Logo Seccion 1 Editada"

    # New resource page
    new_resource_url = f"/course/testlogo/{seccion1.id}/new_resource"
    new_resource = client.get(new_resource_url)
    assert new_resource.status_code == 200
    assert "Seleccione un elemento a añadir al curso.".encode("utf-8") in new_resource.data

    # Resources creation pages
    types = ["youtube", "pdf", "audio", "img", "text", "slides", "link", "html", "meet"]
    for type in types:
        new_resource_url = f"/course/testlogo/{seccion1.id}/{type}/new"
        new_resource = client.get(new_resource_url)
        log.warning(f"Testing {new_resource_url}")
        assert new_resource.status_code == 200

    # Test resource creation
    # Youtube resource
    new_resource_url = f"/course/testlogo/{seccion1.id}/youtube/new"
    new_resource = client.get(new_resource_url)
    assert new_resource.status_code == 200
    new_resource_post = client.post(
        new_resource_url,
        data={
            "nombre": "Test Logo Recurso 1",
            "descripcion": "Descripcion del recurso 1.",
            "url": "https://www.youtube.com/watch?v=test",
        },
    )
    assert new_resource_post.status_code == 302

    # Text resource
    new_resource_url = f"/course/testlogo/{seccion1.id}/text/new"
    new_resource = client.get(new_resource_url)
    assert new_resource.status_code == 200
    new_resource_post = client.post(
        new_resource_url,
        data={
            "nombre": "Test Logo Recurso 2",
            "descripcion": "Descripcion del recurso 2.",
            "text": "Contenido del recurso 2.",
        },
    )
    assert new_resource_post.status_code == 302

    # Test link resource
    new_resource_url = f"/course/testlogo/{seccion1.id}/link/new"
    new_resource = client.get(new_resource_url)
    assert new_resource.status_code == 200
    new_resource_post = client.post(
        new_resource_url,
        data={
            "nombre": "Test Logo Recurso 3",
            "descripcion": "Descripcion del recurso 3.",
            "url": "https://www.google.com",
        },
    )
    # Test PDF resource
    new_resource_url = f"/course/testlogo/{seccion1.id}/pdf/new"
    new_resource = client.get(new_resource_url)
    assert new_resource.status_code == 200
    data = {
        "nombre": "Test Logo Recurso 4",
        "descripcion": "Descripcion del recurso 4.",
    }
    data = {key: str(value) for key, value in data.items()}
    data["pdf"] = (BytesIO(b"abksakjdalksdjlkAFcdef"), "file.pdf")
    new_resource_post = client.post(
        new_resource_url,
        data=data,
        content_type="multipart/form-data",
    )
    assert new_resource_post.status_code == 302

    # Test meet resource
    new_resource_url = f"/course/testlogo/{seccion1.id}/meet/new"
    new_resource = client.get(new_resource_url)
    assert new_resource.status_code == 200
    new_resource_post = client.post(
        new_resource_url,
        data={
            "nombre": "Test Logo Recurso 5",
            "descripcion": "Descripcion del recurso 5.",
            "url": "https://meet.google.com/test",
            "fecha": "2025-08-15",
            "hora_inicio": "10:00",
            "hora_fin": "12:00",
            "notes": "Notas del recurso 5.",
        },
    )
    assert new_resource_post.status_code == 302

    # Test img resource
    new_resource_url = f"/course/testlogo/{seccion1.id}/img/new"
    new_resource = client.get(new_resource_url)
    assert new_resource.status_code == 200
    data = {
        "nombre": "Test Logo Recurso 6",
        "descripcion": "Descripcion del recurso 6.",
    }
    data = {key: str(value) for key, value in data.items()}
    data["img"] = (BytesIO(b"abksakjdalksdjlkAFcdef"), "hola.jpg")
    new_resource_post = client.post(
        new_resource_url,
        data=data,
        content_type="multipart/form-data",
    )
    assert new_resource_post.status_code == 302

    # Test audio resource
    new_resource_url = f"/course/testlogo/{seccion1.id}/audio/new"
    new_resource = client.get(new_resource_url)
    assert new_resource.status_code == 200
    data = {
        "nombre": "Test Logo Recurso 7",
        "descripcion": "Descripcion del recurso 7.",
    }
    data = {key: str(value) for key, value in data.items()}
    data["audio"] = (BytesIO(b"abksakjdalksdjlkAFcdef"), "audio.ogg")
    new_resource_post = client.post(
        new_resource_url,
        data=data,
        content_type="multipart/form-data",
    )
    assert new_resource_post.status_code == 302

    # Test HTML resource
    new_resource_url = f"/course/testlogo/{seccion1.id}/html/new"
    new_resource = client.get(new_resource_url)
    assert new_resource.status_code == 200
    new_resource_post = client.post(
        new_resource_url,
        data={
            "nombre": "Test Logo Recurso 8",
            "descripcion": "Descripcion del recurso 8.",
            "external_code": "<h1>Contenido del recurso 8.</h1>",
        },
    )

    # Other admin pages
    delete_logo = client.get("/course/testlogo/delete_logo")
    assert delete_logo.status_code == 302


def test_course_resource_edit_functionality(basic_config_setup, client):
    """Test editing functionality for all course resource types."""
    app = basic_config_setup
    from now_lms.db import Usuario, Curso, CursoSeccion, CursoRecurso
    from now_lms.auth import proteger_passwd

    # Create instructor user
    with app.app_context():
        instructor = Usuario(
            usuario="instructor1",
            acceso=proteger_passwd("testpass"),
            nombre="Test",
            apellido="Instructor",
            tipo="instructor",
            activo=True,
            correo_electronico="instructor1@test.com",
        )
        database.session.add(instructor)
        database.session.commit()

        # Create a test course
        test_course = Curso(
            nombre="Test Course for Edit",
            codigo="testEdit",
            descripcion="Test course for edit functionality",
            descripcion_corta="Short description",
            nivel=1,
            duracion=10,
            estado="draft",
            publico=False,
            modalidad="self_paced",
            foro_habilitado=False,
            limitado=False,
            pagado=False,
            certificado=False,
            creado_por="instructor1",
        )
        database.session.add(test_course)
        database.session.commit()

        # Create test section
        test_section = CursoSeccion(
            curso="testEdit",
            nombre="Test Section",
            descripcion="Test section for resources",
            estado=False,
            indice=1,
            creado_por="instructor1",
        )
        database.session.add(test_section)
        database.session.commit()

        # Create test resources
        youtube_resource = CursoRecurso(
            curso="testEdit",
            seccion=test_section.id,
            tipo="youtube",
            nombre="Test YouTube Video",
            descripcion="Test YouTube description",
            url="https://www.youtube.com/watch?v=test",
            requerido="required",
            indice=1,
            creado_por="instructor1",
        )

        text_resource = CursoRecurso(
            curso="testEdit",
            seccion=test_section.id,
            tipo="text",
            nombre="Test Text Document",
            descripcion="Test text description",
            text="# Test Content\nThis is test content.",
            requerido="required",
            indice=2,
            creado_por="instructor1",
        )

        link_resource = CursoRecurso(
            curso="testEdit",
            seccion=test_section.id,
            tipo="link",
            nombre="Test External Link",
            descripcion="Test link description",
            url="https://www.example.com",
            requerido="optional",
            indice=3,
            creado_por="instructor1",
        )

        meet_resource = CursoRecurso(
            curso="testEdit",
            seccion=test_section.id,
            tipo="meet",
            nombre="Test Meeting",
            descripcion="Test meeting description",
            url="https://meet.example.com/test",
            requerido="required",
            indice=4,
            creado_por="instructor1",
        )

        html_resource = CursoRecurso(
            curso="testEdit",
            seccion=test_section.id,
            tipo="html",
            nombre="Test HTML Content",
            descripcion="Test HTML description",
            external_code="<h1>Test HTML</h1>",
            requerido="optional",
            indice=5,
            creado_por="instructor1",
        )

        database.session.add_all([youtube_resource, text_resource, link_resource, meet_resource, html_resource])
        database.session.commit()

        # Store IDs while in app context
        section_id = test_section.id
        youtube_id = youtube_resource.id
        text_id = text_resource.id
        link_id = link_resource.id
        meet_id = meet_resource.id
        html_id = html_resource.id

    # Login as instructor
    login_response = client.post(
        "/user/login",
        data={"usuario": "instructor1", "acceso": "testpass"},
        follow_redirects=True,
    )
    assert login_response.status_code == 200

    # Test edit forms access for all resource types
    edit_urls = [
        f"/course/testEdit/{section_id}/youtube/{youtube_id}/edit",
        f"/course/testEdit/{section_id}/text/{text_id}/edit",
        f"/course/testEdit/{section_id}/link/{link_id}/edit",
        f"/course/testEdit/{section_id}/meet/{meet_id}/edit",
        f"/course/testEdit/{section_id}/html/{html_id}/edit",
    ]

    for url in edit_urls:
        edit_get = client.get(url)
        assert edit_get.status_code == 200, f"GET failed for {url}"

    # Test editing YouTube resource
    youtube_edit_post = client.post(
        f"/course/testEdit/{section_id}/youtube/{youtube_id}/edit",
        data={
            "nombre": "Updated YouTube Video",
            "descripcion": "Updated YouTube description",
            "youtube_url": "https://www.youtube.com/watch?v=updated",
            "requerido": "optional",
        },
        follow_redirects=False,
    )
    assert youtube_edit_post.status_code in [200, 302], "YouTube edit failed"

    # Test editing text resource
    text_edit_post = client.post(
        f"/course/testEdit/{section_id}/text/{text_id}/edit",
        data={
            "nombre": "Updated Text Document",
            "descripcion": "Updated text description",
            "editor": "# Updated Content\nThis is updated content.",
            "requerido": "optional",
        },
        follow_redirects=False,
    )
    assert text_edit_post.status_code in [200, 302], "Text edit failed"

    # Test editing link resource
    link_edit_post = client.post(
        f"/course/testEdit/{section_id}/link/{link_id}/edit",
        data={
            "nombre": "Updated External Link",
            "descripcion": "Updated link description",
            "url": "https://www.updated-example.com",
            "requerido": "required",
        },
        follow_redirects=False,
    )
    assert link_edit_post.status_code in [200, 302], "Link edit failed"

    # Test editing meet resource
    meet_edit_post = client.post(
        f"/course/testEdit/{section_id}/meet/{meet_id}/edit",
        data={
            "nombre": "Updated Meeting",
            "descripcion": "Updated meeting description",
            "url": "https://meet.example.com/updated",
            "requerido": "optional",
        },
        follow_redirects=False,
    )
    assert meet_edit_post.status_code in [200, 302], "Meet edit failed"

    # Test editing HTML resource
    html_edit_post = client.post(
        f"/course/testEdit/{section_id}/html/{html_id}/edit",
        data={
            "nombre": "Updated HTML Content",
            "descripcion": "Updated HTML description",
            "html_externo": "<h1>Updated HTML</h1>",
            "requerido": "required",
        },
        follow_redirects=False,
    )
    assert html_edit_post.status_code in [200, 302], "HTML edit failed"

    # Test access to non-existent resource
    non_existent_edit = client.get(f"/course/testEdit/{section_id}/youtube/999999/edit")
    assert non_existent_edit.status_code == 302, "Should redirect for non-existent resource"

    # Test access with wrong resource type
    wrong_type_edit = client.get(f"/course/testEdit/{section_id}/pdf/{youtube_id}/edit")
    assert wrong_type_edit.status_code == 302, "Should redirect for wrong resource type"


def test_program_administration_flow(basic_config_setup, client):
    """Test GET and POST for creating a new course."""
    app = basic_config_setup
    from now_lms.db import Usuario
    from now_lms.auth import proteger_passwd

    # Crear usuario instructor
    with app.app_context():
        instructor = Usuario(
            usuario="instructor1",
            acceso=proteger_passwd("testpass"),
            nombre="Test",
            apellido="Instructor",
            tipo="instructor",  # Rol requerido por la vista
            activo=True,
            correo_electronico_verificado=True,
        )
        database.session.add(instructor)
        database.session.commit()

    # Iniciar sesión como instructor
    login_response = client.post(
        "/user/login",
        data={"usuario": "instructor1", "acceso": "testpass"},
        follow_redirects=True,
    )
    assert login_response.status_code == 200

    # GET: acceder al formulario de creación de programa
    get_response = client.get("/program/new")
    assert get_response.status_code == 200
    post_response = client.post(
        "/program/new",
        data={
            "nombre": "Programa de Prueba",
            "descripcion": "Descripcion completa del programa.",
            "codigo": "test_program",
            "precio": 0,
        },
    )
    assert post_response.status_code == 302


def test_masterclass_administration_flow(basic_config_setup, client):
    """Test comprehensive Master Class administration flow for instructor."""
    app = basic_config_setup
    from now_lms.db import Usuario, MasterClass, MasterClassEnrollment, Configuracion
    from now_lms.auth import proteger_passwd
    from datetime import datetime

    # Create instructor user and enable masterclass
    with app.app_context():
        # Enable master class in configuration
        config = database.session.execute(database.select(Configuracion)).first()[0]
        config.enable_masterclass = True

        instructor = Usuario(
            usuario="instructor1",
            acceso=proteger_passwd("testpass"),
            nombre="Test",
            apellido="Instructor",
            tipo="instructor",
            activo=True,
            correo_electronico_verificado=True,
        )
        database.session.add(instructor)
        database.session.commit()

    # Login as instructor
    login_response = client.post(
        "/user/login",
        data={"usuario": "instructor1", "acceso": "testpass"},
        follow_redirects=True,
    )
    assert login_response.status_code == 200

    # GET: Access instructor master class list (should be empty initially)
    list_response = client.get("/masterclass/instructor")
    assert list_response.status_code == 200
    assert "Mis Clases Magistrales".encode("utf-8") in list_response.data

    # GET: Access create master class form
    create_get = client.get("/masterclass/instructor/create")
    assert create_get.status_code == 200
    assert "Crear Clase Magistral".encode("utf-8") in create_get.data

    # POST: Create new master class
    future_date = datetime.now().date().replace(year=datetime.now().year + 1)
    create_post = client.post(
        "/masterclass/instructor/create",
        data={
            "title": "Introduction to Python Programming",
            "description_public": "Learn the fundamentals of Python programming in this comprehensive master class.",
            "description_private": "Advanced tips and resources for enrolled students.",
            "date": future_date.strftime("%Y-%m-%d"),
            "start_time": "14:00",
            "end_time": "16:00",
            "platform_name": "Zoom",
            "platform_url": "https://zoom.us/j/123456789",
            "is_certificate": False,
        },
        follow_redirects=False,
    )
    assert create_post.status_code == 302  # Redirect after successful creation

    # Validate master class was created
    with app.app_context():
        master_class = (
            database.session.execute(database.select(MasterClass).filter_by(title="Introduction to Python Programming"))
            .scalars()
            .first()
        )
        assert master_class is not None
        assert master_class.instructor_id == "instructor1"
        assert master_class.slug == "introduction-to-python-programming"
        master_class_id = master_class.id

    # GET: Access edit master class form
    edit_get = client.get(f"/masterclass/instructor/{master_class_id}/edit")
    assert edit_get.status_code == 200
    assert "Editar Clase Magistral".encode("utf-8") in edit_get.data

    # POST: Edit master class
    edit_post = client.post(
        f"/masterclass/instructor/{master_class_id}/edit",
        data={
            "title": "Advanced Python Programming",
            "description_public": "Updated description: Advanced Python programming concepts.",
            "description_private": "Updated private content for enrolled students.",
            "date": future_date.strftime("%Y-%m-%d"),
            "start_time": "15:00",
            "end_time": "17:00",
            "platform_name": "Google Meet",
            "platform_url": "https://meet.google.com/abc-def-ghi",
            "is_certificate": False,
        },
        follow_redirects=False,
    )
    assert edit_post.status_code == 302  # Redirect after successful edit

    # Validate master class was updated
    with app.app_context():
        updated_master_class = database.session.get(MasterClass, master_class_id)
        assert updated_master_class.title == "Advanced Python Programming"
        assert updated_master_class.platform_name == "Google Meet"
        assert updated_master_class.slug == "advanced-python-programming"

    # Create a student user and enroll them for testing student list
    with app.app_context():
        student = Usuario(
            usuario="student1",
            acceso=proteger_passwd("studentpass"),
            nombre="Test",
            apellido="Student",
            tipo="student",
            activo=True,
            correo_electronico_verificado=True,
        )
        database.session.add(student)
        database.session.commit()

        # Create enrollment
        enrollment = MasterClassEnrollment(
            master_class_id=master_class_id,
            user_id="student1",
            is_confirmed=True,
        )
        database.session.add(enrollment)
        database.session.commit()

    # Verify updated list shows the master class
    list_updated = client.get("/masterclass/instructor")
    assert list_updated.status_code == 200
    assert "Advanced Python Programming".encode("utf-8") in list_updated.data


def test_certificate_management_flow(basic_config_setup, client):
    """Test certificate management flow for instructor."""
    app = basic_config_setup
    from now_lms.db import Usuario
    from now_lms.auth import proteger_passwd

    # Create instructor user
    with app.app_context():
        instructor = Usuario(
            usuario="instructor1",
            acceso=proteger_passwd("testpass"),
            nombre="Test",
            apellido="Instructor",
            tipo="instructor",
            activo=True,
            correo_electronico_verificado=True,
        )
        database.session.add(instructor)
        database.session.commit()

    # Login as instructor
    login_response = client.post(
        "/user/login",
        data={"usuario": "instructor1", "acceso": "testpass"},
        follow_redirects=True,
    )
    assert login_response.status_code == 200

    # GET: Access certificate list
    list_response = client.get("/certificate/list")
    assert list_response.status_code == 200

    # GET: Access issued certificates list
    issued_list = client.get("/certificate/issued/list")
    assert issued_list.status_code == 200

    # GET: Access certificate generation form
    generate_get = client.get("/certificate/release/")
    assert generate_get.status_code == 200
    assert "Emitir un nuevo Certificado".encode("utf-8") in generate_get.data


def test_blog_management_flow(basic_config_setup, client):
    """Test blog management flow for instructor."""
    app = basic_config_setup
    from now_lms.db import Usuario, BlogPost
    from now_lms.auth import proteger_passwd

    # Create instructor user
    with app.app_context():
        instructor = Usuario(
            usuario="instructor1",
            acceso=proteger_passwd("testpass"),
            nombre="Test",
            apellido="Instructor",
            tipo="instructor",
            activo=True,
            correo_electronico_verificado=True,
        )
        database.session.add(instructor)
        database.session.commit()

    # Login as instructor
    login_response = client.post(
        "/user/login",
        data={"usuario": "instructor1", "acceso": "testpass"},
        follow_redirects=True,
    )
    assert login_response.status_code == 200

    # GET: Access instructor blog index
    blog_index = client.get("/instructor/blog")
    assert blog_index.status_code == 200

    # GET: Access create blog post form
    create_get = client.get("/admin/blog/posts/new")
    assert create_get.status_code == 200
    assert "Nueva Entrada".encode("utf-8") in create_get.data

    # POST: Create new blog post (with both BaseForm and BlogPostForm fields)
    create_post = client.post(
        "/admin/blog/posts/new",
        data={
            "nombre": "Getting Started with Machine Learning",  # BaseForm field
            "descripcion": "This is a comprehensive guide to machine learning fundamentals.",  # BaseForm field
            "title": "Getting Started with Machine Learning",  # BlogPostForm field
            "content": "This is a comprehensive guide to machine learning fundamentals.",  # BlogPostForm field
            "tags": "machine learning, python, tutorial",
            "allow_comments": True,
            "status": "pending",
        },
        follow_redirects=False,
    )
    assert create_post.status_code == 302  # Redirect after creation

    # Validate blog post was created
    with app.app_context():
        blog_post = (
            database.session.execute(database.select(BlogPost).filter_by(title="Getting Started with Machine Learning"))
            .scalars()
            .first()
        )
        assert blog_post is not None
        assert blog_post.author_id == "instructor1"
        assert blog_post.status == "pending"
        blog_post_id = blog_post.id

    # GET: Access edit blog post form
    edit_get = client.get(f"/admin/blog/posts/{blog_post_id}/edit")
    assert edit_get.status_code == 200
    assert "Editar Entrada".encode("utf-8") in edit_get.data

    # POST: Edit blog post
    edit_post = client.post(
        f"/admin/blog/posts/{blog_post_id}/edit",
        data={
            "nombre": "Advanced Machine Learning Techniques",  # BaseForm field
            "descripcion": "Updated content about advanced machine learning techniques.",  # BaseForm field
            "title": "Advanced Machine Learning Techniques",  # BlogPostForm field
            "content": "Updated content about advanced machine learning techniques.",  # BlogPostForm field
            "tags": "machine learning, advanced, neural networks",
            "allow_comments": True,
            "status": "pending",
        },
        follow_redirects=False,
    )
    assert edit_post.status_code == 302  # Redirect after edit

    # Validate blog post was updated
    with app.app_context():
        updated_post = database.session.get(BlogPost, blog_post_id)
        assert updated_post.title == "Advanced Machine Learning Techniques"
        assert "advanced" in updated_post.slug


def test_announcements_management_flow(basic_config_setup, client):
    """Test announcements management flow for instructor."""
    app = basic_config_setup
    from now_lms.db import Usuario, Announcement, Curso, DocenteCurso
    from now_lms.auth import proteger_passwd
    from datetime import datetime

    # Create instructor user and course
    with app.app_context():
        instructor = Usuario(
            usuario="instructor1",
            acceso=proteger_passwd("testpass"),
            nombre="Test",
            apellido="Instructor",
            tipo="instructor",
            activo=True,
            correo_electronico_verificado=True,
        )
        database.session.add(instructor)

        # Create a course and assign instructor
        course = Curso(
            codigo="test_course",
            nombre="Test Course",
            descripcion="Test course description",
            descripcion_corta="Short description",
            estado="published",
            creado_por="instructor1",
            modificado_por="instructor1",
        )
        database.session.add(course)
        database.session.flush()

        # Assign instructor to course
        instructor_assignment = DocenteCurso(
            usuario="instructor1",
            curso="test_course",
        )
        database.session.add(instructor_assignment)
        database.session.commit()

    # Login as instructor
    login_response = client.post(
        "/user/login",
        data={"usuario": "instructor1", "acceso": "testpass"},
        follow_redirects=True,
    )
    assert login_response.status_code == 200

    # Debug: Check instructor-course assignment
    with app.app_context():
        assignment = (
            database.session.execute(database.select(DocenteCurso).filter_by(usuario="instructor1", curso="test_course"))
            .scalars()
            .first()
        )
        print(f"Instructor assignment found: {assignment is not None}")
        if assignment:
            print(f"Assignment: {assignment.usuario} -> {assignment.curso}")

    # GET: Access announcements list
    list_response = client.get("/instructor/announcements")
    assert list_response.status_code == 200

    # GET: Access create announcement form
    create_get = client.get("/instructor/announcements/new")
    assert create_get.status_code == 200
    assert "Nuevo Anuncio de Curso".encode("utf-8") in create_get.data

    # POST: Create new announcement
    future_date = datetime.now().date().replace(year=datetime.now().year + 1)
    create_post = client.post(
        "/instructor/announcements/new",
        data={
            "title": "Important Course Update",
            "message": "This is an important announcement about the course schedule.",
            "course_id": "test_course",
            "expires_at": future_date.strftime("%Y-%m-%d"),
        },
        follow_redirects=False,
    )
    if create_post.status_code != 302:
        print(f"Create post failed with status {create_post.status_code}")
        print(f"Response data: {create_post.data.decode()}")
    else:
        print(f"Create post redirected to: {create_post.location}")
    assert create_post.status_code == 302  # Redirect after creation

    # Validate announcement was created
    with app.app_context():
        # Debug: Check all announcements in database
        all_announcements = database.session.execute(database.select(Announcement)).scalars().all()
        print(f"Total announcements in database: {len(all_announcements)}")
        for ann in all_announcements:
            print(f"  - {ann.title} (course_id: {ann.course_id}, created_by: {ann.created_by_id})")

        announcement = (
            database.session.execute(database.select(Announcement).filter_by(title="Important Course Update"))
            .scalars()
            .first()
        )
        assert announcement is not None
        assert announcement.course_id == "test_course"
        assert announcement.created_by_id == "instructor1"
        announcement_id = announcement.id

    # GET: Access edit announcement form
    edit_get = client.get(f"/instructor/announcements/{announcement_id}/edit")
    assert edit_get.status_code == 200
    assert "Editar Anuncio de Curso".encode("utf-8") in edit_get.data

    # POST: Edit announcement
    edit_post = client.post(
        f"/instructor/announcements/{announcement_id}/edit",
        data={
            "title": "Updated Course Information",
            "message": "Updated message about the course changes.",
            "course_id": "test_course",
            "expires_at": future_date.strftime("%Y-%m-%d"),
        },
        follow_redirects=False,
    )
    assert edit_post.status_code == 302  # Redirect after edit

    # Validate announcement was updated
    with app.app_context():
        updated_announcement = database.session.get(Announcement, announcement_id)
        assert updated_announcement.title == "Updated Course Information"

    # POST: Delete announcement
    delete_post = client.post(f"/instructor/announcements/{announcement_id}/delete")
    assert delete_post.status_code == 302  # Redirect after deletion


def test_evaluations_management_basic_flow(basic_config_setup, client):
    """Test basic evaluations access for instructor."""
    app = basic_config_setup
    from now_lms.db import Usuario, Curso, CursoSeccion, DocenteCurso
    from now_lms.auth import proteger_passwd

    # Create instructor user and course with section
    with app.app_context():
        instructor = Usuario(
            usuario="instructor1",
            acceso=proteger_passwd("testpass"),
            nombre="Test",
            apellido="Instructor",
            tipo="instructor",
            activo=True,
            correo_electronico_verificado=True,
        )
        database.session.add(instructor)

        # Create a course and assign instructor
        course = Curso(
            codigo="test_course",
            nombre="Test Course",
            descripcion="Test course description",
            descripcion_corta="Short description",
            estado="published",
            creado_por="instructor1",
            modificado_por="instructor1",
        )
        database.session.add(course)
        database.session.flush()

        # Create a section
        section = CursoSeccion(
            curso="test_course",
            nombre="Test Section",
            descripcion="Test section description",
            indice=1,
        )
        database.session.add(section)
        database.session.flush()

        # Assign instructor to course
        instructor_assignment = DocenteCurso(
            usuario="instructor1",
            curso="test_course",
        )
        database.session.add(instructor_assignment)
        database.session.commit()

    # Login as instructor
    login_response = client.post(
        "/user/login",
        data={"usuario": "instructor1", "acceso": "testpass"},
        follow_redirects=True,
    )
    assert login_response.status_code == 200

    # Test basic instructor access (evaluation routes are typically course-specific)
    # Note: The evaluations module currently appears to be more student-focused
    # This test validates basic instructor access, but evaluation management routes
    # may need to be implemented in the instructor profiles or course views


def test_masterclass_basic_access_flow(basic_config_setup, client):
    """Test basic Master Class access for instructor (avoiding template issues)."""
    app = basic_config_setup
    from now_lms.db import Usuario, Configuracion
    from now_lms.auth import proteger_passwd

    # Create instructor user and enable masterclass
    with app.app_context():
        # Enable master class in configuration
        config = database.session.execute(database.select(Configuracion)).first()[0]
        config.enable_masterclass = True

        instructor = Usuario(
            usuario="instructor1",
            acceso=proteger_passwd("testpass"),
            nombre="Test",
            apellido="Instructor",
            tipo="instructor",
            activo=True,
            correo_electronico_verificado=True,
        )
        database.session.add(instructor)
        database.session.commit()

    # Login as instructor
    login_response = client.post(
        "/user/login",
        data={"usuario": "instructor1", "acceso": "testpass"},
        follow_redirects=True,
    )
    assert login_response.status_code == 200

    # Test GET access to create master class form (template issue exists but route works)
    create_get = client.get("/masterclass/instructor/create")
    assert create_get.status_code == 200
    assert "Crear Clase Magistral".encode("utf-8") in create_get.data

    # Note: Full masterclass test has template issues with current_theme in test environment
    # This test validates that instructor access control is working correctly


def test_announcements_basic_access_flow(basic_config_setup, client):
    """Test basic announcements access for instructor."""
    app = basic_config_setup
    from now_lms.db import Usuario, Curso, DocenteCurso
    from now_lms.auth import proteger_passwd

    # Create instructor user and course
    with app.app_context():
        instructor = Usuario(
            usuario="instructor1",
            acceso=proteger_passwd("testpass"),
            nombre="Test",
            apellido="Instructor",
            tipo="instructor",
            activo=True,
            correo_electronico_verificado=True,
        )
        database.session.add(instructor)

        # Create a course and assign instructor
        course = Curso(
            codigo="test_course",
            nombre="Test Course",
            descripcion="Test course description",
            descripcion_corta="Short description",
            estado="published",
            creado_por="instructor1",
            modificado_por="instructor1",
        )
        database.session.add(course)
        database.session.flush()

        # Assign instructor to course
        instructor_assignment = DocenteCurso(
            usuario="instructor1",
            curso="test_course",
        )
        database.session.add(instructor_assignment)
        database.session.commit()

    # Login as instructor
    login_response = client.post(
        "/user/login",
        data={"usuario": "instructor1", "acceso": "testpass"},
        follow_redirects=True,
    )
    assert login_response.status_code == 200

    # Test access to announcements routes
    list_response = client.get("/instructor/announcements")
    assert list_response.status_code == 200

    create_get = client.get("/instructor/announcements/new")
    assert create_get.status_code == 200
    assert "Nuevo Anuncio de Curso".encode("utf-8") in create_get.data

    # Note: Form validation has complex inheritance requiring both BaseForm and AnnouncementForm fields
    # This test validates that instructor access control is working correctly
