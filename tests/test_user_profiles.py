# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.

"""Integration tests for user profiles (now_lms/vistas/profiles/user.py)."""

import pytest
from unittest import mock

from now_lms.auth import proteger_passwd
from now_lms.db import Certificacion, Curso, EstudianteCurso, Usuario, database
from now_lms.vistas.profiles.user import user_profile


@pytest.fixture
def profile_users(app, db_session):
    """Creates a student, an instructor, and another student user for testing."""
    student = Usuario(
        usuario="test_student_user",
        acceso=proteger_passwd("studentpass"),
        nombre="Test Student",
        correo_electronico="student_user@example.com",
        tipo="student",
        activo=True,
        visible=True,
    )
    instructor = Usuario(
        usuario="test_instructor_user",
        acceso=proteger_passwd("instructorpass"),
        nombre="Test Instructor",
        correo_electronico="instructor_user@example.com",
        tipo="instructor",
        activo=True,
        visible=True,
    )
    other_student = Usuario(
        usuario="other_student_user",
        acceso=proteger_passwd("otherpass"),
        nombre="Other Student",
        correo_electronico="other_user@example.com",
        tipo="student",
        activo=True,
        visible=False, # Private profile
    )
    db_session.add_all([student, instructor, other_student])
    db_session.commit()
    return {"student": student, "instructor": instructor, "other": other_student}


@pytest.fixture
def client_student(client, profile_users, app):
    """Client authenticated as a student."""
    with app.test_request_context():
        with client.session_transaction() as sess:
            sess["_user_id"] = profile_users["student"].id
            sess["_fresh"] = True
    return client


def test_pagina_estudiante(client_student):
    """Test accessing the student page."""
    resp = client_student.get("/student")
    assert resp.status_code == 200
    assert b"test_student_user" in resp.data or b"Test Student" in resp.data


def test_perfil_student(client_student, db_session, profile_users):
    """Test profile view for a student (with courses and certifications)."""
    # Create test course and enroll student
    course = Curso(
        nombre="Test Course For Profile",
        codigo="PROF101",
        descripcion_corta="Corta",
        descripcion="Long description",
        estado="open",
        certificado=True,
        publico=True,
    )
    db_session.add(course)
    db_session.commit()

    enrollment = EstudianteCurso(
        curso="PROF101",
        usuario=profile_users["student"].usuario,
        vigente=True,
    )
    db_session.add(enrollment)

    # Create a certification
    cert = Certificacion(
        usuario=profile_users["student"].id,
        curso="PROF101",
        certificado="default",
    )
    db_session.add(cert)
    db_session.commit()

    # Get profile
    resp = client_student.get("/perfil")
    assert resp.status_code == 200
    assert b"Test Course For Profile" in resp.data


def test_perfil_instructor(client, profile_users, app):
    """Test profile view for an instructor."""
    # Authenticate as instructor
    with app.test_request_context():
        with client.session_transaction() as sess:
            sess["_user_id"] = profile_users["instructor"].id
            sess["_fresh"] = True

    resp = client.get("/perfil")
    assert resp.status_code == 200
    assert b"Test Instructor" in resp.data


def test_view_other_users(client_student, profile_users):
    """Test viewing other users' profiles based on visibility."""
    # View public profile (instructor) -> should succeed
    resp_pub = client_student.get(f"/user/{profile_users['instructor'].usuario}")
    assert resp_pub.status_code == 200

    # View private profile (other student) -> should render private page
    resp_priv = client_student.get(f"/user/{profile_users['other'].usuario}")
    assert resp_priv.status_code == 200
    assert b"private" in resp_priv.data or b"privado" in resp_priv.data.lower()


def test_edit_perfil(client_student, profile_users, db_session):
    """Test editing profile via GET and POST."""
    student_id = profile_users["student"].id

    # 1. GET edit page
    resp_get = client_student.get(f"/perfil/edit/{student_id}")
    assert resp_get.status_code == 200

    # 2. POST updates
    edit_data = {
        "nombre": "Updated Name",
        "apellido": "Updated Surname",
        "correo_electronico": "student_user@example.com", # Same email
        "url": "https://updated.com",
        "bio": "My updated biography.",
    }
    resp_post = client_student.post(f"/perfil/edit/{student_id}", data=edit_data, follow_redirects=True)
    assert resp_post.status_code == 200
    assert b"Pefil actualizado" in resp_post.data

    # Verify updates in DB
    db_session.expire(profile_users["student"])
    updated_user = db_session.get(Usuario, student_id)
    assert updated_user.nombre == "Updated Name"
    assert updated_user.url == "https://updated.com"

    # 3. POST with email change (should prompt verification notice)
    edit_data["correo_electronico"] = "new_student_email@example.com"
    resp_post_email = client_student.post(f"/perfil/edit/{student_id}", data=edit_data, follow_redirects=True)
    if b"verifique su nuevo correo" not in resp_post_email.data:
        print("HTML RESP:", resp_post_email.data.decode("utf-8"))
    assert resp_post_email.status_code == 200
    assert b"verifique su nuevo correo" in resp_post_email.data


def test_edit_perfil_unauthorized(client_student, profile_users):
    """A user cannot edit another user's profile."""
    other_id = profile_users["other"].id
    resp = client_student.get(f"/perfil/edit/{other_id}")
    assert resp.status_code == 403


def test_elimina_logo_usuario(client_student, profile_users, db_session):
    """Test deleting user logo."""
    student_id = profile_users["student"].id
    with mock.patch("now_lms.vistas.profiles.user.elimina_imagen_usuario") as mock_elimina:
        resp = client_student.get(f"/perfil/{student_id}/delete_logo", follow_redirects=True)
        assert resp.status_code == 200
        mock_elimina.assert_called_once_with(ulid=student_id)


def test_cambiar_contrasena(client_student, profile_users, db_session):
    """Test changing user password."""
    student_id = profile_users["student"].id

    # 1. GET change password page
    resp_get = client_student.get(f"/perfil/cambiar_contrase\u00f1a/{student_id}")
    assert resp_get.status_code == 200

    # 2. POST with wrong current password
    pwd_data_wrong = {
        "current_password": "wrongpassword",
        "new_password": "newpassword123",
        "confirm_password": "newpassword123",
    }
    resp_post_wrong = client_student.post(
        f"/perfil/cambiar_contrase\u00f1a/{student_id}",
        data=pwd_data_wrong,
        follow_redirects=True
    )
    assert resp_post_wrong.status_code == 200
    assert b"La contrase\xc3\xb1a actual es incorrecta" in resp_post_wrong.data

    # 3. POST with mismatched new passwords
    pwd_data_mismatch = {
        "current_password": "studentpass",
        "new_password": "newpassword123",
        "confirm_password": "differentnew123",
    }
    resp_post_mismatch = client_student.post(
        f"/perfil/cambiar_contrase\u00f1a/{student_id}",
        data=pwd_data_mismatch,
        follow_redirects=True
    )
    assert resp_post_mismatch.status_code == 200
    assert b"Las nuevas contrase\xc3\xb1as no coinciden" in resp_post_mismatch.data

    # 4. POST correct password change
    pwd_data_correct = {
        "current_password": "studentpass",
        "new_password": "newpassword123",
        "confirm_password": "newpassword123",
    }
    resp_post_correct = client_student.post(
        f"/perfil/cambiar_contrase\u00f1a/{student_id}",
        data=pwd_data_correct,
        follow_redirects=True
    )
    assert resp_post_correct.status_code == 200
    assert b"Contrase\xc3\xb1a actualizada exitosamente" in resp_post_correct.data
