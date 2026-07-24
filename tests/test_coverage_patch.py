# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.

"""Unit and integration tests to maximize patch coverage of translated views."""

import pytest
from datetime import datetime, timedelta
from unittest import mock
from sqlalchemy.exc import OperationalError

from now_lms.auth import proteger_passwd
from now_lms.db import Usuario, Categoria, Etiqueta, Message, database

VALID_ULID = "01GDHJB3GKW022S729SJV0DCE0"

@pytest.fixture
def patch_users(app, db_session):
    """Creates admin, instructor, and student users for testing."""
    admin = Usuario(
        usuario="patch_admin",
        acceso=proteger_passwd("adminpass"),
        nombre="Patch Admin",
        correo_electronico="patch_admin@example.com",
        tipo="admin",
        activo=True,
    )
    instructor = Usuario(
        usuario="patch_instructor",
        acceso=proteger_passwd("instpass"),
        nombre="Patch Instructor",
        correo_electronico="patch_inst@example.com",
        tipo="instructor",
        activo=True,
    )
    student = Usuario(
        usuario="patch_student",
        acceso=proteger_passwd("studentpass"),
        nombre="Patch Student",
        correo_electronico="patch_stud@example.com",
        tipo="student",
        activo=True,
    )
    db_session.add_all([admin, instructor, student])
    db_session.commit()
    return {"admin": admin, "instructor": instructor, "student": student}


def login_admin(client):
    client.post("/user/login", data={"usuario": "patch_admin", "acceso": "adminpass"})


def login_instructor(client):
    client.post("/user/login", data={"usuario": "patch_instructor", "acceso": "instpass"})


def login_student(client):
    client.post("/user/login", data={"usuario": "patch_student", "acceso": "studentpass"})


# ==============================================================================
# 1. Announcements Uncovered Paths Tests
# ==============================================================================

def test_admin_announcements_not_found(client, patch_users):
    login_admin(client)
    # Non-existent announcement for edit
    resp = client.get("/admin/announcements/9999/edit", follow_redirects=True)
    assert resp.status_code == 200
    assert "Anuncio no encontrado o no es un anuncio global." in resp.text

    # Non-existent announcement for delete
    resp_del = client.post("/admin/announcements/9999/delete", follow_redirects=True)
    assert resp_del.status_code == 200
    assert "Anuncio no encontrado o no es un anuncio global." in resp_del.text


def test_instructor_announcements_not_found(client, patch_users):
    login_instructor(client)
    # Non-existent announcement for edit
    resp = client.get("/instructor/announcements/9999/edit", follow_redirects=True)
    assert resp.status_code == 200
    assert "Anuncio no encontrado o no es un anuncio de curso." in resp.text

    # Non-existent announcement for delete
    resp_del = client.post("/instructor/announcements/9999/delete", follow_redirects=True)
    assert resp_del.status_code == 200
    assert "Anuncio no encontrado o no es un anuncio de curso." in resp_del.text


# ==============================================================================
# 2. Categories Operational Error Tests
# ==============================================================================

def test_categories_create_operational_error(client, patch_users, db_session):
    login_instructor(client)
    with mock.patch("now_lms.db.database.session.commit") as mock_commit:
        mock_commit.side_effect = OperationalError("mock", {}, Exception())
        data = {"nombre": "Error Category", "descripcion": "Will fail on commit."}
        resp = client.post("/category/new", data=data, follow_redirects=True)
        assert resp.status_code == 200
        assert "Hubo un error al crear la categoria." in resp.text


def test_categories_edit_operational_error(client, patch_users, db_session):
    cat = Categoria(nombre="Test Cat", descripcion="Desc")
    db_session.add(cat)
    db_session.commit()

    login_instructor(client)
    with mock.patch("now_lms.db.database.session.commit") as mock_commit:
        mock_commit.side_effect = OperationalError("mock", {}, Exception())
        data = {"nombre": "Updated Cat", "descripcion": "Will fail."}
        resp = client.post(f"/category/{cat.id}/edit", data=data, follow_redirects=True)
        assert resp.status_code == 200
        assert "No se puedo editar la categoria." in resp.text


# ==============================================================================
# 3. Tags Operational Error Tests
# ==============================================================================

def test_tags_create_operational_error(client, patch_users, db_session):
    login_instructor(client)
    with mock.patch("now_lms.db.database.session.commit") as mock_commit:
        mock_commit.side_effect = OperationalError("mock", {}, Exception())
        data = {"nombre": "Error Tag", "color": "blue"}
        resp = client.post("/tag/new", data=data, follow_redirects=True)
        assert resp.status_code == 200
        assert "Hubo un error al crear la etiqueta." in resp.text


