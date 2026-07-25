# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.

"""
NOW Learning Management System.

Gestión de certificados.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required
from sqlalchemy.exc import OperationalError
from werkzeug.wrappers import Response

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms.auth import perfil_requerido
from now_lms.config import DIRECTORIO_PLANTILLAS
from now_lms.db import MAXIMO_RESULTADOS_EN_CONSULTA_PAGINADA, Etiqueta, database
from now_lms.db.tools import cursos_por_etiqueta, programas_por_etiqueta
from now_lms.forms import EtiquetaForm
from now_lms.vistas._helpers import safe_commit

# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------


# Constants
TAG_TAGS_ROUTE = "tag.tags"

# ---------------------------------------------------------------------------------------
# Administración de Etiquetas.
# ---------------------------------------------------------------------------------------

tag = Blueprint("tag", __name__, template_folder=DIRECTORIO_PLANTILLAS)


@tag.route("/tag/new", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def new_tag() -> str | Response:
    """Formulario para crear una etiqueta."""
    form = EtiquetaForm()
    if form.validate_on_submit() or request.method == "POST":
        etiqueta = Etiqueta(
            nombre=form.nombre.data,
            color=form.color.data,
        )
        database.session.add(etiqueta)
        try:
            database.session.commit()
            flash(gettext("Nueva etiqueta creada."), "success")
        except OperationalError:
            database.session.rollback()
            flash("Hubo un error al crear la etiqueta.", "warning")
        return redirect(url_for(TAG_TAGS_ROUTE))

    return render_template("learning/etiquetas/nueva_etiqueta.html", form=form)


@tag.route("/tag/list", methods=["GET"])
@login_required
@perfil_requerido("instructor")
def tags() -> str:
    """Lista de etiquetas."""
    etiquetas = database.paginate(
        database.select(Etiqueta),  # noqa: E712
        page=request.args.get("page", default=1, type=int),
        max_per_page=MAXIMO_RESULTADOS_EN_CONSULTA_PAGINADA,
        count=True,
    )
    return render_template(
        "learning/etiquetas/lista_etiquetas.html",
        consulta=etiquetas,
        cursos_por_etiqueta=cursos_por_etiqueta,
        programas_por_etiqueta=programas_por_etiqueta,
    )


@tag.route("/tag/<ulid>/delete", methods=["GET"])
@login_required
@perfil_requerido("instructor")
def delete_tag(ulid: str) -> Response:
    """Elimina una etiqueta."""
    from sqlalchemy import delete

    database.session.execute(delete(Etiqueta).where(Etiqueta.id == ulid))
    safe_commit()
    return redirect(url_for(TAG_TAGS_ROUTE))


@tag.route("/tag/<ulid>/edit", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def edit_tag(ulid: str) -> str | Response:
    """Edita una etiqueta."""
    from flask import abort

    etiqueta = database.session.execute(database.select(Etiqueta).filter(Etiqueta.id == ulid)).scalar_one_or_none()
    if not etiqueta:
        abort(404)
    form = EtiquetaForm(color=etiqueta.color, nombre=etiqueta.nombre)
    if form.validate_on_submit() or request.method == "POST":
        etiqueta.nombre = form.nombre.data
        etiqueta.color = form.color.data
        try:
            database.session.add(etiqueta)
            database.session.commit()
            flash("Etiqueta editada correctamente.", "success")
        except OperationalError:
            database.session.rollback()
            flash("No se puedo editar la etiqueta.", "warning")
        return redirect(url_for(TAG_TAGS_ROUTE))

    return render_template("learning/etiquetas/editar_etiqueta.html", form=form)
