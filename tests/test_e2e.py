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
# Contributors:
# - William José Moreno Reyes

import pytest


"""
Casos de uso mas comunes.
"""


@pytest.fixture
def lms_application():
    from now_lms import app

    app.config.update(
        {
            "TESTING": True,
            "SECRET_KEY": "jgjañlsldaksjdklasjfkjj",
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
            "WTF_CSRF_ENABLED": False,
            "DEBUG": True,
            "PRESERVE_CONTEXT_ON_EXCEPTION": True,
            "SQLALCHEMY_ECHO": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "MAIL_SUPPRESS_SEND": True,
        }
    )

    yield app


def test_user_registration_to_free_course_enroll(lms_application, request):
    if request.config.getoption("--use-cases") == "True":
        from now_lms import database, initial_setup
        from now_lms.db import Curso, Usuario

        with lms_application.app_context():
            database.drop_all()
            initial_setup(with_tests=False, with_examples=False)
            with lms_application.test_client() as client:
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

                # User must be created
                user = database.session.execute(
                    database.select(Usuario).filter_by(correo_electronico="bmercado@nowlms.com")
                ).first()[0]
                assert user is not None
                assert user.activo is False

                # User must be able to verify his account by email
                from now_lms.auth import generate_confirmation_token, validate_confirmation_token, send_confirmation_email

                token = generate_confirmation_token("bmercado@nowlms.com")
                send_confirmation_email(user)  # Just to cover the code
                assert validate_confirmation_token(token) is True
                assert user.activo is True

                # User must be able to navigate to the free course
                client.get("/course/free/view", follow_redirects=True)
                assert b"Free Course" in client.get("/course/free/view").data
                assert b"Iniciar Sesi" in client.get("/course/free/view").data
                assert b"Crear Cuenta" in client.get("/course/free/view").data

                # Once active, cliente must be able to login
                from flask_login import current_user

                client.post("/user/login", data={"usuario": "bmercado@nowlms.com", "acceso": "bmercado"})
                assert current_user.is_authenticated
                assert current_user.tipo == "student"

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
                complete_resource = client.get(
                    "/course/free/resource/youtube/02HPB3AP3QNVK9ES6JGG5YK7CA/complete", follow_redirects=True
                )
                assert complete_resource.status_code == 200
                assert b"Recurso marcado como completado" in complete_resource.data

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


def test_user_password_change(lms_application, request):
    """Test password change functionality for users."""
    if request.config.getoption("--use-cases") == "True":
        from now_lms import database, initial_setup
        from now_lms.db import Usuario
        from now_lms.auth import proteger_passwd, validar_acceso

        with lms_application.app_context():
            database.drop_all()
            initial_setup(with_tests=False, with_examples=False)
            
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

            with lms_application.test_client() as client:
                # User logs in with old password
                login = client.post("/user/login", data={
                    "usuario": "testuser@nowlms.com", 
                    "acceso": "oldpassword"
                })
                assert login.status_code == 302  # Redirect after successful login

                # Access password change page
                password_change_page = client.get(f"/perfil/cambiar_contraseña/{test_user.id}")
                assert password_change_page.status_code == 200
                assert "Cambiar Contraseña".encode('utf-8') in password_change_page.data
                assert "Contraseña Actual".encode('utf-8') in password_change_page.data
                assert "Nueva Contraseña".encode('utf-8') in password_change_page.data

                # Try to change password with wrong current password
                wrong_password_change = client.post(f"/perfil/cambiar_contraseña/{test_user.id}", data={
                    "current_password": "wrongpassword",
                    "new_password": "newpassword123", 
                    "confirm_password": "newpassword123"
                })
                assert wrong_password_change.status_code == 200
                assert "La contraseña actual es incorrecta".encode('utf-8') in wrong_password_change.data

                # Try to change password with mismatched new passwords
                mismatched_change = client.post(f"/perfil/cambiar_contraseña/{test_user.id}", data={
                    "current_password": "oldpassword",
                    "new_password": "newpassword123", 
                    "confirm_password": "differentpassword"
                })
                assert mismatched_change.status_code == 200
                assert "Las nuevas contraseñas no coinciden".encode('utf-8') in mismatched_change.data

                # Successfully change password
                successful_change = client.post(f"/perfil/cambiar_contraseña/{test_user.id}", data={
                    "current_password": "oldpassword",
                    "new_password": "newpassword123", 
                    "confirm_password": "newpassword123"
                }, follow_redirects=True)
                assert successful_change.status_code == 200
                assert "Contraseña actualizada exitosamente".encode('utf-8') in successful_change.data

                # Verify password was actually changed in database
                updated_user = database.session.execute(
                    database.select(Usuario).filter_by(correo_electronico="testuser@nowlms.com")
                ).first()[0]
                assert validar_acceso("testuser@nowlms.com", "newpassword123")
                assert not validar_acceso("testuser@nowlms.com", "oldpassword")

                # Log out and log in with new password
                client.get("/user/logout")
                new_login = client.post("/user/login", data={
                    "usuario": "testuser@nowlms.com", 
                    "acceso": "newpassword123"
                })
                assert new_login.status_code == 302  # Successful login redirect


