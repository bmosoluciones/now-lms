# Copyright 2025 BMO Soluciones, S.A.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Contributors:
# - William José Moreno Reyes

"""
NOW Learning Management System.

Gestión de usuarios.
"""

# ---------------------------------------------------------------------------------------
# Libreria estandar
# ---------------------------------------------------------------------------------------

# ---------------------------------------------------------------------------------------
# Librerias de terceros
# ---------------------------------------------------------------------------------------
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy.exc import OperationalError

# ---------------------------------------------------------------------------------------
# Recursos locales
# ---------------------------------------------------------------------------------------
from now_lms.auth import perfil_requerido, proteger_passwd, validar_acceso
from now_lms.config import DIRECTORIO_PLANTILLAS
from now_lms.db import Configuracion, MailConfig, Usuario, database
from now_lms.forms import LoginForm, LogonForm, ForgotPasswordForm, ResetPasswordForm
from now_lms.logs import log
from now_lms.misc import INICIO_SESION, PANEL_DE_USUARIO

# ---------------------------------------------------------------------------------------
# Administración de Usuarios.
# ---------------------------------------------------------------------------------------

user = Blueprint("user", __name__, template_folder=DIRECTORIO_PLANTILLAS)


@user.route("/user/login", methods=["GET", "POST"])
def inicio_sesion():
    """Inicio de sesión del usuario."""
    if current_user.is_authenticated:
        flash("Su usuario ya tiene una sesión iniciada.", "info")
        return PANEL_DE_USUARIO
    form = LoginForm()

    # Check if password recovery is available
    mail_config = database.session.execute(database.select(MailConfig)).first()
    show_forgot_password = mail_config and mail_config[0].email_verificado

    if form.validate_on_submit():
        if validar_acceso(form.usuario.data, form.acceso.data):
            identidad = Usuario.query.filter_by(usuario=form.usuario.data).first()
            if identidad.activo:
                login_user(identidad)
                return PANEL_DE_USUARIO
            else:  # pragma: no cover
                flash("Su cuenta esta inactiva.", "info")
                return INICIO_SESION
        else:  # pragma: no cover
            flash("Inicio de Sesion Incorrecto.", "warning")
            return INICIO_SESION
    return render_template(
        "auth/login.html", form=form, titulo="Inicio de Sesion - NOW LMS", show_forgot_password=show_forgot_password
    )


@user.route("/user/logout")
def cerrar_sesion():  # pragma: no cover
    """Finaliza la sesion actual."""
    logout_user()
    return redirect("/home")


# ---------------------------------------------------------------------------------------
# Registro de Nuevos Usuarios.
# - Crear cuenta directamente por el usuario.
# - Crear nuevo usuario por acción del administrador del sistema.
# ---------------------------------------------------------------------------------------
@user.route("/user/logon", methods=["GET", "POST"])
def crear_cuenta():
    """Crear cuenta de usuario desde el sistio web."""

    if current_user.is_authenticated:
        flash("Usted ya posee una cuenta en el sistema.", "warning")
        return PANEL_DE_USUARIO

    else:
        form = LogonForm()
        config = database.session.execute(database.select(Configuracion)).first()[0]
        if form.validate_on_submit() or request.method == "POST":
            usuario_ = Usuario(
                usuario=form.correo_electronico.data,
                acceso=proteger_passwd(form.acceso.data),
                nombre=form.nombre.data,
                apellido=form.apellido.data,
                correo_electronico=form.correo_electronico.data,
                tipo="student",
                activo=False,
                creado_por=form.correo_electronico.data,
            )
            from sqlalchemy.exc import PendingRollbackError

            try:

                database.session.add(usuario_)
                database.session.commit()
                log.info(f"Se ha creado una cuenta de usuario: {usuario_.usuario}")
                if config.verify_user_by_email:
                    mail_config = database.session.execute(database.select(MailConfig)).first()[0]
                    from now_lms.auth import send_confirmation_email

                    send_confirmation_email(usuario_)
                    return render_template(
                        "error_pages/verify_mail.html",
                        mail_config=mail_config,
                    )

                else:
                    return INICIO_SESION
            except OperationalError:  # pragma: no cover
                flash("Error al crear la cuenta.", "warning")
                return redirect("/")
            except PendingRollbackError:  # pragma: no cover
                flash("Error al crear la cuenta.", "warning")
                return redirect("/")
        else:
            return render_template("auth/logon.html", form=form, titulo="Crear cuenta - NOW LMS")


