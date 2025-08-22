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

"""PayPal Payments."""

# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------
import logging

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------
import requests
from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy.exc import OperationalError

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms.auth import perfil_requerido
from now_lms.cache import cache
from now_lms.config import DIRECTORIO_PLANTILLAS
from now_lms.db import Configuracion, Curso, Pago, PaypalConfig, database

# Constants for PayPal API URLs
PAYPAL_SANDBOX_API_URL = "https://api.sandbox.paypal.com"
PAYPAL_PRODUCTION_API_URL = "https://api.paypal.com"
HOME_PAGE_ROUTE = "home.pagina_de_inicio"

paypal = Blueprint("paypal", __name__, template_folder=DIRECTORIO_PLANTILLAS, url_prefix="/paypal_checkout")


@cache.cached(timeout=50)
def check_paypal_enabled():
    """Check if PayPal payments are enabled."""
    with current_app.app_context():
        try:
            q = database.session.execute(database.select(PaypalConfig)).first()[0]
            enabled = q.enable
            return enabled
        except OperationalError:
            return False


@cache.cached(timeout=50)
def get_site_currency():
    """Get the site's default currency from configuration."""
    with current_app.app_context():
        try:
            config = database.session.execute(database.select(Configuracion)).first()[0]
            return config.moneda or "USD"  # Default to USD if not configured
        except OperationalError:
            return "USD"


def validate_paypal_configuration(client_id, client_secret, sandbox=False):
    """Validate PayPal configuration by attempting to get an access token."""
    try:
        # Get access token from PayPal
        base_url = PAYPAL_SANDBOX_API_URL if sandbox else PAYPAL_PRODUCTION_API_URL
        token_url = f"{base_url}/v1/oauth2/token"

        headers = {
            "Accept": "application/json",
            "Accept-Language": "en_US",
        }

        data = "grant_type=client_credentials"

        response = requests.post(token_url, headers=headers, data=data, auth=(client_id, client_secret), timeout=20)

        if response.status_code == 200:
            return {"valid": True, "message": "Configuración de PayPal válida"}
        return {"valid": False, "message": f"Error de configuración de PayPal: {response.text}"}

    except Exception as e:
        return {"valid": False, "message": f"Error al validar configuración: {str(e)}"}


def get_paypal_access_token():
    """Get PayPal access token for API calls."""
    try:
        from now_lms.auth import descifrar_secreto

        paypal_config = database.session.execute(database.select(PaypalConfig)).first()
        if not paypal_config:
            logging.error("PayPal configuration not found in database")
            return None

        config_data = paypal_config[0]

        # Get the appropriate client ID and secret based on sandbox mode
        client_id = config_data.paypal_sandbox if config_data.sandbox else config_data.paypal_id
        client_secret_encrypted = config_data.paypal_sandbox_secret if config_data.sandbox else config_data.paypal_secret

        if not client_id:
            logging.error(f"PayPal client ID not configured for {'sandbox' if config_data.sandbox else 'production'} mode")
            return None

        if not client_secret_encrypted:
            logging.error(f"PayPal client secret not configured for {'sandbox' if config_data.sandbox else 'production'} mode")
            return None

        # Decrypt the client secret
        try:
            client_secret = descifrar_secreto(client_secret_encrypted).decode()
        except Exception as e:
            logging.error(f"Failed to decrypt PayPal client secret: {e}")
            return None

        # Get access token from PayPal
        base_url = PAYPAL_SANDBOX_API_URL if config_data.sandbox else PAYPAL_PRODUCTION_API_URL
        token_url = f"{base_url}/v1/oauth2/token"

        headers = {
            "Accept": "application/json",
            "Accept-Language": "en_US",
        }

        data = "grant_type=client_credentials"

        response = requests.post(token_url, headers=headers, data=data, auth=(client_id, client_secret), timeout=20)

        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get("access_token")
            if access_token:
                logging.info(
                    f"Successfully obtained PayPal access token ({'sandbox' if config_data.sandbox else 'production'})"
                )
                return access_token
            logging.error("PayPal access token missing in response")
            return None
        logging.error(f"Failed to get PayPal access token: HTTP {response.status_code} - {response.text}")
        return None

    except Exception as e:
        logging.error(f"Exception while getting PayPal access token: {e}")
        return None


