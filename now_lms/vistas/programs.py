# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.

"""
NOW Learning Management System.

Gestión de certificados.
"""

from __future__ import annotations

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
from werkzeug.wrappers import Response

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms.auth import perfil_requerido
from now_lms.cache import cache, cache_key_with_auth_state
from now_lms.config import DESARROLLO, DIRECTORIO_PLANTILLAS, images
from now_lms.db import (
    MAXIMO_RESULTADOS_EN_CONSULTA_PAGINADA,
    Categoria,
    CategoriaPrograma,
    CertificacionPrograma,
    Curso,
    EstudianteCurso,
    Etiqueta,
    EtiquetaPrograma,
    Pago,
    Programa,
    ProgramaCurso,
    ProgramaEstudiante,
    Usuario,
    database,
)
from now_lms.db.tools import (
    cuenta_cursos_por_programa,
    generate_category_choices,
    generate_tag_choices,
    generate_template_choices_program,
    get_program_category,
    get_program_tags,
    obtener_progreso_programa,
    verificar_programa_completo,
    verificar_usuario_inscrito_programa,
)
from now_lms.forms import AdminProgramEnrollmentForm, ProgramaForm
from now_lms.i18n import _
from now_lms.themes import get_program_list_template, get_program_view_template

# Constants
PROGRAMS_ROUTE = "program.programas"
ADMIN_PROGRAM_ENROLL_TEMPLATE = "learning/programas/admin_enroll.html"

# ---------------------------------------------------------------------------------------
# Interfaz de gestión de programas
# ---------------------------------------------------------------------------------------

program = Blueprint("program", __name__, template_folder=DIRECTORIO_PLANTILLAS)


def _program_explore_query(tag_param: str | None, category_param: str | None):
    """Build the filtered public program query."""
    query = database.select(Programa).filter(Programa.publico.is_(True), Programa.estado == "open")
    if tag_param:
        tag = database.session.execute(database.select(Etiqueta).filter(Etiqueta.nombre == tag_param)).scalars().first()
        if tag:
            query = query.join(EtiquetaPrograma, Programa.id == EtiquetaPrograma.programa).filter(
                EtiquetaPrograma.etiqueta == tag.id
            )
    if category_param:
        category = (
            database.session.execute(database.select(Categoria).filter(Categoria.nombre == category_param)).scalars().first()
        )
        if category:
            query = query.join(CategoriaPrograma, Programa.id == CategoriaPrograma.programa).filter(
                CategoriaPrograma.categoria == category.id
            )
    return query


def _program_explore_params(tag_param: str | None, category_param: str | None):
    """Build program pagination parameters without the page number."""
    if not any((request.args.get("nivel"), tag_param, category_param)):
        return None
    params = OrderedDict()
    for arg in request.url.split("?", 1)[-1].split("&"):
        if "=" in arg:
            key, value = arg.split("=", 1)
            if key != "page":
                params[key] = value
    return params


def _update_program_assignments(programa: Programa, form: ProgramaForm) -> None:
    """Replace the category and tag assignments for a program."""
    database.session.execute(delete(CategoriaPrograma).where(CategoriaPrograma.programa == programa.id))
    if form.categoria.data:
        database.session.add(CategoriaPrograma(programa=programa.id, categoria=form.categoria.data))
    database.session.execute(delete(EtiquetaPrograma).where(EtiquetaPrograma.programa == programa.id))
    for etiqueta_id in form.etiquetas.data or []:
        database.session.add(EtiquetaPrograma(programa=programa.id, etiqueta=etiqueta_id))


def _save_program_logo(programa: Programa) -> None:
    """Save a program logo when supplied."""
    if "logo" not in request.files:
        return
    try:
        if images.save(request.files["logo"], folder="program" + programa.codigo, name="logo.jpg"):
            programa.logo = True
            flash(_("Portada del curso actualizada correctamente"), "success")
            database.session.commit()
    except UploadNotAllowed:
        flash(_("No se pudo actualizar la portada del curso."), "warning")


