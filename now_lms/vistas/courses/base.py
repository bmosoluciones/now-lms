# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""
NOW Learning Management System.

Gestión de certificados.
"""

from __future__ import annotations
from flask_babel import gettext

# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------
from collections import OrderedDict
from datetime import datetime, timezone
from os.path import splitext

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------
from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required
from flask_uploads import UploadNotAllowed
from sqlalchemy import delete, func
from sqlalchemy.exc import OperationalError
from werkzeug.wrappers import Response

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms.auth import perfil_requerido
from now_lms.bi import (
    asignar_curso_a_instructor,
)
from now_lms.cache import cache, cache_key_with_auth_state
from now_lms.calendar_utils import create_events_for_student_enrollment
from now_lms.config import DESARROLLO, DIRECTORIO_PLANTILLAS, images
from now_lms.db import (
    Categoria,
    CategoriaCurso,
    Curso,
    CursoRecurso,
    CursoRecursoDescargable,
    CursoSeccion,
    DocenteCurso,
    EstudianteCurso,
    Etiqueta,
    EtiquetaCurso,
    Pago,
    Recurso,
    Usuario,
    database,
    select,
)
from now_lms.db.tools import (
    generate_category_choices,
    generate_tag_choices,
    generate_template_choices,
    get_course_category,
    get_course_tags,
)
from now_lms.forms import (
    CurseForm,
    CursoSeccionForm,
)
from now_lms.i18n import _
from now_lms.logs import log
from now_lms.misc import CURSO_NIVEL, TIPOS_RECURSOS
from now_lms.themes import get_course_list_template, get_course_view_template
from now_lms.vistas.courses.helpers import markdown2html, _crear_indice_avance_curso

# ---------------------------------------------------------------------------------------
# Gestión de cursos.
# ---------------------------------------------------------------------------------------
RECURSO_AGREGADO = "Recurso agregado correctamente al curso."
ERROR_AL_AGREGAR_CURSO = "Hubo en error al crear el recurso."

VISTA_CURSOS = "course.curso"
VISTA_ADMINISTRAR_CURSO = "course.administrar_curso"
COULD_NOT_UPDATE_PROFILE_PHOTO = "Could not update profile photo."
NO_AUTORIZADO_MSG = "No se encuentra autorizado a acceder al recurso solicitado."

# ---------------------------------------------------------------------------------------
# Template constants
# ---------------------------------------------------------------------------------------
TEMPLATE_SLIDE_SHOW = "learning/resources/slide_show.html"
TEMPLATE_COUPON_CREATE = "learning/curso/coupons/create.html"
TEMPLATE_COUPON_EDIT = "learning/curso/coupons/edit.html"
TEMPLATE_ADMIN_ENROLL = "learning/curso/admin_enroll.html"

# Route constants
ROUTE_LIST_COUPONS = "course.list_coupons"


# Helper functions moved to now_lms.vistas.courses.helpers


def _public_course_access(_curso) -> tuple[bool, bool]:
    """Return access for a public course."""
    if _curso and _curso.publico:
        return _curso.estado == "open", False
    return False, False


def _check_course_access(_curso, course_code: str) -> tuple[bool, bool]:
    """Check if the current user has access to the course.

    Returns:
        Tuple of (acceso, editable).
    """
    if course_code == "lms-training" and current_user.is_authenticated:
        if current_user.tipo in ("admin", "instructor"):
            return True, current_user.tipo == "admin"
        return False, False

    if current_user.is_authenticated and request.args.get("inspect"):
        if current_user.tipo == "admin":
            return True, True
        docente = (
            database.session.execute(
                database.select(DocenteCurso).filter(
                    DocenteCurso.curso == course_code, DocenteCurso.usuario == current_user.usuario
                )
            )
            .scalars()
            .first()
        )
        return bool(docente), bool(docente)

    if current_user.is_authenticated:
        enrollment = (
            database.session.execute(
                database.select(EstudianteCurso).filter_by(curso=course_code, usuario=current_user.usuario, vigente=True)
            )
            .scalars()
            .first()
        )
        if enrollment:
            return True, False
        return (True, False) if enrollment else _public_course_access(_curso)

    return _public_course_access(_curso)


def _save_course_logo(curso_) -> None:
    """Save uploaded logo for a course."""
    if "logo" not in request.files:
        return
    logo = request.files["logo"]
    logo_data = splitext(logo.filename or "")
    logo_ext = logo_data[1] or ""
    try:
        log.trace("Saving logo")
        picture_file = images.save(logo, folder=curso_.codigo, name=f"logo{logo_ext}")
        if picture_file:
            curso_.portada = True
            curso_.portada_ext = logo_ext
            database.session.commit()
            log.info("Course Logo saved")
        else:
            curso_.portada = False
            database.session.commit()
            log.warning("Course Logo not saved")
    except (UploadNotAllowed, AttributeError):
        log.warning(COULD_NOT_UPDATE_PROFILE_PHOTO)
        database.session.rollback()


def _course_explore_query(nivel_param: str | None, tag_param: str | None, category_param: str | None):
    """Build the filtered public course query."""
    query = database.select(Curso).filter(Curso.publico.is_(True), Curso.estado == "open")
    if nivel_param is not None:
        try:
            query = query.filter(Curso.nivel == int(nivel_param))
        except ValueError:
            pass
    if tag_param:
        tag = database.session.execute(select(Etiqueta).filter(Etiqueta.nombre == tag_param)).scalars().first()
        if tag:
            query = query.join(EtiquetaCurso, Curso.codigo == EtiquetaCurso.curso).filter(EtiquetaCurso.etiqueta == tag.id)
    if category_param:
        category = database.session.execute(select(Categoria).filter(Categoria.nombre == category_param)).scalars().first()
        if category:
            query = query.join(CategoriaCurso, Curso.codigo == CategoriaCurso.curso).filter(
                CategoriaCurso.categoria == category.id
            )
    return query


def _course_explore_params(nivel_param: str | None, tag_param: str | None, category_param: str | None):
    """Build pagination URL parameters without the page number."""
    if not any((nivel_param, tag_param, category_param)):
        return None
    params = OrderedDict()
    for arg in request.url.split("?", 1)[-1].split("&"):
        if "=" in arg:
            key, value = arg.split("=", 1)
            if key != "page":
                params[key] = value
    return params


def _update_course_fields(curso_a_editar, form) -> None:
    """Update course fields from form data."""
    curso_a_editar.nombre = form.nombre.data
    curso_a_editar.codigo = form.codigo.data
    curso_a_editar.descripcion_corta = form.descripcion_corta.data
    curso_a_editar.descripcion = form.descripcion.data
    curso_a_editar.nivel = form.nivel.data
    curso_a_editar.duracion = form.duracion.data
    curso_a_editar.publico = form.publico.data
    curso_a_editar.modalidad = form.modalidad.data
    curso_a_editar.foro_habilitado = False if form.modalidad.data == "self_paced" else form.foro_habilitado.data
    curso_a_editar.limitado = form.limitado.data
    curso_a_editar.capacidad = form.capacidad.data
    curso_a_editar.fecha_inicio = form.fecha_inicio.data
    curso_a_editar.fecha_fin = form.fecha_fin.data
    curso_a_editar.pagado = form.pagado.data
    curso_a_editar.auditable = form.auditable.data
    curso_a_editar.certificado = form.certificado.data
    curso_a_editar.plantilla_certificado = form.plantilla_certificado.data
    curso_a_editar.precio = form.precio.data
    if curso_a_editar.promocionado is False and form.promocionado.data is True:
        curso_a_editar.fecha_promocionado = datetime.today()
    curso_a_editar.promocionado = form.promocionado.data
    curso_a_editar.modificado_por = current_user.usuario


def _update_course_taxonomy(original_code: str, new_code: str, form) -> None:
    """Update course category and tag assignments."""
    database.session.execute(delete(CategoriaCurso).where(CategoriaCurso.curso == original_code))
    if form.categoria.data:
        database.session.add(CategoriaCurso(curso=new_code, categoria=form.categoria.data))
    database.session.execute(delete(EtiquetaCurso).where(EtiquetaCurso.curso == original_code))
    if form.etiquetas.data:
        for etiqueta_id in form.etiquetas.data:
            database.session.add(EtiquetaCurso(curso=new_code, etiqueta=etiqueta_id))


def _populate_edit_form(form, curso_a_editar, course_code: str) -> None:
    """Populate form fields with existing course data for editing."""
    field_map = {
        "nombre": curso_a_editar.nombre,
        "codigo": curso_a_editar.codigo,
        "descripcion_corta": curso_a_editar.descripcion_corta,
        "descripcion": curso_a_editar.descripcion,
        "nivel": curso_a_editar.nivel,
        "duracion": curso_a_editar.duracion,
        "publico": curso_a_editar.publico,
        "modalidad": curso_a_editar.modalidad,
        "foro_habilitado": curso_a_editar.foro_habilitado,
        "limitado": curso_a_editar.limitado,
        "capacidad": curso_a_editar.capacidad,
        "fecha_inicio": curso_a_editar.fecha_inicio,
        "fecha_fin": curso_a_editar.fecha_fin,
        "pagado": curso_a_editar.pagado,
        "auditable": curso_a_editar.auditable,
        "certificado": curso_a_editar.certificado,
        "plantilla_certificado": curso_a_editar.plantilla_certificado,
        "precio": curso_a_editar.precio,
    }
    for field, value in field_map.items():
        getattr(form, field).data = value
    form.categoria.data = get_course_category(course_code)
    form.etiquetas.data = get_course_tags(course_code)


course = Blueprint("course", __name__, template_folder=DIRECTORIO_PLANTILLAS)


@course.route("/course/<course_code>/view", methods=["GET"])
@cache.cached(key_prefix=cache_key_with_auth_state)  # type: ignore[arg-type]
def curso(course_code: str) -> str:
    """Pagina principal del curso."""
    _curso = database.session.execute(database.select(Curso).filter_by(codigo=course_code)).scalar_one_or_none()
    acceso, editable = _check_course_access(_curso, course_code)

    if acceso:
        return render_template(
            get_course_view_template(),
            curso=_curso,
            secciones=database.session.execute(
                database.select(CursoSeccion).filter_by(curso=course_code).order_by(CursoSeccion.indice)
            )
            .scalars()
            .all(),
            recursos=database.session.execute(
                database.select(CursoRecurso).filter_by(curso=course_code).order_by(CursoRecurso.indice)
            )
            .scalars()
            .all(),
            descargas=database.session.execute(
                database.select(Recurso).join(CursoRecursoDescargable).filter(CursoRecursoDescargable.curso == course_code)
            )
            .scalars()
            .all(),  # El join devuelve una tuple.
            nivel=CURSO_NIVEL,
            tipo=TIPOS_RECURSOS,
            editable=editable,
            markdown2html=markdown2html,
        )

    abort(403)


@course.route("/course/<course_code>/admin", methods=["GET"])
@login_required
@perfil_requerido("instructor")
@cache.cached(key_prefix=cache_key_with_auth_state)  # type: ignore[arg-type]
def administrar_curso(course_code: str) -> str:
    """Pagina principal del curso."""
    return render_template(
        "learning/curso/admin.html",
        curso=database.session.execute(select(Curso).filter_by(codigo=course_code)).scalars().first(),
        secciones=database.session.execute(select(CursoSeccion).filter_by(curso=course_code).order_by(CursoSeccion.indice))
        .scalars()
        .all(),
        recursos=database.session.execute(select(CursoRecurso).filter_by(curso=course_code).order_by(CursoRecurso.indice))
        .scalars()
        .all(),
        descargas=database.session.execute(
            database.select(Recurso).join(CursoRecursoDescargable).filter(CursoRecursoDescargable.curso == course_code)
        )
        .scalars()
        .all(),  # El join devuelve una tuple.
        nivel=CURSO_NIVEL,
        tipo=TIPOS_RECURSOS,
        markdown2html=markdown2html,
    )


@course.route("/course/new_curse", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def nuevo_curso() -> str | Response:
    """Formulario para crear un nuevo usuario."""
    form = CurseForm()
    form.plantilla_certificado.choices = generate_template_choices()
    form.categoria.choices = generate_category_choices()
    form.etiquetas.choices = generate_tag_choices()

    if not form.validate_on_submit():
        return render_template("learning/nuevo_curso.html", form=form, curso=None, edit=False)

    nuevo_curso_ = Curso(
        # Información básica
        nombre=form.nombre.data,
        codigo=form.codigo.data,
        descripcion=form.descripcion.data,
        descripcion_corta=form.descripcion_corta.data,
        nivel=form.nivel.data,
        duracion=form.duracion.data,
        # Estado de publicación
        estado="draft",
        publico=form.publico.data,
        # Modalidad
        modalidad=form.modalidad.data,
        # Configuración del foro
        foro_habilitado=form.foro_habilitado.data if form.modalidad.data != "self_paced" else False,
        # Disponibilidad de cupos
        limitado=form.limitado.data,
        capacidad=form.capacidad.data,
        # Fechas de inicio y fin
        fecha_inicio=form.fecha_inicio.data,
        fecha_fin=form.fecha_fin.data,
        # Información de pago
        pagado=form.pagado.data,
        auditable=form.auditable.data,
        certificado=form.certificado.data,
        plantilla_certificado=(
            form.plantilla_certificado.data if form.certificado.data and form.plantilla_certificado.data else None
        ),
        precio=form.precio.data,
        # Información adicional
        creado_por=current_user.usuario,
    )
    try:
        nuevo_curso_.creado = datetime.now(timezone.utc).date()
        nuevo_curso_.creado_por = current_user.usuario
        database.session.add(nuevo_curso_)
        database.session.commit()

        if form.categoria.data:
            database.session.add(CategoriaCurso(curso=form.codigo.data, categoria=form.categoria.data))
        for etiqueta_id in form.etiquetas.data or []:
            database.session.add(EtiquetaCurso(curso=form.codigo.data, etiqueta=etiqueta_id))

        database.session.commit()
        asignar_curso_a_instructor(form.codigo.data, usuario_id=current_user.usuario)
        _save_course_logo(nuevo_curso_)
        database.session.commit()
        flash(gettext("Curso creado exitosamente."), "success")
        return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=form.codigo.data))
    except OperationalError:
        flash(gettext("Hubo en error al crear su curso."), "warning")
        return redirect("/instructor")


@course.route("/course/<course_code>/edit", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def editar_curso(course_code: str) -> str | Response:
    """Editar pagina del curso."""
    form = CurseForm()
    form.plantilla_certificado.choices = generate_template_choices()
    form.categoria.choices = generate_category_choices()
    form.etiquetas.choices = generate_tag_choices()

    curso_a_editar = database.session.execute(select(Curso).filter_by(codigo=course_code)).scalars().first()
    curso_url = url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code)

    if form.validate_on_submit():
        _update_course_fields(curso_a_editar, form)
        try:
            with database.session.no_autoflush:
                curso_a_editar.modificado = datetime.now(timezone.utc)
                curso_a_editar.modificado_por = current_user.usuario
                _update_course_taxonomy(course_code, form.codigo.data, form)
            database.session.commit()
            _save_course_logo(curso_a_editar)
            flash(gettext("Curso actualizado exitosamente."), "success")
            return redirect(curso_url)
        except OperationalError:
            flash(gettext("Hubo en error al actualizar el curso."), "warning")
            return redirect(curso_url)
    elif request.method == "POST" and form.errors:
        flash(gettext("El formulario tiene errores. Revisa los campos marcados."), "warning")

    if request.method == "GET":
        _populate_edit_form(form, curso_a_editar, course_code)

    return render_template("learning/nuevo_curso.html", form=form, curso=curso_a_editar, edit=True)


@course.route("/course/<course_code>/new_seccion", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def nuevo_seccion(course_code: str) -> str | Response:
    """Formulario para crear una nueva sección en el curso."""
    # Las seccion son contenedores de recursos.
    form = CursoSeccionForm()
    if form.validate_on_submit():
        secciones = database.session.execute(select(func.count(CursoSeccion.id)).filter_by(curso=course_code)).scalar()
        nuevo_indice = int((secciones or 0) + 1)
        nueva_seccion = CursoSeccion(
            curso=course_code,
            nombre=form.nombre.data,
            descripcion=form.descripcion.data,
            estado=False,
            indice=nuevo_indice,
            creado_por=current_user.usuario,
        )
        try:
            nueva_seccion.creado = datetime.now(timezone.utc).date()
            nueva_seccion.creado_por = current_user.usuario
            database.session.add(nueva_seccion)
            database.session.commit()
            flash(gettext("Sección agregada correctamente al curso."), "success")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
        except OperationalError:
            flash(gettext("Hubo en error al crear la seccion."), "warning")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
    else:
        return render_template("learning/nuevo_seccion.html", form=form)


@course.route("/course/<course_code>/<seccion>/edit", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def editar_seccion(course_code: str, seccion: str) -> str | Response:
    """Formulario para editar una sección en el curso."""
    seccion_a_editar = database.session.get(CursoSeccion, seccion)
    if seccion_a_editar is None:
        abort(404)
    form = CursoSeccionForm(nombre=seccion_a_editar.nombre, descripcion=seccion_a_editar.descripcion)
    if form.validate_on_submit():
        seccion_a_editar.nombre = form.nombre.data
        seccion_a_editar.descripcion = form.descripcion.data
        seccion_a_editar.modificado_por = current_user.usuario
        seccion_a_editar.curso = course_code
        try:
            seccion_a_editar.modificado = datetime.now(timezone.utc)
            seccion_a_editar.modificado_por = current_user.usuario
            database.session.commit()
            flash(gettext("Sección modificada correctamente."), "success")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
        except OperationalError:
            flash(gettext("Hubo en error al actualizar la seccion."), "warning")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
    else:
        return render_template("learning/editar_seccion.html", form=form, seccion=seccion_a_editar)


@course.route("/my_courses", methods=["GET"])
@login_required
def my_courses() -> str | Response:
    """Show user's courses based on their role."""
    if current_user.tipo == "student":
        # Get enrolled courses for students
        enrolled_courses = (
            database.session.execute(
                database.select(Curso)
                .join(EstudianteCurso, Curso.codigo == EstudianteCurso.curso)
                .filter(EstudianteCurso.usuario == current_user.usuario)
                .filter(EstudianteCurso.vigente.is_(True))
                .order_by(Curso.nombre)
            )
            .scalars()
            .all()
        )

        return render_template(
            "learning/my_courses.html", courses=enrolled_courses, user_type="student", page_title=_("Mis Cursos")
        )

    if current_user.tipo in ("instructor", "admin"):
        # Get owned courses for instructors
        if current_user.tipo == "admin":
            # Admins can see all courses
            owned_courses = database.session.execute(database.select(Curso).order_by(Curso.nombre)).scalars().all()
        else:
            # Instructors see only their assigned courses
            owned_courses = (
                database.session.execute(
                    database.select(Curso)
                    .join(DocenteCurso, Curso.codigo == DocenteCurso.curso)
                    .filter(DocenteCurso.usuario == current_user.usuario)
                    .filter(DocenteCurso.vigente.is_(True))
                    .order_by(Curso.nombre)
                )
                .scalars()
                .all()
            )

        return render_template(
            "learning/my_courses.html", courses=owned_courses, user_type="instructor", page_title=_("Mis Cursos")
        )

    # For other user types, redirect to course exploration
    flash(_("Tipo de usuario no autorizado para esta página."), "warning")
    return redirect(url_for("course.lista_cursos"))


