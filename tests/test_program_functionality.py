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

"""Tests for program functionality."""

from now_lms.db import (
    Certificacion,
    CertificacionPrograma,
    Curso,
    Programa,
    ProgramaCurso,
    ProgramaEstudiante,
    Usuario,
    database,
)
from now_lms.db.tools import (
    cuenta_cursos_por_programa,
    obtener_progreso_programa,
    verificar_programa_completo,
    verificar_usuario_inscrito_programa,
)
from now_lms.auth import proteger_passwd


class TestProgramFunctionality:
    """Test program functionality including certificates, enrollment, and progress tracking."""

    def setup_test_data(self, app):
        """Setup test data for program functionality tests."""
        with app.app_context():
            # Create test program
            programa = Programa(
                nombre="Test Program",
                codigo="TESTPROG",
                descripcion="Test program for functionality testing",
                publico=True,
                estado="open",
                certificado=True,
                plantilla_certificado="default",
            )
            database.session.add(programa)
            database.session.commit()

            # Create test courses
            curso1 = Curso(
                nombre="Test Course 1",
                codigo="TEST01",
                descripcion_corta="Test course 1",
                descripcion="First test course",
                publico=True,
                modalidad="self_paced",
                estado="open",
                certificado=True,
                plantilla_certificado="default",
            )
            curso2 = Curso(
                nombre="Test Course 2",
                codigo="TEST02",
                descripcion_corta="Test course 2",
                descripcion="Second test course",
                publico=True,
                modalidad="self_paced",
                estado="open",
                certificado=True,
                plantilla_certificado="default",
            )
            database.session.add(curso1)
            database.session.add(curso2)
            database.session.commit()

            # Add courses to program
            prog_curso1 = ProgramaCurso(
                programa="TESTPROG",
                curso="TEST01",
            )
            prog_curso2 = ProgramaCurso(
                programa="TESTPROG",
                curso="TEST02",
            )
            database.session.add(prog_curso1)
            database.session.add(prog_curso2)
            database.session.commit()

            # Create test user
            usuario = Usuario(
                usuario="testuser",
                acceso=proteger_passwd("testpass"),
                nombre="Test",
                apellido="User",
                correo_electronico="test@example.com",
                tipo="student",
                activo=True,
                correo_electronico_verificado=True,
            )
            database.session.add(usuario)
            database.session.commit()

            return programa, [curso1, curso2], usuario

    def test_program_course_count(self, basic_config_setup):
        """Test counting courses in a program."""
        app = basic_config_setup
        programa, cursos, usuario = self.setup_test_data(app)

        with app.app_context():
            count = cuenta_cursos_por_programa("TESTPROG")
            assert count == 2

    def test_program_enrollment(self, basic_config_setup):
        """Test program enrollment functionality."""
        app = basic_config_setup
        programa, cursos, usuario = self.setup_test_data(app)

        with app.app_context():
            # User should not be enrolled initially
            assert not verificar_usuario_inscrito_programa("testuser", "TESTPROG")

            # Get the program ID within the same session
            programa_db = database.session.execute(database.select(Programa).filter_by(codigo="TESTPROG")).scalar_one()

            # Enroll user in program
            inscripcion = ProgramaEstudiante(
                usuario="testuser",
                programa=programa_db.id,
            )
            database.session.add(inscripcion)
            database.session.commit()

            # User should now be enrolled
            assert verificar_usuario_inscrito_programa("testuser", "TESTPROG")

    def test_program_progress_tracking(self, basic_config_setup):
        """Test program progress tracking."""
        app = basic_config_setup
        programa, cursos, usuario = self.setup_test_data(app)

        with app.app_context():
            # Initially no progress
            progreso = obtener_progreso_programa("testuser", "TESTPROG")
            assert progreso["total"] == 2
            assert progreso["completados"] == 0
            assert progreso["porcentaje"] == 0

            # Complete first course
            cert1 = Certificacion(
                usuario="testuser",
                curso="TEST01",
                certificado="default",
            )
            database.session.add(cert1)
            database.session.commit()

            # Check progress
            progreso = obtener_progreso_programa("testuser", "TESTPROG")
            assert progreso["total"] == 2
            assert progreso["completados"] == 1
            assert progreso["porcentaje"] == 50.0

            # Complete second course
            cert2 = Certificacion(
                usuario="testuser",
                curso="TEST02",
                certificado="default",
            )
            database.session.add(cert2)
            database.session.commit()

            # Check final progress
            progreso = obtener_progreso_programa("testuser", "TESTPROG")
            assert progreso["total"] == 2
            assert progreso["completados"] == 2
            assert progreso["porcentaje"] == 100.0

    def test_program_completion_detection(self, basic_config_setup):
        """Test program completion detection."""
        app = basic_config_setup
        programa, cursos, usuario = self.setup_test_data(app)

        with app.app_context():
            # Program should not be complete initially
            assert not verificar_programa_completo("testuser", "TESTPROG")

            # Complete first course
            cert1 = Certificacion(
                usuario="testuser",
                curso="TEST01",
                certificado="default",
            )
            database.session.add(cert1)
            database.session.commit()

            # Program still not complete
            assert not verificar_programa_completo("testuser", "TESTPROG")

            # Complete second course
            cert2 = Certificacion(
                usuario="testuser",
                curso="TEST02",
                certificado="default",
            )
            database.session.add(cert2)
            database.session.commit()

            # Program should now be complete
            assert verificar_programa_completo("testuser", "TESTPROG")

    def test_program_certificate_generation(self, basic_config_setup):
        """Test program certificate generation."""
        app = basic_config_setup
        programa, cursos, usuario = self.setup_test_data(app)

        with app.app_context():
            # Get the program ID within the same session
            programa_db = database.session.execute(database.select(Programa).filter_by(codigo="TESTPROG")).scalar_one()

            # Complete all courses first
            cert1 = Certificacion(
                usuario="testuser",
                curso="TEST01",
                certificado="default",
            )
            cert2 = Certificacion(
                usuario="testuser",
                curso="TEST02",
                certificado="default",
            )
            database.session.add(cert1)
            database.session.add(cert2)
            database.session.commit()

            # Verify program is complete
            assert verificar_programa_completo("testuser", "TESTPROG")

            # Generate program certificate
            cert_programa = CertificacionPrograma(
                programa=programa_db.id,
                usuario="testuser",
                certificado="default",
            )
            database.session.add(cert_programa)
            database.session.commit()

            # Verify certificate was created
            certificacion = database.session.execute(
                database.select(CertificacionPrograma).filter_by(usuario="testuser", programa=programa_db.id)
            ).scalar_one_or_none()

            assert certificacion is not None
            assert certificacion.certificado == "default"

    def test_program_model_fields(self, basic_config_setup):
        """Test that Program model has required certificate fields."""
        app = basic_config_setup

        with app.app_context():
            programa = Programa(
                nombre="Test Program",
                codigo="TESTFIELDS",
                descripcion="Test program fields",
                certificado=True,
                plantilla_certificado="default",
            )
            database.session.add(programa)
            database.session.commit()

            # Retrieve and verify fields
            saved_programa = database.session.execute(database.select(Programa).filter_by(codigo="TESTFIELDS")).scalar_one()

            assert saved_programa.certificado is True
            assert saved_programa.plantilla_certificado == "default"

    def test_program_certificate_template_exists(self, basic_config_setup):
        """Test that program certificate template exists in templates."""
        app = basic_config_setup

        with app.app_context():
            from now_lms.db.certificates_templates import CERTIFICADOS

            # Check if program template exists
            program_templates = [cert for cert in CERTIFICADOS if cert[4] == "programa"]
            assert len(program_templates) == 1

            template = program_templates[0]
            assert template[0] == "Programa"  # Title
            assert "programa" in template[2].lower()  # HTML should contain program references

    def test_empty_program_progress(self, basic_config_setup):
        """Test progress tracking for program with no courses."""
        app = basic_config_setup

        with app.app_context():
            # Create program with no courses
            programa = Programa(
                nombre="Empty Program",
                codigo="EMPTY",
                descripcion="Program with no courses",
            )
            database.session.add(programa)
            database.session.commit()

            progreso = obtener_progreso_programa("testuser", "EMPTY")
            assert progreso["total"] == 0
            assert progreso["completados"] == 0
            assert progreso["porcentaje"] == 0

    def test_program_certificate_course_list(self, basic_config_setup):
        """Test getting completed courses list for program certificate."""
        app = basic_config_setup
        programa, cursos, usuario = self.setup_test_data(app)

        with app.app_context():
            # Get the program ID within the same session
            programa_db = database.session.execute(database.select(Programa).filter_by(codigo="TESTPROG")).scalar_one()

            # Complete courses
            cert1 = Certificacion(
                usuario="testuser",
                curso="TEST01",
                certificado="default",
            )
            cert2 = Certificacion(
                usuario="testuser",
                curso="TEST02",
                certificado="default",
            )
            database.session.add(cert1)
            database.session.add(cert2)
            database.session.commit()

            # Create program certificate
            cert_programa = CertificacionPrograma(
                programa=programa_db.id,
                usuario="testuser",
                certificado="default",
            )
            database.session.add(cert_programa)
            database.session.commit()

            # Test getting completed courses
            cursos_completados = cert_programa.get_cursos_completados()
            assert len(cursos_completados) == 2
            assert "TEST01" in cursos_completados
            assert "TEST02" in cursos_completados
