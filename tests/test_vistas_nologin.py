# Copyright 2020 William José Moreno Reyes
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

# pylint: disable=redefined-outer-name
import pytest
import now_lms
from now_lms import app, database, initial_setup, log

app.config["SECRET_KEY"] = "jgjañlsldaksjdklasjfkjj"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["TESTING"] = True
app.config["WTF_CSRF_ENABLED"] = False
app.config["DEBUG"] = True
app.app_context().push()


@pytest.fixture(scope="module", autouse=True)
def lms():
    app.app_context().push()
    database.drop_all()
    initial_setup()

    app.app_context().push()
    yield app


def test_dummy():
    assert app.config["DEBUG"] == True


@pytest.fixture
def client(lms):
    return app.test_client()


@pytest.fixture
def runner(lms):
    return app.test_cli_runner()


def test_no_login_url(client):
    database.drop_all()
    initial_setup()
    page = client.get("/home")
    assert b"NOW LMS" in page.data
    assert b"First Course" in page.data
    assert b"1 cursos disponibles." in page.data
    assert b"Crear Cuenta" in page.data
    assert b"Inicio" in page.data
    page = client.get("/login")
    assert b"Inicio de Ses" in page.data
    assert b"Regresar" in page.data
    assert b"BMO Soluciones" in page.data
    page = client.get("/logon")
    assert b"Crear nuevo usuario." in page.data
    page = client.get("/course/now")
    assert b"Contenido del curso." in page.data
    assert b"now - First Course" in page.data
    assert b"First Course" in page.data
    assert b"Curso Certificado" in page.data
    assert b"This is introductory material to online teaching." in page.data
