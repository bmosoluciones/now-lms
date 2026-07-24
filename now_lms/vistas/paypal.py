# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.

"""PayPal Payments."""

from __future__ import annotations

# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------
import logging
from typing import Any, cast

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------
import requests
from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, url_for
from flask import Response as FlaskResponse
from flask_login import current_user, login_required
from sqlalchemy.exc import OperationalError
from werkzeug.wrappers import Response

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms.auth import perfil_requerido
from now_lms.cache import cache
from now_lms.config import DIRECTORIO_PLANTILLAS
from now_lms.db import Configuracion, Curso, Pago, PaypalConfig, database
from now_lms.i18n import _

# Constants for PayPal API URLs
PAYPAL_SANDBOX_API_URL = "https://api.sandbox.paypal.com"
PAYPAL_PRODUCTION_API_URL = "https://api.paypal.com"
HOME_PAGE_ROUTE = "home.pagina_de_inicio"
PAYPAL_NOT_CONFIGURED_MESSAGE = "PayPal not configured"
CONTENT_TYPE_JSON = "application/json"

paypal = Blueprint("paypal", __name__, template_folder=DIRECTORIO_PLANTILLAS, url_prefix="/paypal_checkout")


@cache.cached(timeout=50)
def check_paypal_enabled() -> bool:
    """Check if PayPal payments are enabled."""
    with current_app.app_context():
        try:
            row = database.session.execute(database.select(PaypalConfig)).first()
            if row is None:
                return False
            q = row[0]
            enabled = q.enable
            return enabled
        except OperationalError:
            return False


@cache.cached(timeout=50)
def get_site_currency() -> str:
    """Get the site's default currency from configuration."""
    with current_app.app_context():
        try:
            row = database.session.execute(database.select(Configuracion)).first()
            if row is None:
                return "USD"
            config = row[0]
            return config.moneda or "USD"  # Default to USD if not configured
        except OperationalError:
            return "USD"


def validate_paypal_configuration(client_id: str, client_secret: str, sandbox: bool = False) -> dict[str, object]:
    """Validate PayPal configuration by attempting to get an access token."""
    try:
        # Get access token from PayPal
        base_url = PAYPAL_SANDBOX_API_URL if sandbox else PAYPAL_PRODUCTION_API_URL
        token_url = f"{base_url}/v1/oauth2/token"

        headers = {
            "Accept": CONTENT_TYPE_JSON,
            "Accept-Language": "en_US",
        }

        data = "grant_type=client_credentials"

        response = requests.post(token_url, headers=headers, data=data, auth=(client_id, client_secret), timeout=20)

        if response.status_code == 200:
            return {"valid": True, "message": "Configuración de PayPal válida"}
        return {"valid": False, "message": f"Error de configuración de PayPal: {response.text}"}

    except Exception as e:
        return {"valid": False, "message": f"Error al validar configuración: {str(e)}"}


def _paypal_credentials(config_data, descifrar_secreto) -> tuple[str, str] | None:
    """Select and decrypt credentials for the configured PayPal environment."""
    sandbox = config_data.sandbox
    client_id = config_data.paypal_sandbox if sandbox else config_data.paypal_id
    encrypted_secret = config_data.paypal_sandbox_secret if sandbox else config_data.paypal_secret
    environment = "sandbox" if sandbox else "production"
    if not client_id:
        logging.error(f"PayPal client ID not configured for {environment} mode")
        return None
    if not encrypted_secret:
        logging.error(f"PayPal client secret not configured for {environment} mode")
        return None
    try:
        client_secret = descifrar_secreto(encrypted_secret)
    except Exception:
        logging.exception("Failed to decrypt PayPal client secret")
        return None
    if not client_secret:
        logging.error("PayPal client secret decryption returned no value")
        return None
    return client_id, client_secret


def _request_paypal_access_token(config_data, credentials: tuple[str, str]) -> str | None:
    """Request an OAuth token from PayPal."""
    client_id, client_secret = credentials
    base_url = PAYPAL_SANDBOX_API_URL if config_data.sandbox else PAYPAL_PRODUCTION_API_URL
    response = requests.post(
        f"{base_url}/v1/oauth2/token",
        headers={"Accept": CONTENT_TYPE_JSON, "Accept-Language": "en_US"},
        data="grant_type=client_credentials",
        auth=(client_id, client_secret),
        timeout=20,
    )
    if response.status_code != 200:
        logging.error(f"Failed to get PayPal access token: HTTP {response.status_code} - {response.text}")
        return None
    access_token = response.json().get("access_token")
    if not access_token:
        logging.error("PayPal access token missing in response")
        return None
    logging.info(f"Successfully obtained PayPal access token ({'sandbox' if config_data.sandbox else 'production'})")
    return access_token


