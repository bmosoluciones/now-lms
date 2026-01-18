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

"""
Blueprint de recursos del curso.

Contiene rutas para visualizar, completar y administrar recursos de cursos,
incluyendo slideshows, archivos, VTT, visor PDF, enlaces externos, y la
biblioteca del curso. Separado del blueprint `course` para evitar importaciones
circulares.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------
from datetime import datetime, timedelta, timezone
from os import listdir, path, remove, stat
from os.path import splitext
from typing import Any, Sequence

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------
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
from sqlalchemy import func
from sqlalchemy.exc import OperationalError
from ulid import ULID
from werkzeug.wrappers import Response

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms.auth import perfil_requerido
from now_lms.calendar_utils import update_meet_resource_events
from now_lms.config import DIRECTORIO_PLANTILLAS, audio, files, images
from now_lms.db import (
    Configuracion,
    CourseLibrary,
    Curso,
    CursoRecurso,
    CursoRecursoAvance,
    CursoRecursoSlides,
    CursoRecursoSlideShow,
    CursoSeccion,
    DocenteCurso,
    EstudianteCurso,
    Evaluation,
    EvaluationAttempt,
    Slide,
    SlideShowResource,
    database,
    select,
)
from now_lms.db.tools import (
    crear_indice_recurso,
    verifica_docente_asignado_a_curso,
    verifica_estudiante_asignado_a_curso,
)
from now_lms.forms import (
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
    SlideShowForm,
)
from now_lms.i18n import _
from now_lms.misc import INICIO_SESION, sanitize_slide_content
from now_lms.vistas.courses.base import (
    NO_AUTORIZADO_MSG,
    RECURSO_AGREGADO,
    ERROR_AL_AGREGAR_CURSO,
    TEMPLATE_SLIDE_SHOW,
    VISTA_ADMINISTRAR_CURSO,
)
from now_lms.vistas.courses.helpers import (
    validate_downloadable_file,
    get_site_config,
    sanitize_filename,
    get_course_library_path,
    ensure_course_library_directory,
    markdown2html,
    _actualizar_avance_curso,
    _get_course_evaluations_and_attempts,
    _get_user_resource_progress,
)


resources = Blueprint("resources", __name__, template_folder=DIRECTORIO_PLANTILLAS)

# Reused literals
PAGINA_RECURSO_ENDPOINT = ".pagina_recurso"
COURSE_LIBRARY_ENDPOINT = ".course_library"
MSG_RECURSO_NO_ENCONTRADO = "Recurso no encontrado."
MSG_RECURSO_ACTUALIZADO = "Recurso actualizado correctamente."
MSG_RECURSO_ERROR_ACTUALIZAR = "Hubo un error al actualizar el recurso."
TEMPLATE_LIBRARY_UPLOAD = "learning/curso/library_upload.html"


# Visualización y avance de recursos
@resources.route("/course/<curso_id>/resource/<resource_type>/<codigo>")
def pagina_recurso(curso_id: str, resource_type: str, codigo: str) -> str:
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


@resources.route("/course/<curso_id>/resource/<resource_type>/<codigo>/complete")
@login_required
@perfil_requerido("student")
def marcar_recurso_completado(curso_id: str, resource_type: str, codigo: str) -> Response:
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

                indice = crear_indice_recurso(codigo)
                if indice.next_resource:
                    if indice.next_is_alternative:
                        return redirect(
                            url_for(
                                ".pagina_recurso_alternativo",
                                curso_id=indice.next_resource.curso_id,
                                codigo=indice.next_resource.codigo,
                                order="asc",
                            )
                        )
                    return redirect(
                        url_for(
                            ".pagina_recurso",
                            curso_id=indice.next_resource.curso_id,
                            resource_type=indice.next_resource.resource_type,
                            codigo=indice.next_resource.codigo,
                        )
                    )
                return redirect(
                    url_for(PAGINA_RECURSO_ENDPOINT, curso_id=curso_id, resource_type=resource_type, codigo=codigo)
                )
            flash(NO_AUTORIZADO_MSG, "warning")
            return abort(403)
        flash(NO_AUTORIZADO_MSG, "warning")
        return abort(403)
    flash(NO_AUTORIZADO_MSG, "warning")
    return abort(403)


@resources.route("/course/<curso_id>/alternative/<codigo>/<order>")
@login_required
@perfil_requerido("student")
def pagina_recurso_alternativo(curso_id: str, codigo: str, order: str) -> str:
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
                    CursoRecurso.indice >= RECURSO.indice,
                )
                .order_by(CursoRecurso.indice)
            )
            .scalars()
            .all()
        )
    else:
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


# Nuevo/editar recursos por tipo
@resources.route("/course/<course_code>/<seccion>/new_resource")
@login_required
@perfil_requerido("instructor")
def nuevo_recurso(course_code: str, seccion: str) -> str:
    return render_template("learning/resources_new/nuevo_recurso.html", id_curso=course_code, id_seccion=seccion)


@resources.route("/course/<course_code>/<seccion>/html/new", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def nuevo_recurso_html(course_code: str, seccion: str) -> str | Response:
    """Formulario para crear un recurso HTML externo."""
    form = CursoRecursoExternalCode()
    recursos = database.session.execute(select(func.count(CursoRecurso.id)).filter_by(seccion=seccion)).scalar()
    nuevo_indice = int((recursos or 0) + 1)
    if form.validate_on_submit() or request.method == "POST":
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
            flash(RECURSO_AGREGADO, "success")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
        except OperationalError:
            flash(ERROR_AL_AGREGAR_CURSO, "warning")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
    return render_template(
        "learning/resources_new/nuevo_recurso_html.html", id_curso=course_code, id_seccion=seccion, form=form
    )


@resources.route("/course/<course_code>/<seccion>/html/<resource_id>/edit", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def editar_recurso_html(course_code: str, seccion: str, resource_id: str) -> str | Response:
    """Formulario para editar un recurso HTML externo."""
    recurso = database.session.execute(
        select(CursoRecurso).filter_by(id=resource_id, curso=course_code, seccion=seccion)
    ).scalar_one_or_none()
    if not recurso or recurso.tipo != "html":
        flash(MSG_RECURSO_NO_ENCONTRADO, "warning")
        return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))

    form = CursoRecursoExternalCode()

    if form.validate_on_submit() or request.method == "POST":
        recurso.nombre = form.nombre.data
        recurso.descripcion = form.descripcion.data
        recurso.requerido = form.requerido.data
        recurso.external_code = form.html_externo.data
        recurso.modificado_por = current_user.usuario

        config = database.session.execute(database.select(Configuracion)).scalars().first()
        if config and config.enable_html_preformatted_descriptions and hasattr(form, "descripcion_html_preformateado"):
            recurso.descripcion_html_preformateado = form.descripcion_html_preformateado.data or False
        else:
            recurso.descripcion_html_preformateado = False

        try:
            database.session.commit()
            flash(MSG_RECURSO_ACTUALIZADO, "success")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
        except OperationalError:
            flash(MSG_RECURSO_ERROR_ACTUALIZAR, "warning")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))

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


@resources.route("/course/<course_code>/<seccion>/youtube/new", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def nuevo_recurso_youtube_video(course_code: str, seccion: str) -> str | Response:
    form = CursoRecursoVideoYoutube()
    consulta_recursos = database.session.execute(select(func.count(CursoRecurso.id)).filter_by(seccion=seccion)).scalar()
    nuevo_indice = int((consulta_recursos or 0) + 1)
    if form.validate_on_submit() or request.method == "POST":
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


@resources.route("/course/<course_code>/<seccion>/youtube/<resource_id>/edit", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def editar_recurso_youtube_video(course_code: str, seccion: str, resource_id: str) -> str | Response:
    recurso = database.session.execute(
        select(CursoRecurso).filter_by(id=resource_id, curso=course_code, seccion=seccion)
    ).scalar_one_or_none()
    if not recurso or recurso.tipo != "youtube":
        flash(MSG_RECURSO_NO_ENCONTRADO, "warning")
        return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))

    form = CursoRecursoVideoYoutube()

    if form.validate_on_submit() or request.method == "POST":
        recurso.nombre = form.nombre.data
        recurso.descripcion = form.descripcion.data
        recurso.url = form.youtube_url.data
        recurso.requerido = form.requerido.data
        recurso.modificado = datetime.now(timezone.utc)
        recurso.modificado_por = current_user.usuario

        config = database.session.execute(database.select(Configuracion)).scalars().first()
        if config and config.enable_html_preformatted_descriptions and hasattr(form, "descripcion_html_preformateado"):
            recurso.descripcion_html_preformateado = form.descripcion_html_preformateado.data or False
        else:
            recurso.descripcion_html_preformateado = False

        try:
            database.session.commit()
            flash(MSG_RECURSO_ACTUALIZADO, "success")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
        except OperationalError:
            flash(MSG_RECURSO_ERROR_ACTUALIZAR, "warning")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
    else:
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


@resources.route("/course/<course_code>/<seccion>/text/new", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def nuevo_recurso_text(course_code: str, seccion: str) -> str | Response:
    form = CursoRecursoArchivoText()
    consulta_recursos = database.session.execute(select(func.count(CursoRecurso.id)).filter_by(seccion=seccion)).scalar()
    nuevo_indice = int((consulta_recursos or 0) + 1)
    if form.validate_on_submit() or request.method == "POST":
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


@resources.route("/course/<course_code>/<seccion>/text/<resource_id>/edit", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def editar_recurso_text(course_code: str, seccion: str, resource_id: str) -> str | Response:
    recurso = database.session.execute(
        select(CursoRecurso).filter_by(id=resource_id, curso=course_code, seccion=seccion)
    ).scalar_one_or_none()
    if not recurso or recurso.tipo != "text":
        flash(MSG_RECURSO_NO_ENCONTRADO, "warning")
        return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))

    form = CursoRecursoArchivoText()

    if form.validate_on_submit() or request.method == "POST":
        recurso.nombre = form.nombre.data
        recurso.descripcion = form.descripcion.data
        recurso.requerido = form.requerido.data
        recurso.text = form.editor.data
        recurso.modificado = datetime.now(timezone.utc)
        recurso.modificado_por = current_user.usuario

        config = database.session.execute(database.select(Configuracion)).scalars().first()
        if config and config.enable_html_preformatted_descriptions and hasattr(form, "descripcion_html_preformateado"):
            recurso.descripcion_html_preformateado = form.descripcion_html_preformateado.data or False
        else:
            recurso.descripcion_html_preformateado = False

        try:
            database.session.commit()
            flash(MSG_RECURSO_ACTUALIZADO, "success")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
        except OperationalError:
            flash(MSG_RECURSO_ERROR_ACTUALIZAR, "warning")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
    else:
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


@resources.route("/course/<course_code>/<seccion>/link/new", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def nuevo_recurso_link(course_code: str, seccion: str) -> str | Response:
    form = CursoRecursoExternalLink()
    recursos = database.session.execute(select(func.count(CursoRecurso.id)).filter_by(seccion=seccion)).scalar()
    nuevo_indice = int((recursos or 0) + 1)
    if form.validate_on_submit() or request.method == "POST":
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


@resources.route("/course/<course_code>/<seccion>/link/<resource_id>/edit", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def editar_recurso_link(course_code: str, seccion: str, resource_id: str) -> str | Response:
    recurso = database.session.execute(
        select(CursoRecurso).filter_by(id=resource_id, curso=course_code, seccion=seccion)
    ).scalar_one_or_none()
    if not recurso or recurso.tipo != "link":
        flash(MSG_RECURSO_NO_ENCONTRADO, "warning")
        return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))

    form = CursoRecursoExternalLink()

    if form.validate_on_submit() or request.method == "POST":
        recurso.nombre = form.nombre.data
        recurso.descripcion = form.descripcion.data
        recurso.requerido = form.requerido.data
        recurso.url = form.url.data
        recurso.modificado_por = current_user.usuario

        config = database.session.execute(database.select(Configuracion)).scalars().first()
        if config and config.enable_html_preformatted_descriptions and hasattr(form, "descripcion_html_preformateado"):
            recurso.descripcion_html_preformateado = form.descripcion_html_preformateado.data or False
        else:
            recurso.descripcion_html_preformateado = False

        try:
            database.session.commit()
            flash(MSG_RECURSO_ACTUALIZADO, "success")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
        except OperationalError:
            flash(MSG_RECURSO_ERROR_ACTUALIZAR, "warning")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
    else:
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


@resources.route("/course/<course_code>/<seccion>/pdf/new", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def nuevo_recurso_pdf(course_code: str, seccion: str) -> str | Response:
    form = CursoRecursoArchivoPDF()
    recursos = database.session.execute(select(func.count(CursoRecurso.id)).filter_by(seccion=seccion)).scalar()
    nuevo_indice = int((recursos or 0) + 1)
    if (form.validate_on_submit() or request.method == "POST") and "pdf" in request.files:
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


@resources.route("/course/<course_code>/<seccion>/pdf/<resource_id>/edit", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def editar_recurso_pdf(course_code: str, seccion: str, resource_id: str) -> str | Response:
    recurso = database.session.execute(
        select(CursoRecurso).filter_by(id=resource_id, curso=course_code, seccion=seccion)
    ).scalar_one_or_none()
    if not recurso or recurso.tipo != "pdf":
        flash(MSG_RECURSO_NO_ENCONTRADO, "warning")
        return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))

    form = CursoRecursoArchivoPDF()

    if form.validate_on_submit() or request.method == "POST":
        recurso.nombre = form.nombre.data
        recurso.descripcion = form.descripcion.data
        recurso.requerido = form.requerido.data
        recurso.modificado_por = current_user.usuario

        config = database.session.execute(database.select(Configuracion)).scalars().first()
        if config and config.enable_html_preformatted_descriptions and hasattr(form, "descripcion_html_preformateado"):
            recurso.descripcion_html_preformateado = form.descripcion_html_preformateado.data or False
        else:
            recurso.descripcion_html_preformateado = False

        if "pdf" in request.files and request.files["pdf"].filename:
            file_name = str(ULID()) + ".pdf"
            pdf_file = files.save(request.files["pdf"], folder=course_code, name=file_name)
            recurso.base_doc_url = files.name
            recurso.doc = pdf_file

        try:
            database.session.commit()
            flash(MSG_RECURSO_ACTUALIZADO, "success")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
        except OperationalError:
            flash(MSG_RECURSO_ERROR_ACTUALIZAR, "warning")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
    else:
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


@resources.route("/course/<course_code>/<seccion>/meet/new", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def nuevo_recurso_meet(course_code: str, seccion: str) -> str | Response:
    form = CursoRecursoMeet()
    recursos = database.session.execute(select(func.count(CursoRecurso.id)).filter_by(seccion=seccion)).scalar()
    nuevo_indice = int((recursos or 0) + 1)
    if form.validate_on_submit() or request.method == "POST":
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


@resources.route("/course/<course_code>/<seccion>/meet/<resource_id>/edit", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def editar_recurso_meet(course_code: str, seccion: str, resource_id: str) -> str | Response:
    recurso = database.session.execute(
        select(CursoRecurso).filter_by(id=resource_id, curso=course_code, seccion=seccion)
    ).scalar_one_or_none()
    if not recurso or recurso.tipo != "meet":
        flash(MSG_RECURSO_NO_ENCONTRADO, "warning")
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

        config = database.session.execute(database.select(Configuracion)).scalars().first()
        if config and config.enable_html_preformatted_descriptions and hasattr(form, "descripcion_html_preformateado"):
            recurso.descripcion_html_preformateado = form.descripcion_html_preformateado.data or False
        else:
            recurso.descripcion_html_preformateado = False

        try:
            database.session.commit()
            update_meet_resource_events(resource_id)
            flash(MSG_RECURSO_ACTUALIZADO, "success")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
        except OperationalError:
            flash(MSG_RECURSO_ERROR_ACTUALIZAR, "warning")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
    else:
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


@resources.route("/course/<course_code>/<seccion>/img/new", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def nuevo_recurso_img(course_code: str, seccion: str) -> str | Response:
    form = CursoRecursoArchivoImagen()
    recursos = database.session.execute(select(func.count(CursoRecurso.id)).filter_by(seccion=seccion)).scalar()
    nuevo_indice = int((recursos or 0) + 1)
    if (form.validate_on_submit() or request.method == "POST") and "img" in request.files:
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


@resources.route("/course/<course_code>/<seccion>/img/<resource_id>/edit", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def editar_recurso_img(course_code: str, seccion: str, resource_id: str) -> str | Response:
    recurso = database.session.execute(
        select(CursoRecurso).filter_by(id=resource_id, curso=course_code, seccion=seccion)
    ).scalar_one_or_none()
    if not recurso or recurso.tipo != "img":
        flash(MSG_RECURSO_NO_ENCONTRADO, "warning")
        return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))

    form = CursoRecursoArchivoImagen()

    if form.validate_on_submit() or request.method == "POST":
        recurso.nombre = form.nombre.data
        recurso.descripcion = form.descripcion.data
        recurso.requerido = form.requerido.data
        recurso.modificado_por = current_user.usuario

        config = database.session.execute(database.select(Configuracion)).scalars().first()
        if config and config.enable_html_preformatted_descriptions and hasattr(form, "descripcion_html_preformateado"):
            recurso.descripcion_html_preformateado = form.descripcion_html_preformateado.data or False
        else:
            recurso.descripcion_html_preformateado = False

        if "img" in request.files and request.files["img"].filename:
            img_filename = request.files["img"].filename
            img_ext = splitext(img_filename)[1]
            file_name = str(ULID()) + (img_ext or "")
            picture_file = images.save(request.files["img"], folder=course_code, name=file_name)
            recurso.base_doc_url = images.name
            recurso.doc = picture_file

        try:
            database.session.commit()
            flash(MSG_RECURSO_ACTUALIZADO, "success")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
        except OperationalError:
            flash(MSG_RECURSO_ERROR_ACTUALIZAR, "warning")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
    else:
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


@resources.route("/course/<course_code>/<seccion>/audio/new", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def nuevo_recurso_audio(course_code: str, seccion: str) -> str | Response:
    form = CursoRecursoArchivoAudio()
    recursos = database.session.execute(select(func.count(CursoRecurso.id)).filter_by(seccion=seccion)).scalar()
    nuevo_indice = int((recursos or 0) + 1)
    if (form.validate_on_submit() or request.method == "POST") and "audio" in request.files:
        config = database.session.execute(database.select(Configuracion)).scalars().first()
        html_preformateado = False
        if config and config.enable_html_preformatted_descriptions and hasattr(form, "descripcion_html_preformateado"):
            html_preformateado = form.descripcion_html_preformateado.data or False

        audio_filename = request.files["audio"].filename
        audio_ext = splitext(audio_filename or "")[1]
        audio_name = str(ULID()) + (audio_ext or "")
        audio_file = audio.save(request.files["audio"], folder=course_code, name=audio_name)

        subtitle_vtt_content = None
        if "vtt_subtitle" in request.files and request.files["vtt_subtitle"].filename:
            vtt_file = request.files["vtt_subtitle"]
            if vtt_file.filename.endswith(".vtt"):
                subtitle_vtt_content = vtt_file.read().decode("utf-8")

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


@resources.route("/course/<course_code>/<seccion>/audio/<resource_id>/edit", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def editar_recurso_audio(course_code: str, seccion: str, resource_id: str) -> str | Response:
    recurso = database.session.execute(
        select(CursoRecurso).filter_by(id=resource_id, curso=course_code, seccion=seccion)
    ).scalar_one_or_none()
    if not recurso or recurso.tipo != "mp3":
        flash(MSG_RECURSO_NO_ENCONTRADO, "warning")
        return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))

    form = CursoRecursoArchivoAudio()

    if form.validate_on_submit() or request.method == "POST":
        recurso.nombre = form.nombre.data
        recurso.descripcion = form.descripcion.data
        recurso.requerido = form.requerido.data
        recurso.modificado_por = current_user.usuario

        config = database.session.execute(database.select(Configuracion)).scalars().first()
        if config and config.enable_html_preformatted_descriptions and hasattr(form, "descripcion_html_preformateado"):
            recurso.descripcion_html_preformateado = form.descripcion_html_preformateado.data or False
        else:
            recurso.descripcion_html_preformateado = False

        if "audio" in request.files and request.files["audio"].filename:
            audio_filename = request.files["audio"].filename
            audio_ext = splitext(audio_filename or "")[1]
            audio_name = str(ULID()) + (audio_ext or "")
            audio_file = audio.save(request.files["audio"], folder=course_code, name=audio_name)
            recurso.base_doc_url = audio.name
            recurso.doc = audio_file

        if "vtt_subtitle" in request.files and request.files["vtt_subtitle"].filename:
            vtt_file = request.files["vtt_subtitle"]
            if vtt_file.filename.endswith(".vtt"):
                recurso.subtitle_vtt = vtt_file.read().decode("utf-8")

        if "vtt_subtitle_secondary" in request.files and request.files["vtt_subtitle_secondary"].filename:
            vtt_secondary_file = request.files["vtt_subtitle_secondary"]
            if vtt_secondary_file.filename.endswith(".vtt"):
                recurso.subtitle_vtt_secondary = vtt_secondary_file.read().decode("utf-8")

        try:
            database.session.commit()
            flash(MSG_RECURSO_ACTUALIZADO, "success")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
        except OperationalError:
            flash(MSG_RECURSO_ERROR_ACTUALIZAR, "warning")
            return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))
    else:
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


@resources.route("/course/<course_code>/<seccion>/descargable/new", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def nuevo_recurso_descargable(course_code: str, seccion: str) -> str | Response:
    site_config = get_site_config()
    if not site_config.enable_file_uploads:
        flash("La subida de archivos descargables no está habilitada por el administrador.", "warning")
        return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))

    form = CursoRecursoArchivoDescargable()
    recursos = database.session.execute(select(func.count(CursoRecurso.id)).filter_by(seccion=seccion)).scalar()
    nuevo_indice = int((recursos or 0) + 1)

    if (form.validate_on_submit() or request.method == "POST") and "archivo" in request.files:
        uploaded_file = request.files["archivo"]

        is_valid, error_msg = validate_downloadable_file(uploaded_file, site_config.max_file_size)
        if not is_valid:
            flash(error_msg, "warning")
            return render_template(
                "learning/resources_new/nuevo_recurso_descargable.html", id_curso=course_code, id_seccion=seccion, form=form
            )

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


@resources.route("/course/<course_code>/<seccion>/descargable/<resource_id>/edit", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def editar_recurso_descargable(course_code: str, seccion: str, resource_id: str) -> str | Response:
    site_config = get_site_config()
    if not site_config.enable_file_uploads:
        flash("La subida de archivos descargables no está habilitada por el administrador.", "warning")
        return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))

    recurso = database.session.execute(select(CursoRecurso).filter_by(id=resource_id)).scalar_one()
    form = CursoRecursoArchivoDescargable()

    if form.validate_on_submit() or request.method == "POST":
        if "archivo" in request.files and request.files["archivo"].filename:
            uploaded_file = request.files["archivo"]
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

            filename = uploaded_file.filename
            file_ext = splitext(filename or "")[1]
            file_name = str(ULID()) + (file_ext or "")

            try:
                saved_file = files.save(uploaded_file, folder=course_code, name=file_name)
                recurso.doc = saved_file
            except UploadNotAllowed:
                flash("Tipo de archivo no permitido.", "warning")
                return redirect(url_for(VISTA_ADMINISTRAR_CURSO, course_code=course_code))

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


# Slideshow
@resources.route("/course/<course_code>/<seccion>/slides/new", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def nuevo_recurso_slideshow(course_code: str, seccion: str) -> str | Response:
    form = SlideShowForm()
    if form.validate_on_submit():
        try:
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
            database.session.flush()

            slideshow = SlideShowResource(
                course_id=course_code, title=form.nombre.data, theme=form.theme.data, creado_por=current_user.usuario
            )
            database.session.add(slideshow)
            database.session.flush()

            nuevo_recurso_obj.external_code = slideshow.id

            database.session.commit()
            flash(RECURSO_AGREGADO, "success")
            return redirect(url_for(".editar_slideshow", course_code=course_code, slideshow_id=slideshow.id))

        except Exception as e:
            database.session.rollback()
            flash(f"Error al crear la presentación: {str(e)}", "error")

    return render_template(
        "learning/resources_new/nuevo_recurso_slides.html", id_curso=course_code, id_seccion=seccion, form=form
    )


@resources.route("/course/<course_code>/slideshow/<slideshow_id>/edit", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def editar_slideshow(course_code: str, slideshow_id: str) -> str | Response:
    slideshow = database.session.get(SlideShowResource, slideshow_id)
    if not slideshow or slideshow.course_id != course_code:
        flash("Presentación no encontrada.", "error")
        return abort(404)

    slides = (
        database.session.execute(select(Slide).filter_by(slide_show_id=slideshow_id).order_by(Slide.order)).scalars().all()
    )

    if request.method == "POST":
        try:
            slideshow.title = request.form.get("title", slideshow.title)
            slideshow.theme = request.form.get("theme", slideshow.theme)
            slideshow.modificado_por = current_user.usuario

            slide_count = int(request.form.get("slide_count", 0))
            existing_orders = []
            for i in range(slide_count):
                order = int(request.form.get(f"slide_{i}_order", i + 1))
                existing_orders.append(order)

            for slide in slides:
                if slide.order not in existing_orders:
                    database.session.delete(slide)

            for i in range(slide_count):
                slide_title = request.form.get(f"slide_{i}_title", "")
                slide_content = request.form.get(f"slide_{i}_content", "")
                slide_order = int(request.form.get(f"slide_{i}_order", i + 1))
                slide_id = request.form.get(f"slide_{i}_id")

                if slide_title and slide_content:
                    clean_content = sanitize_slide_content(slide_content)

                    if slide_id:
                        existing_slide = database.session.get(Slide, slide_id)
                        if existing_slide is not None and existing_slide.slide_show_id == slideshow_id:
                            existing_slide.title = slide_title
                            existing_slide.content = clean_content
                            existing_slide.order = slide_order
                            existing_slide.modificado_por = current_user.usuario
                    else:
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

        return redirect(url_for(".editar_slideshow", course_code=course_code, slideshow_id=slideshow_id))

    return render_template(
        "learning/resources_new/editar_slideshow.html", slideshow=slideshow, slides=slides, course_code=course_code
    )


@resources.route("/course/<course_code>/slideshow/<slideshow_id>/preview")
@login_required
def preview_slideshow(course_code: str, slideshow_id: str) -> str:
    slideshow = database.session.get(SlideShowResource, slideshow_id)
    if not slideshow or slideshow.course_id != course_code:
        abort(404)

    slides = (
        database.session.execute(select(Slide).filter_by(slide_show_id=slideshow_id).order_by(Slide.order)).scalars().all()
    )

    return render_template(TEMPLATE_SLIDE_SHOW, slideshow=slideshow, slides=slides)


@resources.route("/course/<course_code>/files/<recurso_code>")
def recurso_file(course_code: str, recurso_code: str) -> Response:
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


@resources.route("/course/<course_code>/vtt/<recurso_code>")
def recurso_vtt(course_code: str, recurso_code: str) -> Response:
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


@resources.route("/course/<course_code>/vtt_secondary/<recurso_code>")
def recurso_vtt_secondary(course_code: str, recurso_code: str) -> Response:
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


@resources.route("/course/<course_code>/pdf_viewer/<recurso_code>")
def pdf_viewer(course_code: str, recurso_code: str) -> str | Response:
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


@resources.route("/course/<course_code>/external_code/<recurso_code>")
def external_code(course_code: str, recurso_code: str) -> str | Response:
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


@resources.route("/course/slide_show/<recurso_code>")
def slide_show(recurso_code: str) -> str:
    recurso = database.session.execute(select(CursoRecurso).filter(CursoRecurso.id == recurso_code)).scalars().first()
    if not recurso:
        abort(404)

    if recurso.external_code:
        slideshow = database.session.get(SlideShowResource, recurso.external_code)
        if slideshow:
            slides = (
                database.session.execute(select(Slide).filter_by(slide_show_id=slideshow.id).order_by(Slide.order))
                .scalars()
                .all()
            )
            return render_template(TEMPLATE_SLIDE_SHOW, slideshow=slideshow, slides=slides, resource=recurso)

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

    flash("Presentación no encontrada.", "error")
    abort(404)


# Biblioteca del curso
@resources.route("/course/<course_code>/library")
@login_required
@perfil_requerido("instructor")
def course_library(course_code: str) -> str:
    _curso = database.session.execute(database.select(Curso).filter_by(codigo=course_code)).scalar_one_or_none()
    if not _curso:
        abort(404)

    if current_user.tipo != "admin":
        instructor_assignment = database.session.execute(
            database.select(DocenteCurso).filter_by(curso=course_code, usuario=current_user.usuario)
        ).scalar_one_or_none()
        if not instructor_assignment:
            abort(403)

    library_files_db = (
        database.session.execute(database.select(CourseLibrary).filter_by(curso=course_code).order_by(CourseLibrary.nombre))
        .scalars()
        .all()
    )
    db_files_map = {file_record.filename: file_record for file_record in library_files_db}
    library_path = get_course_library_path(course_code)
    physical_files = set()
    if path.exists(library_path):
        for filename in listdir(library_path):
            file_path = path.join(library_path, filename)
            if path.isfile(file_path):
                physical_files.add(filename)

    library_files = []
    for file_record in library_files_db:
        library_files.append(
            {
                "id": file_record.id,
                "name": file_record.filename,
                "display_name": file_record.nombre,
                "description": file_record.descripcion,
                "size": file_record.file_size,
                "modified": file_record.modificado or file_record.timestamp,
                "url": url_for(".serve_library_file", course_code=course_code, filename=file_record.filename),
                "has_db_record": True,
                "file_exists": file_record.filename in physical_files,
            }
        )

    for filename in physical_files:
        if filename not in db_files_map:
            file_path = path.join(library_path, filename)
            file_stat = stat(file_path)
            library_files.append(
                {
                    "id": None,
                    "name": filename,
                    "display_name": filename,
                    "description": _("Archivo subido manualmente"),
                    "size": file_stat.st_size,
                    "modified": datetime.fromtimestamp(file_stat.st_mtime),
                    "url": url_for(".serve_library_file", course_code=course_code, filename=filename),
                    "has_db_record": False,
                    "file_exists": True,
                }
            )

    library_files.sort(key=lambda x: x["display_name"].lower())
    return render_template("learning/curso/library.html", curso=_curso, library_files=library_files)


@resources.route("/course/<course_code>/library/new", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def upload_library_file(course_code: str) -> str | Response:
    site_config = get_site_config()
    if not site_config.enable_file_uploads:
        flash("La subida de archivos no está habilitada por el administrador.", "warning")
        return redirect(url_for(COURSE_LIBRARY_ENDPOINT, course_code=course_code))

    _curso = database.session.execute(database.select(Curso).filter_by(codigo=course_code)).scalar_one_or_none()
    if not _curso:
        abort(404)

    if current_user.tipo != "admin":
        instructor_assignment = database.session.execute(
            database.select(DocenteCurso).filter_by(curso=course_code, usuario=current_user.usuario)
        ).scalar_one_or_none()
        if not instructor_assignment:
            abort(403)

    form = CursoLibraryFileForm()

    if (form.validate_on_submit() or request.method == "POST") and "archivo" in request.files:
        uploaded_file = request.files["archivo"]

        is_valid, error_msg = validate_downloadable_file(uploaded_file, site_config.max_file_size)
        if not is_valid:
            flash(error_msg, "warning")
            return render_template(TEMPLATE_LIBRARY_UPLOAD, curso=_curso, form=form, max_file_size=site_config.max_file_size)

        original_filename = uploaded_file.filename or ""
        sanitized_filename = sanitize_filename(original_filename)
        if not sanitized_filename:
            flash("Nombre de archivo inválido.", "warning")
            return render_template(TEMPLATE_LIBRARY_UPLOAD, curso=_curso, form=form, max_file_size=site_config.max_file_size)

        try:
            library_path = ensure_course_library_directory(course_code)

            existing_file = database.session.execute(
                database.select(CourseLibrary).filter_by(curso=course_code, filename=sanitized_filename)
            ).scalar_one_or_none()
            if existing_file:
                flash(f"Ya existe un archivo con el nombre '{sanitized_filename}' en la biblioteca.", "warning")
                return render_template(
                    TEMPLATE_LIBRARY_UPLOAD, curso=_curso, form=form, max_file_size=site_config.max_file_size
                )

            destination_path = path.join(library_path, sanitized_filename)
            uploaded_file.save(destination_path)
            file_size = uploaded_file.content_length or path.getsize(destination_path)

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
            return redirect(url_for(COURSE_LIBRARY_ENDPOINT, course_code=course_code))

        except Exception as e:
            database.session.rollback()
            try:
                destination_path = path.join(library_path, sanitized_filename)
                if path.exists(destination_path):
                    path.remove(destination_path)
            except Exception:
                pass

            flash(f"Error al subir el archivo: {str(e)}", "error")
            return render_template(TEMPLATE_LIBRARY_UPLOAD, curso=_curso, form=form, max_file_size=site_config.max_file_size)

    return render_template(TEMPLATE_LIBRARY_UPLOAD, curso=_curso, form=form, max_file_size=site_config.max_file_size)


@resources.route("/course/<course_code>/library/file/<filename>")
@login_required
def serve_library_file(course_code: str, filename: str) -> Response:
    _curso = database.session.execute(database.select(Curso).filter_by(codigo=course_code)).scalar_one_or_none()
    if not _curso:
        abort(404)

    has_access = False
    if current_user.tipo == "admin":
        has_access = True
    else:
        instructor_assignment = database.session.execute(
            database.select(DocenteCurso).filter_by(curso=course_code, usuario=current_user.usuario)
        ).scalar_one_or_none()
        if instructor_assignment:
            has_access = True
        else:
            student_enrollment = database.session.execute(
                database.select(EstudianteCurso).filter_by(curso=course_code, usuario=current_user.usuario, vigente=True)
            ).scalar_one_or_none()
            if student_enrollment:
                has_access = True

    if not has_access:
        abort(403)

    safe_filename = path.basename(filename)
    library_path = get_course_library_path(course_code)
    file_path = path.join(library_path, safe_filename)
    if not path.exists(file_path) or not path.isfile(file_path):
        abort(404)

    try:
        return send_from_directory(library_path, safe_filename, as_attachment=True)
    except Exception:
        abort(404)


@resources.route("/course/<course_code>/library/delete/<file_id>", methods=["POST"])
@login_required
@perfil_requerido("instructor")
def delete_library_file(course_code: str, file_id: str) -> Response:
    _curso = database.session.execute(database.select(Curso).filter_by(codigo=course_code)).scalar_one_or_none()
    if not _curso:
        abort(404)

    if current_user.tipo != "admin":
        instructor_assignment = database.session.execute(
            database.select(DocenteCurso).filter_by(curso=course_code, usuario=current_user.usuario)
        ).scalar_one_or_none()
        if not instructor_assignment:
            abort(403)

    library_file = database.session.execute(
        database.select(CourseLibrary).filter_by(id=file_id, curso=course_code)
    ).scalar_one_or_none()

    if not library_file:
        flash(_("Archivo no encontrado en la biblioteca."), "warning")
        return redirect(url_for(COURSE_LIBRARY_ENDPOINT, course_code=course_code))

    try:
        library_path = get_course_library_path(course_code)
        file_path = path.join(library_path, library_file.filename)

        if path.exists(file_path):
            remove(file_path)

        database.session.delete(library_file)
        database.session.commit()

        flash(_("Archivo eliminado exitosamente de la biblioteca."), "success")

    except Exception as e:
        database.session.rollback()
        flash(f"Error al eliminar el archivo: {str(e)}", "error")

    return redirect(url_for(COURSE_LIBRARY_ENDPOINT, course_code=course_code))


# Calendarios para recursos meet
def _generate_meet_ics_content(recurso: Any) -> str:
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//NOW LMS//Meet Calendar//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
    ]

    if recurso.fecha and recurso.hora_inicio:
        start_datetime = datetime.combine(recurso.fecha, recurso.hora_inicio)
        if recurso.hora_fin:
            end_datetime = datetime.combine(recurso.fecha, recurso.hora_fin)
        else:
            end_datetime = start_datetime + timedelta(hours=1)

        start_str = start_datetime.strftime("%Y%m%dT%H%M%S")
        end_str = end_datetime.strftime("%Y%m%dT%H%M%S")

        lines.extend(
            [
                "BEGIN:VEVENT",
                f"DTSTART:{start_str}",
                f"DTEND:{end_str}",
                f"SUMMARY:{recurso.nombre}",
                f"DESCRIPTION:{recurso.descripcion or ''}",
                f"LOCATION:{recurso.notes or 'En línea'}",
                "END:VEVENT",
            ]
        )

    lines.append("END:VCALENDAR")
    return "\r\n".join(lines)


@resources.route("/course/<course_code>/resource/meet/<codigo>/calendar.ics")
@login_required
def download_meet_calendar(course_code: str, codigo: str) -> Response:
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

    ics_content = _generate_meet_ics_content(recurso)
    filename = f"meet-{recurso.nombre[:20].replace(' ', '-')}-{recurso.id}.ics"
    return Response(
        ics_content,
        mimetype="text/calendar",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@resources.route("/course/<course_code>/resource/meet/<codigo>/google-calendar")
@login_required
def google_calendar_link(course_code: str, codigo: str) -> Response:
    from urllib.parse import quote

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

    if recurso.fecha and recurso.hora_inicio:
        start_datetime = datetime.combine(recurso.fecha, recurso.hora_inicio)
        end_datetime = (
            datetime.combine(recurso.fecha, recurso.hora_fin) if recurso.hora_fin else start_datetime + timedelta(hours=1)
        )
        start_str = start_datetime.strftime("%Y%m%dT%H%M%S")
        end_str = end_datetime.strftime("%Y%m%dT%H%M%S")

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
    return redirect(url_for(PAGINA_RECURSO_ENDPOINT, curso_id=course_code, resource_type=recurso.tipo, codigo=codigo))


@resources.route("/course/<course_code>/resource/meet/<codigo>/outlook-calendar")
@login_required
def outlook_calendar_link(course_code: str, codigo: str) -> str | Response:
    from urllib.parse import quote

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

    if recurso.fecha and recurso.hora_inicio:
        start_datetime = datetime.combine(recurso.fecha, recurso.hora_inicio)
        end_datetime = (
            datetime.combine(recurso.fecha, recurso.hora_fin) if recurso.hora_fin else start_datetime + timedelta(hours=1)
        )
        start_str = start_datetime.strftime("%Y%m%dT%H%M%S")
        end_str = end_datetime.strftime("%Y%m%dT%H%M%S")

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
    return redirect(url_for(PAGINA_RECURSO_ENDPOINT, curso_id=course_code, resource_type=recurso.tipo, codigo=codigo))
