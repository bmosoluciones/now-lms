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
from collections import namedtuple
from io import BytesIO
import now_lms
from now_lms import app, database, initial_setup

app.config["SECRET_KEY"] = "jgjañlsldaksjdklasjfkjj"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
app.config["TESTING"] = True
app.config["WTF_CSRF_ENABLED"] = False
app.config["DEBUG"] = True
app.config["PRESERVE_CONTEXT_ON_EXCEPTION"] = False
app.config["SQLALCHEMY_ECHO"] = False
app.app_context().push()

Ruta = namedtuple(
    "Ruta",
    ["ruta", "admin", "no_session", "texto"],
)

Forma = namedtuple(
    "Forma",
    ["ruta", "datos"],
)


@pytest.fixture(scope="module", autouse=True)
def lms():
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
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


rutas_estaticas = [
    Ruta(ruta="/login", admin=302, no_session=200, texto=[b"BMO Solucione", b"Inicio de"]),
    Ruta(ruta="/logon", admin=302, no_session=200, texto=[b"Crear nuevo usuario", b"Crear Cuenta"]),
    Ruta(ruta="/perfil", admin=200, no_session=302, texto=None),
    Ruta(ruta="/student", admin=200, no_session=302, texto=None),
    Ruta(ruta="/instructor", admin=200, no_session=302, texto=None),
    Ruta(ruta="/", admin=200, no_session=200, texto=[b"NOW LMS", b"Sistema de aprendizaje en linea.", b"OnLine Learning 101"]),
    Ruta(
        ruta="/index",
        admin=200,
        no_session=200,
        texto=[b"NOW LMS", b"Sistema de aprendizaje en linea.", b"OnLine Learning 101"],
    ),
    Ruta(
        ruta="/home",
        admin=200,
        no_session=200,
        texto=[b"NOW LMS", b"Sistema de aprendizaje en linea.", b"OnLine Learning 101"],
    ),
    Ruta(
        ruta="/panel",
        admin=200,
        no_session=302,
        texto=None,
    ),
    Ruta(
        ruta="/admin",
        admin=200,
        no_session=302,
        texto=[b"Usuarios", b"Nuevo Grupo", b"Tema del Sitio"],
    ),
    Ruta(
        ruta="/users",
        admin=200,
        no_session=302,
        texto=[
            b"Usuarios registrados en el sistema.",
            b"Lista de usuarios registrados en el sistema.",
        ],
    ),
    Ruta(
        ruta="/inactive_users",
        admin=200,
        no_session=302,
        texto=[
            b"Lista de usuarios registrados en el sistema pendientes de activar.",
        ],
    ),
    Ruta(
        ruta="/groups",
        admin=200,
        no_session=302,
        texto=[
            b"Grupos registrados en el sistema",
        ],
    ),
    Ruta(
        ruta="/new_group",
        admin=200,
        no_session=302,
        texto=[
            b"Agregar un nuevo Grupo de Usuarios",
        ],
    ),
    Ruta(
        ruta="/settings",
        admin=200,
        no_session=302,
        texto=[
            b"Editar config",
        ],
    ),
    Ruta(
        ruta="/theming",
        admin=200,
        no_session=302,
        texto=[
            b"Editar estulo del sitio web",
        ],
    ),
    Ruta(
        ruta="/mail",
        admin=200,
        no_session=302,
        texto=[
            b"de correo electronico",
        ],
    ),
    Ruta(
        ruta="/instructor",
        admin=200,
        no_session=302,
        texto=[b"Nuevo Curso", b"Panel del docente.", b"Nuevo Progama"],
    ),
    Ruta(
        ruta="/cursos",
        admin=200,
        no_session=302,
        texto=[b"Lista de Cursos Disponibles."],
    ),
    Ruta(
        ruta="/new_curse",
        admin=200,
        no_session=302,
        texto=[b"Crear nuevo curso."],
    ),
    Ruta(
        ruta="/explore",
        admin=200,
        no_session=200,
        texto=[b"Cursos disponibles."],
    ),
    Ruta(
        ruta="/programs",
        admin=200,
        no_session=200,
        texto=[b"Programas disponibles."],
    ),
    Ruta(
        ruta="/resources",
        admin=200,
        no_session=200,
        texto=[b"Recursos disponibles."],
    ),
    Ruta(
        ruta="/new_program",
        admin=200,
        no_session=302,
        texto=[b"Crear Programa."],
    ),
    Ruta(
        ruta="/tags",
        admin=200,
        no_session=302,
        texto=[b"Lista de Etiquetas Disponibles."],
    ),
    Ruta(
        ruta="/new_tag",
        admin=200,
        no_session=302,
        texto=[b"Crear nueva Etiqueta."],
    ),
    Ruta(
        ruta="/categories",
        admin=200,
        no_session=302,
        texto=[b"Lista de Categorias Disponibles."],
    ),
    Ruta(
        ruta="/new_category",
        admin=200,
        no_session=302,
        texto=[
            b"Crear Categoria.",
        ],
    ),
    Ruta(
        ruta="/groups",
        admin=200,
        no_session=302,
        texto=None,
    ),
    Ruta(
        ruta="/new_group",
        admin=200,
        no_session=302,
        texto=None,
    ),
    Ruta(
        ruta="/course/now",
        admin=200,
        no_session=200,
        texto=[b"Contenido del curso.", b"Curso Certificado"],
    ),
    Ruta(
        ruta="/course/now/new_seccion",
        admin=200,
        no_session=302,
        texto=[b"Crear una nueva secci"],
    ),
    Ruta(
        ruta="/panel",
        admin=200,
        no_session=302,
        texto=[
            b"Cursos Recientes",
            b"Recursos Creados",
            b"Usuarios Registrados",
        ],
    ),
    Ruta(ruta="/dashboard", admin=200, no_session=302, texto=None),
    Ruta(ruta="/student", admin=200, no_session=302, texto=None),
    Ruta(ruta="/moderator", admin=200, no_session=302, texto=None),
    # Debe estar al final para no cerrar la sesion actual.
    Ruta(ruta="/logout", admin=302, no_session=302, texto=None),
    Ruta(ruta="/salir", admin=302, no_session=302, texto=None),
    Ruta(ruta="/exit", admin=302, no_session=302, texto=None),
]


