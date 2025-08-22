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
from collections import OrderedDict
from datetime import datetime, timezone
from os.path import splitext

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------
from bleach import clean, linkify
from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, send_from_directory, url_for
from flask_login import current_user, login_required
from flask_uploads import UploadNotAllowed
from markdown import markdown
from sqlalchemy import delete, func
from sqlalchemy.exc import OperationalError
from ulid import ULID

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
from now_lms.cache import cache, no_guardar_en_cache_global
from now_lms.calendar_utils import create_events_for_student_enrollment, update_meet_resource_events
from now_lms.config import DESARROLLO, DIRECTORIO_PLANTILLAS, audio, files, images
from now_lms.db import (
    Categoria,
    CategoriaCurso,
    Certificacion,
    Coupon,
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
)
from now_lms.forms import (
    CouponApplicationForm,
    CouponForm,
    CurseForm,
    CursoRecursoArchivoAudio,
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
from now_lms.logs import log
from now_lms.misc import CURSO_NIVEL, HTML_TAGS, INICIO_SESION, TIPOS_RECURSOS, sanitize_slide_content
from now_lms.themes import get_course_list_template, get_course_view_template

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


# ---------------------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------------------
def markdown2html(text):
    """Convierte texto en markdown a HTML."""
    allowed_tags = HTML_TAGS
    allowed_attrs = {"*": ["class"], "a": ["href", "rel"], "img": ["src", "alt"]}

    html = markdown(text)
    html_limpio = clean(linkify(html), tags=allowed_tags, attributes=allowed_attrs)

    return html_limpio


course = Blueprint("course", __name__, template_folder=DIRECTORIO_PLANTILLAS)


@course.route("/course/<course_code>/view")
@cache.cached(unless=no_guardar_en_cache_global)
def curso(course_code):
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
            acceso = database.session.execute(_consulta).scalars().first()
            if acceso:
                editable = True
            else:
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


def _crear_indice_avance_curso(course_code):
    """Crea el índice de avance del curso."""
    from now_lms.db import CursoRecurso, CursoRecursoAvance

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
def course_enroll(course_code):
    """Pagina para inscribirse a un curso."""
    from now_lms.db import EstudianteCurso
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

    if form.validate_on_submit() or request.method == "POST":
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
            except OperationalError:  # pragma: no cover
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
            except OperationalError:  # pragma: no cover
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
            except OperationalError:  # pragma: no cover
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
@cache.cached(unless=no_guardar_en_cache_global)
def tomar_curso(course_code):
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
            user_has_paid = enrollment and enrollment.pago

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
    else:
        return redirect(url_for(VISTA_CURSOS, course_code=course_code))


@course.route("/course/<course_code>/moderate")
@login_required
@perfil_requerido("moderator")
@cache.cached(unless=no_guardar_en_cache_global)
def moderar_curso(course_code):
    """Pagina principal del curso."""
    if current_user.tipo == "moderator" or current_user.tipo == "admin":
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
    else:
        return redirect(url_for(VISTA_CURSOS, course_code=course_code))


@course.route("/course/<course_code>/admin")
@login_required
@perfil_requerido("instructor")
@cache.cached(unless=no_guardar_en_cache_global)
def administrar_curso(course_code):
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
def nuevo_curso():
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
            asignar_curso_a_instructor(curso_codigo=form.codigo.data, usuario_id=current_user.usuario)
            if "logo" in request.files:
                logo = request.files["logo"]
                logo_name = logo.filename
                logo_data = splitext(logo_name)
                logo_ext = logo_data[1]
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
                except UploadNotAllowed:  # pragma: no cover
                    log.warning("Could not update profile photo.")
                    database.session.rollback()
                except AttributeError:  # pragma: no cover
                    log.warning("Could not update profile photo.")
                    database.session.rollback()
            database.session.commit()
            flash("Curso creado exitosamente.", "success")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=form.codigo.data))
        except OperationalError:  # pragma: no cover
            flash("Hubo en error al crear su curso.", "warning")
            return redirect("/instructor")
    else:  # pragma: no cover
        return render_template("learning/nuevo_curso.html", form=form, curso=None, edit=False)


