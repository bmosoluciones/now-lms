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

"""Test instructor access to multimedia resources fix."""

from now_lms.auth import proteger_passwd
from now_lms.db import Curso, CursoRecurso, CursoSeccion, DocenteCurso, Usuario


class TestInstructorResourceAccess:
    """Test that instructors can access multimedia resources only in courses they're assigned to."""

    def create_instructor_user(self, db_session, user_id=None):
        """Create an instructor user for testing."""
        import time as time_module

        if user_id is None:
            user_id = int(time_module.time() * 1000) % 1000000

        instructor = Usuario(
            usuario=f"test_instructor_{user_id}",
            nombre="Test",
            apellido="Instructor",
            correo_electronico=f"instructor_{user_id}@test.com",
            tipo="instructor",
            activo=True,
            correo_electronico_verificado=True,
            acceso=proteger_passwd("password123"),
        )
        db_session.add(instructor)
        db_session.flush()
        return instructor

    def create_test_course(self, db_session, course_code, created_by):
        """Create a test course."""
        course = Curso(
            codigo=course_code,
            nombre=f"Test Course {course_code}",
            descripcion_corta="Course for testing instructor access",
            descripcion="Test course for instructor access testing",
            nivel=1,  # Use integer: 1 = Principiante
            duracion=4,  # Use integer for weeks
            estado="draft",
            modalidad="self_paced",
            pagado=False,
            certificado=False,
            creado_por=created_by,
        )
        db_session.add(course)
        db_session.flush()
        return course

    def create_test_resource(self, db_session, course_code, section_id, resource_type="pdf"):
        """Create a test multimedia resource."""
        resource = CursoRecurso(
            curso=course_code,
            seccion=section_id,
            nombre=f"Test {resource_type.upper()} Resource",
            descripcion=f"Test {resource_type} for access testing",
            tipo=resource_type,
            indice=1,
            publico=False,
            requerido="required",
        )
        if resource_type == "pdf":
            resource.doc = "test.pdf"
        elif resource_type == "mp3":
            resource.doc = "test.mp3"

        db_session.add(resource)
        db_session.flush()
        return resource

    def get_authenticated_client(self, app, user):
        """Get an authenticated test client."""
        client = app.test_client()
        with app.app_context():
            login_data = {"usuario": user.usuario, "acceso": "password123"}
            client.post("/user/login", data=login_data, follow_redirects=True)
        return client

    def test_instructor_can_access_assigned_course_pdf_resource(self, session_full_db_setup, isolated_db_session):
        """Test that an instructor can access PDF resources in courses they're assigned to."""
        import time
        unique_id = int(time.time() * 1000) % 1000000
        
        # Create instructor
        instructor = self.create_instructor_user(isolated_db_session, unique_id)

        # Create course with unique code
        course_code = f"TEST{unique_id}_PDF"
        course = self.create_test_course(isolated_db_session, course_code, instructor.usuario)

        # Create section
        section = CursoSeccion(
            curso=course.codigo,
            nombre="Test Section",
            descripcion="Test section for resource access",
            indice=1,
        )
        isolated_db_session.add(section)
        isolated_db_session.flush()

        # Create PDF resource
        resource = self.create_test_resource(isolated_db_session, course.codigo, section.id, "pdf")

        # Assign instructor to course
        assignment = DocenteCurso(
            curso=course.codigo,
            usuario=instructor.usuario,
            vigente=True,
        )
        isolated_db_session.add(assignment)
        isolated_db_session.commit()

        # Test access
        client = self.get_authenticated_client(session_full_db_setup, instructor)
        with session_full_db_setup.app_context():
            response = client.get(f"/course/{course.codigo}/resource/pdf/{resource.id}")
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            assert "Test PDF Resource" in response.get_data(as_text=True)

    def test_instructor_can_access_assigned_course_audio_resource(self, session_full_db_setup, isolated_db_session):
        """Test that an instructor can access audio resources in courses they're assigned to."""
        import time
        unique_id = int(time.time() * 1000) % 1000000
        
        # Create instructor
        instructor = self.create_instructor_user(isolated_db_session, unique_id)

        # Create course with unique code
        course_code = f"TEST{unique_id}_MP3"
        course = self.create_test_course(isolated_db_session, course_code, instructor.usuario)

        # Create section
        section = CursoSeccion(
            curso=course.codigo,
            nombre="Test Audio Section",
            descripcion="Test section for audio resource access",
            indice=1,
        )
        isolated_db_session.add(section)
        isolated_db_session.flush()

        # Create audio resource
        resource = self.create_test_resource(isolated_db_session, course.codigo, section.id, "mp3")

        # Assign instructor to course
        assignment = DocenteCurso(
            curso=course.codigo,
            usuario=instructor.usuario,
            vigente=True,
        )
        isolated_db_session.add(assignment)
        isolated_db_session.commit()

        # Test access
        client = self.get_authenticated_client(session_full_db_setup, instructor)
        with session_full_db_setup.app_context():
            response = client.get(f"/course/{course.codigo}/resource/mp3/{resource.id}")
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            assert "Test MP3 Resource" in response.get_data(as_text=True)

    def test_instructor_cannot_access_unassigned_course_resource(self, session_full_db_setup, isolated_db_session):
        """Test that an instructor cannot access resources in courses they're NOT assigned to."""
        import time
        unique_id = int(time.time() * 1000) % 1000000
        
        # Create two instructors
        instructor1 = self.create_instructor_user(isolated_db_session, unique_id)
        instructor2 = self.create_instructor_user(isolated_db_session, unique_id + 1)

        # Create course owned by instructor1 with unique code
        course_code = f"TEST{unique_id}_UNAUTH"
        course = self.create_test_course(isolated_db_session, course_code, instructor1.usuario)

        # Create section
        section = CursoSeccion(
            curso=course.codigo,
            nombre="Test Section",
            descripcion="Test section for access control",
            indice=1,
        )
        isolated_db_session.add(section)
        isolated_db_session.flush()

        # Create PDF resource
        resource = self.create_test_resource(isolated_db_session, course.codigo, section.id, "pdf")

        # Assign ONLY instructor1 to course (not instructor2)
        assignment = DocenteCurso(
            curso=course.codigo,
            usuario=instructor1.usuario,  # Only instructor1 is assigned
            vigente=True,
        )
        isolated_db_session.add(assignment)
        isolated_db_session.commit()

        # Test that instructor1 (assigned) CAN access
        client1 = self.get_authenticated_client(session_full_db_setup, instructor1)
        with session_full_db_setup.app_context():
            response1 = client1.get(f"/course/{course.codigo}/resource/pdf/{resource.id}")
            assert response1.status_code == 200, f"Assigned instructor should have access, got {response1.status_code}"

        # Test that instructor2 (NOT assigned) CANNOT access
        client2 = self.get_authenticated_client(session_full_db_setup, instructor2)
        with session_full_db_setup.app_context():
            response2 = client2.get(f"/course/{course.codigo}/resource/pdf/{resource.id}")
            # The resource should not be shown (permission denied)
            assert response2.status_code != 200, f"Unassigned instructor should not have access, got {response2.status_code}"

    def test_admin_can_access_any_course_resource(self, session_full_db_setup, isolated_db_session):
        """Test that admin users can access any course resource regardless of assignment."""
        import time
        unique_id = int(time.time() * 1000) % 1000000
        
        # Create instructor and admin
        instructor = self.create_instructor_user(isolated_db_session, unique_id)
        admin = Usuario(
            usuario=f"test_admin_{unique_id}",
            nombre="Test",
            apellido="Admin",
            correo_electronico=f"admin_{unique_id}@test.com",
            tipo="admin",
            activo=True,
            correo_electronico_verificado=True,
            acceso=proteger_passwd("password123"),
        )
        isolated_db_session.add(admin)
        isolated_db_session.flush()

        # Create course assigned only to instructor with unique code
        course_code = f"TEST{unique_id}_ADMIN"
        course = self.create_test_course(isolated_db_session, course_code, instructor.usuario)

        # Create section
        section = CursoSeccion(
            curso=course.codigo,
            nombre="Test Section",
            descripcion="Test section for admin access",
            indice=1,
        )
        isolated_db_session.add(section)
        isolated_db_session.flush()

        # Create PDF resource
        resource = self.create_test_resource(isolated_db_session, course.codigo, section.id, "pdf")

        # Assign ONLY instructor to course (not admin)
        assignment = DocenteCurso(
            curso=course.codigo,
            usuario=instructor.usuario,
            vigente=True,
        )
        isolated_db_session.add(assignment)
        isolated_db_session.commit()

        # Test that admin can still access without being assigned
        admin_client = self.get_authenticated_client(session_full_db_setup, admin)
        with session_full_db_setup.app_context():
            response = admin_client.get(f"/course/{course.codigo}/resource/pdf/{resource.id}")
            assert response.status_code == 200, f"Admin should have access to any resource, got {response.status_code}"
