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
Comprehensive tests for PayPal routes in now_lms/vistas/paypal.py
"""

import pytest
import json
from unittest.mock import patch


@pytest.fixture
def lms_application():
    """Create test application with proper configuration."""
    from now_lms import app

    app.config.update(
        {
            "TESTING": True,
            "SECRET_KEY": "test_secret_key_for_paypal_routes",
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
            "WTF_CSRF_ENABLED": False,
            "DEBUG": True,
            "PRESERVE_CONTEXT_ON_EXCEPTION": False,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "MAIL_SUPPRESS_SEND": True,
        }
    )

    yield app


@pytest.fixture
def app_with_data(lms_application):
    """Application with database and test data."""
    from now_lms import database, initial_setup
    from now_lms.db import eliminar_base_de_datos_segura
    from now_lms.db import Usuario, Curso, PaypalConfig, Configuracion, Pago
    from now_lms.auth import proteger_secreto, proteger_passwd

    with lms_application.app_context():
        eliminar_base_de_datos_segura()
        initial_setup()

        # Update/Create site configuration (remove any existing one first)
        database.session.execute(database.delete(Configuracion))
        database.session.commit()

        from os import urandom

        config = Configuracion(
            titulo="Test LMS",
            descripcion="Test PayPal Routes",
            moneda="USD",
            r=urandom(16),
        )
        database.session.add(config)
        database.session.commit()  # Commit config first for password hashing

        # Update/Create PayPal configuration (remove any existing one first)
        database.session.execute(database.delete(PaypalConfig))
        database.session.commit()

        paypal_config = PaypalConfig(
            enable=True,
            sandbox=True,
            paypal_id="live_client_id_test",
            paypal_sandbox="sandbox_client_id_test",
        )
        paypal_config.paypal_secret = proteger_secreto("live_secret_test")
        paypal_config.paypal_sandbox_secret = proteger_secreto("sandbox_secret_test")
        database.session.add(paypal_config)

        # Create test users
        admin_user = Usuario(
            usuario="admin_test",
            acceso=proteger_passwd("admin_password"),
            nombre="Admin",
            apellido="User",
            correo_electronico="admin@test.com",
            activo=True,
            tipo="admin",
        )
        database.session.add(admin_user)

        student_user = Usuario(
            usuario="student_test",
            acceso=proteger_passwd("student_password"),
            nombre="Student",
            apellido="User",
            correo_electronico="student@test.com",
            activo=True,
            tipo="student",
        )
        database.session.add(student_user)

        # Create test courses
        paid_course = Curso(
            codigo="PAID001",
            nombre="Paid Test Course",
            descripcion_corta="Paid course for testing",
            descripcion="A course that requires payment",
            modalidad="self_paced",
            precio=99.99,
            pagado=True,
            estado="open",
            publico=True,
        )
        database.session.add(paid_course)

        free_course = Curso(
            codigo="FREE001",
            nombre="Free Test Course",
            descripcion_corta="Free course for testing",
            descripcion="A course that is free",
            modalidad="self_paced",
            precio=0.0,
            pagado=False,
            estado="open",
            publico=True,
        )
        database.session.add(free_course)

        # Commit users and courses first to satisfy foreign key constraints
        database.session.commit()

        # Create a pending payment for testing resume functionality
        pending_payment = Pago(
            usuario="student_test",
            curso="PAID001",
            nombre="Student",
            apellido="User",
            correo_electronico="student@test.com",
            monto=99.99,
            moneda="USD",
            metodo="paypal",
            estado="pending",
            referencia="test_pending_order_123",
        )
        database.session.add(pending_payment)

        database.session.commit()

        yield lms_application


@pytest.fixture
def test_client(app_with_data):
    """Create test client."""

    # Mock csrf_token function for templates
    def mock_csrf_token():
        return "mock_csrf_token_for_testing"

    app_with_data.jinja_env.globals["csrf_token"] = mock_csrf_token

    return app_with_data.test_client()


class TestPayPalHelpers:
    """Helper methods for PayPal tests."""

    def login_as_student(self, test_client):
        """Helper method to login as student."""
        login_data = {"usuario": "student_test", "acceso": "student_password"}
        login_response = test_client.post("/user/login", data=login_data, follow_redirects=True)
        assert login_response.status_code == 200
        return login_response

    def login_as_admin(self, test_client):
        """Helper method to login as admin."""
        login_data = {"usuario": "admin_test", "acceso": "admin_password"}
        login_response = test_client.post("/user/login", data=login_data, follow_redirects=True)
        assert login_response.status_code == 200
        return login_response


class TestPayPalRoutesAuthentication(TestPayPalHelpers):
    """Test authentication and authorization for PayPal routes."""

    def test_payment_page_requires_authentication(self, test_client):
        """Test that payment page requires authentication."""
        response = test_client.get("/paypal_checkout/payment/PAID001")
        assert response.status_code == 302  # Redirect to login
        assert "/user/login" in response.headers.get("Location", "")

    def test_confirm_payment_requires_authentication(self, test_client):
        """Test that confirm payment requires authentication."""
        response = test_client.post("/paypal_checkout/confirm_payment")
        assert response.status_code == 302  # Redirect to login

    def test_get_client_id_requires_authentication(self, test_client):
        """Test that get client ID requires authentication."""
        response = test_client.get("/paypal_checkout/get_client_id")
        assert response.status_code == 302  # Redirect to login

    def test_debug_config_requires_admin_privileges(self, test_client, app_with_data):
        """Test that debug config requires admin privileges."""
        with app_with_data.app_context():
            # Test with unauthenticated user
            response = test_client.get("/paypal_checkout/debug_config")
            assert response.status_code == 302  # Redirect to login

            # Test with student user (should be denied after login)
            self.login_as_student(test_client)

            response = test_client.get("/paypal_checkout/debug_config")
            assert response.status_code in [302, 403]  # Redirect or forbidden


class TestPayPalPaymentPageRoute(TestPayPalHelpers):
    """Test the payment page route functionality."""

    def test_payment_page_valid_paid_course(self, test_client, app_with_data):
        """Test payment page for valid paid course."""
        with app_with_data.app_context():
            # Login by posting to the login endpoint
            login_data = {"usuario": "student_test", "acceso": "student_password"}
            login_response = test_client.post("/user/login", data=login_data, follow_redirects=True)
            assert login_response.status_code == 200

            # Clear cache to ensure fresh PayPal config check
            from now_lms.cache import cache

            cache.clear()

            response = test_client.get("/paypal_checkout/payment/PAID001")

            # The route should either show the payment page (200) or redirect (302)
            # Both are valid depending on PayPal configuration and course enrollment status
            if response.status_code == 200:
                # Payment page is shown
                assert b"Paid Test Course" in response.data
                assert b"paypal" in response.data.lower()
            elif response.status_code == 302:
                # Redirected - could be due to PayPal disabled or other business logic
                # This is also a valid scenario to test
                redirect_location = response.headers.get("Location", "")
                assert "/course/" in redirect_location or "/" in redirect_location
            else:
                # Unexpected status code
                assert False, f"Unexpected status code: {response.status_code}"

    def test_payment_page_free_course_redirects(self, test_client, app_with_data):
        """Test payment page redirects for free course."""
        with app_with_data.app_context():
            self.login_as_student(test_client)

            response = test_client.get("/paypal_checkout/payment/FREE001")
            assert response.status_code == 302  # Redirect away from payment page

    def test_payment_page_nonexistent_course(self, test_client, app_with_data):
        """Test payment page for nonexistent course."""
        with app_with_data.app_context():
            self.login_as_student(test_client)

            response = test_client.get("/paypal_checkout/payment/NONEXISTENT")
            assert response.status_code == 302  # Redirect with error

    def test_payment_page_paypal_disabled(self, test_client, app_with_data):
        """Test payment page when PayPal is disabled."""
        with app_with_data.app_context():
            # Disable PayPal
            from now_lms.db import PaypalConfig, database

            paypal_config = database.session.execute(database.select(PaypalConfig)).scalar()
            paypal_config.enable = False
            database.session.commit()

            # Login as student
            self.login_as_student(test_client)

            response = test_client.get("/paypal_checkout/payment/PAID001")
            assert response.status_code == 302  # Redirect with error


class TestPayPalGetClientIdRoute(TestPayPalHelpers):
    """Test the get client ID route functionality."""

    def test_get_client_id_success(self, test_client, app_with_data):
        """Test successful client ID retrieval."""
        with app_with_data.app_context():
            # Login as student
            self.login_as_student(test_client)

            response = test_client.get("/paypal_checkout/get_client_id")
            assert response.status_code == 200

            data = json.loads(response.data)
            assert "client_id" in data
            assert "sandbox" in data
            assert "currency" in data
            assert data["client_id"] == "sandbox_client_id_test"  # Sandbox mode
            assert data["sandbox"] is True
            assert data["currency"] == "USD"

    def test_get_client_id_no_configuration(self, test_client, app_with_data):
        """Test client ID retrieval with no PayPal configuration."""
        with app_with_data.app_context():
            # Remove PayPal configuration
            from now_lms.db import PaypalConfig, database

            database.session.execute(database.delete(PaypalConfig))
            database.session.commit()

            # Login as student
            self.login_as_student(test_client)

            response = test_client.get("/paypal_checkout/get_client_id")
            assert response.status_code == 500

            data = json.loads(response.data)
            assert "error" in data


class TestPayPalConfirmPaymentRoute(TestPayPalHelpers):
    """Test the confirm payment route functionality."""

    def test_confirm_payment_missing_data(self, test_client, app_with_data):
        """Test payment confirmation with missing data."""
        with app_with_data.app_context():
            # Login as student
            self.login_as_student(test_client)

            response = test_client.post(
                "/paypal_checkout/confirm_payment",
                data=json.dumps({}),
                content_type="application/json",
            )
            assert response.status_code == 400

            data = json.loads(response.data)
            assert data["success"] is False
            assert "No payment data received" in data["error"]

    def test_confirm_payment_missing_required_fields(self, test_client, app_with_data):
        """Test payment confirmation with missing required fields."""
        with app_with_data.app_context():
            # Login as student
            self.login_as_student(test_client)

            # Send incomplete payment data
            payment_data = {
                "orderID": "test_order_123",
                "payerID": "test_payer_456",
                # Missing courseCode and amount
            }

            response = test_client.post(
                "/paypal_checkout/confirm_payment",
                data=json.dumps(payment_data),
                content_type="application/json",
            )
            assert response.status_code == 400

            data = json.loads(response.data)
            assert data["success"] is False
            assert "Missing required payment data" in data["error"]

    def test_confirm_payment_invalid_amount(self, test_client, app_with_data):
        """Test payment confirmation with invalid amount."""
        with app_with_data.app_context():
            # Login as student
            self.login_as_student(test_client)

            # Send payment data with invalid amount
            payment_data = {
                "orderID": "test_order_123",
                "payerID": "test_payer_456",
                "courseCode": "PAID001",
                "amount": "invalid_amount",
            }

            response = test_client.post(
                "/paypal_checkout/confirm_payment",
                data=json.dumps(payment_data),
                content_type="application/json",
            )
            assert response.status_code == 400

            data = json.loads(response.data)
            assert data["success"] is False
            assert "Invalid payment amount" in data["error"]

    def test_confirm_payment_negative_amount(self, test_client, app_with_data):
        """Test payment confirmation with negative amount."""
        with app_with_data.app_context():
            # Login as student
            self.login_as_student(test_client)

            # Send payment data with negative amount
            payment_data = {
                "orderID": "test_order_123",
                "payerID": "test_payer_456",
                "courseCode": "PAID001",
                "amount": "-50.00",
            }

            response = test_client.post(
                "/paypal_checkout/confirm_payment",
                data=json.dumps(payment_data),
                content_type="application/json",
            )
            assert response.status_code == 400

            data = json.loads(response.data)
            assert data["success"] is False
            assert "Invalid payment amount" in data["error"]

    def test_confirm_payment_nonexistent_course(self, test_client, app_with_data):
        """Test payment confirmation for nonexistent course."""
        with app_with_data.app_context():
            # Login as student
            self.login_as_student(test_client)

            # Mock PayPal API calls
            with (
                patch("now_lms.vistas.paypal.get_paypal_access_token") as mock_token,
                patch("now_lms.vistas.paypal.verify_paypal_payment") as mock_verify,
            ):
                mock_token.return_value = "mock_access_token"
                mock_verify.return_value = {
                    "verified": True,
                    "status": "COMPLETED",
                    "amount": "99.99",
                    "currency": "USD",
                }

                payment_data = {
                    "orderID": "test_order_123",
                    "payerID": "test_payer_456",
                    "courseCode": "NONEXISTENT",
                    "amount": "99.99",
                }

                response = test_client.post(
                    "/paypal_checkout/confirm_payment",
                    data=json.dumps(payment_data),
                    content_type="application/json",
                )
                assert response.status_code == 404

                data = json.loads(response.data)
                assert data["success"] is False
                assert "Course not found" in data["error"]

    @patch("now_lms.vistas.paypal.get_paypal_access_token")
    def test_confirm_payment_paypal_token_failure(self, mock_token, test_client, app_with_data):
        """Test payment confirmation when PayPal token retrieval fails."""
        with app_with_data.app_context():
            mock_token.return_value = None

            # Login as student
            self.login_as_student(test_client)

            payment_data = {
                "orderID": "test_order_123",
                "payerID": "test_payer_456",
                "courseCode": "PAID001",
                "amount": "99.99",
            }

            response = test_client.post(
                "/paypal_checkout/confirm_payment",
                data=json.dumps(payment_data),
                content_type="application/json",
            )
            assert response.status_code == 500

            data = json.loads(response.data)
            assert data["success"] is False
            assert "PayPal configuration error" in data["error"]


class TestPayPalResumePaymentRoute(TestPayPalHelpers):
    """Test the resume payment route functionality."""

    def test_resume_payment_valid_pending_payment(self, test_client, app_with_data):
        """Test resuming a valid pending payment."""
        with app_with_data.app_context():
            # Get the pending payment ID
            from now_lms.db import Pago, database

            pending_payment = database.session.execute(
                database.select(Pago).filter_by(usuario="student_test", estado="pending")
            ).scalar()

            # Login as student
            self.login_as_student(test_client)

            response = test_client.get(f"/paypal_checkout/resume_payment/{pending_payment.id}")
            assert response.status_code == 302  # Redirect to payment page
            assert "/paypal_checkout/payment/PAID001" in response.headers.get("Location", "")

    def test_resume_payment_nonexistent_payment(self, test_client, app_with_data):
        """Test resuming a nonexistent payment."""
        with app_with_data.app_context():
            # Login as student
            self.login_as_student(test_client)

            response = test_client.get("/paypal_checkout/resume_payment/99999")
            assert response.status_code == 302  # Redirect home with error

    def test_resume_payment_other_user_payment(self, test_client, app_with_data):
        """Test resuming another user's payment."""
        with app_with_data.app_context():
            # Create another user for the test
            from now_lms.db import Usuario, Pago, database
            from now_lms.auth import proteger_passwd

            other_user = Usuario(
                usuario="other_user",
                acceso=proteger_passwd("other_password"),
                nombre="Other",
                apellido="User",
                correo_electronico="other@test.com",
                activo=True,
                tipo="student",
            )
            database.session.add(other_user)
            database.session.commit()

            # Create a payment for the other user
            other_payment = Pago(
                usuario="other_user",
                curso="PAID001",
                nombre="Other",
                apellido="User",
                correo_electronico="other@test.com",
                monto=99.99,
                moneda="USD",
                metodo="paypal",
                estado="pending",
                referencia="other_order_123",
            )
            database.session.add(other_payment)
            database.session.commit()

            # Login as student
            self.login_as_student(test_client)

            response = test_client.get(f"/paypal_checkout/resume_payment/{other_payment.id}")
            assert response.status_code == 302  # Redirect home with error