@course.route("/course/<course_code>/edit", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def editar_curso(course_code):
    """Editar pagina del curso."""
    form = CurseForm()
    form.plantilla_certificado.choices = generate_template_choices()
    form.categoria.choices = generate_category_choices()
    form.etiquetas.choices = generate_tag_choices()

    curso_a_editar = database.session.execute(select(Curso).filter_by(codigo=course_code)).scalars().first()

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
    curso_url = url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code)
    if form.validate_on_submit() or request.method == "POST":
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
            curso_a_editar.modificado = datetime.now(timezone.utc)
            curso_a_editar.modificado_por = current_user.usuario

            # Update category assignment
            # First remove existing category assignment
            database.session.execute(delete(CategoriaCurso).where(CategoriaCurso.curso == course_code))

            # Add new category if selected
            if form.categoria.data:
                categoria_curso = CategoriaCurso(curso=course_code, categoria=form.categoria.data)
                database.session.add(categoria_curso)

            # Update tag assignments
            # First remove existing tag assignments
            database.session.execute(delete(EtiquetaCurso).where(EtiquetaCurso.curso == course_code))

            # Add new tags if selected
            if form.etiquetas.data:
                for etiqueta_id in form.etiquetas.data:
                    etiqueta_curso = EtiquetaCurso(curso=course_code, etiqueta=etiqueta_id)
                    database.session.add(etiqueta_curso)

            database.session.commit()

            if "logo" in request.files:
                logo = request.files["logo"]
                logo_name = logo.filename
                logo_data = splitext(logo_name)
                logo_ext = logo_data[1]
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
                except UploadNotAllowed:  # pragma: no cover
                    log.warning("Could not update profile photo.")
                    database.session.rollback()
                except AttributeError:  # pragma: no cover
                    log.warning("Could not update profile photo.")
                    database.session.rollback()
            flash("Curso actualizado exitosamente.", "success")
            return redirect(curso_url)

        except OperationalError:  # pragma: no cover
            flash("Hubo en error al actualizar el curso.", "warning")
            return redirect(curso_url)

    return render_template("learning/nuevo_curso.html", form=form, curso=curso_a_editar, edit=True)


@course.route("/course/<course_code>/new_seccion", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def nuevo_seccion(course_code):
    """Formulario para crear una nueva sección en el curso."""
    # Las seccion son contenedores de recursos.
    form = CursoSeccionForm()
    if form.validate_on_submit() or request.method == "POST":
        secciones = database.session.execute(select(func.count(CursoSeccion.id)).filter_by(curso=course_code)).scalar()
        nuevo_indice = int(secciones + 1)
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
        except OperationalError:  # pragma: no cover
            flash("Hubo en error al crear la seccion.", "warning")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
    else:  # pragma: no cover
        return render_template("learning/nuevo_seccion.html", form=form)


@course.route("/course/<course_code>/<seccion>/edit", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def editar_seccion(course_code, seccion):
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
        except OperationalError:  # pragma: no cover
            flash("Hubo en error al actualizar la seccion.", "warning")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
    else:  # pragma: no cover
        return render_template("learning/editar_seccion.html", form=form, seccion=seccion_a_editar)


@course.route("/course/<course_code>/seccion/increment/<indice>")
@login_required
@perfil_requerido("instructor")
def incrementar_indice_seccion(course_code, indice):
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
def reducir_indice_seccion(course_code, indice):
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
def modificar_orden_recurso(cource_code, seccion_id, resource_index, task):
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
def eliminar_recurso(curso_code, seccion, id_):
    """Elimina una seccion del curso."""
    database.session.execute(delete(CursoRecurso).where(CursoRecurso.id == id_))
    database.session.commit()
    reorganiza_indice_seccion(seccion=seccion)
    return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=curso_code))


