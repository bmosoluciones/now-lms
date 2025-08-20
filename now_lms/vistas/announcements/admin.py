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

"""Admin announcements views."""

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
from now_lms.db import MAXIMO_RESULTADOS_EN_CONSULTA_PAGINADA, Announcement, database
from now_lms.forms import GlobalAnnouncementForm

# Route constants
ROUTE_ADMIN_ANNOUNCEMENTS_LIST = "admin_announcements.list_announcements"

admin_announcements = Blueprint("admin_announcements", __name__, template_folder=DIRECTORIO_PLANTILLAS)


@admin_announcements.route("/admin/announcements")
@login_required
@perfil_requerido("admin")
@cache.cached(timeout=60)
def list_announcements():
    """Lista de anuncios globales para administradores."""
    consulta = database.paginate(
        database.select(Announcement)
        .filter(Announcement.course_id.is_(None))
        .order_by(Announcement.is_sticky.desc(), Announcement.timestamp.desc()),
        page=request.args.get("page", default=1, type=int),
        max_per_page=MAXIMO_RESULTADOS_EN_CONSULTA_PAGINADA,
        count=True,
    )

    return render_template("announcements/admin_list.html", consulta=consulta)


@admin_announcements.route("/admin/announcements/new", methods=["GET", "POST"])
@login_required
@perfil_requerido("admin")
def new_announcement():
    """Formulario para crear un nuevo anuncio global."""
    form = GlobalAnnouncementForm()

    if form.validate_on_submit():
        announcement = Announcement(
            title=form.title.data,
            message=form.message.data,
            expires_at=form.expires_at.data,
            is_sticky=form.is_sticky.data,
            created_by_id=current_user.usuario,
            creado_por=current_user.usuario,
        )

        database.session.add(announcement)
        database.session.commit()

        flash("Anuncio global creado exitosamente.", "success")
        return redirect(url_for(ROUTE_ADMIN_ANNOUNCEMENTS_LIST))

    return render_template("announcements/admin_form.html", form=form, title="Nuevo Anuncio Global")


@admin_announcements.route("/admin/announcements/<announcement_id>/edit", methods=["GET", "POST"])
@login_required
@perfil_requerido("admin")
def edit_announcement(announcement_id):
    """Formulario para editar un anuncio global."""
    announcement = database.session.get(Announcement, announcement_id)
    if not announcement or announcement.course_id is not None:
        flash("Anuncio no encontrado o no es un anuncio global.", "error")
        return redirect(url_for(ROUTE_ADMIN_ANNOUNCEMENTS_LIST))

    form = GlobalAnnouncementForm(obj=announcement)

    if form.validate_on_submit():
        announcement.title = form.title.data
        announcement.message = form.message.data
        announcement.expires_at = form.expires_at.data
        announcement.is_sticky = form.is_sticky.data
        announcement.modificado_por = current_user.usuario

        database.session.commit()

        flash("Anuncio global actualizado exitosamente.", "success")
        return redirect(url_for(ROUTE_ADMIN_ANNOUNCEMENTS_LIST))

    return render_template(
        "announcements/admin_form.html", form=form, title="Editar Anuncio Global", announcement=announcement
    )


@admin_announcements.route("/admin/announcements/<announcement_id>/delete")
@login_required
@perfil_requerido("admin")
def delete_announcement(announcement_id):
    """Eliminar un anuncio global."""
    announcement = database.session.get(Announcement, announcement_id)
    if not announcement or announcement.course_id is not None:
        flash("Anuncio no encontrado o no es un anuncio global.", "error")
        return redirect(url_for(ROUTE_ADMIN_ANNOUNCEMENTS_LIST))

    database.session.delete(announcement)
    database.session.commit()

    flash("Anuncio global eliminado exitosamente.", "success")
    return redirect(url_for(ROUTE_ADMIN_ANNOUNCEMENTS_LIST))
