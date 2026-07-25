# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""NOW Learning Management System."""

from __future__ import annotations

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required
from flask_uploads import UploadNotAllowed
from sqlalchemy.exc import OperationalError
from werkzeug.wrappers import Response

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms.auth import perfil_requerido, proteger_secreto
from now_lms.cache import cache, invalidate_all_cache
from now_lms.config import DIRECTORIO_PLANTILLAS, images
from now_lms.db import AdSense, Configuracion, MailConfig, PaypalConfig, Style, ExternalApiKey, database
from now_lms.db.tools import elimina_logo_perzonalizado
from now_lms.forms import AdSenseForm, CheckMailForm, ConfigForm, MailForm, PayaplForm, ThemeForm, ExternalApiKeyForm
from now_lms.i18n import _
from now_lms.logs import log

# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------

# Constants
SETTING_PERSONALIZACION_ROUTE = "setting.personalizacion"
SETTING_MAIL_ROUTE = "setting.mail"
HOME_ROUTE = "home.pagina_de_inicio"
ADMIN_MAIL_TEMPLATE = "admin/mail.html"
ADMIN_PAYPAL_TEMPLATE = "admin/paypal.html"

# ---------------------------------------------------------------------------------------
# Administración de la configuración del sistema.
# ---------------------------------------------------------------------------------------

setting = Blueprint("setting", __name__, template_folder=DIRECTORIO_PLANTILLAS)


def _save_theme_asset(config: Style, field_name: str, filename: str, config_attribute: str) -> None:
    """Save an optional theme asset and mark it as configured."""
    if field_name not in request.files:
        return
    try:
        if images.save(request.files[field_name], name=filename):
            setattr(config, config_attribute, True)
    except UploadNotAllowed:
        log.warning("An error occurred while updating the website %s.", field_name)


def _configuration_form(config: Configuracion) -> ConfigForm:
    """Build the general settings form from persisted configuration."""
    values = {
        field: getattr(config, field)
        for field in (
            "titulo",
            "descripcion",
            "moneda",
            "lang",
            "enable_programs",
            "enable_masterclass",
            "enable_resources",
            "enable_blog",
            "enable_contact",
            "show_latest_blog_posts_on_home",
            "enable_file_uploads",
            "max_file_size",
            "enable_html_preformatted_descriptions",
            "enable_footer",
            "verify_user_by_email",
            "allow_unverified_email_login",
            "titulo_html",
            "hero",
            "enable_feature_section",
            "custom_feature_section",
            "custom_text1",
            "custom_text2",
            "custom_text3",
            "custom_text4",
            "eslogan",
            "social_facebook",
            "social_twitter",
            "social_linkedin",
            "social_youtube",
            "social_instagram",
            "social_github",
            "contact_address",
            "contact_email",
            "contact_phone",
            "contact_mobile",
            "contact_whatsapp",
        )
    }
    values["timezone"] = config.time_zone
    return ConfigForm(**values)


def _update_configuration(config: Configuracion, form: ConfigForm) -> None:
    """Copy editable general settings from the form to the model."""
    fields = (
        "titulo",
        "descripcion",
        "moneda",
        "lang",
        "enable_programs",
        "enable_masterclass",
        "enable_resources",
        "enable_blog",
        "enable_contact",
        "show_latest_blog_posts_on_home",
        "enable_file_uploads",
        "max_file_size",
        "enable_html_preformatted_descriptions",
        "enable_footer",
        "verify_user_by_email",
        "allow_unverified_email_login",
        "titulo_html",
        "hero",
        "enable_feature_section",
        "custom_feature_section",
        "custom_text1",
        "custom_text2",
        "custom_text3",
        "custom_text4",
        "eslogan",
        "social_facebook",
        "social_twitter",
        "social_linkedin",
        "social_youtube",
        "social_instagram",
        "social_github",
        "contact_address",
        "contact_email",
        "contact_phone",
        "contact_mobile",
        "contact_whatsapp",
    )
    for field in fields:
        setattr(config, field, getattr(form, field).data)
    config.time_zone = form.timezone.data