def test_visit_all_views_no_session(client, auth):
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
    app.app_context().push()
    database.drop_all()
    initial_setup()
    auth.logout()
    assert app.config["SQLALCHEMY_DATABASE_URI"] == "sqlite://"
    for ruta in rutas_estaticas:
        consulta = client.get(ruta.ruta)
        assert consulta.status_code == ruta.no_session
        if consulta.status_code == 200 and ruta.texto:
            for t in ruta.texto:
                assert t in consulta.data


def test_visit_all_views_with_admin_session(client, auth):
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
    app.app_context().push()
    database.drop_all()
    initial_setup()
    auth.login()
    assert app.config["SQLALCHEMY_DATABASE_URI"] == "sqlite://"
    for ruta in rutas_estaticas:
        consulta = client.get(ruta.ruta)
        assert consulta.status_code == ruta.admin
        if consulta.status_code == 200 and ruta.texto:
            for t in ruta.texto:
                assert t in consulta.data


formularios = [
    Forma(
        ruta="/new_program",
        datos={
            "nombre": "nombre",
            "descripcion": "descripcion",
            "precio": "precio",
            "codigo": "test",
        },
    ),
    Forma(
        ruta="new_tag",
        datos={
            "nombre": "test",
            "color": "#34e5eb",
        },
    ),
    Forma(
        ruta="/new_category",
        datos={
            "nombre": "test",
            "descripcion": "test",
        },
    ),
    Forma(ruta="/logon", datos={"usuario": "Carlos", "apellido": "Monge", "acceso": "gordo"}),
    Forma(
        ruta="/mail",
        datos={
            "email": "test@hola.com",
            "mail_server": "hello.com",
            "mail_port": "433",
            "mail_use_tls": True,
            "mail_use_ssl": True,
            "mail_username": "hello",
            "mail_password": "hola",
        },
    ),
]


def test_fill_all_forms(client, auth):
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
    app.app_context().push()
    database.drop_all()
    initial_setup(with_examples=True)
    auth.login()
    for f in formularios:
        client.get(f.ruta)
        client.post(f.ruta, data=f.datos)

    from now_lms.db import Usuario

    usario = Usuario.query.filter(Usuario.usuario == "student1").first()
    ruta = "/perfil/edit/" + usario.id
    get = client.get(ruta)
    assert get.status_code == 403
    usario = Usuario.query.filter(Usuario.usuario == "lms-admin").first()
    ruta = "/perfil/edit/" + usario.id
    post = client.post(
        ruta,
        data={
            "correo_electronico": "holahola.hello.net",
        },
        follow_redirects=False,
    )
    assert post.status_code == 302
    perfil = client.get("/perfil")
    assert b"holahola.hello.net" in perfil.data


def test_cambiar_curso(client, auth):
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
    app.app_context().push()
    database.drop_all()
    initial_setup()
    auth.login()
    client.get("/change_curse_public?curse=now")
    client.get("/change_curse_public?curse=now")
    client.get("/change_curse_status?curse=now&status=draft")
    client.get("/change_curse_status?curse=now&status=public")
    client.get("/change_curse_status?curse=now&status=open")
    client.get("/change_curse_status?curse=now&status=closed")


def test_indices_seccion():
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
    app.app_context().push()
    database.drop_all()
    initial_setup()
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
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
    app.app_context().push()
    database.drop_all()
    initial_setup()
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
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
    app.app_context().push()
    database.drop_all()
    initial_setup()
    from now_lms import CursoSeccion

    auth.login()

    SECCION = CursoSeccion.query.filter_by(nombre="How to sell a online course.").first()
    URL = "/course/now/" + SECCION.id + "/new_resource"
    get = client.get(URL)
    assert get.status_code == 200


