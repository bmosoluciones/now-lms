# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.

"""Admin profile views for NOW LMS."""

from __future__ import annotations
from flask_babel import gettext

# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------
from datetime import date, datetime, time

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
from now_lms.db import Pago
from now_lms.i18n import _

# Constants
ADMIN_USERS_ROUTE = "admin_profile.usuarios"
ADMIN_UNVERIFIED_USERS_ROUTE = "admin_profile.usuarios_sin_verificar"
CACHE_VIEW_PREFIX = "view/"

admin_profile = Blueprint("admin_profile", __name__, template_folder=DIRECTORIO_PLANTILLAS)


@admin_profile.route("/admin/panel", methods=["GET"])
@login_required
@perfil_requerido("admin")
@cache.cached(timeout=90)
def pagina_admin() -> str:
    """Perfil de usuario administrador."""
    # Get admin statistics
    total_users = database.session.execute(database.select(func.count(Usuario.id))).scalar() or 0
    inactive_users = database.session.execute(database.select(func.count(Usuario.id)).filter_by(activo=False)).scalar() or 0
    unverified_users = (
        database.session.execute(
            database.select(func.count(Usuario.id)).filter_by(correo_electronico_verificado=False)
        ).scalar()
        or 0
    )
    total_courses = database.session.execute(database.select(func.count(Curso.id))).scalar() or 0

    # Get recent courses (for display)
    cursos_recientes = database.session.execute(database.select(Curso).order_by(Curso.creado.desc()).limit(5)).scalars().all()

    # Get total enrollments
    total_enrollments = database.session.execute(database.select(func.count(EstudianteCurso.id))).scalar() or 0

    from sqlalchemy import cast, Numeric

    total_payments = (
        database.session.execute(
            database.select(func.count(Pago.id)).filter(Pago.estado == "completed", Pago.metodo == "paypal")
        ).scalar()
        or 0
    )
    total_ingresos = (
        database.session.execute(
            database.select(func.sum(cast(Pago.monto, Numeric))).filter(Pago.estado == "completed", Pago.metodo == "paypal")
        ).scalar()
        or 0
    )

    return render_template(
        "perfiles/admin.html",
        inactivos=inactive_users,
        unverified_users=unverified_users,
        total_users=total_users,
        total_courses=total_courses,
        total_enrollments=total_enrollments,
        cursos_recientes=cursos_recientes,
        total_payments=total_payments,
        total_ingresos=total_ingresos,
    )


@admin_profile.route("/admin/users/list", methods=["GET"])
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


@admin_profile.route("/admin/users/set_active/<user_id>", methods=["POST"])
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
        flash(gettext("Usuario definido como activo"), "info")
    else:
        flash(gettext("Usuario ya se encuentra definido como activo"), "warning")
    cache.delete(CACHE_VIEW_PREFIX + url_for(ADMIN_USERS_ROUTE))
    return redirect(url_for(ADMIN_USERS_ROUTE))


@admin_profile.route("/admin/users/set_inactive/<user_id>", methods=["POST"])
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
        flash(gettext("Usuario definido como inactivo"), "info")
    else:
        flash(gettext("Usuario ya se encuentra definido como inactivo"), "warning")
    cache.delete(CACHE_VIEW_PREFIX + url_for(ADMIN_USERS_ROUTE))
    return redirect(url_for(ADMIN_USERS_ROUTE))


@admin_profile.route("/admin/users/delete/<user_id>", methods=["POST"])
@login_required
@perfil_requerido("admin")
def eliminar_usuario(user_id: str) -> Response:
    """Elimina un usuario por su id y redirecciona a la vista dada."""
    database.session.execute(delete(Usuario).where(Usuario.id == user_id))
    database.session.commit()
    cache.delete(CACHE_VIEW_PREFIX + url_for(ADMIN_USERS_ROUTE))
    flash(gettext("Usuario eliminado correctamente."), "info")
    return redirect(url_for(request.form.get("ruta", default="home", type=str)))


@admin_profile.route("/admin/users/list_inactive", methods=["GET"])
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


@admin_profile.route("/admin/users/list_unverified", methods=["GET"])
@login_required
@perfil_requerido("admin")
@cache.cached(timeout=60)
def usuarios_sin_verificar() -> str:
    """Lista de usuarios que no han verificado su correo electrónico."""
    CONSULTA = database.paginate(
        database.select(Usuario).filter_by(correo_electronico_verificado=False),
        page=request.args.get("page", default=1, type=int),
        max_per_page=MAXIMO_RESULTADOS_EN_CONSULTA_PAGINADA,
        count=True,
    )

    return render_template(
        "admin/unverified_users.html",
        consulta=CONSULTA,
    )


@admin_profile.route("/admin/users/verify_email/<user_id>", methods=["POST"])
@login_required
@perfil_requerido("admin")
def verificar_email_usuario(user_id: str) -> Response:
    """Marca el correo electrónico del usuario como verificado y activa la cuenta."""
    from now_lms.demo_mode import demo_restriction_check

    # Check demo mode restrictions
    if demo_restriction_check("verify_user_email"):
        return redirect(url_for(ADMIN_UNVERIFIED_USERS_ROUTE))

    row = database.session.execute(database.select(Usuario).filter(Usuario.id == user_id)).first()
    if row is None:
        flash(gettext("Usuario no encontrado."), "error")
        return redirect(url_for(ADMIN_UNVERIFIED_USERS_ROUTE))

    perfil_usuario = row[0]

    # Mark email as verified and activate account
    perfil_usuario.correo_electronico_verificado = True
    perfil_usuario.activo = True
    perfil_usuario.modificado_por = current_user.usuario

    try:
        database.session.commit()
        flash(_("Correo electrónico de %(user)s verificado exitosamente.") % {"user": perfil_usuario.usuario}, "success")
    except Exception as e:
        database.session.rollback()
        flash(_("Error al verificar el correo electrónico: %(error)s") % {"error": str(e)}, "error")

    # Clear cache
    cache.delete(CACHE_VIEW_PREFIX + url_for(ADMIN_UNVERIFIED_USERS_ROUTE))

    return redirect(url_for(ADMIN_UNVERIFIED_USERS_ROUTE))