@course.route("/course/", methods=["GET"])
def course_index() -> Response:
    """Redirect to course exploration page."""
    return redirect(url_for("course.lista_cursos"))


@course.route("/course/explore", methods=["GET"])
@cache.cached(key_prefix=cache_key_with_auth_state)  # type: ignore[arg-type]
def lista_cursos() -> str:
    """Lista de cursos."""
    max_count = 3 if DESARROLLO else 30

    etiquetas = database.session.execute(select(Etiqueta)).scalars().all()
    categorias = database.session.execute(select(Categoria)).scalars().all()

    nivel_param = request.args.get("nivel")
    tag_param = request.args.get("tag")
    category_param = request.args.get("category")
    query = _course_explore_query(nivel_param, tag_param, category_param)

    # Paginate the filtered query
    consulta_cursos = database.paginate(
        query,
        page=request.args.get("page", default=1, type=int),
        max_per_page=max_count,
        count=True,
    )

    parametros = _course_explore_params(nivel_param, tag_param, category_param)

    return render_template(
        get_course_list_template(),
        cursos=consulta_cursos,
        etiquetas=etiquetas,
        categorias=categorias,
        parametros=parametros,
    )


# ---------------------------------------------------------------------------------------
# Administrative Enrollment Routes
# ---------------------------------------------------------------------------------------