def _create_program_from_form(form: ProgramaForm) -> Programa:
    """Create a program and its selected taxonomy records."""
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
        creado_por=current_user.usuario,
    )
    database.session.add(programa)
    database.session.commit()
    _update_program_assignments(programa, form)
    database.session.commit()
    return programa


@program.route("/program/new", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def nuevo_programa() -> str | Response:
    """Nueva programa."""
    form = ProgramaForm()
    form.plantilla_certificado.choices = generate_template_choices_program()
    form.categoria.choices = generate_category_choices()
    form.etiquetas.choices = generate_tag_choices()

    if form.validate_on_submit() or request.method == "POST":
        try:
            programa = _create_program_from_form(form)
            cache.delete("view/" + url_for(PROGRAMS_ROUTE))
            flash(_("Nuevo Programa creado."), "success")
            return redirect(url_for("program.pagina_programa", codigo=programa.codigo))
        except OperationalError:
            database.session.rollback()
            flash(_("Hubo un error al crear el programa."), "warning")
            return redirect(url_for(PROGRAMS_ROUTE))

    return render_template("learning/programas/nuevo_programa.html", form=form)


@program.route("/program/list", methods=["GET"])
@login_required
@perfil_requerido("instructor")
@cache.cached(timeout=60)
def programas() -> str:
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
            database.select(Programa).filter(Programa.creado_por == current_user.usuario),  # noqa: E712
            page=request.args.get("page", default=1, type=int),
            max_per_page=MAXIMO_RESULTADOS_EN_CONSULTA_PAGINADA,
            count=True,
        )

    return render_template("learning/programas/lista_programas.html", consulta=consulta)


@program.route("/program/<ulid>/delete", methods=["POST"])
@login_required
@perfil_requerido("instructor")
def delete_program(ulid: str) -> Response:
    """Elimina programa."""
    if current_user.tipo != "admin":
        abort(403)

    database.session.execute(delete(Programa).where(Programa.id == ulid))
    database.session.commit()
    cache.delete("view/" + url_for(PROGRAMS_ROUTE))
    return redirect(url_for(PROGRAMS_ROUTE))


