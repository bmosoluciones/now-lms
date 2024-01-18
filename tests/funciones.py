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


import pytest
from io import BytesIO
from now_lms import app, database, initial_setup
from now_lms.db import Usuario


@pytest.fixture
def lms_application():
    from now_lms import app

    app.config.update(
        {
            "TESTING": True,
            "SECRET_KEY": "jgjañlsldaksjdklasjfkjj",
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
            "TESTING": True,
            "WTF_CSRF_ENABLED": False,
            "DEBUG": True,
            "PRESERVE_CONTEXT_ON_EXCEPTION": True,
            "SQLALCHEMY_ECHO": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
        }
    )

    yield app


def test_cambiar_curso(lms_application):

    from now_lms import database, initial_setup

    with lms_application.app_context():
        from flask_login import current_user

        database.drop_all()
        initial_setup()

        with lms_application.test_client() as client:
            # Keep the session alive until the with clausule closes

            client.post("/user/login", data={"usuario": "lms-admin", "acceso": "lms-admin"})
            assert current_user.is_authenticated
            assert current_user.tipo == "admin"
            client.get("/change_curse_public?curse=now")
            client.get("/change_curse_public?curse=now")
            client.get("/change_curse_status?curse=now&status=draft")
            client.get("/change_curse_status?curse=now&status=public")
            client.get("/change_curse_status?curse=now&status=open")
            client.get("/change_curse_status?curse=now&status=closed")


def test_indices_seccion():
    from now_lms import database, initial_setup
    from now_lms.db import Curso, CursoSeccion

    with lms_application.app_context():
        from flask_login import current_user

        database.drop_all()
        initial_setup()

        with lms_application.test_client() as client:
            # Keep the session alive until the with clausule closes

            client.post("/user/login", data={"usuario": "lms-admin", "acceso": "lms-admin"})
            assert current_user.is_authenticated
            assert current_user.tipo == "admin"
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
    app.app_context().push()
    database.drop_all()
    initial_setup()

    auth.login()

    get = client.get("/course/now/seccion/decrement/1")
    assert get.status_code == 302
    get = client.get("/course/now/seccion/increment/2")
    assert get.status_code == 302


def test_serve_files(client, auth):
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


def test_crear_usuario(client):
    app.app_context().push()
    database.drop_all()
    initial_setup(with_examples=False)

    url = "/logon"
    data = {"usuario": "testing", "acceso": "testing"}

    response = client.get(url)
    response = client.post(url, data=data, follow_redirects=True)
    assert response.status_code == 200

    usuario_ = database.session.execute(database.select(Usuario).filter(Usuario.usuario == "testing")).first()[0]

    # Editar correo de usuario.
    data = {"usuario": "testing", "acceso": "testing", "correo_electronico": "testing1@dominio.net"}

    url = "/perfil/edit/" + usuario_.id

    response = client.post(url, data=data, follow_redirects=True)
    assert response.status_code == 200

    data = {"usuario": "testing", "acceso": "testing", "correo_electronico": "testing2@dominio.net"}
    response = client.post(url, data=data, follow_redirects=True)
    assert response.status_code == 200

    bytesio_object = BytesIO(b"Hello World!")

    from os import path, makedirs
    from now_lms.config import DIRECTORIO_UPLOAD_IMAGENES

    file_name = usuario_.id + ".jpg"
    directorio = path.join(DIRECTORIO_UPLOAD_IMAGENES, "usuarios")
    try:
        makedirs(directorio)
    except FileExistsError:
        pass

    with open(
        path.join(directorio, file_name),
        "wb",
    ) as f:
        f.write(bytesio_object.getbuffer())

    url = "/perfil/" + usuario_.id + "/delete_logo"

    response = client.get(url, follow_redirects=True)
    assert response.status_code == 200


