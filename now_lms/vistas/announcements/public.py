# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.

"""Public announcements views."""


from __future__ import annotations

# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------
from datetime import datetime

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from werkzeug.wrappers import Response

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms.cache import cache
from now_lms.config import DIRECTORIO_PLANTILLAS
from now_lms.db import MAXIMO_RESULTADOS_EN_CONSULTA_PAGINADA, Announcement, Curso, EstudianteCurso, database

public_announcements = Blueprint("public_announcements", __name__, template_folder=DIRECTORIO_PLANTILLAS)


@public_announcements.route("/dashboard/announcements")
@login_required
@cache.cached(timeout=60)
def global_announcements() -> str:
    """Ver anuncios globales para todos los usuarios autenticados."""
    # Filtrar anuncios globales activos (no expirados)
    now = datetime.now()

    consulta = database.paginate(
        database.select(Announcement)
        .filter(
            Announcement.course_id.is_(None),  # Solo anuncios globales
            database.or_(
                Announcement.expires_at.is_(None),
                Announcement.expires_at >= now,  # Sin fecha de expiración  # No expirados
            ),
        )
        .order_by(Announcement.is_sticky.desc(), Announcement.timestamp.desc()),  # Destacados primero  # Más recientes primero
        page=request.args.get("page", default=1, type=int),
        max_per_page=MAXIMO_RESULTADOS_EN_CONSULTA_PAGINADA,
        count=True,
    )

    return render_template("announcements/global.html", consulta=consulta)


@public_announcements.route("/course/<course_id>/announcements")
@login_required
@cache.cached(timeout=60)
def course_announcements(course_id: str) -> str | Response:
    """Ver anuncios específicos de un curso."""
    # Verificar que el curso existe
    course = database.session.get(Curso, course_id)
    if not course:
        flash("Curso no encontrado.", "error")
        return redirect(url_for("public_announcements.global_announcements"))

    # Verificar que el usuario está inscrito en el curso
    # (Administradores e instructores pueden ver todos los anuncios)
    if current_user.tipo not in ["admin", "instructor"]:
        # Verificar si es estudiante del curso
        enrollment = database.session.execute(
            database.select(EstudianteCurso).filter(
                EstudianteCurso.usuario == current_user.usuario, EstudianteCurso.curso == course_id
            )
        ).scalar_one_or_none()

        if not enrollment:
            flash("No tienes acceso a los anuncios de este curso.", "error")
            return redirect(url_for("public_announcements.global_announcements"))

    # Obtener anuncios del curso
    consulta = database.paginate(
        database.select(Announcement).filter(Announcement.course_id == course_id).order_by(Announcement.timestamp.desc()),
        page=request.args.get("page", default=1, type=int),
        max_per_page=MAXIMO_RESULTADOS_EN_CONSULTA_PAGINADA,
        count=True,
    )

    return render_template("announcements/course.html", consulta=consulta, course=course)
