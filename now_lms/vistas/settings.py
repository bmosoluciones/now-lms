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

"""NOW Learning Management System."""

# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required
from flask_uploads import UploadNotAllowed
from sqlalchemy.exc import OperationalError

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms.auth import perfil_requerido, proteger_secreto
from now_lms.cache import cache, invalidate_all_cache
from now_lms.config import DIRECTORIO_PLANTILLAS, images
from now_lms.db import AdSense, Configuracion, MailConfig, PaypalConfig, Style, database
from now_lms.db.tools import elimina_logo_perzonalizado
from now_lms.forms import AdSenseForm, CheckMailForm, ConfigForm, MailForm, PayaplForm, ThemeForm
from now_lms.i18n import _
from now_lms.logs import log

# Constants
SETTING_PERSONALIZACION_ROUTE = "setting.personalizacion"
SETTING_MAIL_ROUTE = "setting.mail"

# ---------------------------------------------------------------------------------------
# Administración de la configuración del sistema.
# ---------------------------------------------------------------------------------------

setting = Blueprint("setting", __name__, template_folder=DIRECTORIO_PLANTILLAS)


@setting.route("/setting/theming", methods=["GET", "POST"])
@login_required
@perfil_requerido("admin")
def personalizacion():
    """Personalizar el sistema."""
    from now_lms.themes import list_themes

    TEMPLATE_CHOICES = []

    for template in list_themes():
        TEMPLATE_CHOICES.append((template, template))

    config = database.session.execute(database.select(Style)).first()[0]
    form = ThemeForm(style=config.theme)
    form.style.choices = TEMPLATE_CHOICES

    if form.validate_on_submit() or request.method == "POST":  # pragma: no cover
        # Check if theme is changing
        old_theme = config.theme
        new_theme = form.style.data
        theme_changed = old_theme != new_theme
        config.theme = new_theme

        if "logo" in request.files:
            try:
                picture_file = images.save(request.files["logo"], name="logotipo.jpg")
                if picture_file:
                    config.custom_logo = True
                    cache.delete("cached_logo")

            except UploadNotAllowed:  # pragma: no cover
                log.warning("An error occurred while updating the website logo.")

        if "favicon" in request.files:
            try:
                picture_file = images.save(request.files["favicon"], name="favicon.png")
                if picture_file:
                    config.custom_favicon = True
                    cache.delete("cached_favicon")

            except UploadNotAllowed:  # pragma: no cover
                log.warning("An error occurred while updating the website favicon.")

        try:
            database.session.commit()
            cache.delete("cached_style")

            # Invalidate all cache if theme changed
            if theme_changed:
                invalidate_all_cache()
                log.trace(f"Theme changed from {old_theme} to {new_theme}, cache invalidated")

            flash(_("Tema del sitio web actualizado exitosamente."), "success")
            return redirect(url_for(SETTING_PERSONALIZACION_ROUTE))
        except OperationalError:  # pragma: no cover
            database.session.rollback()
            flash("No se pudo actualizar el tema del sitio web.", "warning")
            return redirect(url_for(SETTING_PERSONALIZACION_ROUTE))

    else:  # pragma: no cover
        return render_template("admin/theme.html", form=form, config=config)


@setting.route("/setting/general", methods=["GET", "POST"])
@login_required
@perfil_requerido("admin")
def configuracion():
    """System settings."""
    config = config = database.session.execute(database.select(Configuracion)).first()[0]
    config_mail = database.session.execute(database.select(MailConfig)).first()[0]
    form = ConfigForm(
        titulo=config.titulo,
        descripcion=config.descripcion,
        moneda=config.moneda,
        verify_user_by_email=config.verify_user_by_email,
        enable_programs=config.enable_programs,
        enable_masterclass=config.enable_masterclass,
        enable_resources=config.enable_resources,
        enable_blog=config.enable_blog,
    )
    if form.validate_on_submit() or request.method == "POST":
        config.titulo = form.titulo.data
        config.descripcion = form.descripcion.data
        config.moneda = form.moneda.data
        config.verify_user_by_email = form.verify_user_by_email.data
        config.enable_programs = form.enable_programs.data
        config.enable_masterclass = form.enable_masterclass.data
        config.enable_resources = form.enable_resources.data
        config.enable_blog = form.enable_blog.data

        if form.verify_user_by_email.data is True:
            config_mail = database.session.execute(database.select(MailConfig)).first()[0]
            if not config_mail.email_verificado:
                flash(_("Debe configurar el correo electronico antes de habilitar verificación por e-mail."), "warning")
                config.verify_user_by_email = False
            else:
                config.verify_user_by_email = True

        try:
            database.session.commit()
            cache.delete("site_config")
            # Clear navigation cache when configuration changes
            cache.delete("nav_programs_enabled")
            cache.delete("nav_masterclass_enabled")
            cache.delete("nav_resources_enabled")
            cache.delete("nav_blog_enabled")
            # Invalidate site currency cache when configuration changes
            from now_lms.vistas.paypal import get_site_currency

            cache.delete_memoized(get_site_currency)
            flash(_("Sitio web actualizado exitosamente."), "success")
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
            return redirect(url_for(SETTING_MAIL_ROUTE))

        except OperationalError:  # pragma: no cover
            flash("No se pudo actualizar la configuración de correo electronico.", "warning")
            return redirect(url_for(SETTING_MAIL_ROUTE))

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

        from flask_mail import Message

        from now_lms.mail import send_mail

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
            return redirect(url_for(SETTING_MAIL_ROUTE))
        except Exception as e:  # noqa: E722
            flash("Hubo un error al enviar un correo de prueba. Revise su configuración.", "warning")
            from now_lms.db import Configuracion

            config_g = database.session.execute(database.select(Configuracion)).first()[0]
            config.email_verificado = False
            config_g.verify_user_by_email = False
            database.session.commit()
            log.error(f"Error sending test email: {e}")
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
            return render_template("admin/mail.html", form=form, config=config, error=str(e))

    else:
        return render_template("admin/mail_check.html", form=form)


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
        add_leaderboard=config.add_leaderboard,
        add_medium_rectangle=config.add_medium_rectangle,
        add_large_rectangle=config.add_large_rectangle,
        add_mobile_banner=config.add_mobile_banner,
        add_wide_skyscraper=config.add_wide_skyscraper,
        add_skyscraper=config.add_skyscraper,
        add_large_skyscraper=config.add_large_skyscraper,
        add_billboard=config.add_billboard,
    )

    if form.validate_on_submit() or request.method == "POST":

        config.meta_tag = form.meta_tag.data
        config.meta_tag_include = form.meta_tag_include.data
        config.pub_id = form.pub_id.data
        config.add_code = form.add_code.data
        config.show_ads = form.show_ads.data
        config.add_leaderboard = form.add_leaderboard.data
        config.add_medium_rectangle = form.add_medium_rectangle.data
        config.add_large_rectangle = form.add_large_rectangle.data
        config.add_mobile_banner = form.add_mobile_banner.data
        config.add_wide_skyscraper = form.add_wide_skyscraper.data
        config.add_skyscraper = form.add_skyscraper.data
        config.add_large_skyscraper = form.add_large_skyscraper.data
        config.add_billboard = form.add_billboard.data

        try:  # pragma: no cover
            database.session.commit()
            flash("Configuración de Google AdSense actualizada exitosamente.", "success")
            return redirect(url_for("setting.adsense"))

        except OperationalError:  # pragma: no cover
            database.session.rollback()
            flash("No se pudo actualizar la configuración de Google AdSense.", "warning")
            return redirect(url_for("setting.adsense"))

    else:  # pragma: no cover
        return render_template("admin/adsense.html", form=form, config=config)


