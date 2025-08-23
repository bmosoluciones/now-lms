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

"""Master Class views."""

# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------
from datetime import datetime

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from slugify import slugify
from sqlalchemy import and_

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms.db import MasterClass, MasterClassEnrollment, Usuario, database, select
from now_lms.forms.masterclass import MasterClassEnrollmentForm, MasterClassForm

# ---------------------------------------------------------------------------------------
# Blueprint definition
# ---------------------------------------------------------------------------------------
masterclass = Blueprint("masterclass", __name__, url_prefix="/masterclass")


# ---------------------------------------------------------------------------------------
# Public routes - Available to all users
# ---------------------------------------------------------------------------------------


@masterclass.route("/")
def list_public():
    """Public listing of master classes."""
    page = request.args.get("page", 1, type=int)
    per_page = 9  # Display 9 items per page for card layout

    # Get upcoming public master classes
    master_classes = database.paginate(
        select(MasterClass)
        .filter(MasterClass.date >= datetime.now().date())
        .order_by(MasterClass.date.asc(), MasterClass.start_time.asc()),
        page=page,
        per_page=per_page,
        error_out=False,
    )

    return render_template("masterclass/list_public.html", master_classes=master_classes, title="Clases Magistrales")


@masterclass.route("/<slug>")
def detail_public(slug):
    """Public detail view of a master class."""
    master_class = database.session.execute(select(MasterClass).filter_by(slug=slug)).scalars().first()
    if not master_class:
        abort(404)

    # Check if user is enrolled
    enrollment = None
    if current_user.is_authenticated:
        enrollment = (
            database.session.execute(
                select(MasterClassEnrollment).filter_by(master_class_id=master_class.id, user_id=current_user.usuario)
            )
            .scalars()
            .first()
        )

    return render_template(
        "masterclass/detail_public.html", master_class=master_class, enrollment=enrollment, title=master_class.title
    )


@masterclass.route("/<slug>/enroll", methods=["GET", "POST"])
@login_required
def enroll(slug):
    """Enroll in a master class."""
    master_class = database.session.execute(select(MasterClass).filter_by(slug=slug)).scalars().first()
    if not master_class:
        abort(404)

    # Check if already enrolled
    existing_enrollment = (
        database.session.execute(
            select(MasterClassEnrollment).filter_by(master_class_id=master_class.id, user_id=current_user.usuario)
        )
        .scalars()
        .first()
    )

    if existing_enrollment:
        flash("Ya estás inscrito en esta clase magistral.", "info")
        return redirect(url_for("masterclass.detail_public", slug=slug))

    form = MasterClassEnrollmentForm()

    if form.validate_on_submit():
        # Create enrollment record (always free, no payment processing needed)
        enrollment = MasterClassEnrollment(
            master_class_id=master_class.id,
            user_id=current_user.usuario,
            is_confirmed=True,  # Always confirmed since it's free
            payment_id=None,  # No payment required
        )

        database.session.add(enrollment)
        database.session.commit()

        flash("Te has inscrito exitosamente en la clase magistral.", "success")
        return redirect(url_for("masterclass.detail_public", slug=slug))

    return render_template(
        "masterclass/enroll.html", master_class=master_class, form=form, title=f"Inscribirse en {master_class.title}"
    )


# ---------------------------------------------------------------------------------------
# Instructor routes - For instructors to manage their master classes
# ---------------------------------------------------------------------------------------


@masterclass.route("/instructor")
@login_required
def instructor_list():
    """List instructor's master classes."""
    if current_user.tipo not in ["instructor", "admin"]:
        abort(403)

    page = request.args.get("page", 1, type=int)
    per_page = 10

    master_classes = database.paginate(
        select(MasterClass).filter_by(instructor_id=current_user.usuario).order_by(MasterClass.date.desc()),
        page=page,
        per_page=per_page,
        error_out=False,
    )

    return render_template("masterclass/instructor_list.html", master_classes=master_classes, title="Mis Clases Magistrales")


@masterclass.route("/instructor/create", methods=["GET", "POST"])
@login_required
def instructor_create():
    """Create a new master class."""
    if current_user.tipo not in ["instructor", "admin"]:
        abort(403)

    form = MasterClassForm()

    if form.validate_on_submit():
        # Generate slug from title
        slug = slugify(form.title.data)
        counter = 1
        original_slug = slug

        # Ensure slug is unique by adding counter if needed
        while database.session.execute(select(MasterClass).filter_by(slug=slug)).scalars().first():
            slug = f"{original_slug}-{counter}"
            counter += 1

        # Create master class with validated data
        master_class = MasterClass(
            title=form.title.data,
            slug=slug,
            description_public=form.description_public.data,
            description_private=form.description_private.data,
            date=form.date.data,
            start_time=form.start_time.data,
            end_time=form.end_time.data,
            is_paid=False,  # Always free for marketing purposes
            price=None,
            early_discount=None,
            discount_deadline=None,
            platform_name=form.platform_name.data,
            platform_url=form.platform_url.data,
            is_certificate=form.is_certificate.data,
            diploma_template_id=form.diploma_template_id.data if form.is_certificate.data else None,
            instructor_id=current_user.usuario,
        )

        database.session.add(master_class)
        database.session.commit()

        flash("Clase magistral creada exitosamente.", "success")
        return redirect(url_for("masterclass.instructor_list"))

    return render_template("masterclass/instructor_create.html", form=form, title="Crear Clase Magistral")


