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

"""Comprehensive tests for Course functionality - Basic version."""

from decimal import Decimal

from now_lms.db import (
    Curso,
    CursoSeccion,
    EstudianteCurso,
    Usuario,
    database,
)


class TestCourseBasicFunctionality:
    """Test basic course model and creation."""

    def test_course_model_exists(self, session_basic_db_setup):
        """Test that Course model can be imported and instantiated."""
        with session_basic_db_setup.app_context():
            course = Curso(
                codigo="TEST001",
                nombre="Test Course",
                descripcion_corta="Short test course description",
                descripcion="Test course long description",
                estado="draft",
                modalidad="self_paced",
                pagado=False,
                certificado=False,
            )
            assert course is not None
            assert course.codigo == "TEST001"
            assert course.nombre == "Test Course"

    def test_course_creation_with_database(self, isolated_db_session):
        """Test course creation and persistence in database."""
        course = Curso(
            codigo="TEST002",
            nombre="Database Test Course",
            descripcion_corta="Database testing course",
            descripcion="Testing database persistence",
            estado="draft",
            modalidad="time_based",
            pagado=True,
            precio=Decimal("99.99"),
            certificado=True,
        )

        database.session.add(course)
        database.session.commit()

        # Retrieve and verify
        retrieved = database.session.execute(database.select(Curso).filter_by(codigo="TEST002")).scalar_one()

        assert retrieved.nombre == "Database Test Course"
        assert retrieved.precio == Decimal("99.99")
        assert retrieved.pagado is True
        assert retrieved.certificado is True

    def test_course_sections_creation(self, isolated_db_session):
        """Test creation of course sections."""
        # Create course
        course = Curso(
            codigo="SECTION_COURSE",
            nombre="Course with Sections",
            descripcion_corta="Testing sections",
            descripcion="Testing sections",
            estado="draft",
        )
        database.session.add(course)
        database.session.commit()

        # Create section
        section = CursoSeccion(
            curso=course.codigo,
            nombre="Introduction Section",
            descripcion="Introduction to the course",
            indice=1,
        )
        database.session.add(section)
        database.session.commit()

        # Verify section
        retrieved = database.session.execute(database.select(CursoSeccion).filter_by(curso=course.codigo)).scalar_one()

        assert retrieved.nombre == "Introduction Section"
        assert retrieved.indice == 1

    def test_student_enrollment(self, isolated_db_session):
        """Test student enrollment in courses."""
        # Create user
        user = Usuario(
            usuario="student_test",
            acceso=b"password123",
            nombre="Test",
            apellido="Student",
            correo_electronico="student@test.com",
            tipo="student",
        )
        database.session.add(user)

        # Create course
        course = Curso(
            codigo="ENROLL_COURSE",
            nombre="Enrollment Course",
            descripcion_corta="Test enrollment",
            descripcion="Test enrollment",
            estado="open",
            pagado=False,
        )
        database.session.add(course)
        database.session.commit()

        # Enroll student
        enrollment = EstudianteCurso(
            usuario=user.usuario,
            curso=course.codigo,
            vigente=True,
        )
        database.session.add(enrollment)
        database.session.commit()

        # Verify enrollment
        retrieved = database.session.execute(
            database.select(EstudianteCurso).filter_by(usuario=user.usuario, curso=course.codigo)
        ).scalar_one()

        assert retrieved.vigente is True
