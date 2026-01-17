"""Acciones y rutas auxiliares para gestión de cursos."""

from __future__ import annotations

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------
from flask import redirect, request, url_for
from flask_login import login_required
from sqlalchemy import delete
from werkzeug.wrappers import Response

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms.auth import perfil_requerido
from now_lms.bi import (
    cambia_curso_publico,
    cambia_estado_curso_por_id,
    cambia_seccion_publico,
    modificar_indice_curso,
    modificar_indice_seccion,
    reorganiza_indice_curso,
    reorganiza_indice_seccion,
)
from now_lms.db import CursoRecurso, CursoSeccion, database
from now_lms.db import select as db_select
from now_lms.vistas.courses.base import course, VISTA_ADMINISTRAR_CURSO, VISTA_CURSOS


@course.route("/course/<course_code>/seccion/increment/<indice>")
@login_required
@perfil_requerido("instructor")
def incrementar_indice_seccion(course_code: str, indice: str) -> Response:
    """Actualiza indice de secciones."""
    modificar_indice_curso(
        codigo_curso=course_code,
        indice=int(indice),
        task="decrement",
    )
    return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))


@course.route("/course/<course_code>/seccion/decrement/<indice>")
@login_required
@perfil_requerido("instructor")
def reducir_indice_seccion(course_code: str, indice: str) -> Response:
    """Actualiza indice de secciones."""
    modificar_indice_curso(
        codigo_curso=course_code,
        indice=int(indice),
        task="increment",
    )
    return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))


@course.route("/course/resource/<cource_code>/<seccion_id>/<task>/<resource_index>")
@login_required
@perfil_requerido("instructor")
def modificar_orden_recurso(cource_code: str, seccion_id: str, resource_index: str, task: str) -> Response:
    """Actualiza indice de recursos."""
    modificar_indice_seccion(
        seccion_id=seccion_id,
        indice=int(resource_index),
        task=task,
    )
    return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=cource_code))


@course.route("/course/<curso_code>/delete_recurso/<seccion>/<id_>")
@login_required
@perfil_requerido("instructor")
def eliminar_recurso(curso_code: str, seccion: str, id_: str) -> Response:
    """Elimina un recurso del curso y reorganiza índices."""
    database.session.execute(delete(CursoRecurso).where(CursoRecurso.id == id_))
    database.session.commit()
    reorganiza_indice_seccion(seccion=seccion)
    return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=curso_code))


@course.route("/course/<curso_id>/delete_seccion/<id_>")
@login_required
@perfil_requerido("instructor")
def eliminar_seccion(curso_id: str, id_: str) -> Response:
    """Elimina una sección del curso y reorganiza índices."""
    database.session.execute(delete(CursoSeccion).where(CursoSeccion.id == id_))
    database.session.commit()
    reorganiza_indice_curso(codigo_curso=curso_id)
    return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=curso_id))


@course.route("/course/change_curse_status")
@login_required
@perfil_requerido("instructor")
def cambiar_estatus_curso() -> Response:
    """Actualiza el estatus de un curso."""
    cambia_estado_curso_por_id(
        request.args.get("curse"), nuevo_estado=request.args.get("status"), usuario=request.args.get("usuario")
    )
    return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=request.args.get("curse")))


@course.route("/course/change_curse_public")
@login_required
@perfil_requerido("instructor")
def cambiar_curso_publico() -> Response:
    """Actualiza el estado público de un curso."""
    cambia_curso_publico(
        id_curso=request.args.get("curse"),
    )
    return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=request.args.get("curse")))


@course.route("/course/change_curse_seccion_public")
@login_required
@perfil_requerido("instructor")
def cambiar_seccion_publico() -> Response:
    """Actualiza el estado público de una sección."""
    cambia_seccion_publico(
        codigo=request.args.get("codigo"),
    )
    return redirect(url_for(VISTA_CURSOS, course_code=request.args.get("course_code")))
