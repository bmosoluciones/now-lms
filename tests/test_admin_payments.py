# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.

from datetime import datetime, timedelta

from now_lms.auth import proteger_passwd
from now_lms.db import Curso, Pago, Usuario, database


def _crear_admin(db_session) -> Usuario:
    user = Usuario(
        usuario="admin_payments",
        acceso=proteger_passwd("password"),
        nombre="Admin",
        apellido="Payments",
        correo_electronico="admin_payments@example.com",
        tipo="admin",
        activo=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


def _crear_estudiante(db_session) -> Usuario:
    user = Usuario(
        usuario="student_payments",
        acceso=proteger_passwd("password"),
        nombre="Student",
        apellido="Payments",
        correo_electronico="student_payments@example.com",
        tipo="student",
        activo=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


def _crear_curso(db_session, code: str = "PAY001", name: str = "Paid Course") -> Curso:
    curso = Curso(
        codigo=code,
        nombre=name,
        descripcion_corta="Paid course",
        descripcion="Paid course for payment admin tests",
        estado="open",
        pagado=True,
        precio=1.00,
    )
    db_session.add(curso)
    db_session.commit()
    return curso


def test_admin_payments_renders_payment_rows(app, client, db_session):
    admin = _crear_admin(db_session)
    student = _crear_estudiante(db_session)
    curso = _crear_curso(db_session)
    pago = Pago(
        usuario=student.usuario,
        curso=curso.codigo,
        nombre=student.nombre,
        apellido=student.apellido,
        correo_electronico=student.correo_electronico,
        monto=1.00,
        moneda="USD",
        metodo="paypal",
        estado="completed",
        referencia="ORDER-123",
    )
    db_session.add(pago)
    db_session.commit()

    client.post("/user/login", data={"usuario": admin.usuario, "acceso": "password"}, follow_redirects=False)

    resp = client.get("/admin/payments")

    assert resp.status_code == 200
    assert b"Student Payments" in resp.data
    assert b"Paid Course" in resp.data
    assert b"ORDER-123" in resp.data


def test_admin_panel_renders_paypal_kpi(app, client, db_session):
    admin = _crear_admin(db_session)

    client.post("/user/login", data={"usuario": admin.usuario, "acceso": "password"}, follow_redirects=False)

    resp = client.get("/admin/panel")

    assert resp.status_code == 200
    assert b"Pagos PayPal" in resp.data


def test_admin_payments_filters_by_course_and_date_range(app, client, db_session):
    admin = _crear_admin(db_session)
    student = _crear_estudiante(db_session)
    first_course = _crear_curso(db_session, "PAY001", "Filtered Course")
    second_course = _crear_curso(db_session, "PAY002", "Other Course")
    now = datetime.now()

    db_session.add_all(
        [
            Pago(
                usuario=student.usuario,
                curso=first_course.codigo,
                nombre=student.nombre,
                apellido=student.apellido,
                correo_electronico=student.correo_electronico,
                monto=1.00,
                moneda="USD",
                metodo="paypal",
                estado="completed",
                referencia="VISIBLE-ORDER",
                fecha=now,
            ),
            Pago(
                usuario=student.usuario,
                curso=second_course.codigo,
                nombre=student.nombre,
                apellido=student.apellido,
                correo_electronico=student.correo_electronico,
                monto=2.00,
                moneda="USD",
                metodo="paypal",
                estado="completed",
                referencia="OTHER-COURSE",
                fecha=now,
            ),
            Pago(
                usuario=student.usuario,
                curso=first_course.codigo,
                nombre=student.nombre,
                apellido=student.apellido,
                correo_electronico=student.correo_electronico,
                monto=3.00,
                moneda="USD",
                metodo="paypal",
                estado="completed",
                referencia="OLD-ORDER",
                fecha=now - timedelta(days=10),
            ),
        ]
    )
    db_session.commit()

    client.post("/user/login", data={"usuario": admin.usuario, "acceso": "password"}, follow_redirects=False)

    resp = client.get(
        "/admin/payments",
        query_string={
            "course_code": first_course.codigo,
            "start_date": now.date().isoformat(),
            "end_date": now.date().isoformat(),
        },
    )

    assert resp.status_code == 200
    assert b"VISIBLE-ORDER" in resp.data
    assert b"OTHER-COURSE" not in resp.data
    assert b"OLD-ORDER" not in resp.data
