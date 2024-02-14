# Copyright 2022 -2023 BMO Soluciones, S.A.
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

Gestión de certificados.
"""

# ---------------------------------------------------------------------------------------
# Libreria estandar
# ---------------------------------------------------------------------------------------

# ---------------------------------------------------------------------------------------
# Librerias de terceros
# ---------------------------------------------------------------------------------------
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required
from flask_uploads import UploadNotAllowed
from sqlalchemy.exc import OperationalError

# ---------------------------------------------------------------------------------------
# Recursos locales
# ---------------------------------------------------------------------------------------
from now_lms.auth import perfil_requerido
from now_lms.cache import cache
from now_lms.config import DIRECTORIO_PLANTILLAS, images
from now_lms.db import Configuracion, database
from now_lms.db.tools import elimina_logo_perzonalizado
from now_lms.forms import ConfigForm, MailForm, ThemeForm
from now_lms.logs import log

# ---------------------------------------------------------------------------------------
# Administración de la configuración del sistema.
# ---------------------------------------------------------------------------------------

setting = Blueprint("setting", __name__, template_folder=DIRECTORIO_PLANTILLAS)


@setting.route("/setting/theming", methods=["GET", "POST"])
@login_required
@perfil_requerido("admin")
def personalizacion():
    """Personalizar el sistema."""

    config = Configuracion.query.first()
    form = ThemeForm(style=config.style)

    if form.validate_on_submit() or request.method == "POST":  # pragma: no cover
        config.style = form.style.data

        if "logo" in request.files:
            try:
                picture_file = images.save(request.files["logo"], name="logotipo.jpg")
                if picture_file:
                    config.custom_logo = True
                    cache.delete("cached_logo")
                    cache.delete("cached_style")
            except UploadNotAllowed:
                log.warning("Ocurrio un error al actualizar el logotipo del sitio web.")

        try:
            database.session.commit()
            flash("Tema del sitio web actualizado exitosamente.", "success")
            return redirect(url_for("personalizacion"))
        except OperationalError:
            flash("No se pudo actualizar el tema del sitio web.", "warning")
            return redirect(url_for("personalizacion"))

    else:  # pragma: no cover
        return render_template("admin/theme.html", form=form, config=config)


@setting.route("/setting/general", methods=["GET", "POST"])
@login_required
@perfil_requerido("admin")
def configuracion():
    """Configuración del sistema."""

    config = Configuracion.query.first()
    form = ConfigForm(modo=config.modo, moneda=config.moneda)
    if form.validate_on_submit() or request.method == "POST":
        config.titulo = form.titulo.data
        config.descripcion = form.descripcion.data
        config.modo = form.descripcion.data
        config.stripe = form.stripe.data
        config.paypal = form.paypal.data
        config.stripe_secret = form.stripe_secret.data
        config.stripe_public = form.stripe_secret.data
        config.moneda = form.moneda.data
        try:
            database.session.commit()
            cache.delete("site_config")
            flash("Sitio web actualizado exitosamente.", "success")
            return redirect("/admin")
        except OperationalError:  # pragma: no cover
            flash("No se pudo actualizar la configuración del sitio web.", "warning")
            return redirect("/admin")

    else:
        return render_template("admin/config.html", form=form, config=config)


@setting.route("/setting/mail", methods=["GET", "POST"])
@login_required
@perfil_requerido("admin")
def mail():
    """Configuración de Correo Electronico."""
    config = Configuracion.query.first()
    form = MailForm()
    if form.validate_on_submit() or request.method == "POST":  # pragma: no cover
        config.email = form.email.data
        config.mail_server = form.mail_server.data
        config.mail_port = form.mail_port.data
        config.mail_use_tls = form.mail_use_tls.data
        config.mail_use_ssl = form.mail_use_ssl.data
        config.mail_username = form.mail_username.data
        config.mail_password = form.mail_password.data
        try:  # pragma: no cover
            database.session.commit()
            flash("Configuración de correo electronico actualizada exitosamente.", "success")
            return redirect(url_for("mail"))
        except OperationalError:
            flash("No se pudo actualizar la configuración de correo electronico.", "warning")
            return redirect(url_for("mail"))
    else:  # pragma: no cover
        return render_template("admin/mail.html", form=form, config=configuracion)


@setting.route("/setting/delete_site_logo")
@login_required
@perfil_requerido("admin")
def elimina_logo():
    """Elimina logo"""
    elimina_logo_perzonalizado()
    return redirect(url_for("personalizacion"))
