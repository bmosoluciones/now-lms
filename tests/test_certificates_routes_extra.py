# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""
Extra comprehensive unit and integration tests for certificates routes (now_lms/vistas/certificates.py).
"""

import os
from datetime import datetime
import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.exc import OperationalError

from now_lms.auth import proteger_passwd
from now_lms.db import (
    database,
    Usuario,
    Curso,
    Programa,
    Certificacion,
    CertificacionPrograma,
    Certificado,
    MasterClassEnrollment,
)


@pytest.fixture
def extra_cert_setup(app, db_session):
    """Sets up a complete set of records for extra certificate routing tests."""
    admin = Usuario(
        usuario="admin_cert_ex",
        acceso=proteger_passwd("pass"),
        nombre="Admin",
        correo_electronico="admin_c_ex@example.com",
        tipo="admin",
        activo=True,
    )
    instructor = Usuario(
        usuario="inst_cert_ex",
        acceso=proteger_passwd("pass"),
        nombre="Instructor",
        correo_electronico="inst_c_ex@example.com",
        tipo="instructor",
        activo=True,
    )
    student = Usuario(
        usuario="stud_cert_ex",
        acceso=proteger_passwd("pass"),
        nombre="Student",
        correo_electronico="stud_c_ex@example.com",
        tipo="student",
        activo=True,
        correo_electronico_verificado=True,
    )
    moderator = Usuario(
        usuario="mod_cert_ex",
        acceso=proteger_passwd("pass"),
        nombre="Moderator",
        correo_electronico="mod_c_ex@example.com",
        tipo="moderator",
        activo=True,
    )
    db_session.add_all([admin, instructor, student, moderator])

    curso1 = Curso(
        codigo="C202",
        nombre="Curso 202",
        descripcion_corta="desc",
        descripcion="desc",
        estado="open",
        certificado=True,
    )
    db_session.add(curso1)
    db_session.commit()

    # Create certificate templates
    template_c = Certificado(
        code="TEMP_C",
        titulo="Course Temp",
        descripcion="desc",
        html="<h1>Course template for {{ usuario.nombre }}</h1>",
        css="h1 { color: red; }",
        tipo="course",
        habilitado=True,
        publico=True,
        usuario=admin.usuario,
    )
    template_p = Certificado(
        code="TEMP_P",
        titulo="Prog Temp",
        descripcion="desc",
        html="<h1>Prog template for {{ usuario.nombre }}</h1>",
        css="h1 { color: red; }",
        tipo="program",
        habilitado=True,
        publico=True,
        usuario=admin.usuario,
    )
    db_session.add_all([template_c, template_p])
    db_session.commit()

    # Create standard certification
    cert = Certificacion(
        usuario=student.usuario,
        curso="C202",
        certificado=template_c.code,
    )
    db_session.add(cert)
    db_session.commit()

    # Create program
    prog = Programa(
        codigo="P202",
        nombre="Program 202",
        descripcion="desc",
        creado_por=admin.usuario,
    )
    db_session.add(prog)
    db_session.commit()

    # Create program certification
    cert_p = CertificacionPrograma(
        usuario=student.usuario,
        programa=prog.id,
        certificado=template_p.code,
        cursos_snapshot='{"C202": "Curso 202"}',
    )
    db_session.add(cert_p)
    db_session.commit()

    return {
        "admin": admin,
        "instructor": instructor,
        "student": student,
        "moderator": moderator,
        "curso1": curso1,
        "template_c": template_c,
        "template_p": template_p,
        "cert": cert,
        "prog": prog,
        "cert_p": cert_p,
    }


def login(client, username):
    client.get("/user/logout")
    client.post("/user/login", data={"usuario": username, "acceso": "pass"})


def test_invalid_ulid_handling(client, db_session, extra_cert_setup):
    """Test remove, add, publish, unpublish, and inspect actions with invalid ULIDs."""
    login(client, "admin_cert_ex")

    # 1. Invalid ULID on remove -> Redirects
    resp = client.get("/certificate/NONEXISTENT/remove", follow_redirects=True)
    assert resp.status_code == 200

    # 2. Invalid ULID on add -> Redirects
    resp = client.get("/certificate/NONEXISTENT/add", follow_redirects=True)
    assert resp.status_code == 200

    # 3. Invalid ULID on publish -> Redirects
    resp = client.get("/certificate/NONEXISTENT/publish", follow_redirects=True)
    assert resp.status_code == 200

    # 4. Invalid ULID on unpublish -> Redirects
    resp = client.get("/certificate/NONEXISTENT/unpublish", follow_redirects=True)
    assert resp.status_code == 200

    # 5. Invalid ULID on inspect -> Returns not found
    resp = client.get("/certificate/inspect/NONEXISTENT/")
    assert b"Certificate not found" in resp.data

    # 6. Invalid ULID on certificate rendering -> Redirects
    resp = client.get("/certificate/certificate/NONEXISTENT/")
    assert resp.status_code == 302


def test_certificate_creation_edition_operational_errors(client, db_session, extra_cert_setup):
    """Test OperationalErrors in certificate creation and editing."""
    login(client, "admin_cert_ex")

    # 1. Test creation OperationalError
    with patch("now_lms.vistas.certificates.database.session.commit", side_effect=OperationalError("mock", {}, Exception())):
        resp = client.post(
            "/certificate/new",
            data={
                "titulo": "Temp Operational Error",
                "descripcion": "desc",
                "html": "<h1>test</h1>",
                "css": "h1 {}",
                "tipo": "course",
            },
            follow_redirects=True,
        )
        assert b"Hubo un error al crear el certificado." in resp.data

    # 2. Test edit OperationalError
    template = extra_cert_setup["template_c"]
    with patch("now_lms.vistas.certificates.database.session.commit", side_effect=OperationalError("mock", {}, Exception())):
        resp = client.post(
            f"/certificate/{template.id}/edit",
            data={
                "titulo": "Course Temp Updated",
                "descripcion": "desc",
                "html": "<h1>test</h1>",
                "css": "h1 {}",
                "tipo": "course",
            },
            follow_redirects=True,
        )
        assert b"No se puedo editar el certificado." in resp.data


def test_role_based_certificaciones_listing(client, db_session, extra_cert_setup):
    """Test certificaciones() route filtering for diverse user roles."""
    # 1. Moderator / Other role listing
    login(client, "mod_cert_ex")
    resp = client.get("/certificate/issued/list")
    assert resp.status_code == 200

    # 2. Instructor who has no assigned courses
    login(client, "inst_cert_ex")
    resp = client.get("/certificate/issued/list")
    assert resp.status_code == 200


def test_pdf_rendering_endpoints(client, db_session, extra_cert_setup):
    """Test serving certificates as PDF for both course and program certifications."""
    # Mocking flask_weasyprint.render_pdf to avoid needing full external tools or native library dependencies
    mock_pdf_response = MagicMock()
    mock_pdf_response.status_code = 200
    mock_pdf_response.mimetype = "application/pdf"

    # 1. Course PDF download
    with patch("flask_weasyprint.render_pdf", return_value=mock_pdf_response):
        resp = client.get(f"/certificate/download/{extra_cert_setup['cert'].id}/")
        assert resp.status_code == 200
        # Wait, if render_pdf is successfully mocked, it will return the mock_pdf_response
        # but since resp is returned from render_pdf, we can assert resp has mimetype application/pdf!

    # 2. Program PDF download
    with patch("flask_weasyprint.render_pdf", return_value=mock_pdf_response):
        resp = client.get(f"/certificate/program/download/{extra_cert_setup['cert_p'].id}/")
        assert resp.status_code == 200


def test_certificate_release_prerequisites_and_validation(client, db_session, extra_cert_setup):
    """Test manual certificate release prerequisites validation checks."""
    login(client, "inst_cert_ex")

    # 1. Manual creation with empty course selection -> warns user
    resp = client.post(
        "/certificate/release/",
        data={
            "usuario": "stud_cert_ex",
            "content_type": "course",
            "curso": "",
            "template": "TEMP_C",
            "nota": "100",
        },
        follow_redirects=True,
    )
    assert b"Por favor selecciona un curso." in resp.data

    # 2. Manual creation when can_user_receive_certificate check fails -> warns user
    with patch("now_lms.vistas.evaluation_helpers.can_user_receive_certificate", return_value=(False, "Evaluaciones pendientes")):
        resp = client.post(
            "/certificate/release/",
            data={
                "usuario": "stud_cert_ex",
                "content_type": "course",
                "curso": "C202",
                "template": "TEMP_C",
                "nota": "100",
            },
            follow_redirects=True,
        )
        assert b"No se puede emitir el certificado: Evaluaciones pendientes" in resp.data

    # 3. Manual creation for unconfirmed master class -> warns user
    resp = client.post(
        "/certificate/release/",
        data={
            "usuario": "stud_cert_ex",
            "content_type": "masterclass",
            "master_class": "MC999",
            "template": "TEMP_C",
            "nota": "100",
        },
        follow_redirects=True,
    )
    assert b"El usuario debe estar inscrito y confirmado en la clase magistral." in resp.data


def test_certificacion_crear_failures_and_emissions(client, db_session, extra_cert_setup):
    """Test direct course certification creation checks and exceptions."""
    login(client, "inst_cert_ex")

    # 1. Try to create certificate directly when user cannot receive it
    with patch("now_lms.vistas.evaluation_helpers.can_user_receive_certificate", return_value=(False, "Curso no completado")):
        resp = client.post(
            f"/certificate/issue/C202/stud_cert_ex/TEMP_C/",
            follow_redirects=True,
        )
        assert b"No se puede emitir el certificado: Curso no completado" in resp.data


def test_program_certificate_view_invalid_and_exceptions(client, db_session, extra_cert_setup):
    """Test program certificate view edge cases, nonexistent references and JSON decoding."""
    # 1. Nonexistent program certification -> 404
    resp = client.get("/certificate/program/view/NONEXISTENT/")
    assert resp.status_code == 404

    # 2. Program certificate view with corrupted JSON snapshot -> still renders
    cert_p = extra_cert_setup["cert_p"]
    cert_p.cursos_snapshot = "{invalid-json"
    db_session.commit()

    resp = client.get(f"/certificate/program/view/{cert_p.id}/")
    assert resp.status_code == 200
    assert b"Prog template" in resp.data
