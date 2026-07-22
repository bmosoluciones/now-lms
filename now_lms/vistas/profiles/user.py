# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.

"""User profile views and functionality."""

from __future__ import annotations

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from flask_uploads import UploadNotAllowed
from sqlalchemy.exc import OperationalError
from werkzeug.wrappers import Response

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms.cache import cache
from now_lms.calendar_utils import get_upcoming_events_for_user
from now_lms.config import DIRECTORIO_PLANTILLAS, images
from now_lms.db import Certificacion, Curso, DocenteCurso, EstudianteCurso, Usuario, database
from now_lms.db.tools import elimina_imagen_usuario
from now_lms.forms import ChangePasswordForm, UserForm
from now_lms.logs import log
from now_lms.misc import GENEROS

# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------


# Constants
PROFILE_ROUTE = "/perfil"
TEMPLATE_CAMBIAR_CONTRASENA = "inicio/cambiar_contraseña.html"

user_profile = Blueprint("user_profile", __name__, template_folder=DIRECTORIO_PLANTILLAS)


def _update_profile_photo(usuario_: Usuario) -> None:
    """Save a profile photo when one was uploaded."""
    if "logo" not in request.files:
        return
    try:
        picture_file = images.save(request.files["logo"], folder="usuarios", name=current_user.id + ".jpg")
        if picture_file:
            usuario_.portada = True
            database.session.commit()
            flash("Imagen de perfil actualizada.", "success")
    except UploadNotAllowed:
        log.warning("Could not update profile image.")


# ---------------------------------------------------------------------------------------
# Espacio del usuario, por defecto un usuario se considera un estudiante.
# ---------------------------------------------------------------------------------------
@user_profile.route("/student", methods=["GET"])
@login_required
def pagina_estudiante() -> str:
    """Perfil de usuario."""
    # Get upcoming calendar events for the dashboard
    upcoming_events = get_upcoming_events_for_user(current_user.usuario, limit=5)

    return render_template("perfiles/estudiante.html", upcoming_events=upcoming_events)


@user_profile.route("/perfil", methods=["GET"])
@login_required
def perfil() -> str | Response:
    """Perfil del usuario."""
    row = database.session.execute(database.select(Usuario).filter(Usuario.id == current_user.id)).first()
    if row is None:
        return redirect(url_for("home.pagina_de_inicio"))
    registro_usuario = row[0]

    # Initialize context data
    cursos_inscritos = []
    certificaciones = []
    cursos_creados = []

    # Fetch data based on user type
    if registro_usuario.tipo == "student":
        # Get enrolled courses for students
        cursos_inscritos_query = database.session.execute(
            database.select(Curso)
            .join(EstudianteCurso, Curso.codigo == EstudianteCurso.curso)
            .filter(EstudianteCurso.usuario == current_user.usuario)
            .filter(EstudianteCurso.vigente.is_(True))  # noqa: E712
        ).fetchall()
        cursos_inscritos = [curso[0] for curso in cursos_inscritos_query]

        # Get certifications for students
        certificaciones_query = database.session.execute(
            database.select(Certificacion, Curso)
            .join(Curso, Certificacion.curso == Curso.codigo)
            .filter(Certificacion.usuario == current_user.usuario)
        ).fetchall()
        certificaciones = [{"certificacion": cert[0], "curso": cert[1]} for cert in certificaciones_query]

    elif registro_usuario.tipo == "instructor":
        # Get courses created by instructors
        cursos_creados_query = database.session.execute(
            database.select(Curso)
            .join(DocenteCurso, Curso.codigo == DocenteCurso.curso)
            .filter(DocenteCurso.usuario == current_user.usuario)
            .filter(DocenteCurso.vigente.is_(True))  # noqa: E712
        ).fetchall()
        cursos_creados = [curso[0] for curso in cursos_creados_query]

    return render_template(
        "inicio/perfil.html",
        perfil=registro_usuario,
        genero=GENEROS,
        cursos_inscritos=cursos_inscritos,
        certificaciones=certificaciones,
        cursos_creados=cursos_creados,
    )


@user_profile.route("/user/<id_usuario>", methods=["GET"])
@login_required
def usuario(id_usuario: str) -> str:
    """Acceso administrativo al perfil de un usuario."""
    perfil_usuario = database.session.execute(database.select(Usuario).filter_by(usuario=id_usuario)).scalar_one_or_none()
    if perfil_usuario is None:
        abort(404)
    # La misma plantilla del perfil de usuario con permisos elevados como
    # activar desactivar el perfil o cambiar el perfil del usuario.
    if current_user.usuario == id_usuario or current_user.tipo != "student" or perfil_usuario.visible is True:
        return render_template("inicio/perfil.html", perfil=perfil_usuario, genero=GENEROS)
    return render_template("inicio/private.html")


