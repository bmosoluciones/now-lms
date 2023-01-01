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


def test_database_is_populated():
    database.drop_all()
    initial_setup()
    query = now_lms.Curso.query.filter_by(codigo="now").first()
    assert query is not None
    assert query.codigo == "now"
    query = now_lms.CursoSeccion.query.filter_by(nombre="Introduction to online teaching.").first()
    assert query.descripcion == "This is introductory material to online teaching."
    query = now_lms.CursoRecurso.query.filter_by(nombre="Introduction to Online Teaching").first()
    assert query.descripcion == "UofSC Center for Teaching Excellence - Introduction to Online Teaching."
    assert query.tipo == "youtube"
    assert query.url == "https://www.youtube.com/watch?v=CvPj4V_j7u8"
    assert query.seccion is not None
    assert query.codigo is not None


def test_login(client):
    response = client.get("/login")
    assert response.status_code == 200
    assert b"Inicio" in response.data
    assert b"BMO Soluciones" in response.data


def test_logon(client):
    response = client.get("/logon")
    assert response.status_code == 200
    assert b"Crear nuevo usuario." in response.data


def test_root(client):
    database.drop_all()
    initial_setup()
    response = client.get("/")
    assert response.status_code == 200
    assert b"NOW LMS" in response.data
    assert b"Welcome! This is your first course." in response.data


def test_course_logout(client):
    database.drop_all()
    initial_setup()
    response = client.get("/course/now")
    assert response.status_code == 200
    assert b"First Course" in response.data
    assert b"Welcome! This is your first course." in response.data
    assert b"now - First Course" in response.data
    assert b"Crear Cuenta" in response.data


def test_course_logoin(client, auth):
    database.drop_all()
    initial_setup()
    auth.login()
    response = client.get("/course/now")
    assert response.status_code == 200
    assert b"First Course" in response.data
    assert b"Welcome! This is your first course." in response.data
    assert b"now - First Course" in response.data
    assert b"Quitar del Sitio Web" in response.data


def test_app(client, auth):
    auth.login()
    response = client.get("/panel")
    assert response.status_code == 200
    assert b"Administrador del Sistema." in response.data


def test_admin(client, auth):
    auth.login()
    response = client.get("/admin")
    assert response.status_code == 200
    assert b"Panel de Adminis" in response.data
    assert b"Usuarios" in response.data


def test_instructor(client, auth):
    auth.login()
    response = client.get("/instructor")
    assert response.status_code == 200
    assert b"Panel del docente." in response.data


def test_moderator(client, auth):
    auth.login()
    response = client.get("/moderator")
    assert response.status_code == 200
    assert response.data


def test_student(client, auth):
    auth.login()
    response = client.get("/student")
    assert response.status_code == 200
    assert response.data


def test_users(client, auth):
    auth.login()
    response = client.get("/users")
    assert response.status_code == 200
    assert response.data
    assert b"Usuarios registrados en el sistema." in response.data


def test_users_inactive(client, auth):
    auth.login()
    response = client.get("/inactive_users")
    assert response.status_code == 200
    assert response.data
    assert b"Usuarios pendientes" in response.data


def test_nuevo_usuario(client, auth):
    auth.login()
    response = client.get("/new_user")
    assert response.status_code == 200
    assert response.data

    assert b"Crear nuevo Usuario." in response.data


def test_cursos(client, auth):
    auth.login()
    response = client.get("/cursos")
    assert response.status_code == 200
    assert response.data

    assert b"Lista de Cursos Disponibles." in response.data


def test_perfil(client, auth):
    auth.login()
    response = client.get("/perfil")
    assert response.status_code == 200
    assert response.data

    assert b"Perfil del usuario lms-admin" in response.data


def test_user_admin(client, auth):
    auth.login()
    response = client.get("/user/admin")
    assert response.status_code == 200
    assert response.data

    assert b"Perfil del usuario " in response.data


def test_activar_usuario(client, auth):
    auth.login()
    response = client.get("/set_user_as_active/instructor")
    assert response.status_code == 302


