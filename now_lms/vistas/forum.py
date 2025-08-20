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

"""Vistas para la funcionalidad del foro."""

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------
from bleach import clean
from flask import Blueprint, abort, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from markdown import markdown

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms.db import Curso, DocenteCurso, EstudianteCurso, ForoMensaje, ModeradorCurso, database, select
from now_lms.forms import ForoMensajeForm, ForoMensajeRespuestaForm

# ---------------------------------------------------------------------------------------
# Configuration constants
# ---------------------------------------------------------------------------------------

# Configuración de HTML permitido para sanitización
ALLOWED_HTML_TAGS = [
    "p",
    "br",
    "strong",
    "em",
    "u",
    "ol",
    "ul",
    "li",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "blockquote",
    "code",
    "pre",
    "a",
    "img",
]
ALLOWED_HTML_ATTRS = {
    "a": ["href", "title"],
    "img": ["src", "alt", "title", "width", "height"],
}

# Route constants
ROUTE_FORUM_VER_FORO = "forum.ver_foro"

# ---------------------------------------------------------------------------------------
# Blueprint definition
# ---------------------------------------------------------------------------------------
forum = Blueprint("forum", __name__)


# ---------------------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------------------


def verificar_acceso_curso(course_code, usuario_id):
    """Verifica si un usuario tiene acceso al curso."""
    # Verificar si es instructor
    instructor = (
        database.session.execute(select(DocenteCurso).filter_by(curso=course_code, usuario=usuario_id, vigente=True))
        .scalars()
        .first()
    )
    if instructor:
        return True, "instructor"

    # Verificar si es moderador
    moderador = (
        database.session.execute(select(ModeradorCurso).filter_by(curso=course_code, usuario=usuario_id, vigente=True))
        .scalars()
        .first()
    )
    if moderador:
        return True, "moderador"

    # Verificar si es estudiante
    estudiante = (
        database.session.execute(select(EstudianteCurso).filter_by(curso=course_code, usuario=usuario_id, vigente=True))
        .scalars()
        .first()
    )
    if estudiante:
        return True, "estudiante"

    return False, None


def puede_cerrar_mensajes(role, user_type):
    """Verifica si un usuario puede cerrar mensajes del foro."""
    return role in ["instructor", "moderador"] or user_type == "admin"


def markdown_to_html(contenido_markdown):
    """Convierte markdown a HTML y lo sanitiza."""
    html = markdown(contenido_markdown, extensions=["nl2br", "codehilite"])
    return clean(html, tags=ALLOWED_HTML_TAGS, attributes=ALLOWED_HTML_ATTRS)


# ---------------------------------------------------------------------------------------
# Forum routes - Course forum functionality
# ---------------------------------------------------------------------------------------


@forum.route("/course/<course_code>/forum")
@login_required
def ver_foro(course_code):
    """Página principal del foro de un curso."""
    # Verificar que el curso existe y tiene foro habilitado
    curso = database.session.execute(select(Curso).filter_by(codigo=course_code)).scalars().first()
    if not curso:
        abort(404)

    if not curso.foro_habilitado:
        flash("El foro no está habilitado para este curso.", "warning")
        return redirect(url_for("course.tomar_curso", course_code=course_code))

    # Verificar acceso del usuario al curso
    tiene_acceso, role = verificar_acceso_curso(course_code, current_user.usuario)
    if not tiene_acceso:
        abort(403)

    # Obtener mensajes principales (sin parent_id) paginados
    page = request.args.get("page", 1, type=int)
    mensajes = database.paginate(
        select(ForoMensaje).filter_by(curso_id=course_code, parent_id=None).order_by(ForoMensaje.fecha_creacion.desc()),
        page=page,
        per_page=10,
        error_out=False,
    )

    # Procesar contenido markdown para renderizado
    for mensaje in mensajes.items:
        mensaje.contenido_html = markdown_to_html(mensaje.contenido)

    puede_cerrar = puede_cerrar_mensajes(role, current_user.tipo)

    return render_template("forum/forum_list.html", curso=curso, mensajes=mensajes, role=role, puede_cerrar=puede_cerrar)


