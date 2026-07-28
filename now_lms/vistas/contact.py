# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""Contact views (contact form and contact messages management)."""

from __future__ import annotations

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import login_required
from werkzeug.wrappers import Response

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms.auth import perfil_requerido
from now_lms.config import DIRECTORIO_PLANTILLAS
from now_lms.db import ContactMessage, database
from now_lms.i18n import _

contact = Blueprint("contact", __name__, template_folder=DIRECTORIO_PLANTILLAS)
HOME_ROUTE = "home.pagina_de_inicio"
CONTACT_TEMPLATE = "page_info/contact.html"


@contact.route("/contact", methods=["GET", "POST"])
def contact_form() -> str | Response:
    """Contact form page."""
    from now_lms.db import Configuracion

    config_row = database.session.execute(database.select(Configuracion)).first()
    config = config_row[0] if config_row else None

    # Honor the admin toggle: while contact is disabled this page must not serve.
    # Fork-local fix ported from the pre-split static_pages.py at the v2.0.0
    # sync (upstream's split carried the same bug; offered upstream as U1).
    if not (config and config.enable_contact):
        abort(404)

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


@contact.route("/admin/contact-messages", methods=["GET"])
@login_required
@perfil_requerido("admin")
def list_contact_messages() -> str:
    """List all contact messages."""
    status_filter = request.args.get("status", "all")
    subject_query = request.args.get("q", "").strip()

    query = database.select(ContactMessage).order_by(ContactMessage.creado.desc())

    if status_filter != "all":
        query = query.filter(ContactMessage.status == status_filter)

    # Subject filter so waiting-list rows are one URL away:
    # /admin/contact-messages?q=[ACCESS] (the access-request discriminator).
    # Fork-local, ported from the pre-split static_pages.py at the v2.0.0 sync.
    if subject_query:
        query = query.filter(ContactMessage.subject.like(f"%{subject_query}%"))

    messages = database.session.execute(query).scalars().all()

    return render_template("admin/contact_messages.html", messages=messages, status_filter=status_filter)


@contact.route("/admin/contact-messages/<message_id>/view", methods=["GET", "POST"])
@login_required
@perfil_requerido("admin")
def view_contact_message(message_id: str) -> str | Response:
    """View and update a contact message."""
    from flask_login import current_user

    message = database.session.get(ContactMessage, message_id)

    if not message:
        flash(_("Mensaje no encontrado."), "danger")
        return redirect(url_for("contact.list_contact_messages"))

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
        return redirect(url_for("contact.list_contact_messages"))

    return render_template("admin/view_contact_message.html", message=message)
