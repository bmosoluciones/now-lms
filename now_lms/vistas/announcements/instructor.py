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

"""Instructor announcements views."""

# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms.auth import perfil_requerido
from now_lms.cache import cache
from now_lms.config import DIRECTORIO_PLANTILLAS
from now_lms.db import MAXIMO_RESULTADOS_EN_CONSULTA_PAGINADA, Announcement, Curso, DocenteCurso, database
from now_lms.forms import CourseAnnouncementForm

# Route constants
ROUTE_INSTRUCTOR_ANNOUNCEMENTS_LIST = "instructor_announcements.list_announcements"

instructor_announcements = Blueprint("instructor_announcements", __name__, template_folder=DIRECTORIO_PLANTILLAS)


def get_instructor_courses(instructor_user):
    """Obtiene los cursos asignados a un instructor."""
    if instructor_user.tipo == "admin":
        # Los administradores pueden crear anuncios para cualquier curso
        return database.session.execute(database.select(Curso).filter(Curso.estado != "draft")).scalars().all()
    else:
        # Los instructores solo pueden crear anuncios para sus cursos asignados
        return (
            (
                database.session.execute(
                    database.select(Curso)
                    .join(DocenteCurso)
                    .filter(DocenteCurso.usuario == instructor_user.usuario, Curso.estado != "draft")
                )
            )
            .scalars()
            .all()
        )


@instructor_announcements.route("/instructor/announcements")
@login_required
@perfil_requerido("instructor")
@cache.cached(timeout=60)
def list_announcements():
    """Lista de anuncios de curso para instructores."""
    # Obtener cursos del instructor
    instructor_courses = get_instructor_courses(current_user)
    course_ids = [course.codigo for course in instructor_courses]

    if course_ids:
        consulta = database.paginate(
            database.select(Announcement)
            .filter(Announcement.course_id.in_(course_ids))
            .order_by(Announcement.timestamp.desc()),
            page=request.args.get("page", default=1, type=int),
            max_per_page=MAXIMO_RESULTADOS_EN_CONSULTA_PAGINADA,
            count=True,
        )
    else:
        # No hay cursos asignados
        consulta = None

    return render_template("announcements/instructor_list.html", consulta=consulta, courses=instructor_courses)


@instructor_announcements.route("/instructor/announcements/new", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def new_announcement():
    """Formulario para crear un nuevo anuncio de curso."""
    form = CourseAnnouncementForm()

    # Poblar choices del campo curso
    instructor_courses = get_instructor_courses(current_user)
    form.course_id.choices = [(course.codigo, course.nombre) for course in instructor_courses]

    if not instructor_courses:
        flash("No tienes cursos asignados para crear anuncios.", "warning")
        return redirect(url_for(ROUTE_INSTRUCTOR_ANNOUNCEMENTS_LIST))

    if form.validate_on_submit():
        # Verificar que el instructor tenga acceso al curso
        selected_course = (
            database.session.execute(database.select(Curso).filter_by(codigo=form.course_id.data)).scalars().first()
        )
        if not selected_course or selected_course not in instructor_courses:
            flash("No tienes permisos para crear anuncios en ese curso.", "error")
            return redirect(url_for("instructor_announcements.new_announcement"))

        announcement = Announcement(
            title=form.title.data,
            message=form.message.data,
            expires_at=form.expires_at.data,
            course_id=form.course_id.data,
            created_by_id=current_user.usuario,
            creado_por=current_user.usuario,
        )

        database.session.add(announcement)
        database.session.commit()

        flash("Anuncio de curso creado exitosamente.", "success")
        return redirect(url_for(ROUTE_INSTRUCTOR_ANNOUNCEMENTS_LIST))

    return render_template("announcements/instructor_form.html", form=form, title="Nuevo Anuncio de Curso")


@instructor_announcements.route("/instructor/announcements/<announcement_id>/edit", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def edit_announcement(announcement_id):
    """Formulario para editar un anuncio de curso."""
    announcement = database.session.get(Announcement, announcement_id)
    if not announcement or announcement.course_id is None:
        flash("Anuncio no encontrado o no es un anuncio de curso.", "error")
        return redirect(url_for(ROUTE_INSTRUCTOR_ANNOUNCEMENTS_LIST))

    # Verificar que el instructor tenga acceso al curso
    instructor_courses = get_instructor_courses(current_user)
    course_ids = [course.codigo for course in instructor_courses]

    if announcement.course_id not in course_ids:
        flash("No tienes permisos para editar este anuncio.", "error")
        return redirect(url_for(ROUTE_INSTRUCTOR_ANNOUNCEMENTS_LIST))

    form = CourseAnnouncementForm(obj=announcement)
    form.course_id.choices = [(course.codigo, course.nombre) for course in instructor_courses]

    if form.validate_on_submit():
        # Verificar nuevamente el permiso del curso seleccionado
        if form.course_id.data not in course_ids:
            flash("No tienes permisos para asignar este anuncio a ese curso.", "error")
            return redirect(url_for("instructor_announcements.edit_announcement", announcement_id=announcement_id))

        announcement.title = form.title.data
        announcement.message = form.message.data
        announcement.expires_at = form.expires_at.data
        announcement.course_id = form.course_id.data
        announcement.modificado_por = current_user.usuario

        database.session.commit()

        flash("Anuncio de curso actualizado exitosamente.", "success")
        return redirect(url_for(ROUTE_INSTRUCTOR_ANNOUNCEMENTS_LIST))

    return render_template(
        "announcements/instructor_form.html", form=form, title="Editar Anuncio de Curso", announcement=announcement
    )


@instructor_announcements.route("/instructor/announcements/<announcement_id>/delete", methods=["POST"])
@login_required
@perfil_requerido("instructor")
def delete_announcement(announcement_id):
    """Eliminar un anuncio de curso."""
    announcement = database.session.get(Announcement, announcement_id)
    if not announcement or announcement.course_id is None:
        flash("Anuncio no encontrado o no es un anuncio de curso.", "error")
        return redirect(url_for(ROUTE_INSTRUCTOR_ANNOUNCEMENTS_LIST))

    # Verificar que el instructor tenga acceso al curso
    instructor_courses = get_instructor_courses(current_user)
    course_ids = [course.codigo for course in instructor_courses]

    if announcement.course_id not in course_ids:
        flash("No tienes permisos para eliminar este anuncio.", "error")
        return redirect(url_for(ROUTE_INSTRUCTOR_ANNOUNCEMENTS_LIST))

    database.session.delete(announcement)
    database.session.commit()

    flash("Anuncio de curso eliminado exitosamente.", "success")
    return redirect(url_for(ROUTE_INSTRUCTOR_ANNOUNCEMENTS_LIST))
