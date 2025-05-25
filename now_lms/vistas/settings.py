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

# ---------------------------------------------------------------------------------------
# Librerias de terceros
# ---------------------------------------------------------------------------------------
from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
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
from now_lms.forms import AdSenseForm, ConfigForm, MailForm, PayaplForm, ThemeForm, CheckMailForm
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

    config = database.session.execute(database.select(Style)).first()[0]
    form = ThemeForm(style=config.theme)

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
    form = ConfigForm()
    if form.validate_on_submit() or request.method == "POST":
        config.titulo = form.titulo.data
        config.descripcion = form.descripcion.data
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
    config = database.session.execute(database.select(MailConfig)).first()[0]

    form = MailForm(
        email=config.email,
        MAIL_SERVER=config.MAIL_SERVER,
        MAIL_PORT=config.MAIL_PORT,
        MAIL_USERNAME=config.MAIL_USERNAME,
        MAIL_PASSWORD=config.MAIL_PASSWORD,
        MAIL_USE_TLS=config.MAIL_USE_TLS,
        MAIL_USE_SSL=config.MAIL_USE_SSL,
        MAIL_DEFAULT_SENDER=config.MAIL_DEFAULT_SENDER,
    )

    if form.validate_on_submit() or request.method == "POST":

        config.email = form.email.data
        config.MAIL_SERVER = form.MAIL_SERVER.data
        config.MAIL_PORT = form.MAIL_PORT.data
        config.MAIL_USE_TLS = form.MAIL_USE_TLS.data
        config.MAIL_USE_SSL = form.MAIL_USE_SSL.data
        config.MAIL_USERNAME = form.MAIL_USERNAME.data
        config.MAIL_PASSWORD = proteger_secreto(form.MAIL_PASSWORD.data)
        config.MAIL_DEFAULT_SENDER = form.MAIL_DEFAULT_SENDER.data
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


@setting.route("/setting/mail/verify", methods=["GET", "POST"])
@login_required
@perfil_requerido("admin")
def mail_check():
    """Configuración de Correo Electronico."""
    config = database.session.execute(database.select(MailConfig)).first()[0]

    form = CheckMailForm()

    if form.validate_on_submit() or request.method == "POST":
        from flask_mail import Mail, Message
        from now_lms.mail import load_email_setup

        load_email_setup(current_app)
        mail = Mail()
        mail.init_app(current_app)
        msg = Message(
            subject="Hello",
            recipients=[form.email.data],
        )
        try:
            mail.send(msg)
            try:
                config.email_verificado = True
                database.session.commit()
                flash("Correo de prueba enviado correctamente.", "success")
                return redirect(url_for("setting.mail"))
            except OperationalError:
                flash("No se pudo actualizar la configuración de correo electronico.", "warning")
                return redirect(url_for("setting.mail"))
        except:  # noqa: E722
            flash("No se puede enviar un correo de prueba. Revise su configuración.", "warning")
            return redirect(url_for("setting.mail"))

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
