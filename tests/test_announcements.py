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

from unittest import TestCase
from datetime import datetime, timedelta

from now_lms import app
from now_lms.db import eliminar_base_de_datos_segura
from now_lms.db import Announcement, Curso, Usuario, DocenteCurso, database


class TestAnnouncementsModel(TestCase):
    """Test the Announcement model."""

    def setUp(self):
        """Set up test environment."""
        self.app = app
        self.app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        self.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        self.app.app_context().push()
        database.create_all()

        # Create test user
        self.test_user = Usuario(
            usuario="test_usera",
            acceso=b"test_password",
            nombre="Test",
            apellido="User",
            tipo="admin",
            activo=True,
        )
        database.session.add(self.test_user)
        database.session.commit()

    def tearDown(self):
        """Clean up after tests."""
        database.session.remove()
        eliminar_base_de_datos_segura()
        database.session.close()

    def test_announcement_creation(self):
        """Test creating an announcement."""
        announcement = Announcement(
            title="Test Announcement",
            message="This is a test announcement",
            created_by_id=self.test_user.usuario,
        )
        database.session.add(announcement)
        database.session.commit()

        self.assertIsNotNone(announcement.id)
        self.assertEqual(announcement.title, "Test Announcement")
        self.assertEqual(announcement.message, "This is a test announcement")
        self.assertEqual(announcement.created_by_id, self.test_user.usuario)
        self.assertIsNone(announcement.course_id)
        self.assertFalse(announcement.is_sticky)

    def test_global_announcement(self):
        """Test that announcement without course_id is global."""
        announcement = Announcement(
            title="Global Announcement",
            message="This is a global announcement",
            created_by_id=self.test_user.usuario,
        )
        database.session.add(announcement)
        database.session.commit()

        self.assertTrue(announcement.is_global())
        self.assertFalse(announcement.is_course_announcement())

    def test_course_announcement(self):
        """Test course announcement."""
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
            created_by_id=self.test_user.usuario,
        )
        database.session.add(announcement)
        database.session.commit()

        self.assertFalse(announcement.is_global())
        self.assertTrue(announcement.is_course_announcement())
        self.assertEqual(announcement.course_id, course.codigo)

    def test_announcement_expiration(self):
        """Test announcement expiration logic."""
        # Active announcement (no expiration)
        active_announcement = Announcement(
            title="Active Announcement",
            message="This announcement never expires",
            created_by_id=self.test_user.usuario,
        )
        self.assertTrue(active_announcement.is_active())

        # Active announcement (future expiration)
        future_expiration = datetime.now() + timedelta(days=1)
        future_announcement = Announcement(
            title="Future Announcement",
            message="This announcement expires tomorrow",
            expires_at=future_expiration,
            created_by_id=self.test_user.usuario,
        )
        self.assertTrue(future_announcement.is_active())

        # Expired announcement
        past_expiration = datetime.now() - timedelta(days=1)
        expired_announcement = Announcement(
            title="Expired Announcement",
            message="This announcement has expired",
            expires_at=past_expiration,
            created_by_id=self.test_user.usuario,
        )
        self.assertFalse(expired_announcement.is_active())

    def test_sticky_announcement(self):
        """Test sticky announcement."""
        announcement = Announcement(
            title="Sticky Announcement",
            message="This is a sticky announcement",
            is_sticky=True,
            created_by_id=self.test_user.usuario,
        )
        database.session.add(announcement)
        database.session.commit()

        self.assertTrue(announcement.is_sticky)


class TestAnnouncementsViews(TestCase):
    """Test announcement views."""

    def setUp(self):
        """Set up test environment."""
        self.app = app
        self.app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        self.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        self.app.config["TESTING"] = True
        self.app.config["WTF_CSRF_ENABLED"] = False

        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

        database.create_all()

        # Create test admin user
        self.admin_user = Usuario(
            usuario="admin",
            acceso=b"admin_password",
            nombre="Admin",
            apellido="User",
            tipo="admin",
            activo=True,
        )
        database.session.add(self.admin_user)

        # Create test instructor user
        self.instructor_user = Usuario(
            usuario="instructor",
            acceso=b"instructor_password",
            nombre="Instructor",
            apellido="User",
            tipo="instructor",
            activo=True,
        )
        database.session.add(self.instructor_user)

        # Create test student user
        self.student_user = Usuario(
            usuario="student",
            acceso=b"student_password",
            nombre="Student",
            apellido="User",
            tipo="user",
            activo=True,
        )
        database.session.add(self.student_user)

        # Create test course
        self.test_course = Curso(
            nombre="Test Course",
            codigo="TEST01",
            descripcion="Test course description",
            descripcion_corta="Test course",
            estado="open",
        )
        database.session.add(self.test_course)

        database.session.commit()

    def tearDown(self):
        """Clean up after tests."""
        database.session.remove()
        eliminar_base_de_datos_segura()
        database.session.close()
        self.app_context.pop()

    def test_admin_announcements_list_unauthorized(self):
        """Test that unauthorized users cannot access admin announcements."""
        response = self.client.get("/admin/announcements")
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_global_announcements_unauthorized(self):
        """Test that unauthorized users cannot access global announcements."""
        response = self.client.get("/dashboard/announcements")
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_instructor_announcements_unauthorized(self):
        """Test that unauthorized users cannot access instructor announcements."""
        response = self.client.get("/instructor/announcements")
        self.assertEqual(response.status_code, 302)  # Redirect to login


