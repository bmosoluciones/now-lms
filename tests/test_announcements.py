# Copyright 2025 BMO Soluciones, S.A.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""Tests for announcements functionality."""

from datetime import datetime, timedelta

from now_lms.db import Announcement, Curso, Usuario, DocenteCurso, database


def test_announcement_creation(isolated_db_session):
    """Test creating an announcement."""
    # Create test user
    test_user = Usuario(
        usuario="test_usera",
        acceso=b"test_password",
        nombre="Test",
        apellido="User",
        tipo="admin",
        activo=True,
    )
    database.session.add(test_user)
    database.session.commit()

    announcement = Announcement(
        title="Test Announcement",
        message="This is a test announcement",
        created_by_id=test_user.usuario,
    )
    database.session.add(announcement)
    database.session.commit()

    assert announcement.id is not None
    assert announcement.title == "Test Announcement"
    assert announcement.message == "This is a test announcement"
    assert announcement.created_by_id == test_user.usuario
    assert announcement.course_id is None
    assert not announcement.is_sticky


def test_global_announcement(isolated_db_session):
    """Test that announcement without course_id is global."""
    # Create test user
    test_user = Usuario(
        usuario="test_userb",
        acceso=b"test_password",
        nombre="Test",
        apellido="User",
        tipo="admin",
        activo=True,
    )
    database.session.add(test_user)
    database.session.commit()

    announcement = Announcement(
        title="Global Announcement",
        message="This is a global announcement",
        created_by_id=test_user.usuario,
    )
    database.session.add(announcement)
    database.session.commit()

    assert announcement.is_global()
    assert not announcement.is_course_announcement()


def test_course_announcement(isolated_db_session):
    """Test course announcement."""
    # Create test user
    test_user = Usuario(
        usuario="test_userc",
        acceso=b"test_password",
        nombre="Test",
        apellido="User",
        tipo="admin",
        activo=True,
    )
    database.session.add(test_user)

    # Create test course
    course = Curso(
        nombre="Test Course",
        codigo="TEST001",
        descripcion="Test course description",
        descripcion_corta="Test course",
        estado="open",
    )
    database.session.add(course)
    database.session.commit()

    announcement = Announcement(
        title="Course Announcement",
        message="This is a course announcement",
        course_id=course.codigo,
        created_by_id=test_user.usuario,
    )
    database.session.add(announcement)
    database.session.commit()

    assert not announcement.is_global()
    assert announcement.is_course_announcement()
    assert announcement.course_id == course.codigo


def test_announcement_expiration(session_basic_db_setup):
    """Test announcement expiration logic."""
    # Create test user (use existing session user to avoid conflicts)
    with session_basic_db_setup.app_context():
        from now_lms.db import select

        # Get an existing user from session fixture
        existing_user = database.session.execute(select(Usuario).limit(1)).scalar_one_or_none()
        if not existing_user:
            # Fallback if no users exist
            test_user = Usuario(
                usuario="test_userd",
                acceso=b"test_password",
                nombre="Test",
                apellido="User",
                tipo="admin",
                activo=True,
            )
            database.session.add(test_user)
            database.session.commit()
            user_id = test_user.usuario
        else:
            user_id = existing_user.usuario

        # Active announcement (no expiration)
        active_announcement = Announcement(
            title="Active Announcement",
            message="This announcement never expires",
            created_by_id=user_id,
        )
        assert active_announcement.is_active()

        # Active announcement (future expiration)
        future_expiration = datetime.now() + timedelta(days=1)
        future_announcement = Announcement(
            title="Future Announcement",
            message="This announcement expires tomorrow",
            expires_at=future_expiration,
            created_by_id=user_id,
        )
        assert future_announcement.is_active()

        # Expired announcement
        past_expiration = datetime.now() - timedelta(days=1)
        expired_announcement = Announcement(
            title="Expired Announcement",
            message="This announcement has expired",
            expires_at=past_expiration,
            created_by_id=user_id,
        )
        assert not expired_announcement.is_active()


def test_sticky_announcement(isolated_db_session):
    """Test sticky announcement."""
    # Create test user
    test_user = Usuario(
        usuario="test_usere",
        acceso=b"test_password",
        nombre="Test",
        apellido="User",
        tipo="admin",
        activo=True,
    )
    database.session.add(test_user)
    database.session.commit()

    announcement = Announcement(
        title="Sticky Announcement",
        message="This is a sticky announcement",
        is_sticky=True,
        created_by_id=test_user.usuario,
    )
    database.session.add(announcement)
    database.session.commit()

    assert announcement.is_sticky