def _validate_email_verification(config: Configuracion, form: ConfigForm) -> None:
    """Only enable email verification when mail is configured and verified."""
    if not form.verify_user_by_email.data:
        return
    row = database.session.execute(database.select(MailConfig)).first()
    if row is None or not row[0].email_verificado:
        config.verify_user_by_email = False
        flash(_("Debe configurar el correo electronico antes de habilitar verificación por e-mail."), "warning")
        return
    config.verify_user_by_email = True


def invalidar_cache() -> bool:
    """
    Invalida comprensivamente todas las entradas de la cache relacionadas con la configuración del sistema.

    Esta función debe ejecutarse al actualizar la configuración o la apariencia del sistema para asegurar
    que los usuarios no vean información incorrecta o desactualizada.

    Invalida:
    - Configuración global del sistema (moneda, lenguaje, zona horaria)
    - Configuración de navegación (programas, masterclass, recursos, blog)
    - Configuración del sitio (título, descripción)
    - Logos y favicons personalizados
    - Estilos y temas
    - Configuración de PayPal
    - Configuración de idioma para Babel
    - Todas las demás entradas de cache del sistema

    Returns:
        bool: True if cache invalidation was successful, False otherwise
    """
    try:
        # Invalidate specific configuration caches
        cache.delete("configuracion_global")  # i18n configuration
        cache.delete("site_config")  # site configuration
        cache.delete("site_config_global")  # global site configuration for templates
        cache.delete("global_config")  # global config from db/tools.py

        # Invalidate navigation configuration caches
        cache.delete("nav_programs_enabled")
        cache.delete("nav_masterclass_enabled")
        cache.delete("nav_resources_enabled")
        cache.delete("nav_blog_enabled")
        cache.delete("nav_contact_enabled")

        # Invalidate appearance caches
        cache.delete("cached_style")
        cache.delete("cached_logo")
        cache.delete("cached_favicon")

        # Invalidate PayPal configuration caches
        from now_lms.vistas.paypal import check_paypal_enabled, get_site_currency

        cache.delete_memoized(get_site_currency)
        cache.delete_memoized(check_paypal_enabled)

        # Clear all remaining cache entries to ensure complete invalidation
        # This is safe for configuration changes as they are infrequent operations
        invalidate_all_cache()

        log.trace("Comprehensive cache invalidation completed successfully")
        return True

    except Exception as e:
        log.error(f"Error during comprehensive cache invalidation: {e}")
        return False


@setting.route("/setting/theming", methods=["GET", "POST"])
@login_required
@perfil_requerido("admin")
def personalizacion() -> str | Response:
    """Personalizar el sistema."""
    from now_lms.themes import list_themes

    TEMPLATE_CHOICES = []

    for template in list_themes():
        TEMPLATE_CHOICES.append((template, template))

    row = database.session.execute(database.select(Style)).first()
    if row is None:
        return redirect(url_for(HOME_ROUTE))
    config = row[0]
    form = ThemeForm(style=config.theme)
    form.style.choices = TEMPLATE_CHOICES

    if form.validate_on_submit() or request.method == "POST":
        # Check if theme is changing
        old_theme = config.theme
        new_theme = form.style.data
        theme_changed = old_theme != new_theme
        config.theme = new_theme

        _save_theme_asset(config, "logo", "logotipo.jpg", "custom_logo")
        _save_theme_asset(config, "favicon", "favicon.png", "custom_favicon")

        try:
            database.session.commit()

            # Always invalidate cache when appearance settings change
            # This includes theme changes, logo updates, and favicon updates
            invalidar_cache()

            if theme_changed:
                log.trace(f"Theme changed from {old_theme} to {new_theme}, comprehensive cache invalidated")
            else:
                log.trace("Appearance settings updated, comprehensive cache invalidated")

            flash(_("Tema del sitio web actualizado exitosamente."), "success")
            return redirect(url_for(SETTING_PERSONALIZACION_ROUTE))
        except OperationalError:
            database.session.rollback()
            flash(_("No se pudo actualizar el tema del sitio web."), "warning")
            return redirect(url_for(SETTING_PERSONALIZACION_ROUTE))

    else:
        return render_template("admin/theme.html", form=form, config=config)


