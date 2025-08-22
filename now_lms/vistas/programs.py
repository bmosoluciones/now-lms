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
from datetime import datetime, timezone

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from flask_uploads import UploadNotAllowed
from sqlalchemy import delete
from sqlalchemy.exc import OperationalError

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms.auth import perfil_requerido
from now_lms.cache import cache, no_guardar_en_cache_global
from now_lms.config import DESARROLLO, DIRECTORIO_PLANTILLAS, images
from now_lms.db import (
    MAXIMO_RESULTADOS_EN_CONSULTA_PAGINADA,
    Categoria,
    CategoriaPrograma,
    CertificacionPrograma,
    Curso,
    Etiqueta,
    EtiquetaPrograma,
    Programa,
    ProgramaCurso,
    ProgramaEstudiante,
    database,
)
from now_lms.db.tools import (
    cuenta_cursos_por_programa,
    generate_category_choices,
    generate_tag_choices,
    generate_template_choices,
    get_program_category,
    get_program_tags,
    obtener_progreso_programa,
    verificar_programa_completo,
    verificar_usuario_inscrito_programa,
)
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
    form.plantilla_certificado.choices = generate_template_choices()
    form.categoria.choices = generate_category_choices()
    form.etiquetas.choices = generate_tag_choices()

    if form.validate_on_submit() or request.method == "POST":

        programa = Programa(
            nombre=form.nombre.data,
            descripcion=form.descripcion.data,
            codigo=form.codigo.data,
            precio=form.precio.data,
            publico=False,
            estado="draft",
            logo=False,
            certificado=form.certificado.data if form.certificado.data else False,
            plantilla_certificado=(
                form.plantilla_certificado.data if form.certificado.data and form.plantilla_certificado.data else None
            ),
            creado_por=current_user.id,
        )
        database.session.add(programa)
        try:
            database.session.commit()

            # Assign category if selected
            if form.categoria.data:
                categoria_programa = CategoriaPrograma(programa=programa.id, categoria=form.categoria.data)
                database.session.add(categoria_programa)

            # Assign tags if selected
            if form.etiquetas.data:
                for etiqueta_id in form.etiquetas.data:
                    etiqueta_programa = EtiquetaPrograma(programa=programa.id, etiqueta=etiqueta_id)
                    database.session.add(etiqueta_programa)

            database.session.commit()
            cache.delete("view/" + url_for(PROGRAMS_ROUTE))
            flash("Nuevo Programa creado.", "success")
            return redirect(url_for("program.pagina_programa", codigo=programa.codigo))
        except OperationalError:  # pragma: no cover
            database.session.rollback()
            flash("Hubo un error al crear el programa.", "warning")
            return redirect(url_for(PROGRAMS_ROUTE))

    return render_template("learning/programas/nuevo_programa.html", form=form)


