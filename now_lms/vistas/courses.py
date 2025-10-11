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
from datetime import datetime, timedelta, timezone
from os import makedirs, path, remove, listdir, stat
from os.path import splitext
import re
from typing import Any, Sequence

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------
from bleach import clean, linkify
from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from flask_login import current_user, login_required
from flask_uploads import UploadNotAllowed
from markdown import markdown
from sqlalchemy import delete, func
from sqlalchemy.exc import OperationalError
from ulid import ULID
from werkzeug.wrappers import Response

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms.auth import perfil_requerido
from now_lms.bi import (
    asignar_curso_a_instructor,
    cambia_curso_publico,
    cambia_estado_curso_por_id,
    cambia_seccion_publico,
    modificar_indice_curso,
    modificar_indice_seccion,
    reorganiza_indice_curso,
    reorganiza_indice_seccion,
)
from now_lms.cache import cache, cache_key_with_auth_state
from now_lms.calendar_utils import create_events_for_student_enrollment, update_meet_resource_events
from now_lms.config import DESARROLLO, DIRECTORIO_PLANTILLAS, DIRECTORIO_ARCHIVOS_PUBLICOS, audio, files, images
from now_lms.db import (
    Categoria,
    CategoriaCurso,
    Certificacion,
    Configuracion,
    Coupon,
    CourseLibrary,
    Curso,
    CursoRecurso,
    CursoRecursoAvance,
    CursoRecursoDescargable,
    CursoRecursoSlides,
    CursoRecursoSlideShow,
    CursoSeccion,
    DocenteCurso,
    EstudianteCurso,
    Etiqueta,
    EtiquetaCurso,
    Evaluation,
    EvaluationAttempt,
    EvaluationReopenRequest,
    Pago,
    Recurso,
    Slide,
    SlideShowResource,
    Usuario,
    database,
    select,
)
from now_lms.db.tools import (
    crear_indice_recurso,
    generate_category_choices,
    generate_tag_choices,
    generate_template_choices,
    get_course_category,
    get_course_tags,
    verifica_docente_asignado_a_curso,
    verifica_estudiante_asignado_a_curso,
)
from now_lms.forms import (
    CouponApplicationForm,
    CouponForm,
    CurseForm,
    CursoLibraryFileForm,
    CursoRecursoArchivoAudio,
    CursoRecursoArchivoDescargable,
    CursoRecursoArchivoImagen,
    CursoRecursoArchivoPDF,
    CursoRecursoArchivoText,
    CursoRecursoExternalCode,
    CursoRecursoExternalLink,
    CursoRecursoMeet,
    CursoRecursoVideoYoutube,
    CursoSeccionForm,
    SlideShowForm,
)
from now_lms.i18n import _
from now_lms.logs import log
from now_lms.misc import CURSO_NIVEL, HTML_TAGS, INICIO_SESION, TIPOS_RECURSOS, sanitize_slide_content
from now_lms.themes import get_course_list_template, get_course_view_template

# ---------------------------------------------------------------------------------------
# Gestión de cursos.
# ---------------------------------------------------------------------------------------
RECURSO_AGREGADO = "Recurso agregado correctamente al curso."
ERROR_AL_AGREGAR_CURSO = "Hubo en error al crear el recurso."

# Safe file extensions for downloadable resources
SAFE_FILE_EXTENSIONS = {
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
    ".txt",
    ".rtf",
    ".csv",
    ".zip",
    ".rar",
    ".7z",
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".bmp",
    ".svg",
    ".webp",
    ".mp3",
    ".wav",
    ".ogg",
    ".mp4",
    ".avi",
    ".mov",
    ".wmv",
    ".flv",
    ".webm",
    ".json",
    ".xml",
    ".yaml",
    ".yml",
    ".md",
    ".html",
    ".css",
    ".prn",  # Project files (e.g., Microsoft Project)
}

# Dangerous file extensions that should never be allowed
DANGEROUS_FILE_EXTENSIONS = {
    ".exe",
    ".bat",
    ".cmd",
    ".com",
    ".scr",
    ".pif",
    ".msi",
    ".dll",
    ".vbs",
    ".js",
    ".jar",
    ".app",
    ".deb",
    ".rpm",
    ".dmg",
    ".pkg",
    ".sh",
    ".ps1",
    ".py",
    ".pl",
    ".rb",
    ".php",
    ".asp",
    ".jsp",
}
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


# ---------------------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------------------
def validate_downloadable_file(file, max_size_mb: int = 1) -> tuple[bool, str]:
    """
    Validate uploaded file for downloadable resources.

    Args:
        file: Flask uploaded file object
        max_size_mb: Maximum file size in megabytes

    Returns:
        tuple: (is_valid, error_message)
    """
    if not file or not file.filename:
        return False, "No se ha seleccionado ningún archivo"

    # Check file extension
    filename = file.filename.lower()
    file_ext = splitext(filename or "")[1].lower()

    if file_ext in DANGEROUS_FILE_EXTENSIONS:
        return False, f"Tipo de archivo no permitido por seguridad: {file_ext}"

    if file_ext not in SAFE_FILE_EXTENSIONS:
        return False, f"Tipo de archivo no soportado: {file_ext}"

    # Check file size (read position and reset)
    file.seek(0, 2)  # Seek to end
    file_size = file.tell()
    file.seek(0)  # Reset position

    max_size_bytes = max_size_mb * 1024 * 1024
    if file_size > max_size_bytes:
        return False, f"El archivo es demasiado grande. Máximo permitido: {max_size_mb}MB"

    return True, ""