def test_tags_edit_operational_error(client, patch_users, db_session):
    tag = Etiqueta(nombre="Test Tag", color="blue")
    db_session.add(tag)
    db_session.commit()

    login_instructor(client)
    with mock.patch("now_lms.db.database.session.commit") as mock_commit:
        mock_commit.side_effect = OperationalError("mock", {}, Exception())
        data = {"nombre": "Updated Tag", "color": "red"}
        resp = client.post(f"/tag/{tag.id}/edit", data=data, follow_redirects=True)
        assert resp.status_code == 200
        assert "No se puedo editar la etiqueta." in resp.text


# ==============================================================================
# 4. Instructor Profiles Non-Existent Entities Tests
# ==============================================================================

def test_instructor_evaluation_entities_not_found(client, patch_users):
    login_instructor(client)
    # Non-existent evaluation edit
    resp = client.get(f"/instructor/evaluations/{VALID_ULID}/edit", follow_redirects=True)
    assert resp.status_code == 200
    assert "Evaluación no encontrada." in resp.text

    # Non-existent evaluation toggle status - assert redirect status code 302
    resp_toggle = client.post(f"/instructor/evaluations/{VALID_ULID}/toggle", follow_redirects=False)
    assert resp_toggle.status_code == 302

    # Non-existent question edit
    resp_q = client.get(f"/instructor/questions/{VALID_ULID}/edit", follow_redirects=True)
    assert resp_q.status_code == 200
    assert "Pregunta no encontrada." in resp_q.text

    # Non-existent option edit
    resp_opt = client.get(f"/instructor/options/{VALID_ULID}/edit", follow_redirects=True)
    assert resp_opt.status_code == 200
    assert "Opción no encontrada." in resp_opt.text

    # Non-existent option delete
    resp_opt_del = client.post(f"/instructor/options/{VALID_ULID}/delete", follow_redirects=True)
    assert resp_opt_del.status_code == 200
    assert "Opción no encontrada." in resp_opt_del.text

    # Non-existent question delete
    resp_q_del = client.post(f"/instructor/questions/{VALID_ULID}/delete", follow_redirects=True)
    assert resp_q_del.status_code == 200
    assert "Pregunta no encontrada." in resp_q_del.text

    # Non-existent question new option
    resp_q_new_opt = client.get(f"/instructor/questions/{VALID_ULID}/options/new", follow_redirects=True)
    assert resp_q_new_opt.status_code == 200
    assert "Pregunta no encontrada." in resp_q_new_opt.text


# ==============================================================================
# 5. PayPal Checkout Non-Existent Resumption Tests
# ==============================================================================

def test_paypal_resume_payment_not_found(client, patch_users):
    login_student(client)
    resp = client.get(f"/paypal_checkout/resume_payment/{VALID_ULID}", follow_redirects=True)
    assert resp.status_code == 200
    assert "Pago no encontrado o ya procesado." in resp.text


# ==============================================================================
# 6. Messages Non-Existent Standalone Report Tests
# ==============================================================================

def test_messages_uncovered_paths(client, patch_users, db_session):
    login_instructor(client)

    # 1. Standalone report with missing parameters
    resp_empty = client.post("/message/report/", data={}, follow_redirects=True)
    assert resp_empty.status_code == 200
    assert "Debe seleccionar un mensaje y proporcionar un motivo." in resp_empty.text

    # 2. Standalone report with non-existent message ID
    resp_no_msg = client.post("/message/report/", data={"message_id": "9999", "reason": "offensive"}, follow_redirects=True)
    assert resp_no_msg.status_code == 200
    assert "Mensaje no encontrado." in resp_no_msg.text

    # 3. Standalone report with message having non-existent thread
    # On databases with enforced FK constraints (PostgreSQL, MySQL), this insert
    # will fail with an IntegrityError or ProgrammingError.  Only run the check
    # on databases that allow orphan rows (e.g. SQLite without FK enforcement).
    from sqlalchemy.exc import IntegrityError, ProgrammingError

    msg = Message(thread_id="9999", sender_id="patch_admin", content="spam content")
    db_session.add(msg)
    try:
        db_session.commit()
    except (IntegrityError, ProgrammingError):
        db_session.rollback()
        return

    resp_no_thread = client.post("/message/report/", data={"message_id": msg.id, "reason": "offensive"}, follow_redirects=True)
    assert resp_no_thread.status_code == 200
    assert "Hilo de conversación no encontrado." in resp_no_thread.text