def test_inactivar_usuario(client, auth):
    auth.login()
    response = client.get("/set_user_as_inactive/instructor")
    assert response.status_code == 302


def test_eliminar_usuario(client, auth):
    auth.login()
    response = client.get("/delete_user/instructor")
    assert response.status_code == 302


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
    client.get("/change_curse_public?curse=now")
    client.get("/change_curse_public?curse=now")


def test_cambiar_estatus_curso(client, auth):
    auth.login()
    client.get("/change_curse_status?curse=now&status=draft")
    client.get("/change_curse_status?curse=now&status=public")
    client.get("/change_curse_status?curse=now&status=open")
    client.get("/change_curse_status?curse=now&status=closed")


def test_indices_seccion():
    from now_lms import CursoSeccion, modificar_indice_curso, reorganiza_indice_curso

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
    modificar_indice_curso(codigo_curso="demo", indice=3, task="decrement")
    seccion1 = CursoSeccion.query.filter_by(nombre="Seccion Prueba A").first()
    assert seccion1.indice == 3
    seccion2 = CursoSeccion.query.filter_by(nombre="Seccion Prueba B").first()
    assert seccion2.indice == 1
    seccion3 = CursoSeccion.query.filter_by(nombre="Seccion Prueba C").first()
    assert seccion3.indice == 2
    modificar_indice_curso(codigo_curso="demo", indice=2, task="increment")
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
    client.get("/course/seccion/T-002/increment/3")
    seccion1 = CursoSeccion.query.filter(CursoSeccion.nombre == "Seccion test 1", CursoSeccion.curso == "T-002").first()
    assert seccion1.indice == 3
    seccion2 = CursoSeccion.query.filter(CursoSeccion.nombre == "Seccion test 2", CursoSeccion.curso == "T-002").first()
    assert seccion2.indice == 1
    seccion3 = CursoSeccion.query.filter(CursoSeccion.nombre == "Seccion test 3", CursoSeccion.curso == "T-002").first()
    assert seccion3.indice == 2
    client.get("/course/seccion/T-002/decrement/2")
    seccion1 = CursoSeccion.query.filter(CursoSeccion.nombre == "Seccion test 1", CursoSeccion.curso == "T-002").first()
    assert seccion1.indice == 3


def test_update_resource_index(client, auth):
    from now_lms import CursoRecurso
    from now_lms.bi import reorganiza_indice_seccion

    database.drop_all()
    initial_setup()

    auth.login()

    recurso1 = CursoRecurso.query.filter(CursoRecurso.nombre == "Introduction to Online Teaching").first()
    assert recurso1 is not None
    recurso2 = CursoRecurso.query.filter(CursoRecurso.nombre == "How to Teach OnLine.").first()
    assert recurso2 is not None
    recurso3 = CursoRecurso.query.filter(CursoRecurso.nombre == "4 Steps to Sell your Online Course with 0 audience.").first()
    assert recurso3 is not None

    urls = (
        "/course/resource/now/" + recurso1.seccion + "/increment/1",
        "/course/resource/now/" + recurso1.seccion + "/decrement/1",
        "/course/resource/now/" + recurso1.seccion + "/increment/2",
        "/course/resource/now/" + recurso1.seccion + "/decrement/2",
    )

    for url in urls:
        response = client.get(url)
        assert response.status_code == 302

    reorganiza_indice_seccion(recurso1.seccion)


def test_courses_nologin(client, auth):

    database.drop_all()
    initial_setup()

    auth.login()

    query = now_lms.CursoRecurso.query.all()

    for recurso in query:
        URL = "/cource/" + recurso.curso + "/resource/" + recurso.tipo + "/" + recurso.codigo
        page = client.get(URL)
        as_bytes = str.encode(recurso.nombre)
        assert as_bytes in page.data
        assert b"Recurso Anterior" in page.data
        assert b"Marcar Completado" in page.data
        assert b"Recurso Siguiente" in page.data
        assert page.status_code == 200
