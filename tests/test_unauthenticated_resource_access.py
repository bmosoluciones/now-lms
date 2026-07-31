# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""
Regression tests for unauthenticated access to course resources.

Two defects are covered:

1. `pagina_recurso` gated on the resource's own `publico` flag only, never on the
   owning course. A resource marked as a free preview stayed readable after its course
   was unpublished, made private, or closed. The same handler also fetched the resource
   by id alone, with no `CursoRecurso.curso == curso_id` filter, so an attacker-supplied
   `curso_id` could render a resource in the context of an unrelated course.

2. `slide_show` carried no authorization check whatsoever - not even the `publico` one -
   so it served slideshows from draft, private and paid courses to anonymous visitors.

Both now route through `_resource_is_viewable()`. Reverting either call site must fail
at least one test here.
"""

from now_lms.auth import proteger_passwd
from now_lms.db import Curso, CursoRecurso, CursoSeccion, Usuario

REDIRECT_STATUS_CODES = {301, 302, 303, 307, 308}


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


def _crear_recurso_texto(db_session, curso: Curso, seccion: CursoSeccion, publico: bool = True) -> CursoRecurso:
    recurso = CursoRecurso(
        curso=curso.codigo,
        seccion=seccion.id,
        tipo="text",
        nombre="Texto",
        descripcion="Contenido",
        requerido="required",
        indice=1,
        publico=publico,
        text="Contenido del recurso",
    )
    db_session.add(recurso)
    db_session.commit()
    return recurso


def _crear_recurso_slides(db_session, curso: Curso, seccion: CursoSeccion, publico: bool = True) -> CursoRecurso:
    recurso = CursoRecurso(
        curso=curso.codigo,
        seccion=seccion.id,
        tipo="slides",
        nombre="Presentacion",
        descripcion="Diapositivas",
        requerido="required",
        indice=2,
        publico=publico,
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


# --------------------------------------------------------------------------------------
# 1. pagina_recurso must consult the course, not only the resource
# --------------------------------------------------------------------------------------


def test_public_resource_stays_readable_while_its_course_is_public(app, db_session):
    """The free-preview feature itself must keep working - this is the control case."""
    curso = _crear_curso(db_session, "c_pub_open", publico=True, estado="open")
    seccion = _crear_seccion(db_session, curso)
    recurso = _crear_recurso_texto(db_session, curso, seccion, publico=True)

    with app.test_client() as client:
        resp = client.get(f"/course/{curso.codigo}/resource/text/{recurso.id}")

    assert resp.status_code == 200


def test_public_resource_is_denied_once_its_course_is_unpublished(app, db_session):
    """A preview resource must not outlive its course being made private."""
    curso = _crear_curso(db_session, "c_privado", publico=False, estado="open")
    seccion = _crear_seccion(db_session, curso)
    recurso = _crear_recurso_texto(db_session, curso, seccion, publico=True)

    with app.test_client() as client:
        resp = client.get(f"/course/{curso.codigo}/resource/text/{recurso.id}")

    assert resp.status_code == 403


def test_public_resource_is_denied_once_its_course_is_closed(app, db_session):
    """`estado` matters as well as `publico` - a draft course leaks otherwise."""
    curso = _crear_curso(db_session, "c_draft", publico=True, estado="draft")
    seccion = _crear_seccion(db_session, curso)
    recurso = _crear_recurso_texto(db_session, curso, seccion, publico=True)

    with app.test_client() as client:
        resp = client.get(f"/course/{curso.codigo}/resource/text/{recurso.id}")

    assert resp.status_code == 403


def test_resource_cannot_be_rendered_under_an_unrelated_course(app, db_session):
    """`curso_id` is attacker-controlled; the resource must belong to that course.

    The private course's resource must not become reachable by quoting a public
    course's code in the URL.
    """
    publico = _crear_curso(db_session, "c_tapadera", publico=True, estado="open")
    privado = _crear_curso(db_session, "c_oculto", publico=False, estado="open")
    seccion_privada = _crear_seccion(db_session, privado)
    recurso_privado = _crear_recurso_texto(db_session, privado, seccion_privada, publico=True)

    with app.test_client() as client:
        resp = client.get(f"/course/{publico.codigo}/resource/text/{recurso_privado.id}")

    assert resp.status_code == 404


# --------------------------------------------------------------------------------------
# 2. slide_show had no authorization check at all
# --------------------------------------------------------------------------------------


def test_slide_show_denies_anonymous_access_to_a_private_course(app, db_session):
    """The headline defect: no decorator, no `publico` check, any course."""
    curso = _crear_curso(db_session, "c_slides_priv", publico=False, estado="open")
    seccion = _crear_seccion(db_session, curso)
    recurso = _crear_recurso_slides(db_session, curso, seccion, publico=False)

    with app.test_client() as client:
        resp = client.get(f"/course/slide_show/{recurso.id}")

    assert resp.status_code == 403


def test_slide_show_denies_a_non_public_resource_in_a_public_course(app, db_session):
    """A course being public does not make every resource in it public."""
    curso = _crear_curso(db_session, "c_slides_mixto", publico=True, estado="open")
    seccion = _crear_seccion(db_session, curso)
    recurso = _crear_recurso_slides(db_session, curso, seccion, publico=False)

    with app.test_client() as client:
        resp = client.get(f"/course/slide_show/{recurso.id}")

    assert resp.status_code == 403


def test_slide_show_denies_an_authenticated_student_who_is_not_enrolled(app, db_session):
    """Being logged in is not entitlement - enrolment is."""
    curso = _crear_curso(db_session, "c_slides_matric", publico=False, estado="open")
    seccion = _crear_seccion(db_session, curso)
    recurso = _crear_recurso_slides(db_session, curso, seccion, publico=False)
    _crear_estudiante(db_session, "sin_matricula")

    with app.test_client() as client:
        client.post("/user/login", data={"usuario": "sin_matricula", "acceso": "sin_matricula"})
        resp = client.get(f"/course/slide_show/{recurso.id}")

    assert resp.status_code == 403


def test_slide_show_still_serves_a_public_resource_in_a_public_course(app, db_session):
    """Control case: the legitimate anonymous path must survive the fix.

    A missing slideshow body 404s rather than 403s - the point is that authorization
    passed, so the handler got far enough to look for content.
    """
    curso = _crear_curso(db_session, "c_slides_pub", publico=True, estado="open")
    seccion = _crear_seccion(db_session, curso)
    recurso = _crear_recurso_slides(db_session, curso, seccion, publico=True)

    with app.test_client() as client:
        resp = client.get(f"/course/slide_show/{recurso.id}")

    assert resp.status_code != 403
    assert resp.status_code in {200, 404}


def test_slide_show_returns_404_for_an_unknown_resource(app, db_session):
    """Unknown ids must not be distinguishable via the new authorization branch."""
    with app.test_client() as client:
        resp = client.get("/course/slide_show/no-such-resource-id")

    assert resp.status_code == 404