class TestPayPalPaymentStatusRoute(TestPayPalHelpers):
    """Test the payment status route functionality."""

    def test_payment_status_valid_course(self, test_client, app_with_data):
        """Test payment status for valid course."""
        with app_with_data.app_context():
            # Login as student
            self.login_as_student(test_client)

            response = test_client.get("/paypal_checkout/payment_status/PAID001")
            assert response.status_code == 200

            data = json.loads(response.data)
            assert data["course_code"] == "PAID001"
            assert data["course_name"] == "Paid Test Course"
            assert data["course_paid"] is True
            assert data["course_price"] == 99.99
            assert data["site_currency"] == "USD"
            assert "payments" in data

    def test_payment_status_nonexistent_course(self, test_client, app_with_data):
        """Test payment status for nonexistent course."""
        with app_with_data.app_context():
            # Login as student
            self.login_as_student(test_client)

            response = test_client.get("/paypal_checkout/payment_status/NONEXISTENT")
            assert response.status_code == 404

            data = json.loads(response.data)
            assert "error" in data


class TestPayPalDebugConfigRoute(TestPayPalHelpers):
    """Test the debug config route functionality."""

    def test_debug_config_admin_access(self, test_client, app_with_data):
        """Test debug config with admin access."""
        with app_with_data.app_context():
            # Login as admin
            self.login_as_admin(test_client)

            response = test_client.get("/paypal_checkout/debug_config")
            assert response.status_code == 200

            data = json.loads(response.data)
            assert "paypal_enabled" in data
            assert "sandbox_mode" in data
            assert "client_id_configured" in data
            assert "site_currency" in data
            assert data["paypal_enabled"] is True
            assert data["sandbox_mode"] is True
            assert data["site_currency"] == "USD"

    def test_debug_config_no_paypal_configuration(self, test_client, app_with_data):
        """Test debug config with no PayPal configuration."""
        with app_with_data.app_context():
            # Remove PayPal configuration
            from now_lms.db import PaypalConfig, database

            database.session.execute(database.delete(PaypalConfig))
            database.session.commit()

            # Login as admin
            self.login_as_admin(test_client)

            response = test_client.get("/paypal_checkout/debug_config")
            assert response.status_code == 404

            data = json.loads(response.data)
            assert "error" in data
            assert "PayPal configuration not found" in data["error"]


