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
"""Static pages views (About Us, Privacy Policy, Contact)."""

from __future__ import annotations

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required
from werkzeug.wrappers import Response

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms.auth import perfil_requerido
from now_lms.cache import cache
from now_lms.config import DIRECTORIO_PLANTILLAS
from now_lms.db import ContactMessage, EnlacesUtiles, StaticPage, database
from now_lms.forms import EnlaceUtilForm
from now_lms.i18n import _

static_pages = Blueprint("static_pages", __name__, template_folder=DIRECTORIO_PLANTILLAS)
PAGE_NOT_FOUND_MESSAGE = _("Página no encontrada.")
HOME_ROUTE = "home.pagina_de_inicio"
CONTACT_TEMPLATE = "page_info/contact.html"
STATIC_LINKS_ROUTE = "static_pages.list_enlaces_utiles"


@static_pages.route("/page/<slug>")
@cache.cached(timeout=300)
def view_page(slug: str) -> str | Response:
    """View a static page by slug."""
    # Validate slug to prevent path traversal
    if any(c in slug for c in ["/", "\\", ".", "$"]):
        flash(PAGE_NOT_FOUND_MESSAGE, "danger")
        return redirect(url_for("static_pages.list_pages"))

    page = database.session.execute(
        database.select(StaticPage).filter(StaticPage.slug == slug, StaticPage.is_active.is_(True))
    ).scalar_one_or_none()

    if not page:
        flash(PAGE_NOT_FOUND_MESSAGE, "danger")
        return redirect(url_for(HOME_ROUTE))

    return render_template("page_info/static_page.html", page=page)


@static_pages.route("/contact", methods=["GET", "POST"])
def contact() -> str | Response:
    """Contact form page."""
    # Get system configuration to display contact information
    from now_lms.db import Configuracion

    config_row = database.session.execute(database.select(Configuracion)).first()
    config = config_row[0] if config_row else None

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        subject = request.form.get("subject", "").strip()
        message = request.form.get("message", "").strip()

        # Basic validation
        if not name or not email or not subject or not message:
            flash(_("Por favor complete todos los campos."), "warning")
            return render_template(CONTACT_TEMPLATE, config=config)

        if len(name) > 150 or len(email) > 150 or len(subject) > 200 or len(message) > 5000:
            flash(_("Uno o más campos exceden la longitud máxima permitida."), "warning")
            return render_template(CONTACT_TEMPLATE, config=config)

        # Save contact message
        contact_msg = ContactMessage(
            name=name,
            email=email,
            subject=subject,
            message=message,
            status="not_seen",
        )
        database.session.add(contact_msg)
        database.session.commit()

        flash(_("Gracias por contactarnos. Le responderemos pronto."), "success")
        return redirect(url_for(HOME_ROUTE))

    return render_template(CONTACT_TEMPLATE, config=config)


@static_pages.route("/admin/pages")
@login_required
@perfil_requerido("admin")
def list_pages() -> str:
    """List all static pages for admin."""
    pages = database.session.execute(database.select(StaticPage).order_by(StaticPage.slug)).scalars().all()

    return render_template("admin/static_pages.html", pages=pages)


@static_pages.route("/admin/pages/<page_id>/edit", methods=["GET", "POST"])
@login_required
@perfil_requerido("admin")
def edit_page(page_id: str) -> str | Response:
    """Edit a static page."""
    page = database.session.get(StaticPage, page_id)

    if not page:
        flash(PAGE_NOT_FOUND_MESSAGE, "danger")
        return redirect(url_for(HOME_ROUTE))

    if request.method == "POST":
        page.title = request.form.get("title", "").strip()
        page.content = request.form.get("content", "").strip()
        page.is_active = request.form.get("is_active") == "on"
        page.mostrar_en_footer = request.form.get("mostrar_en_footer") == "on"

        database.session.commit()

        # Invalidate cache
        cache.delete_memoized(view_page, page.slug)

        flash(_("Página actualizada correctamente."), "success")
        return redirect(url_for("static_pages.list_pages"))

    return render_template("admin/edit_static_page.html", page=page)