@admin_profile.route("/admin/users/reject_unverified/<user_id>", methods=["POST"])
@login_required
@perfil_requerido("admin")
def rechazar_usuario_sin_verificar(user_id: str) -> Response:
    """Rechaza un usuario no verificado marcándolo como inactivo."""
    from now_lms.demo_mode import demo_restriction_check

    # Check demo mode restrictions
    if demo_restriction_check("reject_unverified_user"):
        return redirect(url_for(ADMIN_UNVERIFIED_USERS_ROUTE))

    row = database.session.execute(database.select(Usuario).filter(Usuario.id == user_id)).first()
    if row is None:
        flash(gettext("Usuario no encontrado."), "error")
        return redirect(url_for(ADMIN_UNVERIFIED_USERS_ROUTE))

    perfil_usuario = row[0]

    # Mark user as inactive
    perfil_usuario.activo = False
    perfil_usuario.modificado_por = current_user.usuario

    try:
        database.session.commit()
        flash(_("Usuario %(user)s rechazado e inactivado.") % {"user": perfil_usuario.usuario}, "info")
    except Exception as e:
        database.session.rollback()
        flash(_("Error al rechazar el usuario: %(error)s") % {"error": str(e)}, "error")

    # Clear cache
    cache.delete(CACHE_VIEW_PREFIX + url_for(ADMIN_UNVERIFIED_USERS_ROUTE))

    return redirect(url_for(ADMIN_UNVERIFIED_USERS_ROUTE))


@admin_profile.route("/admin/user/change_type", methods=["POST"])
@login_required
@perfil_requerido("admin")
def cambiar_tipo_usario() -> Response:
    """Actualiza el tipo de usuario."""
    from now_lms.demo_mode import demo_restriction_check

    new_type = request.form.get("type")
    user_id = request.form.get("user")
    redirect_to = request.form.get("redirect_to", "profile")

    # Check demo mode restrictions for any user type changes by admin
    if demo_restriction_check("change_user_type"):
        if redirect_to == "list":
            return redirect(url_for(ADMIN_USERS_ROUTE))
        return redirect(url_for("user_profile.usuario", id_usuario=user_id))

    cambia_tipo_de_usuario_por_id(
        user_id,
        nuevo_tipo=new_type,
        usuario=current_user.usuario,
    )

    # Redirect back to the appropriate page based on request
    if redirect_to == "list":
        return redirect(url_for(ADMIN_USERS_ROUTE))
    return redirect(url_for("user_profile.usuario", id_usuario=user_id))


@admin_profile.route("/admin/payments", methods=["GET"])
@login_required
@perfil_requerido("admin")
def pagos() -> str:
    """Lista de pagos recibidos."""
    from sqlalchemy import Numeric, cast

    course_code = request.args.get("course_code", "").strip()
    start_date_raw = request.args.get("start_date", "").strip()
    end_date_raw = request.args.get("end_date", "").strip()
    start_date = None
    end_date = None

    try:
        if start_date_raw:
            start_date = date.fromisoformat(start_date_raw)
        if end_date_raw:
            end_date = date.fromisoformat(end_date_raw)
    except ValueError:
        flash(gettext("El rango de fechas no es válido."), "warning")
        start_date_raw = ""
        end_date_raw = ""

    filters = []
    if course_code:
        filters.append(Pago.curso == course_code)
    if start_date:
        filters.append(Pago.fecha >= datetime.combine(start_date, time.min))
    if end_date:
        filters.append(Pago.fecha <= datetime.combine(end_date, time.max))

    query = database.select(Pago)
    if filters:
        query = query.filter(*filters)

    CONSULTA = database.paginate(
        query.order_by(Pago.fecha.desc()),
        page=request.args.get("page", default=1, type=int),
        max_per_page=MAXIMO_RESULTADOS_EN_CONSULTA_PAGINADA,
        count=True,
    )
    payment_rows = []
    for pago in CONSULTA.items:
        usuario = database.session.execute(database.select(Usuario).filter_by(usuario=pago.usuario)).scalar_one_or_none()
        curso = database.session.execute(database.select(Curso).filter_by(codigo=pago.curso)).scalar_one_or_none()
        payment_rows.append((pago, usuario, curso))

    total_pagos_query = database.select(func.count(Pago.id)).filter(Pago.estado == "completed")
    total_ingresos_query = database.select(func.sum(cast(Pago.monto, Numeric))).filter(
        Pago.estado == "completed", Pago.metodo == "paypal"
    )
    if filters:
        total_pagos_query = total_pagos_query.filter(*filters)
        total_ingresos_query = total_ingresos_query.filter(*filters)

    total_pagos = database.session.execute(total_pagos_query).scalar() or 0
    total_ingresos = database.session.execute(total_ingresos_query).scalar() or 0
    cursos = database.session.execute(database.select(Curso).order_by(Curso.nombre)).scalars().all()
    filter_args = {
        "course_code": course_code,
        "start_date": start_date_raw,
        "end_date": end_date_raw,
    }
    return render_template(
        "admin/payments.html",
        consulta=CONSULTA,
        payment_rows=payment_rows,
        cursos=cursos,
        filter_args=filter_args,
        total_pagos=total_pagos,
        total_ingresos=total_ingresos,
    )
