# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.

"""Integration tests for admin and instructor announcements."""

import pytest
from flask import url_for
from datetime import datetime, timedelta
from unittest import mock

from now_lms.auth import proteger_passwd
from now_lms.db import Announcement, Curso, DocenteCurso, Usuario, database


@pytest.fixture
def test_users(app, db_session):
    """Creates an admin and an instructor user for testing."""
    admin = Usuario(
        usuario="ann_admin",
        acceso=proteger_passwd("adminpass"),
        nombre="Ann Admin",
        correo_electronico="ann_admin@example.com",
        tipo="admin",
        activo=True,
    )
    instructor = Usuario(
        usuario="ann_instructor",
        acceso=proteger_passwd("instpass"),
        nombre="Ann Instructor",
        correo_electronico="ann_inst@example.com",
        tipo="instructor",
        activo=True,
    )
    db_session.add_all([admin, instructor])
    db_session.commit()
    return {"admin": admin, "instructor": instructor}


@pytest.fixture
def client_admin(client, test_users, app):
    """Client authenticated as an admin."""
    with app.test_request_context():
        with client.session_transaction() as sess:
            sess["_user_id"] = test_users["admin"].id
            sess["_fresh"] = True
    return client


@pytest.fixture
def client_instructor(client, test_users, app):
    """Client authenticated as an instructor."""
    with app.test_request_context():
        with client.session_transaction() as sess:
            sess["_user_id"] = test_users["instructor"].id
            sess["_fresh"] = True
    return client


@pytest.fixture
def test_course(app, db_session, test_users):
    """Creates a test course and assigns the test instructor to it."""
    course = Curso(
        nombre="Announcement Course",
        codigo="ANN101",
        descripcion_corta="Short desc",
        descripcion="Long desc",
        estado="open",
        certificado=False,
        publico=True,
    )
    db_session.add(course)
    db_session.commit()

    assignment = DocenteCurso(
        curso="ANN101",
        usuario=test_users["instructor"].usuario,
        vigente=True,
        creado_por="system",
    )
    db_session.add(assignment)
    db_session.commit()

    return course


# ==============================================================================
# Admin Announcements Tests
# ==============================================================================

def test_admin_list_announcements(client_admin, db_session):
    """Test admin view listing global announcements."""
    # Create global announcement (course_id is None)
    ann = Announcement(
        title="Global Announcement",
        message="Important global updates.",
        is_sticky=True,
        created_by_id="ann_admin",
        creado_por="ann_admin",
    )
    db_session.add(ann)
    db_session.commit()

    resp = client_admin.get("/admin/announcements")
    assert resp.status_code == 200
    assert b"Global Announcement" in resp.data


