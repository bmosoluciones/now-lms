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


from __future__ import annotations

from collections import OrderedDict

# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------
from datetime import datetime
from os import path

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------
from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, send_from_directory, url_for
from flask_login import current_user, login_required
from sqlalchemy import delete
from sqlalchemy.exc import OperationalError
from werkzeug.wrappers import Response

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms.auth import perfil_requerido
from now_lms.cache import cache, cache_key_with_auth_state
from now_lms.config import DESARROLLO, DIRECTORIO_PLANTILLAS, files, images
from now_lms.db import MAXIMO_RESULTADOS_EN_CONSULTA_PAGINADA, Categoria, Configuracion, Etiqueta, Recurso, database
from now_lms.forms import RecursoForm
from now_lms.misc import TIPOS_RECURSOS

# ---------------------------------------------------------------------------------------
# Interfaz de gestión de recursos descargables
# ---------------------------------------------------------------------------------------

resource_d = Blueprint("resource", __name__, template_folder=DIRECTORIO_PLANTILLAS)


@resource_d.route("/resource/new", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def new_resource() -> str | Response:
    """Nueva recursos."""
    form = RecursoForm()
    if form.validate_on_submit() or request.method == "POST":
        file_name = None  # Initialize file_name to avoid UnboundLocalError

        if "img" in request.files:
            file_name = form.codigo.data + ".jpg"
            picture_file = images.save(request.files["img"], folder="resources_files", name=file_name)
        else:
            picture_file = None

        if "recurso" in request.files:
            recurso = request.files["recurso"]
            file_name = form.codigo.data + "." + recurso.filename.split(".")[1]
            resource_file = files.save(request.files["recurso"], folder="resources_files", name=file_name)
        else:
            resource_file = ""

        # Get global configuration for HTML preformatted descriptions
        config = database.session.execute(database.select(Configuracion)).scalars().first()
        html_preformateado = False
        if config and config.enable_html_preformatted_descriptions and hasattr(form, "descripcion_html_preformateado"):
            html_preformateado = form.descripcion_html_preformateado.data or False

        recurso = Recurso(
            nombre=form.nombre.data,
            descripcion=form.descripcion.data,
            codigo=form.codigo.data,
            precio=form.precio.data,
            publico=False,
            file_name=file_name,
            tipo=form.tipo.data,
            descripcion_html_preformateado=html_preformateado,
        )
        if resource_file and picture_file:
            recurso.logo = True
        database.session.add(recurso)
        try:
            database.session.commit()
            flash("Nuevo Recurso creado correctamente.", "success")
        except OperationalError:
            flash("Hubo un error al crear el recurso.", "warning")
        return redirect(url_for("resource.lista_de_recursos"))

    return render_template("learning/recursos/nuevo_recurso.html", form=form)


@resource_d.route("/resource/list")
@login_required
@perfil_requerido("instructor")
def lista_de_recursos() -> str:
    """Lista de programas."""
    if current_user.tipo == "admin":
        consulta = database.paginate(
            database.select(Recurso),  # noqa: E712
            page=request.args.get("page", default=1, type=int),
            max_per_page=MAXIMO_RESULTADOS_EN_CONSULTA_PAGINADA,
            count=True,
        )
    else:
        consulta = database.paginate(
            database.select(Recurso).filter(Recurso.usuario == current_user.usuario),  # noqa: E712
            page=request.args.get("page", default=1, type=int),
            max_per_page=MAXIMO_RESULTADOS_EN_CONSULTA_PAGINADA,
            count=True,
        )

    return render_template("learning/recursos/lista_recursos.html", consulta=consulta)


@resource_d.route("/resource/<resource_code>/donwload")
@login_required
@perfil_requerido("user")
def descargar_recurso(resource_code: str) -> Response:
    """Genera link para descargar recurso."""
    recurso = database.session.execute(database.select(Recurso).filter(Recurso.id == resource_code)).scalars().first()
    config = current_app.upload_set_config.get("files")
    directorio = path.join(config.destination, "resources_files")

    if current_user.is_authenticated:
        if current_user.tipo == "admin":
            return send_from_directory(directorio, recurso.file_name)
        return abort(403)
    return redirect("/login")


@resource_d.route("/resource/<ulid>/delete")
@login_required
@perfil_requerido("instructor")
def delete_resource(ulid: str) -> Response:
    """Elimina recurso."""
    if current_user.tipo == "admin":
        database.session.execute(delete(Recurso).where(Recurso.id == ulid))
        database.session.commit()
        return redirect("/resources_list")
    return abort(403)


@resource_d.route("/resource/<ulid>/update", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def edit_resource(ulid: str) -> str | Response:
    """Actualiza recurso."""
    recurso = database.session.execute(database.select(Recurso).filter(Recurso.id == ulid)).scalars().first()
    form = RecursoForm(
        nombre=recurso.nombre,
        descripcion=recurso.descripcion,
        tipo=recurso.tipo,
        descripcion_html_preformateado=recurso.descripcion_html_preformateado or False,
    )

    if form.validate_on_submit() or request.method == "POST":
        if current_user.tipo == "admin":
            if recurso.promocionado is False and form.promocionado.data is True:
                recurso.fecha_promocionado = datetime.today()
            recurso.nombre = form.nombre.data
            recurso.descripcion = form.descripcion.data
            recurso.precio = form.precio.data
            recurso.publico = form.publico.data
            recurso.tipo = form.tipo.data

            # Handle HTML preformatted flag - only set if global config allows it
            config = database.session.execute(database.select(Configuracion)).scalars().first()
            if config and config.enable_html_preformatted_descriptions and hasattr(form, "descripcion_html_preformateado"):
                recurso.descripcion_html_preformateado = form.descripcion_html_preformateado.data or False
            else:
                recurso.descripcion_html_preformateado = False
        else:
            return abort(403)

        try:
            database.session.commit()
            flash("Recurso actualizado correctamente.", "success")
        except OperationalError:
            flash("Error al editar el recurso.", "warning")
        return redirect(url_for("resource.vista_recurso", resource_code=recurso.codigo))

    return render_template("learning/recursos/editar_recurso.html", form=form, recurso=recurso)


@resource_d.route("/resource/<resource_code>")
@cache.cached(key_prefix=cache_key_with_auth_state)  # type: ignore[arg-type]
def vista_recurso(resource_code: str) -> str:
    """Pagina de un recurso."""
    return render_template(
        "learning/recursos/recurso.html",
        curso=database.session.execute(database.select(Recurso).filter_by(codigo=resource_code)).scalars().first(),
        tipo=TIPOS_RECURSOS,
    )


@resource_d.route("/resource/explore")
@cache.cached(key_prefix=cache_key_with_auth_state)  # type: ignore[arg-type]
def lista_recursos() -> str:
    """Lista de programas."""
    if DESARROLLO:
        MAX_COUNT = 3
    else:
        MAX_COUNT = 30

    etiquetas = database.session.execute(database.select(Etiqueta)).scalars().all()
    categorias = database.session.execute(database.select(Categoria)).scalars().all()
    consulta_cursos = database.paginate(
        database.select(Recurso).filter(Recurso.publico.is_(True)),  # noqa: E712
        page=request.args.get("page", default=1, type=int),
        max_per_page=MAX_COUNT,
        count=True,
    )
    # /explore?page=2&nivel=2&tag=python&category=programing
    if request.args.get("nivel") or request.args.get("tag") or request.args.get("category"):
        PARAMETROS = OrderedDict()
        for arg in request.url[request.url.find("?") + 1 :].split("&"):  # noqa: E203
            PARAMETROS[arg[: arg.find("=")]] = arg[arg.find("=") + 1 :]  # noqa: E203

            # El numero de pagina debe ser generado por el macro de paginación.
            try:
                del PARAMETROS["page"]
            except KeyError:
                pass
    else:
        PARAMETROS = None

    return render_template(
        "inicio/recursos.html",
        cursos=consulta_cursos,
        etiquetas=etiquetas,
        categorias=categorias,
        parametros=PARAMETROS,
        tipo=TIPOS_RECURSOS,
    )