class TestAnnouncementsIntegration(TestCase):
    """Integration tests for announcements functionality."""

    def setUp(self):
        """Set up test environment."""
        self.app = app
        self.app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        self.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        self.app.config["TESTING"] = True
        self.app.config["WTF_CSRF_ENABLED"] = False

        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

        database.create_all()

        # Create test users and course
        self.admin_user = Usuario(
            usuario="admin",
            acceso=b"admin_password",
            nombre="Admin",
            apellido="User",
            tipo="admin",
            activo=True,
        )
        database.session.add(self.admin_user)

        self.instructor_user = Usuario(
            usuario="instructor",
            acceso=b"instructor_password",
            nombre="Instructor",
            apellido="User",
            tipo="instructor",
            activo=True,
        )
        database.session.add(self.instructor_user)

        self.test_course = Curso(
            nombre="Test Course",
            codigo="TEST01",
            descripcion="Test course description",
            descripcion_corta="Test course",
            estado="open",
        )
        database.session.add(self.test_course)
        database.session.commit()

        # Assign instructor to course
        instructor_assignment = DocenteCurso(
            curso=self.test_course.codigo,
            usuario=self.instructor_user.usuario,
        )
        database.session.add(instructor_assignment)

        database.session.commit()

    def tearDown(self):
        """Clean up after tests."""
        database.session.remove()
        eliminar_base_de_datos_segura()
        database.session.close()
        self.app_context.pop()

    def test_full_announcement_workflow(self):
        """Test complete announcement creation and viewing workflow."""
        # Create a global announcement
        global_announcement = Announcement(
            title="Global Test Announcement",
            message="This is a **global** announcement with markdown.",
            created_by_id=self.admin_user.usuario,
            creado_por=self.admin_user.usuario,
            is_sticky=True,
        )
        database.session.add(global_announcement)

        # Create a course announcement
        course_announcement = Announcement(
            title="Course Test Announcement",
            message="This is a course-specific announcement.",
            course_id=self.test_course.codigo,
            created_by_id=self.instructor_user.usuario,
            creado_por=self.instructor_user.usuario,
        )
        database.session.add(course_announcement)

        database.session.commit()

        # Verify announcements were created
        self.assertEqual(Announcement.query.count(), 2)

        # Verify global announcement properties
        global_ann = Announcement.query.filter_by(title="Global Test Announcement").first()
        self.assertIsNotNone(global_ann)
        self.assertTrue(global_ann.is_global())
        self.assertTrue(global_ann.is_sticky)
        self.assertTrue(global_ann.is_active())

        # Verify course announcement properties
        course_ann = Announcement.query.filter_by(title="Course Test Announcement").first()
        self.assertIsNotNone(course_ann)
        self.assertTrue(course_ann.is_course_announcement())
        self.assertFalse(course_ann.is_sticky)
        self.assertEqual(course_ann.course_id, self.test_course.codigo)

    def test_announcement_ordering(self):
        """Test that announcements are ordered correctly."""
        # Create multiple announcements with different timestamps
        from datetime import datetime, timedelta

        base_time = datetime.now()

        announcements = [
            Announcement(
                title="Old Announcement",
                message="Old announcement",
                created_by_id=self.admin_user.usuario,
                timestamp=base_time - timedelta(hours=2),
            ),
            Announcement(
                title="Sticky Announcement",
                message="Sticky announcement",
                created_by_id=self.admin_user.usuario,
                is_sticky=True,
                timestamp=base_time - timedelta(hours=1),
            ),
            Announcement(
                title="New Announcement",
                message="New announcement",
                created_by_id=self.admin_user.usuario,
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
        self.assertEqual(titles, expected_order)