@program.route("/program/<ulid>/edit", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def edit_program(ulid: str) -> str | Response:
    """Editar programa."""
    programa = database.session.execute(database.select(Programa).filter(Programa.id == ulid)).scalars().first()
    if programa is None:
        abort(404)

    form = ProgramaForm(
        nombre=programa.nombre,
        descripcion=programa.descripcion,
        codigo=programa.codigo,
        precio=programa.precio,
        estado=programa.estado,
        promocionado=programa.promocionado,
        plantilla_certificado=programa.plantilla_certificado,
    )
    form.plantilla_certificado.choices = generate_template_choices_program()
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
            flash(_("No se puede cambiar estatus de programa a publico porque no tiene cursos añadidos"), "error")
            programa.publico = False

        if programa.estado == "open" and cuenta_cursos_por_programa(programa.codigo) == 0:
            flash(_("No se puede cambiar programa a abierto porque no tiene cursos añadidos"), "error")
            programa.estado = "draft"

        try:
            database.session.add(programa)

            _update_program_assignments(programa, form)

            database.session.commit()
            _save_program_logo(programa)

            flash(_("Programa editado correctamente."), "success")
        except OperationalError:
            database.session.rollback()
            flash(_("No se puedo editar el programa."))
        return redirect(url_for(PROGRAMS_ROUTE))

    return render_template("learning/programas/editar_programa.html", form=form, programa=programa)


@program.route("/program/<codigo>/courses", methods=["GET"])
@login_required
@perfil_requerido("instructor")
def programa_cursos(codigo: str) -> str | Response:
    """Pagina principal del curso."""
    if current_user.tipo == "admin":
        return render_template("learning/programas/lista_cursos.html")

    return abort(403)


@program.route("/program/<codigo>", methods=["GET"])
@cache.cached(timeout=60, key_prefix=cache_key_with_auth_state)  # type: ignore[arg-type]
def pagina_programa(codigo: str) -> str:
    """Pagina principal del curso."""
    programa_obj = database.session.execute(database.select(Programa).filter(Programa.codigo == codigo)).scalars().first()

    return render_template(get_program_view_template(), programa=programa_obj, cuenta_cursos=cuenta_cursos_por_programa)


@program.route("/program/explore", methods=["GET"])
@cache.cached(key_prefix=cache_key_with_auth_state)  # type: ignore[arg-type]
def lista_programas() -> str:
    """Lista de programas."""
    max_count = 3 if DESARROLLO else 30

    etiquetas = database.session.execute(database.select(Etiqueta)).scalars().all()
    categorias = database.session.execute(database.select(Categoria)).scalars().all()

    tag_param = request.args.get("tag")
    category_param = request.args.get("category")
    query = _program_explore_query(tag_param, category_param)

    # Paginate the filtered query
    consulta_cursos = database.paginate(
        query,
        page=request.args.get("page", default=1, type=int),
        max_per_page=max_count,
        count=True,
    )

    parametros = _program_explore_params(tag_param, category_param)

    return render_template(
        get_program_list_template(),
        cursos=consulta_cursos,
        etiquetas=etiquetas,
        categorias=categorias,
        parametros=parametros,
    )


def inscribir_usuario_en_cursos_de_programa(username: str, programa: Programa) -> list[str]:
    """Enroll a user in all courses of a program. Returns list of enrolled course codes."""
    from now_lms.calendar_utils import create_events_for_student_enrollment
    from now_lms.vistas.courses import _crear_indice_avance_curso
    from now_lms.vistas.paypal import get_site_currency

    program_courses = (
        database.session.execute(database.select(ProgramaCurso).filter_by(programa=programa.codigo)).scalars().all()
    )

    enrolled = []
    for pc in program_courses:
        # Check if already enrolled in this course
        existing = database.session.execute(
            database.select(EstudianteCurso).filter_by(curso=pc.curso, usuario=username, vigente=True)
        ).scalar_one_or_none()
        if existing:
            continue

        # Create Pago
        curso = database.session.execute(database.select(Curso).filter_by(codigo=pc.curso)).scalar_one_or_none()
        if not curso:
            continue

        pago = Pago()
        pago.usuario = username
        pago.curso = pc.curso
        pago.estado = "completed"
        pago.metodo = "program_enrollment"
        pago.monto = 0
        pago.moneda = get_site_currency()
        pago.descripcion = f"Inscripción al curso como parte del programa '{programa.nombre}'"
        pago.audit = False
        pago.creado = datetime.now(timezone.utc).date()
        pago.creado_por = current_user.usuario if (current_user and current_user.is_authenticated) else username

        usuario_obj = database.session.execute(database.select(Usuario).filter_by(usuario=username)).scalar_one_or_none()
        if usuario_obj:
            pago.nombre = usuario_obj.nombre or username
            pago.apellido = usuario_obj.apellido or ""
            pago.correo_electronico = usuario_obj.correo_electronico or ""
        else:
            pago.nombre = username
            pago.apellido = ""
            pago.correo_electronico = ""

        database.session.add(pago)
        database.session.flush()

        course_enrollment = EstudianteCurso(
            curso=pc.curso,
            usuario=username,
            vigente=True,
            pago=pago.id,
            creado=datetime.now(timezone.utc).date(),
            creado_por=current_user.usuario if (current_user and current_user.is_authenticated) else username,
        )
        database.session.add(course_enrollment)
        enrolled.append(pc.curso)

    if enrolled:
        for course_code in enrolled:
            _crear_indice_avance_curso(course_code)
            create_events_for_student_enrollment(username, course_code)

    return enrolled


def inscribir_usuario_en_curso_especifico_de_programa(username: str, course_code: str, programa: Programa) -> bool:
    """Enrolls a single user in a single course of a program."""
    from now_lms.calendar_utils import create_events_for_student_enrollment
    from now_lms.vistas.courses import _crear_indice_avance_curso
    from now_lms.vistas.paypal import get_site_currency

    existing = database.session.execute(
        database.select(EstudianteCurso).filter_by(curso=course_code, usuario=username, vigente=True)
    ).scalar_one_or_none()
    if existing:
        return False

    curso = database.session.execute(database.select(Curso).filter_by(codigo=course_code)).scalar_one_or_none()
    if not curso:
        return False

    pago = Pago()
    pago.usuario = username
    pago.curso = course_code
    pago.estado = "completed"
    pago.metodo = "program_enrollment"
    pago.monto = 0
    pago.moneda = get_site_currency()
    pago.descripcion = f"Inscripción al curso como parte del programa '{programa.nombre}'"
    pago.audit = False
    pago.creado = datetime.now(timezone.utc).date()
    pago.creado_por = current_user.usuario if (current_user and current_user.is_authenticated) else "system"

    usuario_obj = database.session.execute(database.select(Usuario).filter_by(usuario=username)).scalar_one_or_none()
    if usuario_obj:
        pago.nombre = usuario_obj.nombre or username
        pago.apellido = usuario_obj.apellido or ""
        pago.correo_electronico = usuario_obj.correo_electronico or ""
    else:
        pago.nombre = username
        pago.apellido = ""
        pago.correo_electronico = ""

    database.session.add(pago)
    database.session.flush()

    course_enrollment = EstudianteCurso(
        curso=course_code,
        usuario=username,
        vigente=True,
        pago=pago.id,
        creado=datetime.now(timezone.utc).date(),
        creado_por=current_user.usuario if (current_user and current_user.is_authenticated) else "system",
    )
    database.session.add(course_enrollment)
    _crear_indice_avance_curso(course_code)
    create_events_for_student_enrollment(username, course_code)
    return True


@program.route("/program/<codigo>/enroll", methods=["GET", "POST"])
@login_required
@perfil_requerido("student")
def inscribir_programa(codigo: str) -> str | Response:
    """Inscribir usuario a un programa."""
    print("DEBUG INSCRIBIR PROGRAMA: method:", request.method, "user:", current_user.usuario if current_user else None)
    programa = database.session.execute(database.select(Programa).filter(Programa.codigo == codigo)).scalars().first()

    if not programa:
        abort(404)

    # Check if already enrolled
    if verificar_usuario_inscrito_programa(current_user.usuario, codigo):
        flash(_("Ya estás inscrito en este programa."), "info")
        return redirect(url_for("program.tomar_programa", codigo=codigo))

    if request.method == "POST":
        if programa.precio and programa.precio > 0:
            # Check if already has a pending payment for this program
            existing_pago = (
                database.session.execute(
                    database.select(Pago).filter_by(usuario=current_user.usuario, programa=programa.id, estado="pending")
                )
                .scalars()
                .first()
            )

            if existing_pago:
                return redirect(url_for("program.program_payment", codigo=codigo, payment_id=existing_pago.id))

            # Create a pending payment
            from now_lms.vistas.paypal import get_site_currency

            pago = Pago()
            pago.usuario = current_user.usuario
            pago.programa = programa.id
            pago.curso = None
            pago.moneda = get_site_currency()
            pago.monto = programa.precio
            pago.estado = "pending"
            pago.metodo = "paypal"
            pago.nombre = current_user.nombre or current_user.usuario
            pago.apellido = current_user.apellido or ""
            pago.correo_electronico = current_user.correo_electronico or ""
            pago.descripcion = f"Pago del programa '{programa.nombre}'"
            pago.audit = False
            pago.creado = datetime.now(timezone.utc).date()
            pago.creado_por = current_user.usuario

            try:
                database.session.add(pago)
                database.session.commit()
                return redirect(url_for("program.program_payment", codigo=codigo, payment_id=pago.id))
            except Exception:
                import traceback

                traceback.print_exc()
                database.session.rollback()
                flash(_("Error al procesar la inscripción al programa."), "error")
                return redirect(url_for("program.inscribir_programa", codigo=codigo))

        # Create enrollment for free program
        inscripcion = ProgramaEstudiante(usuario=current_user.usuario, programa=programa.id, creado_por=current_user.usuario)

        try:
            database.session.add(inscripcion)
            inscribir_usuario_en_cursos_de_programa(current_user.usuario, programa)
            database.session.commit()
            print("PE IN THE VIEW:", database.session.execute(database.select(ProgramaEstudiante)).scalars().all())
            flash(_("Te has inscrito exitosamente al programa."), "success")
            return redirect(url_for("program.tomar_programa", codigo=codigo))
        except OperationalError:
            database.session.rollback()
            flash(_("Hubo un error al inscribirte al programa."), "error")

    return render_template("learning/programas/inscribir_programa.html", programa=programa)


@program.route("/program/<codigo>/payment", methods=["GET"])
@login_required
@perfil_requerido("student")
def program_payment(codigo: str) -> str | Response:
    """Página de pago con PayPal para un programa."""
    payment_id = request.args.get("payment_id")
    pago = None
    if payment_id:
        pago = (
            database.session.execute(database.select(Pago).filter_by(id=payment_id, usuario=current_user.usuario))
            .scalars()
            .first()
        )

    programa = database.session.execute(database.select(Programa).filter_by(codigo=codigo)).scalars().first()
    if not programa:
        flash(_("Programa no encontrado."), "error")
        return redirect(url_for("program.lista_programas"))

    if not (programa.precio and programa.precio > 0):
        flash(_("Este programa es gratuito."), "info")
        return redirect(url_for("program.tomar_programa", codigo=codigo))

    # Check if PayPal is enabled
    from now_lms.vistas.paypal import check_paypal_enabled, get_site_currency

    if not check_paypal_enabled():
        flash(_("Los pagos con PayPal no están habilitados."), "error")
        return redirect(url_for("program.tomar_programa", codigo=codigo))

    site_currency = get_site_currency()

    from flask_wtf.csrf import generate_csrf

    return render_template(
        "learning/programas/program_payment.html",
        programa=programa,
        site_currency=site_currency,
        pago=pago,
        csrf_token=generate_csrf(),
    )


@program.route("/program/<codigo>/take", methods=["GET"])
@login_required
@perfil_requerido("student")
def tomar_programa(codigo: str) -> str | Response:
    """Página para tomar un programa."""
    programa = database.session.execute(database.select(Programa).filter(Programa.codigo == codigo)).scalars().first()

    if not programa:
        abort(404)

    # Check if enrolled
    if not verificar_usuario_inscrito_programa(current_user.usuario, codigo):
        flash(_("Debes inscribirte al programa primero."), "warning")
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
def gestionar_cursos_programa(codigo: str) -> str | Response:
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
            if not curso_codigo:
                flash(_("Seleccione un curso."), "warning")
                return redirect(url_for("program.gestionar_cursos_programa", codigo=codigo))

            # Check if already exists
            existente = database.session.execute(
                database.select(ProgramaCurso).filter(ProgramaCurso.programa == codigo, ProgramaCurso.curso == curso_codigo)
            ).scalar_one_or_none()

            if not existente:
                nuevo_curso = ProgramaCurso(programa=codigo, curso=curso_codigo, creado_por=current_user.usuario)
                database.session.add(nuevo_curso)

                # Enroll all students currently in the program in this new course
                estudiantes = (
                    database.session.execute(database.select(ProgramaEstudiante).filter_by(programa=programa.id))
                    .scalars()
                    .all()
                )
                for est in estudiantes:
                    inscribir_usuario_en_curso_especifico_de_programa(est.usuario, curso_codigo, programa)

                database.session.commit()
                flash(f"Curso {curso_codigo} agregado al programa.", "success")
            else:
                flash(_("El curso ya está en el programa."), "warning")

        elif action == "remove_course":
            curso_codigo = request.form.get("curso_codigo")

            curso_programa = database.session.execute(
                database.select(ProgramaCurso).filter(ProgramaCurso.programa == codigo, ProgramaCurso.curso == curso_codigo)
            ).scalar_one_or_none()

            if curso_programa:
                # Unenroll all students currently in the program from this course
                estudiantes = (
                    database.session.execute(database.select(ProgramaEstudiante).filter_by(programa=programa.id))
                    .scalars()
                    .all()
                )
                for est in estudiantes:
                    enrollment = database.session.execute(
                        database.select(EstudianteCurso).filter_by(curso=curso_codigo, usuario=est.usuario, vigente=True)
                    ).scalar_one_or_none()
                    if enrollment:
                        enrollment.vigente = False
                        enrollment.modificado = datetime.now(timezone.utc).date()
                        enrollment.modificado_por = current_user.usuario

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
def inscribir_usuario_programa(codigo: str) -> str | Response:
    """Inscribir manualmente a un usuario en un programa (solo admin)."""
    programa = database.session.execute(database.select(Programa).filter(Programa.codigo == codigo)).scalars().first()

    if not programa:
        abort(404)

    if request.method == "POST":
        usuario_email = request.form.get("usuario_email")

        # Find user
        usuario = database.session.execute(
            database.select(Usuario).filter(Usuario.correo_electronico == usuario_email)
        ).scalar_one_or_none()

        if not usuario:
            flash(_("Usuario no encontrado."), "error")
        elif verificar_usuario_inscrito_programa(usuario.usuario, codigo):
            flash(_("El usuario ya está inscrito en este programa."), "warning")
        else:
            inscripcion = ProgramaEstudiante(usuario=usuario.usuario, programa=programa.id, creado_por=current_user.usuario)

            try:
                database.session.add(inscripcion)
                database.session.commit()
                flash(f"Usuario {usuario.nombre} {usuario.apellido} inscrito exitosamente.", "success")
            except OperationalError:
                database.session.rollback()
                flash(_("Error al inscribir usuario."), "error")

        return redirect(url_for("program.inscribir_usuario_programa", codigo=codigo))

    return render_template("learning/programas/inscribir_usuario.html", programa=programa)


def _emitir_certificado_programa(codigo_programa: str, usuario: str, plantilla: str) -> None:
    """Emit a program certificate for a user."""
    # Get program by codigo to get its ID
    programa = database.session.execute(
        database.select(Programa).filter(Programa.codigo == codigo_programa)
    ).scalar_one_or_none()

    if not programa:
        try:
            flash(_("Programa no encontrado."), "error")
        except RuntimeError:
            pass
        return

    import json

    # Generate snapshot of courses currently in the program
    snapshot_dict = {}
    program_courses = (
        database.session.execute(database.select(ProgramaCurso).filter_by(programa=programa.codigo)).scalars().all()
    )
    for pc in program_courses:
        c = database.session.execute(database.select(Curso).filter_by(codigo=pc.curso)).scalar_one_or_none()
        if c:
            snapshot_dict[c.codigo] = c.nombre
        else:
            snapshot_dict[pc.curso] = pc.curso

    certificado = CertificacionPrograma(
        programa=programa.id,
        usuario=usuario,
        certificado=plantilla,
        cursos_snapshot=json.dumps(snapshot_dict),
    )
    certificado.creado = datetime.now(timezone.utc).date()
    certificado.creado_por = current_user.usuario if (current_user and current_user.is_authenticated) else usuario
    database.session.add(certificado)
    database.session.commit()
    try:
        flash(_("Certificado de programa emitido por completar todos los cursos."), "success")
    except RuntimeError:
        pass


# ---------------------------------------------------------------------------------------
# Administrative Program Enrollment Routes
# ---------------------------------------------------------------------------------------


def _verify_program_and_admin(codigo: str) -> Programa:
    """Verify program exists and current user is admin. Returns Programa or aborts."""
    programa = database.session.execute(database.select(Programa).filter(Programa.codigo == codigo)).scalar_one_or_none()
    if not programa:
        abort(404)
    if current_user.tipo != "admin":
        abort(403)
    return programa


def _verify_student_and_enrollment(student_username: str) -> dict | None:
    """Verify student exists and is not already enrolled in the program. Returns None if ok, else render_template call."""
    usuario_existe = database.session.execute(
        database.select(Usuario).filter_by(usuario=student_username)
    ).scalar_one_or_none()
    if not usuario_existe:
        return {"msg": f"El usuario '{student_username}' no existe en el sistema.", "cat": "error"}
    return None


def _get_or_create_course_enrollment(course_code, student_username, bypass_payment, notes, programa):
    """Enroll a student into a single course of the program if not already enrolled. Returns course_code if enrolled."""
    existing_course_enrollment = database.session.execute(
        database.select(EstudianteCurso).filter_by(curso=course_code, usuario=student_username, vigente=True)
    ).scalar_one_or_none()

    if existing_course_enrollment:
        return None

    curso = database.session.execute(database.select(Curso).filter_by(codigo=course_code)).scalar_one_or_none()
    if not curso:
        return None

    pago = Pago()
    pago.usuario = student_username
    pago.curso = course_code
    pago.estado = "completed"
    pago.metodo = "admin_program_enrollment"
    pago.monto = 0 if bypass_payment else curso.precio
    pago.descripcion = f"Inscripción administrativa al programa '{programa.nombre}' por {current_user.usuario}"
    if notes:
        pago.descripcion += f" - Notas: {notes}"
    pago.audit = not bypass_payment and curso.pagado
    pago.creado = datetime.now(timezone.utc).date()
    pago.creado_por = current_user.usuario
    database.session.add(pago)
    database.session.flush()

    course_enrollment = EstudianteCurso(
        curso=course_code,
        usuario=student_username,
        vigente=True,
        pago=pago.id,
        creado=datetime.now(timezone.utc).date(),
        creado_por=current_user.usuario,
    )
    database.session.add(course_enrollment)

    return course_code


def _post_enrollment_processing(student_username, enrolled_courses, programa):
    """Create progress indices and calendar events for enrolled courses."""
    from now_lms.calendar_utils import create_events_for_student_enrollment
    from now_lms.vistas.courses import _crear_indice_avance_curso

    for course_code in enrolled_courses:
        _crear_indice_avance_curso(course_code)
        create_events_for_student_enrollment(student_username, course_code)

    message = f"Estudiante '{student_username}' inscrito exitosamente en el programa '{programa.nombre}'"
    if enrolled_courses:
        message += f" y en {len(enrolled_courses)} curso(s)."
    else:
        message += ". El estudiante ya estaba inscrito en todos los cursos del programa."

    return message


@program.route("/program/<codigo>/admin/enroll", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def admin_program_enrollment(codigo: str) -> str | Response:
    """Administrative enrollment of students to a program and all its courses."""
    programa = _verify_program_and_admin(codigo)

    form = AdminProgramEnrollmentForm()

    if not form.validate_on_submit():
        return render_template(ADMIN_PROGRAM_ENROLL_TEMPLATE, programa=programa, form=form)

    student_username = form.student_username.data.strip()
    bypass_payment = form.bypass_payment.data
    notes = form.notes.data.strip() if form.notes.data else ""

    # Verify student
    err = _verify_student_and_enrollment(student_username)
    if err:
        flash(err["msg"], err["cat"])
        return render_template(ADMIN_PROGRAM_ENROLL_TEMPLATE, programa=programa, form=form)

    # Check if student is already enrolled in program
    existing_enrollment = database.session.execute(
        database.select(ProgramaEstudiante).filter_by(programa=programa.id, usuario=student_username)
    ).scalar_one_or_none()
    if existing_enrollment:
        flash(f"El estudiante '{student_username}' ya está inscrito en este programa.", "warning")
        return render_template(ADMIN_PROGRAM_ENROLL_TEMPLATE, programa=programa, form=form)

    try:
        # Get all courses in the program
        program_courses = (
            database.session.execute(database.select(ProgramaCurso).filter_by(programa=programa.codigo)).scalars().all()
        )

        # Enroll student in program
        program_enrollment = ProgramaEstudiante(
            usuario=student_username,
            programa=programa.id,
            creado=datetime.now(timezone.utc).date(),
            creado_por=current_user.usuario,
        )
        database.session.add(program_enrollment)

        # Enroll student in all courses of the program
        enrolled_courses = [
            cid
            for cid in (
                _get_or_create_course_enrollment(c.curso, student_username, bypass_payment, notes, programa)
                for c in program_courses
            )
            if cid is not None
        ]

        database.session.commit()

        message = _post_enrollment_processing(student_username, enrolled_courses, programa)
        flash(message, "success")
        return redirect(url_for("program.programa_cursos", codigo=codigo))

    except Exception:
        database.session.rollback()
        flash("Error al inscribir al estudiante en el programa.", "error")

    return render_template(ADMIN_PROGRAM_ENROLL_TEMPLATE, programa=programa, form=form)


@program.route("/program/<codigo>/admin/enrollments", methods=["GET"])
@login_required
@perfil_requerido("instructor")
def admin_program_enrollments(codigo: str) -> str:
    """View and manage program enrollments."""
    # Verify program exists
    programa = database.session.execute(database.select(Programa).filter(Programa.codigo == codigo)).scalar_one_or_none()
    if not programa:
        abort(404)

    # Only admins can view program enrollments
    if current_user.tipo != "admin":
        abort(403)

    # Get all enrollments for this program
    enrollments = database.session.execute(
        database.select(ProgramaEstudiante, Usuario)
        .join(Usuario, ProgramaEstudiante.usuario == Usuario.usuario)
        .filter(ProgramaEstudiante.programa == programa.id)
        .order_by(ProgramaEstudiante.creado.desc())
    ).all()

    return render_template("learning/programas/admin_enrollments.html", programa=programa, enrollments=enrollments)


@program.route("/program/<codigo>/admin/unenroll/<student_username>", methods=["POST"])
@login_required
@perfil_requerido("instructor")
def admin_program_unenrollment(codigo: str, student_username: str) -> Response:
    """Administrative unenrollment of a student from a program and all its courses."""
    # Verify program exists
    programa = database.session.execute(database.select(Programa).filter(Programa.codigo == codigo)).scalar_one_or_none()
    if not programa:
        abort(404)

    # Only admins can unenroll from programs
    if current_user.tipo != "admin":
        abort(403)

    # Find the program enrollment
    program_enrollment = database.session.execute(
        database.select(ProgramaEstudiante).filter_by(programa=programa.id, usuario=student_username)
    ).scalar_one_or_none()

    if not program_enrollment:
        flash(f"El estudiante '{student_username}' no está inscrito en este programa.", "error")
        return redirect(url_for("program.admin_program_enrollments", codigo=codigo))

    try:
        # Get all courses in the program by querying ProgramaCurso
        program_courses = (
            database.session.execute(database.select(ProgramaCurso).filter_by(programa=programa.codigo)).scalars().all()
        )

        # Unenroll from all courses in the program (mark as inactive)
        unenrolled_courses = []
        for course_data in program_courses:
            course_code = course_data.curso
            course_enrollment = database.session.execute(
                database.select(EstudianteCurso).filter_by(curso=course_code, usuario=student_username, vigente=True)
            ).scalar_one_or_none()

            if course_enrollment:
                course_enrollment.vigente = False
                course_enrollment.modificado = datetime.now(timezone.utc).date()
                course_enrollment.modificado_por = current_user.usuario
                unenrolled_courses.append(course_code)

        # Remove program enrollment
        database.session.delete(program_enrollment)
        database.session.commit()

        message = f"Estudiante '{student_username}' desinscrito del programa '{programa.nombre}'"
        if unenrolled_courses:
            message += f" y de {len(unenrolled_courses)} curso(s)."
        else:
            message += "."

        flash(message, "success")

    except Exception as e:
        database.session.rollback()
        flash(f"Error al desinscribir al estudiante del programa: {str(e)}", "error")

    return redirect(url_for("program.admin_program_enrollments", codigo=codigo))
