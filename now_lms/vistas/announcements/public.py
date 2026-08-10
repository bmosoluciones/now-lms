# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.

"""Public announcements views."""

from __future__ import annotations

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
from now_lms.db import MAXIMO_RESULTADOS_EN_CONSULTA_PAGINADA, Announcement, Curso, EstudianteCurso, database, utc_now
from now_lms.i18n import _

public_announcements = Blueprint("public_announcements", __name__, template_folder=DIRECTORIO_PLANTILLAS)


@public_announcements.route("/dashboard/announcements", methods=["GET"])
@login_required
def global_announcements() -> str:
    """The full archive of active global announcements, paginated.

    FORK-LOCAL NOTE. The member dashboard is the primary door for community
    communication and carries the newest few announcements inline. This page is
    the OVERFLOW, not a competing reader: the dashboard links here only when
    there are more announcements than it shows.

    An earlier revision of this branch redirected here to the dashboard, on the
    reasoning that one channel beats two. The reasoning was right and the
    execution was wrong — the dashboard caps at MAX_ANNOUNCEMENTS, so every
    announcement past the newest few became unreachable for every authenticated
    role, silently. A summary with an explicit "view all" is one channel; a
    summary that quietly drops the rest is a data-loss bug wearing a product
    decision's clothes. Found by Greptile on PR #79.

    Timezone: filtered against naive UTC, matching ``Announcement.is_active()``
    and how ``expires_at`` is stored. The original compared against
    ``datetime.now()``, which is local time, so on a non-UTC host it retired
    announcements early or late by the offset.
    """
    ahora = utc_now().replace(tzinfo=None)

    consulta = database.paginate(
        database.select(Announcement)
        .filter(
            Announcement.course_id.is_(None),
            database.or_(
                Announcement.expires_at.is_(None),
                Announcement.expires_at >= ahora,
            ),
        )
        .order_by(Announcement.is_sticky.desc(), Announcement.timestamp.desc()),
        page=request.args.get("page", default=1, type=int),
        max_per_page=MAXIMO_RESULTADOS_EN_CONSULTA_PAGINADA,
        count=True,
    )

    return render_template("announcements/global.html", consulta=consulta)


@public_announcements.route("/course/<course_id>/announcements", methods=["GET"])
@login_required
@cache.cached(timeout=60, key_prefix=lambda course_id: f"course_announcements_{course_id}_{current_user.id}")  # type: ignore[arg-type]
def course_announcements(course_id: str) -> str | Response:
    """Ver anuncios específicos de un curso."""
    # Verificar que el curso existe
    course = database.session.get(Curso, course_id)
    if not course:
        flash(_("Curso no encontrado."), "error")
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
            flash(_("No tienes acceso a los anuncios de este curso."), "error")
            return redirect(url_for("public_announcements.global_announcements"))

    # Obtener anuncios del curso
    consulta = database.paginate(
        database.select(Announcement).filter(Announcement.course_id == course_id).order_by(Announcement.timestamp.desc()),
        page=request.args.get("page", default=1, type=int),
        max_per_page=MAXIMO_RESULTADOS_EN_CONSULTA_PAGINADA,
        count=True,
    )

    return render_template("announcements/course.html", consulta=consulta, course=course)
