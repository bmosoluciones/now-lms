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
from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from flask_uploads import UploadNotAllowed
from sqlalchemy.exc import OperationalError

# ---------------------------------------------------------------------------------------
# Recursos locales
# ---------------------------------------------------------------------------------------
from now_lms.auth import perfil_requerido, proteger_secreto
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
            except UploadNotAllowed:  # pragma: no cover
                log.warning("Ocurrio un error al actualizar el logotipo del sitio web.")

        try:
            database.session.commit()
            flash("Tema del sitio web actualizado exitosamente.", "success")
            return redirect(url_for("personalizacion"))
        except OperationalError:  # pragma: no cover
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
    config = database.session.execute(database.select(Configuracion)).first()[0]
    form = MailForm(
        email=config.email,
        MAIL_HOST=config.MAIL_SERVER,
        MAIL_PORT=config.MAIL_PORT,
        MAIL_USERNAME=config.MAIL_USERNAME,
        MAIL_PASSWORD=config.MAIL_PASSWORD,
        MAIL_USE_TLS=config.MAIL_USE_TLS,
        MAIL_USE_SSL=config.MAIL_USE_SSL,
    )

    if form.validate_on_submit() or request.method == "POST":

        config.email = form.email.data
        config.MAIL_SERVER = form.MAIL_HOST.data
        config.MAIL_PORT = form.MAIL_PORT.data
        config.MAIL_USE_TLS = form.MAIL_USE_TLS.data
        config.MAIL_USE_SSL = form.MAIL_USE_SSL.data
        config.MAIL_USERNAME = form.MAIL_USERNAME.data
        config.MAIL_PASSWORD = proteger_secreto(form.MAIL_PASSWORD.data)
        config.email_verificado = False
        try:  # pragma: no cover
            database.session.commit()
            flash("Configuración de correo electronico actualizada exitosamente.", "success")
            return redirect(url_for("setting.mail"))
            return redirect(url_for("mail"))
        except OperationalError:  # pragma: no cover
            flash("No se pudo actualizar la configuración de correo electronico.", "warning")
            return redirect(url_for("setting.mail"))
    else:  # pragma: no cover
        return render_template("admin/mail.html", form=form, config=config)


@setting.route("/setting/mail_check", methods=["GET", "POST"])
@login_required
@perfil_requerido("admin")
async def test_mail():
    """Envia un correo de prueba."""
    from flask_mailing import Message
    from now_lms.mail import cargar_configuracion_correo_desde_db

    mail = cargar_configuracion_correo_desde_db()

    if current_user.correo_electronico:
        message = Message(
            subject="NOW-LMS mail setup confirmation.",
            recipients=[current_user.correo_electronico],
            body="Your email is working.",
        )
        await mail.send_message(message)
        flash(
            "Verifique su casilla de correo electronico, incluso los spam. Si no recibio un correo de confirmación favor verifique su configuración.",
            "success",
        )

    else:
        flash("Error, no ha configurado su correo electronico.", "error")

    return redirect(url_for("setting.mail"))


@setting.route("/setting/delete_site_logo")
@login_required
@perfil_requerido("admin")
def elimina_logo():
    """Elimina logo"""
    elimina_logo_perzonalizado()
    return redirect(url_for("setting.personalizacion"))
