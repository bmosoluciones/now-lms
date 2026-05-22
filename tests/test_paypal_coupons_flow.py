# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""
Tests for PayPal payment flow with coupons.
"""

from unittest.mock import MagicMock, patch
import pytest
from now_lms.auth import proteger_passwd, proteger_secreto
from now_lms.db import Curso, Pago, PaypalConfig, Usuario, Coupon, database


def _crear_admin(db_session) -> Usuario:
    user = Usuario(
        usuario="admin_coupon",
        acceso=proteger_passwd("password"),
        nombre="Admin",
        apellido="Coupon",
        correo_electronico="admin_coupon@example.com",
        tipo="admin",
        activo=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


def _crear_estudiante(db_session) -> Usuario:
    user = Usuario(
        usuario="student_coupon",
        acceso=proteger_passwd("password"),
        nombre="Coupon",
        apellido="Tester",
        correo_electronico="coupon@example.com",
        tipo="student",
        activo=True,
    )
    db_session.add(user)
    db_session.commit()
    return user

def _crear_curso_pagado(db_session) -> Curso:
    curso = Curso(
        codigo="COUPON_COURSE",
        nombre="Coupon Course",
        descripcion_corta="A short description",
        descripcion="A long description",
        pagado=True,
        precio=100.0,
        estado="open",
    )
    db_session.add(curso)
    db_session.commit()
    return curso

def _crear_cupon(db_session, curso_codigo, admin_user) -> Coupon:
    coupon = Coupon(
        course_id=curso_codigo,
        code="SAVE50",
        discount_type="percentage",
        discount_value=50.0,
        created_by=admin_user,
    )
    db_session.add(coupon)
    db_session.commit()
    return coupon

def _configurar_paypal(db_session):
    paypal_config = db_session.execute(database.select(PaypalConfig)).scalars().first()
    if not paypal_config:
        paypal_config = PaypalConfig()
        db_session.add(paypal_config)
    paypal_config.enable = True
    paypal_config.sandbox = True
    paypal_config.paypal_sandbox = "test_client_id"
    paypal_config.paypal_sandbox_secret = proteger_secreto("test_secret")
    db_session.commit()
    return paypal_config

def _login(client, username, password):
    return client.post("/user/login", data={"usuario": username, "acceso": password}, follow_redirects=True)

class TestPayPalCouponFlow:
    def test_course_enroll_has_page_title(self, app, client, db_session):
        student = _crear_estudiante(db_session)
        curso = _crear_curso_pagado(db_session)

        _login(client, student.usuario, "password")

        resp = client.get(f"/course/{curso.codigo}/enroll")

        assert resp.status_code == 200
        assert f"<title>Inscripción - {curso.nombre}</title>".encode() in resp.data

    def test_create_coupon_allows_blank_optional_limits(self, app, client, db_session):
        admin = _crear_admin(db_session)
        curso = _crear_curso_pagado(db_session)

        _login(client, admin.usuario, "password")

        resp = client.post(
            f"/course/{curso.codigo}/coupons/new",
            data={
                "code": "TEST1",
                "discount_type": "fixed",
                "discount_value": "4",
                "max_uses": "",
                "expires_at": "",
            },
            follow_redirects=False,
        )

        assert resp.status_code == 302
        assert f"/course/{curso.codigo}/coupons/" in resp.location

        coupon = (
            db_session.execute(database.select(Coupon).filter_by(course_id=curso.codigo, code="TEST1"))
            .scalars()
            .first()
        )
        assert coupon is not None
        assert coupon.max_uses is None
        assert coupon.expires_at is None

    @patch("now_lms.vistas.paypal.render_template")
    @patch("now_lms.vistas.paypal.verify_paypal_payment")
    @patch("now_lms.vistas.paypal.get_paypal_access_token")
    def test_full_coupon_payment_flow(self, mock_get_token, mock_verify, mock_render, app, client, db_session):
        # 1. Setup
        student = _crear_estudiante(db_session)
        curso = _crear_curso_pagado(db_session)
        _crear_cupon(db_session, curso.codigo, student.usuario)
        _configurar_paypal(db_session)

        _login(client, student.usuario, "password")

        # 2. Enroll with coupon
        enroll_data = {
            "nombre": student.nombre,
            "apellido": student.apellido,
            "correo_electronico": student.correo_electronico,
            "direccion1": "Street 1",
            "pais": "Costa Rica",
            "provincia": "San Jose",
            "codigo_postal": "10101",
            "modo": "paid"
        }
        # First "GET" to have the coupon in the session/URL if needed,
        # but the view handles it from request.args or request.form
        resp = client.post(f"/course/{curso.codigo}/enroll?coupon_code=SAVE50", data=enroll_data, follow_redirects=False)

        # Should redirect to payment page
        assert resp.status_code == 302
        assert "/paypal_checkout/payment/COUPON_COURSE" in resp.location

        # Verify a pending payment was created with discounted price
        pago = db_session.execute(database.select(Pago).filter_by(usuario=student.usuario, curso=curso.codigo, estado="pending")).scalars().first()
        assert pago is not None
        assert float(pago.monto) == 50.0
        assert "Cupón aplicado: SAVE50" in pago.descripcion

        # 3. Access payment page
        mock_render.return_value = "<html>50.00 data-amount=\"50.0\"</html>"
        resp = client.get(f"/paypal_checkout/payment/{curso.codigo}?payment_id={pago.id}")
        assert resp.status_code == 200
        assert b"50.00" in resp.data
        assert b"data-amount=\"50.0\"" in resp.data

        # Verify render_template was called with correct pago object
        args, kwargs = mock_render.call_args
        assert kwargs["pago"].id == pago.id
        assert float(kwargs["pago"].monto) == 50.0

        # 4. Confirm payment
        mock_get_token.return_value = "test_token"
        mock_verify.return_value = {
            "verified": True,
            "status": "COMPLETED",
            "amount": "50.00",
            "currency": "USD",
            "payer_id": "payer_123",
        }

        confirm_data = {
            "orderID": "order_123",
            "payerID": "payer_123",
            "courseCode": curso.codigo,
            "amount": "50.00"
        }

        resp = client.post("/paypal_checkout/confirm_payment", json=confirm_data)
        assert resp.status_code == 200

        # Verify the same Pago record was updated
        db_session.expire_all()
        pago_final = db_session.execute(database.select(Pago).filter_by(id=pago.id)).scalars().first()
        assert pago_final.estado == "completed"
        assert pago_final.referencia == "order_123"
        assert "Cupón aplicado: SAVE50" in pago_final.descripcion

        # Verify another payment was NOT created
        all_payments = db_session.execute(database.select(Pago).filter_by(usuario=student.usuario, curso=curso.codigo)).scalars().all()
        assert len(all_payments) == 1