def test_reorganizar_indice_seccion(client, auth):
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
    app.app_context().push()
    database.drop_all()
    initial_setup()
    from now_lms import CursoSeccion

    auth.login()

    get = client.get("/course/now/seccion/decrement/1")
    assert get.status_code == 302
    get = client.get("/course/now/seccion/increment/2")
    assert get.status_code == 302


def test_serve_files(client, auth):
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
    app.app_context().push()
    database.drop_all()
    initial_setup()
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
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
    app.app_context().push()
    database.drop_all()
    initial_setup()
    from now_lms.db import Curso

    cursos = Curso.query.all()

    auth.login()

    for curso in cursos:
        url = "/course/" + curso.codigo + "/description"
        page = client.get(url)
        assert page.status_code == 200


def test_edit_course(client, auth):
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
    app.app_context().push()
    database.drop_all()
    initial_setup()
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
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
    app.app_context().push()
    database.drop_all()
    initial_setup()
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
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
    app.app_context().push()
    database.drop_all()
    initial_setup()

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

    data = {
        "style": "dark",
    }
    data = {key: str(value) for key, value in data.items()}
    data["logo"] = (BytesIO(b"abcdef"), "logo.pdf")
    get = client.get("/theming")
    assert get.status_code == 200
    post = client.post("/theming", data=data, follow_redirects=True)
    assert post.status_code == 200


def test_crear_recursos(client, auth):
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
    app.app_context().push()
    database.drop_all()
    initial_setup(with_examples=False)
    from now_lms.db import CursoSeccion

    seccion = CursoSeccion.query.filter(CursoSeccion.curso == "now").first()
    base_url = "/course/now/" + seccion.id

    url = base_url + "/pdf/new"
    data = {"nombre": "test", "descripcion": "test pdf"}
    data = {key: str(value) for key, value in data.items()}
    data["pdf"] = (BytesIO(b"abcdef"), "test.pdf")
    auth.login()
    response = client.get(url)
    response = client.post(url, data=data, follow_redirects=True, content_type="multipart/form-data")
    assert response.status_code == 200

    url = base_url + "/img/new"
    data = {"nombre": "test", "descripcion": "test pdf"}
    data = {key: str(value) for key, value in data.items()}
    data["img"] = (BytesIO(b"abcdef"), "test.jpg")
    auth.login()
    response = client.get(url)
    response = client.post(url, data=data, follow_redirects=True, content_type="multipart/form-data")
    assert response.status_code == 200

    url = base_url + "/audio/new"
    data = {"nombre": "test", "descripcion": "test pdf"}
    data = {key: str(value) for key, value in data.items()}
    data["audio"] = (BytesIO(b"abcdef"), "test.ogg")
    auth.login()
    response = client.get(url)
    response = client.post(url, data=data, follow_redirects=True, content_type="multipart/form-data")
    assert response.status_code == 200

    url = base_url + "/youtube/new"
    data = {"nombre": "test", "descripcion": "test pdf", "youtube_url": "test"}
    data = {key: str(value) for key, value in data.items()}
    auth.login()
    response = client.get(url)
    response = client.post(url, data=data, follow_redirects=True)
    assert response.status_code == 200

    url = base_url + "/meet/new"
    data = {"nombre": "test", "descripcion": "test pdf", "url": "test"}
    data = {key: str(value) for key, value in data.items()}
    auth.login()
    response = client.get(url)
    response = client.post(url, data=data, follow_redirects=True)
    assert response.status_code == 200

    url = base_url + "/html/new"
    data = {"nombre": "test", "descripcion": "test pdf", "html_externo": "test"}
    data = {key: str(value) for key, value in data.items()}
    auth.login()
    response = client.get(url)
    response = client.post(url, data=data, follow_redirects=True)
    assert response.status_code == 200

    url = base_url + "/link/new"
    data = {"nombre": "test", "descripcion": "test pdf", "url": "test"}
    data = {key: str(value) for key, value in data.items()}
    auth.login()
    response = client.get(url)
    response = client.post(url, data=data, follow_redirects=True)
    assert response.status_code == 200

    url = base_url + "/text/new"
    data = {"nombre": "test", "descripcion": "test pdf", "editor": "test"}
    data = {key: str(value) for key, value in data.items()}
    auth.login()
    response = client.get(url)
    response = client.post(url, data=data, follow_redirects=True)
    assert response.status_code == 200


def test_eliminar_recursos(client, auth):
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
    app.app_context().push()
    database.drop_all()
    initial_setup()
    from now_lms.db import CursoRecurso

    auth.login()
    recursos = CursoRecurso.query.filter(CursoRecurso.curso == "resources").all()
    assert recursos is not None
    for recurso in recursos:
        url = "/delete_recurso/resources/" + recurso.seccion + "/" + recurso.id
        page = client.get(url)
        assert page.status_code == 302


def test_generar_indice_recurso():
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
    app.app_context().push()
    database.drop_all()
    initial_setup()
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
