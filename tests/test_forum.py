# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""
Tests unitarios e integración para la funcionalidad de foros.
"""

import pytest
from flask_login import login_user, logout_user
from now_lms.db import database, Usuario, Curso, DocenteCurso, EstudianteCurso, ModeradorCurso, ForoMensaje
from now_lms.auth import proteger_passwd
from now_lms.vistas.forum import (
    verificar_acceso_curso,
    puede_cerrar_mensajes,
    markdown_to_html,
)

@pytest.fixture
def forum_setup(app, db_session):
    """Configura usuarios y curso para pruebas de foro."""
    admin = Usuario(
        usuario="admin_f",
        acceso=proteger_passwd("pass"),
        nombre="Admin",
        correo_electronico="admin_f@example.com",
        tipo="admin",
        activo=True,
    )
    instructor = Usuario(
        usuario="inst_f",
        acceso=proteger_passwd("pass"),
        nombre="Instructor",
        correo_electronico="inst_f@example.com",
        tipo="instructor",
        activo=True,
    )
    moderator = Usuario(
        usuario="mod_f",
        acceso=proteger_passwd("pass"),
        nombre="Moderator",
        correo_electronico="mod_f@example.com",
        tipo="instructor",
        activo=True,
    )
    student = Usuario(
        usuario="stud_f",
        acceso=proteger_passwd("pass"),
        nombre="Student",
        correo_electronico="stud_f@example.com",
        tipo="student",
        activo=True,
        correo_electronico_verificado=True,
    )
    db_session.add_all([admin, instructor, moderator, student])

    curso = Curso(
        codigo="FORUM01",
        nombre="Forum Course",
        descripcion_corta="forum",
        descripcion="forum",
        estado="open",
        foro_habilitado=True,
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

def test_verificar_acceso_curso(app, db_session, forum_setup):
    """Verifica si el acceso al foro del curso es correcto según roles."""
    code = "FORUM01"

    # 1. No enrolled
    access, role = verificar_acceso_curso(code, "stud_f")
    assert access is False
    assert role is None

    # 2. Student enrolled
    est = EstudianteCurso(curso=code, usuario="stud_f", vigente=True)
    db_session.add(est)
    db_session.commit()
    access, role = verificar_acceso_curso(code, "stud_f")
    assert access is True
    assert role == "estudiante"

    # 3. Instructor enrolled
    inst = DocenteCurso(curso=code, usuario="inst_f", vigente=True)
    db_session.add(inst)
    db_session.commit()
    access, role = verificar_acceso_curso(code, "inst_f")
    assert access is True
    assert role == "instructor"

    # 4. Moderator enrolled
    mod = ModeradorCurso(curso=code, usuario="mod_f", vigente=True)
    db_session.add(mod)
    db_session.commit()
    access, role = verificar_acceso_curso(code, "mod_f")
    assert access is True
    assert role == "moderador"

def test_puede_cerrar_mensajes(app, db_session):
    """Verifica permisos para cerrar mensajes."""
    assert puede_cerrar_mensajes("instructor", "student") is True
    assert puede_cerrar_mensajes("moderador", "student") is True
    assert puede_cerrar_mensajes("estudiante", "admin") is True
    assert puede_cerrar_mensajes("estudiante", "student") is False

def test_markdown_to_html():
    """Prueba la conversión y sanitización de markdown a html."""
    md = "**Negrita** y <script>alert('xss')</script>"
    html = markdown_to_html(md)
    assert "<strong>Negrita</strong>" in html
    assert "<script>" not in html

def test_forum_list_routes(client, db_session, forum_setup):
    """Prueba la vista del foro con accesos y estado."""
    # 1. Sin enrolamiento -> 403 Forbidden
    client.post("/user/login", data={"usuario": "stud_f", "acceso": "pass"})
    response = client.get("/course/FORUM01/forum")
    assert response.status_code == 403

    # Enrolar al estudiante
    est = EstudianteCurso(curso="FORUM01", usuario="stud_f", vigente=True)
    db_session.add(est)
    db_session.commit()

    # Acceso exitoso
    response = client.get("/course/FORUM01/forum")
    assert response.status_code == 200

    # 2. Deshabilitar foro del curso -> Redirige
    forum_setup["curso"].foro_habilitado = False
    db_session.commit()
    response = client.get("/course/FORUM01/forum")
    assert response.status_code == 302

def test_forum_message_management(client, db_session, forum_setup):
    """Prueba creación, visualización, respuesta y cierre/apertura de mensajes."""
    # Enrolar estudiante e instructor
    est = EstudianteCurso(curso="FORUM01", usuario="stud_f", vigente=True)
    inst = DocenteCurso(curso="FORUM01", usuario="inst_f", vigente=True)
    db_session.add_all([est, inst])
    db_session.commit()

    # 1. Crear nuevo mensaje por estudiante
    client.post("/user/login", data={"usuario": "stud_f", "acceso": "pass"})
    response = client.post(
        "/course/FORUM01/forum/new",
        data={"contenido": "Hola foro!"},
        follow_redirects=True,
    )
    assert response.status_code == 200

    # Recuperar mensaje creado
    msg = db_session.execute(database.select(ForoMensaje).filter_by(curso_id="FORUM01")).scalars().first()
    assert msg is not None
    assert msg.contenido == "Hola foro!"
    assert msg.estado == "abierto"

    # 2. Responder al mensaje por estudiante
    response_reply = client.post(
        f"/course/FORUM01/forum/message/{msg.id}/reply",
        data={"contenido": "Esto es una respuesta."},
        follow_redirects=True,
    )
    assert response_reply.status_code == 200

    # 3. Ver mensaje con hilo
    response_view = client.get(f"/course/FORUM01/forum/message/{msg.id}")
    assert response_view.status_code == 200
    assert b"Hola foro!" in response_view.data

    # 4. Cerrar mensaje (por estudiante debe dar 403)
    response_close_fail = client.post(f"/course/FORUM01/forum/message/{msg.id}/close")
    assert response_close_fail.status_code == 403

    # Cerrar mensaje (por instructor)
    client.get("/user/logout")
    client.post("/user/login", data={"usuario": "inst_f", "acceso": "pass"})
    response_close_ok = client.post(f"/course/FORUM01/forum/message/{msg.id}/close", follow_redirects=True)
    assert response_close_ok.status_code == 200

    db_session.refresh(msg)
    assert msg.estado == "cerrado"

    # No se puede responder a un mensaje cerrado
    client.get("/user/logout")
    client.post("/user/login", data={"usuario": "stud_f", "acceso": "pass"})
    response_reply_fail = client.post(
        f"/course/FORUM01/forum/message/{msg.id}/reply",
        data={"contenido": "Intento fallido"},
        follow_redirects=True,
    )
    assert b"No se puede responder a este mensaje" in response_reply_fail.data

    # 5. Abrir mensaje por instructor
    client.get("/user/logout")
    client.post("/user/login", data={"usuario": "inst_f", "acceso": "pass"})
    response_open_ok = client.post(f"/course/FORUM01/forum/message/{msg.id}/open", follow_redirects=True)
    assert response_open_ok.status_code == 200
    db_session.refresh(msg)
    assert msg.estado == "abierto"
