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
NO_AUTORIZADO_MSG = "No se encuentra autorizado a acceder al recurso solicitado."

# ---------------------------------------------------------------------------------------
# Template constants
# ---------------------------------------------------------------------------------------
TEMPLATE_SLIDE_SHOW = "learning/resources/slide_show.html"
TEMPLATE_COUPON_CREATE = "learning/curso/coupons/create.html"
TEMPLATE_COUPON_EDIT = "learning/curso/coupons/edit.html"

# Route constants
ROUTE_LIST_COUPONS = "course.list_coupons"


# Helper functions moved to now_lms.vistas.courses.helpers


course = Blueprint("course", __name__, template_folder=DIRECTORIO_PLANTILLAS)


@course.route("/course/<course_code>/view")
@cache.cached(key_prefix=cache_key_with_auth_state)  # type: ignore[arg-type]
def curso(course_code: str) -> str:
    """Pagina principal del curso."""
    _curso = database.session.execute(database.select(Curso).filter_by(codigo=course_code)).scalar_one_or_none()

    # Special access logic for LMS training course - accessible to admins and instructors
    if course_code == "lms-training" and current_user.is_authenticated:
        if current_user.tipo in ["admin", "instructor"]:
            acceso = True
            editable = current_user.tipo == "admin"
        else:
            acceso = False
            editable = False
    elif current_user.is_authenticated and request.args.get("inspect"):
        if current_user.tipo == "admin":
            acceso = True
            editable = True
        else:
            _consulta = database.select(DocenteCurso).filter(
                DocenteCurso.curso == course_code, DocenteCurso.usuario == current_user.usuario
            )
            docente_result = database.session.execute(_consulta).scalars().first()
            acceso = bool(docente_result)
            editable = bool(docente_result)
    elif current_user.is_authenticated:
        enrollment = (
            database.session.execute(
                database.select(EstudianteCurso).filter_by(curso=course_code, usuario=current_user.usuario, vigente=True)
            )
            .scalars()
            .first()
        )

        if enrollment:
            acceso = True
            editable = False
        elif _curso and _curso.publico:
            acceso = _curso.estado == "open" and _curso.publico is True
            editable = False
        else:
            acceso = False
            editable = False
    elif _curso and _curso.publico:
        acceso = _curso.estado == "open" and _curso.publico is True
        editable = False
    else:
        acceso = False
        editable = False

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


