# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""
Tests unitarios y de integración para la gestión de certificados.
"""

import pytest

from now_lms.auth import proteger_passwd
from now_lms.db import Certificacion, CertificacionPrograma, Certificado, Curso, Programa, Usuario, database
from now_lms.vistas.certificates import insert_style_in_html


@pytest.fixture
def cert_setup(app, db_session):
    """Configura usuarios, cursos y plantillas de certificados."""
    admin = Usuario(
        usuario="admin_cert",
        acceso=proteger_passwd("pass"),
        nombre="Admin",
        correo_electronico="admin_ct@example.com",
        tipo="admin",
        activo=True,
    )
    instructor = Usuario(
        usuario="inst_cert",
        acceso=proteger_passwd("pass"),
        nombre="Instructor",
        correo_electronico="inst_ct@example.com",
        tipo="instructor",
        activo=True,
    )
    student = Usuario(
        usuario="stud_cert",
        acceso=proteger_passwd("pass"),
        nombre="Student",
        correo_electronico="stud_ct@example.com",
        tipo="student",
        activo=True,
        correo_electronico_verificado=True,
    )
    db_session.add_all([admin, instructor, student])

    curso = Curso(
        codigo="CERT01",
        nombre="Certificate Course",
        descripcion_corta="cert",
        descripcion="cert",
        estado="open",
        certificado=True,
    )
    db_session.add(curso)
    db_session.commit()

    # Plantilla de certificado
    template = Certificado(
        code="TEMP01",
        titulo="Template 1",
        descripcion="Template Desc",
        html="<h1>Certificado de {{ usuario.nombre }}</h1>",
        css="h1 { color: blue; }",
        tipo="course",
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
        "curso": curso,
        "template": template,
    }


def test_insert_style_in_html(app, db_session, cert_setup):
    """Verifica que el CSS se inyecte en el HTML."""
    template = cert_setup["template"]
    result = insert_style_in_html(template)
    assert "<style>h1 { color: blue; }</style>" in result
    assert "<h1>Certificado de {{ usuario.nombre }}</h1>" in result


def test_routes_admin_manage_certificates(client, db_session, cert_setup):
    """Prueba acciones de habilitar, deshabilitar, publicar, despublicar de admin."""
    # Login admin
    client.post("/user/login", data={"usuario": "admin_cert", "acceso": "pass"})

    template = cert_setup["template"]

    # 1. Remove (Habilitado -> False)
    response = client.get(f"/certificate/{template.id}/remove", follow_redirects=True)
    assert response.status_code == 200
    db_session.refresh(template)
    assert template.habilitado is False

    # 2. Add (Habilitado -> True)
    response = client.get(f"/certificate/{template.id}/add", follow_redirects=True)
    assert response.status_code == 200
    db_session.refresh(template)
    assert template.habilitado is True

    # 3. Unpublish (Publico -> False)
    response = client.get(f"/certificate/{template.id}/unpublish", follow_redirects=True)
    assert response.status_code == 200
    db_session.refresh(template)
    assert template.publico is False

    # 4. Publish (Publico -> True)
    response = client.get(f"/certificate/{template.id}/publish", follow_redirects=True)
    assert response.status_code == 200
    db_session.refresh(template)
    assert template.publico is True


def test_routes_create_and_edit_certificate(client, db_session, cert_setup):
    """Prueba rutas para crear y editar plantillas de certificados."""
    client.post("/user/login", data={"usuario": "admin_cert", "acceso": "pass"})

    # 1. Crear nuevo
    response_create = client.post(
        "/certificate/new",
        data={
            "titulo": "New Template",
            "descripcion": "New Desc",
            "html": "<div>HTML</div>",
            "css": "div {}",
            "tipo": "course",
        },
        follow_redirects=True,
    )
    assert response_create.status_code == 200

    new_cert = db_session.execute(database.select(Certificado).filter_by(titulo="New Template")).scalars().first()
    assert new_cert is not None

    # 2. Inspect
    response_inspect = client.get(f"/certificate/inspect/{new_cert.id}/")
    assert response_inspect.status_code == 200
    assert b"HTML" in response_inspect.data

    # 3. Editar
    response_edit = client.post(
        f"/certificate/{new_cert.id}/edit",
        data={
            "titulo": "New Template Updated",
            "descripcion": "New Desc Updated",
            "html": "<div>HTML UPDATED</div>",
            "css": "div {color: red;}",
            "tipo": "course",
            "habilitado": True,
            "publico": True,
        },
        follow_redirects=True,
    )
    assert response_edit.status_code == 200
    db_session.refresh(new_cert)
    assert new_cert.titulo == "New Template Updated"


def test_routes_emit_and_view_certificate(client, db_session, cert_setup):
    """Prueba emisión y visualización de certificaciones."""
    student = cert_setup["student"]
    template = cert_setup["template"]

    # Generar certificación
    cert = Certificacion(
        usuario=student.usuario,
        curso="CERT01",
        certificado=template.code,
    )
    db_session.add(cert)
    db_session.commit()

    # QR de certificación
    response_qr = client.get(f"/certificate/get_as_qr/{cert.id}/")
    assert response_qr.status_code == 200
    assert response_qr.mimetype == "image/png"

    # Ver certificación renderizada
    response_view = client.get(f"/certificate/certificate/{cert.id}/")
    assert response_view.status_code == 200
    assert b"Certificado de Student" in response_view.data

    # Ver página de información del certificado (público)
    response_view_public = client.get(f"/certificate/view/{cert.id}")
    assert response_view_public.status_code == 200

    # Listar certificaciones (login student)
    client.post("/user/login", data={"usuario": "stud_cert", "acceso": "pass"})
    response_list = client.get("/certificate/issued/list")
    assert response_list.status_code == 200


def test_routes_program_certificate(client, db_session, cert_setup):
    """Prueba certificados para programas."""
    student = cert_setup["student"]
    template = cert_setup["template"]

    programa = Programa(
        codigo="PROG01",
        nombre="Prog 1",
        descripcion="Prog Desc",
        estado="open",
    )
    db_session.add(programa)
    db_session.commit()

    cert_prog = CertificacionPrograma(
        usuario=student.usuario,
        programa=programa.id,
        certificado=template.code,
    )
    db_session.add(cert_prog)
    db_session.commit()

    # QR de programa
    response_qr = client.get(f"/certificate/program/get_as_qr/{cert_prog.id}/")
    assert response_qr.status_code == 200
    assert response_qr.mimetype == "image/png"

    # Ver certificado programa
    response_view = client.get(f"/certificate/program/view/{cert_prog.id}/")
    assert response_view.status_code == 200
    assert b"Certificado de Student" in response_view.data