@course.route("/course/<curso_id>/delete_seccion/<id_>")
@login_required
@perfil_requerido("instructor")
def eliminar_seccion(curso_id, id_):
    """Elimina una seccion del curso."""
    database.session.execute(delete(CursoSeccion).where(CursoSeccion.id == id_))
    database.session.commit()
    reorganiza_indice_curso(codigo_curso=curso_id)
    return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=curso_id))


@course.route("/course/change_curse_status")
@login_required
@perfil_requerido("instructor")
def cambiar_estatus_curso():
    """Actualiza el estatus de un curso."""
    cambia_estado_curso_por_id(
        id_curso=request.args.get("curse"), nuevo_estado=request.args.get("status"), usuario=current_user.usuario
    )
    return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=request.args.get("curse")))


@course.route("/course/change_curse_public")
@login_required
@perfil_requerido("instructor")
def cambiar_curso_publico():
    """Actualiza el estado publico de un curso."""
    cambia_curso_publico(
        id_curso=request.args.get("curse"),
    )
    return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=request.args.get("curse")))


@course.route("/course/change_curse_seccion_public")
@login_required
@perfil_requerido("instructor")
def cambiar_seccion_publico():
    """Actualiza el estado publico de un curso."""
    cambia_seccion_publico(
        codigo=request.args.get("codigo"),
    )
    return redirect(url_for(VISTA_CURSOS, course_code=request.args.get("course_code")))


def _get_user_resource_progress(curso_id, usuario=None):
    """Obtiene el progreso del usuario en todos los recursos del curso."""
    if not usuario:
        return {}

    progress_data = (
        database.session.execute(select(CursoRecursoAvance).filter_by(usuario=usuario, curso=curso_id)).scalars().all()
    )

    return {p.recurso: {"completado": p.completado} for p in progress_data}


def _get_course_evaluations_and_attempts(curso_id, usuario=None):
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
def pagina_recurso(curso_id, resource_type, codigo):
    """Pagina de un recurso."""
    from now_lms.db.tools import verifica_estudiante_asignado_a_curso

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
        if current_user.tipo == "admin" or current_user.tipo == "instructor":
            show_resource = True
        elif current_user.tipo == "student" and verifica_estudiante_asignado_a_curso(curso_id):
            show_resource = True
        else:
            show_resource = False
    else:
        show_resource = False

    if show_resource or RECURSO.publico:
        # Obtener progreso del recurso actual
        resource_progress = (
            database.session.execute(
                database.select(CursoRecursoAvance).filter_by(usuario=current_user.usuario, curso=curso_id, recurso=codigo)
            )
            .scalars()
            .first()
        )
        if resource_progress:
            recurso_completado = resource_progress.completado
        else:
            recurso_completado = False

        # Obtener datos adicionales para el sidebar mejorado
        user_progress = {}
        evaluaciones = []
        evaluation_attempts = {}

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
    else:
        flash(NO_AUTORIZADO_MSG, "warning")
        return abort(403)


def _emitir_certificado(curso_id, usuario, plantilla):
    """Emit a certificate for a user in a course."""
    from now_lms.db import Certificacion

    certificado = Certificacion(
        curso=curso_id,
        usuario=usuario,
        certificado=plantilla,
    )
    certificado.creado = datetime.now(timezone.utc).date()
    certificado.creado_por = current_user.usuario
    database.session.add(certificado)
    database.session.commit()
    flash("Certificado de finalización emitido.", "success")


def _actualizar_avance_curso(curso_id, usuario):
    """Actualiza el avance de un usuario en un curso."""
    from now_lms.db import CursoRecursoAvance, CursoUsuarioAvance

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

    _avance.recursos_requeridos = _recursos_requeridos
    _avance.recursos_completados = _recursos_completados
    _avance.avance = (_recursos_completados / _recursos_requeridos) * 100
    if _avance.avance >= 100:
        _avance.completado = True
        flash("Curso completado", "success")
        curso = database.session.execute(select(Curso).filter(Curso.codigo == curso_id)).scalars().first()
        log.warning(curso)
        if curso.certificado:
            _emitir_certificado(curso_id, usuario, curso.plantilla_certificado)
    database.session.commit()


