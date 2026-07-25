# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""Acciones y rutas auxiliares para gestión de cursos."""

from __future__ import annotations

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------
from flask import flash, redirect, request, url_for
from flask_login import login_required
from sqlalchemy import delete
from werkzeug.wrappers import Response

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms.cache import invalidar_cache_curso
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
from now_lms.vistas._helpers import safe_commit
from now_lms.vistas.courses.base import course, VISTA_ADMINISTRAR_CURSO, VISTA_CURSOS


@course.route("/course/<course_code>/seccion/increment/<indice>")
@login_required
@perfil_requerido("instructor")
def incrementar_indice_seccion(course_code: str, indice: str) -> Response:
    """Actualiza indice de secciones."""
    try:
        indice_int = int(indice)
    except (ValueError, TypeError):
        flash("Índice inválido.", "danger")
        return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
    modificar_indice_curso(
        codigo_curso=course_code,
        indice=indice_int,
        task="increment",
    )
    invalidar_cache_curso(course_code)
    return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))


@course.route("/course/<course_code>/seccion/decrement/<indice>")
@login_required
@perfil_requerido("instructor")
def reducir_indice_seccion(course_code: str, indice: str) -> Response:
    """Actualiza indice de secciones."""
    try:
        indice_int = int(indice)
    except (ValueError, TypeError):
        flash("Índice inválido.", "danger")
        return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
    modificar_indice_curso(
        codigo_curso=course_code,
        indice=indice_int,
        task="decrement",
    )
    invalidar_cache_curso(course_code)
    return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))


@course.route("/course/resource/<cource_code>/<seccion_id>/<task>/<resource_index>")
@login_required
@perfil_requerido("instructor")
def modificar_orden_recurso(cource_code: str, seccion_id: str, resource_index: str, task: str) -> Response:
    """Actualiza indice de recursos."""
    try:
        indice_int = int(resource_index)
    except (ValueError, TypeError):
        flash("Índice inválido.", "danger")
        return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=cource_code))
    modificar_indice_seccion(
        seccion_id=seccion_id,
        indice=indice_int,
        task=task,
    )
    invalidar_cache_curso(cource_code)
    return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=cource_code))


@course.route("/course/<curso_code>/delete_recurso/<seccion>/<id_>")
@login_required
@perfil_requerido("instructor")
def eliminar_recurso(curso_code: str, seccion: str, id_: str) -> Response:
    """Elimina un recurso del curso y reorganiza índices."""
    database.session.execute(delete(CursoRecurso).where(CursoRecurso.id == id_))
    safe_commit()
    reorganiza_indice_seccion(seccion=seccion)
    invalidar_cache_curso(curso_code)
    return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=curso_code))


@course.route("/course/<curso_id>/delete_seccion/<id_>")
@login_required
@perfil_requerido("instructor")
def eliminar_seccion(curso_id: str, id_: str) -> Response:
    """Elimina una sección del curso y reorganiza índices."""
    database.session.execute(delete(CursoSeccion).where(CursoSeccion.id == id_))
    safe_commit()
    reorganiza_indice_curso(codigo_curso=curso_id)
    invalidar_cache_curso(curso_id)
    return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=curso_id))


@course.route("/course/<course_code>/delete_logo")
@login_required
@perfil_requerido("instructor")
def elimina_logo(course_code: str) -> Response:
    """Elimina el logotipo personalizado de un curso."""
    from now_lms.db.tools import elimina_logo_perzonalizado_curso

    elimina_logo_perzonalizado_curso(course_code=course_code)
    invalidar_cache_curso(course_code)
    return redirect(url_for("course.editar_curso", course_code=course_code))


@course.route("/course/change_curse_status")
@login_required
@perfil_requerido("instructor")
def cambiar_estatus_curso() -> Response:
    """Actualiza el estatus de un curso."""
    cambia_estado_curso_por_id(
        request.args.get("curse"), nuevo_estado=request.args.get("status"), usuario=request.args.get("usuario")
    )
    curse = request.args.get("curse", "")
    invalidar_cache_curso(curse)
    return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=curse))


@course.route("/course/change_curse_public")
@login_required
@perfil_requerido("instructor")
def cambiar_curso_publico() -> Response:
    """Actualiza el estado público de un curso."""
    curse = request.args.get("curse", "")
    cambia_curso_publico(
        id_curso=curse,
    )
    invalidar_cache_curso(curse)
    return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=curse))


@course.route("/course/change_curse_seccion_public")
@login_required
@perfil_requerido("instructor")
def cambiar_seccion_publico() -> Response:
    """Actualiza el estado público de una sección."""
    course_code = request.args.get("course_code", "")
    cambia_seccion_publico(
        codigo=request.args.get("codigo"),
    )
    invalidar_cache_curso(course_code)
    return redirect(url_for(VISTA_CURSOS, course_code=request.args.get("course_code")))
