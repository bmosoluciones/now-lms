# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""
Comprehensive tests for programs and instructor profiles view files.
"""

import pytest
from unittest import mock
from datetime import datetime
from now_lms.auth import proteger_passwd
from now_lms.db import (
    database,
    Usuario,
    Curso,
    DocenteCurso,
    UsuarioGrupo,
    UsuarioGrupoMiembro,
    Programa,
    ProgramaCurso,
)

@pytest.fixture
def test_setup(app, db_session):
    instructor = Usuario(
        usuario="inst_prof",
        acceso=proteger_passwd("pass"),
        nombre="Instructor Profile",
        correo_electronico="inst_prof@test.com",
        tipo="instructor",
        activo=True,
    )
    admin = Usuario(
        usuario="admin_prof",
        acceso=proteger_passwd("pass"),
        nombre="Admin Profile",
        correo_electronico="admin_prof@test.com",
        tipo="admin",
        activo=True,
    )
    student = Usuario(
        usuario="stud_prof",
        acceso=proteger_passwd("pass"),
        nombre="Student Profile",
        correo_electronico="student_prof@test.com",
        tipo="student",
        activo=True,
    )
    db_session.add_all([instructor, admin, student])
    db_session.commit()

    course = Curso(
        nombre="Instructor Course",
        codigo="IC101",
        descripcion_corta="desc",
        descripcion="desc",
        estado="open",
        certificado=False,
        publico=True,
    )
    db_session.add(course)
    db_session.commit()

    # Assign instructor
    dc = DocenteCurso(usuario="inst_prof", curso="IC101", vigente=True, creado_por="admin_prof")
    db_session.add(dc)
    db_session.commit()

    return {
        "instructor": instructor,
        "admin": admin,
        "student": student,
        "course": course,
    }


def login(client, user):
    client.get("/user/logout")
    resp = client.post("/user/login", data={"usuario": user.usuario, "acceso": "pass"})
    assert resp.status_code in [302, 200]


# ==============================================================================
# Instructor Profile View Tests
# ==============================================================================

def test_instructor_profile_routes(client, test_setup, db_session):
    # GET /instructor
    login(client, test_setup["instructor"])
    resp = client.get("/instructor")
    assert resp.status_code == 200

    # GET /instructor/courses_list
    resp = client.get("/instructor/courses_list")
    assert resp.status_code == 200

    # GET /instructor/evaluations
    resp = client.get("/instructor/evaluations")
    assert resp.status_code == 200


def test_instructor_groups_workflow(client, test_setup, db_session):
    login(client, test_setup["instructor"])

    # Create a group via DB
    grp = UsuarioGrupo(nombre="Group A", descripcion="A test group", tutor="inst_prof", activo=True)
    db_session.add(grp)
    db_session.commit()

    # GET list
    resp = client.get("/instructor/group/list")
    assert resp.status_code == 200

    # GET group details
    resp = client.get(f"/group/{grp.id}?id={grp.id}")
    assert resp.status_code == 200

    # Add student to group (POST)
    data = {"usuario": "stud_prof", "id": grp.id}
    resp = client.post("/group/add", data=data, follow_redirects=True)
    assert resp.status_code == 200

    gu = db_session.execute(database.select(UsuarioGrupoMiembro).filter_by(grupo=grp.id, usuario="stud_prof")).scalar_one_or_none()
    assert gu is not None

    # Remove student from group
    resp = client.get(f"/group/remove/{grp.id}/stud_prof", follow_redirects=True)
    assert resp.status_code == 200

    gu_deleted = db_session.execute(database.select(UsuarioGrupoMiembro).filter_by(grupo=grp.id, usuario="stud_prof")).scalar_one_or_none()
    assert gu_deleted is None


# ==============================================================================
# Programs View Remaining Coverage Tests
# ==============================================================================

def test_programs_remaining_coverage(client, test_setup, db_session):
    login(client, test_setup["admin"])

    # Create a program via DB
    prog = Programa(
        codigo="PROG_REM",
        nombre="Program Rem",
        descripcion="desc",
        creado_por="admin_prof",
        estado="draft",
        publico=False,
    )
    db_session.add(prog)

    # Associate course to program so open transition is allowed
    pc = ProgramaCurso(programa="PROG_REM", curso="IC101", creado_por="admin_prof")
    db_session.add(pc)
    db_session.commit()

    # GET edit program
    resp = client.get(f"/program/{prog.id}/edit")
    assert resp.status_code == 200

    # POST edit program with status change
    data = {
        "nombre": "Program Rem Updated",
        "descripcion": "updated description",
        "codigo": "PROG_REM",
        "precio": "100.0",
        "estado": "open",
    }
    resp = client.post(f"/program/{prog.id}/edit", data=data, follow_redirects=True)
    assert resp.status_code == 200

    db_session.refresh(prog)
    assert prog.nombre == "Program Rem Updated"
    assert prog.estado == "open"