@course.route("/course/<curso_id>/resource/<resource_type>/<codigo>/complete")
@login_required
@perfil_requerido("student")
def marcar_recurso_completado(curso_id, resource_type, codigo):
    """Registra avance de un 100% en un recurso."""
    from now_lms.db.tools import verifica_estudiante_asignado_a_curso

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
            else:
                flash(NO_AUTORIZADO_MSG, "warning")
                return abort(403)
        else:
            flash(NO_AUTORIZADO_MSG, "warning")
            return abort(403)
    else:
        flash(NO_AUTORIZADO_MSG, "warning")
        return abort(403)


@course.route("/course/<curso_id>/alternative/<codigo>/<order>")
@login_required
@perfil_requerido("student")
def pagina_recurso_alternativo(curso_id, codigo, order):
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
    else:
        flash(NO_AUTORIZADO_MSG, "warning")
        return abort(403)


@course.route("/course/<course_code>/<seccion>/new_resource")
@login_required
@perfil_requerido("instructor")
def nuevo_recurso(course_code, seccion):
    """Página para seleccionar tipo de recurso."""
    return render_template("learning/resources_new/nuevo_recurso.html", id_curso=course_code, id_seccion=seccion)


@course.route("/course/<course_code>/<seccion>/youtube/new", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def nuevo_recurso_youtube_video(course_code, seccion):
    """Formulario para crear un nuevo recurso tipo vídeo en Youtube."""
    form = CursoRecursoVideoYoutube()
    consulta_recursos = database.session.execute(select(func.count(CursoRecurso.id)).filter_by(seccion=seccion)).scalar()
    nuevo_indice = int(consulta_recursos + 1)
    if form.validate_on_submit() or request.method == "POST":
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
        )
        try:
            database.session.add(nuevo_recurso_)
            database.session.commit()
            flash(RECURSO_AGREGADO, "success")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
        except OperationalError:  # pragma: no cover
            flash(ERROR_AL_AGREGAR_CURSO, "warning")
            return redirect(url_for(VISTA_CURSOS, course_code=course_code))
    else:
        return render_template(
            "learning/resources_new/nuevo_recurso_youtube.html", id_curso=course_code, id_seccion=seccion, form=form
        )


@course.route("/course/<course_code>/<seccion>/youtube/<resource_id>/edit", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def editar_recurso_youtube_video(course_code, seccion, resource_id):
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

        try:
            database.session.commit()
            flash("Recurso actualizado correctamente.", "success")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
        except OperationalError:  # pragma: no cover
            flash("Hubo un error al actualizar el recurso.", "warning")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
    else:
        # Pre-populate form with existing data
        form.nombre.data = recurso.nombre
        form.descripcion.data = recurso.descripcion
        form.youtube_url.data = recurso.url
        form.requerido.data = recurso.requerido

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
def nuevo_recurso_text(course_code, seccion):
    """Formulario para crear un nuevo documento de texto."""
    form = CursoRecursoArchivoText()
    consulta_recursos = database.session.execute(select(func.count(CursoRecurso.id)).filter_by(seccion=seccion)).scalar()
    nuevo_indice = int(consulta_recursos + 1)
    if form.validate_on_submit() or request.method == "POST":
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
        )
        try:
            nuevo_recurso_.creado = datetime.now(timezone.utc).date()
            nuevo_recurso_.creado_por = current_user.usuario
            database.session.add(nuevo_recurso_)
            database.session.commit()
            flash(RECURSO_AGREGADO, "success")
            return redirect(url_for(VISTA_CURSOS, course_code=course_code))
        except OperationalError:  # pragma: no cover
            flash(ERROR_AL_AGREGAR_CURSO, "warning")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
    else:
        return render_template(
            "learning/resources_new/nuevo_recurso_text.html", id_curso=course_code, id_seccion=seccion, form=form
        )