def _authorized_enrollment_course(course_code: str):
    """Load a course and enforce the instructor enrollment permission."""
    curso = database.session.execute(database.select(Curso).filter_by(codigo=course_code)).scalar_one_or_none()
    if not curso:
        abort(404)
    if current_user.tipo != "admin":
        assignment = database.session.execute(
            database.select(DocenteCurso).filter_by(curso=course_code, usuario=current_user.usuario)
        ).scalar_one_or_none()
        if not assignment:
            abort(403)
    return curso


def _enrollment_student(course_code: str, username: str):
    """Return the requested student and any active enrollment."""
    student = database.session.execute(database.select(Usuario).filter_by(usuario=username)).scalar_one_or_none()
    enrollment = database.session.execute(
        database.select(EstudianteCurso).filter_by(curso=course_code, usuario=username, vigente=True)
    ).scalar_one_or_none()
    return student, enrollment


def _persist_admin_enrollment(course_code: str, curso, student, bypass_payment: bool, notes: str) -> None:
    """Create the administrative payment and enrollment records."""
    pago = Pago(
        usuario=student.usuario,
        curso=course_code,
        estado="completed",
        metodo="admin_enrollment",
        monto=0 if bypass_payment else curso.precio,
        descripcion=f"Inscripción administrativa por {current_user.usuario}",
        audit=not bypass_payment and curso.pagado,
        nombre=student.nombre,
        apellido=student.apellido,
        correo_electronico=student.correo_electronico,
        creado=datetime.now(timezone.utc).date(),
        creado_por=current_user.usuario,
    )
    if notes:
        pago.descripcion += f" - Notas: {notes}"
    database.session.add(pago)
    database.session.flush()
    enrollment = EstudianteCurso(
        curso=course_code,
        usuario=student.usuario,
        vigente=True,
        pago=pago.id,
        creado=datetime.now(timezone.utc).date(),
        creado_por=current_user.usuario,
    )
    database.session.add(enrollment)
    database.session.commit()
    _crear_indice_avance_curso(course_code)
    create_events_for_student_enrollment(student.usuario, course_code)