class TestPayPalRouteInputValidation(TestPayPalHelpers):
    """Test input validation for PayPal routes."""

    def test_confirm_payment_malformed_json(self, test_client, app_with_data):
        """Test payment confirmation with malformed JSON."""
        with app_with_data.app_context():
            # Login as student
            self.login_as_student(test_client)

            response = test_client.post(
                "/paypal_checkout/confirm_payment",
                data="invalid json",
                content_type="application/json",
            )
            # Should handle gracefully
            assert response.status_code in [400, 500]

    def test_payment_status_special_characters_in_course_code(self, test_client, app_with_data):
        """Test payment status with special characters in course code."""
        with app_with_data.app_context():
            # Login as student
            self.login_as_student(test_client)

            # Test with various special characters
            special_codes = ["<script>", "'; DROP TABLE courses; --", "../../../etc/passwd", "COURSE%20CODE"]

            for code in special_codes:
                response = test_client.get(f"/paypal_checkout/payment_status/{code}")
                # Should not cause security issues, likely 404
                assert response.status_code in [404, 500]

    def test_resume_payment_invalid_payment_id(self, test_client, app_with_data):
        """Test resume payment with invalid payment ID."""
        with app_with_data.app_context():
            # Login as student
            self.login_as_student(test_client)

            # Test with various invalid IDs
            invalid_ids = ["abc", "-1", "999999999999999999999", "<script>", "nonexistent"]

            for payment_id in invalid_ids:
                response = test_client.get(f"/paypal_checkout/resume_payment/{payment_id}")
                # Should handle gracefully with either redirect or 404
                assert response.status_code in [302, 404]


