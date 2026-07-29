# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.

"""Enrolling twice should leave you with one enrollment, not two.

The paid path already gets this right — ``paypal.py::_save_payment_enrollment``
reuses the existing ``EstudianteCurso`` row. The free and audit paths did not,
so submitting the enrollment form again just added another row for the same
(usuario, curso) and quietly inflated every enrollment count that reads it.

The one case that must keep working is upgrading: a student holding an audit
enrollment is still allowed to pay.
"""

from now_lms.auth import proteger_passwd
from now_lms.db import Curso, EstudianteCurso, Pago, Usuario, database

PASSWORD = "dup-guard-pw-123"


def _make_course(app, code, *, pagado, auditable=False):
    with app.app_context():
        database.session.add(
            Curso(
                nombre=f"Course {code}",
                codigo=code,
                descripcion="Duplicate-enrollment guard test course.",
                descripcion_corta="Dup guard.",
                estado="open",
                publico=True,
                pagado=pagado,
                precio=100 if pagado else 0,
                auditable=auditable,
                certificado=False,
                modalidad="self_paced",
                creado_por="test",
            )
        )
        database.session.commit()


def _make_student(app, username):
    with app.app_context():
        database.session.add(
            Usuario(
                usuario=username,
                acceso=proteger_passwd(PASSWORD),
                nombre="Dup",
                apellido="Guard",
                correo_electronico=username,
                tipo="student",
                activo=True,
                correo_electronico_verificado=True,
                creado_por="test",
            )
        )
        database.session.commit()


def _login(client, username):
    client.post("/user/login", data={"usuario": username, "acceso": PASSWORD})


def _enrollment_rows(app, code, username):
    with app.app_context():
        return (
            database.session.execute(database.select(EstudianteCurso).filter_by(curso=code, usuario=username))
            .scalars()
            .all()
        )


def _pago_rows(app, code, username):
    with app.app_context():
        return database.session.execute(database.select(Pago).filter_by(curso=code, usuario=username)).scalars().all()


def _enroll(client, code, username, **extra):
    """Submit the enrollment form.

    The address fields are filled in because PagoForm currently requires them on
    every course, free ones included. That is its own discussion; this test just
    plays along so it can focus on the duplicate-row question.
    """
    data = {
        "nombre": "Dup",
        "apellido": "Guard",
        "correo_electronico": username,
        "direccion1": "1 Main St",
        "direccion2": "",
        "pais": "Nicaragua",
        "provincia": "Managua",
        "codigo_postal": "10001",
    }
    data.update(extra)
    return client.post(f"/course/{code}/enroll", data=data, follow_redirects=False)


def test_first_free_enrollment_creates_one_row(app, client):
    user = "dup-first@example.test"
    _make_course(app, "DUPONE", pagado=False)
    _make_student(app, user)
    _login(client, user)

    _enroll(client, "DUPONE", user)
    assert len(_enrollment_rows(app, "DUPONE", user)) == 1


def test_second_free_enrollment_does_not_add_a_row(app, client):
    """The regression itself: submit three times, end up with one enrollment."""
    user = "dup-second@example.test"
    _make_course(app, "DUPTWO", pagado=False)
    _make_student(app, user)
    _login(client, user)

    for _ in range(3):
        _enroll(client, "DUPTWO", user)

    rows = _enrollment_rows(app, "DUPTWO", user)
    assert len(rows) == 1, f"expected 1 enrollment after 3 submissions, found {len(rows)}"


def test_second_free_enrollment_does_not_add_a_payment_row(app, client):
    """Turning away a repeat enrollment should not leave a stray Pago behind."""
    user = "dup-pago@example.test"
    _make_course(app, "DUPPAGO", pagado=False)
    _make_student(app, user)
    _login(client, user)

    _enroll(client, "DUPPAGO", user)
    first = len(_pago_rows(app, "DUPPAGO", user))
    _enroll(client, "DUPPAGO", user)
    second = len(_pago_rows(app, "DUPPAGO", user))

    assert second == first, f"re-enrollment created another Pago row ({first} -> {second})"


def test_already_enrolled_student_is_sent_to_the_course(app, client):
    user = "dup-redirect@example.test"
    _make_course(app, "DUPREDIR", pagado=False)
    _make_student(app, user)
    _login(client, user)

    _enroll(client, "DUPREDIR", user)
    response = _enroll(client, "DUPREDIR", user)

    assert response.status_code == 302
    assert "/course/DUPREDIR/take" in response.headers["Location"]


def test_audit_enrollment_may_still_upgrade_to_paid(app, client):
    """The case worth protecting: auditing a course must not block paying for it."""
    user = "dup-upgrade@example.test"
    _make_course(app, "DUPUP", pagado=True, auditable=True)
    _make_student(app, user)
    _login(client, user)

    # Audit first: free, and it creates the enrollment row.
    _enroll(client, "DUPUP", user, modo="audit")
    assert len(_enrollment_rows(app, "DUPUP", user)) == 1

    # Now pay for it. This must reach the payment flow, not get waved off.
    response = _enroll(client, "DUPUP", user)
    assert response.status_code == 302
    assert "/take" not in response.headers["Location"], (
        "the paid upgrade was refused as a duplicate; it must reach the payment flow"
    )
    assert len(_enrollment_rows(app, "DUPUP", user)) == 1