def test_password_recovery_functionality(lms_application, request):
    """Test the complete password recovery flow."""
    if request.config.getoption("--use-cases") == "True":
        from now_lms import database, initial_setup
        from now_lms.db import Usuario, Configuracion, MailConfig
        from now_lms.auth import proteger_passwd, validar_acceso

        with lms_application.app_context():
            database.drop_all()
            initial_setup(with_tests=False, with_examples=False)
            
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
                creado_por="system"
            )
            database.session.add(test_user)
            database.session.commit()
            
        with lms_application.test_client() as client:
            
            # Test that forgot password link shows on login page when email is configured
            login_response = client.get("/user/login")
            assert login_response.status_code == 200
            assert "¿Olvidaste tu contraseña?".encode('utf-8') in login_response.data
            
            # Test forgot password form
            forgot_password_response = client.get("/user/forgot_password")
            assert forgot_password_response.status_code == 200
            assert "Recuperar Contraseña".encode('utf-8') in forgot_password_response.data
            
            # Test submitting forgot password form with valid email
            from unittest.mock import patch
            with patch('now_lms.mail.send_mail') as mock_send_mail:
                mock_send_mail.return_value = True
                forgot_post = client.post("/user/forgot_password", data={
                    "email": "testuser2@nowlms.com"
                }, follow_redirects=True)
                assert forgot_post.status_code == 200
                assert "Se ha enviado un correo".encode('utf-8') in forgot_post.data
                mock_send_mail.assert_called_once()
            
            # Test submitting forgot password form with unverified email
            with lms_application.app_context():
                unverified_user = Usuario(
                    usuario="unverified",
                    correo_electronico="unverified@nowlms.com",
                    acceso=proteger_passwd("password"),
                    nombre="Unverified",
                    apellido="User",
                    tipo="student",
                    activo=True,
                    correo_electronico_verificado=False,
                    creado_por="system"
                )
                database.session.add(unverified_user)
                database.session.commit()
            
            forgot_unverified = client.post("/user/forgot_password", data={
                "email": "unverified@nowlms.com"
            }, follow_redirects=True)
            assert forgot_unverified.status_code == 200
            # Should still show success message for security
            assert "Se ha enviado un correo".encode('utf-8') in forgot_unverified.data
            
            # Test password reset with valid token
            with lms_application.app_context():
                from now_lms.auth import generate_password_reset_token
                reset_token = generate_password_reset_token("testuser2@nowlms.com")
            
            reset_form_response = client.get(f"/user/reset_password/{reset_token}")
            assert reset_form_response.status_code == 200
            assert "Restablecer Contraseña".encode('utf-8') in reset_form_response.data
            
            # Test password reset with mismatched passwords
            reset_mismatch = client.post(f"/user/reset_password/{reset_token}", data={
                "new_password": "newpassword123",
                "confirm_password": "differentpassword"
            })
            assert reset_mismatch.status_code == 200
            assert "Las nuevas contraseñas no coinciden".encode('utf-8') in reset_mismatch.data
            
            # Test successful password reset
            reset_success = client.post(f"/user/reset_password/{reset_token}", data={
                "new_password": "newpassword456", 
                "confirm_password": "newpassword456"
            }, follow_redirects=True)
            assert reset_success.status_code == 200
            assert "Contraseña actualizada exitosamente".encode('utf-8') in reset_success.data
            
            # Verify password was actually changed
            with lms_application.app_context():
                updated_user = database.session.execute(
                    database.select(Usuario).filter_by(correo_electronico="testuser2@nowlms.com")
                ).first()[0]
                assert validar_acceso("testuser2@nowlms.com", "newpassword456")
                assert not validar_acceso("testuser2@nowlms.com", "originalpassword")
            
            # Test password reset with invalid token
            invalid_token_response = client.get("/user/reset_password/invalidtoken")
            assert invalid_token_response.status_code == 302  # Redirect to login
            
            # Test that token validation works
            with lms_application.app_context():
                from now_lms.auth import validate_password_reset_token, generate_password_reset_token
                valid_token = generate_password_reset_token("testuser2@nowlms.com")
                email = validate_password_reset_token(valid_token)
                assert email == "testuser2@nowlms.com"  # Fresh token should work