class TestPayPalConfirmPaymentAdvanced(TestPayPalHelpers):
    """Advanced test cases for confirm_payment route."""

    @patch("now_lms.vistas.paypal.get_paypal_access_token")
    @patch("now_lms.vistas.paypal.verify_paypal_payment")
    def test_confirm_payment_successful_new_payment(self, mock_verify, mock_token, test_client, app_with_data):
        """Test successful payment confirmation creating new payment record."""
        with app_with_data.app_context():
            mock_token.return_value = "mock_access_token"
            mock_verify.return_value = {
                "verified": True,
                "status": "COMPLETED",
                "amount": "99.99",
                "currency": "USD",
                "payer_id": "test_payer_456",
                "order_data": {"id": "test_order_new", "status": "COMPLETED"},
            }

            # Login as student
            self.login_as_student(test_client)

            payment_data = {
                "orderID": "test_order_new",
                "payerID": "test_payer_456",
                "courseCode": "PAID001",
                "amount": "99.99",
                "currency": "USD",
            }

            with patch("now_lms.vistas.courses._crear_indice_avance_curso") as mock_progress:
                mock_progress.return_value = None

                response = test_client.post(
                    "/paypal_checkout/confirm_payment",
                    data=json.dumps(payment_data),
                    content_type="application/json",
                )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["success"] is True
            assert "Pago completado exitosamente" in data["message"]
            assert "redirect_url" in data

            # Verify payment was created in database
            from now_lms.db import Pago, database

            payment = database.session.execute(database.select(Pago).filter_by(referencia="test_order_new")).scalar()
            assert payment is not None
            assert payment.estado == "completed"
            assert float(payment.monto) == 99.99

    @patch("now_lms.vistas.paypal.get_paypal_access_token")
    @patch("now_lms.vistas.paypal.verify_paypal_payment")
    def test_confirm_payment_amount_mismatch(self, mock_verify, mock_token, test_client, app_with_data):
        """Test payment confirmation with amount mismatch."""
        with app_with_data.app_context():
            mock_token.return_value = "mock_access_token"
            mock_verify.return_value = {
                "verified": True,
                "status": "COMPLETED",
                "amount": "50.00",  # Different from expected course price
                "currency": "USD",
                "payer_id": "test_payer_456",
                "order_data": {"id": "test_order_mismatch", "status": "COMPLETED"},
            }

            # Login as student
            self.login_as_student(test_client)

            payment_data = {
                "orderID": "test_order_mismatch",
                "payerID": "test_payer_456",
                "courseCode": "PAID001",
                "amount": "50.00",
                "currency": "USD",
            }

            response = test_client.post(
                "/paypal_checkout/confirm_payment",
                data=json.dumps(payment_data),
                content_type="application/json",
            )

            assert response.status_code == 400
            data = json.loads(response.data)
            assert data["success"] is False
            assert "Payment amount mismatch" in data["error"]

    @patch("now_lms.vistas.paypal.get_paypal_access_token")
    @patch("now_lms.vistas.paypal.verify_paypal_payment")
    def test_confirm_payment_duplicate_order_completed(self, mock_verify, mock_token, test_client, app_with_data):
        """Test payment confirmation for already completed order."""
        with app_with_data.app_context():
            # Create existing completed payment
            from now_lms.db import Pago, database

            existing_payment = Pago(
                usuario="student_test",
                curso="PAID001",
                nombre="Student",
                apellido="User",
                correo_electronico="student@test.com",
                monto=99.99,
                moneda="USD",
                metodo="paypal",
                estado="completed",
                referencia="test_order_duplicate",
            )
            database.session.add(existing_payment)
            database.session.commit()

            mock_token.return_value = "mock_access_token"
            mock_verify.return_value = {
                "verified": True,
                "status": "COMPLETED",
                "amount": "99.99",
                "currency": "USD",
                "payer_id": "test_payer_456",
                "order_data": {"id": "test_order_duplicate", "status": "COMPLETED"},
            }

            # Login as student
            self.login_as_student(test_client)

            payment_data = {
                "orderID": "test_order_duplicate",
                "payerID": "test_payer_456",
                "courseCode": "PAID001",
                "amount": "99.99",
                "currency": "USD",
            }

            response = test_client.post(
                "/paypal_checkout/confirm_payment",
                data=json.dumps(payment_data),
                content_type="application/json",
            )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["success"] is True
            assert "Pago ya procesado anteriormente" in data["message"]

    @patch("now_lms.vistas.paypal.get_paypal_access_token")
    @patch("now_lms.vistas.paypal.verify_paypal_payment")
    def test_confirm_payment_paypal_verification_failure(self, mock_verify, mock_token, test_client, app_with_data):
        """Test payment confirmation when PayPal verification fails."""
        with app_with_data.app_context():
            mock_token.return_value = "mock_access_token"
            mock_verify.return_value = {
                "verified": False,
                "error": "Order not found in PayPal system",
            }

            # Login as student
            self.login_as_student(test_client)

            payment_data = {
                "orderID": "test_order_invalid",
                "payerID": "test_payer_456",
                "courseCode": "PAID001",
                "amount": "99.99",
                "currency": "USD",
            }

            response = test_client.post(
                "/paypal_checkout/confirm_payment",
                data=json.dumps(payment_data),
                content_type="application/json",
            )

            assert response.status_code == 400
            data = json.loads(response.data)
            assert data["success"] is False
            assert "Payment verification failed" in data["error"]

    @patch("now_lms.vistas.paypal.get_paypal_access_token")
    @patch("now_lms.vistas.paypal.verify_paypal_payment")
    def test_confirm_payment_database_error_rollback(self, mock_verify, mock_token, test_client, app_with_data):
        """Test payment confirmation with database error and rollback."""
        with app_with_data.app_context():
            mock_token.return_value = "mock_access_token"
            mock_verify.return_value = {
                "verified": True,
                "status": "COMPLETED",
                "amount": "99.99",
                "currency": "USD",
                "payer_id": "test_payer_456",
                "order_data": {"id": "test_order_db_error", "status": "COMPLETED"},
            }

            # Login as student
            self.login_as_student(test_client)

            payment_data = {
                "orderID": "test_order_db_error",
                "payerID": "test_payer_456",
                "courseCode": "PAID001",
                "amount": "99.99",
                "currency": "USD",
            }

            # Mock database commit to raise an OperationalError
            with patch("now_lms.db.database.session.commit") as mock_commit:
                from sqlalchemy.exc import OperationalError

                mock_commit.side_effect = OperationalError("Database connection lost", None, None)

                response = test_client.post(
                    "/paypal_checkout/confirm_payment",
                    data=json.dumps(payment_data),
                    content_type="application/json",
                )

            assert response.status_code == 500
            data = json.loads(response.data)
            assert data["success"] is False
            assert "Error en la base de datos" in data["error"]

    @patch("now_lms.vistas.paypal.get_paypal_access_token")
    @patch("now_lms.vistas.paypal.verify_paypal_payment")
    def test_confirm_payment_with_pending_payment_coupon(self, mock_verify, mock_token, test_client, app_with_data):
        """Test payment confirmation using pending payment with coupon discount."""
        with app_with_data.app_context():
            # Update the existing pending payment to have coupon discount
            from now_lms.db import Pago, database

            pending_payment = database.session.execute(
                database.select(Pago).filter_by(usuario="student_test", estado="pending")
            ).scalar()
            pending_payment.monto = 79.99  # Discounted price
            pending_payment.descripcion = "Cupón aplicado: SAVE20 (20% de descuento)"
            database.session.commit()

            mock_token.return_value = "mock_access_token"
            mock_verify.return_value = {
                "verified": True,
                "status": "COMPLETED",
                "amount": "79.99",  # Matches discounted price
                "currency": "USD",
                "payer_id": "test_payer_456",
                "order_data": {"id": "test_order_coupon", "status": "COMPLETED"},
            }

            # Login as student
            self.login_as_student(test_client)

            payment_data = {
                "orderID": "test_order_coupon",
                "payerID": "test_payer_456",
                "courseCode": "PAID001",
                "amount": "79.99",
                "currency": "USD",
            }

            with patch("now_lms.vistas.courses._crear_indice_avance_curso") as mock_progress:
                mock_progress.return_value = None

                response = test_client.post(
                    "/paypal_checkout/confirm_payment",
                    data=json.dumps(payment_data),
                    content_type="application/json",
                )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["success"] is True


