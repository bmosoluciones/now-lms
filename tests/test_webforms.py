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

from flask import session

from now_lms import log

# Add currect dir to path to import the list of static views to test
sys.path.append(os.path.join(os.path.dirname(__file__)))

from x_forms_data import forms


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


def test_fill_all_forms(lms_application, request):

    if request.config.getoption("--slow") == "True":

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

                for form in forms:

                    log.warning(form.ruta)

                    if form.file:
                        data = {key: str(value) for key, value in form.data.items()}
                        data[form.file.get("name")] = form.file.get("bytes")
                        consulta = client.post(form.ruta, data=data, follow_redirects=True, content_type="multipart/form-data")
                    else:
                        consulta = client.post(form.ruta, data=form.data, follow_redirects=True)

                    assert consulta.status_code == 200

                    if form.flash:
                        assert session["_flashes"][0][0] == "success"
                        assert session["_flashes"][0][1] == "Grupo creado correctamente"

                client.get("/user/logout")
