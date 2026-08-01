# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""
Regression tests for the course gate on the resource routes that were missed
by the first pass (`fix(security): apply the course gate to raw resource file
routes` and `fix(security): require course entitlement before serving course
resources`).

`pagina_recurso`, `slide_show`, `recurso_file`, `recurso_vtt`,
`recurso_vtt_secondary` and `pdf_viewer` already route through
`_resource_is_viewable()`. The three routes exercised here used to accept a
`publico` resource on its own flag, with no check on `Curso.publico` or
`Curso.estado`:

- `external_code` returned the resource's `external_code` (the raw HTML / iframe
  for an `html` resource) to any logged-in user when the resource was
  `publico`, even on a private or closed course.
- `pagina_recurso_alternativo` rendered the alternative-resource sidebar to any
  logged-in student when the resource was `publico`, and loaded the resource by
  id alone with no `CursoRecurso.curso == curso_id` filter, so a resource could
  be rendered in the context of an unrelated course.
- `_meet_resource_context` (used by `download_meet_calendar`,
  `google_calendar_link` and `outlook_calendar_link`) accepted a `publico` meet
  resource from any logged-in user, regardless of course state, exposing the
  meet URL and the Google/Outlook calendar deeplink.

Each of the three now answers 403 when the resource is a free preview of a
course that is no longer public and open, while the legitimate preview,
enrolled-student, assigned-instructor and admin paths keep working.
"""

from now_lms.auth import proteger_passwd
from now_lms.db import (
    Curso,
    CursoRecurso,
    CursoSeccion,
    DocenteCurso,
    EstudianteCurso,
    Usuario,
)


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
    indice: int = 1,
    external_code: str | None = None,
) -> CursoRecurso:
    recurso = CursoRecurso(
        curso=curso.codigo,
        seccion=seccion.id,
        tipo=tipo,
        nombre="Recurso",
        descripcion="Contenido",
        requerido="required",
        indice=indice,
        publico=publico,
        external_code=external_code,
    )
    db_session.add(recurso)
    db_session.commit()
    return recurso


def _crear_usuario(db_session, usuario: str, tipo: str = "student") -> Usuario:
    user = Usuario(
        usuario=usuario,
        acceso=proteger_passwd(usuario),
        nombre=usuario.title(),
        correo_electronico=f"{usuario}@example.com",
        tipo=tipo,
        activo=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


def _inscribir(db_session, curso: Curso, usuario: str) -> None:
    db_session.add(EstudianteCurso(curso=curso.codigo, usuario=usuario, vigente=True, creado_por="test"))
    db_session.commit()


def _asignar_instructor(db_session, curso: Curso, usuario: str) -> None:
    db_session.add(DocenteCurso(curso=curso.codigo, usuario=usuario, vigente=True))
    db_session.commit()


def _login(client, usuario: str) -> None:
    resp = client.post("/user/login", data={"usuario": usuario, "acceso": usuario}, follow_redirects=False)
    assert resp.status_code in {200, 301, 302, 303, 307, 308}


# --------------------------------------------------------------------------------------
# external_code
# --------------------------------------------------------------------------------------


def test_external_code_denied_for_publico_resource_of_private_course(app, db_session):
    """A logged-in but non-enrolled user used to read the external_code of a free
    preview of a course that had been made private or unpublished.
    """
    curso = _crear_curso(db_session, "ec_priv", publico=False)
    seccion = _crear_seccion(db_session, curso)
    recurso = _crear_recurso(db_session, curso, seccion, publico=True, tipo="html", external_code="<iframe></iframe>")
    _crear_usuario(db_session, "no_matriculado")

    with app.test_client() as client:
        _login(client, "no_matriculado")
        resp = client.get(f"/course/{curso.codigo}/external_code/{recurso.id}")

    assert resp.status_code == 403


def test_external_code_denied_for_publico_resource_of_closed_course(app, db_session):
    curso = _crear_curso(db_session, "ec_draft", estado="draft")
    seccion = _crear_seccion(db_session, curso)
    recurso = _crear_recurso(db_session, curso, seccion, publico=True, tipo="html", external_code="<iframe></iframe>")
    _crear_usuario(db_session, "no_matriculado")

    with app.test_client() as client:
        _login(client, "no_matriculado")
        resp = client.get(f"/course/{curso.codigo}/external_code/{recurso.id}")

    assert resp.status_code == 403


def test_external_code_serves_free_preview_of_public_open_course(app, db_session):
    """The free-preview feature must keep working."""
    curso = _crear_curso(db_session, "ec_pub")
    seccion = _crear_seccion(db_session, curso)
    recurso = _crear_recurso(db_session, curso, seccion, publico=True, tipo="html", external_code="<iframe></iframe>")
    _crear_usuario(db_session, "no_matriculado")

    with app.test_client() as client:
        _login(client, "no_matriculado")
        resp = client.get(f"/course/{curso.codigo}/external_code/{recurso.id}")

    assert resp.status_code == 200
    assert b"<iframe></iframe>" in resp.data


def test_external_code_serves_enrolled_student_of_private_course(app, db_session):
    curso = _crear_curso(db_session, "ec_mat", publico=False)
    seccion = _crear_seccion(db_session, curso)
    recurso = _crear_recurso(db_session, curso, seccion, publico=False, tipo="html", external_code="<iframe></iframe>")
    _crear_usuario(db_session, "matriculado")
    _inscribir(db_session, curso, "matriculado")

    with app.test_client() as client:
        _login(client, "matriculado")
        resp = client.get(f"/course/{curso.codigo}/external_code/{recurso.id}")

    assert resp.status_code == 200


# --------------------------------------------------------------------------------------
# pagina_recurso_alternativo
# --------------------------------------------------------------------------------------


def test_pagina_recurso_alternativo_denied_for_publico_resource_of_private_course(app, db_session):
    """A student of a different course used to read the alternative-resource
    sidebar of a free preview of a private course.
    """
    curso = _crear_curso(db_session, "pa_priv", publico=False)
    seccion = _crear_seccion(db_session, curso)
    recurso = _crear_recurso(db_session, curso, seccion, publico=True)
    _crear_usuario(db_session, "otro_alumno")

    with app.test_client() as client:
        _login(client, "otro_alumno")
        resp = client.get(f"/course/{curso.codigo}/alternative/{recurso.id}/asc")

    assert resp.status_code == 403


def test_pagina_recurso_alternativo_denied_for_cross_course_render(app, db_session):
    """`curso_id` is attacker-controlled; the resource must not render under an
    unrelated course even if a `publico` resource with that id exists somewhere
    else. The view now filters on `CursoRecurso.curso == curso_id`.
    """
    curso_real = _crear_curso(db_session, "pa_real")
    seccion_real = _crear_seccion(db_session, curso_real)
    recurso_real = _crear_recurso(db_session, curso_real, seccion_real, publico=True)

    curso_mentira = _crear_curso(db_session, "pa_mentira", publico=True)
    _crear_usuario(db_session, "otro_alumno")

    with app.test_client() as client:
        _login(client, "otro_alumno")
        # The resource belongs to `pa_real`; the URL claims it belongs to `pa_mentira`.
        resp = client.get(f"/course/{curso_mentira.codigo}/alternative/{recurso_real.id}/asc")

    assert resp.status_code == 404


def test_pagina_recurso_alternativo_serves_enrolled_student_of_private_course(app, db_session):
    curso = _crear_curso(db_session, "pa_mat", publico=False)
    seccion = _crear_seccion(db_session, curso)
    recurso = _crear_recurso(db_session, curso, seccion, publico=False, indice=1)
    _crear_recurso(db_session, curso, seccion, publico=False, indice=2)
    _crear_usuario(db_session, "matriculado")
    _inscribir(db_session, curso, "matriculado")

    with app.test_client() as client:
        _login(client, "matriculado")
        resp = client.get(f"/course/{curso.codigo}/alternative/{recurso.id}/asc")

    assert resp.status_code == 200


# --------------------------------------------------------------------------------------
# _meet_resource_context (calendar.ics / google-calendar / outlook-calendar)
# --------------------------------------------------------------------------------------


def test_meet_calendar_denied_for_publico_resource_of_private_course(app, db_session):
    """A logged-in user used to receive the meet ICS file when the resource was
    `publico`, even on a private course. The defect was in the shared helper, so
    each of the three calendar routes inherited it.
    """
    curso = _crear_curso(db_session, "mc_priv", publico=False)
    seccion = _crear_seccion(db_session, curso)
    recurso = _crear_recurso(db_session, curso, seccion, publico=True, tipo="meet", indice=1)
    _crear_usuario(db_session, "otro_usuario")

    with app.test_client() as client:
        _login(client, "otro_usuario")
        resp = client.get(f"/course/{curso.codigo}/resource/meet/{recurso.id}/calendar.ics")

    assert resp.status_code == 403


def test_meet_calendar_serves_enrolled_student_of_private_course(app, db_session):
    curso = _crear_curso(db_session, "mc_mat", publico=False)
    seccion = _crear_seccion(db_session, curso)
    recurso = _crear_recurso(db_session, curso, seccion, publico=False, tipo="meet", indice=1)
    _crear_usuario(db_session, "matriculado")
    _inscribir(db_session, curso, "matriculado")

    with app.test_client() as client:
        _login(client, "matriculado")
        resp = client.get(f"/course/{curso.codigo}/resource/meet/{recurso.id}/calendar.ics")

    # 200 (ICS) or 302/redirect are both acceptable - what matters is the user
    # is no longer denied with a 403.
    assert resp.status_code != 403


def test_meet_calendar_serves_assigned_instructor_of_private_course(app, db_session):
    """The previous helper let any instructor through; the new gate restricts
    to instructors assigned to the course. Verify the assigned-instructor path
    keeps working.
    """
    curso = _crear_curso(db_session, "mc_inst", publico=False)
    seccion = _crear_seccion(db_session, curso)
    recurso = _crear_recurso(db_session, curso, seccion, publico=False, tipo="meet", indice=1)
    _crear_usuario(db_session, "docente", tipo="instructor")
    _asignar_instructor(db_session, curso, "docente")

    with app.test_client() as client:
        _login(client, "docente")
        resp = client.get(f"/course/{curso.codigo}/resource/meet/{recurso.id}/calendar.ics")

    assert resp.status_code != 403


def test_meet_calendar_denied_for_unassigned_instructor(app, db_session):
    """Stricter-than-before: an instructor from a different course no longer
    reads the ICS of a meet they don't own. The original helper let any
    instructor through; the new gate mirrors the rest of the module.
    """
    curso = _crear_curso(db_session, "mc_otro_inst", publico=False)
    seccion = _crear_seccion(db_session, curso)
    recurso = _crear_recurso(db_session, curso, seccion, publico=False, tipo="meet", indice=1)
    _crear_usuario(db_session, "docente_ajeno", tipo="instructor")

    with app.test_client() as client:
        _login(client, "docente_ajeno")
        resp = client.get(f"/course/{curso.codigo}/resource/meet/{recurso.id}/calendar.ics")

    assert resp.status_code == 403