def get_site_config() -> Configuracion:
    """Get site configuration."""
    row = database.session.execute(database.select(Configuracion)).first()
    if row is None:
        raise ValueError("No configuration found")
    return row[0]


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for library uploads.

    - Replace spaces with underscores
    - Remove unsafe characters
    - Keep original extension

    Args:
        filename: Original filename

    Returns:
        str: Sanitized filename
    """
    if not filename:
        return ""

    # Get base name and extension
    base_name, extension = splitext(filename)

    # Replace spaces with underscores and remove unsafe characters
    # Allow alphanumeric, underscore, hyphen, and dots
    safe_base = re.sub(r"[^a-zA-Z0-9._-]", "_", base_name)
    safe_base = re.sub(r"_+", "_", safe_base)  # Multiple underscores to single
    safe_base = safe_base.strip("_")  # Remove leading/trailing underscores

    return safe_base + extension.lower()


def get_course_library_path(course_code: str) -> str:
    """Get the library directory path for a course."""
    return path.join(DIRECTORIO_ARCHIVOS_PUBLICOS, "files", course_code, "library")


def ensure_course_library_directory(course_code: str) -> str:
    """Ensure course library directory exists and return its path."""
    library_path = get_course_library_path(course_code)
    if not path.exists(library_path):
        makedirs(library_path, exist_ok=True)
    return library_path


def markdown2html(text: str) -> str:
    """Convierte texto en markdown a HTML."""
    allowed_tags = HTML_TAGS
    allowed_attrs = {"*": ["class"], "a": ["href", "rel"], "img": ["src", "alt"]}

    html = markdown(text)
    html_limpio = clean(linkify(html), tags=allowed_tags, attributes=allowed_attrs)

    return html_limpio


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
        # Check if user is enrolled in the course
        enrollment = (
            database.session.execute(
                database.select(EstudianteCurso).filter_by(curso=course_code, usuario=current_user.usuario, vigente=True)
            )
            .scalars()
            .first()
        )

        if enrollment:
            # Enrolled student has access
            acceso = True
            editable = False
        elif _curso and _curso.publico:
            # Public course access
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


def _crear_indice_avance_curso(course_code: str) -> None:
    """Crea el índice de avance del curso."""
    recursos = (
        database.session.execute(
            database.select(CursoRecurso).filter(CursoRecurso.curso == course_code).order_by(CursoRecurso.indice)
        )
        .scalars()
        .all()
    )
    usuario = current_user.usuario

    if recursos:
        for recurso in recursos:
            avance = CursoRecursoAvance(
                usuario=usuario,
                curso=course_code,
                recurso=recurso.id,
                completado=False,
                requerido=recurso.requerido,
            )
            database.session.add(avance)
            database.session.commit()


@course.route("/course/<course_code>/enroll", methods=["GET", "POST"])
@login_required
@perfil_requerido("student")
def course_enroll(course_code: str) -> str | Response:
    """Pagina para inscribirse a un curso."""
    from now_lms.forms import PagoForm

    _curso = database.session.execute(database.select(Curso).filter_by(codigo=course_code)).scalar_one_or_none()
    _usuario = database.session.execute(database.select(Usuario).filter_by(usuario=current_user.usuario)).scalar_one_or_none()

    _modo = request.args.get("modo", "") or request.form.get("modo", "")

    # Check for coupon code in URL or form
    coupon_code = request.args.get("coupon_code", "") or request.form.get("coupon_code", "")
    applied_coupon = None
    original_price = _curso.precio if _curso.pagado else 0
    final_price = original_price
    discount_amount = 0

    # Validate and apply coupon if provided
    if coupon_code and _curso.pagado:
        coupon, _, validation_error = _validate_coupon_for_enrollment(course_code, coupon_code, _usuario)
        if coupon:
            applied_coupon = coupon
            discount_amount = coupon.calculate_discount(original_price)
            final_price = coupon.calculate_final_price(original_price)
        elif validation_error:
            flash(validation_error, "warning")

    form = PagoForm()
    coupon_form = CouponApplicationForm()

    # Pre-fill form data
    form.nombre.data = _usuario.nombre
    form.apellido.data = _usuario.apellido
    form.correo_electronico.data = _usuario.correo_electronico
    if coupon_code:
        coupon_form.coupon_code.data = coupon_code

    if form.validate_on_submit():
        pago = Pago()
        pago.usuario = _usuario.usuario
        pago.curso = _curso.codigo
        pago.nombre = form.nombre.data
        pago.apellido = form.apellido.data
        pago.correo_electronico = form.correo_electronico.data
        pago.direccion1 = form.direccion1.data
        pago.direccion2 = form.direccion2.data
        pago.provincia = form.provincia.data
        pago.codigo_postal = form.codigo_postal.data
        pago.pais = form.pais.data
        pago.monto = final_price
        pago.metodo = "paypal" if final_price > 0 else "free"

        # Add coupon information to payment description
        if applied_coupon:
            pago.descripcion = f"Cupón aplicado: {applied_coupon.code} (Descuento: {discount_amount})"

        # Handle different enrollment modes
        if not _curso.pagado or final_price == 0:
            # Free course or 100% discount coupon - complete enrollment immediately
            pago.estado = "completed"
            try:
                pago.creado = datetime.now(timezone.utc).date()
                pago.creado_por = current_user.usuario
                database.session.add(pago)
                database.session.flush()

                # Update coupon usage if applied
                if applied_coupon:
                    applied_coupon.current_uses += 1

                registro = EstudianteCurso(
                    curso=pago.curso,
                    usuario=pago.usuario,
                    vigente=True,
                    pago=pago.id,
                )
                registro.creado = datetime.now(timezone.utc).date()
                registro.creado_por = current_user.usuario
                database.session.add(registro)
                database.session.commit()
                _crear_indice_avance_curso(course_code)

                # Create calendar events for the enrolled student
                create_events_for_student_enrollment(pago.usuario, pago.curso)

                if applied_coupon and final_price == 0:
                    flash(
                        f"¡Cupón aplicado exitosamente! Inscripción gratuita con código {applied_coupon.code}",
                        "success",
                    )
                elif applied_coupon:
                    flash(f"¡Cupón aplicado! Descuento de {discount_amount} aplicado", "success")

                return redirect(url_for("course.tomar_curso", course_code=course_code))
            except OperationalError:
                database.session.rollback()
                flash("Hubo en error al crear el registro de pago.", "warning")
                return redirect(url_for(VISTA_CURSOS, course_code=course_code))

        elif _modo == "audit" and _curso.auditable:
            # Audit mode - allow access without payment but mark as audit
            pago.audit = True
            pago.estado = "completed"  # Audit enrollment is completed immediately
            pago.monto = 0
            pago.metodo = "audit"
            try:
                database.session.add(pago)
                database.session.flush()
                registro = EstudianteCurso(
                    curso=pago.curso,
                    usuario=pago.usuario,
                    vigente=True,
                    pago=pago.id,
                )
                database.session.add(registro)
                database.session.commit()
                _crear_indice_avance_curso(course_code)

                # Create calendar events for the enrolled student
                create_events_for_student_enrollment(pago.usuario, pago.curso)

                return redirect(url_for("course.tomar_curso", course_code=course_code))
            except OperationalError:
                flash("Hubo en error al crear el registro de pago.", "warning")
                return redirect(url_for(VISTA_CURSOS, course_code=course_code))

        else:
            # Paid course with amount > 0 - check for existing pending payment first
            existing = (
                database.session.execute(
                    select(Pago).filter_by(usuario=current_user.usuario, curso=course_code, estado="pending")
                )
                .scalars()
                .first()
            )
            if existing:
                return redirect(url_for("paypal.resume_payment", payment_id=existing.id))

            # Store payment with coupon information for PayPal processing
            try:
                database.session.add(pago)
                database.session.commit()

                # Redirect to PayPal payment page with payment ID
                return redirect(url_for("paypal.payment_page", course_code=course_code, payment_id=pago.id))
            except OperationalError:
                database.session.rollback()
                flash("Error al procesar el pago", "warning")
                return redirect(url_for(VISTA_CURSOS, course_code=course_code))

    return render_template(
        "learning/curso/enroll.html",
        curso=_curso,
        usuario=_usuario,
        form=form,
        coupon_form=coupon_form,
        applied_coupon=applied_coupon,
        original_price=original_price,
        final_price=final_price,
        discount_amount=discount_amount,
    )


@course.route("/course/<course_code>/take")
@login_required
@perfil_requerido("student")
@cache.cached(key_prefix=cache_key_with_auth_state)  # type: ignore[arg-type]
def tomar_curso(course_code: str) -> str | Response:
    """Pagina principal del curso."""
    if current_user.tipo == "student":
        # Get evaluations for this course
        evaluaciones = (
            database.session.execute(select(Evaluation).join(CursoSeccion).filter(CursoSeccion.curso == course_code))
            .scalars()
            .all()
        )

        # Get user's evaluation attempts
        evaluation_attempts = (
            database.session.execute(select(EvaluationAttempt).filter_by(user_id=current_user.usuario)).scalars().all()
        )

        # Get reopen requests
        reopen_requests = (
            database.session.execute(select(EvaluationReopenRequest).filter_by(user_id=current_user.usuario)).scalars().all()
        )

        # Check if user has paid for course (for paid courses)
        curso_obj = database.session.execute(database.select(Curso).filter_by(codigo=course_code)).scalar_one_or_none()
        user_has_paid = True  # Default for free courses
        if curso_obj and curso_obj.pagado:
            enrollment = database.session.execute(
                database.select(EstudianteCurso).filter_by(curso=course_code, usuario=current_user.usuario)
            ).scalar_one_or_none()
            user_has_paid = bool(enrollment and enrollment.pago)

        # Check if user has a certificate for this course
        user_certificate = (
            database.session.execute(select(Certificacion).filter_by(curso=course_code, usuario=current_user.usuario))
            .scalars()
            .first()
        )

        return render_template(
            "learning/curso.html",
            curso=curso_obj,
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
            evaluaciones=evaluaciones,
            evaluation_attempts=evaluation_attempts,
            reopen_requests=reopen_requests,
            user_has_paid=user_has_paid,
            user_certificate=user_certificate,
            markdown2html=markdown2html,
        )
    return redirect(url_for(VISTA_CURSOS, course_code=course_code))


@course.route("/course/<course_code>/moderate")
@login_required
@perfil_requerido("moderator")
@cache.cached(key_prefix=cache_key_with_auth_state)  # type: ignore[arg-type]
def moderar_curso(course_code: str) -> str | Response:
    """Pagina principal del curso."""
    if current_user.tipo in ("moderator", "admin"):
        return render_template(
            "learning/curso.html",
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
    return redirect(url_for(VISTA_CURSOS, course_code=course_code))


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

    # Populate form with existing data for GET requests and failed validations
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


@course.route("/course/<course_code>/seccion/increment/<indice>")
@login_required
@perfil_requerido("instructor")
def incrementar_indice_seccion(course_code: str, indice: str) -> Response:
    """Actualiza indice de secciones."""
    modificar_indice_curso(
        codigo_curso=course_code,
        indice=int(indice),
        task="decrement",
    )
    return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))


@course.route("/course/<course_code>/seccion/decrement/<indice>")
@login_required
@perfil_requerido("instructor")
def reducir_indice_seccion(course_code: str, indice: str) -> Response:
    """Actualiza indice de secciones."""
    modificar_indice_curso(
        codigo_curso=course_code,
        indice=int(indice),
        task="increment",
    )
    return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))


@course.route("/course/resource/<cource_code>/<seccion_id>/<task>/<resource_index>")
@login_required
@perfil_requerido("instructor")
def modificar_orden_recurso(cource_code: str, seccion_id: str, resource_index: str, task: str) -> Response:
    """Actualiza indice de recursos."""
    modificar_indice_seccion(
        seccion_id=seccion_id,
        indice=int(resource_index),
        task=task,
    )
    return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=cource_code))


@course.route("/course/<curso_code>/delete_recurso/<seccion>/<id_>")
@login_required
@perfil_requerido("instructor")
def eliminar_recurso(curso_code: str, seccion: str, id_: str) -> Response:
    """Elimina una seccion del curso."""
    database.session.execute(delete(CursoRecurso).where(CursoRecurso.id == id_))
    database.session.commit()
    reorganiza_indice_seccion(seccion=seccion)
    return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=curso_code))


@course.route("/course/<curso_id>/delete_seccion/<id_>")
@login_required
@perfil_requerido("instructor")
def eliminar_seccion(curso_id: str, id_: str) -> Response:
    """Elimina una seccion del curso."""
    database.session.execute(delete(CursoSeccion).where(CursoSeccion.id == id_))
    database.session.commit()
    reorganiza_indice_curso(codigo_curso=curso_id)
    return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=curso_id))


@course.route("/course/change_curse_status")
@login_required
@perfil_requerido("instructor")
def cambiar_estatus_curso() -> Response:
    """Actualiza el estatus de un curso."""
    cambia_estado_curso_por_id(
        request.args.get("curse"), nuevo_estado=request.args.get("status"), usuario=current_user.usuario
    )
    return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=request.args.get("curse")))


@course.route("/course/change_curse_public")
@login_required
@perfil_requerido("instructor")
def cambiar_curso_publico() -> Response:
    """Actualiza el estado publico de un curso."""
    cambia_curso_publico(
        id_curso=request.args.get("curse"),
    )
    return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=request.args.get("curse")))


@course.route("/course/change_curse_seccion_public")
@login_required
@perfil_requerido("instructor")
def cambiar_seccion_publico() -> Response:
    """Actualiza el estado publico de un curso."""
    cambia_seccion_publico(
        codigo=request.args.get("codigo"),
    )
    return redirect(url_for(VISTA_CURSOS, course_code=request.args.get("course_code")))


def _get_user_resource_progress(curso_id: str, usuario: str | None = None) -> dict[int, dict[str, bool]]:
    """Obtiene el progreso del usuario en todos los recursos del curso."""
    if not usuario:
        return {}

    progress_data = (
        database.session.execute(select(CursoRecursoAvance).filter_by(usuario=usuario, curso=curso_id)).scalars().all()
    )

    return {p.recurso: {"completado": p.completado} for p in progress_data}


def _get_course_evaluations_and_attempts(
    curso_id: str, usuario: str | None = None
) -> tuple[Sequence[Evaluation], dict[Any, Sequence[EvaluationAttempt]]]:
    """Obtiene las evaluaciones del curso y los intentos del usuario."""
    # Obtener las secciones del curso
    secciones = database.session.execute(select(CursoSeccion).filter_by(curso=curso_id)).scalars().all()
    section_ids = [s.id for s in secciones]

    # Obtener evaluaciones de todas las secciones del curso
    evaluaciones = database.session.execute(select(Evaluation).filter(Evaluation.section_id.in_(section_ids))).scalars().all()

    evaluation_attempts = {}
    if usuario:
        # Obtener intentos del usuario para cada evaluación
        for evaluation in evaluaciones:
            attempts = (
                database.session.execute(
                    select(EvaluationAttempt)
                    .filter_by(evaluation_id=evaluation.id, user_id=usuario)
                    .order_by(EvaluationAttempt.started_at)
                )
                .scalars()
                .all()
            )
            evaluation_attempts[evaluation.id] = attempts

    return evaluaciones, evaluation_attempts


@course.route("/course/<curso_id>/resource/<resource_type>/<codigo>")
def pagina_recurso(curso_id: str, resource_type: str, codigo: str) -> str:
    """Pagina de un recurso."""
    CURSO = database.session.execute(select(Curso).filter(Curso.codigo == curso_id)).scalars().first()
    RECURSO = database.session.execute(select(CursoRecurso).filter(CursoRecurso.id == codigo)).scalars().first()

    if not RECURSO:
        abort(404)

    RECURSOS = (
        database.session.execute(select(CursoRecurso).filter(CursoRecurso.curso == curso_id).order_by(CursoRecurso.indice))
        .scalars()
        .all()
    )
    SECCION = database.session.execute(select(CursoSeccion).filter(CursoSeccion.id == RECURSO.seccion)).scalars().first()
    SECCIONES = (
        database.session.execute(select(CursoSeccion).filter(CursoSeccion.curso == curso_id).order_by(CursoSeccion.indice))
        .scalars()
        .all()
    )
    match resource_type:
        case "html":
            TEMPLATE = "learning/resources/type_html.html"
        case "img":
            TEMPLATE = "learning/resources/type_img.html"
        case "link":
            TEMPLATE = "learning/resources/type_link.html"
        case "meet":
            TEMPLATE = "learning/resources/type_meet.html"
        case "mp3":
            TEMPLATE = "learning/resources/type_audio.html"
        case "pdf":
            TEMPLATE = "learning/resources/type_pdf.html"
        case "slides":
            TEMPLATE = "learning/resources/type_slides.html"
        case "text":
            TEMPLATE = "learning/resources/type_text.html"
        case "youtube":
            TEMPLATE = "learning/resources/type_youtube.html"
        case _:
            # Unknown resource type
            abort(404)
    INDICE = crear_indice_recurso(codigo)

    if current_user.is_authenticated:
        if current_user.tipo == "admin":
            show_resource = True
        elif current_user.tipo == "instructor" and verifica_docente_asignado_a_curso(curso_id):
            show_resource = True
        elif current_user.tipo == "student" and verifica_estudiante_asignado_a_curso(curso_id):
            show_resource = True
        else:
            show_resource = False
    else:
        show_resource = False

    if show_resource or RECURSO.publico:
        # Obtener progreso del recurso actual (solo para usuarios autenticados)
        recurso_completado = False
        if current_user.is_authenticated:
            resource_progress = (
                database.session.execute(
                    database.select(CursoRecursoAvance).filter_by(usuario=current_user.usuario, curso=curso_id, recurso=codigo)
                )
                .scalars()
                .first()
            )
            if resource_progress:
                recurso_completado = resource_progress.completado

        # Obtener datos adicionales para el sidebar mejorado
        user_progress: dict[int, dict[str, bool]] = {}
        evaluaciones: Sequence[Evaluation] = []
        evaluation_attempts: dict[Any, Sequence[EvaluationAttempt]] = {}

        if current_user.is_authenticated:
            user_progress = _get_user_resource_progress(curso_id, current_user.usuario)
            evaluaciones, evaluation_attempts = _get_course_evaluations_and_attempts(curso_id, current_user.usuario)

        return render_template(
            TEMPLATE,
            curso=CURSO,
            recurso=RECURSO,
            recursos=RECURSOS,
            seccion=SECCION,
            secciones=SECCIONES,
            indice=INDICE,
            recurso_completado=recurso_completado,
            user_progress=user_progress,
            evaluaciones=evaluaciones,
            evaluation_attempts=evaluation_attempts,
            markdown2html=markdown2html,
        )
    flash(NO_AUTORIZADO_MSG, "warning")
    return abort(403)


def _emitir_certificado(curso_id: str, usuario: str, plantilla: str) -> None:
    """Emit a certificate for a user in a course."""
    certificado = Certificacion(
        curso=curso_id,
        usuario=usuario,
        certificado=plantilla,
    )
    certificado.creado = datetime.now(timezone.utc).date()
    # Handle automatic certificate generation where current_user might not be available
    if current_user.is_authenticated:
        certificado.creado_por = current_user.usuario
    else:
        certificado.creado_por = "system"  # Mark as system-generated
    database.session.add(certificado)
    database.session.commit()
    flash("Certificado de finalización emitido.", "success")


def _actualizar_avance_curso(curso_id: str, usuario: str) -> None:
    """Actualiza el avance de un usuario en un curso."""
    from now_lms.db import CursoUsuarioAvance

    _avance = (
        database.session.execute(
            select(CursoUsuarioAvance).filter(CursoUsuarioAvance.curso == curso_id, CursoUsuarioAvance.usuario == usuario)
        )
        .scalars()
        .first()
    )

    if not _avance:
        _avance = CursoUsuarioAvance(
            curso=curso_id,
            usuario=usuario,
            recursos_requeridos=0,
            recursos_completados=0,
        )
        database.session.add(_avance)
        database.session.commit()

    _recursos_requeridos = database.session.execute(
        select(func.count(CursoRecurso.id)).filter(CursoRecurso.curso == curso_id, CursoRecurso.requerido == "required")
    ).scalar()

    _recursos_completados = database.session.execute(
        select(func.count(CursoRecursoAvance.id)).filter(
            CursoRecursoAvance.curso == curso_id,
            CursoRecursoAvance.usuario == usuario,
            CursoRecursoAvance.completado.is_(True),
            CursoRecursoAvance.requerido == "required",
        )
    ).scalar()
    log.warning("Required resources: %s, Completed: %s", _recursos_requeridos, _recursos_completados)

    _avance.recursos_requeridos = _recursos_requeridos or 0
    _avance.recursos_completados = _recursos_completados or 0
    _avance.avance = ((_recursos_completados or 0) / (_recursos_requeridos or 1)) * 100
    if _avance.avance >= 100:
        _avance.completado = True
        flash("Curso completado", "success")
        _curso = database.session.execute(select(Curso).filter(Curso.codigo == curso_id)).scalars().first()
        log.warning(_curso)
        if _curso.certificado:
            # Check if user meets ALL requirements including evaluations before issuing certificate
            from now_lms.vistas.evaluation_helpers import can_user_receive_certificate

            can_receive, reason = can_user_receive_certificate(curso_id, usuario)
            if can_receive:
                _emitir_certificado(curso_id, usuario, _curso.plantilla_certificado)
            else:
                log.info(f"Certificate not issued for user {usuario} in course {curso_id}: {reason}")
    database.session.commit()


@course.route("/course/<curso_id>/resource/<resource_type>/<codigo>/complete")
@login_required
@perfil_requerido("student")
def marcar_recurso_completado(curso_id: str, resource_type: str, codigo: str) -> Response:
    """Registra avance de un 100% en un recurso."""
    if current_user.is_authenticated:
        if current_user.tipo == "student":
            if verifica_estudiante_asignado_a_curso(curso_id):
                avance = (
                    database.session.execute(
                        select(CursoRecursoAvance).filter(
                            CursoRecursoAvance.usuario == current_user.usuario,
                            CursoRecursoAvance.curso == curso_id,
                            CursoRecursoAvance.recurso == codigo,
                        )
                    )
                    .scalars()
                    .first()
                )
                if avance:
                    avance.completado = True
                    database.session.commit()
                    flash("Recurso marcado como completado.", "success")
                else:
                    avance = CursoRecursoAvance(
                        usuario=current_user.usuario,
                        curso=curso_id,
                        recurso=codigo,
                        completado=True,
                    )
                    database.session.add(avance)
                    database.session.commit()
                    flash("Recurso marcado como completado.", "success")
                _actualizar_avance_curso(curso_id, current_user.usuario)
                return redirect(
                    url_for("course.pagina_recurso", curso_id=curso_id, resource_type=resource_type, codigo=codigo)
                )
            flash(NO_AUTORIZADO_MSG, "warning")
            return abort(403)
        flash(NO_AUTORIZADO_MSG, "warning")
        return abort(403)
    flash(NO_AUTORIZADO_MSG, "warning")
    return abort(403)


@course.route("/course/<curso_id>/alternative/<codigo>/<order>")
@login_required
@perfil_requerido("student")
def pagina_recurso_alternativo(curso_id: str, codigo: str, order: str) -> str:
    """Pagina para seleccionar un curso alternativo."""
    CURSO = database.session.execute(select(Curso).filter(Curso.codigo == curso_id)).scalars().first()
    RECURSO = database.session.execute(select(CursoRecurso).filter(CursoRecurso.id == codigo)).scalars().first()
    SECCION = database.session.execute(select(CursoSeccion).filter(CursoSeccion.id == RECURSO.seccion)).scalars().first()
    INDICE = crear_indice_recurso(codigo)

    if order == "asc":
        consulta_recursos = (
            database.session.execute(
                select(CursoRecurso)
                .filter(
                    CursoRecurso.seccion == RECURSO.seccion,
                    CursoRecurso.indice >= RECURSO.indice,  # type     : ignore[union-attr]
                )
                .order_by(CursoRecurso.indice)
            )
            .scalars()
            .all()
        )

    else:  # Equivale a order == "desc".
        consulta_recursos = (
            database.session.execute(
                select(CursoRecurso)
                .filter(CursoRecurso.seccion == RECURSO.seccion, CursoRecurso.indice >= RECURSO.indice)
                .order_by(CursoRecurso.indice.desc())
            )
            .scalars()
            .all()
        )

    if (current_user.is_authenticated and current_user.tipo == "admin") or RECURSO.publico is True:
        return render_template(
            "learning/resources/type_alternativo.html",
            recursos=consulta_recursos,
            curso=CURSO,
            recurso=RECURSO,
            seccion=SECCION,
            indice=INDICE,
        )
    flash(NO_AUTORIZADO_MSG, "warning")
    return abort(403)


@course.route("/course/<course_code>/<seccion>/new_resource")
@login_required
@perfil_requerido("instructor")
def nuevo_recurso(course_code: str, seccion: str) -> str:
    """Página para seleccionar tipo de recurso."""
    return render_template("learning/resources_new/nuevo_recurso.html", id_curso=course_code, id_seccion=seccion)


@course.route("/course/<course_code>/<seccion>/youtube/new", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def nuevo_recurso_youtube_video(course_code: str, seccion: str) -> str | Response:
    """Formulario para crear un nuevo recurso tipo vídeo en Youtube."""
    form = CursoRecursoVideoYoutube()
    consulta_recursos = database.session.execute(select(func.count(CursoRecurso.id)).filter_by(seccion=seccion)).scalar()
    nuevo_indice = int((consulta_recursos or 0) + 1)
    if form.validate_on_submit() or request.method == "POST":
        # Get global configuration for HTML preformatted descriptions
        config = database.session.execute(database.select(Configuracion)).scalars().first()
        html_preformateado = False
        if config and config.enable_html_preformatted_descriptions and hasattr(form, "descripcion_html_preformateado"):
            html_preformateado = form.descripcion_html_preformateado.data or False

        nuevo_recurso_ = CursoRecurso(
            curso=course_code,
            seccion=seccion,
            tipo="youtube",
            nombre=form.nombre.data,
            descripcion=form.descripcion.data,
            url=form.youtube_url.data,
            requerido=form.requerido.data,
            indice=nuevo_indice,
            creado_por=current_user.usuario,
            descripcion_html_preformateado=html_preformateado,
        )
        try:
            database.session.add(nuevo_recurso_)
            database.session.commit()
            flash(RECURSO_AGREGADO, "success")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
        except OperationalError:
            flash(ERROR_AL_AGREGAR_CURSO, "warning")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
    else:
        return render_template(
            "learning/resources_new/nuevo_recurso_youtube.html", id_curso=course_code, id_seccion=seccion, form=form
        )


@course.route("/course/<course_code>/<seccion>/youtube/<resource_id>/edit", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def editar_recurso_youtube_video(course_code: str, seccion: str, resource_id: str) -> str | Response:
    """Formulario para editar un recurso tipo vídeo en Youtube."""
    recurso = database.session.execute(
        select(CursoRecurso).filter_by(id=resource_id, curso=course_code, seccion=seccion)
    ).scalar_one_or_none()
    if not recurso or recurso.tipo != "youtube":
        flash("Recurso no encontrado.", "warning")
        return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))

    form = CursoRecursoVideoYoutube()

    if form.validate_on_submit() or request.method == "POST":
        recurso.nombre = form.nombre.data
        recurso.descripcion = form.descripcion.data
        recurso.url = form.youtube_url.data
        recurso.requerido = form.requerido.data
        recurso.modificado = datetime.now(timezone.utc)
        recurso.modificado_por = current_user.usuario

        # Handle HTML preformatted flag - only set if global config allows it
        config = database.session.execute(database.select(Configuracion)).scalars().first()
        if config and config.enable_html_preformatted_descriptions and hasattr(form, "descripcion_html_preformateado"):
            recurso.descripcion_html_preformateado = form.descripcion_html_preformateado.data or False
        else:
            recurso.descripcion_html_preformateado = False

        try:
            database.session.commit()
            flash("Recurso actualizado correctamente.", "success")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
        except OperationalError:
            flash("Hubo un error al actualizar el recurso.", "warning")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
    else:
        # Pre-populate form with existing data
        form.nombre.data = recurso.nombre
        form.descripcion.data = recurso.descripcion
        form.youtube_url.data = recurso.url
        form.requerido.data = recurso.requerido
        form.descripcion_html_preformateado.data = recurso.descripcion_html_preformateado or False

        return render_template(
            "learning/resources_new/editar_recurso_youtube.html",
            id_curso=course_code,
            id_seccion=seccion,
            recurso=recurso,
            form=form,
        )


@course.route("/course/<course_code>/<seccion>/text/new", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def nuevo_recurso_text(course_code: str, seccion: str) -> str | Response:
    """Formulario para crear un nuevo documento de texto."""
    form = CursoRecursoArchivoText()
    consulta_recursos = database.session.execute(select(func.count(CursoRecurso.id)).filter_by(seccion=seccion)).scalar()
    nuevo_indice = int((consulta_recursos or 0) + 1)
    if form.validate_on_submit() or request.method == "POST":
        # Get global configuration for HTML preformatted descriptions
        config = database.session.execute(database.select(Configuracion)).scalars().first()
        html_preformateado = False
        if config and config.enable_html_preformatted_descriptions and hasattr(form, "descripcion_html_preformateado"):
            html_preformateado = form.descripcion_html_preformateado.data or False

        nuevo_recurso_ = CursoRecurso(
            curso=course_code,
            seccion=seccion,
            tipo="text",
            nombre=form.nombre.data,
            descripcion=form.descripcion.data,
            requerido=form.requerido.data,
            indice=nuevo_indice,
            text=form.editor.data,
            creado_por=current_user.usuario,
            descripcion_html_preformateado=html_preformateado,
        )
        try:
            nuevo_recurso_.creado = datetime.now(timezone.utc).date()
            nuevo_recurso_.creado_por = current_user.usuario
            database.session.add(nuevo_recurso_)
            database.session.commit()
            flash(RECURSO_AGREGADO, "success")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
        except OperationalError:
            flash(ERROR_AL_AGREGAR_CURSO, "warning")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
    else:
        return render_template(
            "learning/resources_new/nuevo_recurso_text.html", id_curso=course_code, id_seccion=seccion, form=form
        )


@course.route("/course/<course_code>/<seccion>/text/<resource_id>/edit", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def editar_recurso_text(course_code: str, seccion: str, resource_id: str) -> str | Response:
    """Formulario para editar un documento de texto."""
    recurso = database.session.execute(
        select(CursoRecurso).filter_by(id=resource_id, curso=course_code, seccion=seccion)
    ).scalar_one_or_none()
    if not recurso or recurso.tipo != "text":
        flash("Recurso no encontrado.", "warning")
        return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))

    form = CursoRecursoArchivoText()

    if form.validate_on_submit() or request.method == "POST":
        recurso.nombre = form.nombre.data
        recurso.descripcion = form.descripcion.data
        recurso.requerido = form.requerido.data
        recurso.text = form.editor.data
        recurso.modificado = datetime.now(timezone.utc)
        recurso.modificado_por = current_user.usuario

        # Handle HTML preformatted flag - only set if global config allows it
        config = database.session.execute(database.select(Configuracion)).scalars().first()
        if config and config.enable_html_preformatted_descriptions and hasattr(form, "descripcion_html_preformateado"):
            recurso.descripcion_html_preformateado = form.descripcion_html_preformateado.data or False
        else:
            recurso.descripcion_html_preformateado = False

        try:
            database.session.commit()
            flash("Recurso actualizado correctamente.", "success")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
        except OperationalError:
            flash("Hubo un error al actualizar el recurso.", "warning")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
    else:
        # Pre-populate form with existing data
        form.nombre.data = recurso.nombre
        form.descripcion.data = recurso.descripcion
        form.requerido.data = recurso.requerido
        form.editor.data = recurso.text
        form.descripcion_html_preformateado.data = recurso.descripcion_html_preformateado or False

        return render_template(
            "learning/resources_new/editar_recurso_text.html",
            id_curso=course_code,
            id_seccion=seccion,
            recurso=recurso,
            form=form,
        )


@course.route("/course/<course_code>/<seccion>/link/new", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def nuevo_recurso_link(course_code: str, seccion: str) -> str | Response:
    """Formulario para crear un nuevo documento de texto."""
    form = CursoRecursoExternalLink()
    recursos = database.session.execute(select(func.count(CursoRecurso.id)).filter_by(seccion=seccion)).scalar()
    nuevo_indice = int((recursos or 0) + 1)
    if form.validate_on_submit() or request.method == "POST":
        # Get global configuration for HTML preformatted descriptions
        config = database.session.execute(database.select(Configuracion)).scalars().first()
        html_preformateado = False
        if config and config.enable_html_preformatted_descriptions and hasattr(form, "descripcion_html_preformateado"):
            html_preformateado = form.descripcion_html_preformateado.data or False

        nuevo_recurso_ = CursoRecurso(
            curso=course_code,
            seccion=seccion,
            tipo="link",
            nombre=form.nombre.data,
            descripcion=form.descripcion.data,
            requerido=form.requerido.data,
            indice=nuevo_indice,
            url=form.url.data,
            creado_por=current_user.usuario,
            descripcion_html_preformateado=html_preformateado,
        )
        try:
            database.session.add(nuevo_recurso_)
            database.session.commit()
            flash(RECURSO_AGREGADO, "success")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
        except OperationalError:
            flash(ERROR_AL_AGREGAR_CURSO, "warning")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
    else:
        return render_template(
            "learning/resources_new/nuevo_recurso_link.html", id_curso=course_code, id_seccion=seccion, form=form
        )


@course.route("/course/<course_code>/<seccion>/link/<resource_id>/edit", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def editar_recurso_link(course_code: str, seccion: str, resource_id: str) -> str | Response:
    """Formulario para editar un enlace externo."""
    recurso = database.session.execute(
        select(CursoRecurso).filter_by(id=resource_id, curso=course_code, seccion=seccion)
    ).scalar_one_or_none()
    if not recurso or recurso.tipo != "link":
        flash("Recurso no encontrado.", "warning")
        return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))

    form = CursoRecursoExternalLink()

    if form.validate_on_submit() or request.method == "POST":
        recurso.nombre = form.nombre.data
        recurso.descripcion = form.descripcion.data
        recurso.requerido = form.requerido.data
        recurso.url = form.url.data
        recurso.modificado_por = current_user.usuario

        # Handle HTML preformatted flag - only set if global config allows it
        config = database.session.execute(database.select(Configuracion)).scalars().first()
        if config and config.enable_html_preformatted_descriptions and hasattr(form, "descripcion_html_preformateado"):
            recurso.descripcion_html_preformateado = form.descripcion_html_preformateado.data or False
        else:
            recurso.descripcion_html_preformateado = False

        try:
            database.session.commit()
            flash("Recurso actualizado correctamente.", "success")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
        except OperationalError:
            flash("Hubo un error al actualizar el recurso.", "warning")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
    else:
        # Pre-populate form with existing data
        form.nombre.data = recurso.nombre
        form.descripcion.data = recurso.descripcion
        form.requerido.data = recurso.requerido
        form.url.data = recurso.url
        form.descripcion_html_preformateado.data = recurso.descripcion_html_preformateado or False

        return render_template(
            "learning/resources_new/editar_recurso_link.html",
            id_curso=course_code,
            id_seccion=seccion,
            recurso=recurso,
            form=form,
        )


@course.route("/course/<course_code>/<seccion>/pdf/new", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def nuevo_recurso_pdf(course_code: str, seccion: str) -> str | Response:
    """Formulario para crear un nuevo recurso tipo archivo en PDF."""
    form = CursoRecursoArchivoPDF()
    recursos = database.session.execute(select(func.count(CursoRecurso.id)).filter_by(seccion=seccion)).scalar()
    nuevo_indice = int((recursos or 0) + 1)
    if (form.validate_on_submit() or request.method == "POST") and "pdf" in request.files:
        # Get global configuration for HTML preformatted descriptions
        config = database.session.execute(database.select(Configuracion)).scalars().first()
        html_preformateado = False
        if config and config.enable_html_preformatted_descriptions and hasattr(form, "descripcion_html_preformateado"):
            html_preformateado = form.descripcion_html_preformateado.data or False

        file_name = str(ULID()) + ".pdf"
        pdf_file = files.save(request.files["pdf"], folder=course_code, name=file_name)
        nuevo_recurso_ = CursoRecurso(
            curso=course_code,
            seccion=seccion,
            tipo="pdf",
            nombre=form.nombre.data,
            descripcion=form.descripcion.data,
            requerido=form.requerido.data,
            indice=nuevo_indice,
            base_doc_url=files.name,
            doc=pdf_file,
            creado_por=current_user.usuario,
            descripcion_html_preformateado=html_preformateado,
        )
        try:
            database.session.add(nuevo_recurso_)
            database.session.commit()
            flash("RECURSO_AGREGADO", "success")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
        except OperationalError:
            flash(ERROR_AL_AGREGAR_CURSO, "warning")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
    else:
        return render_template(
            "learning/resources_new/nuevo_recurso_pdf.html", id_curso=course_code, id_seccion=seccion, form=form
        )


@course.route("/course/<course_code>/<seccion>/pdf/<resource_id>/edit", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def editar_recurso_pdf(course_code: str, seccion: str, resource_id: str) -> str | Response:
    """Formulario para editar un recurso tipo archivo en PDF."""
    recurso = database.session.execute(
        select(CursoRecurso).filter_by(id=resource_id, curso=course_code, seccion=seccion)
    ).scalar_one_or_none()
    if not recurso or recurso.tipo != "pdf":
        flash("Recurso no encontrado.", "warning")
        return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))

    form = CursoRecursoArchivoPDF()

    if form.validate_on_submit() or request.method == "POST":
        recurso.nombre = form.nombre.data
        recurso.descripcion = form.descripcion.data
        recurso.requerido = form.requerido.data
        recurso.modificado_por = current_user.usuario

        # Handle HTML preformatted flag - only set if global config allows it
        config = database.session.execute(database.select(Configuracion)).scalars().first()
        if config and config.enable_html_preformatted_descriptions and hasattr(form, "descripcion_html_preformateado"):
            recurso.descripcion_html_preformateado = form.descripcion_html_preformateado.data or False
        else:
            recurso.descripcion_html_preformateado = False

        # Handle file replacement if a new PDF is uploaded
        if "pdf" in request.files and request.files["pdf"].filename:
            file_name = str(ULID()) + ".pdf"
            pdf_file = files.save(request.files["pdf"], folder=course_code, name=file_name)
            recurso.base_doc_url = files.name
            recurso.doc = pdf_file

        try:
            database.session.commit()
            flash("Recurso actualizado correctamente.", "success")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
        except OperationalError:
            flash("Hubo un error al actualizar el recurso.", "warning")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
    else:
        # Pre-populate form with existing data
        form.nombre.data = recurso.nombre
        form.descripcion.data = recurso.descripcion
        form.requerido.data = recurso.requerido
        form.descripcion_html_preformateado.data = recurso.descripcion_html_preformateado or False

        return render_template(
            "learning/resources_new/editar_recurso_pdf.html",
            id_curso=course_code,
            id_seccion=seccion,
            recurso=recurso,
            form=form,
        )


@course.route("/course/<course_code>/<seccion>/meet/new", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def nuevo_recurso_meet(course_code: str, seccion: str) -> str | Response:
    """Formulario para crear un nuevo recurso tipo archivo en PDF."""
    form = CursoRecursoMeet()
    recursos = database.session.execute(select(func.count(CursoRecurso.id)).filter_by(seccion=seccion)).scalar()
    nuevo_indice = int((recursos or 0) + 1)
    if form.validate_on_submit() or request.method == "POST":
        # Get global configuration for HTML preformatted descriptions
        config = database.session.execute(database.select(Configuracion)).scalars().first()
        html_preformateado = False
        if config and config.enable_html_preformatted_descriptions and hasattr(form, "descripcion_html_preformateado"):
            html_preformateado = form.descripcion_html_preformateado.data or False

        nuevo_recurso_ = CursoRecurso(
            curso=course_code,
            seccion=seccion,
            tipo="meet",
            nombre=form.nombre.data,
            descripcion=form.descripcion.data,
            requerido=form.requerido.data,
            indice=nuevo_indice,
            creado_por=current_user.usuario,
            url=form.url.data,
            fecha=form.fecha.data,
            hora_inicio=form.hora_inicio.data,
            hora_fin=form.hora_fin.data,
            notes=form.notes.data,
            descripcion_html_preformateado=html_preformateado,
        )
        try:
            database.session.add(nuevo_recurso_)
            database.session.commit()
            flash("RECURSO_AGREGADO", "success")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
        except OperationalError:
            flash(ERROR_AL_AGREGAR_CURSO, "warning")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
    else:
        return render_template(
            "learning/resources_new/nuevo_recurso_meet.html", id_curso=course_code, id_seccion=seccion, form=form
        )


@course.route("/course/<course_code>/<seccion>/meet/<resource_id>/edit", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def editar_recurso_meet(course_code: str, seccion: str, resource_id: str) -> str | Response:
    """Formulario para editar un recurso tipo meet."""
    recurso = database.session.execute(
        select(CursoRecurso).filter_by(id=resource_id, curso=course_code, seccion=seccion)
    ).scalar_one_or_none()
    if not recurso or recurso.tipo != "meet":
        flash("Recurso no encontrado.", "warning")
        return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))

    form = CursoRecursoMeet()

    if form.validate_on_submit() or request.method == "POST":
        recurso.nombre = form.nombre.data
        recurso.descripcion = form.descripcion.data
        recurso.requerido = form.requerido.data
        recurso.url = form.url.data
        recurso.fecha = form.fecha.data
        recurso.hora_inicio = form.hora_inicio.data
        recurso.hora_fin = form.hora_fin.data
        recurso.notes = form.notes.data
        recurso.modificado_por = current_user.usuario

        # Handle HTML preformatted flag - only set if global config allows it
        config = database.session.execute(database.select(Configuracion)).scalars().first()
        if config and config.enable_html_preformatted_descriptions and hasattr(form, "descripcion_html_preformateado"):
            recurso.descripcion_html_preformateado = form.descripcion_html_preformateado.data or False
        else:
            recurso.descripcion_html_preformateado = False

        try:
            database.session.commit()
            # Update calendar events for this meet resource
            update_meet_resource_events(resource_id)
            flash("Recurso actualizado correctamente.", "success")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
        except OperationalError:
            flash("Hubo un error al actualizar el recurso.", "warning")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
    else:
        # Pre-populate form with existing data
        form.nombre.data = recurso.nombre
        form.descripcion.data = recurso.descripcion
        form.requerido.data = recurso.requerido
        form.url.data = recurso.url
        form.fecha.data = recurso.fecha
        form.hora_inicio.data = recurso.hora_inicio
        form.hora_fin.data = recurso.hora_fin
        form.notes.data = recurso.notes
        form.descripcion_html_preformateado.data = recurso.descripcion_html_preformateado or False

        return render_template(
            "learning/resources_new/editar_recurso_meet.html",
            id_curso=course_code,
            id_seccion=seccion,
            recurso=recurso,
            form=form,
        )


@course.route("/course/<course_code>/<seccion>/img/new", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def nuevo_recurso_img(course_code: str, seccion: str) -> str | Response:
    """Formulario para crear un nuevo recurso tipo imagen."""
    form = CursoRecursoArchivoImagen()
    recursos = database.session.execute(select(func.count(CursoRecurso.id)).filter_by(seccion=seccion)).scalar()
    nuevo_indice = int((recursos or 0) + 1)
    if (form.validate_on_submit() or request.method == "POST") and "img" in request.files:
        # Get global configuration for HTML preformatted descriptions
        config = database.session.execute(database.select(Configuracion)).scalars().first()
        html_preformateado = False
        if config and config.enable_html_preformatted_descriptions and hasattr(form, "descripcion_html_preformateado"):
            html_preformateado = form.descripcion_html_preformateado.data or False

        img_filename = request.files["img"].filename
        img_ext = splitext(img_filename or "")[1]
        file_name = str(ULID()) + (img_ext or "")
        picture_file = images.save(request.files["img"], folder=course_code, name=file_name)

        nuevo_recurso_ = CursoRecurso(
            curso=course_code,
            seccion=seccion,
            tipo="img",
            nombre=form.nombre.data,
            descripcion=form.descripcion.data,
            requerido=form.requerido.data,
            indice=nuevo_indice,
            base_doc_url=images.name,
            doc=picture_file,
            creado_por=current_user.usuario,
            descripcion_html_preformateado=html_preformateado,
        )
        try:
            database.session.add(nuevo_recurso_)
            database.session.commit()
            flash("RECURSO_AGREGADO", "success")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
        except OperationalError:
            flash(ERROR_AL_AGREGAR_CURSO, "warning")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
    else:
        return render_template(
            "learning/resources_new/nuevo_recurso_img.html", id_curso=course_code, id_seccion=seccion, form=form
        )


@course.route("/course/<course_code>/<seccion>/img/<resource_id>/edit", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def editar_recurso_img(course_code: str, seccion: str, resource_id: str) -> str | Response:
    """Formulario para editar un recurso tipo imagen."""
    recurso = database.session.execute(
        select(CursoRecurso).filter_by(id=resource_id, curso=course_code, seccion=seccion)
    ).scalar_one_or_none()
    if not recurso or recurso.tipo != "img":
        flash("Recurso no encontrado.", "warning")
        return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))

    form = CursoRecursoArchivoImagen()

    if form.validate_on_submit() or request.method == "POST":
        recurso.nombre = form.nombre.data
        recurso.descripcion = form.descripcion.data
        recurso.requerido = form.requerido.data
        recurso.modificado_por = current_user.usuario

        # Handle HTML preformatted flag - only set if global config allows it
        config = database.session.execute(database.select(Configuracion)).scalars().first()
        if config and config.enable_html_preformatted_descriptions and hasattr(form, "descripcion_html_preformateado"):
            recurso.descripcion_html_preformateado = form.descripcion_html_preformateado.data or False
        else:
            recurso.descripcion_html_preformateado = False

        # Handle file replacement if a new image is uploaded
        if "img" in request.files and request.files["img"].filename:
            img_filename = request.files["img"].filename
            img_ext = splitext(img_filename)[1]
            file_name = str(ULID()) + (img_ext or "")
            picture_file = images.save(request.files["img"], folder=course_code, name=file_name)
            recurso.base_doc_url = images.name
            recurso.doc = picture_file

        try:
            database.session.commit()
            flash("Recurso actualizado correctamente.", "success")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
        except OperationalError:
            flash("Hubo un error al actualizar el recurso.", "warning")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
    else:
        # Pre-populate form with existing data
        form.nombre.data = recurso.nombre
        form.descripcion.data = recurso.descripcion
        form.requerido.data = recurso.requerido
        form.descripcion_html_preformateado.data = recurso.descripcion_html_preformateado or False

        return render_template(
            "learning/resources_new/editar_recurso_img.html",
            id_curso=course_code,
            id_seccion=seccion,
            recurso=recurso,
            form=form,
        )


@course.route("/course/<course_code>/<seccion>/audio/new", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def nuevo_recurso_audio(course_code: str, seccion: str) -> str | Response:
    """Formulario para crear un nuevo recurso de audio."""
    form = CursoRecursoArchivoAudio()
    recursos = database.session.execute(select(func.count(CursoRecurso.id)).filter_by(seccion=seccion)).scalar()
    nuevo_indice = int((recursos or 0) + 1)
    if (form.validate_on_submit() or request.method == "POST") and "audio" in request.files:
        # Get global configuration for HTML preformatted descriptions
        config = database.session.execute(database.select(Configuracion)).scalars().first()
        html_preformateado = False
        if config and config.enable_html_preformatted_descriptions and hasattr(form, "descripcion_html_preformateado"):
            html_preformateado = form.descripcion_html_preformateado.data or False

        audio_filename = request.files["audio"].filename
        audio_ext = splitext(audio_filename or "")[1]
        audio_name = str(ULID()) + (audio_ext or "")
        audio_file = audio.save(request.files["audio"], folder=course_code, name=audio_name)

        # Handle VTT subtitle file upload
        subtitle_vtt_content = None
        if "vtt_subtitle" in request.files and request.files["vtt_subtitle"].filename:
            vtt_file = request.files["vtt_subtitle"]
            if vtt_file.filename.endswith(".vtt"):
                subtitle_vtt_content = vtt_file.read().decode("utf-8")

        # Handle secondary VTT subtitle file upload
        subtitle_vtt_secondary_content = None
        if "vtt_subtitle_secondary" in request.files and request.files["vtt_subtitle_secondary"].filename:
            vtt_secondary_file = request.files["vtt_subtitle_secondary"]
            if vtt_secondary_file.filename.endswith(".vtt"):
                subtitle_vtt_secondary_content = vtt_secondary_file.read().decode("utf-8")

        nuevo_recurso_ = CursoRecurso(
            curso=course_code,
            seccion=seccion,
            tipo="mp3",
            nombre=form.nombre.data,
            descripcion=form.descripcion.data,
            requerido=form.requerido.data,
            indice=nuevo_indice,
            base_doc_url=audio.name,
            doc=audio_file,
            subtitle_vtt=subtitle_vtt_content,
            subtitle_vtt_secondary=subtitle_vtt_secondary_content,
            creado_por=current_user.usuario,
            descripcion_html_preformateado=html_preformateado,
        )
        try:
            database.session.add(nuevo_recurso_)
            database.session.commit()
            flash("RECURSO_AGREGADO", "success")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
        except OperationalError:
            flash(ERROR_AL_AGREGAR_CURSO, "warning")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
    else:
        return render_template(
            "learning/resources_new/nuevo_recurso_mp3.html", id_curso=course_code, id_seccion=seccion, form=form
        )


@course.route("/course/<course_code>/<seccion>/audio/<resource_id>/edit", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def editar_recurso_audio(course_code: str, seccion: str, resource_id: str) -> str | Response:
    """Formulario para editar un recurso de audio."""
    recurso = database.session.execute(
        select(CursoRecurso).filter_by(id=resource_id, curso=course_code, seccion=seccion)
    ).scalar_one_or_none()
    if not recurso or recurso.tipo != "mp3":
        flash("Recurso no encontrado.", "warning")
        return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))

    form = CursoRecursoArchivoAudio()

    if form.validate_on_submit() or request.method == "POST":
        recurso.nombre = form.nombre.data
        recurso.descripcion = form.descripcion.data
        recurso.requerido = form.requerido.data
        recurso.modificado_por = current_user.usuario

        # Handle HTML preformatted flag - only set if global config allows it
        config = database.session.execute(database.select(Configuracion)).scalars().first()
        if config and config.enable_html_preformatted_descriptions and hasattr(form, "descripcion_html_preformateado"):
            recurso.descripcion_html_preformateado = form.descripcion_html_preformateado.data or False
        else:
            recurso.descripcion_html_preformateado = False

        # Handle file replacement if a new audio file is uploaded
        if "audio" in request.files and request.files["audio"].filename:
            audio_filename = request.files["audio"].filename
            audio_ext = splitext(audio_filename or "")[1]
            audio_name = str(ULID()) + (audio_ext or "")
            audio_file = audio.save(request.files["audio"], folder=course_code, name=audio_name)
            recurso.base_doc_url = audio.name
            recurso.doc = audio_file

        # Handle VTT subtitle file upload
        if "vtt_subtitle" in request.files and request.files["vtt_subtitle"].filename:
            vtt_file = request.files["vtt_subtitle"]
            if vtt_file.filename.endswith(".vtt"):
                recurso.subtitle_vtt = vtt_file.read().decode("utf-8")

        # Handle secondary VTT subtitle file upload
        if "vtt_subtitle_secondary" in request.files and request.files["vtt_subtitle_secondary"].filename:
            vtt_secondary_file = request.files["vtt_subtitle_secondary"]
            if vtt_secondary_file.filename.endswith(".vtt"):
                recurso.subtitle_vtt_secondary = vtt_secondary_file.read().decode("utf-8")

        try:
            database.session.commit()
            flash("Recurso actualizado correctamente.", "success")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
        except OperationalError:
            flash("Hubo un error al actualizar el recurso.", "warning")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
    else:
        # Pre-populate form with existing data
        form.nombre.data = recurso.nombre
        form.descripcion.data = recurso.descripcion
        form.requerido.data = recurso.requerido
        form.descripcion_html_preformateado.data = recurso.descripcion_html_preformateado or False

        return render_template(
            "learning/resources_new/editar_recurso_mp3.html",
            id_curso=course_code,
            id_seccion=seccion,
            recurso=recurso,
            form=form,
        )


@course.route("/course/<course_code>/<seccion>/descargable/new", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def nuevo_recurso_descargable(course_code: str, seccion: str) -> str | Response:
    """Formulario para crear un nuevo recurso descargable."""
    # Check if file uploads are enabled by admin
    site_config = get_site_config()
    if not site_config.enable_file_uploads:
        flash("La subida de archivos descargables no está habilitada por el administrador.", "warning")
        return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))

    form = CursoRecursoArchivoDescargable()
    recursos = database.session.execute(select(func.count(CursoRecurso.id)).filter_by(seccion=seccion)).scalar()
    nuevo_indice = int((recursos or 0) + 1)

    if (form.validate_on_submit() or request.method == "POST") and "archivo" in request.files:
        uploaded_file = request.files["archivo"]

        # Validate file
        is_valid, error_msg = validate_downloadable_file(uploaded_file, site_config.max_file_size)
        if not is_valid:
            flash(error_msg, "warning")
            return render_template(
                "learning/resources_new/nuevo_recurso_descargable.html", id_curso=course_code, id_seccion=seccion, form=form
            )

        # Save file with original extension
        filename = uploaded_file.filename
        file_ext = splitext(filename or "")[1]
        file_name = str(ULID()) + (file_ext or "")

        try:
            saved_file = files.save(uploaded_file, folder=course_code, name=file_name)

            nuevo_recurso_ = CursoRecurso(
                curso=course_code,
                seccion=seccion,
                tipo="descargable",
                nombre=form.nombre.data,
                descripcion=form.descripcion.data,
                requerido=form.requerido.data,
                indice=nuevo_indice,
                base_doc_url=files.name,
                doc=saved_file,
                creado_por=current_user.usuario,
            )

            database.session.add(nuevo_recurso_)
            database.session.commit()
            flash(RECURSO_AGREGADO, "success")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))

        except UploadNotAllowed:
            flash("Tipo de archivo no permitido.", "warning")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
        except OperationalError:
            flash(ERROR_AL_AGREGAR_CURSO, "warning")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
    else:
        return render_template(
            "learning/resources_new/nuevo_recurso_descargable.html",
            id_curso=course_code,
            id_seccion=seccion,
            form=form,
            max_file_size=site_config.max_file_size,
        )


@course.route("/course/<course_code>/<seccion>/descargable/<resource_id>/edit", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def editar_recurso_descargable(course_code: str, seccion: str, resource_id: str) -> str | Response:
    """Formulario para editar un recurso descargable."""
    # Check if file uploads are enabled by admin
    site_config = get_site_config()
    if not site_config.enable_file_uploads:
        flash("La subida de archivos descargables no está habilitada por el administrador.", "warning")
        return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))

    recurso = database.session.execute(select(CursoRecurso).filter_by(id=resource_id)).scalar_one()
    form = CursoRecursoArchivoDescargable()

    if form.validate_on_submit() or request.method == "POST":
        if "archivo" in request.files and request.files["archivo"].filename:
            # New file uploaded
            uploaded_file = request.files["archivo"]

            # Validate file
            is_valid, error_msg = validate_downloadable_file(uploaded_file, site_config.max_file_size)
            if not is_valid:
                flash(error_msg, "warning")
                return render_template(
                    "learning/resources_new/editar_recurso_descargable.html",
                    id_curso=course_code,
                    id_seccion=seccion,
                    recurso=recurso,
                    form=form,
                    max_file_size=site_config.max_file_size,
                )

            # Save new file with original extension
            filename = uploaded_file.filename
            file_ext = splitext(filename or "")[1]
            file_name = str(ULID()) + (file_ext or "")

            try:
                saved_file = files.save(uploaded_file, folder=course_code, name=file_name)
                recurso.doc = saved_file
            except UploadNotAllowed:
                flash("Tipo de archivo no permitido.", "warning")
                return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))

        # Update resource metadata
        recurso.nombre = form.nombre.data
        recurso.descripcion = form.descripcion.data
        recurso.requerido = form.requerido.data
        recurso.modificado_por = current_user.usuario

        try:
            database.session.commit()
            flash(RECURSO_AGREGADO, "success")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
        except OperationalError:
            flash(ERROR_AL_AGREGAR_CURSO, "warning")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
    else:
        # Pre-populate form with existing data
        form.nombre.data = recurso.nombre
        form.descripcion.data = recurso.descripcion
        form.requerido.data = recurso.requerido

        return render_template(
            "learning/resources_new/editar_recurso_descargable.html",
            id_curso=course_code,
            id_seccion=seccion,
            recurso=recurso,
            form=form,
            max_file_size=site_config.max_file_size,
        )


@course.route("/course/<course_code>/<seccion>/html/new", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def nuevo_recurso_html(course_code: str, seccion: str) -> str | Response:
    """Formulario para crear un nuevo recurso tipo HTML externo."""
    form = CursoRecursoExternalCode()
    recursos = database.session.execute(select(func.count(CursoRecurso.id)).filter_by(seccion=seccion)).scalar()
    nuevo_indice = int((recursos or 0) + 1)
    if form.validate_on_submit() or request.method == "POST":
        # Get global configuration for HTML preformatted descriptions
        config = database.session.execute(database.select(Configuracion)).scalars().first()
        html_preformateado = False
        if config and config.enable_html_preformatted_descriptions and hasattr(form, "descripcion_html_preformateado"):
            html_preformateado = form.descripcion_html_preformateado.data or False

        nuevo_recurso_ = CursoRecurso(
            curso=course_code,
            seccion=seccion,
            tipo="html",
            nombre=form.nombre.data,
            descripcion=form.descripcion.data,
            requerido=form.requerido.data,
            external_code=form.html_externo.data,
            indice=nuevo_indice,
            creado_por=current_user.usuario,
            descripcion_html_preformateado=html_preformateado,
        )
        try:
            database.session.add(nuevo_recurso_)
            database.session.commit()
            flash("RECURSO_AGREGADO", "success")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
        except OperationalError:
            flash(ERROR_AL_AGREGAR_CURSO, "warning")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
    else:
        return render_template(
            "learning/resources_new/nuevo_recurso_html.html", id_curso=course_code, id_seccion=seccion, form=form
        )


@course.route("/course/<course_code>/<seccion>/html/<resource_id>/edit", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def editar_recurso_html(course_code: str, seccion: str, resource_id: str) -> str | Response:
    """Formulario para editar un recurso tipo HTML externo."""
    recurso = database.session.execute(
        select(CursoRecurso).filter_by(id=resource_id, curso=course_code, seccion=seccion)
    ).scalar_one_or_none()
    if not recurso or recurso.tipo != "html":
        flash("Recurso no encontrado.", "warning")
        return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))

    form = CursoRecursoExternalCode()

    if form.validate_on_submit() or request.method == "POST":
        recurso.nombre = form.nombre.data
        recurso.descripcion = form.descripcion.data
        recurso.requerido = form.requerido.data
        recurso.external_code = form.html_externo.data
        recurso.modificado_por = current_user.usuario

        # Handle HTML preformatted flag - only set if global config allows it
        config = database.session.execute(database.select(Configuracion)).scalars().first()
        if config and config.enable_html_preformatted_descriptions and hasattr(form, "descripcion_html_preformateado"):
            recurso.descripcion_html_preformateado = form.descripcion_html_preformateado.data or False
        else:
            recurso.descripcion_html_preformateado = False

        try:
            database.session.commit()
            flash("Recurso actualizado correctamente.", "success")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
        except OperationalError:
            flash("Hubo un error al actualizar el recurso.", "warning")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
    else:
        # Pre-populate form with existing data
        form.nombre.data = recurso.nombre
        form.descripcion.data = recurso.descripcion
        form.requerido.data = recurso.requerido
        form.html_externo.data = recurso.external_code
        form.descripcion_html_preformateado.data = recurso.descripcion_html_preformateado or False

        return render_template(
            "learning/resources_new/editar_recurso_html.html",
            id_curso=course_code,
            id_seccion=seccion,
            recurso=recurso,
            form=form,
        )


@course.route("/course/<course_code>/delete_logo")
@login_required
@perfil_requerido("instructor")
def elimina_logo(course_code: str) -> Response:
    """Elimina logotipo del curso."""
    from now_lms.db.tools import elimina_logo_perzonalizado_curso

    elimina_logo_perzonalizado_curso(course_code=course_code)
    return redirect(url_for("course.editar_curso", course_code=course_code))


# ---------------------------------------------------------------------------------------
# Slideshow Resource Routes
# ---------------------------------------------------------------------------------------
@course.route("/course/<course_code>/<seccion>/slides/new", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def nuevo_recurso_slideshow(course_code: str, seccion: str) -> str | Response:
    """Crear una nueva presentación de diapositivas."""
    form = SlideShowForm()
    if form.validate_on_submit():
        try:
            # Crear el recurso en CursoRecurso
            consulta_recursos = database.session.execute(
                select(func.count(CursoRecurso.id)).filter_by(seccion=seccion)
            ).scalar()
            nuevo_indice = int((consulta_recursos or 0) + 1)

            nuevo_recurso_obj = CursoRecurso(
                curso=course_code,
                seccion=seccion,
                tipo="slides",
                nombre=form.nombre.data,
                descripcion=form.descripcion.data,
                indice=nuevo_indice,
                publico=False,
                requerido="required",
            )
            database.session.add(nuevo_recurso_obj)
            database.session.flush()  # Para obtener el ID

            # Crear la presentación SlideShowResource
            slideshow = SlideShowResource(
                course_id=course_code, title=form.nombre.data, theme=form.theme.data, creado_por=current_user.usuario
            )
            database.session.add(slideshow)
            database.session.flush()

            # Agregar el ID del slideshow al recurso como referencia
            nuevo_recurso_obj.external_code = slideshow.id

            database.session.commit()
            flash(RECURSO_AGREGADO, "success")
            return redirect(url_for("course.editar_slideshow", course_code=course_code, slideshow_id=slideshow.id))

        except Exception as e:
            database.session.rollback()
            flash(f"Error al crear la presentación: {str(e)}", "error")

    return render_template(
        "learning/resources_new/nuevo_recurso_slides.html", id_curso=course_code, id_seccion=seccion, form=form
    )


@course.route("/course/<course_code>/slideshow/<slideshow_id>/edit", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def editar_slideshow(course_code: str, slideshow_id: str) -> str | Response:
    """Editar una presentación de diapositivas."""
    slideshow = database.session.get(SlideShowResource, slideshow_id)
    if not slideshow or slideshow.course_id != course_code:
        flash("Presentación no encontrada.", "error")
        return abort(404)

    # Obtener slides existentes
    slides = (
        database.session.execute(select(Slide).filter_by(slide_show_id=slideshow_id).order_by(Slide.order)).scalars().all()
    )

    if request.method == "POST":
        try:
            # Actualizar información del slideshow
            slideshow.title = request.form.get("title", slideshow.title)
            slideshow.theme = request.form.get("theme", slideshow.theme)
            slideshow.modificado_por = current_user.usuario

            # Procesar slides
            slide_count = int(request.form.get("slide_count", 0))

            # Eliminar slides que ya no existen
            existing_orders = []
            for i in range(slide_count):
                order = int(request.form.get(f"slide_{i}_order", i + 1))
                existing_orders.append(order)

            for slide in slides:
                if slide.order not in existing_orders:
                    database.session.delete(slide)

            # Actualizar o crear slides
            for i in range(slide_count):
                slide_title = request.form.get(f"slide_{i}_title", "")
                slide_content = request.form.get(f"slide_{i}_content", "")
                slide_order = int(request.form.get(f"slide_{i}_order", i + 1))
                slide_id = request.form.get(f"slide_{i}_id")

                if slide_title and slide_content:
                    # Sanitizar contenido
                    clean_content = sanitize_slide_content(slide_content)

                    if slide_id:
                        # Actualizar slide existente
                        existing_slide = database.session.get(Slide, slide_id)
                        if existing_slide is not None and existing_slide.slide_show_id == slideshow_id:
                            existing_slide.title = slide_title
                            existing_slide.content = clean_content
                            existing_slide.order = slide_order
                            existing_slide.modificado_por = current_user.usuario
                    else:
                        # Crear nuevo slide
                        new_slide = Slide(
                            slide_show_id=slideshow_id,
                            title=slide_title,
                            content=clean_content,
                            order=slide_order,
                            creado_por=current_user.usuario,
                        )
                        database.session.add(new_slide)

            database.session.commit()
            flash("Presentación actualizada correctamente.", "success")

        except Exception as e:
            database.session.rollback()
            flash(f"Error al actualizar la presentación: {str(e)}", "error")

        return redirect(url_for("course.editar_slideshow", course_code=course_code, slideshow_id=slideshow_id))

    return render_template(
        "learning/resources_new/editar_slideshow.html", slideshow=slideshow, slides=slides, course_code=course_code
    )


@course.route("/course/<course_code>/slideshow/<slideshow_id>/preview")
@login_required
def preview_slideshow(course_code: str, slideshow_id: str) -> str:
    """Previsualizar una presentación de diapositivas."""
    slideshow = database.session.get(SlideShowResource, slideshow_id)
    if not slideshow or slideshow.course_id != course_code:
        abort(404)

    slides = (
        database.session.execute(select(Slide).filter_by(slide_show_id=slideshow_id).order_by(Slide.order)).scalars().all()
    )

    return render_template(TEMPLATE_SLIDE_SHOW, slideshow=slideshow, slides=slides)


# ---------------------------------------------------------------------------------------
# Vistas auxiliares para servir el contenido de los cursos por tipo de recurso.
# - Enviar archivo.
# - Presentar un recurso HTML externo como iframe
# - Devolver una presentación de reveal.js como iframe
# - Devolver texto en markdown como HTML para usarlo en un iframe
# ---------------------------------------------------------------------------------------
@course.route("/course/<course_code>/files/<recurso_code>")
def recurso_file(course_code: str, recurso_code: str) -> Response:
    """Devuelve un archivo desde el sistema de archivos."""
    doc = (
        database.session.execute(
            select(CursoRecurso).filter(CursoRecurso.id == recurso_code, CursoRecurso.curso == course_code)
        )
        .scalars()
        .first()
    )
    config = current_app.upload_set_config.get(doc.base_doc_url)

    if current_user.is_authenticated:
        if (
            doc.publico
            or current_user.tipo == "admin"
            or verifica_estudiante_asignado_a_curso(course_code)
            or verifica_docente_asignado_a_curso(course_code)
        ):
            return send_from_directory(config.destination, doc.doc)
        return abort(403)
    return INICIO_SESION


@course.route("/course/<course_code>/vtt/<recurso_code>")
def recurso_vtt(course_code: str, recurso_code: str) -> Response:
    """Devuelve el contenido VTT de subtítulos para un recurso de audio."""
    doc = (
        database.session.execute(
            select(CursoRecurso).filter(CursoRecurso.id == recurso_code, CursoRecurso.curso == course_code)
        )
        .scalars()
        .first()
    )

    if not doc or not doc.subtitle_vtt:
        return abort(404)

    if current_user.is_authenticated:
        if doc.publico or current_user.tipo == "admin" or verifica_estudiante_asignado_a_curso(course_code):
            return Response(doc.subtitle_vtt, mimetype="text/vtt", headers={"Content-Type": "text/vtt; charset=utf-8"})
        return abort(403)
    return INICIO_SESION


@course.route("/course/<course_code>/vtt_secondary/<recurso_code>")
def recurso_vtt_secondary(course_code: str, recurso_code: str) -> Response:
    """Devuelve el contenido VTT de subtítulos secundarios para un recurso de audio."""
    doc = (
        database.session.execute(
            select(CursoRecurso).filter(CursoRecurso.id == recurso_code, CursoRecurso.curso == course_code)
        )
        .scalars()
        .first()
    )

    if not doc or not doc.subtitle_vtt_secondary:
        return abort(404)

    if current_user.is_authenticated:
        if doc.publico or current_user.tipo == "admin" or verifica_estudiante_asignado_a_curso(course_code):
            return Response(
                doc.subtitle_vtt_secondary, mimetype="text/vtt", headers={"Content-Type": "text/vtt; charset=utf-8"}
            )
        return abort(403)
    return INICIO_SESION


@course.route("/course/<course_code>/pdf_viewer/<recurso_code>")
def pdf_viewer(course_code: str, recurso_code: str) -> str | Response:
    """Renderiza el visor PDF.js para un recurso PDF."""
    recurso = (
        database.session.execute(
            select(CursoRecurso).filter(CursoRecurso.id == recurso_code, CursoRecurso.curso == course_code)
        )
        .scalars()
        .first()
    )

    if not recurso:
        return abort(404)

    if current_user.is_authenticated:
        if (
            recurso.publico
            or current_user.tipo == "admin"
            or verifica_estudiante_asignado_a_curso(course_code)
            or verifica_docente_asignado_a_curso(course_code)
        ):
            return render_template("learning/resources/pdf_viewer.html", recurso=recurso)
        return abort(403)
    return INICIO_SESION


@course.route("/course/<course_code>/external_code/<recurso_code>")
def external_code(course_code: str, recurso_code: str) -> str | Response:
    """Devuelve un archivo desde el sistema de archivos."""
    recurso = (
        database.session.execute(
            select(CursoRecurso).filter(CursoRecurso.id == recurso_code, CursoRecurso.curso == course_code)
        )
        .scalars()
        .first()
    )

    if current_user.is_authenticated:
        if recurso.publico or current_user.tipo == "admin" or verifica_estudiante_asignado_a_curso(course_code):
            return recurso.external_code

        return abort(403)
    return INICIO_SESION


@course.route("/course/slide_show/<recurso_code>")
def slide_show(recurso_code: str) -> str:
    """Renderiza una presentación de diapositivas."""
    # Primero buscar el recurso para obtener la referencia al slideshow
    recurso = database.session.execute(select(CursoRecurso).filter(CursoRecurso.id == recurso_code)).scalars().first()

    if not recurso:
        abort(404)

    if recurso.external_code:
        # Usar nuevo modelo SlideShowResource
        slideshow = database.session.get(SlideShowResource, recurso.external_code)
        if slideshow:
            slides = (
                database.session.execute(select(Slide).filter_by(slide_show_id=slideshow.id).order_by(Slide.order))
                .scalars()
                .all()
            )
            return render_template(TEMPLATE_SLIDE_SHOW, slideshow=slideshow, slides=slides, resource=recurso)

    # Fallback a modelos legacy para compatibilidad
    legacy_slide = (
        database.session.execute(select(CursoRecursoSlideShow).filter(CursoRecursoSlideShow.recurso == recurso_code))
        .scalars()
        .first()
    )
    legacy_slides = (
        database.session.execute(select(CursoRecursoSlides).filter(CursoRecursoSlides.recurso == recurso_code)).scalars().all()
    )

    if legacy_slide:
        return render_template(TEMPLATE_SLIDE_SHOW, resource=legacy_slide, slides=legacy_slides, legacy=True)

    # No se encontró presentación
    flash("Presentación no encontrada.", "error")
    abort(404)


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
# Coupon Management Functions
# ---------------------------------------------------------------------------------------


def _validate_coupon_permissions(course_code: str, user) -> tuple[object | None, str | None]:
    """Validate that user can manage coupons for this course."""
    course_obj = database.session.execute(select(Curso).filter_by(codigo=course_code)).scalars().first()
    if not course_obj:
        return None, "Curso no encontrado"

    if not course_obj.pagado:
        return None, "Los cupones solo están disponibles para cursos pagados"

    # Check if user is instructor for this course
    instructor_assignment = (
        database.session.execute(select(DocenteCurso).filter_by(curso=course_code, usuario=user.usuario, vigente=True))
        .scalars()
        .first()
    )

    if not instructor_assignment and user.tipo != "admin":
        return None, "Solo el instructor del curso puede gestionar cupones"

    return course_obj, None


def _validate_coupon_for_enrollment(
    course_code: str, coupon_code: str, user
) -> tuple[object | None, object | None, str | None]:
    """Validate coupon for enrollment use."""
    if not coupon_code:
        return None, None, "No se proporcionó código de cupón"

    # Find coupon
    coupon = (
        database.session.execute(select(Coupon).filter_by(course_id=course_code, code=coupon_code.upper())).scalars().first()
    )

    if not coupon:
        return None, None, "Código de cupón inválido"

    # Check if user is already enrolled
    existing_enrollment = (
        database.session.execute(select(EstudianteCurso).filter_by(curso=course_code, usuario=user.usuario, vigente=True))
        .scalars()
        .first()
    )

    if existing_enrollment:
        return None, None, "No puede aplicar cupón - ya está inscrito en el curso"

    # Validate coupon
    is_valid, error_message = coupon.is_valid()
    if not is_valid:
        return None, None, error_message

    return coupon, None, None


@course.route("/course/<course_code>/coupons/")
@login_required
@perfil_requerido("instructor")
def list_coupons(course_code: str) -> str | Response:
    """Lista cupones existentes para un curso."""
    course_obj, error = _validate_coupon_permissions(course_code, current_user)
    if error:
        flash(error, "warning")
        return redirect(url_for("course.administrar_curso", course_code=course_code))

    coupons = (
        database.session.execute(select(Coupon).filter_by(course_id=course_code).order_by(Coupon.timestamp.desc()))
        .scalars()
        .all()
    )

    return render_template("learning/curso/coupons/list.html", curso=course_obj, coupons=coupons)


@course.route("/course/<course_code>/coupons/new", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def create_coupon(course_code: str) -> str | Response:
    """Crear nuevo cupón para un curso."""
    course_obj, error = _validate_coupon_permissions(course_code, current_user)
    if error:
        flash(error, "warning")
        return redirect(url_for("course.administrar_curso", course_code=course_code))

    form = CouponForm()

    if form.validate_on_submit():
        # Check if coupon code already exists for this course
        existing = (
            database.session.execute(select(Coupon).filter_by(course_id=course_code, code=form.code.data.upper()))
            .scalars()
            .first()
        )

        if existing:
            flash("Ya existe un cupón con este código para este curso", "warning")
            return render_template(TEMPLATE_COUPON_CREATE, curso=curso, form=form)

        # Validate discount value
        if form.discount_type.data == "percentage" and form.discount_value.data > 100:
            flash("El descuento porcentual no puede ser mayor al 100%", "warning")
            return render_template(TEMPLATE_COUPON_CREATE, curso=curso, form=form)

        if form.discount_type.data == "fixed" and form.discount_value.data > curso.precio:
            flash("El descuento fijo no puede ser mayor al precio del curso", "warning")
            return render_template(TEMPLATE_COUPON_CREATE, curso=curso, form=form)

        try:
            coupon = Coupon(
                course_id=course_code,
                code=form.code.data.upper(),
                discount_type=form.discount_type.data,
                discount_value=float(form.discount_value.data),
                max_uses=form.max_uses.data if form.max_uses.data else None,
                expires_at=form.expires_at.data if form.expires_at.data else None,
                created_by=current_user.usuario,
            )

            database.session.add(coupon)
            database.session.commit()

            flash("Cupón creado exitosamente", "success")
            return redirect(url_for(ROUTE_LIST_COUPONS, course_code=course_code))

        except Exception as e:
            database.session.rollback()
            flash("Error al crear el cupón", "danger")
            log.error(f"Error creating coupon: {e}")

    return render_template(TEMPLATE_COUPON_CREATE, curso=course_obj, form=form)


@course.route("/course/<course_code>/coupons/<coupon_id>/edit", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def edit_coupon(course_code: str, coupon_id: int) -> str | Response:
    """Editar cupón existente."""
    course_obj, error = _validate_coupon_permissions(course_code, current_user)
    if error:
        flash(error, "warning")
        return redirect(url_for("course.administrar_curso", course_code=course_code))

    coupon = database.session.execute(select(Coupon).filter_by(id=coupon_id, course_id=course_code)).scalars().first()
    if not coupon:
        flash("Cupón no encontrado", "warning")
        return redirect(url_for(ROUTE_LIST_COUPONS, course_code=course_code))

    form = CouponForm(obj=coupon)

    if form.validate_on_submit():
        # Check if coupon code already exists for this course (excluding current coupon)
        existing = (
            database.session.execute(
                select(Coupon).filter(
                    Coupon.course_id == course_code, Coupon.code == form.code.data.upper(), Coupon.id != coupon_id
                )
            )
            .scalars()
            .first()
        )

        if existing:
            flash("Ya existe un cupón con este código para este curso", "warning")
            return render_template(TEMPLATE_COUPON_EDIT, curso=curso, coupon=coupon, form=form)

        # Validate discount value
        if form.discount_type.data == "percentage" and form.discount_value.data > 100:
            flash("El descuento porcentual no puede ser mayor al 100%", "warning")
            return render_template(TEMPLATE_COUPON_EDIT, curso=course_obj, coupon=coupon, form=form)

        if form.discount_type.data == "fixed" and form.discount_value.data > course_obj.precio:
            flash("El descuento fijo no puede ser mayor al precio del curso", "warning")
            return render_template(TEMPLATE_COUPON_EDIT, curso=course_obj, coupon=coupon, form=form)

        try:
            coupon.code = form.code.data.upper()
            coupon.discount_type = form.discount_type.data
            coupon.discount_value = float(form.discount_value.data)
            coupon.max_uses = form.max_uses.data if form.max_uses.data else None
            coupon.expires_at = form.expires_at.data if form.expires_at.data else None
            coupon.modificado_por = current_user.usuario

            database.session.commit()

            flash("Cupón actualizado exitosamente", "success")
            return redirect(url_for(ROUTE_LIST_COUPONS, course_code=course_code))

        except Exception as e:
            database.session.rollback()
            flash("Error al actualizar el cupón", "danger")
            log.error(f"Error updating coupon: {e}")

    return render_template(TEMPLATE_COUPON_EDIT, curso=course_obj, coupon=coupon, form=form)


@course.route("/course/<course_code>/coupons/<coupon_id>/delete", methods=["POST"])
@login_required
@perfil_requerido("instructor")
def delete_coupon(course_code: str, coupon_id: int) -> Response:
    """Eliminar cupón."""
    _, error = _validate_coupon_permissions(course_code, current_user)
    if error:
        flash(error, "warning")
        return redirect(url_for("course.administrar_curso", course_code=course_code))

    coupon = database.session.execute(select(Coupon).filter_by(id=coupon_id, course_id=course_code)).scalars().first()
    if not coupon:
        flash("Cupón no encontrado", "warning")
        return redirect(url_for(ROUTE_LIST_COUPONS, course_code=course_code))

    try:
        database.session.delete(coupon)
        database.session.commit()
        flash("Cupón eliminado exitosamente", "success")
    except Exception as e:
        database.session.rollback()
        flash("Error al eliminar el cupón", "danger")
        log.error(f"Error deleting coupon: {e}")

    return redirect(url_for(ROUTE_LIST_COUPONS, course_code=course_code))


@course.route("/course/<course_code>/resource/meet/<codigo>/calendar.ics")
@login_required
def download_meet_calendar(course_code: str, codigo: str) -> Response:
    """Download ICS calendar file for a meet resource."""
    # Get the meet resource
    recurso = (
        database.session.execute(
            database.select(CursoRecurso).filter(
                CursoRecurso.id == codigo, CursoRecurso.curso == course_code, CursoRecurso.tipo == "meet"
            )
        )
        .scalars()
        .first()
    )

    if not recurso:
        abort(404)

    # Check permissions
    course_obj = database.session.execute(database.select(Curso).filter(Curso.codigo == course_code)).scalars().first()
    if not course_obj:
        abort(404)

    # Verify user has access to this course/resource
    if current_user.is_authenticated:
        if current_user.tipo in ("admin", "instructor"):
            show_resource = True
        elif current_user.tipo == "student" and verifica_estudiante_asignado_a_curso(course_code):
            show_resource = True
        else:
            show_resource = False
    else:
        show_resource = False

    if not (show_resource or recurso.publico):
        abort(403)

    # Generate ICS content
    ics_content = _generate_meet_ics_content(recurso, course_obj)

    # Safe filename
    filename = f"meet-{recurso.nombre[:20].replace(' ', '-')}-{recurso.id}.ics"

    return Response(
        ics_content,
        mimetype="text/calendar",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@course.route("/course/<course_code>/resource/meet/<codigo>/google-calendar")
@login_required
def google_calendar_link(course_code: str, codigo: str) -> Response:
    """Redirect to Google Calendar to add meet event."""
    from urllib.parse import quote

    # Get the meet resource (reuse permission logic)
    recurso = (
        database.session.execute(
            database.select(CursoRecurso).filter(
                CursoRecurso.id == codigo, CursoRecurso.curso == course_code, CursoRecurso.tipo == "meet"
            )
        )
        .scalars()
        .first()
    )

    if not recurso:
        abort(404)

    course_obj = database.session.execute(database.select(Curso).filter(Curso.codigo == course_code)).scalars().first()
    if not course_obj:
        abort(404)

    # Verify user has access to this course/resource
    if current_user.is_authenticated:
        if current_user.tipo in ("admin", "instructor"):
            show_resource = True
        elif current_user.tipo == "student" and verifica_estudiante_asignado_a_curso(course_code):
            show_resource = True
        else:
            show_resource = False
    else:
        show_resource = False

    if not (show_resource or recurso.publico):
        abort(403)

    # Generate Google Calendar URL
    if recurso.fecha and recurso.hora_inicio:
        start_datetime = datetime.combine(recurso.fecha, recurso.hora_inicio)
        if recurso.hora_fin:
            end_datetime = datetime.combine(recurso.fecha, recurso.hora_fin)
        else:
            end_datetime = start_datetime + timedelta(hours=1)

        start_str = start_datetime.strftime("%Y%m%dT%H%M%S")
        end_str = end_datetime.strftime("%Y%m%dT%H%M%S")

        # Build description
        description_parts = [f"Curso: {course_obj.nombre}"]
        if recurso.descripcion:
            description_parts.append("")
            description_parts.append(recurso.descripcion)
        if recurso.url:
            description_parts.append("")
            description_parts.append(f"Enlace: {recurso.url}")

        description = "\n".join(description_parts)

        google_url = (
            f"https://calendar.google.com/calendar/render?action=TEMPLATE"
            f"&text={quote(recurso.nombre)}"
            f"&dates={start_str}/{end_str}"
            f"&details={quote(description)}"
            f"&location={quote(recurso.notes or 'En línea')}"
        )

        return redirect(google_url)
    flash("No se puede crear el evento: faltan datos de fecha/hora", "error")
    return redirect(url_for("course.ver_recurso", course_code=course_code, codigo=codigo))


@course.route("/course/<course_code>/resource/meet/<codigo>/outlook-calendar")
@login_required
def outlook_calendar_link(course_code: str, codigo: str) -> str | Response:
    """Redirect to Outlook Calendar to add meet event."""
    from urllib.parse import quote

    # Get the meet resource (reuse permission logic)
    recurso = (
        database.session.execute(
            database.select(CursoRecurso).filter(
                CursoRecurso.id == codigo, CursoRecurso.curso == course_code, CursoRecurso.tipo == "meet"
            )
        )
        .scalars()
        .first()
    )

    if not recurso:
        abort(404)

    course_obj = database.session.execute(database.select(Curso).filter(Curso.codigo == course_code)).scalars().first()
    if not course_obj:
        abort(404)

    # Verify user has access to this course/resource
    if current_user.is_authenticated:
        if current_user.tipo in ("admin", "instructor"):
            show_resource = True
        elif current_user.tipo == "student" and verifica_estudiante_asignado_a_curso(course_code):
            show_resource = True
        else:
            show_resource = False
    else:
        show_resource = False

    if not (show_resource or recurso.publico):
        abort(403)

    # Generate Outlook Calendar URL
    if recurso.fecha and recurso.hora_inicio:
        start_datetime = datetime.combine(recurso.fecha, recurso.hora_inicio)
        if recurso.hora_fin:
            end_datetime = datetime.combine(recurso.fecha, recurso.hora_fin)
        else:
            end_datetime = start_datetime + timedelta(hours=1)

        start_str = start_datetime.strftime("%Y%m%dT%H%M%S")
        end_str = end_datetime.strftime("%Y%m%dT%H%M%S")

        # Build description
        description_parts = [f"Curso: {course_obj.nombre}"]
        if recurso.descripcion:
            description_parts.append("")
            description_parts.append(recurso.descripcion)
        if recurso.url:
            description_parts.append("")
            description_parts.append(f"Enlace: {recurso.url}")

        description = "\n".join(description_parts)

        outlook_url = (
            f"https://outlook.live.com/calendar/0/deeplink/compose?"
            f"subject={quote(recurso.nombre)}"
            f"&startdt={start_str}"
            f"&enddt={end_str}"
            f"&body={quote(description)}"
            f"&location={quote(recurso.notes or 'En línea')}"
        )

        return redirect(outlook_url)
    flash("No se puede crear el evento: faltan datos de fecha/hora", "error")
    return redirect(url_for("course.ver_recurso", course_code=course_code, codigo=codigo))


def _generate_meet_ics_content(recurso: Any, course_obj: Any) -> str:
    """Generate ICS calendar content for a meet resource."""
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//NOW LMS//Meet Calendar//EN", "CALSCALE:GREGORIAN", "METHOD:PUBLISH"]

    # Combine date and time for start and end
    if recurso.fecha and recurso.hora_inicio:
        start_datetime = datetime.combine(recurso.fecha, recurso.hora_inicio)
        if recurso.hora_fin:
            end_datetime = datetime.combine(recurso.fecha, recurso.hora_fin)
        else:
            # Default to 1 hour duration if no end time
            end_datetime = start_datetime + timedelta(hours=1)
    else:
        # Fallback if no date/time specified
        return "BEGIN:VCALENDAR\r\nVERSION:2.0\r\nEND:VCALENDAR\r\n"

    # Convert to UTC for proper timezone handling (assuming local timezone is desired)
    # For better compatibility, we'll use local time with proper floating time format
    start_dt = start_datetime.strftime("%Y%m%dT%H%M%S")
    end_dt = end_datetime.strftime("%Y%m%dT%H%M%S")
    created_dt = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    # Build description with proper newlines
    description_parts = [f"Curso: {course_obj.nombre}"]
    if recurso.descripcion:
        description_parts.append("")  # Empty line
        description_parts.append(recurso.descripcion)
    if recurso.url:
        description_parts.append("")  # Empty line
        description_parts.append(f"Enlace: {recurso.url}")

    # Join with newlines and then escape for ICS format
    description = _escape_ics_text("\n".join(description_parts))

    title = _escape_ics_text(recurso.nombre)
    location = _escape_ics_text(recurso.notes or "En línea")

    lines.extend(
        [
            "BEGIN:VEVENT",
            f"UID:{recurso.id}@nowlms.local",
            f"DTSTART:{start_dt}",
            f"DTEND:{end_dt}",
            f"DTSTAMP:{created_dt}",
            f"SUMMARY:{title}",
            f"DESCRIPTION:{description}",
            f"LOCATION:{location}",
            "STATUS:CONFIRMED",
            "END:VEVENT",
        ]
    )

    lines.append("END:VCALENDAR")
    return "\r\n".join(lines)


def _escape_ics_text(text: str | None) -> str:
    """Escape text for ICS format."""
    if not text:
        return ""
    return text.replace("\\", "\\\\").replace(",", "\\,").replace(";", "\\;").replace("\n", "\\n")


@course.route("/course/<course_code>/section/<section_id>/new_evaluation")
@login_required
@perfil_requerido("instructor")
def new_evaluation_from_section(course_code: str, section_id: str) -> Response:
    """Create a new evaluation for a course section from section actions."""
    # Redirect to the existing instructor profile route for evaluation creation
    return redirect(url_for("instructor_profile.new_evaluation", course_code=course_code, section_id=section_id))


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

            # Create course progress index
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


# ---------------------------------------------------------------------------------------
# Course Library Routes
# ---------------------------------------------------------------------------------------
@course.route("/course/<course_code>/library")
@login_required
@perfil_requerido("instructor")
def course_library(course_code: str) -> str:
    """View course library files."""
    # Verify course exists and user has access
    _curso = database.session.execute(database.select(Curso).filter_by(codigo=course_code)).scalar_one_or_none()
    if not _curso:
        abort(404)

    # Check if current user is instructor or admin
    if current_user.tipo != "admin":
        instructor_assignment = database.session.execute(
            database.select(DocenteCurso).filter_by(curso=course_code, usuario=current_user.usuario)
        ).scalar_one_or_none()
        if not instructor_assignment:
            abort(403)

    # Get library files from database
    library_files_db = (
        database.session.execute(database.select(CourseLibrary).filter_by(curso=course_code).order_by(CourseLibrary.nombre))
        .scalars()
        .all()
    )

    # Create a mapping of filenames to database records
    db_files_map = {file_record.filename: file_record for file_record in library_files_db}

    # Get physical files from library directory
    library_path = get_course_library_path(course_code)
    physical_files = set()
    if path.exists(library_path):
        for filename in listdir(library_path):
            file_path = path.join(library_path, filename)
            if path.isfile(file_path):
                physical_files.add(filename)

    library_files = []

    # Add files that exist in database (may or may not exist physically)
    for file_record in library_files_db:
        library_files.append(
            {
                "id": file_record.id,
                "name": file_record.filename,
                "display_name": file_record.nombre,
                "description": file_record.descripcion,
                "size": file_record.file_size,
                "modified": file_record.modificado or file_record.timestamp,
                "url": url_for("course.serve_library_file", course_code=course_code, filename=file_record.filename),
                "has_db_record": True,
                "file_exists": file_record.filename in physical_files,
            }
        )

    # Add physical files that don't have database records (manually uploaded)
    for filename in physical_files:
        if filename not in db_files_map:  # Only add if not already in database
            file_path = path.join(library_path, filename)
            file_stat = stat(file_path)
            library_files.append(
                {
                    "id": None,  # No database record
                    "name": filename,
                    "display_name": filename,  # Use filename as display name
                    "description": _("Archivo subido manualmente"),  # Manual upload indicator
                    "size": file_stat.st_size,
                    "modified": datetime.fromtimestamp(file_stat.st_mtime),
                    "url": url_for("course.serve_library_file", course_code=course_code, filename=filename),
                    "has_db_record": False,
                    "file_exists": True,
                }
            )

    # Sort by display name
    library_files.sort(key=lambda x: x["display_name"].lower())

    return render_template("learning/curso/library.html", curso=_curso, library_files=library_files)


@course.route("/course/<course_code>/library/new", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def upload_library_file(course_code: str) -> str | Response:
    """Upload a file to the course library."""
    # Check if file uploads are enabled by admin
    site_config = get_site_config()
    if not site_config.enable_file_uploads:
        flash("La subida de archivos no está habilitada por el administrador.", "warning")
        return redirect(url_for("course.course_library", course_code=course_code))

    # Verify course exists and user has access
    _curso = database.session.execute(database.select(Curso).filter_by(codigo=course_code)).scalar_one_or_none()
    if not _curso:
        abort(404)

    # Check if current user is instructor or admin
    if current_user.tipo != "admin":
        instructor_assignment = database.session.execute(
            database.select(DocenteCurso).filter_by(curso=course_code, usuario=current_user.usuario)
        ).scalar_one_or_none()
        if not instructor_assignment:
            abort(403)

    form = CursoLibraryFileForm()

    if (form.validate_on_submit() or request.method == "POST") and "archivo" in request.files:
        uploaded_file = request.files["archivo"]

        # Validate file
        is_valid, error_msg = validate_downloadable_file(uploaded_file, site_config.max_file_size)
        if not is_valid:
            flash(error_msg, "warning")
            return render_template(
                "learning/curso/library_upload.html", curso=_curso, form=form, max_file_size=site_config.max_file_size
            )

        # Sanitize filename
        original_filename = uploaded_file.filename or ""
        sanitized_filename = sanitize_filename(original_filename)

        if not sanitized_filename:
            flash("Nombre de archivo inválido.", "warning")
            return render_template(
                "learning/curso/library_upload.html", curso=_curso, form=form, max_file_size=site_config.max_file_size
            )

        try:
            # Ensure library directory exists
            library_path = ensure_course_library_directory(course_code)

            # Check if file already exists in database
            existing_file = database.session.execute(
                database.select(CourseLibrary).filter_by(curso=course_code, filename=sanitized_filename)
            ).scalar_one_or_none()

            if existing_file:
                flash(f"Ya existe un archivo con el nombre '{sanitized_filename}' en la biblioteca.", "warning")
                return render_template(
                    "learning/curso/library_upload.html", curso=_curso, form=form, max_file_size=site_config.max_file_size
                )

            # Save file to filesystem
            destination_path = path.join(library_path, sanitized_filename)
            uploaded_file.save(destination_path)

            # Get file size
            file_size = uploaded_file.content_length or path.getsize(destination_path)

            # Create database record
            library_file = CourseLibrary(
                curso=course_code,
                filename=sanitized_filename,
                original_filename=original_filename,
                nombre=form.nombre.data,
                descripcion=form.descripcion.data,
                file_size=file_size,
                mime_type=uploaded_file.content_type,
                creado_por=current_user.usuario,
            )

            database.session.add(library_file)
            database.session.commit()

            flash(f"Archivo '{sanitized_filename}' subido exitosamente a la biblioteca del curso.", "success")
            return redirect(url_for("course.course_library", course_code=course_code))

        except Exception as e:
            database.session.rollback()
            # Try to clean up file if it was saved but database failed
            try:
                destination_path = path.join(library_path, sanitized_filename)
                if path.exists(destination_path):
                    path.remove(destination_path)
            except Exception:
                pass  # Ignore cleanup errors

            flash(f"Error al subir el archivo: {str(e)}", "error")
            return render_template(
                "learning/curso/library_upload.html", curso=_curso, form=form, max_file_size=site_config.max_file_size
            )

    return render_template(
        "learning/curso/library_upload.html", curso=_curso, form=form, max_file_size=site_config.max_file_size
    )


@course.route("/course/<course_code>/library/file/<filename>")
@login_required
def serve_library_file(course_code: str, filename: str) -> Response:
    """Serve a file from the course library."""
    # Verify course exists and user has access (instructor or enrolled student)
    _curso = database.session.execute(database.select(Curso).filter_by(codigo=course_code)).scalar_one_or_none()
    if not _curso:
        abort(404)

    # Check access: admin, instructor, or enrolled student
    has_access = False
    if current_user.tipo == "admin":
        has_access = True
    else:
        # Check if instructor
        instructor_assignment = database.session.execute(
            database.select(DocenteCurso).filter_by(curso=course_code, usuario=current_user.usuario)
        ).scalar_one_or_none()
        if instructor_assignment:
            has_access = True
        else:
            # Check if enrolled student
            student_enrollment = database.session.execute(
                database.select(EstudianteCurso).filter_by(curso=course_code, usuario=current_user.usuario, vigente=True)
            ).scalar_one_or_none()
            if student_enrollment:
                has_access = True

    if not has_access:
        abort(403)

    # Sanitize filename to prevent directory traversal
    safe_filename = path.basename(filename)
    library_path = get_course_library_path(course_code)
    file_path = path.join(library_path, safe_filename)

    # Check if file exists
    if not path.exists(file_path) or not path.isfile(file_path):
        abort(404)

    try:
        return send_from_directory(library_path, safe_filename, as_attachment=True)
    except Exception:
        abort(404)


@course.route("/course/<course_code>/library/delete/<file_id>", methods=["POST"])
@login_required
@perfil_requerido("instructor")
def delete_library_file(course_code: str, file_id: str) -> Response:
    """Delete a file from the course library."""
    # Verify course exists and user has access
    _curso = database.session.execute(database.select(Curso).filter_by(codigo=course_code)).scalar_one_or_none()
    if not _curso:
        abort(404)

    # Check if current user is instructor or admin
    if current_user.tipo != "admin":
        instructor_assignment = database.session.execute(
            database.select(DocenteCurso).filter_by(curso=course_code, usuario=current_user.usuario)
        ).scalar_one_or_none()
        if not instructor_assignment:
            abort(403)

    # Find the library file record
    library_file = database.session.execute(
        database.select(CourseLibrary).filter_by(id=file_id, curso=course_code)
    ).scalar_one_or_none()

    if not library_file:
        flash(_("Archivo no encontrado en la biblioteca."), "warning")
        return redirect(url_for("course.course_library", course_code=course_code))

    try:
        # Delete the physical file
        library_path = get_course_library_path(course_code)
        file_path = path.join(library_path, library_file.filename)

        if path.exists(file_path):
            remove(file_path)

        # Delete the database record
        database.session.delete(library_file)
        database.session.commit()

        flash(_("Archivo eliminado exitosamente de la biblioteca."), "success")

    except Exception as e:
        database.session.rollback()
        flash(f"Error al eliminar el archivo: {str(e)}", "error")

    return redirect(url_for("course.course_library", course_code=course_code))