@setting.route("/setting/general", methods=["GET", "POST"])
@login_required
@perfil_requerido("admin")
def configuracion() -> str | Response:
    """System settings."""
    row = database.session.execute(database.select(Configuracion)).first()
    if row is None:
        return redirect(url_for(HOME_ROUTE))
    config = row[0]
    row = database.session.execute(database.select(MailConfig)).first()
    if row is None:
        return redirect(url_for(HOME_ROUTE))
    form = _configuration_form(config)
    if form.validate_on_submit() or request.method == "POST":
        _update_configuration(config, form)
        _validate_email_verification(config, form)

        try:
            # Invalidate all configuration-related cache
            invalidar_cache()

            database.session.commit()
            flash(_("Sitio web actualizado exitosamente."), "success")
            return redirect(url_for("setting.configuracion"))
        except OperationalError:
            flash(_("No se pudo actualizar la configuración del sitio web."), "warning")
            return redirect(url_for("setting.configuracion"))

    else:
        return render_template("admin/config.html", form=form, config=config)


@setting.route("/setting/mail", methods=["GET", "POST"])
@login_required
@perfil_requerido("admin")
def mail() -> str | Response:
    """Configuración de Correo Electronico."""
    row = database.session.execute(database.select(MailConfig)).first()
    if row is None:
        return redirect(url_for(HOME_ROUTE))
    config = row[0]

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
        from now_lms.demo_mode import demo_restriction_check

        # Check demo mode restrictions for mail settings
        if demo_restriction_check("mail_settings"):
            return render_template(ADMIN_MAIL_TEMPLATE, form=form, config=config)

        config.MAIL_SERVER = form.MAIL_SERVER.data
        config.MAIL_PORT = form.MAIL_PORT.data
        config.MAIL_USE_TLS = form.MAIL_USE_TLS.data
        config.MAIL_USE_SSL = form.MAIL_USE_SSL.data
        config.MAIL_USERNAME = form.MAIL_USERNAME.data
        config.MAIL_PASSWORD = proteger_secreto(form.MAIL_PASSWORD.data)
        config.MAIL_DEFAULT_SENDER = form.MAIL_DEFAULT_SENDER.data
        config.MAIL_DEFAULT_SENDER_NAME = form.MAIL_DEFAULT_SENDER_NAME.data
        config.email_verificado = False

        try:
            database.session.commit()

            # Invalidate cache when mail configuration changes
            # This ensures mail-related settings are properly refreshed
            invalidar_cache()

            flash(_("Configuración de correo electronico actualizada exitosamente."), "success")
            return redirect(url_for(SETTING_MAIL_ROUTE))

        except OperationalError:
            flash(_("No se pudo actualizar la configuración de correo electronico."), "warning")
            return redirect(url_for(SETTING_MAIL_ROUTE))

    else:
        return render_template(ADMIN_MAIL_TEMPLATE, form=form, config=config)


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
def mail_check() -> str | Response:
    """Configuración de Correo Electronico."""
    row = database.session.execute(database.select(MailConfig)).first()
    if row is None:
        return redirect(url_for(HOME_ROUTE))
    config = row[0]

    form = CheckMailForm()

    if form.validate_on_submit() or request.method == "POST":
        from now_lms.demo_mode import demo_restriction_check

        # Check demo mode restrictions for sending test mail
        if demo_restriction_check("send_test_mail"):
            return render_template("admin/mail_check.html", form=form)

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
            flash(_("Hubo un error al enviar un correo de prueba. Revise su configuración."), "warning")

            row = database.session.execute(database.select(Configuracion)).first()
            if row:
                config_g = row[0]
                config.email_verificado = False
                config_g.verify_user_by_email = False
                database.session.commit()
            else:
                config.email_verificado = False
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
            return render_template(ADMIN_MAIL_TEMPLATE, form=form, config=config, error=str(e))

    else:
        return render_template("admin/mail_check.html", form=form)


