# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""Custom pages views (admin-managed DB-driven pages)."""

from __future__ import annotations

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------
import re

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from werkzeug.wrappers import Response

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms.auth import perfil_requerido
from now_lms.cache import cache
from now_lms.config import DIRECTORIO_PLANTILLAS
from now_lms.db import CustomPage, database
from now_lms.forms import CustomPageForm
from now_lms.i18n import _

custom_pages = Blueprint("custom_pages", __name__, template_folder=DIRECTORIO_PLANTILLAS)
PAGE_NOT_FOUND_MESSAGE = _("Página no encontrada.")
HOME_ROUTE = "home.pagina_de_inicio"


def _slugify(text: str) -> str:
    """Generate a URL-safe slug from text."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text)
    return text.strip("-")


def _validate_slug_unique(slug: str, exclude_id: str | None = None) -> bool:
    """Check that slug is unique among custom pages."""
    query = database.select(CustomPage).filter(CustomPage.slug == slug)
    if exclude_id:
        query = query.filter(CustomPage.id != exclude_id)
    existing = database.session.execute(query).scalar_one_or_none()
    return existing is None


@custom_pages.route("/page/<slug>", methods=["GET"])
@cache.cached(timeout=300)
def view_page(slug: str) -> str | Response:
    """View a custom page by slug."""
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


@custom_pages.route("/admin/pages/new", methods=["GET", "POST"])
@login_required
@perfil_requerido("admin")
def create_page() -> str | Response:
    """Create a new custom page."""
    form = CustomPageForm()

    if form.validate_on_submit():
        slug = form.slug.data.strip()

        if not _validate_slug_unique(slug):
            flash(_("Ya existe una página con ese slug."), "danger")
            return render_template("admin/edit_custom_page.html", form=form, page=None)

        page = CustomPage(
            title=form.title.data.strip(),
            slug=slug,
            content=form.content.data.strip(),
            is_active=form.is_active.data,
            mostrar_en_footer=form.mostrar_en_footer.data,
            creado_por=current_user.usuario,
        )
        database.session.add(page)
        database.session.commit()

        cache.delete_memoized(view_page, page.slug)

        flash(_("Página creada correctamente."), "success")
        return redirect(url_for("custom_pages.list_pages"))

    return render_template("admin/edit_custom_page.html", form=form, page=None)


@custom_pages.route("/admin/pages/<page_id>/edit", methods=["GET", "POST"])
@login_required
@perfil_requerido("admin")
def edit_page(page_id: str) -> str | Response:
    """Edit a custom page."""
    page = database.session.get(CustomPage, page_id)

    if not page:
        flash(PAGE_NOT_FOUND_MESSAGE, "danger")
        return redirect(url_for(HOME_ROUTE))

    form = CustomPageForm(obj=page)

    if form.validate_on_submit():
        new_slug = form.slug.data.strip()

        if new_slug != page.slug and not _validate_slug_unique(new_slug, exclude_id=page.id):
            flash(_("Ya existe una página con ese slug."), "danger")
            return render_template("admin/edit_custom_page.html", form=form, page=page)

        old_slug = page.slug
        page.title = form.title.data.strip()
        page.slug = new_slug
        page.content = form.content.data.strip()
        page.is_active = form.is_active.data
        page.mostrar_en_footer = form.mostrar_en_footer.data
        page.modificado_por = current_user.usuario

        database.session.commit()

        cache.delete_memoized(view_page, old_slug)
        if old_slug != new_slug:
            cache.delete_memoized(view_page, new_slug)

        flash(_("Página actualizada correctamente."), "success")
        return redirect(url_for("custom_pages.list_pages"))

    return render_template("admin/edit_custom_page.html", form=form, page=page)


@custom_pages.route("/admin/pages/<page_id>/delete", methods=["POST"])
@login_required
@perfil_requerido("admin")
def delete_page(page_id: str) -> Response:
    """Delete a custom page."""
    page = database.session.get(CustomPage, page_id)

    if not page:
        flash(PAGE_NOT_FOUND_MESSAGE, "danger")
        return redirect(url_for(HOME_ROUTE))

    cache.delete_memoized(view_page, page.slug)

    database.session.delete(page)
    database.session.commit()

    flash(_("Página eliminada correctamente."), "success")
    return redirect(url_for("custom_pages.list_pages"))


@custom_pages.route("/admin/pages/<page_id>/toggle", methods=["POST"])
@login_required
@perfil_requerido("admin")
def toggle_page(page_id: str) -> Response:
    """Toggle active status of a custom page."""
    page = database.session.get(CustomPage, page_id)

    if not page:
        flash(PAGE_NOT_FOUND_MESSAGE, "danger")
        return redirect(url_for(HOME_ROUTE))

    page.is_active = not page.is_active
    page.modificado_por = current_user.usuario
    database.session.commit()

    cache.delete_memoized(view_page, page.slug)

    status = _("activada") if page.is_active else _("desactivada")
    flash(_("Página {status} correctamente.").format(status=status), "success")
    return redirect(url_for("custom_pages.list_pages"))
