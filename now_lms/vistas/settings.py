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

"""NOW Learning Management System."""

# ---------------------------------------------------------------------------------------
# Libreria estandar
# ---------------------------------------------------------------------------------------
from os import listdir
from os.path import join

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
from now_lms.auth import perfil_requerido, proteger_secreto
from now_lms.cache import cache
from now_lms.config import DIRECTORIO_PLANTILLAS, images
from now_lms.db import AdSense, Configuracion, MailConfig, PaypalConfig, Style, database
from now_lms.db.tools import elimina_logo_perzonalizado
from now_lms.forms import AdSenseForm, CheckMailForm, ConfigForm, MailForm, PayaplForm, ThemeForm
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

    THEMES_PATH = join(str(DIRECTORIO_PLANTILLAS), "themes")
    TEMPLATE_LIST = listdir(THEMES_PATH)
    TEMPLATE_CHOICES = []

    for template in TEMPLATE_LIST:
        TEMPLATE_CHOICES.append((template, template))

    config = database.session.execute(database.select(Style)).first()[0]
    form = ThemeForm(style=config.theme)
    form.style.choices = TEMPLATE_CHOICES

    if form.validate_on_submit() or request.method == "POST":  # pragma: no cover
        config.theme = form.style.data

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
            return redirect(url_for("setting.personalizacion"))
        except OperationalError:  # pragma: no cover
            flash("No se pudo actualizar el tema del sitio web.", "warning")
            return redirect(url_for("setting.personalizacion"))

    else:  # pragma: no cover
        return render_template("admin/theme.html", form=form, config=config)


@setting.route("/setting/general", methods=["GET", "POST"])
@login_required
@perfil_requerido("admin")
def configuracion():
    """Configuración del sistema."""

    config = config = database.session.execute(database.select(Configuracion)).first()[0]
    form = ConfigForm(titulo=config.titulo, descripcion=config.descripcion, verify_user_by_email=config.verify_user_by_email)
    if form.validate_on_submit() or request.method == "POST":
        config.titulo = form.titulo.data
        config.descripcion = form.descripcion.data
        config.verify_user_by_email = form.verify_user_by_email.data

        if form.verify_user_by_email.data is True:
            config_mail = database.session.execute(database.select(MailConfig)).first()[0]
            if not config_mail.email_verificado:
                flash("Debe configurar el correo electronico antes de habilitar verificación por e-mail.", "warning")
                config.verify_user_by_email = False
            else:
                config.verify_user_by_email = True

        try:
            database.session.commit()
            cache.delete("site_config")
            flash("Sitio web actualizado exitosamente.", "success")
            return redirect(url_for("setting.configuracion"))
        except OperationalError:  # pragma: no cover
            flash("No se pudo actualizar la configuración del sitio web.", "warning")
            return redirect(url_for("setting.configuracion"))

    else:
        return render_template("admin/config.html", form=form, config=config)


@setting.route("/setting/mail", methods=["GET", "POST"])
@login_required
@perfil_requerido("admin")
def mail():
    """Configuración de Correo Electronico."""
    config = database.session.execute(database.select(MailConfig)).first()[0]

    form = MailForm(
        MAIL_SERVER=config.MAIL_SERVER,
        MAIL_PORT=config.MAIL_PORT,
        MAIL_USERNAME=config.MAIL_USERNAME,
        MAIL_PASSWORD=config.MAIL_PASSWORD,
        MAIL_USE_TLS=config.MAIL_USE_TLS,
        MAIL_USE_SSL=config.MAIL_USE_SSL,
        MAIL_DEFAULT_SENDER=config.MAIL_DEFAULT_SENDER,
        MAIL_DEFAULT_SENDER_NAME=config.MAIL_DEFAULT_SENDER_NAME,
    )

    if form.validate_on_submit() or request.method == "POST":

        config.MAIL_SERVER = form.MAIL_SERVER.data
        config.MAIL_PORT = form.MAIL_PORT.data
        config.MAIL_USE_TLS = form.MAIL_USE_TLS.data
        config.MAIL_USE_SSL = form.MAIL_USE_SSL.data
        config.MAIL_USERNAME = form.MAIL_USERNAME.data
        config.MAIL_PASSWORD = proteger_secreto(form.MAIL_PASSWORD.data)
        config.MAIL_DEFAULT_SENDER = form.MAIL_DEFAULT_SENDER.data
        config.MAIL_DEFAULT_SENDER_NAME = form.MAIL_DEFAULT_SENDER_NAME.data
        config.email_verificado = False

        try:  # pragma: no cover
            database.session.commit()
            flash("Configuración de correo electronico actualizada exitosamente.", "success")
            return redirect(url_for("setting.mail"))

        except OperationalError:  # pragma: no cover
            flash("No se pudo actualizar la configuración de correo electronico.", "warning")
            return redirect(url_for("setting.mail"))

    else:  # pragma: no cover
        return render_template("admin/mail.html", form=form, config=config)


mail_check_message = """
<div class="container">
    <div class="header">
      <h1>Email Configuration Confirmed</h1>
    </div>
    <div class="content">
      <p>We are pleased to inform you that your email configuration has been successfully validated.</p>
      <p>You can now send emails using your configured settings without any issues.</p>
    </div>
    <div class="footer">
      <p>This is an automated message. Please do not reply to this email.</p>
    </div>
  </div>
"""