@static_pages.route("/admin/contact-messages")
@login_required
@perfil_requerido("admin")
def list_contact_messages() -> str:
    """List all contact messages."""
    status_filter = request.args.get("status", "all")

    query = database.select(ContactMessage).order_by(ContactMessage.creado.desc())

    if status_filter != "all":
        query = query.filter(ContactMessage.status == status_filter)

    messages = database.session.execute(query).scalars().all()

    return render_template("admin/contact_messages.html", messages=messages, status_filter=status_filter)


@static_pages.route("/admin/contact-messages/<message_id>/view", methods=["GET", "POST"])
@login_required
@perfil_requerido("admin")
def view_contact_message(message_id: str) -> str | Response:
    """View and update a contact message."""
    from flask_login import current_user

    message = database.session.get(ContactMessage, message_id)

    if not message:
        flash(_("Mensaje no encontrado."), "danger")
        return redirect(url_for("static_pages.list_contact_messages"))

    # Mark as seen on first view
    if message.status == "not_seen":
        message.status = "seen"
        database.session.commit()

    if request.method == "POST":
        new_status = request.form.get("status")
        admin_notes = request.form.get("admin_notes", "").strip()

        if new_status in ["not_seen", "seen", "answered"]:
            message.status = new_status

            if new_status == "answered":
                from datetime import datetime, timezone

                message.answered_at = datetime.now(timezone.utc)
                message.answered_by = current_user.usuario

        if admin_notes:
            message.admin_notes = admin_notes

        database.session.commit()
        flash(_("Mensaje actualizado correctamente."), "success")
        return redirect(url_for("static_pages.list_contact_messages"))

    return render_template("admin/view_contact_message.html", message=message)


@static_pages.route("/admin/enlaces-utiles")
@login_required
@perfil_requerido("admin")
def list_enlaces_utiles() -> str:
    """List all useful links for admin."""
    enlaces = database.session.execute(database.select(EnlacesUtiles).order_by(EnlacesUtiles.orden)).scalars().all()
    return render_template("admin/enlaces_utiles.html", enlaces=enlaces)


@static_pages.route("/admin/enlaces-utiles/new", methods=["GET", "POST"])
@login_required
@perfil_requerido("admin")
def create_enlace_util() -> str | Response:
    """Create a new useful link."""
    form = EnlaceUtilForm()

    if form.validate_on_submit():
        enlace = EnlacesUtiles(
            titulo=form.titulo.data,
            url=form.url.data,
            orden=form.orden.data or 0,
            activo=form.activo.data,
        )
        database.session.add(enlace)
        database.session.commit()

        flash(_("Enlace útil creado correctamente."), "success")
        return redirect(url_for(STATIC_LINKS_ROUTE))

    return render_template("admin/edit_enlace_util.html", form=form, enlace=None)


@static_pages.route("/admin/enlaces-utiles/<enlace_id>/edit", methods=["GET", "POST"])
@login_required
@perfil_requerido("admin")
def edit_enlace_util(enlace_id: str) -> str | Response:
    """Edit a useful link."""
    enlace = database.session.get(EnlacesUtiles, enlace_id)

    if not enlace:
        flash(_("Enlace no encontrado."), "danger")
        return redirect(url_for(STATIC_LINKS_ROUTE))

    form = EnlaceUtilForm(obj=enlace)

    if form.validate_on_submit():
        enlace.titulo = form.titulo.data
        enlace.url = form.url.data
        enlace.orden = form.orden.data or 0
        enlace.activo = form.activo.data

        database.session.commit()

        flash(_("Enlace útil actualizado correctamente."), "success")
        return redirect(url_for(STATIC_LINKS_ROUTE))

    return render_template("admin/edit_enlace_util.html", form=form, enlace=enlace)


@static_pages.route("/admin/enlaces-utiles/<enlace_id>/delete", methods=["POST"])
@login_required
@perfil_requerido("admin")
def delete_enlace_util(enlace_id: str) -> Response:
    """Delete a useful link."""
    enlace = database.session.get(EnlacesUtiles, enlace_id)

    if not enlace:
        flash(_("Enlace no encontrado."), "danger")
        return redirect(url_for(STATIC_LINKS_ROUTE))

    database.session.delete(enlace)
    database.session.commit()

    flash(_("Enlace útil eliminado correctamente."), "success")
    return redirect(url_for(STATIC_LINKS_ROUTE))