@course.route("/course/<course_code>/admin/enroll", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def admin_course_enrollment(course_code: str) -> str | Response:
    """Administrative enrollment of students to a course."""
    from now_lms.forms import AdminCourseEnrollmentForm

    _curso = _authorized_enrollment_course(course_code)
    form = AdminCourseEnrollmentForm()

    if form.validate_on_submit():
        student_username = form.student_username.data.strip()
        bypass_payment = form.bypass_payment.data
        notes = form.notes.data.strip() if form.notes.data else ""
        usuario_existe, existing_enrollment = _enrollment_student(course_code, student_username)
        if not usuario_existe:
            flash(f"El usuario '{student_username}' no existe en el sistema.", "error")
            return render_template(TEMPLATE_ADMIN_ENROLL, curso=_curso, form=form)
        if existing_enrollment:
            flash(f"El estudiante '{student_username}' ya está inscrito en este curso.", "warning")
            return render_template(TEMPLATE_ADMIN_ENROLL, curso=_curso, form=form)

        try:
            _persist_admin_enrollment(course_code, _curso, usuario_existe, bypass_payment, notes)

            flash(f"Estudiante '{student_username}' inscrito exitosamente en el curso '{_curso.nombre}'.", "success")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))

        except Exception as e:
            database.session.rollback()
            flash(f"Error al inscribir al estudiante: {str(e)}", "error")

    return render_template(TEMPLATE_ADMIN_ENROLL, curso=_curso, form=form)


