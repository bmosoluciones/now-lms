# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.

"""Public API for integration with external services."""

from __future__ import annotations

import functools
import hashlib
import json
from datetime import datetime

from flask import Blueprint, jsonify, request, url_for
from flask_mail import Message
from now_lms.auth import proteger_passwd, generate_confirmation_token
from now_lms.db import (
    ExternalApiKey,
    Curso,
    RemoteEnrollmentRequest,
    Usuario,
    EstudianteCurso,
    database,
    MailConfig,
    ContactMessage,
)
from now_lms.i18n import _
from now_lms.mail import send_mail
from now_lms.version import VERSION

public_api = Blueprint("public_api", __name__, url_prefix="/api/v1/public")


def check_rate_limit(key_record):
    """Simple basic rate limiting by API Key.
    Returns True if allowed, False if rate limit exceeded.

    Uses the application cache to store request counts.
    Default: 60 requests per minute per API Key.
    """
    from now_lms.cache import cache, cache_incr

    # Define limit: 60 requests per 60 seconds
    LIMIT = 60
    WINDOW = 60

    cache_key = f"rate_limit_{key_record.id}"
    current_count = cache.get(cache_key)

    if current_count is None:
        cache.set(cache_key, 1, timeout=WINDOW)
        return True

    if int(current_count) >= LIMIT:
        return False

    cache_incr(cache_key, timeout=WINDOW)
    return True


def require_api_key(f):
    """Decorator to require a valid API key."""

    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = None

        # Check Authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            api_key = auth_header.split(" ")[1]

        # Check X-API-Key header if not found
        if not api_key:
            api_key = request.headers.get("X-API-Key")

        if not api_key:
            return jsonify({"error": "unauthorized", "message": "API Key is missing."}), 401

        # Search for the API key hash in database
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        key_record = database.session.execute(
            database.select(ExternalApiKey).filter_by(key_hash=key_hash, active=True)
        ).scalar_one_or_none()

        if not key_record or key_record.revoked_at is not None:
            return jsonify({"error": "unauthorized", "message": "Invalid or revoked API Key."}), 401

        if not check_rate_limit(key_record):
            return jsonify({"error": "rate_limit_exceeded", "message": "Too many requests."}), 429

        # Update last used timestamp
        key_record.last_used_at = datetime.now()
        database.session.commit()

        # Add key_record to request context
        request.api_key_record = key_record

        return f(*args, **kwargs)

    return decorated_function


@public_api.route("/ping", methods=["GET"])
@require_api_key
def ping():
    """Health check / handshake endpoint."""
    return jsonify({"status": "ok", "service": "NOW LMS", "version": VERSION}), 200


@public_api.route("/courses/<course_code>", methods=["GET"])
@require_api_key
def get_course(course_code):
    """Consult public course information by code."""
    course = database.session.execute(database.select(Curso).filter_by(codigo=course_code)).scalar_one_or_none()

    if not course:
        return jsonify({"error": "course_not_found", "message": "Course code was not found."}), 404

    return (
        jsonify(
            {
                "code": course.codigo,
                "title": course.nombre,
                "description": course.descripcion_corta,
                "duration_hours": course.duracion,
                "course_type": "certification" if course.certificado else "course",
                "thumbnail_url": (
                    url_for("static", filename=f"uploads/images/{course.codigo}/portada.jpg", _external=True)
                    if course.portada
                    else None
                ),
                "is_active": course.estado == "open",
                "certificate_available": course.certificado,
                "recertification_required": course.recertification_required,
                "recertification_period_years": course.recertification_period_years,
                "resources": ["video", "quiz", "certificate"],
            }
        ),
        200,
    )


