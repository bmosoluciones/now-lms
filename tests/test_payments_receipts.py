# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from now_lms.auth import proteger_passwd
from now_lms.db import Curso, Pago, Usuario, database


def _crear_estudiante(db_session, username="student_receipts", email="student@example.com") -> Usuario:
    user = Usuario(
        usuario=username,
        acceso=proteger_passwd("password"),
        nombre="Student",
        apellido="Receipts",
        correo_electronico=email,
        tipo="student",
        activo=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


def _crear_curso(db_session, code="PAY003", name="Receipt Course") -> Curso:
    curso = Curso(
        codigo=code,
        nombre=name,
        descripcion_corta="Course with receipt",
        descripcion="Course with receipt for testing",
        estado="open",
        pagado=True,
        precio=50.00,
    )
    db_session.add(curso)
    db_session.commit()
    return curso


def test_student_payments_history_renders(app, client, db_session):
    student = _crear_estudiante(db_session)
    curso = _crear_curso(db_session)

    pago = Pago(
        usuario=student.usuario,
        curso=curso.codigo,
        nombre=student.nombre,
        apellido=student.apellido,
        correo_electronico=student.correo_electronico,
        monto=50.00,
        moneda="USD",
        metodo="paypal",
        estado="completed",
        referencia="ORDER-REC-123",
        fecha=datetime.now(),
    )
    db_session.add(pago)
    db_session.commit()

    # Log in as student
    client.post("/user/login", data={"usuario": student.usuario, "acceso": "password"}, follow_redirects=False)

    # Get payments history page
    resp = client.get("/payments")
    assert resp.status_code == 200
    assert b"Mis Pagos Registrados" in resp.data or b"My Registered Payments" in resp.data
    assert b"ORDER-REC-123" in resp.data
    assert b"Receipt Course" in resp.data


def test_download_receipt_pdf(app, client, db_session):
    student = _crear_estudiante(db_session, "student_pdf", "pdf@example.com")
    curso = _crear_curso(db_session, "PAY_PDF", "PDF Course")

    pago = Pago(
        usuario=student.usuario,
        curso=curso.codigo,
        nombre=student.nombre,
        apellido=student.apellido,
        correo_electronico=student.correo_electronico,
        monto=50.00,
        moneda="USD",
        metodo="paypal",
        estado="completed",
        referencia="ORDER-PDF-999",
        fecha=datetime.now(),
    )
    db_session.add(pago)
    db_session.commit()

    # Log in as student
    client.post("/user/login", data={"usuario": student.usuario, "acceso": "password"}, follow_redirects=False)

    # Download PDF receipt
    resp = client.get(f"/payments/receipt/{pago.id}")
    assert resp.status_code == 200
    assert resp.headers["Content-Type"] == "application/pdf"
    assert b"%PDF" in resp.data


def test_download_receipt_pdf_unauthorized_or_not_found(app, client, db_session):
    student1 = _crear_estudiante(db_session, "student_owner", "owner@example.com")
    student2 = _crear_estudiante(db_session, "student_other", "other@example.com")
    curso = _crear_curso(db_session, "PAY_UNAUTH", "Unauth Course")

    pago = Pago(
        usuario=student1.usuario,
        curso=curso.codigo,
        nombre=student1.nombre,
        apellido=student1.apellido,
        correo_electronico=student1.correo_electronico,
        monto=50.00,
        moneda="USD",
        metodo="paypal",
        estado="completed",
        referencia="ORDER-OWNER",
        fecha=datetime.now(),
    )
    db_session.add(pago)
    db_session.commit()

    # Log in as other student (not the owner)
    client.post("/user/login", data={"usuario": student2.usuario, "acceso": "password"}, follow_redirects=False)

    # Attempt to download other student's receipt
    resp = client.get(f"/payments/receipt/{pago.id}")
    assert resp.status_code == 404


@patch("now_lms.mail.send_mail")
@patch("now_lms.mail._config")
def test_email_receipt_sending(mock_config, mock_send_mail, app, db_session):
    # Set up mock configuration to simulate SMTP enabled
    mock_config.return_value = MagicMock(
        mail_configured=True,
        MAIL_DEFAULT_SENDER_NAME="NOW LMS",
        MAIL_DEFAULT_SENDER="no-reply@nowlms.com"
    )

    from now_lms.vistas.paypal import enviar_recibo_pago

    student = _crear_estudiante(db_session, "student_email", "email_test@example.com")
    curso = _crear_curso(db_session, "PAY_EMAIL", "Email Course")

    pago = Pago(
        usuario=student.usuario,
        curso=curso.codigo,
        nombre=student.nombre,
        apellido=student.apellido,
        correo_electronico=student.correo_electronico,
        monto=50.00,
        moneda="USD",
        metodo="paypal",
        estado="completed",
        referencia="ORDER-EMAIL-888",
        fecha=datetime.now(),
    )
    db_session.add(pago)
    db_session.commit()

    with app.test_request_context():
        # Call the email helper
        enviar_recibo_pago(pago)

        # Verify send_mail was called
        assert mock_send_mail.called
        sent_msg = mock_send_mail.call_args[0][0]
        assert "Recibo de Pago" in sent_msg.subject or "Receipt" in sent_msg.subject
        assert "email_test@example.com" in sent_msg.recipients
        assert "ORDER-EMAIL-888" in sent_msg.html
        assert "Email Course" in sent_msg.html