@course.route("/course/<course_code>/<seccion>/text/<resource_id>/edit", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def editar_recurso_text(course_code, seccion, resource_id):
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
        recurso.descripcion = "Text resource"
        recurso.requerido = form.requerido.data
        recurso.text = form.editor.data
        recurso.modificado = datetime.now(timezone.utc)
        recurso.modificado_por = current_user.usuario

        try:
            database.session.commit()
            flash("Recurso actualizado correctamente.", "success")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
        except OperationalError:  # pragma: no cover
            flash("Hubo un error al actualizar el recurso.", "warning")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
    else:
        # Pre-populate form with existing data
        form.nombre.data = recurso.nombre
        form.descripcion.data = recurso.descripcion
        form.requerido.data = recurso.requerido
        form.editor.data = recurso.text

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
def nuevo_recurso_link(course_code, seccion):
    """Formulario para crear un nuevo documento de texto."""
    form = CursoRecursoExternalLink()
    recursos = database.session.execute(select(func.count(CursoRecurso.id)).filter_by(seccion=seccion)).scalar()
    nuevo_indice = int(recursos + 1)
    if form.validate_on_submit() or request.method == "POST":
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
        )
        try:
            database.session.add(nuevo_recurso_)
            database.session.commit()
            flash(RECURSO_AGREGADO, "success")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
        except OperationalError:  # pragma: no cover
            flash(ERROR_AL_AGREGAR_CURSO, "warning")
            return redirect(url_for(VISTA_CURSOS, course_code=course_code))
    else:
        return render_template(
            "learning/resources_new/nuevo_recurso_link.html", id_curso=course_code, id_seccion=seccion, form=form
        )


@course.route("/course/<course_code>/<seccion>/link/<resource_id>/edit", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def editar_recurso_link(course_code, seccion, resource_id):
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

        try:
            database.session.commit()
            flash("Recurso actualizado correctamente.", "success")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
        except OperationalError:  # pragma: no cover
            flash("Hubo un error al actualizar el recurso.", "warning")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
    else:
        # Pre-populate form with existing data
        form.nombre.data = recurso.nombre
        form.descripcion.data = recurso.descripcion
        form.requerido.data = recurso.requerido
        form.url.data = recurso.url

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
def nuevo_recurso_pdf(course_code, seccion):
    """Formulario para crear un nuevo recurso tipo archivo en PDF."""
    form = CursoRecursoArchivoPDF()
    recursos = database.session.execute(select(func.count(CursoRecurso.id)).filter_by(seccion=seccion)).scalar()
    nuevo_indice = int(recursos + 1)
    if (form.validate_on_submit() or request.method == "POST") and "pdf" in request.files:
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
        )
        try:
            database.session.add(nuevo_recurso_)
            database.session.commit()
            flash("RECURSO_AGREGADO", "success")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
        except OperationalError:  # pragma: no cover
            flash(ERROR_AL_AGREGAR_CURSO, "warning")
            return redirect(url_for(VISTA_CURSOS, course_code=course_code))
    else:
        return render_template(
            "learning/resources_new/nuevo_recurso_pdf.html", id_curso=course_code, id_seccion=seccion, form=form
        )


@course.route("/course/<course_code>/<seccion>/pdf/<resource_id>/edit", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def editar_recurso_pdf(course_code, seccion, resource_id):
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
        except OperationalError:  # pragma: no cover
            flash("Hubo un error al actualizar el recurso.", "warning")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
    else:
        # Pre-populate form with existing data
        form.nombre.data = recurso.nombre
        form.descripcion.data = recurso.descripcion
        form.requerido.data = recurso.requerido

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
def nuevo_recurso_meet(course_code, seccion):
    """Formulario para crear un nuevo recurso tipo archivo en PDF."""
    form = CursoRecursoMeet()
    recursos = database.session.execute(select(func.count(CursoRecurso.id)).filter_by(seccion=seccion)).scalar()
    nuevo_indice = int(recursos + 1)
    if form.validate_on_submit() or request.method == "POST":
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
        )
        try:
            database.session.add(nuevo_recurso_)
            database.session.commit()
            flash("RECURSO_AGREGADO", "success")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
        except OperationalError:  # pragma: no cover
            flash(ERROR_AL_AGREGAR_CURSO, "warning")
            return redirect(url_for(VISTA_CURSOS, course_code=course_code))
    else:
        return render_template(
            "learning/resources_new/nuevo_recurso_meet.html", id_curso=course_code, id_seccion=seccion, form=form
        )