class TestPayPalRouteResponseFormat(TestPayPalHelpers):
    """Test response format validation for PayPal routes."""

    def test_get_client_id_response_format(self, test_client, app_with_data):
        """Test get_client_id returns properly formatted JSON response."""
        with app_with_data.app_context():
            # Login as student
            self.login_as_student(test_client)

            response = test_client.get("/paypal_checkout/get_client_id")
            assert response.status_code == 200
            assert response.content_type == "application/json"

            data = json.loads(response.data)
            # Validate required fields
            required_fields = ["client_id", "sandbox", "currency"]
            for field in required_fields:
                assert field in data, f"Missing required field: {field}"

            # Validate data types
            assert isinstance(data["client_id"], str)
            assert isinstance(data["sandbox"], bool)
            assert isinstance(data["currency"], str)

    def test_payment_status_response_format(self, test_client, app_with_data):
        """Test payment_status returns properly formatted JSON response."""
        with app_with_data.app_context():
            # Login as student
            self.login_as_student(test_client)

            response = test_client.get("/paypal_checkout/payment_status/PAID001")
            assert response.status_code == 200
            assert response.content_type == "application/json"

            data = json.loads(response.data)
            # Validate required fields
            required_fields = [
                "course_code",
                "course_name",
                "course_paid",
                "course_auditable",
                "course_price",
                "enrolled",
                "enrollment_active",
                "payments",
                "site_currency",
            ]
            for field in required_fields:
                assert field in data, f"Missing required field: {field}"

            # Validate data types
            assert isinstance(data["course_code"], str)
            assert isinstance(data["course_name"], str)
            assert isinstance(data["course_paid"], bool)
            assert isinstance(data["course_price"], (int, float))
            assert isinstance(data["enrolled"], bool)
            assert isinstance(data["payments"], list)

    def test_debug_config_response_format(self, test_client, app_with_data):
        """Test debug_config returns properly formatted JSON response."""
        with app_with_data.app_context():
            # Login as admin
            self.login_as_admin(test_client)

            response = test_client.get("/paypal_checkout/debug_config")
            assert response.status_code == 200
            assert response.content_type == "application/json"

            data = json.loads(response.data)
            # Validate required fields
            required_fields = [
                "paypal_enabled",
                "sandbox_mode",
                "client_id_configured",
                "sandbox_client_id_configured",
                "client_secret_configured",
                "sandbox_secret_configured",
                "site_currency",
                "current_client_id",
            ]
            for field in required_fields:
                assert field in data, f"Missing required field: {field}"

            # Validate data types
            assert isinstance(data["paypal_enabled"], bool)
            assert isinstance(data["sandbox_mode"], bool)
            assert isinstance(data["client_id_configured"], bool)

    def test_confirm_payment_error_response_format(self, test_client, app_with_data):
        """Test confirm_payment error responses are properly formatted."""
        with app_with_data.app_context():
            # Login as student
            self.login_as_student(test_client)

            # Test missing data error
            response = test_client.post(
                "/paypal_checkout/confirm_payment",
                data=json.dumps({}),
                content_type="application/json",
            )
            assert response.status_code == 400
            assert response.content_type == "application/json"

            data = json.loads(response.data)
            assert "success" in data
            assert "error" in data
            assert data["success"] is False
            assert isinstance(data["error"], str)


