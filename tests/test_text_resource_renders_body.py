# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""The text-resource page must render the lesson body, not only the blurb.

Fork issue #43: ``CursoRecurso.text`` is the body column for a text resource
and ``descripcion`` is a one-line blurb, but the template rendered only
``descripcion``. Every seeded lesson (which writes the whole lesson into
``text`` and a "Reading for ..." stub into ``descripcion``) displayed the stub
and nothing else, while returning HTTP 200 — so no status assertion could
catch it. These tests assert on the rendered body text itself.
"""

from now_lms.auth import proteger_passwd
from now_lms.db import CursoRecurso, CursoSeccion, Usuario, database

REDIRECT_STATUS_CODES = {301, 302, 303, 307, 308}

# Distinctive mid-body sentence per issue #43's verification note: identical
# stub pages are the symptom, so the assertion must be on body prose.
BODY_SENTENCE = "The advisory flock serialises concurrent worker boots"
BODY_MARKDOWN = f"""# Lesson one

Welcome to the lesson.

{BODY_SENTENCE}, which is the kind of sentence a stub line never contains.

Closing paragraph.
"""
STUB_BLURB = "Reading for Lesson one"


def _instructor_client(app, db_session):
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
    client = app.test_client()
    resp = client.post("/user/login", data={"usuario": "instr", "acceso": "instr"}, follow_redirects=False)
    assert resp.status_code in REDIRECT_STATUS_CODES | {200}
    return client


def _course_with_section(client, db_session, code):
    resp = client.post(
        "/course/new_curse",
        data={
            "nombre": "Curso texto",
            "descripcion": "Descripcion del curso",
            "codigo": code,
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
    assert resp.status_code in REDIRECT_STATUS_CODES | {200}
    resp = client.post(
        f"/course/{code}/new_seccion",
        data={"nombre": "Seccion 1", "descripcion": "Descripcion de seccion"},
        follow_redirects=False,
    )
    assert resp.status_code in REDIRECT_STATUS_CODES | {200}
    seccion = (
        db_session.execute(database.select(CursoSeccion).filter_by(curso=code).order_by(CursoSeccion.indice))
        .scalars()
        .first()
    )
    assert seccion is not None
    return seccion


def test_editor_created_text_resource_renders_its_body(app, db_session):
    """A lesson written through the editor form must reach the page."""
    client = _instructor_client(app, db_session)
    seccion = _course_with_section(client, db_session, "txbody1")

    resp = client.post(
        f"/course/txbody1/{seccion.id}/text/new",
        data={
            "nombre": "Lesson one",
            "descripcion": STUB_BLURB,
            "requerido": "required",
            "editor": BODY_MARKDOWN,
        },
        follow_redirects=False,
    )
    assert resp.status_code in REDIRECT_STATUS_CODES | {200}
    recurso = (
        db_session.execute(database.select(CursoRecurso).filter_by(seccion=seccion.id, tipo="text")).scalars().first()
    )
    assert recurso is not None and recurso.text

    page = client.get(f"/course/txbody1/resource/text/{recurso.id}")
    assert page.status_code == 200
    html = page.get_data(as_text=True)
    assert BODY_SENTENCE in html, "the lesson body stored in CursoRecurso.text never reached the page"


def test_seeder_shaped_text_resource_renders_body_not_stub(app, db_session):
    """A row shaped like the CCA seeder writes it (body in `text`, stub in
    `descripcion`) must render the body — this is the exact issue #43 shape."""
    client = _instructor_client(app, db_session)
    seccion = _course_with_section(client, db_session, "txbody2")

    recurso = CursoRecurso(
        curso="txbody2",
        seccion=seccion.id,
        tipo="text",
        nombre="Lesson: Signing in",
        descripcion="Reading for Signing in",
        text=BODY_MARKDOWN,
        requerido="required",
        indice=1,
        publico=False,
    )
    db_session.add(recurso)
    db_session.commit()

    page = client.get(f"/course/txbody2/resource/text/{recurso.id}")
    assert page.status_code == 200
    html = page.get_data(as_text=True)
    assert BODY_SENTENCE in html, "seeded lesson body (CursoRecurso.text) must render"


def test_text_resource_without_body_falls_back_to_descripcion(app, db_session):
    """Upstream rows that only fill `descripcion` keep rendering it."""
    client = _instructor_client(app, db_session)
    seccion = _course_with_section(client, db_session, "txbody3")

    recurso = CursoRecurso(
        curso="txbody3",
        seccion=seccion.id,
        tipo="text",
        nombre="Blurb only",
        descripcion="A descripcion-only resource keeps its historical rendering.",
        text=None,
        requerido="optional",
        indice=1,
        publico=False,
    )
    db_session.add(recurso)
    db_session.commit()

    page = client.get(f"/course/txbody3/resource/text/{recurso.id}")
    assert page.status_code == 200
    html = page.get_data(as_text=True)
    assert "A descripcion-only resource keeps its historical rendering." in html
