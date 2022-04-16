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
from now_lms import app, database, init_app, Configuracion, crear_usuarios_predeterminados, log

app.config["SECRET_KEY"] = "jgjañlsldaksjdklasjfkjj"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["TESTING"] = True
app.config["WTF_CSRF_ENABLED"] = False
app.config["DEBUG"] = True
app.app_context().push()


@pytest.fixture(scope="module", autouse=True)
def lms():
    with app.app_context():
        database.drop_all()
        database.create_all()
        config = Configuracion(
            titulo="NOW LMS",
            descripcion="Sistema de aprendizaje en linea.",
        )
        database.session.add(config)
        database.session.commit()
        crear_usuarios_predeterminados()
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


class AuthActions:
    def __init__(self, client):
        self._client = client

    def login(self):
        return self._client.post("/login", data={"usuario": "lms-admin", "acceso": "lms-admin"})

    def logout(self):
        return self._client.get("/salir")


@pytest.fixture
def auth(client):
    return AuthActions(client)


def test_login(client):
    response = client.get("/login")
    assert b"Inicio" in response.data
    assert b"BMO Soluciones" in response.data


def test_logon(client):
    response = client.get("/logon")
    assert b"Crear nuevo usuario." in response.data


def test_root(client):
    response = client.get("/")
    assert b"No hay cursos disponibles en este momento." in response.data


def test_app(client, auth):
    auth.login()
    response = client.get("/panel")
    log.error(response.data)

    assert b"Administrador del Sistema." in response.data


def test_admin(client, auth):
    auth.login()
    response = client.get("/admin")
    log.error(response.data)

    assert b"Panel de Adminis" in response.data
    assert b"Usuarios" in response.data


def test_instructor(client, auth):
    auth.login()
    response = client.get("/instructor")
    log.error(response.data)

    assert b"Panel del docente." in response.data


def test_moderator(client, auth):
    auth.login()
    response = client.get("/moderator")
    assert response.data


def test_student(client, auth):
    auth.login()
    response = client.get("/student")
    assert response.data


def test_users(client, auth):
    auth.login()
    response = client.get("/users")
    assert response.data
    assert b"Usuarios registrados en el sistema." in response.data


def test_users_inactive(client, auth):
    auth.login()
    response = client.get("/inactive_users")
    assert response.data

    assert b"Usuarios pendientes" in response.data


def test_nuevo_usuario(client, auth):
    auth.login()
    response = client.get("/new_user")
    assert response.data

    assert b"Crear nuevo Usuario." in response.data


def test_cursos(client, auth):
    auth.login()
    response = client.get("/cursos")
    assert response.data

    assert b"Lista de Cursos Disponibles." in response.data


def test_perfil(client, auth):
    auth.login()
    response = client.get("/perfil")
    assert response.data

    assert b"Perfil del usuario lms-admin" in response.data


def test_user_admin(client, auth):
    auth.login()
    response = client.get("/user/admin")
    assert response.data

    assert b"Perfil del usuario " in response.data


def test_activar_usuario(client, auth):
    auth.login()
    response = client.get("/set_user_as_active/instructor")


def test_inactivar_usuario(client, auth):
    auth.login()
    response = client.get("/set_user_as_inactive/instructor")


def test_eliminar_usuario(client, auth):
    auth.login()
    response = client.get("/delete_user/instructor")


def test_crear_usuario(client):
    post = client.post(
        "/logon",
        data={
            "usuario": "test_user",
            "nombre": "Testing",
            "apellido": "Testing",
            "correo_electronico": "testing@cacao-accounting.io",
            "acceso": "Akjlkas5a4s6asd",
        },
    )
    query = now_lms.Usuario.query.filter_by(usuario="test_user").first()
    assert query
    # Usuario inactivo por defecto.
    assert query.activo is False


def test_funciones_usuario(client, auth):
    post = client.post(
        "/logon",
        data={
            "usuario": "test_user1",
            "nombre": "Testing",
            "apellido": "Testing",
            "correo_electronico": "testing@cacao-accounting.io",
            "acceso": "Akjlkas5a4s6asd",
        },
    )
    query = now_lms.Usuario.query.filter_by(usuario="test_user1").first()
    assert query
    # Usuario inactivo por defecto.
    assert query.activo is False
    # Activar usuario
    auth.login()
    activar = client.get("/set_user_as_active/test_user1")
    activar.data
    activo = now_lms.Usuario.query.filter_by(usuario="test_user1").first()
    assert query.activo is True
    from now_lms import cambia_tipo_de_usuario_por_id

    # Establecer como administrador.
    cambia_tipo_de_usuario_por_id("test_user1", "admin")
    admin = now_lms.Usuario.query.filter_by(usuario="test_user1").first()
    assert admin.tipo == "admin"
    # Establecer como moderador.
    cambia_tipo_de_usuario_por_id("test_user1", "moderator")
    admin = now_lms.Usuario.query.filter_by(usuario="test_user1").first()
    assert admin.tipo == "moderator"
    # Establecer como instructor.
    cambia_tipo_de_usuario_por_id("test_user1", "instructor")
    admin = now_lms.Usuario.query.filter_by(usuario="test_user1").first()
    assert admin.tipo == "instructor"
    # Establecer como instructor.
    cambia_tipo_de_usuario_por_id("test_user1", "user")
    admin = now_lms.Usuario.query.filter_by(usuario="test_user1").first()
    assert admin.tipo == "user"
