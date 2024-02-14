# Copyright 2022 -2023 BMO Soluciones, S.A.
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
# Contributors:
# - William José Moreno Reyes

"""
NOW Learning Management System.

Gestión de certificados.
"""

# ---------------------------------------------------------------------------------------
# Libreria estandar
# ---------------------------------------------------------------------------------------
from collections import OrderedDict
from datetime import datetime

# ---------------------------------------------------------------------------------------
# Librerias de terceros
# ---------------------------------------------------------------------------------------
from bleach import clean, linkify
from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, send_from_directory, url_for
from flask_login import current_user, login_required
from flask_uploads import UploadNotAllowed
from markdown import markdown
from sqlalchemy.exc import OperationalError
from ulid import ULID

# ---------------------------------------------------------------------------------------
# Recursos locales
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
from now_lms.config import DESARROLLO, DIRECTORIO_PLANTILLAS, audio, files, images
from now_lms.db import (
    Categoria,
    Curso,
    CursoRecurso,
    CursoRecursoAvance,
    CursoRecursoDescargable,
    CursoRecursoSlideShow,
    CursoSeccion,
    DocenteCurso,
    Etiqueta,
    Recurso,
    database,
)
from now_lms.db.tools import crear_indice_recurso
from now_lms.forms import (
    CurseForm,
    CursoRecursoArchivoAudio,
    CursoRecursoArchivoImagen,
    CursoRecursoArchivoPDF,
    CursoRecursoArchivoText,
    CursoRecursoExternalCode,
    CursoRecursoExternalLink,
    CursoRecursoMeet,
    CursoRecursoSlides,
    CursoRecursoVideoYoutube,
    CursoSeccionForm,
)
from now_lms.logs import log
from now_lms.misc import CURSO_NIVEL, HTML_TAGS, INICIO_SESION, TEMPLATES_BY_TYPE, TIPOS_RECURSOS

# ---------------------------------------------------------------------------------------
# Gestión de cursos.
# ---------------------------------------------------------------------------------------

RECURSO_AGREGADO = "Recurso agregado correctamente al curso."
ERROR_AL_AGREGAR_CURSO = "Hubo en error al crear el recurso."

course = Blueprint("course", __name__, template_folder=DIRECTORIO_PLANTILLAS)


@course.route("/course/<course_code>/view")
@cache.cached(unless=no_guardar_en_cache_global)
def curso(course_code):
    """Pagina principal del curso."""

    _curso = Curso.query.filter_by(codigo=course_code).first()

    if current_user.is_authenticated and request.args.get("inspect"):
        if current_user.tipo == "admin":
            acceso = True
            editable = True
        else:
            _consulta = database.select(DocenteCurso).filter(
                DocenteCurso.curso == course_code, DocenteCurso.usuario == current_user.usuario
            )
            acceso = database.session.execute(_consulta).first()
            if acceso:
                editable = True
    elif _curso.publico:
        acceso = _curso.estado == "open" and _curso.publico is True
        editable = False
    else:
        acceso = False

    if acceso:
        return render_template(
            "learning/curso/curso.html",
            curso=_curso,
            secciones=CursoSeccion.query.filter_by(curso=course_code).order_by(CursoSeccion.indice).all(),
            recursos=CursoRecurso.query.filter_by(curso=course_code).order_by(CursoRecurso.indice).all(),
            descargas=database.session.execute(
                database.select(Recurso).join(CursoRecursoDescargable).filter(CursoRecursoDescargable.curso == course_code)
            ).all(),  # El join devuelve una tuple.
            nivel=CURSO_NIVEL,
            tipo=TIPOS_RECURSOS,
            editable=editable,
        )

    else:
        abort(403)


@course.route("/course/<course_code>/enroll")
@login_required
@perfil_requerido("student")
def course_enroll(course_code):
    """Pagina para inscribirse a un curso."""

    _curso = Curso.query.filter_by(codigo=course_code).first()

    return render_template("learning/curso/enroll.html", curso=_curso)


