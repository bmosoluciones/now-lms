# Copyright 2021 - 2023 William José Moreno Reyes
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
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["TESTING"] = True
app.config["WTF_CSRF_ENABLED"] = False
app.config["DEBUG"] = True
app.config["PRESERVE_CONTEXT_ON_EXCEPTION"] = False
app.app_context().push()


@pytest.fixture(scope="module", autouse=True)
def lms():
    app.app_context().push()
    database.drop_all()
    initial_setup()

    app.app_context().push()
    yield app


@pytest.fixture
def client(lms):
    return app.test_client()


@pytest.fixture
def runner(lms):
    return app.test_cli_runner()


def test_acceso_recursos(client):
    from now_lms.db import CursoRecurso

    recursos = CursoRecurso.query.filter(CursoRecurso.curso == "resources").all()
    for recurso in recursos:
        url = "/cource/resources/resource/" + recurso.tipo + "/" + recurso.id
        page = client.get(url)
