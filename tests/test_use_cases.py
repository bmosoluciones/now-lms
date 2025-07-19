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

from os import name
from re import A
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
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
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