def get_paypal_access_token() -> str | None:
    """Get PayPal access token for API calls."""
    try:
        from now_lms.auth import descifrar_secreto

        paypal_config = database.session.execute(database.select(PaypalConfig)).first()
        if not paypal_config:
            logging.error("PayPal configuration not found in database")
            return None

        config_data = paypal_config[0]
        credentials = _paypal_credentials(config_data, descifrar_secreto)
        return _request_paypal_access_token(config_data, credentials) if credentials else None

    except Exception:
        logging.exception("Exception while getting PayPal access token")
        return None


def verify_paypal_payment(order_id: str, access_token: str) -> dict[str, object]:
    """Verify a PayPal payment by order ID."""
    try:
        row = database.session.execute(database.select(PaypalConfig)).first()
        if row is None:
            return {"status": "error", "message": PAYPAL_NOT_CONFIGURED_MESSAGE}
        paypal_config = row[0]
        base_url = PAYPAL_SANDBOX_API_URL if paypal_config.sandbox else PAYPAL_PRODUCTION_API_URL
        order_url = f"{base_url}/v2/checkout/orders/{order_id}"

        headers = {
            "Content-Type": CONTENT_TYPE_JSON,
            "Authorization": f"Bearer {access_token}",
        }

        response = requests.get(order_url, headers=headers, timeout=20)

        if response.status_code == 200:
            order_data = response.json()
            return {
                "verified": True,
                "status": order_data.get("status"),
                "amount": order_data.get("purchase_units", [{}])[0].get("amount", {}).get("value"),
                "currency": order_data.get("purchase_units", [{}])[0].get("amount", {}).get("currency_code"),
                "payer_id": order_data.get("payer", {}).get("payer_id"),
                "order_data": order_data,
            }
        logging.error(f"PayPal order verification failed: {response.text}")
        return {"verified": False, "error": "Payment verification failed"}

    except Exception as e:
        logging.exception("PayPal payment verification error")
        return {"verified": False, "error": str(e)}


def _validate_payment_confirmation() -> tuple[dict[str, object] | None, tuple[FlaskResponse, int] | None]:
    """Validate request data and PayPal response before changing local state."""
    data = request.get_json()
    if not data:
        logging.warning(f"Payment confirmation attempt without data from user {current_user.usuario}")
        return None, (jsonify({"success": False, "error": "No payment data received"}), 400)

    fields = {
        "orderID": data.get("orderID"),
        "payerID": data.get("payerID"),
        "courseCode": data.get("courseCode"),
        "amount": data.get("amount"),
        "itemType": data.get("itemType", "course"),
    }
    logging.info(
        f"Payment confirmation attempt for user {current_user.usuario}, "
        f"type {fields['itemType']}, code {fields['courseCode']}, order {fields['orderID']}"
    )
    missing_fields = [name for name, value in fields.items() if not value]
    if missing_fields:
        logging.warning(f"Payment confirmation missing fields {missing_fields} for user {current_user.usuario}")
        return None, (jsonify({"success": False, "error": f"Missing required payment data: {', '.join(missing_fields)}"}), 400)

    try:
        if float(fields["amount"]) <= 0:
            raise ValueError("Amount must be positive")
    except (ValueError, TypeError) as exc:
        logging.warning(f"Invalid payment amount {fields['amount']} for user {current_user.usuario}: {exc}")
        return None, (jsonify({"success": False, "error": "Invalid payment amount"}), 400)

    access_token = get_paypal_access_token()
    if not access_token:
        logging.error(f"Failed to get PayPal access token for user {current_user.usuario}")
        return None, (jsonify({"success": False, "error": "PayPal configuration error - please contact support"}), 500)
    verification = verify_paypal_payment(fields["orderID"], access_token)
    if not verification["verified"]:
        error_msg = verification.get("error", "Payment verification failed")
        logging.error(f"PayPal payment verification failed for order {fields['orderID']}: {error_msg}")
        return None, (jsonify({"success": False, "error": f"Payment verification failed: {error_msg}"}), 400)
    if verification.get("status") != "COMPLETED":
        return None, (jsonify({"success": False, "error": "Payment is not completed"}), 400)

    from now_lms.db import Programa

    if fields["itemType"] == "program":
        programa = database.session.execute(database.select(Programa).filter_by(codigo=fields["courseCode"])).scalars().first()
        if not programa:
            return None, (jsonify({"success": False, "error": "Program not found"}), 404)
        pending_payment = (
            database.session.execute(
                database.select(Pago).filter_by(usuario=current_user.usuario, programa=programa.id, estado="pending")
            )
            .scalars()
            .first()
        )
        expected_amount = float(pending_payment.monto if pending_payment else programa.precio)
    else:
        course = database.session.execute(database.select(Curso).filter_by(codigo=fields["courseCode"])).scalars().first()
        if not course:
            return None, (jsonify({"success": False, "error": "Course not found"}), 404)
        pending_payment = (
            database.session.execute(
                database.select(Pago).filter_by(usuario=current_user.usuario, curso=fields["courseCode"], estado="pending")
            )
            .scalars()
            .first()
        )
        expected_amount = float(pending_payment.monto if pending_payment else course.precio)

    try:
        verified_amount = float(str(verification.get("amount")))
    except (ValueError, TypeError):
        verified_amount = 0.0
    if abs(verified_amount - expected_amount) > 0.01:
        return None, (
            jsonify(
                {
                    "success": False,
                    "error": f"Payment amount mismatch: expected {expected_amount}, received {verified_amount}",
                }
            ),
            400,
        )

    verified_currency = verification.get("currency")
    expected_currency = get_site_currency()
    if verified_currency != expected_currency:
        return None, (
            jsonify(
                {
                    "success": False,
                    "error": f"Payment currency mismatch: expected {expected_currency}, received {verified_currency}",
                }
            ),
            400,
        )
    return {
        "order_id": fields["orderID"],
        "course_code": fields["courseCode"],
        "item_type": fields["itemType"],
        "pending_payment": pending_payment,
        "verified_amount": verified_amount,
        "verified_currency": verified_currency,
    }, None


