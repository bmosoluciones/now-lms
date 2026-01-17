# Copyright 2025 BMO Soluciones, S.A.
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

import io
from datetime import date, time

import pytest

from now_lms.auth import proteger_passwd
from now_lms.db import Configuracion, Curso, CursoRecurso, CursoSeccion, Usuario, database


REDIRECT_STATUS_CODES = {301, 302, 303, 307, 308}


def _crear_instructor(db_session) -> Usuario:
    user = Usuario(
        usuario="instr",
        acceso=proteger_passwd("instr"),
        nombre="Instructor",
        correo_electronico="instr@example.com",
        tipo="instructor",
        activo=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


def _login_instructor(app):
    client = app.test_client()
    resp = client.post("/user/login", data={"usuario": "instr", "acceso": "instr"}, follow_redirects=False)
    assert resp.status_code in REDIRECT_STATUS_CODES | {200}
    return client


def _ultimo_recurso(seccion_id: str, tipo: str | None = None) -> CursoRecurso:
    query = database.select(CursoRecurso).filter(CursoRecurso.seccion == seccion_id)
    if tipo:
        query = query.filter(CursoRecurso.tipo == tipo)
    return database.session.execute(query.order_by(CursoRecurso.indice.desc())).scalars().first()


@pytest.mark.parametrize(
    "tipos",
    [
        [
            "html",
            "youtube",
            "text",
            "link",
            "pdf",
            "meet",
            "img",
            "mp3",
            "slides",
        ]
    ],
)
def test_e2e_curso_seccion_y_recursos(app, db_session, tipos):
    # 1) Crear instructor y login
    _crear_instructor(db_session)
    client = _login_instructor(app)

    # 2) Crear curso via POST
    curso_code = "curso_e2e"
    resp_new_course = client.post(
        "/course/new_curse",
        data={
            "nombre": "Curso E2E",
            "descripcion": "Descripcion del curso",
            "codigo": curso_code,
            "descripcion_corta": "Corta",
            "nivel": "0",
            "duracion": "1",
            "publico": "y",
            "modalidad": "self_paced",
            "foro_habilitado": "",
            "limitado": "",
            "capacidad": "0",
            "pagado": "",
            "auditable": "",
            "certificado": "",
            "precio": "0",
        },
        follow_redirects=False,
    )
    assert resp_new_course.status_code in REDIRECT_STATUS_CODES | {200}
    curso_obj = db_session.execute(database.select(Curso).filter_by(codigo=curso_code)).scalars().first()
    assert curso_obj is not None

    # 3) Crear sección via POST
    resp_new_section = client.post(
        f"/course/{curso_code}/new_seccion",
        data={
            "nombre": "Seccion 1",
            "descripcion": "Descripcion de seccion",
        },
        follow_redirects=False,
    )
    assert resp_new_section.status_code in REDIRECT_STATUS_CODES | {200}
    seccion_obj = (
        db_session.execute(database.select(CursoSeccion).filter_by(curso=curso_code).order_by(CursoSeccion.indice))
        .scalars()
        .first()
    )
    assert seccion_obj is not None

    # 4) Editar curso via POST
    resp_edit_course = client.post(
        f"/course/{curso_code}/edit",
        data={
            "nombre": "Curso E2E Editado",
            "descripcion": "Descripcion del curso editada",
            "codigo": curso_code,
            "descripcion_corta": "Corta",
            "nivel": "0",
            "duracion": "2",
            "publico": "y",
            "modalidad": "self_paced",
            "foro_habilitado": "",
            "limitado": "",
            "capacidad": "0",
            "pagado": "",
            "auditable": "",
            "certificado": "",
            "precio": "0",
        },
        follow_redirects=False,
    )
    assert resp_edit_course.status_code in REDIRECT_STATUS_CODES | {200}
    curso_editado = db_session.execute(database.select(Curso).filter_by(codigo=curso_code)).scalars().first()
    assert curso_editado is not None and curso_editado.nombre == "Curso E2E Editado"

    # 5) Editar sección via POST
    resp_edit_section = client.post(
        f"/course/{curso_code}/{seccion_obj.id}/edit",
        data={
            "nombre": "Seccion 1 Editada",
            "descripcion": "Descripcion seccion editada",
        },
        follow_redirects=False,
    )
    assert resp_edit_section.status_code in REDIRECT_STATUS_CODES | {200}
    seccion_editada = db_session.get(CursoSeccion, seccion_obj.id)
    assert seccion_editada is not None and seccion_editada.nombre == "Seccion 1 Editada"

    # 6) GET a la URL de nueva sección (solo visualización)
    resp_get_new_section = client.get(f"/course/{curso_code}/new_seccion", follow_redirects=False)
    assert resp_get_new_section.status_code in {200, *REDIRECT_STATUS_CODES}

    # Habilitar carga de archivos para recursos descargables en este entorno de prueba
    with app.app_context():
        config = database.session.execute(database.select(Configuracion)).scalars().first()
        if config:
            config.enable_file_uploads = True
            database.session.commit()
    db_session.expire_all()
    config_refreshed = db_session.execute(database.select(Configuracion)).scalars().first()
    assert config_refreshed and config_refreshed.enable_file_uploads is True

    # 7) Por cada tipo de recurso: crear, visualizar, editar, visualizar editado
    for tipo in tipos:
        if tipo == "html":
            # Crear HTML externo (blueprint course)
            resp_new = client.post(
                f"/course/{curso_code}/{seccion_obj.id}/html/new",
                data={
                    "nombre": "HTML R",
                    "descripcion": "Desc HTML",
                    "requerido": "required",
                    "html_externo": "<div>Hola</div>",
                },
                follow_redirects=False,
            )
            assert resp_new.status_code in REDIRECT_STATUS_CODES | {200}
            recurso = _ultimo_recurso(seccion_obj.id, "html")
            assert recurso and recurso.external_code and recurso.tipo == "html"

            # Visualizar
            resp_view = client.get(f"/course/{curso_code}/resource/html/{recurso.id}")
            assert resp_view.status_code == 200

            # Editar
            resp_edit = client.post(
                f"/course/{curso_code}/{seccion_obj.id}/html/{recurso.id}/edit",
                data={
                    "nombre": "HTML R Edit",
                    "descripcion": "Desc HTML Edit",
                    "requerido": "required",
                    "html_externo": "<div>Hola Edit</div>",
                },
                follow_redirects=False,
            )
            assert resp_edit.status_code in REDIRECT_STATUS_CODES | {200}

            # Visualizar editado
            resp_view2 = client.get(f"/course/{curso_code}/resource/html/{recurso.id}")
            assert resp_view2.status_code == 200

        elif tipo == "youtube":
            resp_new = client.post(
                f"/course/{curso_code}/{seccion_obj.id}/youtube/new",
                data={
                    "nombre": "YT R",
                    "descripcion": "Desc YT",
                    "requerido": "required",
                    "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                },
                follow_redirects=False,
            )
            assert resp_new.status_code in REDIRECT_STATUS_CODES | {200}
            recurso = _ultimo_recurso(seccion_obj.id, "youtube")
            assert recurso and recurso.url and recurso.tipo == "youtube"

            resp_view = client.get(f"/course/{curso_code}/resource/youtube/{recurso.id}")
            assert resp_view.status_code == 200

            resp_edit = client.post(
                f"/course/{curso_code}/{seccion_obj.id}/youtube/{recurso.id}/edit",
                data={
                    "nombre": "YT R Edit",
                    "descripcion": "Desc YT Edit",
                    "requerido": "required",
                    "youtube_url": "https://youtu.be/dQw4w9WgXcQ",
                },
                follow_redirects=False,
            )
            assert resp_edit.status_code in REDIRECT_STATUS_CODES | {200}
            resp_view2 = client.get(f"/course/{curso_code}/resource/youtube/{recurso.id}")
            assert resp_view2.status_code == 200

        elif tipo == "text":
            resp_new = client.post(
                f"/course/{curso_code}/{seccion_obj.id}/text/new",
                data={
                    "nombre": "TX R",
                    "descripcion": "Desc TX",
                    "requerido": "required",
                    "editor": "Contenido inicial",
                },
                follow_redirects=False,
            )
            assert resp_new.status_code in REDIRECT_STATUS_CODES | {200}
            recurso = _ultimo_recurso(seccion_obj.id, "text")
            assert recurso and recurso.text and recurso.tipo == "text"

            resp_view = client.get(f"/course/{curso_code}/resource/text/{recurso.id}")
            assert resp_view.status_code == 200

            resp_edit = client.post(
                f"/course/{curso_code}/{seccion_obj.id}/text/{recurso.id}/edit",
                data={
                    "nombre": "TX R Edit",
                    "descripcion": "Desc TX Edit",
                    "requerido": "required",
                    "editor": "Contenido editado",
                },
                follow_redirects=False,
            )
            assert resp_edit.status_code in REDIRECT_STATUS_CODES | {200}
            resp_view2 = client.get(f"/course/{curso_code}/resource/text/{recurso.id}")
            assert resp_view2.status_code == 200

        elif tipo == "link":
            resp_new = client.post(
                f"/course/{curso_code}/{seccion_obj.id}/link/new",
                data={
                    "nombre": "LK R",
                    "descripcion": "Desc LK",
                    "requerido": "required",
                    "url": "https://example.com",
                },
                follow_redirects=False,
            )
            assert resp_new.status_code in REDIRECT_STATUS_CODES | {200}
            recurso = _ultimo_recurso(seccion_obj.id, "link")
            assert recurso and recurso.url and recurso.tipo == "link"

            resp_view = client.get(f"/course/{curso_code}/resource/link/{recurso.id}")
            assert resp_view.status_code == 200

            resp_edit = client.post(
                f"/course/{curso_code}/{seccion_obj.id}/link/{recurso.id}/edit",
                data={
                    "nombre": "LK R Edit",
                    "descripcion": "Desc LK Edit",
                    "requerido": "required",
                    "url": "https://example.org",
                },
                follow_redirects=False,
            )
            assert resp_edit.status_code in REDIRECT_STATUS_CODES | {200}
            resp_view2 = client.get(f"/course/{curso_code}/resource/link/{recurso.id}")
            assert resp_view2.status_code == 200

        elif tipo == "pdf":
            pdf_bytes = io.BytesIO(b"%PDF-1.4\n%Test PDF\n")
            resp_new = client.post(
                f"/course/{curso_code}/{seccion_obj.id}/pdf/new",
                data={
                    "nombre": "PDF R",
                    "descripcion": "Desc PDF",
                    "requerido": "required",
                    "pdf": (pdf_bytes, "doc.pdf"),
                },
                content_type="multipart/form-data",
                follow_redirects=False,
            )
            assert resp_new.status_code in REDIRECT_STATUS_CODES | {200}
            recurso = _ultimo_recurso(seccion_obj.id, "pdf")
            assert recurso and recurso.doc and recurso.tipo == "pdf"

            resp_view = client.get(f"/course/{curso_code}/resource/pdf/{recurso.id}")
            assert resp_view.status_code == 200

            pdf_bytes2 = io.BytesIO(b"%PDF-1.4\n%Test PDF 2\n")
            resp_edit = client.post(
                f"/course/{curso_code}/{seccion_obj.id}/pdf/{recurso.id}/edit",
                data={
                    "nombre": "PDF R Edit",
                    "descripcion": "Desc PDF Edit",
                    "requerido": "required",
                    "pdf": (pdf_bytes2, "doc2.pdf"),
                },
                content_type="multipart/form-data",
                follow_redirects=False,
            )
            assert resp_edit.status_code in REDIRECT_STATUS_CODES | {200}
            resp_view2 = client.get(f"/course/{curso_code}/resource/pdf/{recurso.id}")
            assert resp_view2.status_code == 200

        elif tipo == "meet":
            resp_new = client.post(
                f"/course/{curso_code}/{seccion_obj.id}/meet/new",
                data={
                    "nombre": "ME R",
                    "descripcion": "Desc ME",
                    "requerido": "required",
                    "url": "https://meet.example.com/room",
                    "fecha": date.today().strftime("%Y-%m-%d"),
                    "hora_inicio": time(9, 0).strftime("%H:%M"),
                    "hora_fin": time(10, 0).strftime("%H:%M"),
                    "notes": "google_meet",
                },
                follow_redirects=False,
            )
            assert resp_new.status_code in REDIRECT_STATUS_CODES | {200}
            recurso = _ultimo_recurso(seccion_obj.id, "meet")
            assert recurso and recurso.url and recurso.tipo == "meet"

            resp_view = client.get(f"/course/{curso_code}/resource/meet/{recurso.id}")
            assert resp_view.status_code == 200

            resp_edit = client.post(
                f"/course/{curso_code}/{seccion_obj.id}/meet/{recurso.id}/edit",
                data={
                    "nombre": "ME R Edit",
                    "descripcion": "Desc ME Edit",
                    "requerido": "required",
                    "url": "https://meet.example.com/room2",
                    "fecha": date.today().strftime("%Y-%m-%d"),
                    "hora_inicio": time(11, 0).strftime("%H:%M"),
                    "hora_fin": time(12, 0).strftime("%H:%M"),
                    "notes": "zoom",
                },
                follow_redirects=False,
            )
            assert resp_edit.status_code in REDIRECT_STATUS_CODES | {200}
            resp_view2 = client.get(f"/course/{curso_code}/resource/meet/{recurso.id}")
            assert resp_view2.status_code == 200

        elif tipo == "img":
            img_bytes = io.BytesIO(b"\x89PNG\r\n\x1a\n")
            resp_new = client.post(
                f"/course/{curso_code}/{seccion_obj.id}/img/new",
                data={
                    "nombre": "IM R",
                    "descripcion": "Desc IM",
                    "requerido": "required",
                    "img": (img_bytes, "image.png"),
                },
                content_type="multipart/form-data",
                follow_redirects=False,
            )
            assert resp_new.status_code in REDIRECT_STATUS_CODES | {200}
            recurso = _ultimo_recurso(seccion_obj.id, "img")
            assert recurso and recurso.doc and recurso.tipo == "img"

            resp_view = client.get(f"/course/{curso_code}/resource/img/{recurso.id}")
            assert resp_view.status_code == 200

            img_bytes2 = io.BytesIO(b"\x89PNG\r\n\x1a\n")
            resp_edit = client.post(
                f"/course/{curso_code}/{seccion_obj.id}/img/{recurso.id}/edit",
                data={
                    "nombre": "IM R Edit",
                    "descripcion": "Desc IM Edit",
                    "requerido": "required",
                    "img": (img_bytes2, "image2.png"),
                },
                content_type="multipart/form-data",
                follow_redirects=False,
            )
            assert resp_edit.status_code in REDIRECT_STATUS_CODES | {200}
            resp_view2 = client.get(f"/course/{curso_code}/resource/img/{recurso.id}")
            assert resp_view2.status_code == 200

        elif tipo == "mp3":
            audio_bytes = io.BytesIO(b"ID3")
            vtt_bytes = io.BytesIO(b"WEBVTT\n\n00:00.000 --> 00:00.500\nHola\n")
            resp_new = client.post(
                f"/course/{curso_code}/{seccion_obj.id}/audio/new",
                data={
                    "nombre": "AU R",
                    "descripcion": "Desc AU",
                    "requerido": "required",
                    "audio": (audio_bytes, "audio.mp3"),
                    "vtt_subtitle": (vtt_bytes, "sub.vtt"),
                },
                content_type="multipart/form-data",
                follow_redirects=False,
            )
            assert resp_new.status_code in REDIRECT_STATUS_CODES | {200}
            recurso = _ultimo_recurso(seccion_obj.id, "mp3")
            assert recurso and recurso.doc and recurso.tipo == "mp3"

            resp_view = client.get(f"/course/{curso_code}/resource/mp3/{recurso.id}")
            assert resp_view.status_code == 200

            audio_bytes2 = io.BytesIO(b"ID3")
            resp_edit = client.post(
                f"/course/{curso_code}/{seccion_obj.id}/audio/{recurso.id}/edit",
                data={
                    "nombre": "AU R Edit",
                    "descripcion": "Desc AU Edit",
                    "requerido": "required",
                    "audio": (audio_bytes2, "audio2.mp3"),
                    # sin vtt para probar ramas opcionales
                },
                content_type="multipart/form-data",
                follow_redirects=False,
            )
            assert resp_edit.status_code in REDIRECT_STATUS_CODES | {200}
            resp_view2 = client.get(f"/course/{curso_code}/resource/mp3/{recurso.id}")
            assert resp_view2.status_code == 200

        elif tipo == "descargable":
            pytest.xfail("Pendiente corregir flujo de carga de archivos descargables en tests")
            file_bytes = io.BytesIO(b"hello")
            resp_new = client.post(
                f"/course/{curso_code}/{seccion_obj.id}/descargable/new",
                data={
                    "nombre": "DG R",
                    "descripcion": "Desc DG",
                    "requerido": "required",
                    "archivo": (file_bytes, "file.txt"),
                },
                content_type="multipart/form-data",
                follow_redirects=False,
            )
            assert resp_new.status_code in REDIRECT_STATUS_CODES | {200}
            recurso = _ultimo_recurso(seccion_obj.id, "descargable")
            assert recurso and recurso.doc and recurso.tipo == "descargable"

            resp_view = client.get(f"/course/{curso_code}/resource/descargable/{recurso.id}")
            assert resp_view.status_code == 200

            file_bytes2 = io.BytesIO(b"hello2")
            resp_edit = client.post(
                f"/course/{curso_code}/{seccion_obj.id}/descargable/{recurso.id}/edit",
                data={
                    "nombre": "DG R Edit",
                    "descripcion": "Desc DG Edit",
                    "requerido": "required",
                    "archivo": (file_bytes2, "file2.txt"),
                },
                content_type="multipart/form-data",
                follow_redirects=False,
            )
            assert resp_edit.status_code in REDIRECT_STATUS_CODES | {200}
            resp_view2 = client.get(f"/course/{curso_code}/resource/descargable/{recurso.id}")
            assert resp_view2.status_code == 200

        elif tipo == "slides":
            resp_new = client.post(
                f"/course/{curso_code}/{seccion_obj.id}/slides/new",
                data={
                    "nombre": "SL R",
                    "descripcion": "Desc SL",
                    "theme": "simple",
                },
                follow_redirects=False,
            )
            assert resp_new.status_code in REDIRECT_STATUS_CODES | {200}
            recurso = _ultimo_recurso(seccion_obj.id, "slides")
            assert recurso and recurso.external_code and recurso.tipo == "slides"

            # Visualizar slideshow preview y pagina recurso
            resp_preview = client.get(f"/course/{curso_code}/slideshow/{recurso.external_code}/preview")
            assert resp_preview.status_code == 200
            resp_view = client.get(f"/course/{curso_code}/resource/slides/{recurso.id}")
            assert resp_view.status_code == 200

            # Editar slideshow: actualizar título y una slide
            resp_edit = client.post(
                f"/course/{curso_code}/slideshow/{recurso.external_code}/edit",
                data={
                    "title": "SL R Edit",
                    "theme": "simple",
                    "slide_count": "1",
                    "slide_0_title": "Intro",
                    "slide_0_content": "Contenido",
                    "slide_0_order": "1",
                },
                follow_redirects=False,
            )
            assert resp_edit.status_code in REDIRECT_STATUS_CODES | {200}
            resp_view2 = client.get(f"/course/{curso_code}/resource/slides/{recurso.id}")
            assert resp_view2.status_code == 200
