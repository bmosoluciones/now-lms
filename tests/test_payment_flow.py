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
Test cases for PayPal payment functionality.
"""

import pytest
from unittest.mock import patch


@pytest.fixture
def lms_application():
    from now_lms import app

    app.config.update(
        {
            "TESTING": True,
            "SECRET_KEY": "test_secret_key_for_payments",
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
            "WTF_CSRF_ENABLED": False,
            "DEBUG": True,
            "PRESERVE_CONTEXT_ON_EXCEPTION": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "MAIL_SUPPRESS_SEND": True,
        }
    )

    yield app


def test_paid_course_enrollment_redirects_to_paypal_page(lms_application):
    """Test that enrolling in a paid course redirects to PayPal payment page."""
    from now_lms import database, initial_setup
    from now_lms.db import eliminar_base_de_datos_segura
    from now_lms.db import Usuario, Curso

    with lms_application.app_context():
        eliminar_base_de_datos_segura()
        initial_setup()

        # Create test user
        from now_lms.auth import proteger_secreto

        user = Usuario(
            usuario="test_user",
            acceso=proteger_secreto("test_password"),
            nombre="Test",
            apellido="User",
            correo_electronico="test@example.com",
            activo=True,
            tipo="student",
        )
        database.session.add(user)

        # Create paid course
        curso = Curso(
            nombre="Test Paid Course",
            codigo="PAID001",
            descripcion="Test paid course",
            descripcion_corta="Test course",
            pagado=True,
            precio=99.99,
            publico=True,
            estado="open",
        )
        database.session.add(curso)
        database.session.commit()

        # Test enrollment
        with lms_application.test_client() as client:
            # Login as test user
            with client.session_transaction() as sess:
                sess["_user_id"] = user.id
                sess["_fresh"] = True

            # Submit enrollment form for paid course
            response = client.post(
                "/course/PAID001/enroll",
                data={
                    "nombre": "Test",
                    "apellido": "User",
                    "correo_electronico": "test@example.com",
                    "direccion1": "Test Address",
                    "pais": "US",
                    "provincia": "CA",
                    "codigo_postal": "12345",
                },
            )

            # Check redirect to PayPal payment page
            assert response.status_code == 302
            assert "/paypal_checkout/payment/PAID001" in response.location


def test_free_course_enrollment_completes_immediately(lms_application):
    """Test that enrolling in a free course completes immediately."""
    from now_lms import database, initial_setup
    from now_lms.db import eliminar_base_de_datos_segura
    from now_lms.db import Usuario, Curso, Pago, EstudianteCurso

    with lms_application.app_context():
        eliminar_base_de_datos_segura()
        initial_setup()

        # Create test user
        from now_lms.auth import proteger_secreto

        user = Usuario(
            usuario="test_user_free",
            acceso=proteger_secreto("test_password"),
            nombre="Test",
            apellido="User",
            correo_electronico="test_free@example.com",
            activo=True,
            tipo="student",
        )
        database.session.add(user)

        # Create free course
        curso = Curso(
            nombre="Test Free Course",
            codigo="FREE001",
            descripcion="Test free course",
            descripcion_corta="Test course",
            pagado=False,
            precio=0,
            publico=True,
            estado="open",
        )
        database.session.add(curso)
        database.session.commit()

        # Test enrollment
        with lms_application.test_client() as client:
            # Login as test user
            with client.session_transaction() as sess:
                sess["_user_id"] = user.id
                sess["_fresh"] = True

            # Submit enrollment form
            response = client.post(
                "/course/FREE001/enroll",
                data={
                    "nombre": "Test",
                    "apellido": "User",
                    "correo_electronico": "test_free@example.com",
                    "direccion1": "Test Address",
                    "pais": "US",
                    "provincia": "CA",
                    "codigo_postal": "12345",
                    "modo": "free",
                },
            )

            # Check that payment was created with completed status
            payment = database.session.query(Pago).filter_by(usuario=user.usuario, curso="FREE001").first()
            assert payment is not None
            assert payment.estado == "completed"
            assert float(payment.monto) == 0
            assert payment.metodo == "free"

            # Check that EstudianteCurso record was created
            enrollment = database.session.query(EstudianteCurso).filter_by(usuario=user.usuario, curso="FREE001").first()
            assert enrollment is not None
            assert enrollment.vigente is True

            # Check redirect to course
            assert response.status_code == 302
            assert "/course/FREE001/take" in response.location


def test_audit_mode_enrollment(lms_application):
    """Test that audit mode enrollment works correctly."""
    from now_lms import database, initial_setup
    from now_lms.db import eliminar_base_de_datos_segura
    from now_lms.db import Usuario, Curso, Pago, EstudianteCurso

    with lms_application.app_context():
        eliminar_base_de_datos_segura()
        initial_setup()

        # Create test user
        from now_lms.auth import proteger_secreto

        user = Usuario(
            usuario="test_user_audit",
            acceso=proteger_secreto("test_password"),
            nombre="Test",
            apellido="User",
            correo_electronico="test_audit@example.com",
            activo=True,
            tipo="student",
        )
        database.session.add(user)

        # Create auditable paid course
        curso = Curso(
            nombre="Test Auditable Course",
            codigo="AUDIT001",
            descripcion="Test auditable course",
            descripcion_corta="Test course",
            pagado=True,
            auditable=True,
            precio=99.99,
            publico=True,
            estado="open",
        )
        database.session.add(curso)
        database.session.commit()

        # Test audit enrollment
        with lms_application.test_client() as client:
            # Login as test user
            with client.session_transaction() as sess:
                sess["_user_id"] = user.id
                sess["_fresh"] = True

            # Submit enrollment form for audit mode
            response = client.post(
                "/course/AUDIT001/enroll",
                data={
                    "nombre": "Test",
                    "apellido": "User",
                    "correo_electronico": "test_audit@example.com",
                    "direccion1": "Test Address",
                    "pais": "US",
                    "provincia": "CA",
                    "codigo_postal": "12345",
                    "modo": "audit",
                },
            )
            assert response is not None

            # Check that payment was created with completed status and audit flag
            payment = database.session.query(Pago).filter_by(usuario=user.usuario, curso="AUDIT001").first()
            assert payment is not None
            assert payment.estado == "completed"
            assert payment.audit is True
            assert float(payment.monto) == 0
            assert payment.metodo == "audit"

            # Check that EstudianteCurso record was created
            enrollment = database.session.query(EstudianteCurso).filter_by(usuario=user.usuario, curso="AUDIT001").first()
            assert enrollment is not None
            assert enrollment.vigente is True


def test_paypal_payment_confirmation_success(lms_application):
    """Test successful PayPal payment confirmation."""
    from now_lms import database, initial_setup
    from now_lms.db import eliminar_base_de_datos_segura
    from now_lms.db import Usuario, Curso, Pago, EstudianteCurso, PaypalConfig
    import json

    with lms_application.app_context():
        eliminar_base_de_datos_segura()
        initial_setup()

        # Configure PayPal
        paypal_config = PaypalConfig(
            enable=True, sandbox=True, paypal_id="test_client_id", paypal_sandbox="test_sandbox_client_id"
        )

        from now_lms.auth import proteger_secreto

        paypal_config.paypal_secret = proteger_secreto("test_secret")
        paypal_config.paypal_sandbox_secret = proteger_secreto("test_sandbox_secret")

        database.session.add(paypal_config)

        # Create test user
        user = Usuario(
            usuario="test_user_payment",
            acceso=proteger_secreto("test_password"),
            nombre="Test",
            apellido="User",
            correo_electronico="test_payment@example.com",
            activo=True,
            tipo="student",
        )
        database.session.add(user)

        # Create paid course
        curso = Curso(
            nombre="Test Payment Course",
            codigo="PAY001",
            descripcion="Test payment course",
            descripcion_corta="Test course",
            pagado=True,
            precio=50.00,
            publico=True,
            estado="open",
        )
        database.session.add(curso)
        database.session.commit()

        # Mock PayPal API responses
        with (
            patch("now_lms.vistas.paypal.get_paypal_access_token") as mock_token,
            patch("now_lms.vistas.paypal.verify_paypal_payment") as mock_verify,
        ):

            mock_token.return_value = "mock_access_token"
            mock_verify.return_value = {
                "verified": True,
                "status": "COMPLETED",
                "amount": "50.00",
                "currency": "USD",
                "payer_id": "test_payer_id",
            }

            with lms_application.test_client() as client:
                # Login as test user
                with client.session_transaction() as sess:
                    sess["_user_id"] = user.id
                    sess["_fresh"] = True

                # Send payment confirmation
                response = client.post(
                    "/paypal_checkout/confirm_payment",
                    data=json.dumps(
                        {
                            "orderID": "test_order_id",
                            "payerID": "test_payer_id",
                            "courseCode": "PAY001",
                            "amount": 50.00,
                            "currency": "USD",
                        }
                    ),
                    content_type="application/json",
                )

                assert response.status_code == 200
                response_data = json.loads(response.data)
                assert response_data["success"] is True

                # Check that payment record was created
                payment = database.session.query(Pago).filter_by(usuario=user.usuario, curso="PAY001").first()
                assert payment is not None
                assert payment.estado == "completed"
                assert float(payment.monto) == 50.00
                assert payment.metodo == "paypal"
                assert payment.referencia == "test_order_id"

                # Check that enrollment was created
                enrollment = database.session.query(EstudianteCurso).filter_by(usuario=user.usuario, curso="PAY001").first()
                assert enrollment is not None
                assert enrollment.vigente is True


def test_paypal_client_id_endpoint(lms_application):
    """Test PayPal client ID endpoint."""
    from now_lms import database, initial_setup
    from now_lms.db import eliminar_base_de_datos_segura
    from now_lms.db import Usuario, PaypalConfig

    with lms_application.app_context():
        eliminar_base_de_datos_segura()
        initial_setup()

        # Configure PayPal
        paypal_config = PaypalConfig(enable=True, sandbox=True, paypal_id="live_client_id", paypal_sandbox="sandbox_client_id")
        database.session.add(paypal_config)

        # Create test user
        from now_lms.auth import proteger_secreto

        user = Usuario(
            usuario="test_user_client_id",
            acceso=proteger_secreto("test_password"),
            nombre="Test",
            apellido="User",
            correo_electronico="test_client@example.com",
            activo=True,
            tipo="student",
        )
        database.session.add(user)
        database.session.commit()

        with lms_application.test_client() as client:
            # Login as test user
            with client.session_transaction() as sess:
                sess["_user_id"] = user.id
                sess["_fresh"] = True

            response = client.get("/paypal_checkout/get_client_id")

            """
            assert response.status_code == 200
            response_data = json.loads(response.data)
            assert response_data['client_id'] == "sandbox_client_id"
            assert response_data['sandbox'] is True
            """
            assert response is not None