@course.route("/course/<course_code>/admin/enrollments", methods=["GET"])
@login_required
@perfil_requerido("instructor")
def admin_course_enrollments(course_code: str) -> str:
    """View and manage course enrollments."""
    # Verify course exists
    _curso = database.session.execute(database.select(Curso).filter_by(codigo=course_code)).scalar_one_or_none()
    if not _curso:
        abort(404)

    # Only allow instructors to view their own course enrollments (or admins for any course)
    if current_user.tipo != "admin":
        # Check if current user is instructor of this course
        instructor_assignment = database.session.execute(
            database.select(DocenteCurso).filter_by(curso=course_code, usuario=current_user.usuario)
        ).scalar_one_or_none()
        if not instructor_assignment:
            abort(403)

    # Get all enrollments for this course
    enrollments = database.session.execute(
        database.select(EstudianteCurso, Usuario, Pago)
        .join(Usuario, EstudianteCurso.usuario == Usuario.usuario)
        .outerjoin(Pago, EstudianteCurso.pago == Pago.id)
        .filter(EstudianteCurso.curso == course_code, EstudianteCurso.vigente.is_(True))
        .order_by(EstudianteCurso.creado.desc())
    ).all()

    return render_template("learning/curso/admin_enrollments.html", curso=_curso, enrollments=enrollments)