@course.route("/course/<course_code>/take")
@login_required
@perfil_requerido("student")
@cache.cached(unless=no_guardar_en_cache_global)
def tomar_curso(course_code):
    """Pagina principal del curso."""

    if current_user.tipo == "student":
        return render_template(
            "learning/curso.html",
            curso=Curso.query.filter_by(codigo=course_code).first(),
            secciones=CursoSeccion.query.filter_by(curso=course_code).order_by(CursoSeccion.indice).all(),
            recursos=CursoRecurso.query.filter_by(curso=course_code).order_by(CursoRecurso.indice).all(),
            descargas=database.session.execute(
                database.select(Recurso).join(CursoRecursoDescargable).filter(CursoRecursoDescargable.curso == course_code)
            ).all(),  # El join devuelve una tuple.
            nivel=CURSO_NIVEL,
            tipo=TIPOS_RECURSOS,
        )
    else:
        return redirect(url_for("course.curso", course_code=course_code))


@course.route("/course/<course_code>/moderate")
@login_required
@perfil_requerido("moderator")
@cache.cached(unless=no_guardar_en_cache_global)
def moderar_curso(course_code):
    """Pagina principal del curso."""

    if current_user.tipo == "moderator" or current_user.tipo == "admin":
        return render_template(
            "learning/curso.html",
            curso=Curso.query.filter_by(codigo=course_code).first(),
            secciones=CursoSeccion.query.filter_by(curso=course_code).order_by(CursoSeccion.indice).all(),
            recursos=CursoRecurso.query.filter_by(curso=course_code).order_by(CursoRecurso.indice).all(),
            descargas=database.session.execute(
                database.select(Recurso).join(CursoRecursoDescargable).filter(CursoRecursoDescargable.curso == course_code)
            ).all(),  # El join devuelve una tuple.
            nivel=CURSO_NIVEL,
            tipo=TIPOS_RECURSOS,
        )
    else:
        return redirect(url_for("course.curso", course_code=course_code))


@course.route("/course/<course_code>/admin")
@login_required
@perfil_requerido("instructor")
@cache.cached(unless=no_guardar_en_cache_global)
def administrar_curso(course_code):
    """Pagina principal del curso."""

    return render_template(
        "learning/curso/admin.html",
        curso=Curso.query.filter_by(codigo=course_code).first(),
        secciones=CursoSeccion.query.filter_by(curso=course_code).order_by(CursoSeccion.indice).all(),
        recursos=CursoRecurso.query.filter_by(curso=course_code).order_by(CursoRecurso.indice).all(),
        descargas=database.session.execute(
            database.select(Recurso).join(CursoRecursoDescargable).filter(CursoRecursoDescargable.curso == course_code)
        ).all(),  # El join devuelve una tuple.
        nivel=CURSO_NIVEL,
        tipo=TIPOS_RECURSOS,
    )