@forum.route("/course/<course_code>/forum/new", methods=["GET", "POST"])
@login_required
def nuevo_mensaje(course_code):
    """Crear un nuevo mensaje en el foro."""
    # Verificar curso y permisos
    curso = database.session.execute(select(Curso).filter_by(codigo=course_code)).scalars().first()
    if not curso or not curso.foro_habilitado:
        abort(404)

    tiene_acceso, role = verificar_acceso_curso(course_code, current_user.usuario)
    if not tiene_acceso:
        abort(403)

    # Verificar que el curso no esté finalizado
    if curso.estado == "finalizado":
        flash("No se pueden crear mensajes en cursos finalizados.", "error")
        return redirect(url_for(ROUTE_FORUM_VER_FORO, course_code=course_code))

    form = ForoMensajeForm()

    if form.validate_on_submit():
        # Crear nuevo mensaje en el foro
        mensaje = ForoMensaje(
            curso_id=course_code, usuario_id=current_user.usuario, contenido=form.contenido.data, estado="abierto"
        )

        database.session.add(mensaje)
        database.session.commit()

        flash("Mensaje creado exitosamente.", "success")
        return redirect(url_for(ROUTE_FORUM_VER_FORO, course_code=course_code))

    return render_template("forum/new_message.html", curso=curso, form=form)


@forum.route("/course/<course_code>/forum/message/<message_id>")
@login_required
def ver_mensaje(course_code, message_id):
    """Ver un mensaje específico con sus respuestas."""
    # Verificar curso y mensaje
    curso = database.session.execute(select(Curso).filter_by(codigo=course_code)).scalars().first()
    mensaje = database.session.execute(select(ForoMensaje).filter_by(id=message_id, curso_id=course_code)).scalars().first()

    if not curso or not mensaje or not curso.foro_habilitado:
        abort(404)

    tiene_acceso, role = verificar_acceso_curso(course_code, current_user.usuario)
    if not tiene_acceso:
        abort(403)

    # Obtener el mensaje raíz del hilo
    mensaje_raiz = mensaje.get_thread_root()

    # Obtener todas las respuestas del hilo ordenadas cronológicamente
    respuestas = (
        database.session.execute(
            select(ForoMensaje)
            .filter_by(curso_id=course_code, parent_id=mensaje_raiz.id)
            .order_by(ForoMensaje.fecha_creacion.asc())
        )
        .scalars()
        .all()
    )

    # Procesar contenido markdown para renderizado
    mensaje_raiz.contenido_html = markdown_to_html(mensaje_raiz.contenido)
    for respuesta in respuestas:
        respuesta.contenido_html = markdown_to_html(respuesta.contenido)

    puede_cerrar = puede_cerrar_mensajes(role, current_user.tipo)
    puede_responder = mensaje_raiz.can_reply()

    return render_template(
        "forum/message_thread.html",
        curso=curso,
        mensaje=mensaje_raiz,
        respuestas=respuestas,
        role=role,
        puede_cerrar=puede_cerrar,
        puede_responder=puede_responder,
    )


