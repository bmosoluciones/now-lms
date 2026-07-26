# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""Footer links views (useful links management)."""

from __future__ import annotations

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------
from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import login_required
from werkzeug.wrappers import Response

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms.auth import perfil_requerido
from now_lms.config import DIRECTORIO_PLANTILLAS
from now_lms.db import EnlacesUtiles, database
from now_lms.forms import EnlaceUtilForm
from now_lms.i18n import _

footer_links = Blueprint("footer_links", __name__, template_folder=DIRECTORIO_PLANTILLAS)
FOOTER_LINKS_ROUTE = "footer_links.list_enlaces_utiles"


@footer_links.route("/admin/enlaces-utiles", methods=["GET"])
@login_required
@perfil_requerido("admin")
def list_enlaces_utiles() -> str:
    """List all useful links for admin."""
    enlaces = database.session.execute(database.select(EnlacesUtiles).order_by(EnlacesUtiles.orden)).scalars().all()
    return render_template("admin/enlaces_utiles.html", enlaces=enlaces)


@footer_links.route("/admin/enlaces-utiles/new", methods=["GET", "POST"])
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
        return redirect(url_for(FOOTER_LINKS_ROUTE))

    return render_template("admin/edit_enlace_util.html", form=form, enlace=None)


@footer_links.route("/admin/enlaces-utiles/<enlace_id>/edit", methods=["GET", "POST"])
@login_required
@perfil_requerido("admin")
def edit_enlace_util(enlace_id: str) -> str | Response:
    """Edit a useful link."""
    enlace = database.session.get(EnlacesUtiles, enlace_id)

    if not enlace:
        flash(_("Enlace no encontrado."), "danger")
        return redirect(url_for(FOOTER_LINKS_ROUTE))

    form = EnlaceUtilForm(obj=enlace)

    if form.validate_on_submit():
        enlace.titulo = form.titulo.data
        enlace.url = form.url.data
        enlace.orden = form.orden.data or 0
        enlace.activo = form.activo.data

        database.session.commit()

        flash(_("Enlace útil actualizado correctamente."), "success")
        return redirect(url_for(FOOTER_LINKS_ROUTE))

    return render_template("admin/edit_enlace_util.html", form=form, enlace=enlace)


@footer_links.route("/admin/enlaces-utiles/<enlace_id>/delete", methods=["POST"])
@login_required
@perfil_requerido("admin")
def delete_enlace_util(enlace_id: str) -> Response:
    """Delete a useful link."""
    enlace = database.session.get(EnlacesUtiles, enlace_id)

    if not enlace:
        flash(_("Enlace no encontrado."), "danger")
        return redirect(url_for(FOOTER_LINKS_ROUTE))

    database.session.delete(enlace)
    database.session.commit()

    flash(_("Enlace útil eliminado correctamente."), "success")
    return redirect(url_for(FOOTER_LINKS_ROUTE))