@setting.route("/setting/mail/verify", methods=["GET", "POST"])
@login_required
@perfil_requerido("admin")
def mail_check():
    """Configuración de Correo Electronico."""

    config = database.session.execute(database.select(MailConfig)).first()[0]

    form = CheckMailForm()

    if form.validate_on_submit() or request.method == "POST":

        from now_lms.mail import send_mail
        from flask_mail import Message

        msg = Message(
            subject="Email setup verification.",
            recipients=[form.email.data],
            sender=((config.MAIL_DEFAULT_SENDER_NAME or "NOW LMS"), config.MAIL_DEFAULT_SENDER),
        )
        msg.html = mail_check_message
        try:
            send_mail(
                msg,
                background=False,
                no_config=True,
                _log="Correo de prueba enviado desde NOW LMS",
                _flush="Correo de prueba enviado.",
            )
            config.email_verificado = True
            database.session.commit()
            return redirect(url_for("setting.mail"))
        except Exception as e:  # noqa: E722
            flash("Hubo un error al enviar un correo de prueba. Revise su configuración.", "warning")
            from now_lms.db import Configuracion

            config_g = database.session.execute(database.select(Configuracion)).first()[0]
            config.email_verificado = False
            config_g.verify_user_by_email = False
            database.session.commit()
            log.error(f"Error al enviar correo de prueba: {e}")
            # Re-render the form with the error message
            form = MailForm(
                MAIL_SERVER=config.MAIL_SERVER,
                MAIL_PORT=config.MAIL_PORT,
                MAIL_USERNAME=config.MAIL_USERNAME,
                MAIL_PASSWORD=config.MAIL_PASSWORD,
                MAIL_USE_TLS=config.MAIL_USE_TLS,
                MAIL_USE_SSL=config.MAIL_USE_SSL,
                MAIL_DEFAULT_SENDER=config.MAIL_DEFAULT_SENDER,
                MAIL_DEFAULT_SENDER_NAME=config.MAIL_DEFAULT_SENDER_NAME,
            )
            return render_template("admin/mail.html", form=form_email, config=config, error=str(e))

    else:
        return render_template("admin/mail _check.html", form=form)


@setting.route("/setting/adsense", methods=["GET", "POST"])
@login_required
@perfil_requerido("admin")
def adsense():
    """Configuración de anuncios de AdSense."""
    config = database.session.execute(database.select(AdSense)).first()[0]

    form = AdSenseForm(
        meta_tag=config.meta_tag,
        meta_tag_include=config.meta_tag_include,
        pub_id=config.pub_id,
        add_code=config.add_code,
        show_ads=config.show_ads,
    )

    if form.validate_on_submit() or request.method == "POST":

        config.meta_tag = form.meta_tag.data
        config.meta_tag_include = form.meta_tag_include.data
        config.pub_id = form.pub_id.data
        config.add_code = form.add_code.data
        config.show_ads = form.show_ads.data

        try:  # pragma: no cover
            database.session.commit()
            flash("Configuración de Google AdSense actualizada exitosamente.", "success")
            return redirect(url_for("setting.adsense"))

        except OperationalError:  # pragma: no cover
            flash("No se pudo actualizar la configuración de Google AdSense.", "warning")
            return redirect(url_for("setting.adsense"))

    else:  # pragma: no cover
        return render_template("admin/adsense.html", form=form, config=config)


@setting.route("/ads.txt")
def ads_txt():
    """Información de ads.txt para anuncios."""

    config = database.session.execute(database.select(AdSense)).first()[0]

    pub_id = config.pub_id

    return render_template("ads.txt", pub_id=pub_id)


@setting.route("/setting/mail_check", methods=["GET", "POST"])
@login_required
@perfil_requerido("admin")
def test_mail():
    """Envia un correo de prueba."""

    return redirect(url_for("setting.mail"))


@setting.route("/setting/delete_site_logo")
@login_required
@perfil_requerido("admin")
def elimina_logo():
    """Elimina logo"""
    elimina_logo_perzonalizado()
    return redirect(url_for("setting.personalizacion"))


@setting.route("/setting/stripe", methods=["GET", "POST"])
@login_required
@perfil_requerido("admin")
def stripe():
    """Configuración de Stripe."""

    return render_template("admin/stripe.html")


@setting.route("/setting/paypal", methods=["GET", "POST"])
@login_required
@perfil_requerido("admin")
def paypal():
    """Configuración de Paypal."""

    config = database.session.execute(database.select(PaypalConfig)).first()[0]
    form = PayaplForm(habilitado=config.enable)

    if form.validate_on_submit() or request.method == "POST":

        config.enable = form.habilitado.data

        try:  # pragma: no cover
            database.session.commit()
            flash("Configuración de Paypal actualizada exitosamente.", "success")
            return redirect(url_for("setting.paypal"))

        except OperationalError:  # pragma: no cover
            flash("No se pudo actualizar la configuración de Paypal.", "warning")
            return redirect(url_for("setting.paypal"))

    else:  # pragma: no cover
        return render_template("admin/paypal.html", form=form, config=config, with_paypal=True)
