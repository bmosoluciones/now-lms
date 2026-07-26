# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""Custom pages views (admin-managed DB-driven pages)."""

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
from now_lms.db import CustomPage, database
from now_lms.i18n import _

custom_pages = Blueprint("custom_pages", __name__, template_folder=DIRECTORIO_PLANTILLAS)
PAGE_NOT_FOUND_MESSAGE = _("Página no encontrada.")
HOME_ROUTE = "home.pagina_de_inicio"


@custom_pages.route("/page/<slug>", methods=["GET"])
@cache.cached(timeout=300)
def view_page(slug: str) -> str | Response:
    """View a custom page by slug."""
    # Validate slug to prevent path traversal
    if any(c in slug for c in ["/", "\\", ".", "$"]):
        flash(PAGE_NOT_FOUND_MESSAGE, "danger")
        return redirect(url_for("custom_pages.list_pages"))

    page = database.session.execute(
        database.select(CustomPage).filter(CustomPage.slug == slug, CustomPage.is_active.is_(True))
    ).scalar_one_or_none()

    if not page:
        flash(PAGE_NOT_FOUND_MESSAGE, "danger")
        return redirect(url_for(HOME_ROUTE))

    return render_template("page_info/custom_page.html", page=page)


@custom_pages.route("/admin/pages", methods=["GET"])
@login_required
@perfil_requerido("admin")
def list_pages() -> str:
    """List all custom pages for admin."""
    pages = database.session.execute(database.select(CustomPage).order_by(CustomPage.slug)).scalars().all()

    return render_template("admin/custom_pages.html", pages=pages)


@custom_pages.route("/admin/pages/<page_id>/edit", methods=["GET", "POST"])
@login_required
@perfil_requerido("admin")
def edit_page(page_id: str) -> str | Response:
    """Edit a custom page."""
    page = database.session.get(CustomPage, page_id)

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
        return redirect(url_for("custom_pages.list_pages"))

    return render_template("admin/edit_custom_page.html", page=page)