@public_api.route("/enrollments", methods=["POST"])
@require_api_key
def remote_enrollment():
    """Execute remote enrollment for a user."""
    data = request.get_json()

    if not data:
        return jsonify({"error": "invalid_payload", "message": "JSON payload is required."}), 400

    request_id = data.get("request_id")
    course_code = data.get("course_code")
    email = data.get("email")
    payment_confirmed = data.get("payment_confirmed", False)

    if not request_id or not course_code or not email:
        return jsonify({"error": "missing_fields", "message": "request_id, course_code and email are required."}), 400

    if payment_confirmed is not True:
        return jsonify({"error": "payment_not_confirmed", "message": "Payment must be confirmed to proceed."}), 400

    # Idempotency check
    existing_request = database.session.execute(
        database.select(RemoteEnrollmentRequest).filter_by(request_id=request_id)
    ).scalar_one_or_none()

    if existing_request:
        return (
            jsonify(
                {"status": "already_processed", "course_code": existing_request.course_code, "email": existing_request.email}
            ),
            200,
        )

    # Course existence check
    course = database.session.execute(database.select(Curso).filter_by(codigo=course_code)).scalar_one_or_none()

    if not course:
        return jsonify({"error": "course_not_found", "message": "Course code was not found."}), 404

    # User existence/creation
    user = database.session.execute(database.select(Usuario).filter_by(correo_electronico=email)).scalar_one_or_none()

    user_status = "existing_user"
    new_user = False

    if not user:
        new_user = True
        user_status = "pending_verification"
        # Create new user as pending verification
        import secrets
        import string

        temp_password = "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))

        user = Usuario(
            usuario=email,
            acceso=proteger_passwd(temp_password),
            nombre=email.split("@")[0],
            apellido="",
            correo_electronico=email,
            tipo="student",
            activo=False,
            correo_electronico_verificado=False,
            visible=True,
        )
        database.session.add(user)
        database.session.flush()

    # Enrollment check
    existing_enrollment = database.session.execute(
        database.select(EstudianteCurso).filter_by(usuario=user.usuario, curso=course_code)
    ).scalar_one_or_none()

    if existing_enrollment:
        return jsonify({"status": "already_enrolled", "course_code": course_code, "email": email}), 200

    # Create enrollment
    enrollment = EstudianteCurso(curso=course_code, usuario=user.usuario, vigente=True)
    database.session.add(enrollment)
    database.session.flush()

    # Log the request
    remote_request = RemoteEnrollmentRequest(
        request_id=request_id,
        course_code=course_code,
        email=email,
        payment_confirmed=payment_confirmed,
        status="processed",
        response_message="Enrollment successful",
        api_key_id=request.api_key_record.id,
        user_id=user.usuario,
        enrollment_id=enrollment.id,
        processed_at=datetime.now(),
        raw_payload_json=json.dumps(data),
    )
    database.session.add(remote_request)
    database.session.commit()

    # Send notification email
    # Determine if we should send synchronously (useful for tests)
    sync = data.get("_sync_email") == "1" or data.get("_sync_email") is True
    send_enrollment_email(user, course, new_user, sync=sync)

    message = "Existing user was enrolled successfully."
    if new_user:
        message = "User was created as pending verification and enrolled successfully."

    return (
        jsonify(
            {"status": "enrolled", "user_status": user_status, "course_code": course_code, "email": email, "message": message}
        ),
        201,
    )


def send_enrollment_email(user, course, is_new_user, sync=False):
    """Send notification email to student."""
    mail_config = database.session.execute(database.select(MailConfig)).scalar_one_or_none()
    if not mail_config or not mail_config.email_verificado:
        return

    subject = _("Has sido inscrito en {}").format(course.nombre)

    if is_new_user:
        token = generate_confirmation_token(user.correo_electronico)
        action_url = url_for("user.check_mail", token=token, _external=True)
        body_text = f"""
        {_("Hola,")}

        {_("Has sido inscrito en el curso: {}.").format(course.nombre)}

        {_("Como eres un usuario nuevo, por favor completa tu primer acceso y verifica tu cuenta haciendo clic en el siguiente enlace:")}
        {action_url}

        {_("En este enlace podrás definir tu contraseña y completar tu perfil.")}
        """
    else:
        action_url = url_for("home.pagina_de_inicio", _external=True)
        body_text = f"""
        {_("Hola,")}

        {_("Has sido inscrito en el curso: {}.").format(course.nombre)}

        {_("Puedes acceder al curso ingresando a la plataforma:")}
        {action_url}
        """

    if course.certificado:
        body_text += "\n\n" + _("Este curso cuenta con certificación al finalizar exitosamente.")

    msg = Message(
        subject=subject,
        recipients=[user.correo_electronico],
        sender=((mail_config.MAIL_DEFAULT_SENDER_NAME or "NOW LMS"), mail_config.MAIL_DEFAULT_SENDER),
        body=body_text,
    )

    try:
        send_mail(msg, background=not sync, no_config=True)
    except Exception:
        pass


@public_api.route("/contact-messages", methods=["GET"])
@require_api_key
def list_unread_contact_messages():
    """List unread contact messages (status is 'not_seen')."""
    messages = (
        database.session.execute(
            database.select(ContactMessage).filter(ContactMessage.status == "not_seen").order_by(ContactMessage.creado.desc())
        )
        .scalars()
        .all()
    )

    result = []
    for msg in messages:
        result.append(
            {
                "id": msg.id,
                "name": msg.name,
                "email": msg.email,
                "subject": msg.subject,
                "message": msg.message,
                "status": msg.status,
                "created_at": msg.timestamp.isoformat() if msg.timestamp else None,
            }
        )

    return jsonify(result), 200


@public_api.route("/contact-messages/<message_id>/read", methods=["POST"])
@require_api_key
def mark_contact_message_read(message_id):
    """Mark a contact message as read (status 'seen')."""
    msg = database.session.get(ContactMessage, message_id)

    if not msg:
        return jsonify({"error": "message_not_found", "message": "Contact message ID was not found."}), 404

    if msg.status == "not_seen":
        msg.status = "seen"
        database.session.commit()

    return (
        jsonify(
            {
                "status": "success",
                "message_id": msg.id,
                "new_status": msg.status,
                "message": "Message marked as read successfully.",
            }
        ),
        200,
    )
