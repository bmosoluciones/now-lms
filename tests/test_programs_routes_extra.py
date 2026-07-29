# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""
Extra comprehensive unit and integration tests for program routes (now_lms/vistas/programs.py).
"""

import os
from io import BytesIO
from datetime import datetime
import pytest
from unittest.mock import MagicMock, patch
from flask import url_for
from werkzeug.datastructures import FileStorage
from sqlalchemy.exc import OperationalError
from flask_uploads import UploadNotAllowed

from now_lms.auth import proteger_passwd
from now_lms.db import (
    database,
    Usuario,
    Curso,
    Programa,
    ProgramaCurso,
    ProgramaEstudiante,
    Categoria,
    Etiqueta,
    Pago,
    CertificacionPrograma,
    Certificado,
    Certificacion,
    PaypalConfig,
)
from now_lms.cache import cache


@pytest.fixture
def extra_prog_setup(app, db_session):
    """Sets up a complete set of records for extra program routing tests."""
    admin = Usuario(
        usuario="admin_prog_ex",
        acceso=proteger_passwd("pass"),
        nombre="Admin",
        correo_electronico="admin_p_ex@example.com",
        tipo="admin",
        activo=True,
    )
    instructor = Usuario(
        usuario="inst_prog_ex",
        acceso=proteger_passwd("pass"),
        nombre="Instructor",
        correo_electronico="inst_p_ex@example.com",
        tipo="instructor",
        activo=True,
    )
    student = Usuario(
        usuario="stud_p_ex",
        acceso=proteger_passwd("pass"),
        nombre="Student",
        correo_electronico="stud_p_ex@example.com",
        tipo="student",
        activo=True,
        correo_electronico_verificado=True,
    )
    db_session.add_all([admin, instructor, student])

    curso1 = Curso(
        codigo="C101",
        nombre="Curso 101",
        descripcion_corta="desc",
        descripcion="desc",
        estado="open",
        precio=10.0,
    )
    db_session.add(curso1)

    cat = Categoria(nombre="DevOps", descripcion="Infrastructure")
    tag = Etiqueta(nombre="docker", color="green")
    db_session.add_all([cat, tag])
    db_session.commit()

    # Create certificate template
    template = Certificado(
        code="PROG_TEMP_01",
        titulo="Program Certificate Template",
        descripcion="Template Desc",
        html="<h1>Certificado de Programa para {{ usuario.nombre }}</h1>",
        css="h1 { color: green; }",
        tipo="program",
        habilitado=True,
        publico=True,
        usuario=admin.usuario,
    )
    db_session.add(template)
    db_session.commit()

    return {
        "admin": admin,
        "instructor": instructor,
        "student": student,
        "curso1": curso1,
        "categoria": cat,
        "etiqueta": tag,
        "template": template,
    }


def login(client, username):
    client.get("/user/logout")
    resp = client.post("/user/login", data={"usuario": username, "acceso": "pass"})
    # Ensure login was successful or we are redirected/authenticated
    assert resp.status_code in [200, 302]


def test_logo_upload_and_operational_errors(client, db_session, extra_prog_setup):
    """Test _save_program_logo and OperationalErrors in program creation and editing."""
    login(client, "inst_prog_ex")

    # 1. Test creation OperationalError
    with patch("now_lms.vistas.programs.database.session.commit", side_effect=OperationalError("mock", {}, Exception())):
        response = client.post(
            "/program/new",
            data={
                "nombre": "Python Prog Error",
                "descripcion": "desc",
                "codigo": "PYERR",
                "precio": "0.0",
                "categoria": str(extra_prog_setup["categoria"].id),
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"Hubo un error al crear el programa." in response.data

    # 2. Setup a valid program for testing edits and logo uploads
    login(client, "admin_prog_ex")
    prog = Programa(
        codigo="PROG_LOGO",
        nombre="Logo Program",
        descripcion="desc",
        creado_por="admin_prog_ex",
        estado="draft",
        publico=False,
    )
    db_session.add(prog)
    db_session.commit()

    # 3. Test saving program logo with UploadNotAllowed exception
    # Mocking images.save to raise UploadNotAllowed
    with patch("now_lms.vistas.programs.images.save", side_effect=UploadNotAllowed()):
        data = {
            "nombre": "Logo Program",
            "descripcion": "desc",
            "codigo": "PROG_LOGO",
            "precio": "0.0",
            "estado": "draft",
            "logo": (BytesIO(b"fake image data"), "logo.png"),
        }
        response = client.post(
            f"/program/{prog.id}/edit",
            data=data,
            follow_redirects=True,
        )
        assert b"No se pudo actualizar la portada del curso." in response.data

    # 4. Test successful logo upload saving
    with patch("now_lms.vistas.programs.images.save", return_value="programPROG_LOGO/logo.jpg"):
        data = {
            "nombre": "Logo Program",
            "descripcion": "desc",
            "codigo": "PROG_LOGO",
            "precio": "0.0",
            "estado": "draft",
            "logo": (BytesIO(b"fake image data"), "logo.jpg"),
        }
        response = client.post(
            f"/program/{prog.id}/edit",
            data=data,
            follow_redirects=True,
        )
        assert b"Portada del curso actualizada correctamente" in response.data

    # 5. Test edit OperationalError
    with patch("now_lms.vistas.programs.database.session.commit", side_effect=OperationalError("mock", {}, Exception())):
        response = client.post(
            f"/program/{prog.id}/edit",
            data={
                "nombre": "Logo Program Updated Error",
                "descripcion": "desc",
                "codigo": "PROG_LOGO",
                "precio": "0.0",
                "estado": "draft",
            },
            follow_redirects=True,
        )
        assert b"No se puedo editar el programa." in response.data


def test_delete_program_scenarios(client, db_session, extra_prog_setup):
    """Test delete program route under diverse scenarios."""
    # Create program
    prog = Programa(
        codigo="PROG_DEL",
        nombre="Delete Program",
        descripcion="desc",
        creado_por="inst_prog_ex",
        estado="draft",
    )
    db_session.add(prog)
    db_session.commit()

    # 1. Nonexistent program -> 404
    login(client, "admin_prog_ex")
    response = client.get("/program/999999999999/delete")
    assert response.status_code == 404

    # 2. Non-admin trying to delete -> 403
    login(client, "inst_prog_ex")
    response = client.get(f"/program/{prog.id}/delete")
    assert response.status_code == 403

    # Important: rollback the session because step 2 executed delete on the session before aborting
    db_session.rollback()

    # 3. Admin successfully deletes -> Redirects
    login(client, "admin_prog_ex")
    response = client.get(f"/program/{prog.id}/delete", follow_redirects=True)
    assert response.status_code == 200
    deleted = db_session.execute(database.select(Programa).filter_by(codigo="PROG_DEL")).scalars().first()
    assert deleted is None


def test_program_explore_parameters(client, db_session, extra_prog_setup):
    """Test public explore with advanced filters and query strings."""
    # Create a public program and link category and tag
    prog = Programa(
        codigo="PROG_EXPLORE",
        nombre="Explore Me",
        descripcion="desc",
        creado_por="admin_prog_ex",
        estado="open",
        publico=True,
    )
    db_session.add(prog)
    db_session.commit()

    # Associate tag and category
    from now_lms.db import CategoriaPrograma, EtiquetaPrograma
    db_session.add(CategoriaPrograma(programa=prog.id, categoria=extra_prog_setup["categoria"].id))
    db_session.add(EtiquetaPrograma(programa=prog.id, etiqueta=extra_prog_setup["etiqueta"].id))
    db_session.commit()

    cache.clear()

    # Request with tag and category in URL
    response = client.get(
        "/program/explore",
        query_string={
            "tag": "docker",
            "category": "DevOps",
            "nivel": "easy",
            "page": "1"
        }
    )
    assert response.status_code == 200
    assert b"Explore Me" in response.data


def test_program_enrollment_free_and_paid(client, db_session, extra_prog_setup):
    """Test enrolling in free and paid programs, including errors and redirects."""
    # Enable PayPal globally first
    paypal_cfg = db_session.execute(database.select(PaypalConfig)).scalars().first()
    if paypal_cfg:
        paypal_cfg.enable = True
        db_session.commit()

    # 1. Create a free program
    free_prog = Programa(
        codigo="PROG_FREE",
        nombre="Free Program",
        descripcion="desc",
        creado_por="admin_prog_ex",
        estado="open",
        publico=True,
        precio=0.0,
    )
    # Link a course to the program
    db_session.add(free_prog)
    db_session.commit()
    db_session.add(ProgramaCurso(programa="PROG_FREE", curso="C101", creado_por="admin_prog_ex"))
    db_session.commit()

    # Enroll in FREE program
    login(client, "stud_p_ex")
    response = client.post("/program/PROG_FREE/enroll", follow_redirects=True)
    assert response.status_code == 200
    assert b"Te has inscrito exitosamente al programa." in response.data

    # Attempt duplicate enrollment -> should redirect and show "Ya estás inscrito"
    response2 = client.post("/program/PROG_FREE/enroll", follow_redirects=True)
    assert b"Ya est\xc3\xa1s inscrito" in response2.data

    # 2. Create a PAID program
    paid_prog = Programa(
        codigo="PROG_PAID",
        nombre="Paid Program",
        descripcion="desc",
        creado_por="admin_prog_ex",
        estado="open",
        publico=True,
        precio=50.0,
    )
    db_session.add(paid_prog)
    db_session.commit()

    # Post to enroll in PAID program -> should create a pending payment and redirect
    response_paid = client.post("/program/PROG_PAID/enroll", follow_redirects=True)
    assert response_paid.status_code == 200
    assert b"Pay with" in response_paid.data or b"Pagar con" in response_paid.data or b"PayPal" in response_paid.data

    # Request enroll again -> should redirect using existing pending payment
    response_paid_dup = client.post("/program/PROG_PAID/enroll", follow_redirects=True)
    assert response_paid_dup.status_code == 200


def test_program_checkout_errors(client, db_session, extra_prog_setup):
    """Test errors and constraints in checkout/payment for programs."""
    login(client, "stud_p_ex")

    # 1. Program not found for payment
    response = client.get("/program/NONEXISTENT/payment")
    assert response.status_code == 302

    # 2. Free program payment request -> redirected
    free_prog = Programa(
        codigo="PROG_FREE_PAY",
        nombre="Free Pay",
        precio=0.0,
        creado_por="admin_prog_ex",
    )
    db_session.add(free_prog)
    db_session.commit()
    response = client.get("/program/PROG_FREE_PAY/payment")
    assert response.status_code == 302

    # 3. Paid program with PayPal disabled
    paid_prog = Programa(
        codigo="PROG_PAID_PAY",
        nombre="Paid Pay",
        precio=100.0,
        creado_por="admin_prog_ex",
    )
    db_session.add(paid_prog)
    db_session.commit()

    # Disable PayPal in config table (Configuracion or PaypalConfig)
    paypal_cfg = db_session.execute(database.select(PaypalConfig)).scalars().first()
    if paypal_cfg:
        paypal_cfg.enable = False
        db_session.commit()

    response = client.get("/program/PROG_PAID_PAY/payment")
    assert response.status_code == 302


def test_take_program_cert_emission(client, db_session, extra_prog_setup):
    """Test taking program and certificate auto-emission if complete."""
    student = extra_prog_setup["student"]

    # Create program requiring certificate
    prog = Programa(
        codigo="PROG_CERT",
        nombre="Cert Program",
        descripcion="desc",
        creado_por="admin_prog_ex",
        estado="open",
        publico=True,
        certificado=True,
        plantilla_certificado="PROG_TEMP_01",
    )
    db_session.add(prog)
    db_session.commit()

    # Link course to program
    db_session.add(ProgramaCurso(programa="PROG_CERT", curso="C101", creado_por="admin_prog_ex"))
    db_session.commit()

    # Enroll user in program
    pe = ProgramaEstudiante(usuario=student.usuario, programa=prog.id, creado_por="admin_prog_ex")
    db_session.add(pe)
    db_session.commit()

    # Create course completion certificate to make verification pass
    c_cert = Certificacion(
        usuario=student.usuario,
        curso="C101",
        certificado="PROG_TEMP_01",
    )
    db_session.add(c_cert)
    db_session.commit()

    login(client, "stud_p_ex")

    # Access take program route (course C101 is completed, so program is completed and certificate gets emitted)
    response = client.get("/program/PROG_CERT/take")
    assert response.status_code == 200

    # Verify certificate is generated
    cert = db_session.execute(
        database.select(CertificacionPrograma).filter_by(usuario=student.usuario, programa=prog.id)
    ).scalar_one_or_none()
    assert cert is not None
    assert cert.certificado == "PROG_TEMP_01"


def test_gestionar_cursos_programa_failures_and_actions(client, db_session, extra_prog_setup):
    """Test gestionar_cursos_programa route failures, unauthorized, and action details."""
    # Create program
    prog = Programa(
        codigo="PROG_GEST",
        nombre="Gest Program",
        descripcion="desc",
        creado_por="inst_prog_ex",
        estado="draft",
    )
    db_session.add(prog)
    db_session.commit()

    # 1. Program not found -> 404
    login(client, "admin_prog_ex")
    response = client.get("/program/NONEXISTENT/courses/manage")
    assert response.status_code == 404

    # 2. Non-admin -> 403
    login(client, "inst_prog_ex")
    response = client.get("/program/PROG_GEST/courses/manage")
    assert response.status_code == 403

    # 3. Add existing course warnings
    login(client, "admin_prog_ex")
    # Add course once
    client.post(
        "/program/PROG_GEST/courses/manage",
        data={"action": "add_course", "curso_codigo": "C101"},
        follow_redirects=True,
    )
    # Add again -> warning "El curso ya está en el programa"
    response = client.post(
        "/program/PROG_GEST/courses/manage",
        data={"action": "add_course", "curso_codigo": "C101"},
        follow_redirects=True,
    )
    assert b"El curso ya est\xc3\xa1 en el programa" in response.data

    # 4. Remove course
    response = client.post(
        "/program/PROG_GEST/courses/manage",
        data={"action": "remove_course", "curso_codigo": "C101"},
        follow_redirects=True,
    )
    assert b"removido del programa" in response.data


def test_inscribir_usuario_programa_failures(client, db_session, extra_prog_setup):
    """Test manual student enrollment into programs by admin."""
    prog = Programa(
        codigo="PROG_MAN_EX",
        nombre="Manual Prog",
        descripcion="desc",
        creado_por="admin_prog_ex",
    )
    db_session.add(prog)
    db_session.commit()

    login(client, "admin_prog_ex")

    # 1. User not found
    response = client.post(
        "/program/PROG_MAN_EX/enroll_user",
        data={"usuario_email": "nonexistent@test.com"},
        follow_redirects=True,
    )
    assert b"Usuario no encontrado" in response.data

    # 2. Success
    response = client.post(
        "/program/PROG_MAN_EX/enroll_user",
        data={"usuario_email": "stud_p_ex@example.com"},
        follow_redirects=True,
    )
    assert b"inscrito exitosamente" in response.data

    # 3. Already enrolled
    response = client.post(
        "/program/PROG_MAN_EX/enroll_user",
        data={"usuario_email": "stud_p_ex@example.com"},
        follow_redirects=True,
    )
    assert b"El usuario ya est\xc3\xa1 inscrito" in response.data


def test_admin_enrollment_additional_coverage(client, db_session, extra_prog_setup):
    """Test admin program enrollment edge cases."""
    prog = Programa(
        codigo="PROG_ADMIN_EX",
        nombre="Admin Prog Ex",
        descripcion="desc",
        creado_por="admin_prog_ex",
    )
    db_session.add(prog)
    db_session.commit()

    login(client, "admin_prog_ex")

    # 1. Nonexistent student
    response = client.post(
        "/program/PROG_ADMIN_EX/admin/enroll",
        data={"student_username": "nonexistent_stud", "bypass_payment": True},
        follow_redirects=True,
    )
    assert b"no existe en el sistema" in response.data

    # 2. Duplicate student enrollment
    # Enroll once
    client.post(
        "/program/PROG_ADMIN_EX/admin/enroll",
        data={"student_username": "stud_p_ex", "bypass_payment": True},
        follow_redirects=True,
    )
    # Enroll again -> warning
    response = client.post(
        "/program/PROG_ADMIN_EX/admin/enroll",
        data={"student_username": "stud_p_ex", "bypass_payment": True},
        follow_redirects=True,
    )
    assert b"ya est\xc3\xa1 inscrito en este programa" in response.data

    # 3. Unenroll student who is not enrolled in a different program
    prog2 = Programa(
        codigo="PROG_ADMIN_EX2",
        nombre="Admin Prog Ex 2",
        descripcion="desc",
        creado_por="admin_prog_ex",
    )
    db_session.add(prog2)
    db_session.commit()

    response = client.post(
        "/program/PROG_ADMIN_EX2/admin/unenroll/stud_p_ex",
        follow_redirects=True,
    )
    assert b"no est\xc3\xa1 inscrito en este programa" in response.data
