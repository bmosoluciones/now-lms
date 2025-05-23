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
        }
    )

    yield app


def test_contraseña_incorrecta(lms_application, request):

    if request.config.getoption("--slow") == "True":

        from now_lms import database, initial_setup
        from now_lms.auth import validar_acceso

        with lms_application.app_context():
            from flask_login import current_user
            from flask_login.mixins import AnonymousUserMixin

            database.drop_all()
            initial_setup(with_tests=False, with_examples=False)

            with lms_application.test_client() as client:
                # Keep the session alive until the with clausule closes
                client.post("/user/login", data={"usuario": "lms-admin", "acceso": "lms_admin"})
                assert isinstance(current_user, AnonymousUserMixin)
                assert validar_acceso("lms-admn", "lms-admin") is False


def test_generar_pdf(lms_application, request):

    if name == "nt":
        pytest.skip("PDF generation likelly to fail in Windows.")

    else:

        if request.config.getoption("--testpdf") == "True":

            from now_lms import initial_setup
            from now_lms.db import database

            with lms_application.app_context():

                database.drop_all()
                initial_setup(with_tests=False, with_examples=False)

                from now_lms.misc import check_generate_pdf

                check_generate_pdf()

        else:
            pytest.skip("Not running slow test.")


def test_load_mail_config(lms_application):

    with lms_application.app_context():
        from now_lms.mail import load_email_setup

        load_email_setup(lms_application)
