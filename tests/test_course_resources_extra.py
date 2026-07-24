# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""
Comprehensive tests for remaining course resources helpers and endpoints.
"""

import pytest
from unittest import mock
from datetime import date, time
from now_lms.auth import proteger_passwd
from now_lms.db import Usuario, Curso, CursoRecurso, database
from now_lms.vistas.courses.resources import (
    _generate_meet_ics_content,
)

@pytest.fixture
def test_setup(app, db_session):
    admin = Usuario(
        usuario="admin_res",
        acceso=proteger_passwd("pass"),
        nombre="Res Admin",
        correo_electronico="admin_res@test.com",
        tipo="admin",
        activo=True,
    )
    db_session.add(admin)
    db_session.commit()

    course = Curso(
        nombre="Resources Course",
        codigo="RES101",
        descripcion_corta="desc",
        descripcion="desc",
        estado="open",
        certificado=False,
        publico=True,
    )
    db_session.add(course)
    db_session.commit()

    return {
        "admin": admin,
        "course": course,
    }


def login(client, user):
    client.get("/user/logout")
    resp = client.post("/user/login", data={"usuario": user.usuario, "acceso": "pass"})
    assert resp.status_code in [302, 200]


# ==============================================================================
# Unit Tests for Helper Functions
# ==============================================================================

def test_generate_meet_ics_content():
    """Test generating ICS calendar invite content."""
    res = mock.MagicMock()
    res.nombre = "Class Meet Session"
    res.descripcion = "Introduction to Resources"
    res.fecha = date(2026, 7, 20)
    res.hora_inicio = time(10, 0, 0)
    res.hora_fin = time(11, 0, 0)

    ics_data = _generate_meet_ics_content(res)
    assert "Class Meet Session" in ics_data
    assert "Introduction to Resources" in ics_data
    assert "DTSTART:20260720T100000" in ics_data
    assert "DTEND:20260720T110000" in ics_data


# ==============================================================================
# Endpoint Tests
# ==============================================================================

def test_download_meet_calendar(client, test_setup, db_session):
    login(client, test_setup["admin"])

    # Create the course section referenced by the resource
    from now_lms.db import CursoSeccion

    seccion = CursoSeccion(curso="RES101", nombre="Seccion 1", descripcion="seccion", indice=1)
    db_session.add(seccion)
    db_session.commit()

    # Create a meet resource
    res = CursoRecurso(
        curso="RES101",
        seccion=seccion.id,
        nombre="Meet Session A",
        descripcion="Live class session",
        tipo="meet",
        fecha=date(2026, 7, 20),
        hora_inicio=time(10, 0, 0),
        hora_fin=time(11, 0, 0),
        publico=True,
        indice=1,
    )
    db_session.add(res)
    db_session.commit()

    # GET download route
    resp = client.get(f"/course/RES101/resource/meet/{res.id}/calendar.ics")
    assert resp.status_code == 200
    assert "text/calendar" in resp.headers["Content-Type"]
    assert b"Meet Session A" in resp.data


def test_course_library_routes(client, test_setup):
    login(client, test_setup["admin"])

    # GET library page
    resp = client.get("/course/RES101/library")
    assert resp.status_code == 200
