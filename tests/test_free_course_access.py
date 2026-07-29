# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.

"""Access checks for enrollments that carry no payment record.

``verifica_estudiante_asignado_a_curso`` is what ``permitir_estudiante`` and the
resource routes gate on. Admin-created and bulk/scripted enrollments produce an
``EstudianteCurso`` row with ``pago=None``; on a free course those students must
still get access. Paid courses must keep requiring a completed or audit payment.
"""

from now_lms.db import Curso, EstudianteCurso, Pago, Usuario, database
from now_lms.db.tools import verifica_estudiante_asignado_a_curso


def _course(code, *, pagado):
    return Curso(
        nombre=f"Course {code}",
        codigo=code,
        descripcion="Course used by the free-course access tests.",
        descripcion_corta="Access test course.",
        estado="open",
        publico=False,
        pagado=pagado,
        precio=100 if pagado else 0,
        auditable=False,
        certificado=False,
        modalidad="self_paced",
        creado_por="test",
    )


def _student(username):
    return Usuario(
        usuario=username,
        acceso=b"x",
        nombre="Access",
        apellido="Test",
        correo_electronico=f"{username}@example.test",
        tipo="student",
        activo=True,
        correo_electronico_verificado=True,
        creado_por="test",
    )


def _enroll(course_code, username, pago_id=None):
    return EstudianteCurso(curso=course_code, usuario=username, vigente=True, pago=pago_id, creado_por="test")


def test_free_course_enrollment_without_payment_grants_access(app):
    """The regression: pago=None on a free course must NOT lock the student out."""
    with app.app_context():
        s = database.session
        s.add(_course("FREENP", pagado=False))
        s.add(_student("free-nopago"))
        s.flush()
        s.add(_enroll("FREENP", "free-nopago", pago_id=None))
        s.commit()

        with app.test_request_context():
            from flask_login import login_user

            login_user(s.execute(database.select(Usuario).filter_by(usuario="free-nopago")).scalars().one())
            assert verifica_estudiante_asignado_a_curso("FREENP") is True


def test_paid_course_enrollment_without_payment_denies_access(app):
    """The boundary: a paid course still requires a payment record."""
    with app.app_context():
        s = database.session
        s.add(_course("PAIDNP", pagado=True))
        s.add(_student("paid-nopago"))
        s.flush()
        s.add(_enroll("PAIDNP", "paid-nopago", pago_id=None))
        s.commit()

        with app.test_request_context():
            from flask_login import login_user

            login_user(s.execute(database.select(Usuario).filter_by(usuario="paid-nopago")).scalars().one())
            assert verifica_estudiante_asignado_a_curso("PAIDNP") is False


def test_paid_course_with_completed_payment_grants_access(app):
    """Unchanged behaviour: completed payment on a paid course still works."""
    with app.app_context():
        s = database.session
        s.add(_course("PAIDOK", pagado=True))
        s.add(_student("paid-ok"))
        s.flush()
        pago = Pago(
            usuario="paid-ok",
            curso="PAIDOK",
            nombre="Access",
            apellido="Test",
            correo_electronico="paid-ok@example.test",
            monto=100,
            estado="completed",
            audit=False,
            creado_por="test",
        )
        s.add(pago)
        s.flush()
        s.add(_enroll("PAIDOK", "paid-ok", pago_id=pago.id))
        s.commit()

        with app.test_request_context():
            from flask_login import login_user

            login_user(s.execute(database.select(Usuario).filter_by(usuario="paid-ok")).scalars().one())
            assert verifica_estudiante_asignado_a_curso("PAIDOK") is True


def test_not_enrolled_denies_access(app):
    """Unchanged behaviour: no enrollment row means no access, free course or not."""
    with app.app_context():
        s = database.session
        s.add(_course("FREENE", pagado=False))
        s.add(_student("not-enrolled"))
        s.commit()

        with app.test_request_context():
            from flask_login import login_user

            login_user(s.execute(database.select(Usuario).filter_by(usuario="not-enrolled")).scalars().one())
            assert verifica_estudiante_asignado_a_curso("FREENE") is False