@course.route("/course/<course_code>/admin")
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

    if form.validate_on_submit() or request.method == "POST":
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

            # Assign category if selected
            if form.categoria.data:
                categoria_curso = CategoriaCurso(curso=form.codigo.data, categoria=form.categoria.data)
                database.session.add(categoria_curso)

            # Assign tags if selected
            if form.etiquetas.data:
                for etiqueta_id in form.etiquetas.data:
                    etiqueta_curso = EtiquetaCurso(curso=form.codigo.data, etiqueta=etiqueta_id)
                    database.session.add(etiqueta_curso)

            database.session.commit()
            asignar_curso_a_instructor(form.codigo.data, usuario_id=current_user.usuario)
            if "logo" in request.files:
                logo = request.files["logo"]
                logo_name = logo.filename
                logo_data = splitext(logo_name or "")
                logo_ext = logo_data[1] or ""
                try:
                    log.trace("Saving logo")
                    picture_file = images.save(logo, folder=form.codigo.data, name=f"logo{logo_ext}")
                    if picture_file:
                        nuevo_curso_.portada = True
                        nuevo_curso_.portada_ext = logo_ext
                        database.session.commit()
                        log.info("Course Logo saved")
                    else:
                        log.warning("Course Logo not saved")
                except UploadNotAllowed:
                    log.warning("Could not update profile photo.")
                    database.session.rollback()
                except AttributeError:
                    log.warning("Could not update profile photo.")
                    database.session.rollback()
            database.session.commit()
            flash("Curso creado exitosamente.", "success")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=form.codigo.data))
        except OperationalError:
            flash("Hubo en error al crear su curso.", "warning")
            return redirect("/instructor")
    else:
        return render_template("learning/nuevo_curso.html", form=form, curso=None, edit=False)


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
        # Información básica
        curso_a_editar.nombre = form.nombre.data
        curso_a_editar.codigo = form.codigo.data
        curso_a_editar.descripcion_corta = form.descripcion_corta.data
        curso_a_editar.descripcion = form.descripcion.data
        curso_a_editar.nivel = form.nivel.data
        curso_a_editar.duracion = form.duracion.data
        # Estado de publicación
        curso_a_editar.publico = form.publico.data
        # Modalidad
        curso_a_editar.modalidad = form.modalidad.data
        # Configuración del foro (validar restricción self-paced)
        if form.modalidad.data == "self_paced":
            curso_a_editar.foro_habilitado = False
        else:
            curso_a_editar.foro_habilitado = form.foro_habilitado.data
        # Disponibilidad de cupos
        curso_a_editar.limitado = form.limitado.data
        curso_a_editar.capacidad = form.capacidad.data
        # Fechas de inicio y fin
        curso_a_editar.fecha_inicio = form.fecha_inicio.data
        curso_a_editar.fecha_fin = form.fecha_fin.data
        # Información de pago
        curso_a_editar.pagado = form.pagado.data
        curso_a_editar.auditable = form.auditable.data
        curso_a_editar.certificado = form.certificado.data
        curso_a_editar.plantilla_certificado = form.plantilla_certificado.data
        curso_a_editar.precio = form.precio.data
        # Información de marketing
        if curso_a_editar.promocionado is False and form.promocionado.data is True:
            curso_a_editar.promocionado = datetime.today()
        curso_a_editar.promocionado = form.promocionado.data
        # Información adicional
        curso_a_editar.modificado_por = current_user.usuario

        try:
            with database.session.no_autoflush:
                curso_a_editar.modificado = datetime.now(timezone.utc)
                curso_a_editar.modificado_por = current_user.usuario

                # Handle category and tag updates with proper foreign key reference
                # Use the new course code if it has changed, otherwise use the original
                new_course_code = form.codigo.data

                # Update category assignment
                # First remove existing category assignment using original course_code
                database.session.execute(delete(CategoriaCurso).where(CategoriaCurso.curso == course_code))

                # Add new category if selected using new course code
                if form.categoria.data:
                    categoria_curso = CategoriaCurso(curso=new_course_code, categoria=form.categoria.data)
                    database.session.add(categoria_curso)

                # Update tag assignments
                # First remove existing tag assignments using original course_code
                database.session.execute(delete(EtiquetaCurso).where(EtiquetaCurso.curso == course_code))

                # Add new tags if selected using new course code
                if form.etiquetas.data:
                    for etiqueta_id in form.etiquetas.data:
                        etiqueta_curso = EtiquetaCurso(curso=new_course_code, etiqueta=etiqueta_id)
                        database.session.add(etiqueta_curso)

            database.session.commit()

            if "logo" in request.files:
                logo = request.files["logo"]
                logo_name = logo.filename
                logo_data = splitext(logo_name or "")
                logo_ext = logo_data[1] or ""
                try:
                    log.trace("Saving logo")
                    picture_file = images.save(logo, folder=form.codigo.data, name=f"logo{logo_ext}")
                    if picture_file:
                        curso_a_editar.portada = True
                        curso_a_editar.portada_ext = logo_ext
                        database.session.commit()
                        log.info("Course Logo saved")
                    else:
                        curso_a_editar.portada = False
                        database.session.commit()
                        log.warning("Course Logo not saved")
                except UploadNotAllowed:
                    log.warning("Could not update profile photo.")
                    database.session.rollback()
                except AttributeError:
                    log.warning("Could not update profile photo.")
                    database.session.rollback()
            flash("Curso actualizado exitosamente.", "success")
            return redirect(curso_url)

        except OperationalError:
            flash("Hubo en error al actualizar el curso.", "warning")
            return redirect(curso_url)

    elif request.method == "POST":
        # Mantener los datos enviados por el usuario y mostrar errores de validación
        if form.errors:
            flash("El formulario tiene errores. Revisa los campos marcados.", "warning")

    if request.method == "GET":
        # Populate form with existing data for GET requests
        form.nombre.data = curso_a_editar.nombre
        form.codigo.data = curso_a_editar.codigo
        form.descripcion_corta.data = curso_a_editar.descripcion_corta
        form.descripcion.data = curso_a_editar.descripcion
        form.nivel.data = curso_a_editar.nivel
        form.duracion.data = curso_a_editar.duracion
        form.publico.data = curso_a_editar.publico
        form.modalidad.data = curso_a_editar.modalidad
        form.foro_habilitado.data = curso_a_editar.foro_habilitado
        form.limitado.data = curso_a_editar.limitado
        form.capacidad.data = curso_a_editar.capacidad
        form.fecha_inicio.data = curso_a_editar.fecha_inicio
        form.fecha_fin.data = curso_a_editar.fecha_fin
        form.pagado.data = curso_a_editar.pagado
        form.auditable.data = curso_a_editar.auditable
        form.certificado.data = curso_a_editar.certificado
        form.plantilla_certificado.data = curso_a_editar.plantilla_certificado
        form.precio.data = curso_a_editar.precio

        # Populate category and tag current values
        form.categoria.data = get_course_category(course_code)
        form.etiquetas.data = get_course_tags(course_code)

    return render_template("learning/nuevo_curso.html", form=form, curso=curso_a_editar, edit=True)