def test_activar_inactivar_eliminar_usuario(client, auth):
    app.app_context().push()
    database.drop_all()
    initial_setup(with_examples=True)
    auth.login()

    perfil_usuario = database.session.execute(database.select(Usuario).filter(Usuario.usuario == "student")).first()[0]

    url = "/user/" + "student"
    response = client.get(url, follow_redirects=True)
    assert response.status_code == 200

    url = "/set_user_as_inactive/" + perfil_usuario.id
    response = client.get(url, follow_redirects=True)
    assert response.status_code == 200

    response = client.get(url, follow_redirects=True)
    assert b"Usuario ya se encuentra definido como inactivo" in response.data

    url = "/set_user_as_active/" + perfil_usuario.id
    response = client.get(url, follow_redirects=True)
    assert response.status_code == 200

    response = client.get(url, follow_redirects=True)
    assert b"Usuario ya se encuentra definido como activo" in response.data

    url = "/delete_user/" + perfil_usuario.id
    response = client.get(url, follow_redirects=True)
    assert response.status_code == 200


def test_eliminar_logo_curso(client, auth):
    app.app_context().push()
    database.drop_all()
    initial_setup(with_examples=True)
    auth.login()

    bytesio_object = BytesIO(b"Hello World!")

    from os import path, makedirs
    from now_lms.config import DIRECTORIO_UPLOAD_IMAGENES

    file_name = "logo.jpg"
    directorio = path.join(DIRECTORIO_UPLOAD_IMAGENES, "now")
    try:
        makedirs(directorio)
    except FileExistsError:
        pass

    with open(
        path.join(directorio, file_name),
        "wb",
    ) as f:
        f.write(bytesio_object.getbuffer())

    url = "/now/delete_logo"

    response = client.get(url, follow_redirects=True)
    assert response.status_code == 200


def test_eliminar_logo_programa(client, auth):
    app.app_context().push()
    database.drop_all()
    initial_setup(with_examples=True)
    auth.login()

    bytesio_object = BytesIO(b"Hello World!")

    from os import path, makedirs
    from now_lms.config import DIRECTORIO_UPLOAD_IMAGENES

    file_name = "logo.jpg"
    directorio = path.join(DIRECTORIO_UPLOAD_IMAGENES, "programP001")
    try:
        makedirs(directorio)
    except FileExistsError:
        pass

    with open(
        path.join(directorio, file_name),
        "wb",
    ) as f:
        f.write(bytesio_object.getbuffer())

    from now_lms.db import Programa

    programa_ = Programa.query.filter_by(codigo="P001").first()

    url = "/program/" + programa_.id + "/delete_logo"

    response = client.get(url, follow_redirects=True)
    assert response.status_code == 200


def test_crear_recursos(client, auth):
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


def test_crear_recursos_no_files(client, auth):
    app.app_context().push()
    database.drop_all()
    initial_setup(with_examples=False)

    from now_lms.db import CursoSeccion

    seccion = CursoSeccion.query.filter(CursoSeccion.curso == "now").first()
    base_url = "/course/now/" + seccion.id

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


def test_eliminar_archivos():
    app.app_context().push()
    database.drop_all()
    initial_setup()
    from os import path
    from now_lms.config import DIRECTORIO_UPLOAD_IMAGENES
    from now_lms.db.tools import elimina_logo_perzonalizado, elimina_logo_perzonalizado_curso

    bytesio_object = BytesIO(b"Hello World!")

    with open(path.join(DIRECTORIO_UPLOAD_IMAGENES, "logotipo.jpg"), "wb") as f:
        f.write(bytesio_object.getbuffer())

    elimina_logo_perzonalizado()
    elimina_logo_perzonalizado_curso("now")


def test_eliminar_logo(client, auth):
    app.app_context().push()
    database.drop_all()
    initial_setup()

    auth.login()

    from os import path
    from now_lms.config import DIRECTORIO_UPLOAD_IMAGENES
    from io import BytesIO

    bytesio_object = BytesIO(b"Hello World!")

    with open(path.join(DIRECTORIO_UPLOAD_IMAGENES, "logotipo.jpg"), "wb") as f:
        f.write(bytesio_object.getbuffer())

    page = client.get("/delete_logo")

    assert page.status_code == 302