@user_profile.route("/perfil/edit/<ulid>", methods=["GET", "POST"])
@login_required
def edit_perfil(ulid: str) -> str | Response:
    """Actualizar información de usuario."""
    if current_user.id != ulid:
        abort(403)

    usuario_ = database.session.get(Usuario, ulid)
    if usuario_ is None:
        abort(404)
    form = UserForm(obj=usuario_)

    if request.method == "POST":
        #
        email_changed = form.correo_electronico.data != usuario_.correo_electronico

        usuario_.nombre = form.nombre.data
        usuario_.apellido = form.apellido.data
        usuario_.correo_electronico = form.correo_electronico.data
        usuario_.url = form.url.data
        usuario_.linkedin = form.linkedin.data
        usuario_.facebook = form.facebook.data
        usuario_.twitter = form.twitter.data
        usuario_.github = form.github.data
        usuario_.youtube = form.youtube.data
        usuario_.genero = form.genero.data
        usuario_.titulo = form.titulo.data
        usuario_.nacimiento = form.nacimiento.data
        usuario_.bio = form.bio.data

        if email_changed:
            usuario_.correo_electronico_verificado = False
            flash("Favor verifique su nuevo correo electronico.", "warning")

        try:
            database.session.commit()
            cache.delete("view/" + url_for("user_profile.perfil"))
            flash("Pefil actualizado.", "success")
            _update_profile_photo(usuario_)
        except OperationalError as e:
            database.session.rollback()
            log.error(f"OperationalError in edit_perfil: {e}")
            flash("Error al editar el perfil.", "error")

        return redirect(PROFILE_ROUTE)

    return render_template("inicio/perfil_editar.html", form=form, usuario=usuario_)


@user_profile.route("/perfil/<ulid>/delete_logo", methods=["GET"])
@login_required
def elimina_logo_usuario(ulid: str) -> Response:
    """Elimina logo de usuario."""
    if current_user.id != ulid:
        abort(403)

    elimina_imagen_usuario(ulid=ulid)
    return redirect(PROFILE_ROUTE)


@user_profile.route("/perfil/cambiar_contraseña/<ulid>", methods=["GET", "POST"])
@login_required
def cambiar_contrasena(ulid: str) -> str | Response:
    """Cambiar contraseña del usuario."""
    if current_user.id != ulid:
        abort(403)

    usuario_ = database.session.get(Usuario, ulid)
    if not usuario_:
        abort(404)

    form = ChangePasswordForm()

    if request.method == "POST" and form.validate_on_submit():
        from now_lms.auth import proteger_passwd, validar_acceso
        from now_lms.demo_mode import demo_restriction_check

        # Check demo mode restrictions for admin users
        if demo_restriction_check("change_admin_password"):
            return render_template(TEMPLATE_CAMBIAR_CONTRASENA, form=form, usuario=usuario_)

        # Verificar contraseña actual
        if not validar_acceso(usuario_.usuario, form.current_password.data):
            flash("La contraseña actual es incorrecta.", "error")
            return render_template(TEMPLATE_CAMBIAR_CONTRASENA, form=form, usuario=usuario_)

        # Verificar que las nuevas contraseñas coincidan
        if form.new_password.data != form.confirm_password.data:
            flash("Las nuevas contraseñas no coinciden.", "error")
            return render_template(TEMPLATE_CAMBIAR_CONTRASENA, form=form, usuario=usuario_)

        # Actualizar contraseña
        try:
            usuario_.acceso = proteger_passwd(form.new_password.data)
            database.session.commit()
            flash("Contraseña actualizada exitosamente.", "success")
            return redirect(PROFILE_ROUTE)
        except OperationalError:
            flash("Error al actualizar la contraseña.", "error")

    return render_template(TEMPLATE_CAMBIAR_CONTRASENA, form=form, usuario=usuario_)


@user_profile.route("/payments", methods=["GET"])
@login_required
def payments_history() -> str:
    """Historial de pagos para cualquier usuario autenticado."""
    from now_lms.db import Pago, Curso

    results = database.session.execute(
        database.select(Pago, Curso)
        .outerjoin(Curso, Pago.curso == Curso.codigo)
        .filter(Pago.usuario == current_user.usuario)
        .order_by(Pago.fecha.desc())
    ).all()

    pago_rows = []
    for pago, curso in results:
        pago_rows.append({"pago": pago, "curso": curso})

    return render_template("payments/history.html", pago_rows=pago_rows)


@user_profile.route("/payments/receipt/<payment_id>", methods=["GET"])
@login_required
def download_receipt(payment_id: str) -> Response:
    """Descargar recibo de pago sencillo en PDF."""
    from now_lms.db import Pago, Curso
    from flask_weasyprint import HTML, render_pdf

    pago = database.session.execute(
        database.select(Pago).filter_by(id=payment_id, usuario=current_user.usuario, estado="completed")
    ).scalar_one_or_none()

    if not pago:
        abort(404)

    curso = database.session.execute(
        database.select(Curso).filter_by(codigo=pago.curso)
    ).scalar_one_or_none()

    html_content = render_template("payments/receipt_pdf.html", pago=pago, curso=curso)

    return render_pdf(
        HTML(string=html_content),
        download_filename=f"receipt_{pago.referencia or pago.id}.pdf"
    )
