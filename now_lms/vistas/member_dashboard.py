# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.

"""Member dashboard.

The signed-in landing page for a learner. ``misc.panel_de_usuario`` sends
``tipo == "student"`` here after login; instructors, moderators and admins keep
their existing panels untouched. The route itself is open to any signed-in user
and shows that user's own enrolment data, so an instructor who navigates here
directly sees their own learner view rather than an error.

Why this is a blueprint and not an edit to ``home.panel``: the upstream view is
hardcoded to ``"inicio/panel_user.html"`` with no theme-override slot, and
carrying a large diff against a function upstream also maintains means
re-applying it at every sync. A new file with no imports from ``home.py``
survives a restructure, which is the same reasoning that put ``/request-access``
and ``/my-credentials`` in their own modules.

What this page exists to fix, all measured against the upstream panel:

- **Progress was invisible to the person making it.** ``CursoUsuarioAvance.avance``
  is a maintained 0-100 percentage that no member-facing template reads, while
  ``ops/lms/lms-progress-digest.sh`` selects that same column and mails a
  per-member table to staff every week. Staff could see a learner's completion;
  the learner could not.
- **A new member's dashboard read zero, zero, zero**, and the empty state's only
  call to action pointed at a catalog that is gated to nothing on this
  deployment, so the loop closed with no course in it.
- **Built surfaces had no entry point.** ``/my-credentials`` was reachable from
  nowhere in the entire template tree.

Query budget: this view issues a fixed number of queries regardless of how many
courses the member is enrolled in. The per-course helpers in
``evaluation_helpers`` are deliberately NOT called here — each one runs a query
per evaluation plus a count, which is acceptable inside one course page and is
an N+1 across a dashboard.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------
from flask import Blueprint, render_template
from flask_login import current_user, login_required
from sqlalchemy import func

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms.calendar_utils import get_upcoming_events_for_user
from now_lms.config import DIRECTORIO_PLANTILLAS
from now_lms.db import (
    Announcement,
    Certificacion,
    Curso,
    CursoUsuarioAvance,
    EstudianteCurso,
    PriorCredential,
    database,
    select,
    utc_now,
)
from now_lms.vistas.comunidad import posts_recientes
from now_lms.vistas.prior_credentials import CREDENTIAL_TOTAL

member_dashboard = Blueprint("member_dashboard", __name__, template_folder=DIRECTORIO_PLANTILLAS)

DASHBOARD_TEMPLATE = "themes/intent_learn/pages/dashboard.html"

# How many rows each panel shows before it links out. Small on purpose: the
# dashboard is an orientation surface, not an index.
MAX_ANNOUNCEMENTS = 3
MAX_EVENTS = 4
MAX_COMUNIDAD = 5


def _cursos_con_avance(usuario: str) -> list[dict]:
    """Enrolled courses with their stored progress, in one query.

    LEFT JOIN so a course a member has enrolled in but never opened still
    appears, at zero, rather than vanishing. Filters ``vigente`` because the
    upstream panel did not, which is why its course count disagreed with the
    count on ``/my_courses``.
    """
    filas = database.session.execute(
        select(Curso, CursoUsuarioAvance)
        .join(EstudianteCurso, EstudianteCurso.curso == Curso.codigo)
        .outerjoin(
            CursoUsuarioAvance,
            (CursoUsuarioAvance.curso == Curso.codigo) & (CursoUsuarioAvance.usuario == usuario),
        )
        .filter(EstudianteCurso.usuario == usuario, EstudianteCurso.vigente.is_(True))
        .order_by(Curso.nombre)
    ).all()

    cursos = []
    for curso, avance in filas:
        # `avance` is Decimal on PostgreSQL (Float(asdecimal=True)) and float on
        # SQLite, and a Decimal reaching the template formats differently. round()
        # on a float already returns int, so no cast is needed after the coerce.
        porcentaje = round(float(avance.avance)) if avance and avance.avance is not None else 0
        cursos.append(
            {
                "curso": curso,
                "porcentaje": max(0, min(100, porcentaje)),
                "completado": bool(avance.completado) if avance else False,
                "recursos_completados": (avance.recursos_completados or 0) if avance else 0,
                "recursos_requeridos": (avance.recursos_requeridos or 0) if avance else 0,
                "empezado": avance is not None and (avance.recursos_completados or 0) > 0,
            }
        )
    return cursos


def _anuncios_fijados() -> list[Announcement]:
    """Active global announcements, newest first, sticky first.

    Deliberately the same filter the native ``/dashboard/announcements`` page
    uses, because this surface replaces that one as the member's single door.
    Announcements stay in the native model: staff already have working admin
    CRUD with stickiness and expiry, and a second announcement concept would be
    two channels for the same message.
    """
    # Naive UTC, matching Announcement.is_active() and how expires_at is stored.
    # The native view compared against datetime.now(), which is local time, so on
    # a non-UTC host it retired announcements early or late by the offset.
    ahora = utc_now().replace(tzinfo=None)
    return list(
        database.session.execute(
            select(Announcement)
            .filter(
                Announcement.course_id.is_(None),
                database.or_(Announcement.expires_at.is_(None), Announcement.expires_at >= ahora),
            )
            .order_by(Announcement.is_sticky.desc(), Announcement.timestamp.desc())
            .limit(MAX_ANNOUNCEMENTS)
        )
        .scalars()
        .all()
    )


def _anuncios_totales() -> int:
    """How many active global announcements exist, so the card can admit truncation.

    Without this the dashboard shows its newest few and gives no sign there are
    more, which is how announcements past the cap became unreachable. The count
    is what turns a silent truncation into an explicit "view all". Greptile, #79.
    """
    ahora = utc_now().replace(tzinfo=None)
    return int(
        database.session.execute(
            select(database.func.count())
            .select_from(Announcement)
            .filter(
                Announcement.course_id.is_(None),
                database.or_(Announcement.expires_at.is_(None), Announcement.expires_at >= ahora),
            )
        ).scalar_one()
    )


@member_dashboard.route("/dashboard", methods=["GET"])
@login_required
def panel() -> str:
    """The learner's landing page."""
    usuario = current_user.usuario

    cursos = _cursos_con_avance(usuario)

    certificados = (
        database.session.execute(
            select(func.count(Certificacion.id)).filter(Certificacion.usuario == usuario)
        ).scalar()
        or 0
    )

    credenciales = (
        database.session.execute(
            select(func.count(PriorCredential.id)).filter(PriorCredential.usuario == usuario)
        ).scalar()
        or 0
    )

    return render_template(
        DASHBOARD_TEMPLATE,
        cursos=cursos,
        en_progreso=[c for c in cursos if c["empezado"] and not c["completado"]],
        certificados=certificados,
        credenciales=credenciales,
        credenciales_total=CREDENTIAL_TOTAL,
        anuncios=_anuncios_fijados(),
        anuncios_totales=_anuncios_totales(),
        anuncios_mostrados=MAX_ANNOUNCEMENTS,
        eventos=get_upcoming_events_for_user(usuario, limit=MAX_EVENTS),
        comunidad=posts_recientes(usuario, limite=MAX_COMUNIDAD),
    )