def _payment_record(payment_data: dict[str, object]) -> tuple[Any, tuple[FlaskResponse, int] | None]:
    """Find or create the local payment record for a verified order."""
    order_id = payment_data["order_id"]
    course_code = payment_data["course_code"]
    item_type = payment_data.get("item_type", "course")

    from now_lms.db import Programa

    if item_type == "program":
        programa = database.session.execute(database.select(Programa).filter_by(codigo=course_code)).scalars().first()
        if not programa:
            return None, (jsonify({"success": False, "error": "Program not found"}), 404)
        existing_payment = (
            database.session.execute(database.select(Pago).filter_by(referencia=order_id, programa=programa.id))
            .scalars()
            .first()
        )
        if existing_payment and existing_payment.estado == "completed":
            logging.info(f"Payment {order_id} already completed for user {current_user.usuario}")
            return existing_payment, (
                jsonify(
                    {
                        "success": True,
                        "message": "Pago ya procesado anteriormente",
                        "redirect_url": url_for("program.tomar_programa", codigo=course_code),
                    }
                ),
                200,
            )

        pago = existing_payment or payment_data["pending_payment"] or Pago()
        if not existing_payment and not payment_data["pending_payment"]:
            pago.usuario = current_user.usuario
            pago.programa = programa.id
            pago.curso = None
            pago.nombre = current_user.nombre
            pago.apellido = current_user.apellido
            pago.correo_electronico = current_user.correo_electronico
        pago.referencia = order_id
        pago.monto = payment_data["verified_amount"]
        pago.moneda = payment_data["verified_currency"]
        pago.metodo = "paypal"
        pago.estado = "completed"
        return pago, None
    else:
        existing_payment = (
            database.session.execute(database.select(Pago).filter_by(referencia=order_id, curso=course_code)).scalars().first()
        )
        if existing_payment and existing_payment.estado == "completed":
            logging.info(f"Payment {order_id} already completed for user {current_user.usuario}")
            return existing_payment, (
                jsonify(
                    {
                        "success": True,
                        "message": "Pago ya procesado anteriormente",
                        "redirect_url": url_for("course.tomar_curso", course_code=course_code),
                    }
                ),
                200,
            )

        pago = existing_payment or payment_data["pending_payment"] or Pago()
        if not existing_payment and not payment_data["pending_payment"]:
            pago.usuario = current_user.usuario
            pago.curso = course_code
            pago.nombre = current_user.nombre
            pago.apellido = current_user.apellido
            pago.correo_electronico = current_user.correo_electronico
        pago.referencia = order_id
        pago.monto = payment_data["verified_amount"]
        pago.moneda = payment_data["verified_currency"]
        pago.metodo = "paypal"
        pago.estado = "completed"
        return pago, None


