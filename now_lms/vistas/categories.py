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
from now_lms.db import MAXIMO_RESULTADOS_EN_CONSULTA_PAGINADA, Categoria, database
from now_lms.db.tools import cursos_por_categoria, programas_por_categoria
from now_lms.forms import CategoriaForm

# Route constants
ROUTE_CATEGORY_CATEGORIES = "category.categories"

# ---------------------------------------------------------------------------------------
# Interfaz de mensajes
# ---------------------------------------------------------------------------------------

category = Blueprint("category", __name__, template_folder=DIRECTORIO_PLANTILLAS)


@category.route("/category/new", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def new_category():
    """Nueva Categoria."""
    form = CategoriaForm()
    if form.validate_on_submit() or request.method == "POST":
        categoria = Categoria(
            nombre=form.nombre.data,
            descripcion=form.descripcion.data,
        )
        database.session.add(categoria)
        try:
            database.session.commit()
            flash("Nueva categoria creada.", "success")
        except OperationalError:  # pragma: no cover
            flash("Hubo un error al crear la categoria.", "warning")
        return redirect(url_for(ROUTE_CATEGORY_CATEGORIES))

    return render_template("learning/categorias/nueva_categoria.html", form=form)


@category.route("/category/list")
@login_required
@perfil_requerido("instructor")
def categories():
    """Lista de categorias."""
    categorias = database.paginate(
        database.select(Categoria),  # noqa: E712
        page=request.args.get("page", default=1, type=int),
        max_per_page=MAXIMO_RESULTADOS_EN_CONSULTA_PAGINADA,
        count=True,
    )
    return render_template(
        "learning/categorias/lista_categorias.html",
        consulta=categorias,
        cursos_por_categoria=cursos_por_categoria,
        programas_por_categoria=programas_por_categoria,
    )


@category.route("/category/<ulid>/delete")
@login_required
@perfil_requerido("instructor")
def delete_category(ulid: str):
    """Elimina categoria."""
    from sqlalchemy import delete

    database.session.execute(delete(Categoria).where(Categoria.id == ulid))
    database.session.commit()
    return redirect(url_for(ROUTE_CATEGORY_CATEGORIES))


@category.route("/category/<ulid>/edit", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def edit_category(ulid: str):
    """Editar categoria."""
    categoria = database.session.execute(database.select(Categoria).filter(Categoria.id == ulid)).scalar_one_or_none()
    form = CategoriaForm(nombre=categoria.nombre, descripcion=categoria.descripcion)
    if form.validate_on_submit() or request.method == "POST":
        categoria.nombre = form.nombre.data
        categoria.descripcion = form.descripcion.data
        try:
            database.session.add(categoria)
            database.session.commit()
            flash("Categoria editada correctamente.", "success")
        except OperationalError:  # pragma: no cover
            flash("No se puedo editar la categoria.", "warning")
        return redirect(url_for(ROUTE_CATEGORY_CATEGORIES))

    return render_template("learning/categorias/editar_categoria.html", form=form)