@masterclass.route("/instructor/<master_class_id>/edit", methods=["GET", "POST"])
@login_required
def instructor_edit(master_class_id):
    """Edit a master class."""
    if current_user.tipo not in ["instructor", "admin"]:
        abort(403)

    master_class = database.session.execute(select(MasterClass).filter_by(id=master_class_id)).scalars().first()
    if not master_class:
        abort(404)

    # Check ownership or admin privilege
    if current_user.tipo != "admin" and master_class.instructor_id != current_user.usuario:
        abort(403)

    form = MasterClassForm(obj=master_class)

    if form.validate_on_submit():
        # Update slug if title changed
        if form.title.data != master_class.title:
            slug = slugify(form.title.data)
            counter = 1
            original_slug = slug

            # Check for slug conflicts excluding current record
            existing = (
                database.session.execute(
                    select(MasterClass).filter(and_(MasterClass.slug == slug, MasterClass.id != master_class_id))
                )
                .scalars()
                .first()
            )
            while existing:
                slug = f"{original_slug}-{counter}"
                counter += 1
                existing = (
                    database.session.execute(
                        select(MasterClass).filter(and_(MasterClass.slug == slug, MasterClass.id != master_class_id))
                    )
                    .scalars()
                    .first()
                )
            master_class.slug = slug

        # Update master class with form data
        form.populate_obj(master_class)

        # Ensure payment fields are always disabled (business rule)
        master_class.is_paid = False
        master_class.price = None
        master_class.early_discount = None
        master_class.discount_deadline = None

        # Handle conditional fields
        if not master_class.is_certificate:
            master_class.diploma_template_id = None

        database.session.commit()

        flash("Clase magistral actualizada exitosamente.", "success")
        return redirect(url_for("masterclass.instructor_list"))

    return render_template(
        "masterclass/instructor_edit.html", form=form, master_class=master_class, title="Editar Clase Magistral"
    )


@masterclass.route("/instructor/<master_class_id>/students")
@login_required
def instructor_students(master_class_id):
    """View enrolled students in a master class."""
    if current_user.tipo not in ["instructor", "admin"]:
        abort(403)

    master_class = database.session.execute(select(MasterClass).filter_by(id=master_class_id)).scalars().first()
    if not master_class:
        abort(404)

    # Check ownership or admin privilege
    if current_user.tipo != "admin" and master_class.instructor_id != current_user.usuario:
        abort(403)

    page = request.args.get("page", 1, type=int)
    per_page = 20

    # Get enrollments with user information
    enrollments = database.paginate(
        select(MasterClassEnrollment)
        .filter_by(master_class_id=master_class_id)
        .join(Usuario, MasterClassEnrollment.user_id == Usuario.usuario)
        .order_by(MasterClassEnrollment.enrolled_at.desc()),
        page=page,
        per_page=per_page,
        error_out=False,
    )

    return render_template(
        "masterclass/instructor_students.html",
        master_class=master_class,
        enrollments=enrollments,
        title=f"Estudiantes - {master_class.title}",
    )


# ---------------------------------------------------------------------------------------
# Student routes - For students to manage their enrollments
# ---------------------------------------------------------------------------------------


@masterclass.route("/my-enrollments")
@login_required
def my_enrollments():
    """View user's master class enrollments."""
    page = request.args.get("page", 1, type=int)
    per_page = 10

    # Get user's enrollments with master class details
    enrollments = database.paginate(
        select(MasterClassEnrollment)
        .filter_by(user_id=current_user.usuario)
        .join(MasterClass)
        .order_by(MasterClass.date.desc()),
        page=page,
        per_page=per_page,
        error_out=False,
    )

    return render_template("masterclass/my_enrollments.html", enrollments=enrollments, title="Mis Clases Magistrales")


# ---------------------------------------------------------------------------------------
# Admin routes - Administrative management of all master classes
# ---------------------------------------------------------------------------------------


@masterclass.route("/admin")
@login_required
def admin_list():
    """Admin view of all master classes."""
    if current_user.tipo != "admin":
        abort(403)

    page = request.args.get("page", 1, type=int)
    per_page = 15

    # Get all master classes with instructor details
    master_classes = database.paginate(
        select(MasterClass).join(Usuario, MasterClass.instructor_id == Usuario.usuario).order_by(MasterClass.date.desc()),
        page=page,
        per_page=per_page,
        error_out=False,
    )

    return render_template(
        "masterclass/admin_list.html", master_classes=master_classes, title="Administrar Clases Magistrales"
    )