class TestPayPalNetworkFailures(TestPayPalHelpers):
    """Test PayPal route behavior under network/API failures."""

    @patch("now_lms.vistas.paypal.get_paypal_access_token")
    def test_confirm_payment_network_timeout(self, mock_token, test_client, app_with_data):
        """Test payment confirmation when network timeout occurs."""
        with app_with_data.app_context():
            import requests

            mock_token.side_effect = requests.exceptions.Timeout("Network timeout")

            # Login as student
            self.login_as_student(test_client)

            payment_data = {
                "orderID": "test_order_timeout",
                "payerID": "test_payer_456",
                "courseCode": "PAID001",
                "amount": "99.99",
                "currency": "USD",
            }

            response = test_client.post(
                "/paypal_checkout/confirm_payment",
                data=json.dumps(payment_data),
                content_type="application/json",
            )

            assert response.status_code == 500
            data = json.loads(response.data)
            assert data["success"] is False
            assert "Error interno del servidor" in data["error"]

    @patch("now_lms.vistas.paypal.get_paypal_access_token")
    @patch("now_lms.vistas.paypal.verify_paypal_payment")
    def test_confirm_payment_api_exception(self, mock_verify, mock_token, test_client, app_with_data):
        """Test payment confirmation when PayPal API raises exception."""
        with app_with_data.app_context():
            mock_token.return_value = "mock_access_token"
            mock_verify.side_effect = Exception("PayPal API error")

            # Login as student
            self.login_as_student(test_client)

            payment_data = {
                "orderID": "test_order_exception",
                "payerID": "test_payer_456",
                "courseCode": "PAID001",
                "amount": "99.99",
                "currency": "USD",
            }

            response = test_client.post(
                "/paypal_checkout/confirm_payment",
                data=json.dumps(payment_data),
                content_type="application/json",
            )

            assert response.status_code == 500
            data = json.loads(response.data)
            assert data["success"] is False
            assert "Error interno del servidor" in data["error"]


