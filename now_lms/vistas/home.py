"""Home page views for NOW LMS."""

# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------

from os import path
from pathlib import Path

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------
from flask import Blueprint, redirect, render_template, request
from flask_login import current_user, login_required
from sqlalchemy import func

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms.cache import cache, no_guardar_en_cache_global
from now_lms.config import DESARROLLO, DIRECTORIO_PLANTILLAS
from now_lms.db import (
    MAXIMO_RESULTADOS_EN_CONSULTA_PAGINADA,
    Certificacion,
    Curso,
    CursoRecurso,
    EstudianteCurso,
    Usuario,
    database,
    select,
)
from now_lms.db.tools import get_current_theme
from now_lms.logs import log
from now_lms.themes import get_home_template

home = Blueprint("home", __name__, template_folder=DIRECTORIO_PLANTILLAS)


# ---------------------------------------------------------------------------------------
# Página de inicio de la aplicación.
# ---------------------------------------------------------------------------------------
@home.route("/")
@home.route("/home")
@cache.cached(timeout=90, unless=no_guardar_en_cache_global)
def pagina_de_inicio():
    """Página principal de la aplicación."""
    if DESARROLLO:  # pragma: no cover
        MAX = 3
    else:  # pragma: no cover
        MAX = MAXIMO_RESULTADOS_EN_CONSULTA_PAGINADA

    CURSOS = database.paginate(
        database.select(Curso).filter(Curso.publico.is_(True), Curso.estado == "open"),
        page=request.args.get("page", default=1, type=int),
        max_per_page=MAX,
        count=True,
    )

    return render_template(get_home_template(), cursos=CURSOS)


@home.route("/home/panel")
@login_required
def panel():
    """Panel principal de la aplicacion luego de inicar sesión."""
    if not current_user.is_authenticated:
        return redirect("/")

    # Use structural pattern matching for user types (Python 3.10+)
    match current_user.tipo:
        case "admin":
            cursos_actuales = database.session.execute(select(func.count(Curso.id))).scalar()
            usuarios_registrados = database.session.execute(select(func.count(Usuario.usuario))).scalar()
            recursos_creados = database.session.execute(select(func.count(CursoRecurso.id))).scalar()
            certificados_emitidos = database.session.execute(select(func.count(Certificacion.id))).scalar()
            cursos_por_fecha = database.session.execute(select(Curso).order_by(Curso.creado).limit(5)).scalars().all()
            return render_template(
                "inicio/panel_admin.html",
                cursos_actuales=cursos_actuales,
                usuarios_registrados=usuarios_registrados,
                recursos_creados=recursos_creados,
                cursos_por_fecha=cursos_por_fecha,
                certificados_emitidos=certificados_emitidos,
            )
        case "student":
            cuenta_cursos = database.session.execute(
                select(func.count(EstudianteCurso.id)).filter(EstudianteCurso.usuario == current_user.usuario)
            ).scalar()
            cuenta_certificados = database.session.execute(
                select(func.count(Certificacion.id)).filter(Certificacion.usuario == current_user.usuario)
            ).scalar()
            mis_cursos = (
                database.session.execute(
                    select(Curso)
                    .join(EstudianteCurso, EstudianteCurso.curso == Curso.codigo)
                    .filter(EstudianteCurso.usuario == current_user.usuario)
                )
                .scalars()
                .all()
            )
            log.warning(mis_cursos)
            return render_template(
                "inicio/panel_user.html",
                cuenta_cursos=cuenta_cursos,
                cuenta_certificados=cuenta_certificados,
                mis_cursos=mis_cursos,
            )
        case "instructor":
            from now_lms.db import DocenteCurso

            # Get courses created by this instructor
            created_courses = database.session.execute(
                select(func.count(Curso.id))
                .join(DocenteCurso)
                .filter(DocenteCurso.usuario == current_user.usuario, DocenteCurso.vigente)
            ).scalar()

            # Get enrolled students across instructor's courses
            enrolled_students = database.session.execute(
                select(func.count(EstudianteCurso.usuario.distinct()))
                .join(DocenteCurso, EstudianteCurso.curso == DocenteCurso.curso)
                .filter(DocenteCurso.usuario == current_user.usuario, DocenteCurso.vigente, EstudianteCurso.vigente)
            ).scalar()

            # Get certificates issued for courses taught by this instructor
            issued_certificates = database.session.execute(
                select(func.count(Certificacion.id))
                .join(DocenteCurso, Certificacion.curso == DocenteCurso.curso)
                .filter(DocenteCurso.usuario == current_user.usuario, DocenteCurso.vigente)
            ).scalar()

            # Get recent courses by this instructor
            cursos_por_fecha = (
                database.session.execute(
                    select(Curso)
                    .join(DocenteCurso)
                    .filter(DocenteCurso.usuario == current_user.usuario, DocenteCurso.vigente)
                    .order_by(Curso.creado)
                    .limit(5)
                )
                .scalars()
                .all()
            )

            return render_template(
                "inicio/panel_instructor.html",
                created_courses=created_courses,
                enrolled_students=enrolled_students,
                issued_certificates=issued_certificates,
                cursos_por_fecha=cursos_por_fecha,
            )
        case "moderator":
            from now_lms.db import MessageThread, ModeradorCurso

            # Get courses moderated by this moderator
            created_courses = database.session.execute(
                select(func.count(Curso.id))
                .join(ModeradorCurso)
                .filter(ModeradorCurso.usuario == current_user.usuario, ModeradorCurso.vigente)
            ).scalar()

            # Get enrolled students across moderator's courses
            enrolled_students = database.session.execute(
                select(func.count(EstudianteCurso.usuario.distinct()))
                .join(ModeradorCurso, EstudianteCurso.curso == ModeradorCurso.curso)
                .filter(ModeradorCurso.usuario == current_user.usuario, ModeradorCurso.vigente, EstudianteCurso.vigente)
            ).scalar()

            # Get recent courses by this moderator
            cursos_por_fecha = (
                database.session.execute(
                    select(Curso)
                    .join(ModeradorCurso)
                    .filter(ModeradorCurso.usuario == current_user.usuario, ModeradorCurso.vigente)
                    .order_by(Curso.creado)
                    .limit(5)
                )
                .scalars()
                .all()
            )

            # Get open and closed message counts for moderator
            open_messages = database.session.execute(
                select(func.count(MessageThread.id)).filter(MessageThread.status == "open")
            ).scalar()

            closed_messages = database.session.execute(
                select(func.count(MessageThread.id)).filter(MessageThread.status == "closed")
            ).scalar()

            return render_template(
                "inicio/panel_moderator.html",
                created_courses=created_courses,
                enrolled_students=enrolled_students,
                cursos_por_fecha=cursos_por_fecha,
                open_messages=open_messages,
                closed_messages=closed_messages,
            )
        case _:
            return redirect("/")


@home.route("/custom/<page>")
@cache.cached(timeout=180)
def custom_page(page):
    """Muestra páginas personalizadas por tema."""
    THEME = get_current_theme()

    if any(c in page for c in ["/", "\\", ".", "$"]):
        return redirect("/")

    if THEME and THEME != "now_lms":
        THEMES_DIRECTORY = "themes/"
        custom_page_path = Path(path.join(str(DIRECTORIO_PLANTILLAS), THEMES_DIRECTORY, THEME, "custom_pages", f"{page}.j2"))

        if custom_page_path.exists():
            template_path = f"{THEMES_DIRECTORY}{THEME}/custom_pages/{page}.j2"
            return render_template(template_path)
        return redirect("/")

    # Si no existe la página personalizada, redirigir al inicio
    return redirect("/")