def _save_payment_enrollment(pago: Any, course_code: str) -> None:
    """Persist payment and activate the student's course enrollment or program enrollment."""
    from now_lms.db import EstudianteCurso, ProgramaEstudiante, Programa
    from now_lms.vistas.programs import inscribir_usuario_en_cursos_de_programa

    if pago not in database.session:
        database.session.add(pago)
    database.session.flush()

    if pago.programa:
        # It's a program payment!
        enrollment = (
            database.session.execute(
                database.select(ProgramaEstudiante).filter_by(usuario=pago.usuario, programa=pago.programa)
            )
            .scalars()
            .first()
        )
        if not enrollment:
            database.session.add(ProgramaEstudiante(usuario=pago.usuario, programa=pago.programa))

        # Automatically enroll the user in all courses of this program!
        programa = database.session.execute(database.select(Programa).filter_by(id=pago.programa)).scalars().first()
        if programa:
            inscribir_usuario_en_cursos_de_programa(pago.usuario, programa)
    else:
        enrollment = (
            database.session.execute(database.select(EstudianteCurso).filter_by(usuario=pago.usuario, curso=course_code))
            .scalars()
            .first()
        )
        if enrollment:
            enrollment.vigente = True
            enrollment.pago = pago.id
        else:
            database.session.add(EstudianteCurso(curso=pago.curso, usuario=pago.usuario, vigente=True, pago=pago.id))
    database.session.commit()


def _update_coupon_usage(pago: Any, course_code: str, order_id: str) -> None:
    """Increment coupon usage after a successful payment."""
    if not pago.descripcion or "Cupón aplicado:" not in pago.descripcion:
        return
    try:
        from now_lms.db import Coupon

        coupon_code = pago.descripcion.split("Cupón aplicado: ")[1].split(" ")[0]
        coupon = (
            database.session.execute(
                database.select(Coupon).filter_by(course_id=course_code, code=coupon_code).with_for_update()
            )
            .scalars()
            .first()
        )
        if coupon:
            coupon.current_uses += 1
            database.session.commit()
            logging.info(f"Updated coupon {coupon_code} usage count to {coupon.current_uses}")
    except Exception as exc:
        logging.warning(f"Failed to update coupon usage for payment {order_id}: {exc}")


def enviar_recibo_pago(pago: Pago) -> None:
    """Envía un recibo de pago por correo electrónico en HTML si el correo está configurado."""
    from now_lms.mail import send_mail, _config
    from flask_mail import Message
    from flask import render_template
    from now_lms.db import Curso, Programa

    recipient = pago.correo_electronico
    if not recipient:
        logging.warning(
            "Payment %s has no email address; receipt not sent.",
            pago.referencia or pago.id,
        )
        return

    try:
        mail_config = _config()
        if not mail_config.mail_configured:
            logging.info("Email is not configured. Receipt will not be sent by email.")
            return

        curso = None
        programa = None
        subject_name = ""

        if pago.programa:
            programa = database.session.execute(database.select(Programa).filter_by(id=pago.programa)).scalars().first()
            subject_name = programa.nombre if programa else pago.programa
        else:
            curso = database.session.execute(database.select(Curso).filter_by(codigo=pago.curso)).scalars().first()
            subject_name = curso.nombre if curso else pago.curso

        html_body = render_template("payments/receipt_email.html", pago=pago, curso=curso, programa=programa)

        msg = Message(
            subject=_("Recibo de Pago - %(curso_nombre)s") % {"curso_nombre": subject_name},
            recipients=[recipient],
            sender=((mail_config.MAIL_DEFAULT_SENDER_NAME or "NOW LMS"), mail_config.MAIL_DEFAULT_SENDER),
        )
        msg.html = html_body

        send_mail(
            msg, background=True, _log=f"Recibo de pago {pago.referencia} enviado por correo electrónico a {msg.recipients}."
        )
    except Exception:
        logging.exception(
            "Failed to send receipt for payment %s",
            pago.referencia or pago.id,
        )