def verify_paypal_payment(order_id, access_token):
    """Verify a PayPal payment by order ID."""
    try:
        paypal_config = database.session.execute(database.select(PaypalConfig)).first()[0]
        base_url = PAYPAL_SANDBOX_API_URL if paypal_config.sandbox else PAYPAL_PRODUCTION_API_URL
        order_url = f"{base_url}/v2/checkout/orders/{order_id}"

        headers = {
            "Content-Type": "application/json",
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
        logging.error(f"PayPal payment verification error: {e}")
        return {"verified": False, "error": str(e)}


@paypal.route("/confirm_payment", methods=["POST"])
@login_required
@perfil_requerido("student")
def confirm_payment():
    """Confirm PayPal payment after successful client-side processing."""
    try:
        data = request.get_json()

        if not data:
            logging.warning(f"Payment confirmation attempt without data from user {current_user.usuario}")
            return jsonify({"success": False, "error": "No payment data received"}), 400

        order_id = data.get("orderID")
        payer_id = data.get("payerID")
        course_code = data.get("courseCode")
        amount = data.get("amount")
        currency = data.get("currency", get_site_currency())

        logging.info(f"Payment confirmation attempt for user {current_user.usuario}, course {course_code}, order {order_id}")

        if not all([order_id, payer_id, course_code, amount]):
            missing_fields = [
                field
                for field, value in {
                    "orderID": order_id,
                    "payerID": payer_id,
                    "courseCode": course_code,
                    "amount": amount,
                }.items()
                if not value
            ]
            logging.warning(f"Payment confirmation missing fields {missing_fields} for user {current_user.usuario}")
            return (
                jsonify({"success": False, "error": f'Missing required payment data: {", ".join(missing_fields)}'}),
                400,
            )

        # Validate amount is numeric and positive
        try:
            amount_float = float(amount)
            if amount_float <= 0:
                raise ValueError("Amount must be positive")
        except (ValueError, TypeError) as e:
            logging.warning(f"Invalid payment amount {amount} for user {current_user.usuario}: {e}")
            return jsonify({"success": False, "error": "Invalid payment amount"}), 400

        # Get access token and verify payment with PayPal
        access_token = get_paypal_access_token()
        if not access_token:
            logging.error(f"Failed to get PayPal access token for user {current_user.usuario}")
            return jsonify({"success": False, "error": "PayPal configuration error - please contact support"}), 500

        verification = verify_paypal_payment(order_id, access_token)
        if not verification["verified"]:
            error_msg = verification.get("error", "Payment verification failed")
            logging.error(f"PayPal payment verification failed for order {order_id}, user {current_user.usuario}: {error_msg}")
            return jsonify({"success": False, "error": f"Payment verification failed: {error_msg}"}), 400

        # Check if payment amount matches expected amount (considering coupons)
        curso = database.session.execute(database.select(Curso).filter_by(codigo=course_code)).scalars().first()
        if not curso:
            logging.warning(f"Course {course_code} not found for payment confirmation by user {current_user.usuario}")
            return jsonify({"success": False, "error": "Course not found"}), 404

        # First check if there's a pending payment record for this user/course with coupon discount applied
        pending_payment = (
            database.session.execute(
                database.select(Pago).filter_by(usuario=current_user.usuario, curso=course_code, estado="pending")
            )
            .scalars()
            .first()
        )

        # Determine expected amount - either from pending payment (with coupon) or course price
        if pending_payment:
            expected_amount = float(pending_payment.monto)
        else:
            expected_amount = float(curso.precio)

        # Compare amounts with tolerance for floating point precision
        verified_amount = float(verification["amount"])
        amount_tolerance = 0.01  # 1 cent tolerance

        if abs(verified_amount - expected_amount) > amount_tolerance:
            logging.error(
                f"Payment amount mismatch for course {course_code}, user {current_user.usuario}: expected {expected_amount}, got {verified_amount}"
            )
            return (
                jsonify(
                    {
                        "success": False,
                        "error": f"Payment amount mismatch: expected {expected_amount}, received {verified_amount}",
                    }
                ),
                400,
            )

        # Check if this payment has already been processed
        existing_payment = database.session.execute(database.select(Pago).filter_by(referencia=order_id)).scalars().first()
        if existing_payment:
            if existing_payment.estado == "completed":
                logging.info(f"Payment {order_id} already completed for user {current_user.usuario}")
                return jsonify(
                    {
                        "success": True,
                        "message": "Pago ya procesado anteriormente",
                        "redirect_url": url_for("course.tomar_curso", course_code=course_code),
                    }
                )
            # Update existing payment
            existing_payment.estado = "completed"
            pago = existing_payment
        else:
            # Create new payment record
            pago = Pago()
            pago.usuario = current_user.usuario
            pago.curso = course_code
            pago.nombre = current_user.nombre
            pago.apellido = current_user.apellido
            pago.correo_electronico = current_user.correo_electronico
            pago.referencia = order_id

        # Update payment details
        pago.monto = verified_amount
        pago.moneda = currency
        pago.metodo = "paypal"
        pago.estado = "completed"

        try:
            if not existing_payment:
                database.session.add(pago)
            database.session.flush()

            # Check if enrollment already exists
            from now_lms.db import EstudianteCurso

            existing_enrollment = (
                database.session.execute(
                    database.select(EstudianteCurso).filter_by(usuario=current_user.usuario, curso=course_code)
                )
                .scalars()
                .first()
            )

            if not existing_enrollment:
                # Create course enrollment
                registro = EstudianteCurso(
                    curso=pago.curso,
                    usuario=pago.usuario,
                    vigente=True,
                    pago=pago.id,
                )
                database.session.add(registro)
            else:
                # Update existing enrollment
                existing_enrollment.vigente = True
                existing_enrollment.pago = pago.id

            database.session.commit()

            # Update coupon usage if payment had coupon applied
            if pago.descripcion and "Cupón aplicado:" in pago.descripcion:
                try:
                    # Extract coupon code from payment description
                    coupon_code = pago.descripcion.split("Cupón aplicado: ")[1].split(" ")[0]
                    from now_lms.db import Coupon

                    coupon = (
                        database.session.execute(database.select(Coupon).filter_by(course_id=course_code, code=coupon_code))
                        .scalars()
                        .first()
                    )

                    if coupon:
                        coupon.current_uses += 1
                        database.session.commit()
                        logging.info(f"Updated coupon {coupon_code} usage count to {coupon.current_uses}")
                except Exception as e:
                    logging.warning(f"Failed to update coupon usage for payment {order_id}: {e}")

            # Create course progress index
            from now_lms.vistas.courses import _crear_indice_avance_curso

            _crear_indice_avance_curso(course_code)

            logging.info(f"Payment {order_id} successfully processed for user {current_user.usuario}, course {course_code}")

            return jsonify(
                {
                    "success": True,
                    "message": "Pago completado exitosamente",
                    "redirect_url": url_for("course.tomar_curso", course_code=course_code),
                }
            )

        except OperationalError as e:
            database.session.rollback()
            logging.error(f"Database error during enrollment for user {current_user.usuario}, order {order_id}: {e}")
            return jsonify({"success": False, "error": "Error en la base de datos. Por favor contacte soporte."}), 500

    except Exception as e:
        logging.error(f"Unexpected error in payment confirmation for user {current_user.usuario}: {e}")
        return jsonify({"success": False, "error": "Error interno del servidor. Por favor contacte soporte."}), 500


@paypal.route("/resume_payment/<payment_id>")
@login_required
@perfil_requerido("student")
def resume_payment(payment_id):
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
            flash("Pago no encontrado o ya procesado.", "error")
            return redirect(url_for(HOME_PAGE_ROUTE))

        # Redirect to the payment page for this course
        return redirect(url_for("paypal.payment_page", course_code=pago.curso))

    except Exception as e:
        logging.error(f"Error resuming payment: {e}")
        flash("Error al reanudar el pago.", "error")
        return redirect(url_for(HOME_PAGE_ROUTE))


@paypal.route("/payment/<course_code>")
@login_required
@perfil_requerido("student")
def payment_page(course_code):
    """Display PayPal payment page for a course."""
    curso = database.session.execute(database.select(Curso).filter_by(codigo=course_code)).scalars().first()
    if not curso:
        flash("Curso no encontrado.", "error")
        return redirect(url_for(HOME_PAGE_ROUTE))

    if not curso.pagado:
        flash("Este curso es gratuito.", "info")
        return redirect(url_for("course.curso", course_code=course_code))

    # Check if PayPal is enabled
    if not check_paypal_enabled():
        flash("Los pagos con PayPal no están habilitados.", "error")
        return redirect(url_for("course.curso", course_code=course_code))

    # Get site currency
    site_currency = get_site_currency()

    return render_template("learning/paypal_payment.html", curso=curso, site_currency=site_currency)


@paypal.route("/get_client_id")
@login_required
def get_client_id():
    """Get PayPal client ID for JavaScript SDK."""
    try:
        paypal_config = database.session.execute(database.select(PaypalConfig)).first()[0]

        # Return the appropriate client ID based on sandbox mode
        client_id = paypal_config.paypal_sandbox if paypal_config.sandbox else paypal_config.paypal_id

        if not client_id:
            logging.error(f"PayPal client ID not configured for user {current_user.usuario}")
            return jsonify({"error": "PayPal not configured"}), 500

        return jsonify({"client_id": client_id, "sandbox": paypal_config.sandbox, "currency": get_site_currency()})

    except Exception as e:
        logging.error(f"Failed to get PayPal client ID for user {current_user.usuario}: {e}")
        return jsonify({"error": "Configuration error"}), 500


@paypal.route("/payment_status/<course_code>")
@login_required
@perfil_requerido("student")
def payment_status(course_code):
    """Check payment status for a course (useful for manual testing)."""
    try:
        from now_lms.db import Curso, EstudianteCurso

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

        return jsonify(
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
        )

    except Exception as e:
        logging.error(f"Error getting payment status for course {course_code}, user {current_user.usuario}: {e}")
        return jsonify({"error": "Internal server error"}), 500


@paypal.route("/debug_config")
@login_required
@perfil_requerido("admin")
def debug_config():
    """Debug endpoint for PayPal configuration (admin only, useful for manual testing)."""
    try:
        paypal_config = database.session.execute(database.select(PaypalConfig)).first()
        site_config = database.session.execute(database.select(Configuracion)).first()

        if not paypal_config:
            return jsonify({"error": "PayPal configuration not found"}), 404

        config_data = paypal_config[0]
        site_data = site_config[0] if site_config else None

        return jsonify(
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
        )

    except Exception as e:
        logging.error(f"Error in debug config for user {current_user.usuario}: {e}")
        return jsonify({"error": "Internal server error"}), 500