@setting.route("/ads.txt")
def ads_txt():
    """Información de ads.txt para anuncios."""
    try:
        config = database.session.execute(database.select(AdSense)).first()[0]
        pub_id = config.pub_id if config.pub_id else ""
    except (OperationalError, TypeError):
        pub_id = ""

    # Return ads.txt with proper content type for Google compliance
    if pub_id:
        content = f"google.com, pub-{pub_id}, DIRECT, f08c47fec0942fa0\n"
    else:
        content = "# No AdSense publisher ID configured\n"

    return content, 200, {"Content-Type": "text/plain; charset=utf-8"}


@setting.route("/setting/mail_check", methods=["GET", "POST"])
@login_required
@perfil_requerido("admin")
def test_mail():
    """Envia un correo de prueba."""
    return redirect(url_for(SETTING_MAIL_ROUTE))


@setting.route("/setting/delete_site_logo")
@login_required
@perfil_requerido("admin")
def elimina_logo():
    """Elimina logo."""
    elimina_logo_perzonalizado()
    return redirect(url_for(SETTING_PERSONALIZACION_ROUTE))


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
    form = PayaplForm(
        habilitado=config.enable,
        sandbox=config.sandbox,
        paypal_id=config.paypal_id,
        paypal_sandbox=config.paypal_sandbox,
    )

    if form.validate_on_submit() or request.method == "POST":

        # Validate PayPal configuration if enabling PayPal
        if form.habilitado.data:
            from now_lms.auth import descifrar_secreto
            from now_lms.vistas.paypal import validate_paypal_configuration

            # Get the appropriate credentials based on sandbox mode
            client_id = form.paypal_sandbox.data if form.sandbox.data else form.paypal_id.data

            # Get the secret - either from form or existing config
            if form.sandbox.data and form.paypal_sandbox_secret.data:
                client_secret = form.paypal_sandbox_secret.data
            elif not form.sandbox.data and form.paypal_secret.data:
                client_secret = form.paypal_secret.data
            elif form.sandbox.data and config.paypal_sandbox_secret:
                client_secret = descifrar_secreto(config.paypal_sandbox_secret).decode()
            elif not form.sandbox.data and config.paypal_secret:
                client_secret = descifrar_secreto(config.paypal_secret).decode()
            else:
                client_secret = None

            # Validate if we have both client ID and secret
            if client_id and client_secret:
                validation = validate_paypal_configuration(client_id, client_secret, form.sandbox.data)
                if not validation["valid"]:
                    flash(f"Error en la configuración de PayPal: {validation['message']}", "error")
                    return render_template("admin/paypal.html", form=form, config=config, with_paypal=True)

        config.enable = form.habilitado.data
        config.sandbox = form.sandbox.data
        config.paypal_id = form.paypal_id.data
        config.paypal_sandbox = form.paypal_sandbox.data

        # Only update secrets if provided (to avoid clearing them)
        if form.paypal_secret.data:
            config.paypal_secret = proteger_secreto(form.paypal_secret.data)
        if form.paypal_sandbox_secret.data:
            config.paypal_sandbox_secret = proteger_secreto(form.paypal_sandbox_secret.data)

        try:  # pragma: no cover
            database.session.commit()
            flash("Configuración de Paypal actualizada exitosamente.", "success")
            return redirect(url_for("setting.paypal"))

        except OperationalError:  # pragma: no cover
            database.session.rollback()
            flash("No se pudo actualizar la configuración de Paypal.", "warning")
            return redirect(url_for("setting.paypal"))

    else:  # pragma: no cover
        return render_template("admin/paypal.html", form=form, config=config, with_paypal=True)
