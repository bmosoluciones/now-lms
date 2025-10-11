"""Admin profile views for NOW LMS."""

from __future__ import annotations

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import delete, func
from werkzeug.wrappers import Response

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms.auth import perfil_requerido
from now_lms.bi import cambia_tipo_de_usuario_por_id
from now_lms.cache import cache
from now_lms.config import DIRECTORIO_PLANTILLAS
from now_lms.db import MAXIMO_RESULTADOS_EN_CONSULTA_PAGINADA, Curso, EstudianteCurso, Usuario, database

# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------


# Constants
ADMIN_USERS_ROUTE = "admin_profile.usuarios"

admin_profile = Blueprint("admin_profile", __name__, template_folder=DIRECTORIO_PLANTILLAS)


@admin_profile.route("/admin/panel")
@login_required
@perfil_requerido("admin")
@cache.cached(timeout=90)
def pagina_admin() -> str:
    """Perfil de usuario administrador."""
    # Get admin statistics
    total_users = database.session.execute(database.select(func.count(Usuario.id))).scalar() or 0
    inactive_users = database.session.execute(database.select(func.count(Usuario.id)).filter_by(activo=False)).scalar() or 0
    total_courses = database.session.execute(database.select(func.count(Curso.id))).scalar() or 0

    # Get recent courses (for display)
    cursos_recientes = database.session.execute(database.select(Curso).order_by(Curso.creado.desc()).limit(5)).scalars().all()

    # Get total enrollments
    total_enrollments = database.session.execute(database.select(func.count(EstudianteCurso.id))).scalar() or 0

    return render_template(
        "perfiles/admin.html",
        inactivos=inactive_users,
        total_users=total_users,
        total_courses=total_courses,
        total_enrollments=total_enrollments,
        cursos_recientes=cursos_recientes,
    )


@admin_profile.route("/admin/users/list")
@login_required
@perfil_requerido("admin")
@cache.cached(timeout=60)
def usuarios() -> str:
    """Lista de usuarios con acceso a al aplicación."""
    CONSULTA = database.paginate(
        database.select(Usuario),
        page=request.args.get("page", default=1, type=int),
        max_per_page=MAXIMO_RESULTADOS_EN_CONSULTA_PAGINADA,
        count=True,
    )

    return render_template(
        "admin/users.html",
        consulta=CONSULTA,
    )


@admin_profile.route("/admin/users/set_active/<user_id>")
@login_required
@perfil_requerido("admin")
def activar_usuario(user_id: str) -> Response:
    """Estable el usuario como activo y redirecciona a la vista dada."""
    row = database.session.execute(database.select(Usuario).filter(Usuario.id == user_id)).first()
    if row is None:
        return redirect(url_for(ADMIN_USERS_ROUTE))
    perfil_usuario = row[0]
    if not perfil_usuario.activo:
        perfil_usuario.activo = True
        database.session.commit()
        flash("Usuario definido como activo", "info")
    else:
        flash("Usuario ya se encuentra definido como activo", "warning")
    cache.delete("view/" + url_for(ADMIN_USERS_ROUTE))
    return redirect(url_for(ADMIN_USERS_ROUTE))


@admin_profile.route("/admin/users/set_inactive/<user_id>")
@login_required
@perfil_requerido("admin")
def inactivar_usuario(user_id: str) -> Response:
    """Estable el usuario como activo y redirecciona a la vista dada."""
    row = database.session.execute(database.select(Usuario).filter(Usuario.id == user_id)).first()
    if row is None:
        return redirect(url_for(ADMIN_USERS_ROUTE))
    perfil_usuario = row[0]
    if perfil_usuario.activo:
        perfil_usuario.activo = False
        database.session.commit()
        flash("Usuario definido como inactivo", "info")
    else:
        flash("Usuario ya se encuentra definido como inactivo", "warning")
    cache.delete("view/" + url_for(ADMIN_USERS_ROUTE))
    return redirect(url_for(ADMIN_USERS_ROUTE))


@admin_profile.route("/admin/users/delete/<user_id>")
@login_required
@perfil_requerido("admin")
def eliminar_usuario(user_id: str) -> Response:
    """Elimina un usuario por su id y redirecciona a la vista dada."""
    database.session.execute(delete(Usuario).where(Usuario.id == user_id))
    database.session.commit()
    cache.delete("view/" + url_for("admin_profile.usuarios"))
    flash("Usuario eliminado correctamente.", "info")
    return redirect(url_for(request.args.get("ruta", default="home", type=str)))


@admin_profile.route("/admin/users/list_inactive")
@login_required
@perfil_requerido("admin")
@cache.cached(timeout=60)
def usuarios_inactivos() -> str:
    """Lista de usuarios con acceso a al aplicación."""
    CONSULTA = database.paginate(
        database.select(Usuario).filter_by(activo=False),
        page=request.args.get("page", default=1, type=int),
        max_per_page=MAXIMO_RESULTADOS_EN_CONSULTA_PAGINADA,
        count=True,
    )

    return render_template(
        "admin/inactive_users.html",
        consulta=CONSULTA,
    )


@admin_profile.route("/admin/user/change_type")
@login_required
@perfil_requerido("admin")
def cambiar_tipo_usario() -> Response:
    """Actualiza el tipo de usuario."""
    from now_lms.demo_mode import demo_restriction_check

    new_type = request.args.get("type")
    user_id = request.args.get("user")
    redirect_to = request.args.get("redirect_to", "profile")

    # Check demo mode restrictions for any user type changes by admin
    if demo_restriction_check("change_user_type"):
        if redirect_to == "list":
            return redirect(url_for("admin_profile.usuarios"))
        return redirect(url_for("user_profile.usuario", id_usuario=user_id))

    cambia_tipo_de_usuario_por_id(
        user_id,
        nuevo_tipo=new_type,
        usuario=current_user.usuario,
    )

    # Redirect back to the appropriate page based on request
    if redirect_to == "list":
        return redirect(url_for("admin_profile.usuarios"))
    return redirect(url_for("user_profile.usuario", id_usuario=user_id))
