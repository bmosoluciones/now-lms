# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""
Tests unitarios y de integración para el sistema de mensajería privada.
"""

from datetime import datetime
import pytest
from flask_login import login_user, logout_user
from now_lms.db import (
    database,
    Usuario,
    Curso,
    DocenteCurso,
    EstudianteCurso,
    ModeradorCurso,
    MessageThread,
    Message,
)
from now_lms.auth import proteger_passwd
from now_lms.vistas.messages import (
    check_course_access,
    check_thread_access,
)

@pytest.fixture
def msg_setup(app, db_session):
    """Configura usuarios y curso para pruebas de mensajería."""
    admin = Usuario(
        usuario="admin_m",
        acceso=proteger_passwd("pass"),
        nombre="Admin",
        correo_electronico="admin_m@example.com",
        tipo="admin",
        activo=True,
    )
    instructor = Usuario(
        usuario="inst_m",
        acceso=proteger_passwd("pass"),
        nombre="Instructor",
        correo_electronico="inst_m@example.com",
        tipo="instructor",
        activo=True,
    )
    moderator = Usuario(
        usuario="mod_m",
        acceso=proteger_passwd("pass"),
        nombre="Moderator",
        correo_electronico="mod_m@example.com",
        tipo="instructor",  # user type must be instructor/admin, but we can assign moderator role in course
        activo=True,
    )
    student = Usuario(
        usuario="stud_m",
        acceso=proteger_passwd("pass"),
        nombre="Student",
        correo_electronico="stud_m@example.com",
        tipo="student",
        activo=True,
        correo_electronico_verificado=True,
    )
    db_session.add_all([admin, instructor, moderator, student])

    curso = Curso(
        codigo="MSG01",
        nombre="Messaging Course",
        descripcion_corta="msg",
        descripcion="msg",
        estado="open",
    )
    db_session.add(curso)
    db_session.commit()

    return {
        "admin": admin,
        "instructor": instructor,
        "moderator": moderator,
        "student": student,
        "curso": curso,
    }

def test_check_course_access(app, db_session, msg_setup):
    """Verifica la lógica de acceso al curso."""
    code = "MSG01"

    # 1. Admin siempre tiene acceso
    assert check_course_access(code, msg_setup["admin"]) is True

    # 2. Sin enrolamiento -> False
    assert check_course_access(code, msg_setup["student"]) is False

    # Enrolar student
    est = EstudianteCurso(curso=code, usuario="stud_m", vigente=True)
    db_session.add(est)
    db_session.commit()
    assert check_course_access(code, msg_setup["student"]) is True

    # Enrolar instructor
    doc = DocenteCurso(curso=code, usuario="inst_m", vigente=True)
    db_session.add(doc)
    db_session.commit()
    assert check_course_access(code, msg_setup["instructor"]) is True

    # Enrolar moderator
    mod_c = ModeradorCurso(curso=code, usuario="mod_m", vigente=True)
    db_session.add(mod_c)
    db_session.commit()
    # Cambiar rol en el objeto temporalmente a moderator para el check
    mod_user = msg_setup["moderator"]
    mod_user.tipo = "moderator"
    assert check_course_access(code, mod_user) is True

def test_check_thread_access(app, db_session, msg_setup):
    """Verifica acceso a hilos específicos."""
    code = "MSG01"

    thread = MessageThread(course_id=code, student_id="stud_m", status="open")
    db_session.add(thread)
    db_session.commit()

    # Admin -> True
    assert check_thread_access(thread, msg_setup["admin"]) is True

    # Student dueño -> True, otro student -> False
    assert check_thread_access(thread, msg_setup["student"]) is True
    other_stud = Usuario(usuario="stud_other", acceso=proteger_passwd("p"), nombre="O", correo_electronico="o@e.com", tipo="student", activo=True)
    db_session.add(other_stud)
    db_session.commit()
    assert check_thread_access(thread, other_stud) is False

def test_routes_messages_flow(client, db_session, msg_setup):
    """Prueba el flujo completo de listar, crear, responder e interactuar con hilos."""
    # Enrolar student e instructor
    est = EstudianteCurso(curso="MSG01", usuario="stud_m", vigente=True)
    doc = DocenteCurso(curso="MSG01", usuario="inst_m", vigente=True)
    db_session.add_all([est, doc])
    db_session.commit()

    # Login student
    client.post("/user/login", data={"usuario": "stud_m", "acceso": "pass"})

    # 1. Crear nuevo hilo
    response_new = client.post(
        "/course/MSG01/messages/new",
        data={"subject": "Duda sobre el tema 1", "content": "No entiendo la explicación."},
        follow_redirects=True,
    )
    assert response_new.status_code == 200

    # Recuperar hilo creado
    thread = db_session.execute(database.select(MessageThread).filter_by(course_id="MSG01")).scalars().first()
    assert thread is not None
    assert thread.status == "open"

    # Ver hilos del curso
    response_list = client.get("/course/MSG01/messages")
    assert response_list.status_code == 200

    # Ver hilos del usuario
    response_user_list = client.get("/user/messages")
    assert response_user_list.status_code == 200

    # Ver hilo individual
    response_view = client.get(f"/thread/{thread.id}")
    assert response_view.status_code == 200
    assert b"Duda sobre el tema 1" in response_view.data

    # 2. Responder al hilo
    response_reply = client.post(
        f"/thread/{thread.id}/reply",
        data={"content": "Aquí hay más detalles."},
        follow_redirects=True,
    )
    assert response_reply.status_code == 200

    # 3. Reportar mensaje
    msg_obj = db_session.execute(database.select(Message).filter_by(thread_id=thread.id)).scalars().first()
    assert msg_obj is not None

    response_report = client.post(
        f"/message/{msg_obj.id}/report",
        data={"reason": "Spam"},
        follow_redirects=True,
    )
    assert response_report.status_code == 200
    db_session.refresh(msg_obj)
    assert msg_obj.is_reported is True

    # 4. Cambiar estado a "fixed" (por estudiante)
    response_status = client.get(f"/thread/{thread.id}/status/fixed", follow_redirects=True)
    assert response_status.status_code == 200
    db_session.refresh(thread)
    assert thread.status == "fixed"

    # Logout student
    client.get("/user/logout")

    # Login Admin para resolver reporte y cerrar hilo
    client.post("/user/login", data={"usuario": "admin_m", "acceso": "pass"})

    # Ver mensajes reportados
    response_flagged = client.get("/admin/flagged-messages")
    assert response_flagged.status_code == 200

    # Resolver reporte
    response_resolve = client.post(f"/admin/resolve-report/{msg_obj.id}")
    assert response_resolve.status_code == 200
    db_session.refresh(msg_obj)
    assert msg_obj.is_reported is False

    # Cerrar hilo por Admin
    response_close = client.get(f"/thread/{thread.id}/status/closed", follow_redirects=True)
    assert response_close.status_code == 200
    db_session.refresh(thread)
    assert thread.status == "closed"
