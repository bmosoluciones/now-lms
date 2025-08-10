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

from collections import OrderedDict

# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------
from datetime import datetime

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from flask_uploads import UploadNotAllowed
from sqlalchemy.exc import OperationalError
from sqlalchemy import delete

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms.auth import perfil_requerido
from now_lms.cache import cache, no_guardar_en_cache_global
from now_lms.config import DESARROLLO, DIRECTORIO_PLANTILLAS, images
from now_lms.db import MAXIMO_RESULTADOS_EN_CONSULTA_PAGINADA, Categoria, Etiqueta, Programa, database
from now_lms.db.tools import cuenta_cursos_por_programa
from now_lms.forms import ProgramaForm
from now_lms.themes import get_program_list_template, get_program_view_template

# Constants
PROGRAMS_ROUTE = "program.programas"

# ---------------------------------------------------------------------------------------
# Interfaz de gestión de programas
# ---------------------------------------------------------------------------------------

program = Blueprint("program", __name__, template_folder=DIRECTORIO_PLANTILLAS)


@program.route("/program/new", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def nuevo_programa():
    """Nueva programa."""
    form = ProgramaForm()
    if form.validate_on_submit() or request.method == "POST":

        programa = Programa(
            nombre=form.nombre.data,
            descripcion=form.descripcion.data,
            codigo=form.codigo.data,
            precio=form.precio.data,
            publico=False,
            estado="draft",
            logo=False,
            creado_por=current_user.id,
        )
        database.session.add(programa)
        try:
            database.session.commit()
            cache.delete("view/" + url_for(PROGRAMS_ROUTE))
            flash("Nuevo Programa creado.", "success")
            return redirect(url_for("program.pagina_programa", codigo=programa.codigo))
        except OperationalError:  # pragma: no cover
            flash("Hubo un error al crear el programa.", "warning")
            return redirect(url_for(PROGRAMS_ROUTE))

    return render_template("learning/programas/nuevo_programa.html", form=form)


@program.route("/program/list")
@login_required
@perfil_requerido("instructor")
@cache.cached(timeout=60)
def programas():
    """Lista de programas"""

    if current_user.tipo == "admin":
        consulta = database.paginate(
            database.select(Programa),  # noqa: E712
            page=request.args.get("page", default=1, type=int),
            max_per_page=MAXIMO_RESULTADOS_EN_CONSULTA_PAGINADA,
            count=True,
        )
    else:
        consulta = database.paginate(
            database.select(Programa).filter(Programa.creado_por == current_user.id),  # noqa: E712
            page=request.args.get("page", default=1, type=int),
            max_per_page=MAXIMO_RESULTADOS_EN_CONSULTA_PAGINADA,
            count=True,
        )

    return render_template("learning/programas/lista_programas.html", consulta=consulta)


@program.route("/program/<ulid>/delete")
@login_required
@perfil_requerido("instructor")
def delete_program(ulid: str):
    """Elimina programa."""
    database.session.execute(delete(Programa).where(Programa.id == ulid))

    if current_user.tipo == "admin":
        database.session.commit()
        cache.delete("view/" + url_for(PROGRAMS_ROUTE))
        return redirect(url_for(PROGRAMS_ROUTE))
    else:
        return abort(403)


@program.route("/program/<ulid>/edit", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def edit_program(ulid: str):
    """Editar programa."""
    programa = database.session.execute(database.select(Programa).filter(Programa.id == ulid)).scalars().first()

    form = ProgramaForm(
        nombre=programa.nombre,
        descripcion=programa.descripcion,
        codigo=programa.codigo,
        precio=programa.precio,
        estado=programa.estado,
        promocionado=programa.promocionado,
    )
    if current_user.tipo != "admin":
        return abort(403)

    if form.validate_on_submit() or request.method == "POST":
        if programa.promocionado is False and form.promocionado.data is True:
            programa.fecha_promocionado = datetime.today()

        programa.nombre = form.nombre.data
        programa.descripcion = form.descripcion.data
        programa.precio = form.precio.data
        programa.publico = form.publico.data
        programa.estado = form.estado.data
        programa.promocionado = form.promocionado.data

        if programa.publico is True and cuenta_cursos_por_programa(programa.codigo) == 0:
            flash("No se puede cambiar estatus de programa a publico porque no tiene cursos añadidos", "error")
            programa.publico = False

        if programa.estado == "open" and cuenta_cursos_por_programa(programa.codigo) == 0:
            flash("No se puede cambiar programa a abierto porque no tiene cursos añadidos", "error")
            programa.estado = "draft"

        try:
            database.session.add(programa)
            database.session.commit()
            if "logo" in request.files:
                try:
                    picture_file = images.save(request.files["logo"], folder="program" + programa.codigo, name="logo.jpg")
                    if picture_file:
                        programa.logo = True
                        flash("Portada del curso actualizada correctamente", "success")
                        database.session.commit()
                except UploadNotAllowed:  # pragma: no cover
                    flash("No se pudo actualizar la portada del curso.", "warning")

            flash("Programa editado correctamente.", "success")
        except OperationalError:  # pragma: no cover
            database.session.rollback()
            flash("No se puedo editar el programa.")
        return redirect(url_for(PROGRAMS_ROUTE))

    return render_template("learning/programas/editar_programa.html", form=form, programa=programa)


@program.route("/program/<codigo>/courses")
@login_required
@perfil_requerido("instructor")
def programa_cursos(codigo):
    """Pagina principal del curso."""

    if current_user.tipo == "admin":
        return render_template("learning/programas/lista_cursos.html")

    else:
        return abort(403)


@program.route("/program/<codigo>")
@cache.cached(timeout=60, unless=no_guardar_en_cache_global)
def pagina_programa(codigo):
    """Pagina principal del curso."""

    program = database.session.execute(database.select(Programa).filter(Programa.codigo == codigo)).scalars().first()

    return render_template(get_program_view_template(), programa=program, cuenta_cursos=cuenta_cursos_por_programa)


@program.route("/program/explore")
@cache.cached(unless=no_guardar_en_cache_global)
def lista_programas():
    """Lista de programas."""

    if DESARROLLO:
        MAX_COUNT = 3
    else:
        MAX_COUNT = 30

    etiquetas = database.session.execute(database.select(Etiqueta)).scalars().all()
    categorias = database.session.execute(database.select(Categoria)).scalars().all()
    consulta_cursos = database.paginate(
        database.select(Programa).filter(Programa.publico == True, Programa.estado == "open"),  # noqa: E712
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
            except KeyError:  # pragma: no cover
                pass
    else:
        PARAMETROS = None

    return render_template(
        get_program_list_template(),
        cursos=consulta_cursos,
        etiquetas=etiquetas,
        categorias=categorias,
        parametros=PARAMETROS,
    )
