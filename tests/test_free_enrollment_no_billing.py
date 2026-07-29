# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.

"""A free enrollment must not demand a billing address.

``PagoForm`` gates the address fields on ``requires_billing``, which
``course_enroll`` sets from whether the enrollment actually costs anything.
Free courses therefore enroll with name + email alone; paid courses keep
requiring a full address.
"""

from now_lms.auth import proteger_passwd
from now_lms.db import Curso, EstudianteCurso, Usuario, database
from now_lms.forms import PagoForm

PASSWORD = "billing-test-pw"


def _course(app, code, *, pagado):
    with app.app_context():
        s = database.session
        s.add(
            Curso(
                nombre=f"Course {code}",
                codigo=code,
                descripcion="Billing-requirement test course.",
                descripcion_corta="Billing test.",
                estado="open",
                publico=True,
                pagado=pagado,
                precio=100 if pagado else 0,
                auditable=False,
                certificado=False,
                modalidad="self_paced",
                creado_por="test",
            )
        )
        s.commit()


def _student(app, username):
    with app.app_context():
        s = database.session
        s.add(
            Usuario(
                usuario=username,
                acceso=proteger_passwd(PASSWORD),
                nombre="Billing",
                apellido="Test",
                correo_electronico=f"{username}@example.test",
                tipo="student",
                activo=True,
                correo_electronico_verificado=True,
                creado_por="test",
            )
        )
        s.commit()


def _login(client, username):
    return client.post("/user/login", data={"usuario": username, "acceso": PASSWORD}, follow_redirects=False)


def test_free_course_form_does_not_require_billing(app):
    """The form itself validates with no address when billing is not required."""
    with app.test_request_context(
        "/course/X/enroll",
        method="POST",
        data={"nombre": "A", "apellido": "B", "correo_electronico": "a@b.test"},
    ):
        form = PagoForm()
        form.requires_billing = False
        assert form.validate() is True, form.errors


def test_paid_course_form_still_requires_billing(app):
    """The boundary: with billing required, a missing address fails validation."""
    with app.test_request_context(
        "/course/X/enroll",
        method="POST",
        data={"nombre": "A", "apellido": "B", "correo_electronico": "a@b.test"},
    ):
        form = PagoForm()
        form.requires_billing = True
        assert form.validate() is False
        for field in ("direccion1", "pais", "provincia", "codigo_postal"):
            assert form.errors.get(field), f"{field} should be flagged as required"


def test_paid_course_form_accepts_a_full_address(app):
    """Unchanged behaviour: a complete address validates on a paid course."""
    with app.test_request_context(
        "/course/X/enroll",
        method="POST",
        data={
            "nombre": "A",
            "apellido": "B",
            "correo_electronico": "a@b.test",
            "direccion1": "1 Main St",
            "pais": "Nicaragua",
            "provincia": "Managua",
            "codigo_postal": "10001",
        },
    ):
        form = PagoForm()
        form.requires_billing = True
        assert form.validate() is True, form.errors


def test_free_enrollment_page_hides_the_address_fields(app, client):
    """The rendered free-course page must not ask for an address at all."""
    _course(app, "FREEBIL", pagado=False)
    _student(app, "free-billing@example.test")
    _login(client, "free-billing@example.test")

    body = client.get("/course/FREEBIL/enroll").get_data(as_text=True)
    assert 'id="nombre"' in body
    assert 'id="dirrecion1"' not in body
    assert 'id="pais"' not in body
    assert 'id="codigo_postal"' not in body


def test_free_enrollment_succeeds_without_an_address(app, client):
    """End to end: posting name + email alone enrolls the student."""
    _course(app, "FREEPOST", pagado=False)
    _student(app, "free-post@example.test")
    _login(client, "free-post@example.test")

    client.post(
        "/course/FREEPOST/enroll",
        data={"nombre": "Billing", "apellido": "Test", "correo_electronico": "free-post@example.test"},
        follow_redirects=False,
    )

    with app.app_context():
        enrollment = (
            database.session.execute(
                database.select(EstudianteCurso).filter_by(curso="FREEPOST", usuario="free-post@example.test")
            )
            .scalars()
            .first()
        )
        assert enrollment is not None, "free enrollment should have been created without a billing address"
