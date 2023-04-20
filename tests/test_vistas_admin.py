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

# pylint: disable=redefined-outer-name
import pytest
import now_lms
from now_lms import app, database, initial_setup

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
    app.app_context().push()
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
    assert query.id is not None
    assert query.curso is not None


def test_generar_indice_recurso():
    from now_lms.db import CursoRecurso
    from now_lms.db.tools import crear_indice_recurso

    s = crear_indice_recurso("lalala")
    assert s.has_prev == False
    assert s.has_next == False
    assert s.prev_is_alternative == False
    assert s.next_is_alternative == False
    assert s.prev_resource is None
    assert s.next_resource is None

    r = CursoRecurso.query.filter(CursoRecurso.curso == "resources", CursoRecurso.tipo == "meet").first()
    r = crear_indice_recurso(r.id)

    assert r.has_prev == True
    assert r.has_next == True
    assert r.prev_is_alternative == False
    assert r.next_is_alternative == True
    assert r.prev_resource is not None
    assert r.next_resource is not None

    for a in CursoRecurso.query.all():
        crear_indice_recurso(a.id)


def test_non_interactive(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"NOW LMS" in response.data
    response = client.get("/login")
    assert response.status_code == 200
    assert b"Inicio" in response.data
    assert b"BMO Soluciones" in response.data
    response = client.get("/logon")
    assert response.status_code == 200
    assert b"Crear nuevo usuario." in response.data
    response = client.get("/course/now")
    assert response.status_code == 200
    assert b"OnLine Learning 101" in response.data
    response = client.get("/theming")
    assert response.status_code == 302
    response = client.get("/settings")
    assert response.status_code == 302


def test_logged_in(client, auth):
    auth.login()
    response = client.get("/")
    assert response.status_code == 200
    response = client.get("/panel")
    assert response.status_code == 200
    response = client.get("/student")
    assert response.status_code == 200
    response = client.get("/moderator")
    assert response.status_code == 200
    response = client.get("/instructor")
    assert response.status_code == 200
    response = client.get("/admin")
    assert response.status_code == 200
    response = client.get("/perfil")
    assert response.status_code == 200
    response = client.get("/course/now")
    assert response.status_code == 200
    assert b"OnLine Learning 101" in response.data
    assert b"Quitar del Sitio Web" in response.data
    response = client.get("/panel")
    assert response.status_code == 200
    assert b"Administrador del Sistema." in response.data
    response = client.get("/admin")
    assert response.status_code == 200
    assert b"Panel de Adminis" in response.data
    assert b"Usuarios" in response.data
    response = client.get("/instructor")
    assert response.status_code == 200
    assert b"Panel del docente." in response.data
    response = client.get("/moderator")
    assert response.status_code == 200
    assert response.data
    response = client.get("/student")
    assert response.status_code == 200
    assert response.data
    response = client.get("/users")
    assert response.status_code == 200
    assert response.data
    assert b"Usuarios registrados en el sistema." in response.data
    response = client.get("/cursos")
    assert response.status_code == 200
    assert b"Lista de Cursos Disponibles." in response.data
    response = client.get("/new_user")
    assert response.status_code == 200
    assert b"Crear nuevo Usuario." in response.data
    response = client.get("/user/admin")
    assert response.status_code == 200
    assert b"Perfil de Usuario" in response.data
    query = now_lms.CursoRecurso.query.all()

    for recurso in query:
        URL = "/cource/" + recurso.curso + "/resource/" + recurso.tipo + "/" + recurso.id
        page = client.get(URL)
        as_bytes = str.encode(recurso.nombre)
        assert as_bytes in page.data
        assert page.status_code == 200

        if recurso.requerido == 3:
            URL = "/cource/" + recurso.curso + "/alternative/" + recurso.id + "/asc"
            page = client.get(URL)
            assert page.status_code == 200
            URL = "/cource/" + recurso.curso + "/alternative/" + recurso.id + "/desc"
            page = client.get(URL)
            assert page.status_code == 200

    response = client.get("/theming")
    assert response.status_code == 200
    response = client.get("/settings")
    assert response.status_code == 200
    response = client.get("/salir")
    assert response.status_code == 302
    response = client.get("/login")
    assert response.status_code == 200
    response = client.get("/logon")
    assert response.status_code == 200
    response = client.get("/course/now")
    assert response.status_code == 200


def test_users_inactive(client, auth):
    auth.login()
    response = client.get("/inactive_users")
    assert response.status_code == 200
    assert response.data
    assert b"Usuarios pendientes" in response.data
    response = client.get("/perfil")
    assert response.status_code == 200
    assert b"Perfil de Usuario" in response.data


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
    salir = client.get("/salir")
    assert salir.status_code == 302
    post = client.post(
        "/logon",
        data={
            "usuario": "mperez",
            "nombre": "Meyling",
            "apellido": "Perez",
            "correo_electronico": "mperez@ibw.com.ni",
            "acceso": "Akjlkas5a4s6asd",
        },
    )
    query = now_lms.Usuario.query.filter_by(usuario="mperez").first()
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
    publicar_seccion = "/change_curse_seccion_public?course_code=T-001" + "&codigo=" + seccion.id
    client.get(publicar_seccion)
    client.get(publicar_seccion)
    eliminar_seccion = "/delete_seccion/T-001/" + seccion.id
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
    from now_lms import Curso, CursoSeccion, modificar_indice_curso, reorganiza_indice_curso

    demo = Curso(
        nombre="Demo Course",
        codigo="demo",
        descripcion="Demo Course.",
        estado="open",
        certificado=True,
        publico=True,
        duracion=7,
        nivel=1,
        precio=10,
        capacidad=50,
        auditable=True,
    )
    database.session.add(demo)
    database.session.commit()

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


def test_reorganizar_indice_recurso(client, auth):
    from now_lms import CursoSeccion
    from now_lms.bi import reorganiza_indice_seccion

    auth.login()

    SECCION = CursoSeccion.query.filter_by(nombre="Introduction to online teaching.").first()

    assert SECCION is not None

    URL = "course/resource/now/" + SECCION.id + "/decrement/2"
    get = client.get(URL)
    assert get.status_code == 302

    URL = "course/resource/now/" + SECCION.id + "/increment/2"
    get = client.get(URL)
    assert get.status_code == 302

    reorganiza_indice_seccion(SECCION.id)


def test_reorganizar_nuevo_recurso(client, auth):
    from now_lms import CursoSeccion

    auth.login()

    SECCION = CursoSeccion.query.filter_by(nombre="How to sell a online course.").first()
    URL = "/course/now/" + SECCION.id + "/new_resource"
    get = client.get(URL)
    assert get.status_code == 200


def test_reorganizar_indice_seccion(client, auth):
    from now_lms import CursoSeccion

    auth.login()

    get = client.get("/course/now/seccion/decrement/1")
    assert get.status_code == 302
    get = client.get("/course/now/seccion/increment/2")
    assert get.status_code == 302


def test_serve_files(client, auth):
    auth.login()

    from now_lms.db import CursoRecurso

    recursos = CursoRecurso.query.filter(CursoRecurso.curso == "resources").all()

    for recurso in recursos:
        url = "/cource/resources/resource/" + recurso.tipo + "/" + recurso.id
        page = client.get(url)
        assert page.status_code == 200

        url = "/course/" + recurso.curso + "/description/" + recurso.id
        page = client.get(url)
        assert page.status_code == 200

        url = "/course/" + recurso.curso + "/description"
        page = client.get(url)
        assert page.status_code == 200

        if recurso.doc:
            doc_url = "/course/resources/files/" + recurso.id
            r = client.get(doc_url)
            assert r.status_code == 200

        if recurso.text:
            src = "/course/resources/md_to_html/" + recurso.id
            r = client.get(src)
            assert r.status_code == 200

        if recurso.tipo == "html":
            url = "/course/" + recurso.curso + "/external_code/" + recurso.id
            page = client.get(url)
            assert page.status_code == 200


def test_course_description(client, auth):
    from now_lms.db import Curso

    cursos = Curso.query.all()

    auth.login()

    for curso in cursos:
        url = "/course/" + curso.codigo + "/description"
        page = client.get(url)
        assert page.status_code == 200


def test_edit_course(client, auth):
    from datetime import datetime, timedelta

    data = {
        "nombre": "Edit",
        "descripcion": "Edit",
        "publico": False,
        "auditable": False,
        "certificado": False,
        "precio": 1000,
        "capacidad": 100,
        "fecha_inicio": datetime.today() + timedelta(days=9),
        "fecha_fin": datetime.today() + timedelta(days=9),
        "duracion": 15,
        "nivel": 1,
    }
    data = {key: str(value) for key, value in data.items()}
    auth.login()
    get = client.get("/course/now/edit")
    assert get.status_code == 200
    post = client.post("/course/now/edit", data=data, follow_redirects=True)
    assert post.status_code == 200


def test_edit_seccion(client, auth):
    auth.login()

    from now_lms.db import CursoSeccion

    seccion = CursoSeccion.query.filter(CursoSeccion.curso == "resources").first()

    url = "/course/resources/" + seccion.id + "/edit"

    data = {
        "nombre": "lalala",
        "descripcion": "lalala",
    }

    data = {key: str(value) for key, value in data.items()}
    auth.login()
    get = client.get(url)
    assert get.status_code == 200
    post = client.post(url, data=data, follow_redirects=True)
    assert post.status_code == 200


def test_edit_settings(client, auth):
    from now_lms.db import CursoSeccion

    data = {
        "titulo": "LMS test",
        "descripcion": "LMS test",
        "modo": "mooc",
        "paypal": True,
        "stripe": True,
        "stripe_public": "añldkakdlkadkasdksamdsa",
        "stripe_secret": "añldmañlkdñladm",
    }
    data = {key: str(value) for key, value in data.items()}
    auth.login()
    get = client.get("/settings")
    assert get.status_code == 200
    post = client.post("/settings", data=data, follow_redirects=True)
    assert post.status_code == 200


def test_upload_pdf(client, auth):
    from io import BytesIO
    from now_lms.db import CursoSeccion

    seccion = CursoSeccion.query.filter(CursoSeccion.curso == "resources").first()
    url = "/course/resources/" + seccion.id + "/pdf/new"

    data = {"nombre": "test", "descripcion": "test pdf"}
    data = {key: str(value) for key, value in data.items()}
    data["pdf"] = (BytesIO(b"abcdef"), "test.pdf")
    auth.login()
    response = client.get(url)
    response = client.post(url, data=data, follow_redirects=True, content_type="multipart/form-data")
    assert response.status_code == 200


def test_upload_img(client, auth):
    from io import BytesIO
    from now_lms.db import CursoSeccion

    seccion = CursoSeccion.query.filter(CursoSeccion.curso == "resources").first()
    url = "/course/resources/" + seccion.id + "/img/new"

    data = {"nombre": "test", "descripcion": "test pdf"}
    data = {key: str(value) for key, value in data.items()}
    data["img"] = (BytesIO(b"abcdef"), "test.jpg")
    auth.login()
    response = client.get(url)
    response = client.post(url, data=data, follow_redirects=True, content_type="multipart/form-data")
    assert response.status_code == 200


def test_upload_ogg(client, auth):
    from io import BytesIO
    from now_lms.db import CursoSeccion

    seccion = CursoSeccion.query.filter(CursoSeccion.curso == "resources").first()
    url = "/course/resources/" + seccion.id + "/audio/new"

    data = {"nombre": "test", "descripcion": "test pdf"}
    data = {key: str(value) for key, value in data.items()}
    data["audio"] = (BytesIO(b"abcdef"), "test.ogg")
    auth.login()
    response = client.get(url)
    response = client.post(url, data=data, follow_redirects=True, content_type="multipart/form-data")
    assert response.status_code == 200


def test_upload_youtube(client, auth):
    from now_lms.db import CursoSeccion

    seccion = CursoSeccion.query.filter(CursoSeccion.curso == "resources").first()
    url = "/course/resources/" + seccion.id + "/youtube/new"

    data = {"nombre": "test", "descripcion": "test pdf", "youtube_url": "test"}
    data = {key: str(value) for key, value in data.items()}
    auth.login()
    response = client.get(url)
    response = client.post(url, data=data, follow_redirects=True)
    assert response.status_code == 200


def test_upload_meet(client, auth):
    from datetime import date, datetime
    from now_lms.db import CursoSeccion

    seccion = CursoSeccion.query.filter(CursoSeccion.curso == "resources").first()
    url = "/course/resources/" + seccion.id + "/meet/new"

    data = {"nombre": "test", "descripcion": "test pdf", "url": "test"}
    data = {key: str(value) for key, value in data.items()}
    auth.login()
    response = client.get(url)
    response = client.post(url, data=data, follow_redirects=True)
    assert response.status_code == 200


def test_upload_html(client, auth):
    from now_lms.db import CursoSeccion

    seccion = CursoSeccion.query.filter(CursoSeccion.curso == "resources").first()
    url = "/course/resources/" + seccion.id + "/html/new"

    data = {"nombre": "test", "descripcion": "test pdf", "html_externo": "test"}
    data = {key: str(value) for key, value in data.items()}
    auth.login()
    response = client.get(url)
    response = client.post(url, data=data, follow_redirects=True)
    assert response.status_code == 200


def test_upload_link(client, auth):
    from now_lms.db import CursoSeccion

    seccion = CursoSeccion.query.filter(CursoSeccion.curso == "resources").first()
    url = "/course/resources/" + seccion.id + "/link/new"

    data = {"nombre": "test", "descripcion": "test pdf", "url": "test"}
    data = {key: str(value) for key, value in data.items()}
    auth.login()
    response = client.get(url)
    response = client.post(url, data=data, follow_redirects=True)
    assert response.status_code == 200


def test_upload_text(client, auth):
    from now_lms.db import CursoSeccion

    seccion = CursoSeccion.query.filter(CursoSeccion.curso == "resources").first()
    url = "/course/resources/" + seccion.id + "/text/new"

    data = {"nombre": "test", "descripcion": "test pdf", "editor": "test"}
    data = {key: str(value) for key, value in data.items()}
    auth.login()
    response = client.get(url)
    response = client.post(url, data=data, follow_redirects=True)
    assert response.status_code == 200


def test_eliminar_recursos(client, auth):
    from now_lms.db import CursoRecurso

    auth.login()
    recursos = CursoRecurso.query.filter(CursoRecurso.curso == "resources").all()
    assert recursos is not None
    for recurso in recursos:
        url = "/delete_recurso/resources/" + recurso.seccion + "/" + recurso.id
        page = client.get(url)
        assert page.status_code == 302


def test_cambiar_tipo_usuario(client, auth):
    auth.login()
    page = client.get("change_user_type", query_string={"user": "student", "type": "admin"})
    assert page.status_code == 302
