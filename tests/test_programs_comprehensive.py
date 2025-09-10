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

"""Comprehensive tests for programs.py views using session-scoped fixtures for improved performance."""

import io
import time
from unittest.mock import patch

import pytest

from now_lms.auth import proteger_passwd
from now_lms.db import (
    Categoria,
    CategoriaPrograma,
    CertificacionPrograma,
    Curso,
    Etiqueta,
    EtiquetaPrograma,
    Programa,
    ProgramaCurso,
    ProgramaEstudiante,
    Usuario,
    database,
)


class TestProgramsComprehensive:
    """Comprehensive tests for programs.py views using session-scoped fixtures."""

    @staticmethod
    def _unique_code(base="TEST"):
        """Generate unique code based on timestamp to avoid conflicts."""
        return f"{base}{int(time.time() * 1000) % 1000000}"

    @staticmethod
    def _unique_email(base="test", domain="nowlms.com"):
        """Generate unique email address to avoid conflicts."""
        return f"{base}{int(time.time() * 1000) % 1000000}@{domain}"

    @staticmethod
    def _unique_username(base="test_user"):
        """Generate unique username to avoid conflicts."""
        return f"{base}{int(time.time() * 1000) % 1000000}"

    @pytest.fixture(scope="function")
    def test_client(self, session_full_db_setup):
        """Provide test client using session fixture."""
        return session_full_db_setup.test_client()

    @pytest.fixture(scope="function")
    def isolated_db_session(self, session_full_db_setup):
        """Provide isolated database session for data modification within tests."""
        with session_full_db_setup.app_context():
            # Create a savepoint that we can rollback to
            connection = database.engine.connect()
            trans = connection.begin()

            # Configure session to use this transaction
            database.session.configure(bind=connection)

            yield database.session

            # Rollback to clean state
            trans.rollback()
            connection.close()
            database.session.remove()

    def test_nuevo_programa_get(self, session_full_db_setup, test_client):
        """Test GET request to nuevo_programa route."""
        # Login as instructor
        login_response = test_client.post(
            "/user/login",
            data={"usuario": "lms-admin", "acceso": "lms-admin"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # Test GET request
        response = test_client.get("/program/new")
        assert response.status_code == 200
        assert b"Crear Programa" in response.data or b"programa" in response.data.lower()

    def test_nuevo_programa_post_success(self, session_full_db_setup, test_client, isolated_db_session):
        """Test successful POST request to nuevo_programa route."""
        # Login as instructor
        login_response = test_client.post(
            "/user/login",
            data={"usuario": "lms-admin", "acceso": "lms-admin"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # Use unique code to avoid conflicts
        unique_code = self._unique_code("TEST")

        # Test POST request
        response = test_client.post(
            "/program/new",
            data={
                "nombre": "Test Program",
                "descripcion": "Test program description",
                "codigo": unique_code,
                "precio": "100",
                "certificado": True,
                "plantilla_certificado": "default",
            },
            follow_redirects=False,
        )
        assert response.status_code == 302  # Redirect after creation

        # Verify program was created
        programa = isolated_db_session.execute(database.select(Programa).filter_by(codigo=unique_code)).scalar_one_or_none()
        assert programa is not None
        assert programa.nombre == "Test Program"
        assert programa.estado == "draft"
        assert programa.publico is False

    def test_nuevo_programa_with_category_and_tags(self, session_full_db_setup, test_client, isolated_db_session):
        """Test creating programa with category and tags."""
        # Login as instructor
        login_response = test_client.post(
            "/user/login",
            data={"usuario": "lms-admin", "acceso": "lms-admin"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # Get available categories and tags
        with session_full_db_setup.app_context():
            categoria = isolated_db_session.execute(database.select(Categoria)).scalars().first()
            etiqueta = isolated_db_session.execute(database.select(Etiqueta)).scalars().first()

        # Use unique code to avoid conflicts
        unique_code = self._unique_code("TESTTAGS")

        # Test POST request with category and tags
        response = test_client.post(
            "/program/new",
            data={
                "nombre": "Test Program with Tags",
                "descripcion": "Test program with category and tags",
                "codigo": unique_code,
                "precio": "0",
                "categoria": str(categoria.id) if categoria else "",
                "etiquetas": [str(etiqueta.id)] if etiqueta else [],
            },
            follow_redirects=False,
        )
        assert response.status_code == 302

        # Verify program and associations were created
        programa = isolated_db_session.execute(database.select(Programa).filter_by(codigo=unique_code)).scalar_one_or_none()
        assert programa is not None

        if categoria:
            cat_prog = isolated_db_session.execute(
                database.select(CategoriaPrograma).filter_by(programa=programa.id)
            ).scalar_one_or_none()
            assert cat_prog is not None

        if etiqueta:
            tag_prog = isolated_db_session.execute(
                database.select(EtiquetaPrograma).filter_by(programa=programa.id)
            ).scalar_one_or_none()
            assert tag_prog is not None

    def test_nuevo_programa_operational_error(self, session_full_db_setup, test_client):
        """Test operational error handling in nuevo_programa."""
        # Login as instructor
        login_response = test_client.post(
            "/user/login",
            data={"usuario": "lms-admin", "acceso": "lms-admin"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # Mock OperationalError on the database session commit
        from sqlalchemy.exc import OperationalError

        with patch(
            "now_lms.vistas.programs.database.session.commit", side_effect=OperationalError("Database error", None, None)
        ):
            response = test_client.post(
                "/program/new",
                data={
                    "nombre": "Error Test Program",
                    "descripcion": "Test error handling",
                    "codigo": self._unique_code("ERROR123"),
                    "precio": "0",
                },
                follow_redirects=True,
            )
            assert response.status_code == 200
            # Check that we're redirected back to program list or see an error message
            assert (
                b"/program/list" in response.data or b"error" in response.data.lower() or b"problema" in response.data.lower()
            )

    def test_programas_list_admin(self, session_full_db_setup, test_client):
        """Test programas list view as admin."""
        # Login as admin
        login_response = test_client.post(
            "/user/login",
            data={"usuario": "lms-admin", "acceso": "lms-admin"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # Test list view
        response = test_client.get("/program/list")
        assert response.status_code == 200

    def test_programas_list_instructor(self, session_full_db_setup, test_client, isolated_db_session):
        """Test programas list view as instructor (filtered by creator)."""
        import time

        # Create instructor user with unique identifier
        unique_id = int(time.time() * 1000) % 1000000
        instructor = Usuario(
            usuario=f"test_instructor_{unique_id}",
            acceso=proteger_passwd("testpass"),
            nombre="Test",
            apellido="Instructor",
            correo_electronico=f"instructor_test_{unique_id}@test.com",
            tipo="instructor",
            activo=True,
            correo_electronico_verificado=True,
        )
        isolated_db_session.add(instructor)
        isolated_db_session.commit()

        # Login as instructor
        login_response = test_client.post(
            "/user/login",
            data={"usuario": f"test_instructor_{unique_id}", "acceso": "testpass"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # Test list view (should only show instructor's programs)
        response = test_client.get("/program/list")
        assert response.status_code == 200

    def test_delete_program_admin(self, session_full_db_setup, test_client, isolated_db_session):
        """Test program deletion as admin."""
        # Create test program
        programa = Programa(
            nombre="Program to Delete",
            codigo=self._unique_code("DELETE"),
            descripcion="Test program for deletion",
            creado_por="admin",
        )
        isolated_db_session.add(programa)
        isolated_db_session.commit()
        program_id = programa.id

        # Login as admin
        login_response = test_client.post(
            "/user/login",
            data={"usuario": "lms-admin", "acceso": "lms-admin"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # Test deletion
        response = test_client.get(f"/program/{program_id}/delete", follow_redirects=False)
        assert response.status_code == 302  # Redirect after deletion

        # Verify program was deleted
        deleted_program = isolated_db_session.execute(database.select(Programa).filter_by(id=program_id)).scalar_one_or_none()
        assert deleted_program is None

    def test_delete_program_non_admin(self, session_full_db_setup, test_client, isolated_db_session):
        """Test program deletion as non-admin (should be forbidden)."""
        # Create instructor user
        instructor = Usuario(
            usuario="test_instructor2",
            acceso=proteger_passwd("testpass"),
            nombre="Test",
            apellido="Instructor",
            correo_electronico="instructor2@test.com",
            tipo="instructor",
            activo=True,
            correo_electronico_verificado=True,
        )
        isolated_db_session.add(instructor)
        isolated_db_session.commit()

        # Login as instructor
        login_response = test_client.post(
            "/user/login",
            data={"usuario": "test_instructor2", "acceso": "testpass"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # Test deletion (should be forbidden)
        response = test_client.get("/program/fake_id/delete")
        assert response.status_code == 403

    def test_edit_program_get(self, session_full_db_setup, test_client, isolated_db_session):
        """Test GET request to edit_program route."""
        # Create test program
        programa = Programa(
            nombre="Program to Edit",
            codigo=self._unique_code("EDIT123"),
            descripcion="Test program for editing",
            precio=100,
            estado="draft",
            creado_por="admin",
        )
        isolated_db_session.add(programa)
        isolated_db_session.commit()
        program_id = programa.id

        # Login as admin
        login_response = test_client.post(
            "/user/login",
            data={"usuario": "lms-admin", "acceso": "lms-admin"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # Test GET request
        response = test_client.get(f"/program/{program_id}/edit")
        assert response.status_code == 200
        assert b"Program to Edit" in response.data

    def test_edit_program_post_success(self, session_full_db_setup, test_client, isolated_db_session):
        """Test successful POST request to edit_program route."""
        # Create test program with courses
        programa_codigo = self._unique_code("EDITPOST")
        programa = Programa(
            nombre="Program to Edit",
            codigo=programa_codigo,
            descripcion="Test program for editing",
            precio=100,
            estado="draft",
            publico=False,
            creado_por="admin",
        )
        isolated_db_session.add(programa)

        # Create a course to add to program
        curso_codigo = self._unique_code("TESTCOURSE")
        curso = Curso(
            nombre="Test Course",
            codigo=curso_codigo,
            descripcion="Test course",
            descripcion_corta="Test",
            nivel=1,
            duracion=2,
            estado="published",
            publico=True,
            modalidad="online",
            creado_por="admin",
        )
        isolated_db_session.add(curso)
        isolated_db_session.commit()

        # Add course to program using actual generated codes
        prog_curso = ProgramaCurso(programa=programa_codigo, curso=curso_codigo)
        isolated_db_session.add(prog_curso)
        isolated_db_session.commit()

        program_id = programa.id

        # Login as admin
        login_response = test_client.post(
            "/user/login",
            data={"usuario": "lms-admin", "acceso": "lms-admin"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # Test POST request
        response = test_client.post(
            f"/program/{program_id}/edit",
            data={
                "nombre": "Updated Program Name",
                "descripcion": "Updated description",
                "precio": "150",
                "publico": True,
                "estado": "open",
                "promocionado": False,
                "certificado": True,
                "plantilla_certificado": "default",
            },
            follow_redirects=False,
        )
        assert response.status_code == 302

        # Verify program was updated
        updated_program = isolated_db_session.execute(database.select(Programa).filter_by(id=program_id)).scalar_one()
        assert updated_program.nombre == "Updated Program Name"
        assert updated_program.precio == 150
        assert updated_program.publico is True
        assert updated_program.estado == "open"

    def test_edit_program_validation_no_courses_public(self, session_full_db_setup, test_client, isolated_db_session):
        """Test edit program validation when trying to make public with no courses."""
        # Create test program without courses
        programa = Programa(
            nombre="Program No Courses",
            codigo=self._unique_code("NOCOURSES"),
            descripcion="Test program without courses",
            precio=100,
            estado="draft",
            publico=False,
            creado_por="admin",
        )
        isolated_db_session.add(programa)
        isolated_db_session.commit()
        program_id = programa.id

        # Login as admin
        login_response = test_client.post(
            "/user/login",
            data={"usuario": "lms-admin", "acceso": "lms-admin"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # Try to make program public without courses
        response = test_client.post(
            f"/program/{program_id}/edit",
            data={
                "nombre": "Program No Courses",
                "descripcion": "Test program without courses",
                "precio": "100",
                "publico": True,  # This should fail
                "estado": "draft",
                "promocionado": False,
                "certificado": False,
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"no tiene cursos" in response.data or b"no courses" in response.data

        # Verify program remains non-public
        updated_program = isolated_db_session.execute(database.select(Programa).filter_by(id=program_id)).scalar_one()
        assert updated_program.publico is False

    def test_edit_program_validation_no_courses_open(self, session_full_db_setup, test_client, isolated_db_session):
        """Test edit program validation when trying to open with no courses."""
        # Create test program without courses
        programa = Programa(
            nombre="Program No Courses Open",
            codigo=self._unique_code("NOCOURSESOPEN"),
            descripcion="Test program without courses",
            precio=100,
            estado="draft",
            publico=False,
            creado_por="admin",
        )
        isolated_db_session.add(programa)
        isolated_db_session.commit()
        program_id = programa.id

        # Login as admin
        login_response = test_client.post(
            "/user/login",
            data={"usuario": "lms-admin", "acceso": "lms-admin"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # Try to open program without courses
        response = test_client.post(
            f"/program/{program_id}/edit",
            data={
                "nombre": "Program No Courses Open",
                "descripcion": "Test program without courses",
                "precio": "100",
                "publico": False,
                "estado": "open",  # This should fail
                "promocionado": False,
                "certificado": False,
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"no tiene cursos" in response.data or b"no courses" in response.data

        # Verify program remains draft
        updated_program = isolated_db_session.execute(database.select(Programa).filter_by(id=program_id)).scalar_one()
        assert updated_program.estado == "draft"

    def test_edit_program_non_admin(self, session_full_db_setup, test_client, isolated_db_session):
        """Test edit program as non-admin (should be forbidden)."""
        # Create test program first
        programa = Programa(
            nombre="Program for Non-Admin Test",
            codigo=self._unique_code("NONADMIN"),
            descripcion="Test program for non-admin access",
            precio=100,
            estado="draft",
            creado_por="admin",
        )
        isolated_db_session.add(programa)
        isolated_db_session.commit()
        program_id = programa.id

        # Create instructor user
        instructor = Usuario(
            usuario="test_instructor3",
            acceso=proteger_passwd("testpass"),
            nombre="Test",
            apellido="Instructor",
            correo_electronico="instructor3@test.com",
            tipo="instructor",
            activo=True,
            correo_electronico_verificado=True,
        )
        isolated_db_session.add(instructor)
        isolated_db_session.commit()

        # Login as instructor
        login_response = test_client.post(
            "/user/login",
            data={"usuario": "test_instructor3", "acceso": "testpass"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # Test edit attempt (should be forbidden)
        response = test_client.get(f"/program/{program_id}/edit")
        assert response.status_code == 403

    def test_edit_program_with_file_upload(self, session_full_db_setup, test_client, isolated_db_session):
        """Test edit program with logo file upload."""
        # Create test program
        programa = Programa(
            nombre="Program with Logo",
            codigo=self._unique_code("LOGOTEST"),
            descripcion="Test program for logo upload",
            precio=100,
            estado="draft",
            creado_por="admin",
        )
        isolated_db_session.add(programa)
        isolated_db_session.commit()
        program_id = programa.id

        # Login as admin
        login_response = test_client.post(
            "/user/login",
            data={"usuario": "lms-admin", "acceso": "lms-admin"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # Create a fake image file
        fake_image = io.BytesIO(b"fake image content")
        fake_image.name = "logo.jpg"

        # Test POST request with file
        response = test_client.post(
            f"/program/{program_id}/edit",
            data={
                "nombre": "Program with Logo",
                "descripcion": "Test program for logo upload",
                "precio": "100",
                "publico": False,
                "estado": "draft",
                "promocionado": False,
                "certificado": False,
                "logo": (fake_image, "logo.jpg"),
            },
            content_type="multipart/form-data",
            follow_redirects=False,
        )
        assert response.status_code == 302

    def test_programa_cursos_admin(self, session_full_db_setup, test_client):
        """Test programa_cursos route as admin."""
        # Login as admin
        login_response = test_client.post(
            "/user/login",
            data={"usuario": "lms-admin", "acceso": "lms-admin"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # Test route
        response = test_client.get("/program/TESTCODE/courses")
        assert response.status_code == 200

    def test_programa_cursos_non_admin(self, session_full_db_setup, test_client, isolated_db_session):
        """Test programa_cursos route as non-admin (should be forbidden)."""
        # Create instructor user
        instructor = Usuario(
            usuario="test_instructor4",
            acceso=proteger_passwd("testpass"),
            nombre="Test",
            apellido="Instructor",
            correo_electronico="instructor4@test.com",
            tipo="instructor",
            activo=True,
            correo_electronico_verificado=True,
        )
        isolated_db_session.add(instructor)
        isolated_db_session.commit()

        # Login as instructor
        login_response = test_client.post(
            "/user/login",
            data={"usuario": "test_instructor4", "acceso": "testpass"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # Test route (should be forbidden)
        response = test_client.get("/program/TESTCODE/courses")
        assert response.status_code == 403

    def test_pagina_programa(self, session_full_db_setup, test_client, isolated_db_session):
        """Test pagina_programa route (public program view)."""
        # Create public program
        programa_codigo = self._unique_code("PUBLICPROG")
        programa = Programa(
            nombre="Public Program",
            codigo=programa_codigo,
            descripcion="Test public program",
            publico=True,
            estado="open",
        )
        isolated_db_session.add(programa)
        isolated_db_session.commit()

        # Test route (should work without login)
        response = test_client.get(f"/program/{programa_codigo}")
        assert response.status_code == 200

    def test_lista_programas_no_filters(self, session_full_db_setup, test_client):
        """Test lista_programas route without filters."""
        response = test_client.get("/program/explore")
        assert response.status_code == 200

    def test_lista_programas_with_tag_filter(self, session_full_db_setup, test_client, isolated_db_session):
        """Test lista_programas route with tag filter."""
        # Create tag with required fields
        etiqueta = Etiqueta(nombre="test-tag", color="#000000")
        isolated_db_session.add(etiqueta)
        isolated_db_session.commit()

        # Test with tag filter
        response = test_client.get("/program/explore?tag=test-tag")
        assert response.status_code == 200

    def test_lista_programas_with_category_filter(self, session_full_db_setup, test_client, isolated_db_session):
        """Test lista_programas route with category filter."""
        # Create category with required fields
        categoria = Categoria(nombre="test-category", descripcion="Test category description")
        isolated_db_session.add(categoria)
        isolated_db_session.commit()

        # Test with category filter
        response = test_client.get("/program/explore?category=test-category")
        assert response.status_code == 200

    def test_lista_programas_with_multiple_filters(self, session_full_db_setup, test_client):
        """Test lista_programas route with multiple filters."""
        response = test_client.get("/program/explore?tag=python&category=programming&page=1")
        assert response.status_code == 200

    def test_inscribir_programa_get(self, session_full_db_setup, test_client, isolated_db_session):
        """Test GET request to inscribir_programa route."""
        # Create student user
        student_username = self._unique_username("test_student")
        student_email = self._unique_email("student", "test.com")
        student = Usuario(
            usuario=student_username,
            acceso=proteger_passwd("testpass"),
            nombre="Test",
            apellido="Student",
            correo_electronico=student_email,
            tipo="student",
            activo=True,
            correo_electronico_verificado=True,
        )
        isolated_db_session.add(student)

        # Create program
        programa_codigo = self._unique_code("ENROLLTEST")
        programa = Programa(
            nombre="Enrollment Test Program",
            codigo=programa_codigo,
            descripcion="Test program for enrollment",
            publico=True,
            estado="open",
        )
        isolated_db_session.add(programa)
        isolated_db_session.commit()

        # Login as student
        login_response = test_client.post(
            "/user/login",
            data={"usuario": student_username, "acceso": "testpass"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # Test GET request
        response = test_client.get(f"/program/{programa_codigo}/enroll")
        assert response.status_code == 200

    def test_inscribir_programa_post_success(self, session_full_db_setup, test_client, isolated_db_session):
        """Test successful POST request to inscribir_programa route."""
        # Create student user
        student = Usuario(
            usuario="test_student2",
            acceso=proteger_passwd("testpass"),
            nombre="Test",
            apellido="Student",
            correo_electronico="student2@test.com",
            tipo="student",
            activo=True,
            correo_electronico_verificado=True,
        )
        isolated_db_session.add(student)

        # Create program
        programa_codigo = self._unique_code("ENROLLTEST2")
        programa = Programa(
            nombre="Enrollment Test Program 2",
            codigo=programa_codigo,
            descripcion="Test program for enrollment",
            publico=True,
            estado="open",
        )
        isolated_db_session.add(programa)
        isolated_db_session.commit()

        # Login as student
        login_response = test_client.post(
            "/user/login",
            data={"usuario": "test_student2", "acceso": "testpass"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # Test POST request
        response = test_client.post(f"/program/{programa_codigo}/enroll", follow_redirects=False)
        assert response.status_code == 302  # Redirect after enrollment

        # Verify enrollment was created
        enrollment = isolated_db_session.execute(
            database.select(ProgramaEstudiante).filter_by(usuario="test_student2")
        ).scalar_one_or_none()
        assert enrollment is not None

    def test_inscribir_programa_already_enrolled(self, session_full_db_setup, test_client, isolated_db_session):
        """Test inscribir_programa when user is already enrolled."""
        # Create student user
        student_username = self._unique_username("test_student")
        student_email = self._unique_email("student", "test.com")
        student = Usuario(
            usuario=student_username,
            acceso=proteger_passwd("testpass"),
            nombre="Test",
            apellido="Student",
            correo_electronico=student_email,
            tipo="student",
            activo=True,
            correo_electronico_verificado=True,
        )
        isolated_db_session.add(student)

        # Create program
        programa_codigo = self._unique_code("ALREADYENROLLED")
        programa = Programa(
            nombre="Already Enrolled Program",
            codigo=programa_codigo,
            descripcion="Test program for already enrolled",
            publico=True,
            estado="open",
        )
        isolated_db_session.add(programa)
        isolated_db_session.commit()

        # Enroll user in program
        enrollment = ProgramaEstudiante(
            usuario=student_username,
            programa=programa.id,
            creado_por=student_username,
        )
        isolated_db_session.add(enrollment)
        isolated_db_session.commit()

        # Login as student
        login_response = test_client.post(
            "/user/login",
            data={"usuario": student_username, "acceso": "testpass"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # Test GET request (should redirect because already enrolled)
        response = test_client.get(f"/program/{programa_codigo}/enroll", follow_redirects=False)
        assert response.status_code == 302

    def test_inscribir_programa_not_found(self, session_full_db_setup, test_client, isolated_db_session):
        """Test inscribir_programa with non-existent program."""
        # Create student user
        student = Usuario(
            usuario="test_student4",
            acceso=proteger_passwd("testpass"),
            nombre="Test",
            apellido="Student",
            correo_electronico="student4@test.com",
            tipo="student",
            activo=True,
            correo_electronico_verificado=True,
        )
        isolated_db_session.add(student)
        isolated_db_session.commit()

        # Login as student
        login_response = test_client.post(
            "/user/login",
            data={"usuario": "test_student4", "acceso": "testpass"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # Test with non-existent program
        response = test_client.get("/program/NONEXISTENT/enroll")
        assert response.status_code == 404

    def test_tomar_programa(self, session_full_db_setup, test_client, isolated_db_session):
        """Test tomar_programa route."""
        # Create student user
        student = Usuario(
            usuario="test_student5",
            acceso=proteger_passwd("testpass"),
            nombre="Test",
            apellido="Student",
            correo_electronico="student5@test.com",
            tipo="student",
            activo=True,
            correo_electronico_verificado=True,
        )
        isolated_db_session.add(student)

        # Create program
        programa_codigo = self._unique_code("TAKETEST")
        programa = Programa(
            nombre="Take Program Test",
            codigo=programa_codigo,
            descripcion="Test program for taking",
            publico=True,
            estado="open",
        )
        isolated_db_session.add(programa)
        isolated_db_session.commit()

        # Enroll user in program
        enrollment = ProgramaEstudiante(
            usuario="test_student5",
            programa=programa.id,
            creado_por="test_student5",
        )
        isolated_db_session.add(enrollment)
        isolated_db_session.commit()

        # Login as student
        login_response = test_client.post(
            "/user/login",
            data={"usuario": "test_student5", "acceso": "testpass"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # Test route
        response = test_client.get(f"/program/{programa_codigo}/take")
        assert response.status_code == 200

    def test_tomar_programa_not_enrolled(self, session_full_db_setup, test_client, isolated_db_session):
        """Test tomar_programa when user is not enrolled."""
        # Create student user
        student_username = self._unique_username("test_student")
        student_email = self._unique_email("student", "test.com")
        student = Usuario(
            usuario=student_username,
            acceso=proteger_passwd("testpass"),
            nombre="Test",
            apellido="Student",
            correo_electronico=student_email,
            tipo="student",
            activo=True,
            correo_electronico_verificado=True,
        )
        isolated_db_session.add(student)

        # Create program
        programa_codigo = self._unique_code("TAKENOTENROLLED")
        programa = Programa(
            nombre="Take Program Not Enrolled",
            codigo=programa_codigo,
            descripcion="Test program for not enrolled",
            publico=True,
            estado="open",
        )
        isolated_db_session.add(programa)
        isolated_db_session.commit()

        # Login as student
        login_response = test_client.post(
            "/user/login",
            data={"usuario": student_username, "acceso": "testpass"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # Test route (should redirect to enrollment)
        response = test_client.get(f"/program/{programa_codigo}/take", follow_redirects=False)
        assert response.status_code == 302

    def test_tomar_programa_not_found(self, session_full_db_setup, test_client, isolated_db_session):
        """Test tomar_programa with non-existent program."""
        # Create student user
        student = Usuario(
            usuario="test_student7",
            acceso=proteger_passwd("testpass"),
            nombre="Test",
            apellido="Student",
            correo_electronico="student7@test.com",
            tipo="student",
            activo=True,
            correo_electronico_verificado=True,
        )
        isolated_db_session.add(student)
        isolated_db_session.commit()

        # Login as student
        login_response = test_client.post(
            "/user/login",
            data={"usuario": "test_student7", "acceso": "testpass"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # Test with non-existent program
        response = test_client.get("/program/NONEXISTENT/take")
        assert response.status_code == 404

    def test_gestionar_cursos_programa_get(self, session_full_db_setup, test_client, isolated_db_session):
        """Test GET request to gestionar_cursos_programa route."""
        # Create program
        programa_codigo = self._unique_code("MANAGECOURSES")
        programa = Programa(
            nombre="Manage Courses Program",
            codigo=programa_codigo,
            descripcion="Test program for course management",
            publico=True,
            estado="open",
        )
        isolated_db_session.add(programa)
        isolated_db_session.commit()

        # Login as admin
        login_response = test_client.post(
            "/user/login",
            data={"usuario": "lms-admin", "acceso": "lms-admin"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # Test GET request
        response = test_client.get(f"/program/{programa_codigo}/courses/manage")
        assert response.status_code == 200

    def test_gestionar_cursos_programa_add_course(self, session_full_db_setup, test_client, isolated_db_session):
        """Test adding course to program via gestionar_cursos_programa."""
        # Create program
        programa_codigo = self._unique_code("ADDCOURSE")
        programa = Programa(
            nombre="Add Course Program",
            codigo=programa_codigo,
            descripcion="Test program for adding course",
            publico=True,
            estado="open",
        )
        isolated_db_session.add(programa)

        # Create course
        curso_codigo = self._unique_code("COURSETOADD")
        curso = Curso(
            nombre="Course to Add",
            codigo=curso_codigo,
            descripcion="Test course to add",
            descripcion_corta="Test",
            nivel=1,
            duracion=2,
            estado="published",
            publico=True,
            modalidad="online",
            creado_por="admin",
        )
        isolated_db_session.add(curso)
        isolated_db_session.commit()

        # Login as admin
        login_response = test_client.post(
            "/user/login",
            data={"usuario": "lms-admin", "acceso": "lms-admin"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # Test adding course
        response = test_client.post(
            f"/program/{programa_codigo}/courses/manage",
            data={
                "action": "add_course",
                "curso_codigo": curso_codigo,
            },
            follow_redirects=False,
        )
        assert response.status_code == 302

        # Verify course was added to program
        prog_curso = isolated_db_session.execute(
            database.select(ProgramaCurso).filter_by(programa=programa_codigo, curso=curso_codigo)
        ).scalar_one_or_none()
        assert prog_curso is not None

    def test_gestionar_cursos_programa_add_existing_course(self, session_full_db_setup, test_client, isolated_db_session):
        """Test adding course that already exists in program."""
        # Create program
        programa_codigo = self._unique_code("ADDEXISTING")
        programa = Programa(
            nombre="Add Existing Course Program",
            codigo=programa_codigo,
            descripcion="Test program for adding existing course",
            publico=True,
            estado="open",
        )
        isolated_db_session.add(programa)

        # Create course
        curso_codigo = self._unique_code("EXISTINGCOURSE")
        curso = Curso(
            nombre="Existing Course",
            codigo=curso_codigo,
            descripcion="Test existing course",
            descripcion_corta="Test",
            nivel=1,
            duracion=2,
            estado="published",
            publico=True,
            modalidad="online",
            creado_por="admin",
        )
        isolated_db_session.add(curso)
        isolated_db_session.commit()

        # Add course to program
        prog_curso = ProgramaCurso(programa=programa_codigo, curso=curso_codigo, creado_por="admin")
        isolated_db_session.add(prog_curso)
        isolated_db_session.commit()

        # Login as admin
        login_response = test_client.post(
            "/user/login",
            data={"usuario": "lms-admin", "acceso": "lms-admin"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # Test adding course again (should show warning)
        response = test_client.post(
            f"/program/{programa_codigo}/courses/manage",
            data={
                "action": "add_course",
                "curso_codigo": curso_codigo,
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"ya est" in response.data or b"already" in response.data

    def test_gestionar_cursos_programa_remove_course(self, session_full_db_setup, test_client, isolated_db_session):
        """Test removing course from program via gestionar_cursos_programa."""
        # Create program
        programa_codigo = self._unique_code("REMOVECOURSE")
        programa = Programa(
            nombre="Remove Course Program",
            codigo=programa_codigo,
            descripcion="Test program for removing course",
            publico=True,
            estado="open",
        )
        isolated_db_session.add(programa)

        # Create course
        curso_codigo = self._unique_code("COURSETOREMOVE")
        curso = Curso(
            nombre="Course to Remove",
            codigo=curso_codigo,
            descripcion="Test course to remove",
            descripcion_corta="Test",
            nivel=1,
            duracion=2,
            estado="published",
            publico=True,
            modalidad="online",
            creado_por="admin",
        )
        isolated_db_session.add(curso)
        isolated_db_session.commit()

        # Add course to program
        prog_curso = ProgramaCurso(programa=programa_codigo, curso=curso_codigo, creado_por="admin")
        isolated_db_session.add(prog_curso)
        isolated_db_session.commit()

        # Login as admin
        login_response = test_client.post(
            "/user/login",
            data={"usuario": "lms-admin", "acceso": "lms-admin"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # Test removing course
        response = test_client.post(
            f"/program/{programa_codigo}/courses/manage",
            data={
                "action": "remove_course",
                "curso_codigo": curso_codigo,
            },
            follow_redirects=False,
        )
        assert response.status_code == 302

        # Verify course was removed from program
        prog_curso = isolated_db_session.execute(
            database.select(ProgramaCurso).filter_by(programa=programa_codigo, curso=curso_codigo)
        ).scalar_one_or_none()
        assert prog_curso is None

    def test_gestionar_cursos_programa_not_found(self, session_full_db_setup, test_client):
        """Test gestionar_cursos_programa with non-existent program."""
        # Login as admin
        login_response = test_client.post(
            "/user/login",
            data={"usuario": "lms-admin", "acceso": "lms-admin"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # Test with non-existent program
        response = test_client.get("/program/NONEXISTENT/courses/manage")
        assert response.status_code == 404

    def test_gestionar_cursos_programa_non_admin(self, session_full_db_setup, test_client, isolated_db_session):
        """Test gestionar_cursos_programa as non-admin."""
        # Create test program
        program_code = self._unique_code("NONADMINCOURSE")
        programa = Programa(
            nombre="Program for Non-Admin Course Management",
            codigo=program_code,
            descripcion="Test program for non-admin course management",
            publico=True,
            estado="open",
        )
        isolated_db_session.add(programa)
        isolated_db_session.commit()

        # Create instructor user
        instructor = Usuario(
            usuario="test_instructor5",
            acceso=proteger_passwd("testpass"),
            nombre="Test",
            apellido="Instructor",
            correo_electronico="instructor5@test.com",
            tipo="instructor",
            activo=True,
            correo_electronico_verificado=True,
        )
        isolated_db_session.add(instructor)
        isolated_db_session.commit()

        # Login as instructor
        login_response = test_client.post(
            "/user/login",
            data={"usuario": "test_instructor5", "acceso": "testpass"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # Test route (should be forbidden)
        response = test_client.get(f"/program/{program_code}/courses/manage")
        assert response.status_code == 403

    def test_inscribir_usuario_programa_get(self, session_full_db_setup, test_client, isolated_db_session):
        """Test GET request to inscribir_usuario_programa route."""
        # Create program
        program_code = self._unique_code("MANUALENROLL")
        programa = Programa(
            nombre="Manual Enrollment Program",
            codigo=program_code,
            descripcion="Test program for manual enrollment",
            publico=True,
            estado="open",
        )
        isolated_db_session.add(programa)
        isolated_db_session.commit()

        # Login as admin
        login_response = test_client.post(
            "/user/login",
            data={"usuario": "lms-admin", "acceso": "lms-admin"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # Test GET request
        response = test_client.get(f"/program/{program_code}/enroll_user")
        assert response.status_code == 200

    def test_inscribir_usuario_programa_post_success(self, session_full_db_setup, test_client, isolated_db_session):
        """Test successful POST request to inscribir_usuario_programa route."""
        # Create student user
        student = Usuario(
            usuario="manual_student",
            acceso=proteger_passwd("testpass"),
            nombre="Manual",
            apellido="Student",
            correo_electronico="manual@test.com",
            tipo="student",
            activo=True,
            correo_electronico_verificado=True,
        )
        isolated_db_session.add(student)

        # Create program
        program_code = self._unique_code("MANUALENROLL2")
        programa = Programa(
            nombre="Manual Enrollment Program 2",
            codigo=program_code,
            descripcion="Test program for manual enrollment",
            publico=True,
            estado="open",
        )
        isolated_db_session.add(programa)
        isolated_db_session.commit()

        # Login as admin
        login_response = test_client.post(
            "/user/login",
            data={"usuario": "lms-admin", "acceso": "lms-admin"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # Test POST request
        response = test_client.post(
            f"/program/{program_code}/enroll_user",
            data={"usuario_email": "manual@test.com"},
            follow_redirects=False,
        )
        assert response.status_code == 302

        # Verify enrollment was created
        enrollment = isolated_db_session.execute(
            database.select(ProgramaEstudiante).filter_by(usuario="manual_student")
        ).scalar_one_or_none()
        assert enrollment is not None

    def test_inscribir_usuario_programa_user_not_found(self, session_full_db_setup, test_client, isolated_db_session):
        """Test inscribir_usuario_programa with non-existent user."""
        # Create program
        program_code = self._unique_code("MANUALENROLL3")
        programa = Programa(
            nombre="Manual Enrollment Program 3",
            codigo=program_code,
            descripcion="Test program for manual enrollment",
            publico=True,
            estado="open",
        )
        isolated_db_session.add(programa)
        isolated_db_session.commit()

        # Login as admin
        login_response = test_client.post(
            "/user/login",
            data={"usuario": "lms-admin", "acceso": "lms-admin"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # Test POST request with non-existent user
        response = test_client.post(
            f"/program/{program_code}/enroll_user",
            data={"usuario_email": "nonexistent@test.com"},
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"no encontrado" in response.data or b"not found" in response.data

    def test_inscribir_usuario_programa_already_enrolled(self, session_full_db_setup, test_client, isolated_db_session):
        """Test inscribir_usuario_programa when user is already enrolled."""
        # Create student user
        student = Usuario(
            usuario="already_enrolled_student",
            acceso=proteger_passwd("testpass"),
            nombre="Already",
            apellido="Enrolled",
            correo_electronico="already@test.com",
            tipo="student",
            activo=True,
            correo_electronico_verificado=True,
        )
        isolated_db_session.add(student)

        # Create program
        program_code = self._unique_code("MANUALENROLL4")
        programa = Programa(
            nombre="Manual Enrollment Program 4",
            codigo=program_code,
            descripcion="Test program for manual enrollment",
            publico=True,
            estado="open",
        )
        isolated_db_session.add(programa)
        isolated_db_session.commit()

        # Enroll user in program
        enrollment = ProgramaEstudiante(
            usuario="already_enrolled_student",
            programa=programa.id,
            creado_por="admin",
        )
        isolated_db_session.add(enrollment)
        isolated_db_session.commit()

        # Login as admin
        login_response = test_client.post(
            "/user/login",
            data={"usuario": "lms-admin", "acceso": "lms-admin"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # Test POST request with already enrolled user
        response = test_client.post(
            f"/program/{program_code}/enroll_user",
            data={"usuario_email": "already@test.com"},
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"ya est" in response.data or b"already" in response.data

    def test_inscribir_usuario_programa_not_found(self, session_full_db_setup, test_client):
        """Test inscribir_usuario_programa with non-existent program."""
        # Login as admin
        login_response = test_client.post(
            "/user/login",
            data={"usuario": "lms-admin", "acceso": "lms-admin"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # Test with non-existent program
        response = test_client.get("/program/NONEXISTENT/enroll_user")
        assert response.status_code == 404

    def test_emitir_certificado_programa_function(self, session_full_db_setup, test_client, isolated_db_session):
        """Test _emitir_certificado_programa internal function via HTTP request."""
        # Create program
        programa_codigo = self._unique_code("CERTTEST")
        programa = Programa(
            nombre="Certificate Test Program",
            codigo=programa_codigo,
            descripcion="Test program for certificate",
            publico=True,
            estado="open",
            certificado=True,
            plantilla_certificado="default",
        )
        isolated_db_session.add(programa)

        # Create student user
        student = Usuario(
            usuario="cert_student",
            acceso=proteger_passwd("testpass"),
            nombre="Certificate",
            apellido="Student",
            correo_electronico="cert@test.com",
            tipo="student",
            activo=True,
            correo_electronico_verificado=True,
        )
        isolated_db_session.add(student)

        # Create course and add to program
        curso_codigo = self._unique_code("CERTCOURSE")
        curso = Curso(
            nombre="Test Course",
            codigo=curso_codigo,
            descripcion="Test course",
            descripcion_corta="Test",
            nivel=1,
            duracion=2,
            estado="published",
            publico=True,
            modalidad="online",
            certificado=True,
            plantilla_certificado="default",
            creado_por="admin",
        )
        isolated_db_session.add(curso)
        isolated_db_session.commit()

        # Add course to program
        prog_curso = ProgramaCurso(programa=programa_codigo, curso=curso_codigo)
        isolated_db_session.add(prog_curso)

        # Enroll user in program
        enrollment = ProgramaEstudiante(
            usuario="cert_student",
            programa=programa.id,
            creado_por="cert_student",
        )
        isolated_db_session.add(enrollment)

        # Complete the course (add certificate)
        from now_lms.db import Certificacion

        cert = Certificacion(
            usuario="cert_student",
            curso=curso_codigo,
            certificado="default",
        )
        isolated_db_session.add(cert)
        isolated_db_session.commit()

        # Login as student
        login_response = test_client.post(
            "/user/login",
            data={"usuario": "cert_student", "acceso": "testpass"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # Test certificate emission via tomar_programa route
        with patch("now_lms.vistas.programs.render_template") as mock_render:
            mock_render.return_value = "Mocked template response"
            response = test_client.get(f"/program/{programa_codigo}/take")
            assert response.status_code == 200

        # Verify program certificate was created
        certificado = isolated_db_session.execute(
            database.select(CertificacionPrograma).filter_by(usuario="cert_student")
        ).scalar_one_or_none()
        assert certificado is not None
        assert certificado.certificado == "default"

    def test_edit_program_with_promocionado_date(self, session_full_db_setup, test_client, isolated_db_session):
        """Test edit program setting promocionado flag (covers line 203)."""
        # Create test program
        programa = Programa(
            nombre="Promocionado Test Program",
            codigo=self._unique_code("PROMOCIONADOTEST"),
            descripcion="Test program for promocionado",
            precio=100,
            estado="draft",
            publico=False,
            promocionado=False,  # Initially not promoted
            creado_por="admin",
        )
        isolated_db_session.add(programa)
        isolated_db_session.commit()
        program_id = programa.id

        # Login as admin
        login_response = test_client.post(
            "/user/login",
            data={"usuario": "lms-admin", "acceso": "lms-admin"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # Test POST request with promocionado set to True
        response = test_client.post(
            f"/program/{program_id}/edit",
            data={
                "nombre": "Promocionado Test Program",
                "descripcion": "Test program for promocionado",
                "precio": "100",
                "publico": False,
                "estado": "draft",
                "promocionado": True,  # Setting to promoted
                "certificado": False,
            },
            follow_redirects=False,
        )
        assert response.status_code == 302

        # Verify program was updated with fecha_promocionado
        updated_program = isolated_db_session.execute(database.select(Programa).filter_by(id=program_id)).scalar_one()
        assert updated_program.promocionado is True
        assert updated_program.fecha_promocionado is not None

    def test_edit_program_category_and_tags_update(self, session_full_db_setup, test_client, isolated_db_session):
        """Test edit program updating category and tags (covers lines 231-232, 240-242)."""
        # Create test program
        programa = Programa(
            nombre="Category Tags Test Program",
            codigo=self._unique_code("CATEGORYTAGSTEST"),
            descripcion="Test program for category and tags",
            precio=100,
            estado="draft",
            publico=False,
            creado_por="admin",
        )
        isolated_db_session.add(programa)

        # Create category and tag
        categoria = Categoria(nombre="test-edit-category", descripcion="Test category for edit")
        etiqueta = Etiqueta(nombre="test-edit-tag", color="#FF0000")
        isolated_db_session.add(categoria)
        isolated_db_session.add(etiqueta)
        isolated_db_session.commit()
        program_id = programa.id

        # Login as admin
        login_response = test_client.post(
            "/user/login",
            data={"usuario": "lms-admin", "acceso": "lms-admin"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # Test POST request with category and tags
        response = test_client.post(
            f"/program/{program_id}/edit",
            data={
                "nombre": "Category Tags Test Program",
                "descripcion": "Test program for category and tags",
                "precio": "100",
                "publico": False,
                "estado": "draft",
                "promocionado": False,
                "certificado": False,
                "categoria": str(categoria.id),
                "etiquetas": [str(etiqueta.id)],
            },
            follow_redirects=False,
        )
        assert response.status_code == 302

        # Verify category and tag associations were created (refresh data from database)
        isolated_db_session.expunge_all()  # Clear the session cache
        cat_prog = isolated_db_session.execute(
            database.select(CategoriaPrograma).filter_by(programa=program_id)
        ).scalar_one_or_none()
        if cat_prog:
            assert cat_prog.categoria == categoria.id

        tag_prog = isolated_db_session.execute(
            database.select(EtiquetaPrograma).filter_by(programa=program_id)
        ).scalar_one_or_none()
        if tag_prog:
            assert tag_prog.etiqueta == etiqueta.id

    def test_inscribir_programa_operational_error(self, session_full_db_setup, test_client, isolated_db_session):
        """Test inscribir_programa with operational error (covers lines 380-382)."""
        # Create student user
        student = Usuario(
            usuario="error_test_student",
            acceso=proteger_passwd("testpass"),
            nombre="Error",
            apellido="Student",
            correo_electronico="errorstudent@test.com",
            tipo="student",
            activo=True,
            correo_electronico_verificado=True,
        )
        isolated_db_session.add(student)

        # Create program
        program_code = self._unique_code("ERRORTEST")
        programa = Programa(
            nombre="Error Test Program",
            codigo=program_code,
            descripcion="Test program for error",
            publico=True,
            estado="open",
        )
        isolated_db_session.add(programa)
        isolated_db_session.commit()

        # Login as student
        login_response = test_client.post(
            "/user/login",
            data={"usuario": "error_test_student", "acceso": "testpass"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # Mock OperationalError on database commit
        from sqlalchemy.exc import OperationalError

        with patch(
            "now_lms.vistas.programs.database.session.commit", side_effect=OperationalError("Database error", None, None)
        ):
            response = test_client.post(f"/program/{program_code}/enroll", follow_redirects=True)
            assert response.status_code == 200
            # Check for error message
            assert b"error" in response.data.lower() or b"problema" in response.data.lower()

    def test_inscribir_usuario_programa_operational_error(self, session_full_db_setup, test_client, isolated_db_session):
        """Test inscribir_usuario_programa with operational error (covers lines 522-524)."""
        # Create student user
        student = Usuario(
            usuario="manual_error_student",
            acceso=proteger_passwd("testpass"),
            nombre="Manual Error",
            apellido="Student",
            correo_electronico="manualerror@test.com",
            tipo="student",
            activo=True,
            correo_electronico_verificado=True,
        )
        isolated_db_session.add(student)

        # Create program
        program_code = self._unique_code("MANUALERROR")
        programa = Programa(
            nombre="Manual Error Enrollment Program",
            codigo=program_code,
            descripcion="Test program for manual enrollment error",
            publico=True,
            estado="open",
        )
        isolated_db_session.add(programa)
        isolated_db_session.commit()

        # Login as admin
        login_response = test_client.post(
            "/user/login",
            data={"usuario": "lms-admin", "acceso": "lms-admin"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # Mock OperationalError on database commit
        from sqlalchemy.exc import OperationalError

        with patch(
            "now_lms.vistas.programs.database.session.commit", side_effect=OperationalError("Database error", None, None)
        ):
            response = test_client.post(
                f"/program/{program_code}/enroll_user",
                data={"usuario_email": "manualerror@test.com"},
                follow_redirects=True,
            )
            assert response.status_code == 200
            # Check for error message
            assert b"error" in response.data.lower() or b"problema" in response.data.lower()

    def test_emitir_certificado_programa_program_not_found(self, session_full_db_setup):
        """Test _emitir_certificado_programa with non-existent program."""
        from now_lms.vistas.programs import _emitir_certificado_programa

        with session_full_db_setup.app_context():
            # Create a proper mock current_user
            from unittest.mock import MagicMock

            mock_user = MagicMock()
            mock_user.usuario = "test_user"

            # Mock current_user and flash
            with (
                patch("now_lms.vistas.programs.current_user", mock_user),
                patch("now_lms.vistas.programs.flash") as mock_flash,
            ):

                # Test with non-existent program
                _emitir_certificado_programa("NONEXISTENT", "test_user", "default")

                # Verify flash was called with error message
                mock_flash.assert_called_once()
                args = mock_flash.call_args[0]
                assert "no encontrado" in args[0] or "not found" in args[0]

    def test_tomar_programa_with_certificate_emission_basic(self, session_full_db_setup, test_client, isolated_db_session):
        """Test tomar_programa route basic functionality without template issues."""
        # Create student user
        student = Usuario(
            usuario="cert_basic_student",
            acceso=proteger_passwd("testpass"),
            nombre="Certificate",
            apellido="Basic",
            correo_electronico="certbasic@test.com",
            tipo="student",
            activo=True,
            correo_electronico_verificado=True,
        )
        isolated_db_session.add(student)

        # Create program with certificate enabled
        program_code = self._unique_code("BASICCERTTEST")
        programa = Programa(
            nombre="Basic Certificate Test Program",
            codigo=program_code,
            descripcion="Basic test program for certificate emission",
            publico=True,
            estado="open",
            certificado=True,
            plantilla_certificado="default",
        )
        isolated_db_session.add(programa)
        isolated_db_session.commit()

        # Enroll user in program
        enrollment = ProgramaEstudiante(
            usuario="cert_basic_student",
            programa=programa.id,
            creado_por="cert_basic_student",
        )
        isolated_db_session.add(enrollment)
        isolated_db_session.commit()

        # Login as student
        login_response = test_client.post(
            "/user/login",
            data={"usuario": "cert_basic_student", "acceso": "testpass"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # Test route (mock template rendering to avoid course template issues)
        with patch("now_lms.vistas.programs.render_template") as mock_render:
            mock_render.return_value = "Mocked template response"
            response = test_client.get(f"/program/{program_code}/take")
            assert response.status_code == 200
            # Verify the template was called with correct parameters
            mock_render.assert_called_once()
            call_args = mock_render.call_args
            assert call_args[0][0] == "learning/programas/tomar_programa.html"
            assert "programa" in call_args[1]
            assert "progreso" in call_args[1]
            assert "cursos_programa" in call_args[1]
