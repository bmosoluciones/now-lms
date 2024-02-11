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


import os
import sys
import pytest

from now_lms import log

# Add currect dir to path to import the list of static views to test
sys.path.append(os.path.join(os.path.dirname(__file__)))

from x_rutas_estaticas import rutas_estaticas

"""
Todas las vistas que expone el programa deben de poderse "visitar" sin mostrar
errores al usuario, si el perfil del usuario no tiene permisos para acceder a
la vista mencionada se debe de redireccionar apropiadamente.

Para ver una lista de vistas ejecutar:

>>> from now_lms import app
>>> app.url_map

Error codes se verifican al final.
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
        }
    )

    yield app


def test_visit_all_views_with_anonimus_user(lms_application):

    with lms_application.app_context():

        from now_lms import database, initial_setup

        database.drop_all()
        initial_setup(with_tests=True, with_examples=False)

        with lms_application.test_client() as client:
            for ruta in rutas_estaticas:
                log.warning(ruta.ruta)
                consulta = client.get(ruta.ruta)
                assert consulta.status_code == ruta.no_session
                if consulta.status_code == 200 and ruta.texto:
                    for t in ruta.texto:
                        assert t in consulta.data


def test_visit_all_views_with_admin_user(lms_application):

    from now_lms import database, initial_setup

    with lms_application.app_context():
        from flask_login import current_user

        database.drop_all()
        initial_setup(with_tests=True, with_examples=False)

        with lms_application.test_client() as client:
            # Keep the session alive until the with clausule closes

            client.post("/user/login", data={"usuario": "lms-admin", "acceso": "lms-admin"})
            assert current_user.is_authenticated
            assert current_user.tipo == "admin"

            for ruta in rutas_estaticas:
                log.warning(ruta.ruta)
                consulta = client.get(ruta.ruta)
                assert consulta.status_code == ruta.admin
                if consulta.status_code == 200 and ruta.texto:
                    for t in ruta.texto:
                        assert t in consulta.data
                    for t in ruta.como_admin:
                        assert t in consulta.data
            client.get("/user/logout")


def test_visit_all_views_with_student_user(lms_application):

    from now_lms import database, initial_setup

    with lms_application.app_context():
        from flask_login import current_user

        database.drop_all()
        initial_setup(with_tests=True, with_examples=False)

        with lms_application.test_client() as client:
            # Keep the session alive until the with clausule closes

            client.post("/user/login", data={"usuario": "student1", "acceso": "student1"})
            assert current_user.is_authenticated
            assert current_user.tipo == "student"

            for ruta in rutas_estaticas:
                log.warning(ruta.ruta)
                consulta = client.get(ruta.ruta)
                assert consulta.status_code == ruta.user
                if consulta.status_code == 200 and ruta.texto:
                    for t in ruta.texto:
                        assert t in consulta.data
                    for t in ruta.como_user:
                        assert t in consulta.data
            client.get("/user/logout")


def test_visit_all_views_with_moderator_user(lms_application, request):

    if request.config.getoption("--slow") == "True":

        from now_lms import database, initial_setup

        with lms_application.app_context():
            from flask_login import current_user

            database.drop_all()
            initial_setup(with_tests=True, with_examples=False)

            with lms_application.test_client() as client:
                # Keep the session alive until the with clausule closes

                client.post("/user/login", data={"usuario": "moderator", "acceso": "moderator"})
                assert current_user.is_authenticated
                assert current_user.tipo == "moderator"

                for ruta in rutas_estaticas:
                    log.warning(ruta.ruta)
                    consulta = client.get(ruta.ruta)
                    assert consulta.status_code == ruta.moderator
                    if consulta.status_code == 200 and ruta.texto:
                        for t in ruta.texto:
                            assert t in consulta.data
                        for t in ruta.como_moderador:
                            assert t in consulta.data
                client.get("/user/logout")


def test_visit_all_views_with_instructor_user(lms_application, request):

    if request.config.getoption("--slow") == "True":

        from now_lms import database, initial_setup

        with lms_application.app_context():
            from flask_login import current_user

            database.drop_all()
            initial_setup(with_tests=True, with_examples=False)

            with lms_application.test_client() as client:
                # Keep the session alive until the with clausule closes

                client.post("/user/login", data={"usuario": "instructor", "acceso": "instructor"})
                assert current_user.is_authenticated
                assert current_user.tipo == "instructor"

                for ruta in rutas_estaticas:
                    log.warning(ruta.ruta)
                    consulta = client.get(ruta.ruta)
                    assert consulta.status_code == ruta.instructor
                    if consulta.status_code == 200 and ruta.texto:
                        for t in ruta.texto:
                            assert t in consulta.data
                            for t in ruta.como_instructor:
                                assert t in consulta.data
                client.get("/user/logout")


def test_visit_custom_error_pages(lms_application, request):

    if request.config.getoption("--slow") == "True":
        error_codes = [402, 403, 404, 405, 500]
        with lms_application.test_client() as client:
            for error in error_codes:
                url = "/http/error/" + str(error)
                client.get(url)
    else:
        pytest.skip("Not running slow test.")


def test_demo_course(request, lms_application):
    if request.config.getoption("--slow") == "True":
        from now_lms import database, initial_setup

        with lms_application.app_context():

            database.drop_all()
            initial_setup(with_tests=False, with_examples=True)

            with lms_application.test_client() as client:
                client.get("/course/resources/view")

    else:
        pytest.skip("Not running slow test.")