def _process_confirmed_payment(payment_data: dict[str, object]) -> tuple[FlaskResponse, int]:
    """Complete the local payment and enrollment transaction."""
    order_id = cast(str, payment_data["order_id"])
    course_code = cast(str, payment_data["course_code"])
    pago, already_processed = _payment_record(payment_data)
    if already_processed:
        return already_processed
    try:
        _save_payment_enrollment(pago, course_code)
    except OperationalError:
        database.session.rollback()
        logging.exception("Database error during enrollment")
        return jsonify({"success": False, "error": "Error en la base de datos. Por favor contacte soporte."}), 500

    _update_coupon_usage(pago, course_code, order_id)

    if pago.programa:
        logging.info(f"Payment {order_id} successfully processed for user {current_user.usuario}, program {course_code}")
        redirect_url = url_for("program.tomar_programa", codigo=course_code)
    else:
        from now_lms.vistas.courses import _crear_indice_avance_curso

        _crear_indice_avance_curso(course_code)
        logging.info(f"Payment {order_id} successfully processed for user {current_user.usuario}, course {course_code}")
        redirect_url = url_for("course.tomar_curso", course_code=course_code)

    # Enviar recibo de pago
    enviar_recibo_pago(pago)

    return (
        jsonify(
            {
                "success": True,
                "message": "Pago completado exitosamente",
                "redirect_url": redirect_url,
            }
        ),
        200,
    )


@paypal.route("/confirm_payment", methods=["POST"])
@login_required
@perfil_requerido("student")
def confirm_payment() -> tuple[FlaskResponse, int]:
    """Confirm PayPal payment after successful client-side processing."""
    try:
        payment_data, error_response = _validate_payment_confirmation()
        if error_response:
            return error_response
        if payment_data is None:
            logging.error("Payment validation returned no data without an error response")
            return jsonify({"success": False, "error": "Invalid payment data"}), 400
        return _process_confirmed_payment(payment_data)
    except Exception:
        logging.exception("Unexpected error in payment confirmation")
        return jsonify({"success": False, "error": "Error interno del servidor. Por favor contacte soporte."}), 500


@paypal.route("/resume_payment/<payment_id>", methods=["GET"])
@login_required
@perfil_requerido("student")
def resume_payment(payment_id: str) -> Response:
    """Resume an existing pending payment."""
    try:
        # Find the pending payment
        pago = (
            database.session.execute(
                database.select(Pago).filter_by(id=payment_id, usuario=current_user.usuario, estado="pending")
            )
            .scalars()
            .first()
        )

        if not pago:
            flash(_("Pago no encontrado o ya procesado."), "error")
            return redirect(url_for(HOME_PAGE_ROUTE))

        if pago.programa:
            from now_lms.db import Programa

            programa = database.session.execute(database.select(Programa).filter_by(id=pago.programa)).scalars().first()
            if programa:
                return redirect(url_for("program.program_payment", codigo=programa.codigo, payment_id=pago.id))

        # Redirect to the payment page for this course
        return redirect(url_for("paypal.payment_page", course_code=pago.curso))

    except Exception:
        logging.exception("Error resuming payment")
        flash(_("Error al reanudar el pago."), "error")
        return redirect(url_for(HOME_PAGE_ROUTE))


@paypal.route("/payment/<course_code>", methods=["GET"])
@login_required
@perfil_requerido("student")
def payment_page(course_code: str) -> str | Response | tuple[FlaskResponse, int]:
    """Display PayPal payment page for a course."""
    payment_id = request.args.get("payment_id")
    pago = None
    if payment_id:
        pago = (
            database.session.execute(
                database.select(Pago).filter_by(id=payment_id, usuario=current_user.usuario, curso=course_code)
            )
            .scalars()
            .first()
        )

    curso = database.session.execute(database.select(Curso).filter_by(codigo=course_code)).scalars().first()
    if not curso:
        flash(_("Curso no encontrado."), "error")
        return redirect(url_for(HOME_PAGE_ROUTE))

    if not curso.pagado:
        flash(_("Este curso es gratuito."), "info")
        return redirect(url_for("course.curso", course_code=course_code))

    # Check if PayPal is enabled
    if not check_paypal_enabled():
        flash(_("Los pagos con PayPal no están habilitados."), "error")
        return redirect(url_for("course.curso", course_code=course_code))

    # Get site currency
    site_currency = get_site_currency()

    from flask_wtf.csrf import generate_csrf

    return render_template(
        "learning/paypal_payment.html",
        curso=curso,
        site_currency=site_currency,
        pago=pago,
        csrf_token=generate_csrf(),
    )


