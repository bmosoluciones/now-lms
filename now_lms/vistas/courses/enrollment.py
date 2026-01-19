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

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy.exc import OperationalError
from werkzeug.wrappers import Response

from now_lms.auth import perfil_requerido, usuario_requiere_verificacion_email
from now_lms.cache import cache, cache_key_with_auth_state
from now_lms.calendar_utils import create_events_for_student_enrollment
from now_lms.db import (
    Certificacion,
    Curso,
    CursoRecurso,
    CursoRecursoDescargable,
    CursoSeccion,
    EstudianteCurso,
    Evaluation,
    EvaluationAttempt,
    EvaluationReopenRequest,
    Pago,
    Recurso,
    Usuario,
    database,
    select,
)
from now_lms.forms import CouponApplicationForm, PagoForm
from now_lms.misc import CURSO_NIVEL, TIPOS_RECURSOS
from .base import VISTA_CURSOS, course, markdown2html
from .helpers import _crear_indice_avance_curso
from .coupons import _validate_coupon_for_enrollment


@dataclass
class EnrollmentPricing:
    """Pricing details for an enrollment, including discounts and validation."""

    applied_coupon: object | None
    original_price: float
    final_price: float
    discount_amount: float
    validation_error: str | None = None


def _calculate_enrollment_pricing(course_obj: Curso, coupon_code: str, user: Usuario) -> EnrollmentPricing:
    """Calculate pricing and coupon data for enrollment."""
    original_price = course_obj.precio if course_obj.pagado else 0
    pricing = EnrollmentPricing(None, original_price, original_price, 0)

    if not coupon_code or not course_obj.pagado:
        return pricing

    coupon, _, validation_error = _validate_coupon_for_enrollment(course_obj.codigo, coupon_code, user)
    if coupon:
        pricing.applied_coupon = coupon
        pricing.discount_amount = coupon.calculate_discount(original_price)
        pricing.final_price = coupon.calculate_final_price(original_price)
    else:
        pricing.validation_error = validation_error

    return pricing


def _build_coupon_flash_message(applied_coupon: object | None, final_price: float, discount_amount: float) -> str | None:
    """Generate success flash message for coupon usage."""
    if not applied_coupon:
        return None

    if final_price == 0:
        return f"¡Cupón aplicado exitosamente! Inscripción gratuita con código {applied_coupon.code}"

    return f"¡Cupón aplicado! Descuento de {discount_amount} aplicado"


def _build_pago_from_form(form, course_obj: Curso, final_price: float) -> Pago:
    """Create Pago object with form data."""
    pago = Pago()
    pago.usuario = current_user.usuario
    pago.curso = course_obj.codigo
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
    return pago


def _finalize_completed_enrollment(
    pago: Pago,
    course_code: str,
    applied_coupon: object | None = None,
    final_price: float = 0,
    discount_amount: float = 0,
    success_message: str | None = None,
) -> Response:
    """Persist payment/enrollment and return navigation response."""
    try:
        pago.creado = datetime.now(timezone.utc).date()
        pago.creado_por = current_user.usuario
        database.session.add(pago)
        database.session.flush()

        if applied_coupon and final_price == 0:
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

        create_events_for_student_enrollment(pago.usuario, pago.curso)

        if success_message:
            flash(success_message, "success")

        return redirect(url_for("course.tomar_curso", course_code=course_code))
    except OperationalError:
        database.session.rollback()
        flash("Hubo en error al crear el registro de pago.", "warning")
        return redirect(url_for(VISTA_CURSOS, course_code=course_code))


def _process_paid_enrollment(pago: Pago, course_code: str) -> Response:
    """Handle paid enrollment flow and redirections."""
    existing = (
        database.session.execute(select(Pago).filter_by(usuario=current_user.usuario, curso=course_code, estado="pending"))
        .scalars()
        .first()
    )
    if existing:
        return redirect(url_for("paypal.resume_payment", payment_id=existing.id))

    try:
        database.session.add(pago)
        database.session.commit()
        return redirect(url_for("paypal.payment_page", course_code=course_code, payment_id=pago.id))
    except OperationalError:
        database.session.rollback()
        flash("Error al procesar el pago", "warning")
        return redirect(url_for(VISTA_CURSOS, course_code=course_code))


def _is_free_enrollment(course_obj: Curso, final_price: float) -> bool:
    return not course_obj.pagado or final_price == 0


def _is_audit_enrollment(mode: str, course_obj: Curso) -> bool:
    return mode == "audit" and course_obj.auditable


@course.route("/course/<course_code>/enroll", methods=["GET", "POST"])
@login_required
@perfil_requerido("student")
def course_enroll(course_code: str) -> str | Response:
    """Pagina para inscribirse a un curso."""
    _curso = database.session.execute(database.select(Curso).filter_by(codigo=course_code)).scalar_one_or_none()
    _usuario = database.session.execute(database.select(Usuario).filter_by(usuario=current_user.usuario)).scalar_one_or_none()

    if not _curso or not _usuario:
        abort(404)

    _modo = request.args.get("modo", "") or request.form.get("modo", "")

    # Check for coupon code in URL or form
    coupon_code = request.args.get("coupon_code", "") or request.form.get("coupon_code", "")
    pricing = _calculate_enrollment_pricing(_curso, coupon_code, _usuario)

    # Check if user has unverified email and is trying to enroll in paid course or use coupon
    if _curso.pagado and usuario_requiere_verificacion_email():
        # User has unverified email - only allow free enrollment without coupons
        flash(
            "Debe verificar su correo electrónico para inscribirse en cursos de pago o usar cupones. "
            "Los cursos gratuitos están disponibles sin verificación.",
            "warning",
        )
        return redirect(url_for(VISTA_CURSOS, course_code=course_code))

    if pricing.validation_error:
        flash(pricing.validation_error, "warning")

    form = PagoForm()
    coupon_form = CouponApplicationForm()

    # Pre-fill form data
    form.nombre.data = _usuario.nombre
    form.apellido.data = _usuario.apellido
    form.correo_electronico.data = _usuario.correo_electronico
    if coupon_code:
        coupon_form.coupon_code.data = coupon_code

    if form.validate_on_submit():
        pago = _build_pago_from_form(form, _curso, pricing.final_price)

        # Add coupon information to payment description
        if pricing.applied_coupon:
            pago.descripcion = f"Cupón aplicado: {pricing.applied_coupon.code} (Descuento: {pricing.discount_amount})"

        # Handle different enrollment modes
        if _is_free_enrollment(_curso, pricing.final_price):
            pago.estado = "completed"
            success_message = _build_coupon_flash_message(pricing.applied_coupon, pricing.final_price, pricing.discount_amount)
            return _finalize_completed_enrollment(
                pago,
                course_code,
                pricing.applied_coupon,
                pricing.final_price,
                pricing.discount_amount,
                success_message,
            )

        if _is_audit_enrollment(_modo, _curso):
            pago.audit = True
            pago.estado = "completed"  # Audit enrollment is completed immediately
            pago.monto = 0
            pago.metodo = "audit"
            return _finalize_completed_enrollment(pago, course_code)

        return _process_paid_enrollment(pago, course_code)

    return render_template(
        "learning/curso/enroll.html",
        curso=_curso,
        usuario=_usuario,
        form=form,
        coupon_form=coupon_form,
        applied_coupon=pricing.applied_coupon,
        original_price=pricing.original_price,
        final_price=pricing.final_price,
        discount_amount=pricing.discount_amount,
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