@user.route("/user/new_user", methods=["GET", "POST"])
@login_required
@perfil_requerido("admin")
def crear_usuario():  # pragma: no cover
    """Crear manualmente una cuenta de usuario."""
    form = LogonForm()
    if form.validate_on_submit() or request.method == "POST":
        usuario_ = Usuario(
            usuario=form.usuario.data,
            acceso=proteger_passwd(form.acceso.data),
            nombre=form.nombre.data,
            apellido=form.apellido.data,
            correo_electronico=form.correo_electronico.data,
            tipo="student",
            activo=False,
            creado_por=current_user.usuario,
            correo_electronico_verificado=True,
        )
        try:
            database.session.add(usuario_)
            database.session.commit()
            flash("Usuario creado exitosamente.", "success")
            return redirect(url_for("user_profile.usuario", id_usuario=form.usuario.data))
        except OperationalError:  # pragma: no cover
            flash("Error al crear la cuenta.", "warning")
            return redirect("/new_user")
    else:
        return render_template(
            "learning/nuevo_usuario.html",
            form=form,
        )


@user.route("/user/check_mail/<token>")
def check_mail(token):
    """Verifica correo electronico."""
    from now_lms.auth import validate_confirmation_token

    _token = validate_confirmation_token(token)
    if _token:
        flash("Correo verificado exitosamente. Ya puede iniciar sesión en el sistema", "success")
        return redirect(url_for("user.inicio_sesion"))
    else:
        flash("Token de verificación invalido.", "warning")
        return redirect(url_for("user.cerrar_sesion"))


@user.route("/user/forgot_password", methods=["GET", "POST"])
def forgot_password():
    """Solicitar recuperación de contraseña."""
    if current_user.is_authenticated:
        flash("Su usuario ya tiene una sesión iniciada.", "info")
        return PANEL_DE_USUARIO

    form = ForgotPasswordForm()
    if form.validate_on_submit():
        # Check if user exists and has verified email
        user = Usuario.query.filter_by(correo_electronico=form.email.data).first()
        if user and user.correo_electronico_verificado:
            # Check if email system is configured
            mail_config = database.session.execute(database.select(MailConfig)).first()
            if mail_config and mail_config[0].email_verificado:
                from now_lms.auth import send_password_reset_email

                if send_password_reset_email(user):
                    flash("Se ha enviado un correo con instrucciones para recuperar su contraseña.", "success")
                else:
                    flash("Error al enviar el correo de recuperación. Intente más tarde.", "error")
            else:
                flash("El sistema de correo no está configurado. Contacte al administrador.", "warning")
        else:
            # For security, we show the same message even if user doesn't exist or email not verified
            flash("Se ha enviado un correo con instrucciones para recuperar su contraseña.", "success")

        return redirect(url_for("user.inicio_sesion"))

    return render_template("auth/forgot_password.html", form=form, titulo="Recuperar Contraseña - NOW LMS")


@user.route("/user/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    """Restablecer contraseña con token."""
    if current_user.is_authenticated:
        flash("Su usuario ya tiene una sesión iniciada.", "info")
        return PANEL_DE_USUARIO

    from now_lms.auth import validate_password_reset_token

    email = validate_password_reset_token(token)
    if not email:
        flash("El enlace de recuperación es inválido o ha expirado.", "error")
        return redirect(url_for("user.inicio_sesion"))

    user = Usuario.query.filter_by(correo_electronico=email).first()
    if not user:
        flash("Usuario no encontrado.", "error")
        return redirect(url_for("user.inicio_sesion"))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        if form.new_password.data != form.confirm_password.data:
            flash("Las nuevas contraseñas no coinciden.", "error")
            return render_template("auth/reset_password.html", form=form, titulo="Restablecer Contraseña - NOW LMS")

        # Update password
        user.acceso = proteger_passwd(form.new_password.data)
        database.session.commit()

        flash("Contraseña actualizada exitosamente. Ya puede iniciar sesión.", "success")
        log.info(f"Contraseña restablecida para el usuario {user.usuario}")
        return redirect(url_for("user.inicio_sesion"))

    return render_template("auth/reset_password.html", form=form, titulo="Restablecer Contraseña - NOW LMS")
