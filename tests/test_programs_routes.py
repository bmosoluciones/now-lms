# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""
Tests unitarios y de integración para la gestión de programas de estudio (vistas/programs.py).
"""

from datetime import datetime
import pytest
from flask_login import login_user, logout_user
from now_lms.cache import cache
from now_lms.db import (
    database,
    Usuario,
    Curso,
    Programa,
    ProgramaCurso,
    ProgramaEstudiante,
    Categoria,
    Etiqueta,
    CategoriaPrograma,
    EtiquetaPrograma,
)
from now_lms.auth import proteger_passwd

@pytest.fixture
def prog_setup(app, db_session):
    """Configura usuarios, cursos y categorías para pruebas de programas."""
    admin = Usuario(
        usuario="admin_p",
        acceso=proteger_passwd("pass"),
        nombre="Admin",
        correo_electronico="admin_p@example.com",
        tipo="admin",
        activo=True,
    )
    instructor = Usuario(
        usuario="inst_p",
        acceso=proteger_passwd("pass"),
        nombre="Instructor",
        correo_electronico="inst_p@example.com",
        tipo="instructor",
        activo=True,
    )
    student = Usuario(
        usuario="stud_p",
        acceso=proteger_passwd("pass"),
        nombre="Student",
        correo_electronico="stud_p@example.com",
        tipo="student",
        activo=True,
        correo_electronico_verificado=True,
    )
    db_session.add_all([admin, instructor, student])

    curso1 = Curso(
        codigo="C01",
        nombre="Curso 1",
        descripcion_corta="desc1",
        descripcion="desc1",
        estado="open",
    )
    curso2 = Curso(
        codigo="C02",
        nombre="Curso 2",
        descripcion_corta="desc2",
        descripcion="desc2",
        estado="open",
    )
    db_session.add_all([curso1, curso2])

    cat = Categoria(nombre="Backend", descripcion="Web programming")
    tag = Etiqueta(nombre="python", color="blue")
    db_session.add_all([cat, tag])
    db_session.commit()

    return {
        "admin": admin,
        "instructor": instructor,
        "student": student,
        "curso1": curso1,
        "curso2": curso2,
        "categoria": cat,
        "etiqueta": tag,
    }

def test_routes_create_program(client, db_session, prog_setup):
    """Prueba la creación de un nuevo programa por un instructor."""
    # Login instructor
    client.post("/user/login", data={"usuario": "inst_p", "acceso": "pass"})

    response = client.post(
        "/program/new",
        data={
            "nombre": "Especialización Python",
            "descripcion": "Aprende python desde cero",
            "codigo": "PYSP01",
            "precio": "199.99",
            "categoria": str(prog_setup["categoria"].id),
            "etiquetas": [str(prog_setup["etiqueta"].id)],
            "certificado": True,
        },
        follow_redirects=True,
    )
    assert response.status_code == 200

    # Verificar creación en DB
    prog = db_session.execute(database.select(Programa).filter_by(codigo="PYSP01")).scalars().first()
    assert prog is not None
    assert prog.nombre == "Especialización Python"

    # Verificar asociación de categoría y etiquetas
    cat_p = db_session.execute(database.select(CategoriaPrograma).filter_by(programa=prog.id)).scalars().first()
    assert cat_p is not None
    assert cat_p.categoria == prog_setup["categoria"].id

def test_routes_list_programs(client, db_session, prog_setup):
    """Prueba listar programas para instructor y admin."""
    # Crear programa de prueba
    prog = Programa(
        codigo="PROG_LIST",
        nombre="Programa List",
        descripcion="desc",
        creado_por=prog_setup["instructor"].usuario,
    )
    db_session.add(prog)
    db_session.commit()

    # Clear cache before retrieving to avoid stale lists
    cache.clear()

    # Instructor login
    client.post("/user/login", data={"usuario": "inst_p", "acceso": "pass"})
    response_inst = client.get("/program/list")
    assert response_inst.status_code == 200
    assert b"Programa List" in response_inst.data

    # Admin login
    client.get("/user/logout")
    client.post("/user/login", data={"usuario": "admin_p", "acceso": "pass"})
    response_admin = client.get("/program/list")
    assert response_admin.status_code == 200

def test_routes_edit_program(client, db_session, prog_setup):
    """Prueba editar programa como admin."""
    prog = Programa(
        codigo="PROG_EDIT",
        nombre="Programa Edit",
        descripcion="desc",
        creado_por=prog_setup["instructor"].usuario,
        estado="draft",
    )
    db_session.add(prog)
    db_session.commit()

    # Login como admin
    client.post("/user/login", data={"usuario": "admin_p", "acceso": "pass"})

    # Intentar editar
    response_edit = client.post(
        f"/program/{prog.id}/edit",
        data={
            "nombre": "Programa Edit Actualizado",
            "descripcion": "desc actualizada",
            "codigo": "PROG_EDIT",
            "precio": "50.0",
            "estado": "draft",
        },
        follow_redirects=True,
    )
    assert response_edit.status_code == 200
    db_session.refresh(prog)
    assert prog.nombre == "Programa Edit Actualizado"

def test_routes_explore_programs(client, db_session, prog_setup):
    """Prueba explorar programas públicos."""
    prog = Programa(
        codigo="PROG_EXP",
        nombre="Programa Explore",
        descripcion="desc",
        publico=True,
        estado="open",
        creado_por=prog_setup["instructor"].usuario,
    )
    db_session.add(prog)
    db_session.commit()

    # Ver lista de programas públicos
    response = client.get("/program/explore")
    assert response.status_code == 200
    assert b"Programa Explore" in response.data

def test_routes_enroll_and_take_program(client, db_session, prog_setup):
    """Prueba la inscripción y toma de un programa por un estudiante."""
    prog = Programa(
        codigo="PROG_TAKE",
        nombre="Programa Take",
        descripcion="desc",
        publico=True,
        estado="open",
        creado_por=prog_setup["instructor"].usuario,
    )
    db_session.add(prog)
    db_session.commit()

    # Login estudiante
    client.post("/user/login", data={"usuario": "stud_p", "acceso": "pass"})

    # Inscribir
    response_enroll = client.post(f"/program/PROG_TAKE/enroll", follow_redirects=True)
    assert response_enroll.status_code == 200
    assert b"Te has inscrito exitosamente" in response_enroll.data

    # Tomar programa
    response_take = client.get(f"/program/PROG_TAKE/take")
    assert response_take.status_code == 200

def test_routes_manage_courses_and_admin_enroll(client, db_session, prog_setup):
    """Prueba asociar cursos a programas e inscripción administrativa."""
    prog = Programa(
        codigo="PROG_MAN",
        nombre="Programa Manage",
        descripcion="desc",
        creado_por=prog_setup["instructor"].usuario,
    )
    db_session.add(prog)
    db_session.commit()

    # Login como admin
    client.post("/user/login", data={"usuario": "admin_p", "acceso": "pass"})

    # 1. Asociar un curso
    response_add = client.post(
        f"/program/PROG_MAN/courses/manage",
        data={"action": "add_course", "curso_codigo": "C01"},
        follow_redirects=True,
    )
    assert response_add.status_code == 200

    # Verificar que el curso está asociado
    pc = db_session.execute(database.select(ProgramaCurso).filter_by(programa="PROG_MAN", curso="C01")).scalars().first()
    assert pc is not None

    # 2. Inscripción administrativa
    response_enroll = client.post(
        f"/program/PROG_MAN/admin/enroll",
        data={"student_username": "stud_p", "bypass_payment": True, "notes": "Notas admin"},
        follow_redirects=True,
    )
    assert response_enroll.status_code == 200

    # Verificar enrolamiento
    pe = db_session.execute(database.select(ProgramaEstudiante).filter_by(programa=prog.id, usuario="stud_p")).scalars().first()
    assert pe is not None

    # Ver lista de enrollments
    response_list = client.get(f"/program/PROG_MAN/admin/enrollments")
    assert response_list.status_code == 200

    # 3. Desinscripción administrativa
    response_unenroll = client.post(
        f"/program/PROG_MAN/admin/unenroll/stud_p",
        follow_redirects=True,
    )
    assert response_unenroll.status_code == 200

    pe_deleted = db_session.execute(database.select(ProgramaEstudiante).filter_by(programa=prog.id, usuario="stud_p")).scalars().first()
    assert pe_deleted is None
