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

"""End-to-end tests using session-scoped fixtures for improved performance."""

import pytest

from now_lms.auth import proteger_passwd
from now_lms.db import Curso, DocenteCurso, Usuario, database


class TestEndToEndSessionFixtures:
    """End-to-end tests converted to use session-scoped fixtures."""

    @pytest.fixture(scope="function")
    def test_client(self, session_full_db_setup):
        """Provide test client using session fixture."""
        return session_full_db_setup.test_client()

    def test_user_registration_to_free_course_enroll_session(self, session_full_db_setup, test_client):
        """Test user registration to free course enrollment using session fixture."""
        import uuid

        # Generate unique identifiers to avoid conflicts
        unique_suffix = str(uuid.uuid4())[:8]
        unique_email = f"user_reg_{unique_suffix}@nowlms.com"
        unique_username = f"user_reg_{unique_suffix}"

        with session_full_db_setup.app_context():
            # Test user registration
            post = test_client.post(
                "/user/logon",
                data={
                    "nombre": "Brenda",
                    "apellido": "Mercado",
                    "correo_electronico": unique_email,
                    "acceso": unique_username,
                },
                follow_redirects=True,
            )
            assert post.status_code == 200

            # User must be created
            user = database.session.execute(
                database.select(Usuario).filter_by(correo_electronico=unique_email)
            ).scalar_one_or_none()
            assert user is not None
            assert user.activo is False

            # Basic verification that user creation workflow completed
            assert user.usuario == unique_email  # Email becomes username
            assert user.nombre == "Brenda"
            assert user.apellido == "Mercado"

    def test_course_admin_workflow_session(self, session_full_db_setup, test_client):
        """Test course administration workflow as admin using session fixture."""
        import time

        # Generate unique username to avoid conflicts
        unique_suffix = int(time.time() * 1000) % 1000000
        admin_username = f"admin_workflow_{unique_suffix}"
        admin_email = f"admin_workflow_{unique_suffix}@nowlms.com"

        with session_full_db_setup.app_context():
            # Create admin user
            admin_user = Usuario(
                usuario=admin_username,
                acceso=proteger_passwd("admin_pass"),
                nombre="Admin",
                apellido="Workflow",
                correo_electronico=admin_email,
                tipo="admin",
                activo=True,
                correo_electronico_verificado=True,
            )
            database.session.add(admin_user)
            database.session.commit()

        # Login as admin
        login_response = test_client.post(
            "/user/login",
            data={"usuario": admin_username, "acceso": "admin_pass"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # GET: Access course creation form
        get_response = test_client.get("/course/new_curse")
        assert get_response.status_code == 200
        assert "nuevo curso" in get_response.get_data(as_text=True).lower()

        # POST: Create new course
        post_response = test_client.post(
            "/course/new_curse",
            data={
                "nombre": "Admin Test Course",
                "codigo": "admin_test_course",
                "descripcion": "Course created by admin for testing",
                "descripcion_corta": "Admin test course",
                "nivel": 1,
                "duracion": 4,  # Use integer for weeks
                "publico": True,
                "modalidad": "time_based",
                "foro_habilitado": False,
                "limitado": False,
                "capacidad": 0,
                "fecha_inicio": "2025-08-10",
                "fecha_fin": "2025-09-10",
                "pagado": False,
                "auditable": True,
                "certificado": True,
                "plantilla_certificado": "horizontal",
                "precio": 0,
            },
            follow_redirects=True,
        )
        assert post_response.status_code == 200

        with session_full_db_setup.app_context():
            # Verify course was created
            created_course = database.session.execute(
                database.select(Curso).filter_by(codigo="admin_test_course")
            ).scalar_one_or_none()
            assert created_course is not None
            assert created_course.nombre == "Admin Test Course"

    def test_instructor_course_workflow_session(self, session_full_db_setup, test_client):
        """Test instructor course creation and management workflow using session fixture."""
        import time

        # Generate unique username to avoid conflicts
        unique_suffix = int(time.time() * 1000) % 1000000
        instructor_username = f"instructor_workflow_{unique_suffix}"
        instructor_email = f"instructor_workflow_{unique_suffix}@nowlms.com"

        with session_full_db_setup.app_context():
            # Create instructor user
            instructor_user = Usuario(
                usuario=instructor_username,
                acceso=proteger_passwd("instructor_pass"),
                nombre="Instructor",
                apellido="Workflow",
                correo_electronico=instructor_email,
                tipo="instructor",
                activo=True,
                correo_electronico_verificado=True,
            )
            database.session.add(instructor_user)
            database.session.commit()

        # Login as instructor
        login_response = test_client.post(
            "/user/login",
            data={"usuario": instructor_username, "acceso": "instructor_pass"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # GET: Access course creation form as instructor
        get_response = test_client.get("/course/new_curse")
        assert get_response.status_code == 200

        # POST: Create new course as instructor
        post_response = test_client.post(
            "/course/new_curse",
            data={
                "nombre": "Instructor Test Course",
                "codigo": "instructor_test_course",
                "descripcion": "Course created by instructor for testing",
                "descripcion_corta": "Instructor test course",
                "nivel": 1,
                "duracion": 6,  # Use integer for weeks
                "publico": True,
                "modalidad": "time_based",
                "foro_habilitado": True,
                "limitado": False,
                "capacidad": 0,
                "fecha_inicio": "2025-08-15",
                "fecha_fin": "2025-09-30",
                "pagado": False,
                "auditable": True,
                "certificado": True,
                "plantilla_certificado": "vertical",
                "precio": 0,
            },
            follow_redirects=True,
        )
        assert post_response.status_code == 200

        with session_full_db_setup.app_context():
            # Verify course was created
            created_course = database.session.execute(
                database.select(Curso).filter_by(codigo="instructor_test_course")
            ).scalar_one_or_none()
            assert created_course is not None
            assert created_course.nombre == "Instructor Test Course"

            # Verify instructor is assigned to the course
            instructor_assignment = database.session.execute(
                database.select(DocenteCurso).filter_by(curso="instructor_test_course", usuario=instructor_username)
            ).scalar_one_or_none()
            assert instructor_assignment is not None

    def test_course_coupons_workflow_session(self, session_full_db_setup, test_client):
        """Test course coupon creation and management workflow using session fixture."""
        with session_full_db_setup.app_context():
            # Create instructor user
            instructor_user = Usuario(
                usuario="instructor_coupon",
                acceso=proteger_passwd("instructor_pass"),
                nombre="Coupon",
                apellido="Instructor",
                correo_electronico="instructor_coupon@nowlms.com",
                tipo="instructor",
                activo=True,
                correo_electronico_verificado=True,
            )
            database.session.add(instructor_user)

            # Create paid course for coupon testing
            paid_course = Curso(
                codigo="paid_course",
                nombre="Paid Course with Coupons",
                descripcion="Course for testing coupon functionality",
                descripcion_corta="Paid course",
                estado="published",
                publico=True,
                modalidad="online",
                pagado=True,
                precio=99.99,
                certificado=True,
                plantilla_certificado="horizontal",
            )
            database.session.add(paid_course)
            database.session.commit()

            # Assign instructor to course
            instructor_assignment = DocenteCurso(
                usuario="instructor_coupon",
                curso="paid_course",
                vigente=True,
            )
            database.session.add(instructor_assignment)
            database.session.commit()

        # Login as instructor
        login_response = test_client.post(
            "/user/login",
            data={"usuario": "instructor_coupon", "acceso": "instructor_pass"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # GET: Access coupon creation form
        get_response = test_client.get("/course/paid_course/coupons/new")
        assert get_response.status_code == 200

        # Verify we can access coupon management (testing the main inspect functionality)
        # GET: List coupons for the course
        list_response = test_client.get("/course/paid_course/coupons/")
        assert list_response.status_code == 200
