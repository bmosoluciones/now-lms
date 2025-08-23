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

Gestión del sistema de mensajería.
"""

# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------
from datetime import datetime

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------
from flask import Blueprint, abort, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms.auth import perfil_requerido
from now_lms.config import DIRECTORIO_PLANTILLAS
from now_lms.db import Curso, DocenteCurso, EstudianteCurso, Message, MessageThread, ModeradorCurso, database, select
from now_lms.forms import MessageReplyForm, MessageReportForm, MessageThreadForm

# ---------------------------------------------------------------------------------------
# Interfaz de mensajes
# ---------------------------------------------------------------------------------------

# Route constants
ROUTE_MSG_VIEW_THREAD = "msg.view_thread"

# Template constants
TEMPLATE_STANDALONE_REPORT = "learning/mensajes/standalone_report.html"

msg = Blueprint("msg", __name__, template_folder=DIRECTORIO_PLANTILLAS)


def check_course_access(course_code, user):
    """Check if user has access to course messaging."""
    if user.tipo == "admin":
        return True

    if user.tipo == "student":
        return (
            database.session.execute(select(EstudianteCurso).filter_by(curso=course_code, usuario=user.usuario, vigente=True))
            .scalars()
            .first()
            is not None
        )

    if user.tipo == "instructor":
        return (
            database.session.execute(select(DocenteCurso).filter_by(curso=course_code, usuario=user.usuario, vigente=True))
            .scalars()
            .first()
            is not None
        )

    if user.tipo == "moderator":
        return (
            database.session.execute(select(ModeradorCurso).filter_by(curso=course_code, usuario=user.usuario, vigente=True))
            .scalars()
            .first()
            is not None
        )

    return False


def check_thread_access(thread, user):
    """Check if user can access a specific thread."""
    if user.tipo == "admin":
        return True

    # Student can only access their own threads
    if user.tipo == "student":
        return thread.student_id == user.usuario

    # Instructors and moderators can access threads in their courses
    if user.tipo in ["instructor", "moderator"]:
        return check_course_access(thread.course_id, user)

    return False


@msg.route("/course/<course_code>/messages")
@login_required
def course_messages(course_code):
    """List all message threads for a specific course."""
    if not check_course_access(course_code, current_user):
        return abort(403)

    # Get course info
    course = database.session.execute(select(Curso).filter_by(codigo=course_code)).scalars().first()
    if not course:
        return abort(404)

    # Build query based on user role
    if current_user.tipo == "student":
        # Students only see their own threads
        threads = (
            database.session.execute(
                select(MessageThread)
                .filter_by(course_id=course_code, student_id=current_user.usuario)
                .order_by(MessageThread.timestamp.desc())
            )
            .scalars()
            .all()
        )
    else:
        # Instructors, moderators, and admins see all threads in the course
        threads = (
            database.session.execute(
                select(MessageThread).filter_by(course_id=course_code).order_by(MessageThread.timestamp.desc())
            )
            .scalars()
            .all()
        )

    return render_template("learning/mensajes/course_messages.html", course=course, threads=threads)


@msg.route("/user/messages")
@login_required
def user_messages():
    """List all message threads for the current user across all courses."""
    if current_user.tipo == "student":
        # Students see their own threads
        threads = (
            database.session.execute(
                select(MessageThread).filter_by(student_id=current_user.usuario).order_by(MessageThread.timestamp.desc())
            )
            .scalars()
            .all()
        )
    else:
        # Instructors and moderators see threads from their courses
        if current_user.tipo == "instructor":
            course_codes = [
                dc.curso
                for dc in database.session.execute(select(DocenteCurso).filter_by(usuario=current_user.usuario, vigente=True))
                .scalars()
                .all()
            ]
        elif current_user.tipo == "moderator":
            course_codes = [
                mc.curso
                for mc in database.session.execute(
                    select(ModeradorCurso).filter_by(usuario=current_user.usuario, vigente=True)
                )
                .scalars()
                .all()
            ]
        else:  # admin
            course_codes = [c.codigo for c in database.session.execute(select(Curso)).scalars().all()]

        threads = (
            database.session.execute(
                select(MessageThread)
                .filter(MessageThread.course_id.in_(course_codes))
                .order_by(MessageThread.timestamp.desc())
            )
            .scalars()
            .all()
        )

    return render_template("learning/mensajes/user_messages.html", threads=threads)


@msg.route("/course/<course_code>/messages/new", methods=["GET", "POST"])
@login_required
@perfil_requerido("student")
def new_thread(course_code):
    """Create a new message thread."""
    if not check_course_access(course_code, current_user):
        return abort(403)

    # Only students can create threads
    if current_user.tipo != "student":
        return abort(403)

    course = database.session.execute(select(Curso).filter_by(codigo=course_code)).scalars().first()
    if not course:
        return abort(404)

    form = MessageThreadForm()
    form.course_id.data = course_code

    if form.validate_on_submit():
        # Create new thread
        thread = MessageThread()
        thread.course_id = course_code
        thread.student_id = current_user.usuario
        thread.status = "open"

        database.session.add(thread)
        database.session.flush()  # Get the ID

        # Create first message
        message = Message()
        message.thread_id = thread.id
        message.sender_id = current_user.usuario
        message.content = f"**{form.subject.data}**\n\n{form.content.data}"

        database.session.add(message)
        database.session.commit()

        flash("Mensaje enviado correctamente.", "success")
        return redirect(url_for(ROUTE_MSG_VIEW_THREAD, thread_id=thread.id))

    return render_template("learning/mensajes/new_thread.html", form=form, course=course)


@msg.route("/thread/<thread_id>")
@login_required
def view_thread(thread_id):
    """View a message thread and its messages."""
    thread = database.session.execute(select(MessageThread).filter_by(id=thread_id)).scalars().first()
    if not thread:
        return abort(404)

    if not check_thread_access(thread, current_user):
        return abort(403)

    # Get all messages in the thread
    messages = (
        database.session.execute(select(Message).filter_by(thread_id=thread_id).order_by(Message.timestamp.asc()))
        .scalars()
        .all()
    )

    # Mark messages as read for non-students
    if current_user.tipo != "student":
        for message in messages:
            if not message.read_at and message.sender_id != current_user.usuario:
                message.read_at = datetime.now()
        database.session.commit()

    # Create reply form
    reply_form = MessageReplyForm()
    reply_form.thread_id.data = thread_id

    # Create report form
    report_form = MessageReportForm()
    report_form.thread_id.data = thread_id

    return render_template(
        "learning/mensajes/view_thread.html",
        thread=thread,
        messages=messages,
        reply_form=reply_form,
        report_form=report_form,
    )


@msg.route("/thread/<thread_id>/reply", methods=["POST"])
@login_required
def reply_to_thread(thread_id):
    """Reply to a message thread."""
    thread = database.session.execute(select(MessageThread).filter_by(id=thread_id)).scalars().first()
    if not thread:
        return abort(404)

    if not check_thread_access(thread, current_user):
        return abort(403)

    # Check if thread is closed
    if thread.status == "closed":
        flash("No se puede responder a un hilo cerrado.", "error")
        return redirect(url_for(ROUTE_MSG_VIEW_THREAD, thread_id=thread_id))

    form = MessageReplyForm()

    if form.validate_on_submit():
        # Create reply message
        message = Message()
        message.thread_id = thread_id
        message.sender_id = current_user.usuario
        message.content = form.content.data

        database.session.add(message)
        database.session.commit()

        flash("Respuesta enviada correctamente.", "success")

    return redirect(url_for(ROUTE_MSG_VIEW_THREAD, thread_id=thread_id))


@msg.route("/thread/<thread_id>/status/<new_status>")
@login_required
def change_thread_status(thread_id, new_status):
    """Change thread status."""
    thread = database.session.execute(select(MessageThread).filter_by(id=thread_id)).scalars().first()
    if not thread:
        return abort(404)

    if not check_thread_access(thread, current_user):
        return abort(403)

    # Check permissions for status changes
    if new_status == "fixed" and current_user.tipo != "student":
        return abort(403)

    if new_status == "closed" and current_user.tipo not in ["instructor", "moderator", "admin"]:
        return abort(403)

    # Validate status transitions
    valid_transitions = {"open": ["fixed", "closed"], "fixed": ["closed"], "closed": []}

    if new_status not in valid_transitions.get(thread.status, []):
        flash("Transición de estado no válida.", "error")
        return redirect(url_for(ROUTE_MSG_VIEW_THREAD, thread_id=thread_id))

    thread.status = new_status
    if new_status == "closed":
        thread.closed_at = datetime.now()

    database.session.commit()

    flash(f"Estado del hilo cambiado a {new_status}.", "success")
    return redirect(url_for(ROUTE_MSG_VIEW_THREAD, thread_id=thread_id))


@msg.route("/message/<message_id>/report", methods=["POST"])
@login_required
def report_message(message_id):
    """Report a message."""
    message = database.session.execute(select(Message).filter_by(id=message_id)).scalars().first()
    if not message:
        return abort(404)

    thread = database.session.execute(select(MessageThread).filter_by(id=message.thread_id)).scalars().first()

    # For reporting, students should be able to report messages in any thread
    # within courses they have access to, not just their own threads
    if current_user.tipo == "student":
        if not check_course_access(thread.course_id, current_user):
            return abort(403)
    else:
        # For non-students, use the standard thread access check
        if not check_thread_access(thread, current_user):
            return abort(403)

    form = MessageReportForm()

    if form.validate_on_submit():
        message.is_reported = True
        message.reported_reason = form.reason.data

        database.session.commit()

        flash("Mensaje reportado correctamente.", "success")

    return redirect(url_for(ROUTE_MSG_VIEW_THREAD, thread_id=message.thread_id))


@msg.route("/admin/flagged-messages")
@login_required
@perfil_requerido("admin")
def admin_flagged_messages():
    """Admin view for flagged messages."""
    # Get all reported messages
    flagged_messages = (
        database.session.execute(select(Message).filter_by(is_reported=True).order_by(Message.timestamp.desc()))
        .scalars()
        .all()
    )

    return render_template("admin/flagged_messages.html", flagged_messages=flagged_messages)


@msg.route("/admin/resolve-report/<message_id>", methods=["POST"])
@login_required
@perfil_requerido("admin")
def resolve_report(message_id):
    """Mark a reported message as resolved."""
    from flask import jsonify

    message = database.session.execute(select(Message).filter_by(id=message_id)).scalars().first()
    if not message:
        return jsonify({"success": False, "message": "Mensaje no encontrado"})

    message.is_reported = False
    message.reported_reason = None
    database.session.commit()

    return jsonify({"success": True, "message": "Reporte resuelto"})


@msg.route("/message/report/", methods=["GET", "POST"])
@login_required
def standalone_report_message():
    """Standalone page for reporting messages."""
    from flask import request

    # Get messages accessible to the current user
    accessible_messages = []

    if current_user.tipo == "student":
        # Students can see messages in threads from courses they're enrolled in
        student_courses = (
            database.session.execute(select(EstudianteCurso).filter_by(usuario=current_user.usuario, vigente=True))
            .scalars()
            .all()
        )
        course_codes = [sc.curso for sc in student_courses]

        if course_codes:
            threads = (
                database.session.execute(select(MessageThread).filter(MessageThread.course_id.in_(course_codes)))
                .scalars()
                .all()
            )

            for thread in threads:
                messages = database.session.execute(select(Message).filter_by(thread_id=thread.id)).scalars().all()
                for message in messages:
                    accessible_messages.append(
                        {
                            "id": message.id,
                            "content": message.content[:100] + "..." if len(message.content) > 100 else message.content,
                            "sender": f"{message.sender.nombre} {message.sender.apellido}",
                            "thread_title": f"Curso: {thread.course.nombre}",
                            "timestamp": message.timestamp.strftime("%d/%m/%Y %H:%M"),
                        }
                    )
    else:
        # For instructors, moderators, and admins
        if current_user.tipo == "instructor":
            course_codes = [
                dc.curso
                for dc in database.session.execute(select(DocenteCurso).filter_by(usuario=current_user.usuario, vigente=True))
                .scalars()
                .all()
            ]
        elif current_user.tipo == "moderator":
            course_codes = [
                mc.curso
                for mc in database.session.execute(
                    select(ModeradorCurso).filter_by(usuario=current_user.usuario, vigente=True)
                )
                .scalars()
                .all()
            ]
        else:  # admin
            course_codes = [c.codigo for c in database.session.execute(select(Curso)).scalars().all()]

        if course_codes:
            threads = (
                database.session.execute(select(MessageThread).filter(MessageThread.course_id.in_(course_codes)))
                .scalars()
                .all()
            )

            for thread in threads:
                messages = database.session.execute(select(Message).filter_by(thread_id=thread.id)).scalars().all()
                for message in messages:
                    accessible_messages.append(
                        {
                            "id": message.id,
                            "content": message.content[:100] + "..." if len(message.content) > 100 else message.content,
                            "sender": f"{message.sender.nombre} {message.sender.apellido}",
                            "thread_title": f"Curso: {thread.course.nombre}",
                            "timestamp": message.timestamp.strftime("%d/%m/%Y %H:%M"),
                        }
                    )

    if request.method == "POST":
        message_id = request.form.get("message_id")
        reason = request.form.get("reason")

        if not message_id or not reason:
            flash("Debe seleccionar un mensaje y proporcionar un motivo.", "error")
            return render_template(TEMPLATE_STANDALONE_REPORT, messages=accessible_messages)

        # Find the message
        message = database.session.execute(select(Message).filter_by(id=message_id)).scalars().first()
        if not message:
            flash("Mensaje no encontrado.", "error")
            return render_template(TEMPLATE_STANDALONE_REPORT, messages=accessible_messages)

        # Verify user has access to this message
        thread = database.session.execute(select(MessageThread).filter_by(id=message.thread_id)).scalars().first()

        # Check access permissions
        if current_user.tipo == "student":
            if not check_course_access(thread.course_id, current_user):
                return abort(403)
        else:
            if not check_thread_access(thread, current_user):
                return abort(403)

        # Report the message
        message.is_reported = True
        message.reported_reason = reason
        database.session.commit()

        flash("Mensaje reportado correctamente. El administrador será notificado.", "success")
        return redirect(url_for("home.panel"))

    return render_template(TEMPLATE_STANDALONE_REPORT, messages=accessible_messages)