@course.route("/course/<course_code>/<seccion>/meet/<resource_id>/edit", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def editar_recurso_meet(course_code, seccion, resource_id):
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

        try:
            database.session.commit()
            # Update calendar events for this meet resource
            update_meet_resource_events(resource_id)
            flash("Recurso actualizado correctamente.", "success")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
        except OperationalError:  # pragma: no cover
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
def nuevo_recurso_img(course_code, seccion):
    """Formulario para crear un nuevo recurso tipo imagen."""
    form = CursoRecursoArchivoImagen()
    recursos = database.session.execute(select(func.count(CursoRecurso.id)).filter_by(seccion=seccion)).scalar()
    nuevo_indice = int(recursos + 1)
    if (form.validate_on_submit() or request.method == "POST") and "img" in request.files:
        file_name = str(ULID()) + ".jpg"
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
        )
        try:
            database.session.add(nuevo_recurso_)
            database.session.commit()
            flash("RECURSO_AGREGADO", "success")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
        except OperationalError:  # pragma: no cover
            flash(ERROR_AL_AGREGAR_CURSO, "warning")
            return redirect(url_for(VISTA_CURSOS, course_code=course_code))
    else:
        return render_template(
            "learning/resources_new/nuevo_recurso_img.html", id_curso=course_code, id_seccion=seccion, form=form
        )


@course.route("/course/<course_code>/<seccion>/img/<resource_id>/edit", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def editar_recurso_img(course_code, seccion, resource_id):
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

        # Handle file replacement if a new image is uploaded
        if "img" in request.files and request.files["img"].filename:
            file_name = str(ULID()) + ".jpg"
            picture_file = images.save(request.files["img"], folder=course_code, name=file_name)
            recurso.base_doc_url = images.name
            recurso.doc = picture_file

        try:
            database.session.commit()
            flash("Recurso actualizado correctamente.", "success")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
        except OperationalError:  # pragma: no cover
            flash("Hubo un error al actualizar el recurso.", "warning")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
    else:
        # Pre-populate form with existing data
        form.nombre.data = recurso.nombre
        form.descripcion.data = recurso.descripcion
        form.requerido.data = recurso.requerido

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
def nuevo_recurso_audio(course_code, seccion):
    """Formulario para crear un nuevo recurso de audio."""
    form = CursoRecursoArchivoAudio()
    recursos = database.session.execute(select(func.count(CursoRecurso.id)).filter_by(seccion=seccion)).scalar()
    nuevo_indice = int(recursos + 1)
    if (form.validate_on_submit() or request.method == "POST") and "audio" in request.files:
        audio_name = str(ULID()) + ".ogg"
        audio_file = audio.save(request.files["audio"], folder=course_code, name=audio_name)

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
            creado_por=current_user.usuario,
        )
        try:
            database.session.add(nuevo_recurso_)
            database.session.commit()
            flash("RECURSO_AGREGADO", "success")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
        except OperationalError:  # pragma: no cover
            flash(ERROR_AL_AGREGAR_CURSO, "warning")
            return redirect(url_for(VISTA_CURSOS, course_code=course_code))
    else:
        return render_template(
            "learning/resources_new/nuevo_recurso_mp3.html", id_curso=course_code, id_seccion=seccion, form=form
        )


