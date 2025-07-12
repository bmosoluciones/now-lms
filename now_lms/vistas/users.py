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
from now_lms.forms import LoginForm, LogonForm
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
    return render_template("auth/login.html", form=form, titulo="Inicio de Sesion - NOW LMS")


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
                tipo="user",
                activo=False,
                creado_por=form.usuario.data,
            )
            try:
                database.session.add(usuario_)
                database.session.commit()
                flash("Cuenta creada exitosamente.", "success")
                if config.verify_user_by_email:
                    mail = database.session.execute(database.select(MailConfig)).first()[0]
                    from now_lms.auth import send_confirmation_email

                    send_confirmation_email(usuario_)

                return INICIO_SESION
            except OperationalError:  # pragma: no cover
                flash("Error al crear la cuenta.", "warning")
                return redirect("/logon")
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
            tipo="user",
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