@setting.route("/setting/adsense", methods=["GET", "POST"])
@login_required
@perfil_requerido("admin")
def adsense() -> str | Response:
    """Configuración de anuncios de AdSense."""
    row = database.session.execute(database.select(AdSense)).first()
    if row is None:
        return redirect(url_for(HOME_ROUTE))
    config = row[0]

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
        from now_lms.demo_mode import demo_restriction_check

        # Check demo mode restrictions for AdSense settings
        if demo_restriction_check("adsense_settings"):
            return render_template("admin/adsense.html", form=form, config=config)

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

        try:
            database.session.commit()

            # Invalidate cache when AdSense configuration changes
            # This ensures ad settings are properly refreshed across the site
            invalidar_cache()

            flash(_("Configuración de Google AdSense actualizada exitosamente."), "success")
            return redirect(url_for("setting.adsense"))

        except OperationalError:
            database.session.rollback()
            flash(_("No se pudo actualizar la configuración de Google AdSense."), "warning")
            return redirect(url_for("setting.adsense"))

    else:
        return render_template("admin/adsense.html", form=form, config=config)


@setting.route("/ads.txt", methods=["GET"])
def ads_txt() -> tuple[str, int, dict[str, str]]:
    """Información de ads.txt para anuncios."""
    try:
        row = database.session.execute(database.select(AdSense)).first()
        if row is None:
            pub_id = ""
        else:
            config = row[0]
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
def test_mail() -> Response:
    """Envia un correo de prueba."""
    return redirect(url_for(SETTING_MAIL_ROUTE))


@setting.route("/setting/delete_site_logo", methods=["GET"])
@login_required
@perfil_requerido("admin")
def elimina_logo() -> Response:
    """Elimina logo."""
    elimina_logo_perzonalizado()
    return redirect(url_for(SETTING_PERSONALIZACION_ROUTE))


@setting.route("/setting/stripe", methods=["GET", "POST"])
@login_required
@perfil_requerido("admin")
def stripe() -> str:
    """Configuración de Stripe."""
    return render_template("admin/stripe.html")


@setting.route("/setting/api_keys", methods=["GET", "POST"])
@login_required
@perfil_requerido("admin")
def api_keys() -> str | Response:
    """Manage external API keys."""
    import hashlib
    import secrets

    keys = database.session.execute(database.select(ExternalApiKey).order_by(ExternalApiKey.timestamp.desc())).scalars().all()

    form = ExternalApiKeyForm()
    new_key_plain = None

    if form.validate_on_submit():
        # Generate a new random API key
        api_key = secrets.token_urlsafe(32)
        new_key_plain = api_key

        key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        new_key = ExternalApiKey(
            name=form.name.data, key_hash=key_hash, active=True, allowed_origin=form.allowed_origin.data, notes=form.notes.data
        )

        database.session.add(new_key)
        database.session.commit()
        flash(_("API Key creada exitosamente. Asegúrese de copiarla ahora, ya que no podrá verla de nuevo."), "success")

        # Refresh the list to include the new key
        keys = (
            database.session.execute(database.select(ExternalApiKey).order_by(ExternalApiKey.timestamp.desc())).scalars().all()
        )

    return render_template("admin/api_keys.html", keys=keys, form=form, new_key_plain=new_key_plain)


