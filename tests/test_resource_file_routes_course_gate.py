# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""
Regression tests for the course gate on raw resource routes.

`pagina_recurso` and `slide_show` already route through `_resource_is_viewable()`,
which requires a course to still be public and open before its `publico` resources
are served to unauthenticated or non-entitled visitors. These tests extend the same
rule to the raw file, subtitle (VTT) and PDF-viewer routes:

- `recurso_file`, `recurso_vtt`, `recurso_vtt_secondary` and `pdf_viewer` used to
  grant access on the resource's own `publico` flag alone, so a free-preview file
  stayed readable after its course was unpublished, made private, or closed.

Each route must now answer 403 when the resource is a free preview of a course that
is no longer public and open, while keeping the legitimate preview and enrolled
paths working.
"""

from now_lms.auth import proteger_passwd
from now_lms.db import Curso, CursoRecurso, CursoSeccion, EstudianteCurso, Usuario


def _crear_curso(db_session, code: str, publico: bool = True, estado: str = "open") -> Curso:
    curso = Curso(
        nombre=f"Curso {code}",
        codigo=code,
        descripcion_corta="Desc corta",
        descripcion="Desc",
        estado=estado,
        publico=publico,
        modalidad="self_paced",
        foro_habilitado=False,
    )
    db_session.add(curso)
    db_session.commit()
    return curso


def _crear_seccion(db_session, curso: Curso) -> CursoSeccion:
    seccion = CursoSeccion(curso=curso.codigo, nombre="S1", descripcion="D", indice=1, estado=True)
    db_session.add(seccion)
    db_session.commit()
    return seccion


def _crear_recurso(
    db_session,
    curso: Curso,
    seccion: CursoSeccion,
    publico: bool = True,
    tipo: str = "text",
    base_doc_url: str | None = None,
    doc: str | None = None,
    subtitle_vtt: str | None = None,
    subtitle_vtt_secondary: str | None = None,
) -> CursoRecurso:
    recurso = CursoRecurso(
        curso=curso.codigo,
        seccion=seccion.id,
        tipo=tipo,
        nombre="Recurso",
        descripcion="Contenido",
        requerido="required",
        indice=1,
        publico=publico,
        base_doc_url=base_doc_url,
        doc=doc,
        subtitle_vtt=subtitle_vtt,
        subtitle_vtt_secondary=subtitle_vtt_secondary,
    )
    db_session.add(recurso)
    db_session.commit()
    return recurso


def _crear_estudiante(db_session, usuario: str = "otro_alumno") -> Usuario:
    user = Usuario(
        usuario=usuario,
        acceso=proteger_passwd(usuario),
        nombre="Otro",
        correo_electronico=f"{usuario}@example.com",
        tipo="student",
        activo=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


def _inscribir(db_session, curso: Curso, usuario: str) -> None:
    db_session.add(EstudianteCurso(curso=curso.codigo, usuario=usuario, vigente=True, creado_por="test"))
    db_session.commit()


def _login(client, usuario: str) -> None:
    resp = client.post("/user/login", data={"usuario": usuario, "acceso": usuario}, follow_redirects=False)
    assert resp.status_code in {200, 301, 302, 303, 307, 308}


# --------------------------------------------------------------------------------------
# Denied: a `publico` resource of a course that is no longer public/open
# --------------------------------------------------------------------------------------


def test_recurso_file_denied_for_publico_resource_of_private_course(app, db_session):
    curso = _crear_curso(db_session, "cf_priv", publico=False, estado="open")
    seccion = _crear_seccion(db_session, curso)
    recurso = _crear_recurso(db_session, curso, seccion, publico=True, base_doc_url="files", doc="p.pdf")
    _crear_estudiante(db_session, "sin_matricula")

    with app.test_client() as client:
        _login(client, "sin_matricula")
        resp = client.get(f"/course/{curso.codigo}/files/{recurso.id}")

    assert resp.status_code == 403


def test_recurso_file_denied_for_publico_resource_of_closed_course(app, db_session):
    curso = _crear_curso(db_session, "cf_draft", publico=True, estado="draft")
    seccion = _crear_seccion(db_session, curso)
    recurso = _crear_recurso(db_session, curso, seccion, publico=True, base_doc_url="files", doc="p.pdf")
    _crear_estudiante(db_session, "sin_matricula")

    with app.test_client() as client:
        _login(client, "sin_matricula")
        resp = client.get(f"/course/{curso.codigo}/files/{recurso.id}")

    assert resp.status_code == 403


def test_recurso_vtt_denied_for_publico_resource_of_private_course(app, db_session):
    curso = _crear_curso(db_session, "cv_priv", publico=False, estado="open")
    seccion = _crear_seccion(db_session, curso)
    recurso = _crear_recurso(db_session, curso, seccion, publico=True, subtitle_vtt="WEBVTT\n\n00:00:00.000 --> 00:00:01.000\nHola")
    _crear_estudiante(db_session, "sin_matricula")

    with app.test_client() as client:
        _login(client, "sin_matricula")
        resp = client.get(f"/course/{curso.codigo}/vtt/{recurso.id}")

    assert resp.status_code == 403


def test_recurso_vtt_secondary_denied_for_publico_resource_of_private_course(app, db_session):
    curso = _crear_curso(db_session, "cvs_priv", publico=False, estado="open")
    seccion = _crear_seccion(db_session, curso)
    recurso = _crear_recurso(db_session, curso, seccion, publico=True, subtitle_vtt_secondary="WEBVTT\n\n00:00:00.000 --> 00:00:01.000\nHola")
    _crear_estudiante(db_session, "sin_matricula")

    with app.test_client() as client:
        _login(client, "sin_matricula")
        resp = client.get(f"/course/{curso.codigo}/vtt_secondary/{recurso.id}")

    assert resp.status_code == 403


def test_pdf_viewer_denied_for_publico_resource_of_private_course(app, db_session):
    curso = _crear_curso(db_session, "cp_priv", publico=False, estado="open")
    seccion = _crear_seccion(db_session, curso)
    recurso = _crear_recurso(db_session, curso, seccion, publico=True, tipo="pdf")
    _crear_estudiante(db_session, "sin_matricula")

    with app.test_client() as client:
        _login(client, "sin_matricula")
        resp = client.get(f"/course/{curso.codigo}/pdf_viewer/{recurso.id}")

    assert resp.status_code == 403


def test_pdf_viewer_denied_for_publico_resource_of_closed_course(app, db_session):
    curso = _crear_curso(db_session, "cp_draft", publico=True, estado="draft")
    seccion = _crear_seccion(db_session, curso)
    recurso = _crear_recurso(db_session, curso, seccion, publico=True, tipo="pdf")
    _crear_estudiante(db_session, "sin_matricula")

    with app.test_client() as client:
        _login(client, "sin_matricula")
        resp = client.get(f"/course/{curso.codigo}/pdf_viewer/{recurso.id}")

    assert resp.status_code == 403


# --------------------------------------------------------------------------------------
# Controls: legitimate preview and enrolled paths must keep working
# --------------------------------------------------------------------------------------


def test_recurso_vtt_still_serves_free_preview_of_public_open_course(app, db_session):
    curso = _crear_curso(db_session, "cv_pub", publico=True, estado="open")
    seccion = _crear_seccion(db_session, curso)
    recurso = _crear_recurso(db_session, curso, seccion, publico=True, subtitle_vtt="WEBVTT\n\n00:00:00.000 --> 00:00:01.000\nHola")
    _crear_estudiante(db_session, "sin_matricula")

    with app.test_client() as client:
        _login(client, "sin_matricula")
        resp = client.get(f"/course/{curso.codigo}/vtt/{recurso.id}")

    assert resp.status_code == 200
    assert "WEBVTT" in resp.data.decode("utf-8")


def test_recurso_vtt_serves_enrolled_student_of_private_course(app, db_session):
    curso = _crear_curso(db_session, "cv_mat", publico=False, estado="open")
    seccion = _crear_seccion(db_session, curso)
    recurso = _crear_recurso(db_session, curso, seccion, publico=False, subtitle_vtt="WEBVTT\n\n00:00:00.000 --> 00:00:01.000\nHola")
    _crear_estudiante(db_session, "matriculado")
    _inscribir(db_session, curso, "matriculado")

    with app.test_client() as client:
        _login(client, "matriculado")
        resp = client.get(f"/course/{curso.codigo}/vtt/{recurso.id}")

    assert resp.status_code == 200


def test_pdf_viewer_serves_enrolled_student_of_private_course(app, db_session):
    curso = _crear_curso(db_session, "cp_mat", publico=False, estado="open")
    seccion = _crear_seccion(db_session, curso)
    recurso = _crear_recurso(db_session, curso, seccion, publico=False, tipo="pdf")
    _crear_estudiante(db_session, "matriculado")
    _inscribir(db_session, curso, "matriculado")

    with app.test_client() as client:
        _login(client, "matriculado")
        resp = client.get(f"/course/{curso.codigo}/pdf_viewer/{recurso.id}")

    assert resp.status_code == 200


def test_recurso_file_not_denied_for_enrolled_student_of_private_course(app, db_session):
    """The raw file route may 200 or 404 (no file on disk), but never 403 for an enrolled student."""
    curso = _crear_curso(db_session, "cf_mat", publico=False, estado="open")
    seccion = _crear_seccion(db_session, curso)
    recurso = _crear_recurso(db_session, curso, seccion, publico=False, base_doc_url="files", doc="p.pdf")
    _crear_estudiante(db_session, "matriculado")
    _inscribir(db_session, curso, "matriculado")

    with app.test_client() as client:
        _login(client, "matriculado")
        resp = client.get(f"/course/{curso.codigo}/files/{recurso.id}")

    assert resp.status_code != 403