def test_admin_create_announcement(client_admin, db_session):
    """Test admin creating a new global announcement."""
    data = {
        "title": "New Global Alert",
        "message": "System will be down for maintenance.",
        "expires_at": (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S"),
        "is_sticky": "y",
    }
    resp = client_admin.post("/admin/announcements/new", data=data, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Anuncio global creado exitosamente" in resp.data

    # Verify storage
    ann = db_session.execute(database.select(Announcement).filter_by(title="New Global Alert")).scalar_one()
    assert ann.message == "System will be down for maintenance."
    assert ann.is_sticky is True
    assert ann.course_id is None


def test_admin_edit_announcement(client_admin, db_session):
    """Test admin editing an existing global announcement."""
    ann = Announcement(
        title="To Be Edited",
        message="Original message",
        is_sticky=False,
        created_by_id="ann_admin",
        creado_por="ann_admin",
    )
    db_session.add(ann)
    db_session.commit()

    # Get edit page
    resp_get = client_admin.get(f"/admin/announcements/{ann.id}/edit")
    assert resp_get.status_code == 200

    # Post update
    data = {
        "title": "Edited Title",
        "message": "New modified message",
        "is_sticky": "",
    }
    resp_post = client_admin.post(f"/admin/announcements/{ann.id}/edit", data=data, follow_redirects=True)
    assert resp_post.status_code == 200
    assert b"Anuncio global actualizado exitosamente" in resp_post.data

    # Verify database update
    db_session.expire(ann)
    updated_ann = db_session.get(Announcement, ann.id)
    assert updated_ann.title == "Edited Title"
    assert updated_ann.message == "New modified message"


def test_admin_delete_announcement(client_admin, db_session):
    """Test admin deleting a global announcement."""
    ann = Announcement(
        title="To Be Deleted",
        message="Original message",
        is_sticky=False,
        created_by_id="ann_admin",
        creado_por="ann_admin",
    )
    db_session.add(ann)
    db_session.commit()
    ann_id = ann.id

    resp = client_admin.post(f"/admin/announcements/{ann_id}/delete", follow_redirects=True)
    assert resp.status_code == 200
    assert b"Anuncio global eliminado exitosamente" in resp.data

    # Verify deletion
    deleted = db_session.get(Announcement, ann_id)
    assert deleted is None


# ==============================================================================
# Instructor Announcements Tests
# ==============================================================================

def test_instructor_list_announcements(client_instructor, db_session, test_course):
    """Test instructor view listing course announcements."""
    # Create course announcement
    ann = Announcement(
        title="Course Announcement 1",
        message="Class is cancelled today.",
        course_id=test_course.codigo,
        created_by_id="ann_instructor",
        creado_por="ann_instructor",
    )
    db_session.add(ann)
    db_session.commit()

    resp = client_instructor.get("/instructor/announcements")
    assert resp.status_code == 200
    assert b"Course Announcement 1" in resp.data


def test_instructor_create_announcement_authorized(client_instructor, db_session, test_course):
    """Test instructor creating announcement on a course they teach."""
    data = {
        "course_id": test_course.codigo,
        "title": "Welcome Students",
        "message": "Hope you are ready for a great semester!",
    }
    resp = client_instructor.post("/instructor/announcements/new", data=data, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Anuncio de curso creado exitosamente" in resp.data

    # Verify storage
    ann = db_session.execute(database.select(Announcement).filter_by(title="Welcome Students")).scalar_one()
    assert ann.message == "Hope you are ready for a great semester!"
    assert ann.course_id == test_course.codigo


def test_instructor_create_announcement_unauthorized_course(client_instructor, db_session, test_course):
    """Test instructor cannot create announcement for a course they do not teach."""
    fake_course = Curso(codigo="INVALID_CODE", nombre="Fake Course")

    data = {
        "course_id": "INVALID_CODE",
        "title": "Sneaky Announcement",
        "message": "Instructor trying to post to random course.",
    }

    # Mock get_instructor_courses to include INVALID_CODE in choices so form validation passes,
    # but since it's not saved to DB, selected_course is None and authorization check fails.
    with mock.patch("now_lms.vistas.announcements.instructor.get_instructor_courses", return_value=[test_course, fake_course]):
        resp = client_instructor.post("/instructor/announcements/new", data=data, follow_redirects=True)

    assert resp.status_code == 200
    assert b"No tienes permisos para crear anuncios en ese curso" in resp.data


def test_instructor_edit_announcement(client_instructor, db_session, test_course):
    """Test instructor editing their course announcement."""
    ann = Announcement(
        title="Original Course Title",
        message="Original message",
        course_id=test_course.codigo,
        created_by_id="ann_instructor",
        creado_por="ann_instructor",
    )
    db_session.add(ann)
    db_session.commit()

    # Post update
    data = {
        "course_id": test_course.codigo,
        "title": "Modified Course Title",
        "message": "New modified message",
    }
    resp = client_instructor.post(f"/instructor/announcements/{ann.id}/edit", data=data, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Anuncio de curso actualizado exitosamente" in resp.data

    # Verify database update
    db_session.expire(ann)
    updated_ann = db_session.get(Announcement, ann.id)
    assert updated_ann.title == "Modified Course Title"


def test_instructor_delete_announcement(client_instructor, db_session, test_course):
    """Test instructor deleting their course announcement."""
    ann = Announcement(
        title="Delete me",
        message="Original message",
        course_id=test_course.codigo,
        created_by_id="ann_instructor",
        creado_por="ann_instructor",
    )
    db_session.add(ann)
    db_session.commit()
    ann_id = ann.id

    resp = client_instructor.post(f"/instructor/announcements/{ann_id}/delete", follow_redirects=True)
    assert resp.status_code == 200
    assert b"Anuncio de curso eliminado exitosamente" in resp.data

    # Verify deletion
    deleted = db_session.get(Announcement, ann_id)
    assert deleted is None
