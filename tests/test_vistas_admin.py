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
from now_lms import app, database, init_app, Configuracion, crear_usuarios_predeterminados, crear_curso_predeterminados, log

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
        crear_curso_predeterminados()
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


def test_crear_curso(client, auth):
    auth.login()
    # Crear un curso.
    post = client.post(
        "/new_curse",
        data={
            "nombre": "Curso de Prueba",
            "codigo": "T-001",
            "descripcion": "Curso de Prueba.",
        },
    )
    curso = now_lms.Curso.query.filter_by(codigo="T-001").first()
    assert curso.nombre == "Curso de Prueba"
    assert curso.descripcion == "Curso de Prueba."
    # Crear una sección del curso.
    post = client.post(
        "/course/T-001/new_seccion",
        data={
            "nombre": "Seccion de Prueba",
            "descripcion": "Seccion de Prueba.",
        },
    )
    seccion = now_lms.CursoSeccion.query.filter_by(curso="T-001").first()
    assert seccion.nombre == "Seccion de Prueba"
    assert seccion.descripcion == "Seccion de Prueba."
    client.get("/change_curse_status?curse=T-001&status=draft")
    client.get("/change_curse_status?curse=T-001&status=public")
    client.get("/change_curse_status?curse=T-001&status=open")
    client.get("/change_curse_status?curse=T-001&status=closed")
    client.get("/change_curse_public?curse=T-001")
    client.get("/change_curse_public?curse=T-001")
    publicar_seccion = "/change_curse_seccion_public?course_code=T-001" + "&codigo=" + seccion.codigo
    client.get(publicar_seccion)
    client.get(publicar_seccion)
    eliminar_seccion = "/delete_seccion/T-001/" + seccion.codigo
    client.get(eliminar_seccion)
    client.get("/delete_curse/T-001")


def test_cambiar_curso_publico(client, auth):
    auth.login()
    client.get("/change_curse_public?curse=demo")
    client.get("/change_curse_public?curse=demo")


def test_cambiar_estatus_curso(client, auth):
    auth.login()
    client.get("/change_curse_status?curse=demo&status=draft")
    client.get("/change_curse_status?curse=demo&status=public")
    client.get("/change_curse_status?curse=demo&status=open")
    client.get("/change_curse_status?curse=demo&status=closed")


def test_indices_seccion():
    from now_lms import CursoSeccion, modificar_indice_seccion, reorganiza_indice_curso

    seccion1 = CursoSeccion(
        curso="demo",
        nombre="Seccion Prueba A",
        descripcion="Seccion Prueba A.",
        indice=2,
    )
    seccion2 = CursoSeccion(
        curso="demo",
        nombre="Seccion Prueba B",
        descripcion="Seccion Prueba B.",
        indice=1,
    )
    seccion3 = CursoSeccion(
        curso="demo",
        nombre="Seccion Prueba C",
        descripcion="Seccion Prueba C.",
        indice=3,
    )
    database.session.add(seccion1)
    database.session.add(seccion2)
    database.session.add(seccion3)
    database.session.commit()
    seccion1 = CursoSeccion.query.filter_by(nombre="Seccion Prueba A").first()
    assert seccion1.indice == 2
    seccion2 = CursoSeccion.query.filter_by(nombre="Seccion Prueba B").first()
    assert seccion2.indice == 1
    seccion3 = CursoSeccion.query.filter_by(nombre="Seccion Prueba C").first()
    assert seccion3.indice == 3
    modificar_indice_seccion(codigo_curso="demo", indice=3, task="decrement")
    seccion1 = CursoSeccion.query.filter_by(nombre="Seccion Prueba A").first()
    assert seccion1.indice == 3
    seccion2 = CursoSeccion.query.filter_by(nombre="Seccion Prueba B").first()
    assert seccion2.indice == 1
    seccion3 = CursoSeccion.query.filter_by(nombre="Seccion Prueba C").first()
    assert seccion3.indice == 2
    modificar_indice_seccion(codigo_curso="demo", indice=2, task="increment")
    seccion1 = CursoSeccion.query.filter_by(nombre="Seccion Prueba A").first()
    assert seccion1.indice == 2
    seccion2 = CursoSeccion.query.filter_by(nombre="Seccion Prueba B").first()
    assert seccion2.indice == 1
    seccion3 = CursoSeccion.query.filter_by(nombre="Seccion Prueba C").first()
    assert seccion3.indice == 3
    # Eliminamos la seccion con indice 2
    seccion1 = CursoSeccion.query.filter_by(nombre="Seccion Prueba A").delete()
    database.session.commit()
    reorganiza_indice_curso(codigo_curso="demo")
    seccion1 = CursoSeccion.query.filter_by(nombre="Seccion Prueba B").first()
    assert seccion1.indice == 1
    seccion2 = CursoSeccion.query.filter_by(nombre="Seccion Prueba C").first()
    assert seccion2.indice == 2
    seccion3 = CursoSeccion.query.filter_by(indice=3).first()
    assert seccion3 is None
    cuenta = CursoSeccion.query.filter_by(curso="demo").count()
    assert cuenta == 2


def test_reorganizar_indice_web(client, auth):
    from now_lms import CursoSeccion

    auth.login()
    # Crear un curso.
    post = client.post(
        "/new_curse",
        data={
            "nombre": "Curso de Prueba",
            "codigo": "T-002",
            "descripcion": "Curso de Prueba.",
        },
    )
    curso = now_lms.Curso.query.filter_by(codigo="T-002").first()
    assert curso.nombre == "Curso de Prueba"
    assert curso.descripcion == "Curso de Prueba."
    # Crear una sección del curso.
    post1 = client.post(
        "/course/T-002/new_seccion",
        data={"nombre": "Seccion test 2", "descripcion": "Seccion test 2."},
    )
    post2 = client.post(
        "/course/T-002/new_seccion",
        data={"nombre": "Seccion test 3", "descripcion": "Seccion test 3."},
    )
    post3 = client.post(
        "/course/T-002/new_seccion",
        data={"nombre": "Seccion test 1", "descripcion": "Seccion test 1."},
    )
    cuenta = now_lms.CursoSeccion.query.filter_by(curso="T-002").count()
    assert cuenta == 3
    seccion1 = CursoSeccion.query.filter(CursoSeccion.nombre == "Seccion test 1", CursoSeccion.curso == "T-002").first()
    assert seccion1.indice == 3
    seccion2 = CursoSeccion.query.filter(CursoSeccion.nombre == "Seccion test 2", CursoSeccion.curso == "T-002").first()
    assert seccion2.indice == 1
    seccion3 = CursoSeccion.query.filter(CursoSeccion.nombre == "Seccion test 3", CursoSeccion.curso == "T-002").first()
    assert seccion3.indice == 2
    client.get("/course/T-002/increment/3")
    seccion1 = CursoSeccion.query.filter(CursoSeccion.nombre == "Seccion test 1", CursoSeccion.curso == "T-002").first()
    assert seccion1.indice == 2
    seccion2 = CursoSeccion.query.filter(CursoSeccion.nombre == "Seccion test 2", CursoSeccion.curso == "T-002").first()
    assert seccion2.indice == 1
    seccion3 = CursoSeccion.query.filter(CursoSeccion.nombre == "Seccion test 3", CursoSeccion.curso == "T-002").first()
    assert seccion3.indice == 3
    client.get("/course/T-002/decrement/2")
    seccion1 = CursoSeccion.query.filter(CursoSeccion.nombre == "Seccion test 1", CursoSeccion.curso == "T-002").first()
    assert seccion1.indice == 3