@course.route("/course/<course_code>/<seccion>/audio/<resource_id>/edit", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def editar_recurso_audio(course_code, seccion, resource_id):
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

        # Handle file replacement if a new audio file is uploaded
        if "audio" in request.files and request.files["audio"].filename:
            audio_name = str(ULID()) + ".ogg"
            audio_file = audio.save(request.files["audio"], folder=course_code, name=audio_name)
            recurso.base_doc_url = audio.name
            recurso.doc = audio_file

        try:
            database.session.commit()
            flash("Recurso actualizado correctamente.", "success")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
        except OperationalError:  # pragma: no cover
            flash("Hubo un error al actualizar el recurso.", "warning")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
    else:
        # Pre-populate form with existing data
        form.nombre.data = recurso.nombre
        form.descripcion.data = recurso.descripcion
        form.requerido.data = recurso.requerido

        return render_template(
            "learning/resources_new/editar_recurso_mp3.html",
            id_curso=course_code,
            id_seccion=seccion,
            recurso=recurso,
            form=form,
        )


@course.route("/course/<course_code>/<seccion>/html/new", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def nuevo_recurso_html(course_code, seccion):
    """Formulario para crear un nuevo recurso tipo HTML externo."""
    form = CursoRecursoExternalCode()
    recursos = database.session.execute(select(func.count(CursoRecurso.id)).filter_by(seccion=seccion)).scalar()
    nuevo_indice = int(recursos + 1)
    if form.validate_on_submit() or request.method == "POST":
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
        )
        try:
            database.session.add(nuevo_recurso_)
            database.session.commit()
            flash("RECURSO_AGREGADO", "success")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
        except OperationalError:  # pragma: no cover
            flash(ERROR_AL_AGREGAR_CURSO, "warning")
            return redirect(url_for(VISTA_CURSOS, course_code=course_code))
    else:
        return render_template(
            "learning/resources_new/nuevo_recurso_html.html", id_curso=course_code, id_seccion=seccion, form=form
        )


@course.route("/course/<course_code>/<seccion>/html/<resource_id>/edit", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def editar_recurso_html(course_code, seccion, resource_id):
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

        try:
            database.session.commit()
            flash("Recurso actualizado correctamente.", "success")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
        except OperationalError:  # pragma: no cover
            flash("Hubo un error al actualizar el recurso.", "warning")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
    else:
        # Pre-populate form with existing data
        form.nombre.data = recurso.nombre
        form.descripcion.data = recurso.descripcion
        form.requerido.data = recurso.requerido
        form.html_externo.data = recurso.external_code

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
def elimina_logo(course_code):
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
def nuevo_recurso_slideshow(course_code, seccion):
    """Crear una nueva presentación de diapositivas."""
    form = SlideShowForm()
    if form.validate_on_submit():
        try:
            # Crear el recurso en CursoRecurso
            consulta_recursos = database.session.execute(
                select(func.count(CursoRecurso.id)).filter_by(seccion=seccion)
            ).scalar()
            nuevo_indice = int(consulta_recursos + 1)

            nuevo_recurso = CursoRecurso(
                curso=course_code,
                seccion=seccion,
                tipo="slides",
                nombre=form.nombre.data,
                descripcion=form.descripcion.data,
                indice=nuevo_indice,
                publico=False,
                requerido="required",
            )
            database.session.add(nuevo_recurso)
            database.session.flush()  # Para obtener el ID

            # Crear la presentación SlideShowResource
            slideshow = SlideShowResource(
                course_id=course_code, title=form.nombre.data, theme=form.theme.data, creado_por=current_user.usuario
            )
            database.session.add(slideshow)
            database.session.flush()

            # Agregar el ID del slideshow al recurso como referencia
            nuevo_recurso.external_code = slideshow.id

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
def editar_slideshow(course_code, slideshow_id):
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
                        slide = database.session.get(Slide, slide_id)
                        if slide and slide.slide_show_id == slideshow_id:
                            slide.title = slide_title
                            slide.content = clean_content
                            slide.order = slide_order
                            slide.modificado_por = current_user.usuario
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
def preview_slideshow(course_code, slideshow_id):
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
def recurso_file(course_code, recurso_code):
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
        if doc.publico or current_user.tipo == "admin":
            return send_from_directory(config.destination, doc.doc)
        else:
            return abort(403)
    else:
        return redirect(INICIO_SESION)


@course.route("/course/<course_code>/pdf_viewer/<recurso_code>")
def pdf_viewer(course_code, recurso_code):
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
        if recurso.publico or current_user.tipo == "admin":
            return render_template("learning/resources/pdf_viewer.html", recurso=recurso)
        else:
            return abort(403)
    else:
        return redirect(INICIO_SESION)


@course.route("/course/<course_code>/external_code/<recurso_code>")
def external_code(course_code, recurso_code):
    """Devuelve un archivo desde el sistema de archivos."""
    recurso = (
        database.session.execute(
            select(CursoRecurso).filter(CursoRecurso.id == recurso_code, CursoRecurso.curso == course_code)
        )
        .scalars()
        .first()
    )

    if current_user.is_authenticated:
        if recurso.publico or current_user.tipo == "admin":
            return recurso.external_code

        else:
            return abort(403)
    else:
        return redirect(INICIO_SESION)


@course.route("/course/slide_show/<recurso_code>")
def slide_show(recurso_code):
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


@course.route("/course/explore")
@cache.cached(unless=no_guardar_en_cache_global)
def lista_cursos():
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


def _validate_coupon_permissions(course_code, user):
    """Validate that user can manage coupons for this course."""
    curso = database.session.execute(select(Curso).filter_by(codigo=course_code)).scalars().first()
    if not curso:
        return None, "Curso no encontrado"

    if not curso.pagado:
        return None, "Los cupones solo están disponibles para cursos pagados"

    # Check if user is instructor for this course
    instructor_assignment = (
        database.session.execute(select(DocenteCurso).filter_by(curso=course_code, usuario=user.usuario, vigente=True))
        .scalars()
        .first()
    )

    if not instructor_assignment and user.tipo != "admin":
        return None, "Solo el instructor del curso puede gestionar cupones"

    return curso, None


def _validate_coupon_for_enrollment(course_code, coupon_code, user):
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
def list_coupons(course_code):
    """Lista cupones existentes para un curso."""
    curso, error = _validate_coupon_permissions(course_code, current_user)
    if error:
        flash(error, "warning")
        return redirect(url_for("course.administrar_curso", course_code=course_code))

    coupons = (
        database.session.execute(select(Coupon).filter_by(course_id=course_code).order_by(Coupon.timestamp.desc()))
        .scalars()
        .all()
    )

    return render_template("learning/curso/coupons/list.html", curso=curso, coupons=coupons)


@course.route("/course/<course_code>/coupons/new", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def create_coupon(course_code):
    """Crear nuevo cupón para un curso."""
    curso, error = _validate_coupon_permissions(course_code, current_user)
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

    return render_template(TEMPLATE_COUPON_CREATE, curso=curso, form=form)


@course.route("/course/<course_code>/coupons/<coupon_id>/edit", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def edit_coupon(course_code, coupon_id):
    """Editar cupón existente."""
    curso, error = _validate_coupon_permissions(course_code, current_user)
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
            return render_template(TEMPLATE_COUPON_EDIT, curso=curso, coupon=coupon, form=form)

        if form.discount_type.data == "fixed" and form.discount_value.data > curso.precio:
            flash("El descuento fijo no puede ser mayor al precio del curso", "warning")
            return render_template(TEMPLATE_COUPON_EDIT, curso=curso, coupon=coupon, form=form)

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

    return render_template(TEMPLATE_COUPON_EDIT, curso=curso, coupon=coupon, form=form)


@course.route("/course/<course_code>/coupons/<coupon_id>/delete", methods=["POST"])
@login_required
@perfil_requerido("instructor")
def delete_coupon(course_code, coupon_id):
    """Eliminar cupón."""
    curso, error = _validate_coupon_permissions(course_code, current_user)
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


@course.route("/course/<course_code>/section/<section_id>/new_evaluation")
@login_required
@perfil_requerido("instructor")
def new_evaluation_from_section(course_code, section_id):
    """Create a new evaluation for a course section from section actions."""
    # Redirect to the existing instructor profile route for evaluation creation
    return redirect(url_for("instructor_profile.new_evaluation", course_code=course_code, section_id=section_id))
