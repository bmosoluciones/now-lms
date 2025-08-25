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

"""End-to-end tests for course inspect functionality using session-scoped fixtures."""

import pytest

from now_lms.auth import proteger_passwd
from now_lms.db import Curso, DocenteCurso, Usuario, database


class TestCourseInspectEndToEnd:
    """Test course inspect functionality with admin and instructor users."""

    @pytest.fixture(scope="function")
    def test_client(self, session_full_db_setup):
        """Provide test client using session fixture."""
        return session_full_db_setup.test_client()

    def test_admin_inspect_access_any_course(self, session_full_db_setup, test_client):
        """Test that admin can access any course with ?inspect=1 parameter (lines 175-177)."""
        with session_full_db_setup.app_context():
            # Create admin user
            admin_user = Usuario(
                usuario="admin_inspect",
                acceso=proteger_passwd("admin_pass"),
                nombre="Admin",
                apellido="Inspect",
                correo_electronico="admin_inspect@nowlms.com",
                tipo="admin",
                activo=True,
                correo_electronico_verificado=True,
            )
            database.session.add(admin_user)

            # Create a test course
            test_course = Curso(
                codigo="inspect_course",
                nombre="Course for Inspect Testing",
                descripcion="Test course for inspect functionality",
                descripcion_corta="Inspect test",
                estado="published",
                publico=False,  # Non-public course to test admin access
                modalidad="online",
                pagado=False,
                precio=0,
                certificado=True,
                plantilla_certificado="horizontal",
            )
            database.session.add(test_course)
            database.session.commit()

        # Login as admin
        login_response = test_client.post(
            "/user/login",
            data={"usuario": "admin_inspect", "acceso": "admin_pass"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # Access course with inspect parameter - should work for admin
        inspect_response = test_client.get("/course/inspect_course/view?inspect=1")
        assert inspect_response.status_code == 200

        # Verify course content is accessible
        content = inspect_response.get_data(as_text=True)
        assert "Course for Inspect Testing" in content

    def test_instructor_inspect_access_own_course(self, session_full_db_setup, test_client):
        """Test that instructor can access their own course with ?inspect=1 parameter (lines 179-184)."""
        with session_full_db_setup.app_context():
            # Create instructor user
            instructor_user = Usuario(
                usuario="instructor_inspect",
                acceso=proteger_passwd("instructor_pass"),
                nombre="Instructor",
                apellido="Inspect",
                correo_electronico="instructor_inspect@nowlms.com",
                tipo="instructor",
                activo=True,
                correo_electronico_verificado=True,
            )
            database.session.add(instructor_user)

            # Create a test course
            instructor_course = Curso(
                codigo="instructor_course",
                nombre="Instructor's Course",
                descripcion="Course taught by instructor",
                descripcion_corta="Instructor course",
                estado="published",
                publico=False,
                modalidad="online",
                pagado=False,
                precio=0,
                certificado=True,
                plantilla_certificado="horizontal",
            )
            database.session.add(instructor_course)
            database.session.commit()  # Commit users and courses first

            # Assign instructor to course
            instructor_assignment = DocenteCurso(
                usuario="instructor_inspect",
                curso="instructor_course",
                vigente=True,
            )
            database.session.add(instructor_assignment)
            database.session.commit()

        # Login as instructor
        login_response = test_client.post(
            "/user/login",
            data={"usuario": "instructor_inspect", "acceso": "instructor_pass"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # Try access without inspect parameter first - should fail
        normal_response = test_client.get("/course/instructor_course/view")
        assert normal_response.status_code == 403  # Should be forbidden

        # Access own course with inspect parameter - should work
        inspect_response = test_client.get("/course/instructor_course/view?inspect=1")
        assert inspect_response.status_code == 200  # Should be allowed

        # Verify we're getting a successful course page (has HTML structure)
        content = inspect_response.get_data(as_text=True)
        assert "<html" in content  # Basic HTML structure check
        assert "</html>" in content

    def test_instructor_inspect_access_non_assigned_course(self, session_full_db_setup, test_client):
        """Test that instructor cannot access non-assigned course with ?inspect=1 parameter (lines 185-186)."""
        with session_full_db_setup.app_context():
            # Create instructor user
            instructor_user = Usuario(
                usuario="instructor_no_access",
                acceso=proteger_passwd("instructor_pass"),
                nombre="Instructor",
                apellido="NoAccess",
                correo_electronico="instructor_no_access@nowlms.com",
                tipo="instructor",
                activo=True,
                correo_electronico_verificado=True,
            )
            database.session.add(instructor_user)

            # Create a test course NOT assigned to instructor
            other_course = Curso(
                codigo="other_course",
                nombre="Other Course",
                descripcion="Course not assigned to instructor",
                descripcion_corta="Other course",
                estado="published",
                publico=False,
                modalidad="online",
                pagado=False,
                precio=0,
                certificado=True,
                plantilla_certificado="horizontal",
            )
            database.session.add(other_course)
            database.session.commit()

        # Login as instructor
        login_response = test_client.post(
            "/user/login",
            data={"usuario": "instructor_no_access", "acceso": "instructor_pass"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # Try to access non-assigned course with inspect parameter - should fail
        inspect_response = test_client.get("/course/other_course/view?inspect=1")
        assert inspect_response.status_code == 403  # Access forbidden

    def test_student_inspect_parameter_ignored(self, session_full_db_setup, test_client):
        """Test that student users cannot use inspect parameter for special access."""
        with session_full_db_setup.app_context():
            # Create student user
            student_user = Usuario(
                usuario="student_inspect",
                acceso=proteger_passwd("student_pass"),
                nombre="Student",
                apellido="Inspect",
                correo_electronico="student_inspect@nowlms.com",
                tipo="student",
                activo=True,
                correo_electronico_verificado=True,
            )
            database.session.add(student_user)

            # Create a non-public test course
            private_course = Curso(
                codigo="private_course",
                nombre="Private Course",
                descripcion="Private course for testing",
                descripcion_corta="Private course",
                estado="published",
                publico=False,  # Private course
                modalidad="online",
                pagado=False,
                precio=0,
                certificado=True,
                plantilla_certificado="horizontal",
            )
            database.session.add(private_course)
            database.session.commit()

        # Login as student
        login_response = test_client.post(
            "/user/login",
            data={"usuario": "student_inspect", "acceso": "student_pass"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # Try to access private course with inspect parameter - should fail
        inspect_response = test_client.get("/course/private_course/view?inspect=1")
        assert inspect_response.status_code == 403  # Access forbidden

    def test_unauthenticated_inspect_parameter_ignored(self, session_full_db_setup, test_client):
        """Test that unauthenticated users cannot use inspect parameter."""
        with session_full_db_setup.app_context():
            # Create a non-public test course
            private_course = Curso(
                codigo="public_inspect_course",
                nombre="Public Inspect Course",
                descripcion="Course for testing unauthenticated inspect",
                descripcion_corta="Public inspect course",
                estado="published",
                publico=False,  # Private course
                modalidad="online",
                pagado=False,
                precio=0,
                certificado=True,
                plantilla_certificado="horizontal",
            )
            database.session.add(private_course)
            database.session.commit()

        # Try to access course with inspect parameter without authentication
        inspect_response = test_client.get("/course/public_inspect_course/view?inspect=1")
        assert inspect_response.status_code == 403  # Access forbidden