@program.route("/program/list")
@login_required
@perfil_requerido("instructor")
@cache.cached(timeout=60)
def programas():
    """Lista de programas."""
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
    form.plantilla_certificado.choices = generate_template_choices()
    form.plantilla_certificado.data = programa.plantilla_certificado
    form.certificado.data = programa.certificado

    # Populate category and tag choices and current values
    form.categoria.choices = generate_category_choices()
    form.etiquetas.choices = generate_tag_choices()
    form.categoria.data = get_program_category(programa.id)
    form.etiquetas.data = get_program_tags(programa.id)

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
        programa.certificado = form.certificado.data
        programa.plantilla_certificado = form.plantilla_certificado.data

        if programa.publico is True and cuenta_cursos_por_programa(programa.codigo) == 0:
            flash("No se puede cambiar estatus de programa a publico porque no tiene cursos añadidos", "error")
            programa.publico = False

        if programa.estado == "open" and cuenta_cursos_por_programa(programa.codigo) == 0:
            flash("No se puede cambiar programa a abierto porque no tiene cursos añadidos", "error")
            programa.estado = "draft"

        try:
            database.session.add(programa)

            # Update category assignment
            # First remove existing category assignment
            database.session.execute(delete(CategoriaPrograma).where(CategoriaPrograma.programa == programa.id))

            # Add new category if selected
            if form.categoria.data:
                categoria_programa = CategoriaPrograma(programa=programa.id, categoria=form.categoria.data)
                database.session.add(categoria_programa)

            # Update tag assignments
            # First remove existing tag assignments
            database.session.execute(delete(EtiquetaPrograma).where(EtiquetaPrograma.programa == programa.id))

            # Add new tags if selected
            if form.etiquetas.data:
                for etiqueta_id in form.etiquetas.data:
                    etiqueta_programa = EtiquetaPrograma(programa=programa.id, etiqueta=etiqueta_id)
                    database.session.add(etiqueta_programa)

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

    # Start with base query
    query = database.select(Programa).filter(Programa.publico.is_(True), Programa.estado == "open")

    # Get filtering parameters
    tag_param = request.args.get("tag")
    category_param = request.args.get("category")

    # Apply tag filter
    if tag_param:
        # Find tag by name
        tag = database.session.execute(database.select(Etiqueta).filter(Etiqueta.nombre == tag_param)).scalars().first()
        if tag:
            # Join with EtiquetaPrograma to filter programs by tag
            query = query.join(EtiquetaPrograma, Programa.id == EtiquetaPrograma.programa).filter(
                EtiquetaPrograma.etiqueta == tag.id
            )

    # Apply category filter
    if category_param:
        # Find category by name
        categoria = (
            database.session.execute(database.select(Categoria).filter(Categoria.nombre == category_param)).scalars().first()
        )
        if categoria:
            # Join with CategoriaPrograma to filter programs by category
            query = query.join(CategoriaPrograma, Programa.id == CategoriaPrograma.programa).filter(
                CategoriaPrograma.categoria == categoria.id
            )

    # Paginate the filtered query
    consulta_cursos = database.paginate(
        query,
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


@program.route("/program/<codigo>/enroll", methods=["GET", "POST"])
@login_required
@perfil_requerido("student")
def inscribir_programa(codigo):
    """Inscribir usuario a un programa."""
    programa = database.session.execute(database.select(Programa).filter(Programa.codigo == codigo)).scalars().first()

    if not programa:
        abort(404)

    # Check if already enrolled
    if verificar_usuario_inscrito_programa(current_user.usuario, codigo):
        flash("Ya estás inscrito en este programa.", "info")
        return redirect(url_for("program.tomar_programa", codigo=codigo))

    if request.method == "POST":
        # Create enrollment
        inscripcion = ProgramaEstudiante(usuario=current_user.usuario, programa=programa.id, creado_por=current_user.usuario)

        try:
            database.session.add(inscripcion)
            database.session.commit()
            flash("Te has inscrito exitosamente al programa.", "success")
            return redirect(url_for("program.tomar_programa", codigo=codigo))
        except OperationalError:  # pragma: no cover
            database.session.rollback()
            flash("Hubo un error al inscribirte al programa.", "error")

    return render_template("learning/programas/inscribir_programa.html", programa=programa)


@program.route("/program/<codigo>/take")
@login_required
@perfil_requerido("student")
def tomar_programa(codigo):
    """Página para tomar un programa."""
    programa = database.session.execute(database.select(Programa).filter(Programa.codigo == codigo)).scalars().first()

    if not programa:
        abort(404)

    # Check if enrolled
    if not verificar_usuario_inscrito_programa(current_user.usuario, codigo):
        flash("Debes inscribirte al programa primero.", "warning")
        return redirect(url_for("program.inscribir_programa", codigo=codigo))

    # Get program progress
    progreso = obtener_progreso_programa(current_user.usuario, codigo)

    # Get courses in program
    cursos_programa = (
        database.session.execute(database.select(ProgramaCurso).filter(ProgramaCurso.programa == codigo)).scalars().all()
    )

    # Check if program is complete and issue certificate if needed
    if verificar_programa_completo(current_user.usuario, codigo) and programa.certificado:
        certificacion_existente = database.session.execute(
            database.select(CertificacionPrograma).filter(
                CertificacionPrograma.usuario == current_user.usuario, CertificacionPrograma.programa == programa.id
            )
        ).scalar_one_or_none()

        if not certificacion_existente and programa.plantilla_certificado:
            _emitir_certificado_programa(codigo, current_user.usuario, programa.plantilla_certificado)

    return render_template(
        "learning/programas/tomar_programa.html",
        programa=programa,
        progreso=progreso,
        cursos_programa=cursos_programa,
    )


@program.route("/program/<codigo>/courses/manage", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def gestionar_cursos_programa(codigo):
    """Gestionar cursos de un programa."""
    programa = database.session.execute(database.select(Programa).filter(Programa.codigo == codigo)).scalars().first()

    if not programa:
        abort(404)

    if current_user.tipo != "admin":
        abort(403)

    # Get current courses in program
    cursos_programa = (
        database.session.execute(database.select(ProgramaCurso).filter(ProgramaCurso.programa == codigo)).scalars().all()
    )

    # Get all available courses
    todos_cursos = database.session.execute(database.select(Curso)).scalars().all()

    if request.method == "POST":
        action = request.form.get("action")

        if action == "add_course":
            curso_codigo = request.form.get("curso_codigo")

            # Check if already exists
            existente = database.session.execute(
                database.select(ProgramaCurso).filter(ProgramaCurso.programa == codigo, ProgramaCurso.curso == curso_codigo)
            ).scalar_one_or_none()

            if not existente:
                nuevo_curso = ProgramaCurso(programa=codigo, curso=curso_codigo, creado_por=current_user.usuario)
                database.session.add(nuevo_curso)
                database.session.commit()
                flash(f"Curso {curso_codigo} agregado al programa.", "success")
            else:
                flash("El curso ya está en el programa.", "warning")

        elif action == "remove_course":
            curso_codigo = request.form.get("curso_codigo")

            curso_programa = database.session.execute(
                database.select(ProgramaCurso).filter(ProgramaCurso.programa == codigo, ProgramaCurso.curso == curso_codigo)
            ).scalar_one_or_none()

            if curso_programa:
                database.session.delete(curso_programa)
                database.session.commit()
                flash(f"Curso {curso_codigo} removido del programa.", "success")

        return redirect(url_for("program.gestionar_cursos_programa", codigo=codigo))

    return render_template(
        "learning/programas/gestionar_cursos.html",
        programa=programa,
        cursos_programa=cursos_programa,
        todos_cursos=todos_cursos,
    )


@program.route("/program/<codigo>/enroll_user", methods=["GET", "POST"])
@login_required
@perfil_requerido("admin")
def inscribir_usuario_programa(codigo):
    """Inscribir manualmente a un usuario en un programa (solo admin)."""
    programa = database.session.execute(database.select(Programa).filter(Programa.codigo == codigo)).scalars().first()

    if not programa:
        abort(404)

    if request.method == "POST":
        usuario_email = request.form.get("usuario_email")

        # Find user
        from now_lms.db import Usuario

        usuario = database.session.execute(
            database.select(Usuario).filter(Usuario.correo_electronico == usuario_email)
        ).scalar_one_or_none()

        if not usuario:
            flash("Usuario no encontrado.", "error")
        elif verificar_usuario_inscrito_programa(usuario.usuario, codigo):
            flash("El usuario ya está inscrito en este programa.", "warning")
        else:
            inscripcion = ProgramaEstudiante(usuario=usuario.usuario, programa=programa.id, creado_por=current_user.usuario)

            try:
                database.session.add(inscripcion)
                database.session.commit()
                flash(f"Usuario {usuario.nombre} {usuario.apellido} inscrito exitosamente.", "success")
            except OperationalError:  # pragma: no cover
                database.session.rollback()
                flash("Error al inscribir usuario.", "error")

        return redirect(url_for("program.inscribir_usuario_programa", codigo=codigo))

    return render_template("learning/programas/inscribir_usuario.html", programa=programa)


def _emitir_certificado_programa(codigo_programa, usuario, plantilla):
    """Emit a program certificate for a user."""
    # Get program by codigo to get its ID
    programa = database.session.execute(
        database.select(Programa).filter(Programa.codigo == codigo_programa)
    ).scalar_one_or_none()

    if not programa:
        flash("Programa no encontrado.", "error")
        return

    certificado = CertificacionPrograma(
        programa=programa.id,
        usuario=usuario,
        certificado=plantilla,
    )
    certificado.creado = datetime.now(timezone.utc).date()
    certificado.creado_por = current_user.usuario
    database.session.add(certificado)
    database.session.commit()
    flash("Certificado de programa emitido por completar todos los cursos.", "success")