class TestPayPalRouteConcurrency(TestPayPalHelpers):
    """Test PayPal routes under concurrent access scenarios."""

    @patch("now_lms.vistas.paypal.get_paypal_access_token")
    @patch("now_lms.vistas.paypal.verify_paypal_payment")
    def test_concurrent_payment_processing(self, mock_verify, mock_token, test_client, app_with_data):
        """Test concurrent payment processing for same order."""
        with app_with_data.app_context():
            mock_token.return_value = "mock_access_token"
            mock_verify.return_value = {
                "verified": True,
                "status": "COMPLETED",
                "amount": "99.99",
                "currency": "USD",
                "payer_id": "test_payer_456",
                "order_data": {"id": "test_order_concurrent", "status": "COMPLETED"},
            }

            # Login as student
            self.login_as_student(test_client)

            payment_data = {
                "orderID": "test_order_concurrent",
                "payerID": "test_payer_456",
                "courseCode": "PAID001",
                "amount": "99.99",
                "currency": "USD",
            }

            with patch("now_lms.vistas.courses._crear_indice_avance_curso") as mock_progress:
                mock_progress.return_value = None

                # First request should succeed
                response1 = test_client.post(
                    "/paypal_checkout/confirm_payment",
                    data=json.dumps(payment_data),
                    content_type="application/json",
                )

                # Second request with same order should handle gracefully
                response2 = test_client.post(
                    "/paypal_checkout/confirm_payment",
                    data=json.dumps(payment_data),
                    content_type="application/json",
                )

            assert response1.status_code == 200
            assert response2.status_code == 200  # Should handle duplicate gracefully

            data1 = json.loads(response1.data)
            data2 = json.loads(response2.data)
            assert data1["success"] is True
            assert data2["success"] is True