@forum.route("/course/<course_code>/forum/message/<message_id>/reply", methods=["GET", "POST"])
@login_required
def responder_mensaje(course_code, message_id):
    """Responder a un mensaje del foro."""
    # Verificar curso y mensaje
    curso = database.session.execute(select(Curso).filter_by(codigo=course_code)).scalars().first()
    mensaje = database.session.execute(select(ForoMensaje).filter_by(id=message_id, curso_id=course_code)).scalars().first()

    if not curso or not mensaje or not curso.foro_habilitado:
        abort(404)

    tiene_acceso, role = verificar_acceso_curso(course_code, current_user.usuario)
    if not tiene_acceso:
        abort(403)

    # Verificar que se puede responder
    if not mensaje.can_reply():
        flash("No se puede responder a este mensaje.", "error")
        return redirect(url_for("forum.ver_mensaje", course_code=course_code, message_id=message_id))

    form = ForoMensajeRespuestaForm()

    if form.validate_on_submit():
        # Obtener el mensaje raíz del hilo para mantener estructura
        mensaje_raiz = mensaje.get_thread_root()

        # Crear respuesta vinculada al mensaje raíz
        respuesta = ForoMensaje(
            curso_id=course_code,
            usuario_id=current_user.usuario,
            parent_id=mensaje_raiz.id,
            contenido=form.contenido.data,
            estado="abierto",
        )

        database.session.add(respuesta)
        database.session.commit()

        flash("Respuesta enviada exitosamente.", "success")
        return redirect(url_for("forum.ver_mensaje", course_code=course_code, message_id=mensaje_raiz.id))

    # Procesar contenido del mensaje original para display
    mensaje.contenido_html = markdown_to_html(mensaje.contenido)

    return render_template("forum/reply_message.html", curso=curso, mensaje=mensaje, form=form)


# ---------------------------------------------------------------------------------------
# Message management routes - Administrative actions for forum messages
# ---------------------------------------------------------------------------------------


@forum.route("/course/<course_code>/forum/message/<message_id>/close", methods=["POST"])
@login_required
def cerrar_mensaje(course_code, message_id):
    """Cerrar un mensaje/hilo del foro (solo instructores, moderadores y admins)."""
    # Verificar curso y mensaje
    curso = database.session.execute(select(Curso).filter_by(codigo=course_code)).scalars().first()
    mensaje = database.session.execute(select(ForoMensaje).filter_by(id=message_id, curso_id=course_code)).scalars().first()

    if not curso or not mensaje:
        abort(404)

    tiene_acceso, role = verificar_acceso_curso(course_code, current_user.usuario)
    if not tiene_acceso or not puede_cerrar_mensajes(role, current_user.tipo):
        abort(403)

    # Cerrar el mensaje (cambia estado para prevenir nuevas respuestas)
    mensaje.estado = "cerrado"
    database.session.commit()

    flash("Mensaje cerrado exitosamente.", "success")

    # Redireccionar según el tipo de solicitud (AJAX vs form)
    if request.headers.get("Content-Type") == "application/json":
        return jsonify({"status": "success", "message": "Mensaje cerrado exitosamente"})

    return redirect(url_for(ROUTE_FORUM_VER_FORO, course_code=course_code))


@forum.route("/course/<course_code>/forum/message/<message_id>/open", methods=["POST"])
@login_required
def abrir_mensaje(course_code, message_id):
    """Abrir un mensaje/hilo del foro (solo instructores, moderadores y admins)."""
    # Verificar curso y mensaje
    curso = database.session.execute(select(Curso).filter_by(codigo=course_code)).scalars().first()
    mensaje = database.session.execute(select(ForoMensaje).filter_by(id=message_id, curso_id=course_code)).scalars().first()

    if not curso or not mensaje:
        abort(404)

    tiene_acceso, role = verificar_acceso_curso(course_code, current_user.usuario)
    if not tiene_acceso or not puede_cerrar_mensajes(role, current_user.tipo):
        abort(403)

    # Verificar que el curso no esté finalizado
    if curso.estado == "finalizado":
        flash("No se pueden abrir mensajes en cursos finalizados.", "error")
        return redirect(url_for(ROUTE_FORUM_VER_FORO, course_code=course_code))

    # Abrir el mensaje (permite nuevas respuestas)
    mensaje.estado = "abierto"
    database.session.commit()

    flash("Mensaje abierto exitosamente.", "success")

    # Redireccionar según el tipo de solicitud (AJAX vs form)
    if request.headers.get("Content-Type") == "application/json":
        return jsonify({"status": "success", "message": "Mensaje abierto exitosamente"})

    return redirect(url_for(ROUTE_FORUM_VER_FORO, course_code=course_code))