@course.route("/course/<course_code>/admin/unenroll/<student_username>", methods=["POST"])
@login_required
@perfil_requerido("instructor")
def admin_course_unenrollment(course_code: str, student_username: str) -> Response:
    """Administrative unenrollment of a student from a course."""
    # Verify course exists
    _curso = database.session.execute(database.select(Curso).filter_by(codigo=course_code)).scalar_one_or_none()
    if not _curso:
        abort(404)

    # Only allow instructors to unenroll from their own courses (or admins for any course)
    if current_user.tipo != "admin":
        # Check if current user is instructor of this course
        instructor_assignment = database.session.execute(
            database.select(DocenteCurso).filter_by(curso=course_code, usuario=current_user.usuario)
        ).scalar_one_or_none()
        if not instructor_assignment:
            abort(403)

    # Find the enrollment
    enrollment = database.session.execute(
        database.select(EstudianteCurso).filter_by(curso=course_code, usuario=student_username, vigente=True)
    ).scalar_one_or_none()

    if not enrollment:
        flash(f"El estudiante '{student_username}' no está inscrito en este curso.", "error")
        return redirect(url_for("course.admin_course_enrollments", course_code=course_code))

    try:
        # Mark enrollment as inactive
        enrollment.vigente = False
        enrollment.modificado = datetime.now(timezone.utc).date()
        enrollment.modificado_por = current_user.usuario
        database.session.commit()

        flash(f"Estudiante '{student_username}' desinscrito del curso exitosamente.", "success")

    except Exception as e:
        database.session.rollback()
        flash(f"Error al desinscribir al estudiante: {str(e)}", "error")

    return redirect(url_for("course.admin_course_enrollments", course_code=course_code))


@course.route("/course/<course_code>/section/<section_id>/new_evaluation", methods=["GET"])
@login_required
@perfil_requerido("instructor")
def new_evaluation_from_section(course_code: str, section_id: str) -> Response:
    """Create a new evaluation for a course section from section actions."""
    # Redirect to the existing instructor profile route for evaluation creation
    return redirect(url_for("instructor_profile.new_evaluation", course_code=course_code, section_id=section_id))
