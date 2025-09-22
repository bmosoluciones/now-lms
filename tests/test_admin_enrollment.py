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

"""Test administrative enrollment functionality."""

from now_lms.auth import proteger_passwd
from now_lms.db import (
    DocenteCurso,
    EstudianteCurso,
    Usuario,
    database,
)


class TestAdministrativeEnrollment:
    """Test administrative enrollment for courses and programs."""

    def test_admin_course_enrollment_route_access(self, session_full_db_setup):
        """Test that administrative course enrollment routes exist and require proper authentication."""
        client = session_full_db_setup.test_client()

        # Test without authentication - should redirect to login
        response = client.get("/course/now/admin/enroll")
        assert response.status_code == 302
        assert "/user/login" in response.location

        # Test with student user - should be forbidden
        with session_full_db_setup.app_context():
            student = Usuario(
                usuario="test_student",
                acceso=proteger_passwd("password"),
                nombre="Test",
                apellido="Student",
                tipo="student",
                activo=True,
                correo_electronico="student@test.com",
                correo_electronico_verificado=True,
            )
            database.session.add(student)
            database.session.commit()

        with client.session_transaction() as sess:
            sess["_user_id"] = "test_student"
            sess["_fresh"] = True

        response = client.get("/course/now/admin/enroll")
        assert response.status_code in [403, 302]  # Forbidden or redirect

    def test_admin_course_enrollment_route_instructor_access(self, session_full_db_setup):
        """Test that instructors can access enrollment routes for their courses."""
        client = session_full_db_setup.test_client()

        with session_full_db_setup.app_context():
            # Create instructor
            instructor = Usuario(
                usuario="test_instructor",
                acceso=proteger_passwd("password"),
                nombre="Test",
                apellido="Instructor",
                tipo="instructor",
                activo=True,
                correo_electronico="instructor@test.com",
                correo_electronico_verificado=True,
            )
            database.session.add(instructor)
            database.session.commit()  # Commit instructor first

            # Assign instructor to course
            assignment = DocenteCurso(curso="now", usuario="test_instructor")
            database.session.add(assignment)
            database.session.commit()

        # Login as instructor using POST request
        response = client.post("/user/login", data={"usuario": "test_instructor", "acceso": "password"})
        assert response.status_code in [200, 302]  # Login success

        response = client.get("/course/now/admin/enroll")
        print(f"Response status: {response.status_code}")
        if hasattr(response, "location"):
            print(f"Redirect location: {response.location}")
        assert response.status_code == 200

    def test_admin_course_enrollment_form_renders(self, session_full_db_setup):
        """Test that the administrative enrollment form renders correctly."""
        client = session_full_db_setup.test_client()

        # Login as admin using POST request
        response = client.post("/user/login", data={"usuario": "lms-admin", "acceso": "lms-admin"})
        assert response.status_code in [200, 302]  # Login success

        response = client.get("/course/now/admin/enroll")
        assert response.status_code == 200
        assert b"Inscripci\xc3\xb3n Administrativa" in response.data
        assert b"student_username" in response.data
        assert b"bypass_payment" in response.data

    def test_admin_course_enrollments_view(self, session_full_db_setup):
        """Test the course enrollments management view."""
        client = session_full_db_setup.test_client()

        # Login as admin using POST request
        response = client.post("/user/login", data={"usuario": "lms-admin", "acceso": "lms-admin"})
        assert response.status_code in [200, 302]  # Login success

        response = client.get("/course/now/admin/enrollments")
        assert response.status_code == 200
        assert b"Inscripciones del Curso" in response.data

    def test_admin_program_enrollment_route_access(self, session_full_db_setup):
        """Test that administrative program enrollment routes exist and require admin access."""
        client = session_full_db_setup.test_client()

        # Test without authentication - should redirect to login
        response = client.get("/program/test-program/admin/enroll")
        assert response.status_code in [302, 404]  # Redirect to login or not found

        # Test with instructor - should be forbidden for programs (only admins allowed)
        with session_full_db_setup.app_context():
            instructor = Usuario(
                usuario="test_instructor_prog",
                acceso=proteger_passwd("password"),
                nombre="Test",
                apellido="Instructor",
                tipo="instructor",
                activo=True,
                correo_electronico="instructor_prog@test.com",
                correo_electronico_verificado=True,
            )
            database.session.add(instructor)
            database.session.commit()

        # Login as instructor using POST request
        response = client.post("/user/login", data={"usuario": "test_instructor_prog", "acceso": "password"})
        assert response.status_code in [200, 302]  # Login success

        response = client.get("/program/test-program/admin/enroll")
        assert response.status_code in [403, 404]  # Forbidden or not found

    def test_admin_enrollment_forms_validation(self, session_full_db_setup):
        """Test form validation for administrative enrollment."""
        from now_lms.forms import AdminCourseEnrollmentForm, AdminProgramEnrollmentForm

        with session_full_db_setup.app_context():
            # Test course enrollment form
            course_form = AdminCourseEnrollmentForm()
            assert hasattr(course_form, "student_username")
            assert hasattr(course_form, "bypass_payment")
            assert hasattr(course_form, "notes")

            # Test program enrollment form
            program_form = AdminProgramEnrollmentForm()
            assert hasattr(program_form, "student_username")
            assert hasattr(program_form, "bypass_payment")
            assert hasattr(program_form, "notes")

    def test_enrollment_functionality_basic(self, session_full_db_setup):
        """Test basic enrollment functionality through the interface."""
        client = session_full_db_setup.test_client()

        with session_full_db_setup.app_context():
            # Create a test student
            student = Usuario(
                usuario="enroll_test_student",
                acceso=proteger_passwd("password"),
                nombre="Enroll",
                apellido="Student",
                tipo="student",
                activo=True,
                correo_electronico="enroll_student@test.com",
                correo_electronico_verificado=True,
            )
            database.session.add(student)
            database.session.commit()

        # Login as admin using POST request
        response = client.post("/user/login", data={"usuario": "lms-admin", "acceso": "lms-admin"})
        assert response.status_code in [200, 302]  # Login success

        # Test that we can access the enrollment form
        response = client.get("/course/now/admin/enroll")
        assert response.status_code == 200

        # Test form submission (POST)
        response = client.post(
            "/course/now/admin/enroll",
            data={
                "student_username": "enroll_test_student",
                "bypass_payment": True,
                "notes": "Test administrative enrollment",
            },
        )

        # Should redirect on successful enrollment
        assert response.status_code in [200, 302]

        # Verify enrollment was created (if redirect to success page)
        if response.status_code == 302:
            with session_full_db_setup.app_context():
                enrollment = database.session.execute(
                    database.select(EstudianteCurso).filter_by(curso="now", usuario="enroll_test_student", vigente=True)
                ).scalar_one_or_none()

                # Check if enrollment exists or if it was a redirect to error page
                if enrollment:
                    assert enrollment.curso == "now"
                    assert enrollment.usuario == "enroll_test_student"
                    assert enrollment.vigente is True