def test_admin_announcements_list_unauthorized(app):
    """Test that unauthorized users cannot access admin announcements."""
    client = app.test_client()
    response = client.get("/admin/announcements")
    assert response.status_code == 302  # Redirect to login


def test_global_announcements_unauthorized(app):
    """Test that unauthorized users cannot access global announcements."""
    client = app.test_client()
    response = client.get("/dashboard/announcements")
    assert response.status_code == 302  # Redirect to login


def test_instructor_announcements_unauthorized(app):
    """Test that unauthorized users cannot access instructor announcements."""
    client = app.test_client()
    response = client.get("/instructor/announcements")
    assert response.status_code == 302  # Redirect to login


def test_full_announcement_workflow(isolated_db_session):
    """Test complete announcement creation and viewing workflow."""
    # First clear any existing announcements in this session
    database.session.query(Announcement).delete()
    database.session.commit()

    # Create test users and course
    admin_user = Usuario(
        usuario="admin_workflow",
        acceso=b"admin_password",
        nombre="Admin",
        apellido="User",
        tipo="admin",
        activo=True,
    )
    database.session.add(admin_user)

    instructor_user = Usuario(
        usuario="instructor_workflow",
        acceso=b"instructor_password",
        nombre="Instructor",
        apellido="User",
        tipo="instructor",
        activo=True,
    )
    database.session.add(instructor_user)

    test_course = Curso(
        nombre="Test Course",
        codigo="TEST_WORKFLOW",
        descripcion="Test course description",
        descripcion_corta="Test course",
        estado="open",
    )
    database.session.add(test_course)
    database.session.commit()

    # Assign instructor to course
    instructor_assignment = DocenteCurso(
        curso=test_course.codigo,
        usuario=instructor_user.usuario,
    )
    database.session.add(instructor_assignment)
    database.session.commit()

    # Create a global announcement
    global_announcement = Announcement(
        title="Global Test Announcement",
        message="This is a **global** announcement with markdown.",
        created_by_id=admin_user.usuario,
        creado_por=admin_user.usuario,
        is_sticky=True,
    )
    database.session.add(global_announcement)

    # Create a course announcement
    course_announcement = Announcement(
        title="Course Test Announcement",
        message="This is a course-specific announcement.",
        course_id=test_course.codigo,
        created_by_id=instructor_user.usuario,
        creado_por=instructor_user.usuario,
    )
    database.session.add(course_announcement)

    database.session.commit()

    # Verify announcements were created
    assert Announcement.query.count() == 2

    # Verify global announcement properties
    global_ann = Announcement.query.filter_by(title="Global Test Announcement").first()
    assert global_ann is not None
    assert global_ann.is_global()
    assert global_ann.is_sticky
    assert global_ann.is_active()

    # Verify course announcement properties
    course_ann = Announcement.query.filter_by(title="Course Test Announcement").first()
    assert course_ann is not None
    assert course_ann.is_course_announcement()
    assert not course_ann.is_sticky
    assert course_ann.course_id == test_course.codigo


def test_announcement_ordering(isolated_db_session):
    """Test that announcements are ordered correctly."""
    # First clear any existing announcements in this session
    database.session.query(Announcement).delete()
    database.session.commit()

    # Create test user
    admin_user = Usuario(
        usuario="admin_ordering",
        acceso=b"admin_password",
        nombre="Admin",
        apellido="User",
        tipo="admin",
        activo=True,
    )
    database.session.add(admin_user)
    database.session.commit()

    # Create multiple announcements with different timestamps
    base_time = datetime.now()

    announcements = [
        Announcement(
            title="Old Announcement",
            message="Old announcement",
            created_by_id=admin_user.usuario,
            timestamp=base_time - timedelta(hours=2),
        ),
        Announcement(
            title="Sticky Announcement",
            message="Sticky announcement",
            created_by_id=admin_user.usuario,
            is_sticky=True,
            timestamp=base_time - timedelta(hours=1),
        ),
        Announcement(
            title="New Announcement",
            message="New announcement",
            created_by_id=admin_user.usuario,
            timestamp=base_time,
        ),
    ]

    for ann in announcements:
        database.session.add(ann)
    database.session.commit()

    # Query announcements in the order they should appear
    ordered_announcements = (
        database.session.query(Announcement)
        .filter(Announcement.course_id.is_(None))
        .order_by(Announcement.is_sticky.desc(), Announcement.timestamp.desc())
        .all()
    )

    # Verify ordering: sticky first, then by timestamp desc
    titles = [ann.title for ann in ordered_announcements]
    expected_order = ["Sticky Announcement", "New Announcement", "Old Announcement"]
    assert titles == expected_order