@course.route("/course/<course_code>/new_seccion", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def nuevo_seccion(course_code: str) -> str | Response:
    """Formulario para crear una nueva sección en el curso."""
    # Las seccion son contenedores de recursos.
    form = CursoSeccionForm()
    if form.validate_on_submit() or request.method == "POST":
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
            flash("Sección agregada correctamente al curso.", "success")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
        except OperationalError:
            flash("Hubo en error al crear la seccion.", "warning")
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
    if form.validate_on_submit() or request.method == "POST":
        seccion_a_editar.nombre = form.nombre.data
        seccion_a_editar.descripcion = form.descripcion.data
        seccion_a_editar.modificado_por = current_user.usuario
        seccion_a_editar.curso = course_code
        try:
            seccion_a_editar.modificado = datetime.now(timezone.utc)
            seccion_a_editar.modificado_por = current_user.usuario
            database.session.commit()
            flash("Sección modificada correctamente.", "success")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
        except OperationalError:
            flash("Hubo en error al actualizar la seccion.", "warning")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
    else:
        return render_template("learning/editar_seccion.html", form=form, seccion=seccion_a_editar)


@course.route("/my_courses")
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


@course.route("/course/")
def course_index() -> Response:
    """Redirect to course exploration page."""
    return redirect(url_for("course.lista_cursos"))


@course.route("/course/explore")
@cache.cached(key_prefix=cache_key_with_auth_state)  # type: ignore[arg-type]
def lista_cursos() -> str:
    """Lista de cursos."""
    if DESARROLLO:
        MAX_COUNT = 3
    else:
        MAX_COUNT = 30

    etiquetas = database.session.execute(select(Etiqueta)).scalars().all()
    categorias = database.session.execute(select(Categoria)).scalars().all()

    # Build base query for courses
    query = database.select(Curso).filter(Curso.publico.is_(True), Curso.estado == "open")

    # Extract filter parameters
    nivel_param = request.args.get("nivel")
    tag_param = request.args.get("tag")
    category_param = request.args.get("category")

    # Apply level filter
    if nivel_param is not None:
        try:
            nivel = int(nivel_param)
            query = query.filter(Curso.nivel == nivel)
        except ValueError:
            pass  # Ignore invalid level values

    # Apply tag filter
    if tag_param:
        # Find tag by name
        tag = database.session.execute(select(Etiqueta).filter(Etiqueta.nombre == tag_param)).scalars().first()
        if tag:
            # Join with EtiquetaCurso to filter courses by tag
            query = query.join(EtiquetaCurso, Curso.codigo == EtiquetaCurso.curso).filter(EtiquetaCurso.etiqueta == tag.id)

    # Apply category filter
    if category_param:
        # Find category by name
        categoria = database.session.execute(select(Categoria).filter(Categoria.nombre == category_param)).scalars().first()
        if categoria:
            # Join with CategoriaCurso to filter courses by category
            query = query.join(CategoriaCurso, Curso.codigo == CategoriaCurso.curso).filter(
                CategoriaCurso.categoria == categoria.id
            )

    # Paginate the filtered query
    consulta_cursos = database.paginate(
        query,
        page=request.args.get("page", default=1, type=int),
        max_per_page=MAX_COUNT,
        count=True,
    )

    # Build parameters dict for URL building
    # /explore?page=2&nivel=2&tag=python&category=programming
    if nivel_param or tag_param or category_param:
        PARAMETROS = OrderedDict()
        for arg in request.url[request.url.find("?") + 1 :].split("&"):  # noqa: E203
            if "=" in arg:
                PARAMETROS[arg[: arg.find("=")]] = arg[arg.find("=") + 1 :]  # noqa: E203

        # El numero de pagina debe ser generado por el macro de paginación.
        try:
            del PARAMETROS["page"]
        except KeyError:
            pass
    else:
        PARAMETROS = None

    return render_template(
        get_course_list_template(),
        cursos=consulta_cursos,
        etiquetas=etiquetas,
        categorias=categorias,
        parametros=PARAMETROS,
    )


# ---------------------------------------------------------------------------------------
# Administrative Enrollment Routes
# ---------------------------------------------------------------------------------------


@course.route("/course/<course_code>/admin/enroll", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def admin_course_enrollment(course_code: str) -> str | Response:
    """Administrative enrollment of students to a course."""
    from now_lms.forms import AdminCourseEnrollmentForm

    # Verify course exists
    _curso = database.session.execute(database.select(Curso).filter_by(codigo=course_code)).scalar_one_or_none()
    if not _curso:
        abort(404)

    # Only allow instructors to enroll in their own courses (or admins for any course)
    if current_user.tipo != "admin":
        # Check if current user is instructor of this course
        instructor_assignment = database.session.execute(
            database.select(DocenteCurso).filter_by(curso=course_code, usuario=current_user.usuario)
        ).scalar_one_or_none()
        if not instructor_assignment:
            abort(403)

    form = AdminCourseEnrollmentForm()

    if form.validate_on_submit():
        student_username = form.student_username.data.strip()
        bypass_payment = form.bypass_payment.data
        notes = form.notes.data.strip() if form.notes.data else ""

        # Verify student exists
        usuario_existe = database.session.execute(
            database.select(Usuario).filter_by(usuario=student_username)
        ).scalar_one_or_none()

        if not usuario_existe:
            flash(f"El usuario '{student_username}' no existe en el sistema.", "error")
            return render_template("learning/curso/admin_enroll.html", curso=_curso, form=form)

        # Check if student is already enrolled
        existing_enrollment = database.session.execute(
            database.select(EstudianteCurso).filter_by(curso=course_code, usuario=student_username, vigente=True)
        ).scalar_one_or_none()

        if existing_enrollment:
            flash(f"El estudiante '{student_username}' ya está inscrito en este curso.", "warning")
            return render_template("learning/curso/admin_enroll.html", curso=_curso, form=form)

        try:
            # Create payment record for administrative enrollment
            pago = Pago()
            pago.usuario = student_username
            pago.curso = course_code
            pago.estado = "completed"
            pago.metodo = "admin_enrollment"
            pago.monto = 0 if bypass_payment else _curso.precio
            pago.descripcion = f"Inscripción administrativa por {current_user.usuario}"
            if notes:
                pago.descripcion += f" - Notas: {notes}"
            pago.audit = not bypass_payment and _curso.pagado
            # Populate required billing fields from student's user record
            pago.nombre = usuario_existe.nombre
            pago.apellido = usuario_existe.apellido
            pago.correo_electronico = usuario_existe.correo_electronico
            pago.creado = datetime.now(timezone.utc).date()
            pago.creado_por = current_user.usuario
            database.session.add(pago)
            database.session.flush()

            # Create student enrollment record
            enrollment = EstudianteCurso(
                curso=course_code,
                usuario=student_username,
                vigente=True,
                pago=pago.id,
            )
            enrollment.creado = datetime.now(timezone.utc).date()
            enrollment.creado_por = current_user.usuario
            database.session.add(enrollment)
            database.session.commit()

            _crear_indice_avance_curso(course_code)

            # Create calendar events for the enrolled student
            create_events_for_student_enrollment(student_username, course_code)

            flash(f"Estudiante '{student_username}' inscrito exitosamente en el curso '{_curso.nombre}'.", "success")
            return redirect(url_for("course.administrar_curso", course_code=course_code))

        except Exception as e:
            database.session.rollback()
            flash(f"Error al inscribir al estudiante: {str(e)}", "error")

    return render_template("learning/curso/admin_enroll.html", curso=_curso, form=form)


@course.route("/course/<course_code>/admin/enrollments")
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


@course.route("/course/<course_code>/section/<section_id>/new_evaluation")
@login_required
@perfil_requerido("instructor")
def new_evaluation_from_section(course_code: str, section_id: str) -> Response:
    """Create a new evaluation for a course section from section actions."""
    # Redirect to the existing instructor profile route for evaluation creation
    return redirect(url_for("instructor_profile.new_evaluation", course_code=course_code, section_id=section_id))