@course.route("/course/new_curse", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def nuevo_curso():
    """Formulario para crear un nuevo usuario."""
    form = CurseForm()
    if form.validate_on_submit() or request.method == "POST":
        nuevo_curso_ = Curso(
            nombre=form.nombre.data,
            codigo=form.codigo.data,
            descripcion=form.descripcion.data,
            estado="draft",
            publico=form.publico.data,
            auditable=form.auditable.data,
            certificado=form.certificado.data,
            precio=form.precio.data,
            capacidad=form.capacidad.data,
            fecha_inicio=form.fecha_inicio.data,
            fecha_fin=form.fecha_fin.data,
            duracion=form.duracion.data,
            creado_por=current_user.usuario,
            nivel=form.nivel.data,
        )
        try:
            database.session.add(nuevo_curso_)
            database.session.commit()
            asignar_curso_a_instructor(curso_codigo=form.codigo.data, usuario_id=current_user.usuario)
            if "logo" in request.files:
                try:
                    picture_file = images.save(request.files["logo"], folder=form.codigo.data, name="logo.jpg")
                    if picture_file:
                        _curso = database.session.execute(
                            database.select(Curso).filter(Curso.codigo == form.codigo.data)
                        ).first()[0]
                        _curso.portada = True
                        database.session.commit()
                except UploadNotAllowed:  # pragma: no cover
                    log.warning("No se pudo actualizar la foto de perfil.")
                except AttributeError:  # pragma: no cover
                    log.warning("No se pudo actualizar la foto de perfil.")

            flash("Curso creado exitosamente.", "success")
            cache.delete("view/" + url_for("home.pagina_de_inicio"))
            return redirect(url_for("course.administrar_curso", course_code=form.codigo.data))
        except OperationalError:  # pragma: no cover
            flash("Hubo en error al crear su curso.", "warning")
            return redirect("/instructor")
    else:  # pragma: no cover
        return render_template("learning/nuevo_curso.html", form=form)


@course.route("/course/<course_code>/edit", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def editar_curso(course_code):
    """Editar pagina del curso."""

    curso_a_editar = Curso.query.filter_by(codigo=course_code).first()
    form = CurseForm(
        nivel=curso_a_editar.nivel, descripcion=curso_a_editar.descripcion, promocionado=curso_a_editar.promocionado
    )
    curso_url = url_for("course.administrar_curso", course_code=course_code)
    if form.validate_on_submit() or request.method == "POST":
        if curso_a_editar.promocionado is False and form.promocionado.data is True:
            curso_a_editar.promocionado = datetime.today()
        curso_a_editar.nombre = form.nombre.data
        curso_a_editar.descripcion = form.descripcion.data
        curso_a_editar.publico = form.publico.data
        curso_a_editar.auditable = form.auditable.data
        curso_a_editar.certificado = form.certificado.data
        curso_a_editar.precio = form.precio.data
        curso_a_editar.capacidad = form.capacidad.data
        curso_a_editar.fecha_inicio = form.fecha_inicio.data
        curso_a_editar.fecha_fin = form.fecha_fin.data
        curso_a_editar.duracion = form.duracion.data
        curso_a_editar.modificado_por = current_user.usuario
        curso_a_editar.nivel = form.nivel.data
        curso_a_editar.promocionado = form.promocionado.data

        try:
            database.session.commit()
            if "logo" in request.files:
                try:
                    picture_file = images.save(request.files["logo"], folder=curso_a_editar.codigo, name="logo.jpg")
                    if picture_file:
                        curso_a_editar.portada = True
                        database.session.commit()
                except UploadNotAllowed:  # pragma: no cover
                    log.warning("No se pudo actualizar la portada del curso.")
            flash("Curso actualizado exitosamente.", "success")
            return redirect(curso_url)

        except OperationalError:  # pragma: no cover
            flash("Hubo en error al actualizar el curso.", "warning")
            return redirect(curso_url)

    return render_template("learning/edit_curso.html", form=form, curso=curso_a_editar)


@course.route("/course/<course_code>/new_seccion", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def nuevo_seccion(course_code):
    """Formulario para crear una nueva sección en el curso."""
    # Las seccion son contenedores de recursos.
    form = CursoSeccionForm()
    if form.validate_on_submit() or request.method == "POST":
        secciones = CursoSeccion.query.filter_by(curso=course_code).count()
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
            database.session.add(nueva_seccion)
            database.session.commit()
            flash("Sección agregada correctamente al curso.", "success")
            return redirect(url_for("course.administrar_curso", course_code=course_code))
        except OperationalError:  # pragma: no cover
            flash("Hubo en error al crear la seccion.", "warning")
            return redirect(url_for("course.administrar_curso", course_code=course_code))
    else:  # pragma: no cover
        return render_template("learning/nuevo_seccion.html", form=form)


@course.route("/course/<course_code>/<seccion>/edit", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def editar_seccion(course_code, seccion):
    """Formulario para editar una sección en el curso."""

    seccion_a_editar = CursoSeccion.query.get_or_404(seccion)
    form = CursoSeccionForm(nombre=seccion_a_editar.nombre, descripcion=seccion_a_editar.descripcion)
    if form.validate_on_submit() or request.method == "POST":
        seccion_a_editar.nombre = form.nombre.data
        seccion_a_editar.descripcion = form.descripcion.data
        seccion_a_editar.modificado_por = current_user.usuario
        seccion_a_editar.curso = course_code
        try:
            database.session.commit()
            flash("Sección modificada correctamente.", "success")
            return redirect(url_for("course.administrar_curso", course_code=course_code))
        except OperationalError:  # pragma: no cover
            flash("Hubo en error al actualizar la seccion.", "warning")
            return redirect(url_for("course.administrar_curso", course_code=course_code))
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
    return redirect(url_for("course.administrar_curso", course_code=course_code))


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
    return redirect(url_for("course.administrar_curso", course_code=course_code))


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
    return redirect(url_for("course.administrar_curso", course_code=cource_code))


@course.route("/course/<curso_code>/delete_recurso/<seccion>/<id_>")
@login_required
@perfil_requerido("instructor")
def eliminar_recurso(curso_code, seccion, id_):
    """Elimina una seccion del curso."""
    CursoRecurso.query.filter(CursoRecurso.id == id_).delete()
    database.session.commit()
    reorganiza_indice_seccion(seccion=seccion)
    return redirect(url_for("course.administrar_curso", course_code=curso_code))


@course.route("/course/<curso_id>/delete_seccion/<id_>")
@login_required
@perfil_requerido("instructor")
def eliminar_seccion(curso_id, id_):
    """Elimina una seccion del curso."""
    CursoSeccion.query.filter(CursoSeccion.id == id_).delete()
    database.session.commit()
    reorganiza_indice_curso(codigo_curso=curso_id)
    return redirect(url_for("course.administrar_curso", course_code=curso_id))


@course.route("/course/change_curse_status")
@login_required
@perfil_requerido("instructor")
def cambiar_estatus_curso():
    """Actualiza el estatus de un curso."""
    cambia_estado_curso_por_id(
        id_curso=request.args.get("curse"), nuevo_estado=request.args.get("status"), usuario=current_user.usuario
    )
    return redirect(url_for("course.administrar_curso", course_code=request.args.get("curse")))


@course.route("/course/change_curse_public")
@login_required
@perfil_requerido("instructor")
def cambiar_curso_publico():
    """Actualiza el estado publico de un curso."""
    cambia_curso_publico(
        id_curso=request.args.get("curse"),
    )
    return redirect(url_for("course.administrar_curso", course_code=request.args.get("curse")))


@course.route("/course/change_curse_seccion_public")
@login_required
@perfil_requerido("instructor")
def cambiar_seccion_publico():
    """Actualiza el estado publico de un curso."""
    cambia_seccion_publico(
        codigo=request.args.get("codigo"),
    )
    return redirect(url_for("course.curso", course_code=request.args.get("course_code")))


@course.route("/course/<curso_id>/resource/<resource_type>/<codigo>")
def pagina_recurso(curso_id, resource_type, codigo):
    """Pagina de un recurso."""

    CURSO = database.session.query(Curso).filter(Curso.codigo == curso_id).first()
    RECURSO = database.session.query(CursoRecurso).filter(CursoRecurso.id == codigo).first()
    RECURSOS = database.session.query(CursoRecurso).filter(CursoRecurso.curso == curso_id).order_by(CursoRecurso.indice)
    SECCION = database.session.query(CursoSeccion).filter(CursoSeccion.id == RECURSO.seccion).first()
    SECCIONES = database.session.query(CursoSeccion).filter(CursoSeccion.curso == curso_id).order_by(CursoSeccion.indice)
    TEMPLATE = "learning/resources/" + TEMPLATES_BY_TYPE[resource_type]
    INDICE = crear_indice_recurso(codigo)

    if (current_user.is_authenticated and current_user.tipo == "admin") or RECURSO.publico is True:
        return render_template(
            TEMPLATE, curso=CURSO, recurso=RECURSO, recursos=RECURSOS, seccion=SECCION, secciones=SECCIONES, indice=INDICE
        )
    else:
        flash("No se encuentra autorizado a acceder al recurso solicitado.", "warning")
        return abort(403)


@course.route("/course/<curso_id>/resource/<resource_type>/<codigo>/complete")
@login_required
@perfil_requerido("student")
def marcar_recurso_completado(curso_id, resource_type, codigo):
    """Registra avance de un 100% en un recurso."""

    if current_user.is_authenticated and current_user.tipo == "admin":
        RECURSO = database.session.query(CursoRecurso).filter(CursoRecurso.id == codigo).first()

        if RECURSO:
            avance = CursoRecursoAvance(
                curso=curso_id,
                seccion=RECURSO.seccion,
                recurso=RECURSO.id,
                usuario=current_user.id,
                avance=100,
            )
            database.session.add(avance)
            database.session.commit()

        return redirect(url_for("course.pagina_recurso", curso_id=curso_id, resource_type=resource_type, codigo=RECURSO.id))
    else:
        flash("No se encuentra autorizado a acceder al recurso solicitado.", "warning")
        return abort(403)


@course.route("/course/<curso_id>/alternative/<codigo>/<order>")
@login_required
@perfil_requerido("student")
def pagina_recurso_alternativo(curso_id, codigo, order):
    """Pagina para seleccionar un curso alternativo."""

    CURSO = database.session.query(Curso).filter(Curso.codigo == curso_id).first()
    RECURSO = database.session.query(CursoRecurso).filter(CursoRecurso.id == codigo).first()
    SECCION = database.session.query(CursoSeccion).filter(CursoSeccion.id == RECURSO.seccion).first()
    INDICE = crear_indice_recurso(codigo)

    if order == "asc":
        consulta_recursos = (
            CursoRecurso.query.filter(
                CursoRecurso.seccion == RECURSO.seccion,
                CursoRecurso.indice >= RECURSO.indice,  # type     : ignore[union-attr]
            )
            .order_by(CursoRecurso.indice)
            .all()
        )

    else:  # Equivale a order == "desc".
        consulta_recursos = (
            CursoRecurso.query.filter(CursoRecurso.seccion == RECURSO.seccion, CursoRecurso.indice >= RECURSO.indice)
            .order_by(CursoRecurso.indice.desc())
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
        flash("No se encuentra autorizado a acceder al recurso solicitado.", "warning")
        return abort(403)


@course.route("/course/<course_code>/<seccion>/new_resource")
@login_required
@perfil_requerido("instructor")
def nuevo_recurso(course_code, seccion):
    """Página para seleccionar tipo de recurso."""
    if current_user.is_authenticated and current_user.tipo == "admin":
        return render_template("learning/resources_new/nuevo_recurso.html", id_curso=course_code, id_seccion=seccion)
    else:
        flash("No se encuentra autorizado a acceder al recurso solicitado.", "warning")
        return abort(403)


@course.route("/course/<course_code>/<seccion>/youtube/new", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def nuevo_recurso_youtube_video(course_code, seccion):
    """Formulario para crear un nuevo recurso tipo vídeo en Youtube."""
    form = CursoRecursoVideoYoutube()
    consulta_recursos = CursoRecurso.query.filter_by(seccion=seccion).count()
    nuevo_indice = int(consulta_recursos + 1)
    if form.validate_on_submit() or request.method == "POST":
        nuevo_recurso_ = CursoRecurso(
            curso=course_code,
            seccion=seccion,
            tipo="youtube",
            nombre=form.nombre.data,
            descripcion=form.descripcion.data,
            url=form.youtube_url.data,
            indice=nuevo_indice,
            creado_por=current_user.usuario,
        )
        try:
            database.session.add(nuevo_recurso_)
            database.session.commit()
            flash(RECURSO_AGREGADO, "success")
            return redirect(url_for("course.administrar_curso", course_code=course_code))
        except OperationalError:  # pragma: no cover
            flash(ERROR_AL_AGREGAR_CURSO, "warning")
            return redirect(url_for("course.curso", course_code=course_code))
    else:
        if current_user.tipo == "admin":
            return render_template(
                "learning/resources_new/nuevo_recurso_youtube.html", id_curso=course_code, id_seccion=seccion, form=form
            )
        else:
            flash("No se encuentra autorizado a acceder al recurso solicitado.", "warning")
            return abort(403)


@course.route("/course/<course_code>/<seccion>/text/new", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def nuevo_recurso_text(course_code, seccion):
    """Formulario para crear un nuevo documento de texto."""
    form = CursoRecursoArchivoText()
    consulta_recursos = CursoRecurso.query.filter_by(seccion=seccion).count()
    nuevo_indice = int(consulta_recursos + 1)
    if form.validate_on_submit() or request.method == "POST":
        nuevo_recurso_ = CursoRecurso(
            curso=course_code,
            seccion=seccion,
            tipo="text",
            nombre=form.nombre.data,
            descripcion=form.descripcion.data,
            indice=nuevo_indice,
            text=form.editor.data,
            creado_por=current_user.usuario,
        )
        try:
            database.session.add(nuevo_recurso_)
            database.session.commit()
            flash(RECURSO_AGREGADO, "success")
            return redirect(url_for("course.curso", course_code=course_code))
        except OperationalError:  # pragma: no cover
            flash(ERROR_AL_AGREGAR_CURSO, "warning")
            return redirect(url_for("course.administrar_curso", course_code=course_code))
    else:
        if current_user.tipo == "admin":
            return render_template(
                "learning/resources_new/nuevo_recurso_text.html", id_curso=course_code, id_seccion=seccion, form=form
            )
        else:
            flash("No se encuentra autorizado a acceder al recurso solicitado.", "warning")
            return abort(403)


@course.route("/course/<course_code>/<seccion>/link/new", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def nuevo_recurso_link(course_code, seccion):
    """Formulario para crear un nuevo documento de texto."""
    form = CursoRecursoExternalLink()
    recursos = CursoRecurso.query.filter_by(seccion=seccion).count()
    nuevo_indice = int(recursos + 1)
    if form.validate_on_submit() or request.method == "POST":
        nuevo_recurso_ = CursoRecurso(
            curso=course_code,
            seccion=seccion,
            tipo="link",
            nombre=form.nombre.data,
            descripcion=form.descripcion.data,
            indice=nuevo_indice,
            url=form.url.data,
            creado_por=current_user.usuario,
        )
        try:
            database.session.add(nuevo_recurso_)
            database.session.commit()
            flash(RECURSO_AGREGADO, "success")
            return redirect(url_for("course.administrar_curso", course_code=course_code))
        except OperationalError:  # pragma: no cover
            flash(ERROR_AL_AGREGAR_CURSO, "warning")
            return redirect(url_for("course.curso", course_code=course_code))
    else:
        if current_user.tipo == "admin":
            return render_template(
                "learning/resources_new/nuevo_recurso_link.html", id_curso=course_code, id_seccion=seccion, form=form
            )
        else:
            flash("No se encuentra autorizado a acceder al recurso solicitado.", "warning")
            return abort(403)


@course.route("/course/<course_code>/<seccion>/pdf/new", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def nuevo_recurso_pdf(course_code, seccion):
    """Formulario para crear un nuevo recurso tipo archivo en PDF."""
    form = CursoRecursoArchivoPDF()
    recursos = CursoRecurso.query.filter_by(seccion=seccion).count()
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
            indice=nuevo_indice,
            base_doc_url=files.name,
            doc=pdf_file,
            creado_por=current_user.usuario,
        )
        try:
            database.session.add(nuevo_recurso_)
            database.session.commit()
            flash("RECURSO_AGREGADO", "success")
            return redirect(url_for("course.administrar_curso", course_code=course_code))
        except OperationalError:  # pragma: no cover
            flash(ERROR_AL_AGREGAR_CURSO, "warning")
            return redirect(url_for("course.curso", course_code=course_code))
    else:
        if current_user.tipo == "admin":
            return render_template(
                "learning/resources_new/nuevo_recurso_pdf.html", id_curso=course_code, id_seccion=seccion, form=form
            )
        else:
            flash("No se encuentra autorizado a acceder al recurso solicitado.", "warning")
            return abort(403)


@course.route("/course/<course_code>/<seccion>/meet/new", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def nuevo_recurso_meet(course_code, seccion):
    """Formulario para crear un nuevo recurso tipo archivo en PDF."""
    form = CursoRecursoMeet()
    recursos = CursoRecurso.query.filter_by(seccion=seccion).count()
    nuevo_indice = int(recursos + 1)
    if form.validate_on_submit() or request.method == "POST":
        nuevo_recurso_ = CursoRecurso(
            curso=course_code,
            seccion=seccion,
            tipo="meet",
            nombre=form.nombre.data,
            descripcion=form.descripcion.data,
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
            return redirect(url_for("course.administrar_curso", course_code=course_code))
        except OperationalError:  # pragma: no cover
            flash(ERROR_AL_AGREGAR_CURSO, "warning")
            return redirect(url_for("course.curso", course_code=course_code))
    else:
        if current_user.tipo == "admin":
            return render_template(
                "learning/resources_new/nuevo_recurso_meet.html", id_curso=course_code, id_seccion=seccion, form=form
            )
        else:
            flash("No se encuentra autorizado a acceder al recurso solicitado.", "warning")
            return abort(403)


@course.route("/course/<course_code>/<seccion>/img/new", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def nuevo_recurso_img(course_code, seccion):
    """Formulario para crear un nuevo recurso tipo imagen."""
    form = CursoRecursoArchivoImagen()
    recursos = CursoRecurso.query.filter_by(seccion=seccion).count()
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
            indice=nuevo_indice,
            base_doc_url=images.name,
            doc=picture_file,
            creado_por=current_user.usuario,
        )
        try:
            database.session.add(nuevo_recurso_)
            database.session.commit()
            flash("RECURSO_AGREGADO", "success")
            return redirect(url_for("course.administrar_curso", course_code=course_code))
        except OperationalError:  # pragma: no cover
            flash(ERROR_AL_AGREGAR_CURSO, "warning")
            return redirect(url_for("course.curso", course_code=course_code))
    else:
        if current_user.tipo == "admin":
            return render_template(
                "learning/resources_new/nuevo_recurso_img.html", id_curso=course_code, id_seccion=seccion, form=form
            )
        else:
            flash("No se encuentra autorizado a acceder al recurso solicitado.", "warning")
            return abort(403)


@course.route("/course/<course_code>/<seccion>/audio/new", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def nuevo_recurso_audio(course_code, seccion):
    """Formulario para crear un nuevo recurso de audio"""
    form = CursoRecursoArchivoAudio()
    recursos = CursoRecurso.query.filter_by(seccion=seccion).count()
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
            indice=nuevo_indice,
            base_doc_url=audio.name,
            doc=audio_file,
            creado_por=current_user.usuario,
        )
        try:
            database.session.add(nuevo_recurso_)
            database.session.commit()
            flash("RECURSO_AGREGADO", "success")
            return redirect(url_for("course.administrar_curso", course_code=course_code))
        except OperationalError:  # pragma: no cover
            flash(ERROR_AL_AGREGAR_CURSO, "warning")
            return redirect(url_for("course.curso", course_code=course_code))
    else:
        if current_user.tipo == "admin":
            return render_template(
                "learning/resources_new/nuevo_recurso_mp3.html", id_curso=course_code, id_seccion=seccion, form=form
            )
        else:
            flash("No se encuentra autorizado a acceder al recurso solicitado.", "warning")
            return abort(403)


@course.route("/course/<course_code>/<seccion>/html/new", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def nuevo_recurso_html(course_code, seccion):
    """Formulario para crear un nuevo recurso tipo HTML externo."""
    form = CursoRecursoExternalCode()
    recursos = CursoRecurso.query.filter_by(seccion=seccion).count()
    nuevo_indice = int(recursos + 1)
    if form.validate_on_submit() or request.method == "POST":
        nuevo_recurso_ = CursoRecurso(
            curso=course_code,
            seccion=seccion,
            tipo="html",
            nombre=form.nombre.data,
            descripcion=form.descripcion.data,
            external_code=form.html_externo.data,
            indice=nuevo_indice,
            creado_por=current_user.usuario,
        )
        try:
            database.session.add(nuevo_recurso_)
            database.session.commit()
            flash("RECURSO_AGREGADO", "success")
            return redirect(url_for("course.administrar_curso", course_code=course_code))
        except OperationalError:  # pragma: no cover
            flash(ERROR_AL_AGREGAR_CURSO, "warning")
            return redirect(url_for("course.curso", course_code=course_code))
    else:
        if current_user.tipo == "admin":
            return render_template(
                "learning/resources_new/nuevo_recurso_html.html", id_curso=course_code, id_seccion=seccion, form=form
            )
        else:
            flash("No se encuentra autorizado a acceder al recurso solicitado.", "warning")
            return abort(403)


@course.route("/course/<course_code>/delete_logo")
@login_required
@perfil_requerido("instructor")
def elimina_logo(course_code):
    """Elimina logotipo del curso."""
    from now_lms.db.tools import elimina_logo_perzonalizado_curso

    if current_user.tipo == "admin":
        elimina_logo_perzonalizado_curso(course_code=course_code)
        return redirect(url_for("course.curso", course_code=course_code))
    else:
        flash("No se encuentra autorizado a acceder al recurso solicitado.", "warning")
        return abort(403)


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
    doc = CursoRecurso.query.filter(CursoRecurso.id == recurso_code, CursoRecurso.curso == course_code).first()
    config = current_app.upload_set_config.get(doc.base_doc_url)

    if current_user.is_authenticated:
        if doc.publico or current_user.tipo == "admin":
            return send_from_directory(config.destination, doc.doc)
        else:
            return abort(403)
    else:
        return redirect(INICIO_SESION)


@course.route("/course/<course_code>/external_code/<recurso_code>")
def external_code(course_code, recurso_code):
    """Devuelve un archivo desde el sistema de archivos."""

    recurso = CursoRecurso.query.filter(CursoRecurso.id == recurso_code, CursoRecurso.curso == course_code).first()

    if current_user.is_authenticated:
        if recurso.publico or current_user.tipo == "admin":

            return recurso.external_code

        else:
            return abort(403)
    else:
        return redirect(INICIO_SESION)


@course.route("/course/slide_show/<recurso_code>")
def slide_show(recurso_code):
    """Devuelve un archivo desde el sistema de archivos."""

    slide = CursoRecursoSlideShow.query.filter(CursoRecursoSlideShow.recurso == recurso_code).first()
    slides = CursoRecursoSlides.query.filter(CursoRecursoSlides.recurso == recurso_code).all()

    return render_template("/learning/resources/slide_show.html", resource=slide, slides=slides)


@course.route("/course/<course_code>/md_to_html/<recurso_code>")
def markdown_a_html(course_code, recurso_code):
    """Devuelve un texto en markdown como HTML."""
    recurso = CursoRecurso.query.filter(CursoRecurso.id == recurso_code, CursoRecurso.curso == course_code).first()
    allowed_tags = HTML_TAGS
    allowed_attrs = {"*": ["class"], "a": ["href", "rel"], "img": ["src", "alt"]}

    html = markdown(recurso.text)
    html_limpio = clean(linkify(html), tags=allowed_tags, attributes=allowed_attrs)

    return html_limpio


@course.route("/course/<course_code>/description")
def curso_descripcion_a_html(course_code):
    """Devuelve la descripción de un curso como HTML."""
    course = Curso.query.filter(Curso.codigo == course_code).first()
    allowed_tags = HTML_TAGS
    allowed_attrs = {"*": ["class"], "a": ["href", "rel"], "img": ["src", "alt"]}

    html = markdown(course.descripcion)
    html_limpio = clean(linkify(html), tags=allowed_tags, attributes=allowed_attrs)

    return html_limpio


@course.route("/course/<course_code>/description/<resource>")
def recurso_descripcion_a_html(course_code, resource):
    """Devuelve la descripción de un curso como HTML."""
    recurso = CursoRecurso.query.filter(CursoRecurso.id == resource, CursoRecurso.curso == course_code).first()
    allowed_tags = HTML_TAGS
    allowed_attrs = {"*": ["class"], "a": ["href", "rel"], "img": ["src", "alt"]}

    html = markdown(recurso.descripcion)
    html_limpio = clean(linkify(html), tags=allowed_tags, attributes=allowed_attrs)

    return html_limpio


@course.route("/course/explore")
@cache.cached(unless=no_guardar_en_cache_global)
def lista_cursos():
    """Lista de cursos."""

    if DESARROLLO:
        MAX_COUNT = 3
    else:
        MAX_COUNT = 30

    etiquetas = Etiqueta.query.all()
    categorias = Categoria.query.all()
    consulta_cursos = database.paginate(
        database.select(Curso).filter(Curso.publico == True, Curso.estado == "open"),  # noqa: E712
        page=request.args.get("page", default=1, type=int),
        max_per_page=MAX_COUNT,
        count=True,
    )
    # /explore?page=2&nivel=2&tag=python&category=programing
    if request.args.get("nivel") or request.args.get("tag") or request.args.get("category"):
        PARAMETROS = OrderedDict()
        for arg in request.url[request.url.find("?") + 1 :].split("&"):  # noqa: E203
            PARAMETROS[arg[: arg.find("=")]] = arg[arg.find("=") + 1 :]  # noqa: E203

            # El numero de pagina debe ser generado por el macro de paginación.
            try:
                del PARAMETROS["page"]
            except KeyError:
                pass
    else:
        PARAMETROS = None

    return render_template(
        "inicio/cursos.html", cursos=consulta_cursos, etiquetas=etiquetas, categorias=categorias, parametros=PARAMETROS
    )