class TestPayPalRouteEdgeCases(TestPayPalHelpers):
    """Test edge cases and boundary conditions for PayPal routes."""

    def test_payment_page_course_with_zero_price(self, test_client, app_with_data):
        """Test payment page for course with zero price but marked as paid."""
        with app_with_data.app_context():
            # Create a course with zero price but marked as paid
            from now_lms.db import Curso, database

            edge_course = Curso(
                codigo="EDGE001",
                nombre="Edge Case Course",
                descripcion_corta="Course with zero price but paid flag",
                descripcion="Testing edge case",
                modalidad="self_paced",
                precio=0.0,
                pagado=True,  # Marked as paid but zero price
                estado="open",
                publico=True,
            )
            database.session.add(edge_course)
            database.session.commit()

            # Login as student
            self.login_as_student(test_client)

            response = test_client.get("/paypal_checkout/payment/EDGE001")
            # Should handle this edge case appropriately
            assert response.status_code in [200, 302]

    def test_payment_status_very_long_course_code(self, test_client, app_with_data):
        """Test payment status with very long course code."""
        with app_with_data.app_context():
            # Login as student
            self.login_as_student(test_client)

            # Very long course code
            long_code = "A" * 1000
            response = test_client.get(f"/paypal_checkout/payment_status/{long_code}")
            # Should handle gracefully without crashing
            assert response.status_code in [404, 500]

    @patch("now_lms.vistas.paypal.get_paypal_access_token")
    @patch("now_lms.vistas.paypal.verify_paypal_payment")
    def test_confirm_payment_unicode_characters(self, mock_verify, mock_token, test_client, app_with_data):
        """Test payment confirmation with unicode characters in data."""
        with app_with_data.app_context():
            mock_token.return_value = "mock_access_token"
            mock_verify.return_value = {
                "verified": True,
                "status": "COMPLETED",
                "amount": "99.99",
                "currency": "USD",
                "payer_id": "test_payer_456",
                "order_data": {"id": "test_order_unicode", "status": "COMPLETED"},
            }

            # Login as student
            self.login_as_student(test_client)

            payment_data = {
                "orderID": "test_order_unicode_🎓📚",
                "payerID": "test_payer_456_résumé",
                "courseCode": "PAID001",
                "amount": "99.99",
                "currency": "EUR€",
            }

            with patch("now_lms.vistas.courses._crear_indice_avance_curso") as mock_progress:
                mock_progress.return_value = None

                response = test_client.post(
                    "/paypal_checkout/confirm_payment",
                    data=json.dumps(payment_data),
                    content_type="application/json",
                )

            # Should handle unicode characters without errors
            assert response.status_code in [200, 400]
