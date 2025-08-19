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

"""
NOW Learning Management System.

Gestión de certificados.
"""

# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------


# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required
from sqlalchemy.exc import OperationalError

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms.auth import perfil_requerido
from now_lms.config import DIRECTORIO_PLANTILLAS
from now_lms.db import MAXIMO_RESULTADOS_EN_CONSULTA_PAGINADA, Etiqueta, database
from now_lms.db.tools import cursos_por_etiqueta, programas_por_etiqueta
from now_lms.forms import EtiquetaForm

# Constants
TAG_TAGS_ROUTE = "tag.tags"

# ---------------------------------------------------------------------------------------
# Administración de Etiquetas.
# ---------------------------------------------------------------------------------------

tag = Blueprint("tag", __name__, template_folder=DIRECTORIO_PLANTILLAS)


@tag.route("/tag/new", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def new_tag():
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
            flash("Nueva etiqueta creada.", "successs")
        except OperationalError:  # pragma: no cover
            database.session.rollback()
            flash("Hubo un error al crear la etiqueta.", "warning")
        return redirect(url_for(TAG_TAGS_ROUTE))

    return render_template("learning/etiquetas/nueva_etiqueta.html", form=form)


@tag.route("/tag/list")
@login_required
@perfil_requerido("instructor")
def tags():
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


@tag.route("/tag/<ulid>/delete")
@login_required
@perfil_requerido("instructor")
def delete_tag(ulid: str):
    """Elimina una etiqueta."""
    from sqlalchemy import delete

    database.session.execute(delete(Etiqueta).where(Etiqueta.id == ulid))
    database.session.commit()
    return redirect(url_for(TAG_TAGS_ROUTE))


@tag.route("/tag/<ulid>/edit", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def edit_tag(ulid: str):
    """Edita una etiqueta."""
    etiqueta = database.session.execute(database.select(Etiqueta).filter(Etiqueta.id == ulid)).scalar_one_or_none()
    form = EtiquetaForm(color=etiqueta.color, nombre=etiqueta.nombre)
    if form.validate_on_submit() or request.method == "POST":
        etiqueta.nombre = form.nombre.data
        etiqueta.color = form.color.data
        try:
            database.session.add(etiqueta)
            database.session.commit()
            flash("Etiqueta editada correctamente.", "success")
        except OperationalError:  # pragma: no cover
            database.session.rollback()
            flash("No se puedo editar la etiqueta.", "warning")
        return redirect(url_for(TAG_TAGS_ROUTE))

    return render_template("learning/etiquetas/editar_etiqueta.html", form=form)