@paypal.route("/get_client_id", methods=["GET"])
@login_required
def get_client_id() -> Response | tuple[FlaskResponse, int]:
    """Get PayPal client ID for JavaScript SDK."""
    try:
        row = database.session.execute(database.select(PaypalConfig)).first()
        if row is None:
            return jsonify({"error": PAYPAL_NOT_CONFIGURED_MESSAGE}), 500
        paypal_config = row[0]

        # Return the appropriate client ID based on sandbox mode
        client_id = paypal_config.paypal_sandbox if paypal_config.sandbox else paypal_config.paypal_id

        if not client_id:
            logging.error(f"PayPal client ID not configured for user {current_user.usuario}")
            return jsonify({"error": PAYPAL_NOT_CONFIGURED_MESSAGE}), 500

        return jsonify({"client_id": client_id, "sandbox": paypal_config.sandbox, "currency": get_site_currency()}), 200

    except Exception:
        logging.exception("Failed to get PayPal client ID")
        return jsonify({"error": "Configuration error"}), 500


@paypal.route("/payment_status/<course_code>", methods=["GET"])
@login_required
@perfil_requerido("student")
def payment_status(course_code: str) -> tuple[FlaskResponse, int]:
    """Check payment status for a course (useful for manual testing)."""
    try:
        from now_lms.db import EstudianteCurso

        # Check if course exists
        curso = database.session.execute(database.select(Curso).filter_by(codigo=course_code)).scalars().first()
        if not curso:
            return jsonify({"error": "Course not found"}), 404

        # Check enrollment status
        enrollment = (
            database.session.execute(
                database.select(EstudianteCurso).filter_by(usuario=current_user.usuario, curso=course_code, vigente=True)
            )
            .scalars()
            .first()
        )

        # Check payment records
        payments = (
            database.session.execute(
                database.select(Pago).filter_by(usuario=current_user.usuario, curso=course_code).order_by(Pago.fecha.desc())
            )
            .scalars()
            .all()
        )

        payment_info = []
        for payment in payments:
            payment_info.append(
                {
                    "id": payment.id,
                    "amount": float(payment.monto),
                    "currency": payment.moneda,
                    "method": payment.metodo,
                    "status": payment.estado,
                    "reference": payment.referencia,
                    "audit": payment.audit,
                    "created": payment.fecha.isoformat() if payment.fecha else None,
                }
            )

        return (
            jsonify(
                {
                    "course_code": course_code,
                    "course_name": curso.nombre,
                    "course_paid": curso.pagado,
                    "course_auditable": curso.auditable,
                    "course_price": float(curso.precio) if curso.precio else 0,
                    "enrolled": enrollment is not None,
                    "enrollment_active": enrollment.vigente if enrollment else False,
                    "payment_id": enrollment.pago if enrollment else None,
                    "payments": payment_info,
                    "site_currency": get_site_currency(),
                }
            ),
            200,
        )

    except Exception:
        logging.exception("Error getting payment status")
        return jsonify({"error": "Internal server error"}), 500


@paypal.route("/debug_config", methods=["GET"])
@login_required
@perfil_requerido("admin")
def debug_config() -> tuple[FlaskResponse, int]:
    """Debug endpoint for PayPal configuration (admin only, useful for manual testing)."""
    try:
        paypal_config = database.session.execute(database.select(PaypalConfig)).first()
        site_config = database.session.execute(database.select(Configuracion)).first()

        if not paypal_config:
            return jsonify({"error": "PayPal configuration not found"}), 404

        config_data = paypal_config[0]
        site_data = site_config[0] if site_config else None

        return (
            jsonify(
                {
                    "paypal_enabled": config_data.enable,
                    "sandbox_mode": config_data.sandbox,
                    "client_id_configured": bool(config_data.paypal_id),
                    "sandbox_client_id_configured": bool(config_data.paypal_sandbox),
                    "client_secret_configured": bool(config_data.paypal_secret),
                    "sandbox_secret_configured": bool(config_data.paypal_sandbox_secret),
                    "site_currency": site_data.moneda if site_data else "USD",
                    "site_title": site_data.titulo if site_data else "Not configured",
                    "cache_currency": get_site_currency(),
                    "current_client_id": config_data.paypal_sandbox if config_data.sandbox else config_data.paypal_id,
                }
            ),
            200,
        )

    except Exception:
        logging.exception("Error in debug config")
        return jsonify({"error": "Internal server error"}), 500
