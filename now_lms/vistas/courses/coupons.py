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

from flask import flash, redirect, render_template, url_for
from flask_login import current_user, login_required
from sqlalchemy import select
from werkzeug.wrappers import Response

from now_lms.auth import perfil_requerido
from now_lms.db import Configuracion, Coupon, Curso, DocenteCurso, EstudianteCurso, database
from now_lms.forms import CouponForm
from now_lms.logs import log
from .base import ROUTE_LIST_COUPONS, TEMPLATE_COUPON_CREATE, TEMPLATE_COUPON_EDIT, course


def _validate_coupon_permissions(course_code: str, user) -> tuple[object | None, str | None]:
    """Validate that user can manage coupons for this course."""
    course_obj = database.session.execute(select(Curso).filter_by(codigo=course_code)).scalars().first()
    if not course_obj:
        return None, "Curso no encontrado"

    if not course_obj.pagado:
        return None, "Los cupones solo están disponibles para cursos pagados"

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

    coupon = (
        database.session.execute(select(Coupon).filter_by(course_id=course_code, code=coupon_code.upper())).scalars().first()
    )

    if not coupon:
        return None, None, "Código de cupón inválido"

    existing_enrollment = (
        database.session.execute(select(EstudianteCurso).filter_by(curso=course_code, usuario=user.usuario, vigente=True))
        .scalars()
        .first()
    )

    if existing_enrollment:
        return None, None, "No puede aplicar cupón - ya está inscrito en el curso"

    is_valid, error_message = coupon.is_valid()
    if not is_valid:
        return None, None, error_message

    course_obj = database.session.execute(database.select(Curso).filter_by(codigo=course_code)).scalar_one_or_none()
    if course_obj and course_obj.pagado:
        final_price = coupon.calculate_final_price(course_obj.precio)
        if final_price == 0 and not user.correo_electronico_verificado:
            config = database.session.execute(database.select(Configuracion)).scalar_one_or_none()
            if config and (config.verify_user_by_email or config.allow_unverified_email_login):
                return None, None, "Debe verificar su correo electrónico antes de usar cupones de descuento"

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
        existing = (
            database.session.execute(select(Coupon).filter_by(course_id=course_code, code=form.code.data.upper()))
            .scalars()
            .first()
        )

        if existing:
            flash("Ya existe un cupón con este código para este curso", "warning")
            return render_template(TEMPLATE_COUPON_CREATE, curso=course_obj, form=form)

        if form.discount_type.data == "percentage" and form.discount_value.data > 100:
            flash("El descuento porcentual no puede ser mayor al 100%", "warning")
            return render_template(TEMPLATE_COUPON_CREATE, curso=course_obj, form=form)

        if form.discount_type.data == "fixed" and form.discount_value.data > course_obj.precio:
            flash("El descuento fijo no puede ser mayor al precio del curso", "warning")
            return render_template(TEMPLATE_COUPON_CREATE, curso=course, form=form)

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
            return render_template(TEMPLATE_COUPON_EDIT, curso=course_obj, coupon=coupon, form=form)

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