@setting.route("/setting/api_keys/<key_id>/revoke", methods=["POST"])
@login_required
@perfil_requerido("admin")
def revoke_api_key(key_id: str) -> Response:
    """Revoke an API key."""
    from datetime import datetime

    key = database.session.get(ExternalApiKey, key_id)
    if key:
        key.active = False
        key.revoked_at = datetime.now()
        database.session.commit()
        flash(_("API Key revocada exitosamente."), "success")

    return redirect(url_for("setting.api_keys"))


def _resolve_paypal_client_secret(form: PayaplForm, config: PaypalConfig, descifrar_secreto) -> str | None:
    """Resolve the PayPal client secret from form data or existing config."""
    if form.sandbox.data:
        if form.paypal_sandbox_secret.data:
            return form.paypal_sandbox_secret.data
        if config.paypal_sandbox_secret:
            return descifrar_secreto(config.paypal_sandbox_secret).decode()
        return None

    if form.paypal_secret.data:
        return form.paypal_secret.data
    if config.paypal_secret:
        return descifrar_secreto(config.paypal_secret).decode()
    return None


def _validate_paypal_enabled(form: PayaplForm, config: PaypalConfig) -> bool:
    """Validate PayPal configuration when enabling PayPal. Returns False if invalid."""
    from now_lms.auth import descifrar_secreto
    from now_lms.vistas.paypal import validate_paypal_configuration

    client_id = form.paypal_sandbox.data if form.sandbox.data else form.paypal_id.data
    client_secret = _resolve_paypal_client_secret(form, config, descifrar_secreto)

    if not (client_id and client_secret):
        return True

    validation = validate_paypal_configuration(client_id, client_secret, form.sandbox.data)
    if validation["valid"]:
        return True

    flash(gettext("Error en la configuración de PayPal: %(error)s", error=validation['message']), "error")
    return False


def _save_paypal_config(form: PayaplForm, config: PaypalConfig) -> Response:
    """Save PayPal configuration from form data."""
    config.enable = form.habilitado.data
    config.sandbox = form.sandbox.data
    config.paypal_id = form.paypal_id.data
    config.paypal_sandbox = form.paypal_sandbox.data

    if form.paypal_secret.data:
        config.paypal_secret = proteger_secreto(form.paypal_secret.data)
    if form.paypal_sandbox_secret.data:
        config.paypal_sandbox_secret = proteger_secreto(form.paypal_sandbox_secret.data)

    try:
        database.session.commit()
        invalidar_cache()
        flash(_("Configuración de Paypal actualizada exitosamente."), "success")
    except OperationalError:
        database.session.rollback()
        flash(_("No se pudo actualizar la configuración de Paypal."), "warning")

    return redirect(url_for("setting.paypal"))


@setting.route("/setting/paypal", methods=["GET", "POST"])
@login_required
@perfil_requerido("admin")
def paypal() -> str | Response:
    """Configuración de Paypal."""
    row = database.session.execute(database.select(PaypalConfig)).first()
    if row is None:
        return redirect(url_for(HOME_ROUTE))

    config = row[0]
    form = PayaplForm(
        habilitado=config.enable,
        sandbox=config.sandbox,
        paypal_id=config.paypal_id,
        paypal_sandbox=config.paypal_sandbox,
    )

    if not (form.validate_on_submit() or request.method == "POST"):
        return render_template(ADMIN_PAYPAL_TEMPLATE, form=form, config=config, with_paypal=True)

    from now_lms.demo_mode import demo_restriction_check

    if demo_restriction_check("paypal_settings"):
        return render_template(ADMIN_PAYPAL_TEMPLATE, form=form, config=config, with_paypal=True)

    if form.habilitado.data and not _validate_paypal_enabled(form, config):
        return render_template(ADMIN_PAYPAL_TEMPLATE, form=form, config=config, with_paypal=True)

    return _save_paypal_config(form, config)
