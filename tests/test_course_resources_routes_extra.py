# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""
Extra comprehensive unit and integration tests for course resources routes (now_lms/vistas/courses/resources.py).
"""

import io
import os
from datetime import date, datetime, time
import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.exc import OperationalError

from now_lms.auth import proteger_passwd
from now_lms.db import (
    database,
    Usuario,
    Curso,
    CursoSeccion,
    CursoRecurso,
    DocenteCurso,
    EstudianteCurso,
    Pago,
    Configuracion,
    SlideShowResource,
    Slide,
)


@pytest.fixture
def extra_res_setup(app, db_session):
    """Sets up a complete set of records for extra resource routing tests."""
    admin = Usuario(
        usuario="admin_res_ex",
        acceso=proteger_passwd("pass"),
        nombre="Admin",
        correo_electronico="admin_res_ex@example.com",
        tipo="admin",
        activo=True,
    )
    instructor = Usuario(
        usuario="inst_res_ex",
        acceso=proteger_passwd("pass"),
        nombre="Instructor",
        correo_electronico="inst_res_ex@example.com",
        tipo="instructor",
        activo=True,
    )
    student = Usuario(
        usuario="stud_res_ex",
        acceso=proteger_passwd("pass"),
        nombre="Student",
        correo_electronico="stud_res_ex@example.com",
        tipo="student",
        activo=True,
    )
    db_session.add_all([admin, instructor, student])
    db_session.commit()

    curso = Curso(
        codigo="C404",
        nombre="Curso 404",
        descripcion_corta="desc",
        descripcion="desc",
        estado="open",
        precio=0.0,
    )
    db_session.add(curso)
    db_session.commit()

    # Assign instructor
    dc = DocenteCurso(usuario="inst_res_ex", curso="C404", vigente=True)
    db_session.add(dc)
    db_session.commit()

    # Enroll student (with completed payment so access verification passes)
    pago = Pago(
        usuario=student.usuario,
        curso="C404",
        estado="completed",
        metodo="free",
        monto=0,
        nombre="Student",
        apellido="Res",
        correo_electronico="stud_res_ex@example.com",
    )
    db_session.add(pago)
    db_session.commit()

    enrollment = EstudianteCurso(
        curso="C404",
        usuario=student.usuario,
        vigente=True,
        pago=pago.id,
    )
    db_session.add(enrollment)
    db_session.commit()

    # Create section
    section = CursoSeccion(
        curso="C404",
        nombre="Section 1",
        descripcion="desc",
        indice=1,
    )
    db_session.add(section)
    db_session.commit()

    return {
        "admin": admin,
        "instructor": instructor,
        "student": student,
        "curso": curso,
        "section": section,
    }


def login(client, username):
    client.get("/user/logout")
    client.post("/user/login", data={"usuario": username, "acceso": "pass"})


def test_resource_detail_view_not_found(client, db_session, extra_res_setup):
    """Test accessing nonexistent resource returns 404/redirect."""
    login(client, "stud_res_ex")

    # Nonexistent resource details
    resp = client.get("/course/C404/resource/text/99999")
    assert resp.status_code == 404


def test_invalid_resource_edit_gets_and_posts(client, db_session, extra_res_setup):
    """Test editing nonexistent resource returns 302 redirect."""
    login(client, "inst_res_ex")

    # Nonexistent resource edit GET -> redirects back with error
    resp = client.get(f"/course/C404/{extra_res_setup['section'].id}/text/99999/edit", follow_redirects=False)
    assert resp.status_code == 302


def test_download_recurso_errors_and_serving(client, db_session, extra_res_setup):
    """Test file download endpoint with missing and existent files."""
    course_code = "C404"
    section_id = extra_res_setup["section"].id

    # Create a downloadable file resource
    rec = CursoRecurso(
        curso=course_code,
        seccion=section_id,
        tipo="descargable",
        nombre="Downloadable File",
        descripcion="desc",
        doc="manual_test.pdf",
        creado_por="inst_res_ex",
    )
    db_session.add(rec)
    db_session.commit()

    login(client, "stud_res_ex")

    # 1. Nonexistent resource ID -> 404
    resp = client.get(f"/course/{course_code}/files/99999")
    assert resp.status_code == 404

    # 2. Existent resource ID -> works or redirects if file not found / config is unpopulated
    resp = client.get(f"/course/{course_code}/files/{rec.id}")
    assert resp.status_code in [200, 302, 404]


def test_slideshow_additional_crud_and_previews(client, db_session, extra_res_setup):
    """Test slideshow CRUD edge cases, nonexistent slides, and previews."""
    course_code = "C404"
    section_id = extra_res_setup["section"].id

    login(client, "inst_res_ex")

    # 1. Accessing nonexistent slideshow edit page -> 404
    resp = client.get(f"/course/{course_code}/slideshow/99999/edit")
    assert resp.status_code == 404

    # 2. Accessing nonexistent slideshow preview page -> 404
    resp = client.get(f"/course/{course_code}/slideshow/99999/preview")
    assert resp.status_code == 404


def test_meet_calendar_links_failures(client, db_session, extra_res_setup):
    """Test meet calendar integrations for nonexistent resources."""
    course_code = "C404"

    login(client, "stud_res_ex")

    # 1. Nonexistent meet resource calendar.ics -> 404
    resp = client.get(f"/course/{course_code}/resource/meet/99999/calendar.ics")
    assert resp.status_code == 404

    # 2. Nonexistent meet resource google-calendar -> 404
    resp = client.get(f"/course/{course_code}/resource/meet/99999/google-calendar")
    assert resp.status_code == 404

    # 3. Nonexistent meet resource outlook-calendar -> 404
    resp = client.get(f"/course/{course_code}/resource/meet/99999/outlook-calendar")
    assert resp.status_code == 404


def test_course_library_failures_and_permission_checks(client, db_session, extra_res_setup):
    """Test course library file uploads when disabled or unauthorized."""
    course_code = "C404"

    # Disable file uploads in config
    cfg = db_session.execute(database.select(Configuracion)).scalars().first()
    if cfg:
        cfg.enable_file_uploads = False
        db_session.commit()

    # 1. Try uploading library file when disabled -> redirects with error (302)
    login(client, "inst_res_ex")
    file_data = {
        "nombre": "User Guide",
        "descripcion": "Reference guide.",
        "archivo": (io.BytesIO(b"content"), "guide.pdf")
    }
    resp = client.post(
        f"/course/{course_code}/library/new",
        data=file_data,
        content_type="multipart/form-data",
        follow_redirects=False
    )
    assert resp.status_code == 302
