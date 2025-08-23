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

"""Advanced comprehensive tests for Certificate views to improve coverage."""

import pytest
import sys
from unittest.mock import patch, MagicMock

from now_lms.db import (
    Certificacion,
    CertificacionPrograma,
    Certificado,
    Curso,
    CursoSeccion,
    Evaluation,
    EvaluationAttempt,
    MasterClass,
    MasterClassEnrollment,
    Programa,
    Usuario,
    database,
)
from now_lms.auth import proteger_passwd
from now_lms.vistas.certificates import insert_style_in_html


class TestCertificateHelperFunctionAdvanced:
    """Test edge cases in certificate helper functions."""

    def test_insert_style_in_html_empty_css_edge_case(self):
        """Test insert_style_in_html with empty CSS properly returns without CSS."""
        template = MagicMock()
        template.html = "<h1>Test Certificate</h1>"
        template.css = ""

        result = insert_style_in_html(template)

        # Should return original HTML when CSS is empty since empty string is falsy
        assert result == "<h1>Test Certificate</h1>"

    def test_insert_style_in_html_none_css_handling(self):
        """Test insert_style_in_html handles None CSS gracefully."""
        template = MagicMock()
        template.html = "<h1>Test Certificate</h1>"
        template.css = None

        result = insert_style_in_html(template)

        # Should return original HTML when CSS is None since None is falsy
        assert result == "<h1>Test Certificate</h1>"


class TestCertificatePDFGeneration:
    """Test PDF generation routes for certificates."""

    def setup_test_certification_with_masterclass(self, app):
        """Helper to create certification with masterclass for PDF tests."""
        with app.app_context():
            # Create user
            user = Usuario(
                usuario="pdf_test_user",
                acceso=proteger_passwd("testpass"),
                nombre="PDF",
                apellido="Test",
                correo_electronico="pdf@test.com",
                tipo="student",
                activo=True,
                correo_electronico_verificado=True,
            )
            database.session.add(user)

            # Create masterclass
            from datetime import date, time

            masterclass = MasterClass(
                slug="MC_PDF_001",
                title="PDF Test MasterClass",
                description_public="MasterClass for PDF testing",
                description_private="Internal description",
                date=date.today(),
                start_time=time(10, 0),
                end_time=time(12, 0),
                platform_name="Zoom",
                platform_url="https://zoom.us/test",
                is_certificate=True,
                instructor_id="instructor",
            )
            database.session.add(masterclass)

            # Create certificate template
            template = Certificado(
                code="PDF_TEMPLATE",
                titulo="PDF Certificate Template",
                html="<h1>{{usuario.nombre}} {{usuario.apellido}}</h1><p>MasterClass: {{master_class.title}}</p>",
                css="h1 { color: blue; } p { font-size: 14px; }",
                habilitado=True,
                publico=True,
            )
            database.session.add(template)
            database.session.flush()

            # Create certification with masterclass
            certification = Certificacion(
                usuario=user.usuario,
                curso=None,
                master_class_id=masterclass.id,
                certificado=template.code,
            )
            database.session.add(certification)
            database.session.commit()

            return certification.id, masterclass.id

    @pytest.mark.skipif(sys.platform == "win32", reason="This test does not run on Windows.")
    @patch("weasyprint.CSS")
    @patch("flask_weasyprint.HTML")
    @patch("flask_weasyprint.render_pdf")
    def test_certificate_serve_pdf_course(self, mock_render_pdf, mock_html, mock_css, full_db_setup, client):
        """Test PDF generation for course certificate."""
        app = full_db_setup

        # Create test certification with existing user and course
        with app.app_context():
            # Create certification using existing course "now" and certificate "default"
            certification = Certificacion(
                usuario="student1",  # Use existing student
                curso="now",  # Use existing course
                certificado="default",  # Use existing certificate template
            )
            database.session.add(certification)
            database.session.commit()
            cert_id = certification.id

        # Mock PDF generation
        mock_render_pdf.return_value = b"mock_pdf_content"
        mock_html_instance = MagicMock()
        mock_html.return_value = mock_html_instance

        # Test PDF download
        response = client.get(f"/certificate/download/{cert_id}/")
        assert response.status_code == 200
        assert response.data == b"mock_pdf_content"

        # Verify PDF generation was called correctly
        mock_render_pdf.assert_called_once_with(mock_html_instance, stylesheets=[mock_css.return_value])

    @pytest.mark.skipif(sys.platform == "win32", reason="This test does not run on Windows.")
    @patch("weasyprint.CSS")
    @patch("flask_weasyprint.HTML")
    @patch("flask_weasyprint.render_pdf")
    def test_certificate_serve_pdf_masterclass(self, mock_render_pdf, mock_html, mock_css, full_db_setup, client):
        """Test PDF generation for masterclass certificate."""
        app = full_db_setup
        cert_id, masterclass_id = self.setup_test_certification_with_masterclass(app)

        # Mock PDF generation
        mock_render_pdf.return_value = b"mock_masterclass_pdf"
        mock_html_instance = MagicMock()
        mock_html.return_value = mock_html_instance

        # Test PDF download
        response = client.get(f"/certificate/download/{cert_id}/")
        assert response.status_code == 200
        assert response.data == b"mock_masterclass_pdf"

        # Verify PDF generation was called
        mock_render_pdf.assert_called_once()


class TestCertificateIssuanceWorkflow:
    """Test certificate issuance and release workflows."""

    def setup_course_with_evaluation(self, app):
        """Helper to create course with evaluation for issuance tests."""
        with app.app_context():
            # Create course with evaluation requirement
            course = Curso(
                codigo="ISSUE_TEST_COURSE",
                nombre="Issuance Test Course",
                descripcion_corta="Course for testing issuance",
                descripcion="Course for testing certificate issuance",
                estado="open",
                certificado=True,
                plantilla_certificado="default",
            )
            database.session.add(course)
            database.session.flush()

            # Create a course section first
            section = CursoSeccion(
                curso=course.codigo,
                nombre="Test Section",
                descripcion="Test section for evaluation",
                indice=1,
            )
            database.session.add(section)
            database.session.flush()

            # Create evaluation
            evaluation = Evaluation(
                section_id=section.id,
                title="Final Test",
                description="Final evaluation",
                is_exam=True,
                passing_score=70.0,
            )
            database.session.add(evaluation)

            # Create student user
            student = Usuario(
                usuario="issue_student",
                acceso=proteger_passwd("testpass"),
                nombre="Issue",
                apellido="Student",
                correo_electronico="issue@test.com",
                tipo="student",
                activo=True,
                correo_electronico_verificado=True,
            )
            database.session.add(student)

            database.session.commit()
            return course.codigo, evaluation.id, student.usuario

    def test_certificacion_crear_successful_issuance(self, full_db_setup, client):
        """Test successful certificate issuance via direct route."""
        app = full_db_setup
        course_code, eval_id, student_usuario = self.setup_course_with_evaluation(app)

        # Create passing evaluation submission and course completion
        with app.app_context():
            from now_lms.db import CursoUsuarioAvance

            submission = EvaluationAttempt(
                evaluation_id=eval_id,
                user_id=student_usuario,
                score=85.0,
                passed=True,
            )
            database.session.add(submission)

            # Create course completion record
            avance = CursoUsuarioAvance(
                curso=course_code,
                usuario=student_usuario,
                recursos_requeridos=1,
                recursos_completados=1,
                avance=100.0,
                completado=True,
            )
            database.session.add(avance)
            database.session.commit()

        # Login as instructor
        login_response = client.post(
            "/user/login",
            data={"usuario": "instructor", "acceso": "instructor"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # Issue certificate
        response = client.get(
            f"/certificate/issue/{course_code}/{student_usuario}/default/",
            follow_redirects=True,
        )
        assert response.status_code == 200

        # Verify certification was created
        with app.app_context():
            cert = database.session.execute(
                database.select(Certificacion).filter_by(usuario=student_usuario, curso=course_code)
            ).first()
            assert cert is not None
            assert cert[0].certificado == "default"

    def test_certificacion_crear_failed_requirements(self, full_db_setup, client):
        """Test certificate issuance failure due to unmet requirements."""
        app = full_db_setup
        course_code, eval_id, student_usuario = self.setup_course_with_evaluation(app)

        # Don't create evaluation submission (student hasn't passed)

        # Login as instructor
        login_response = client.post(
            "/user/login",
            data={"usuario": "instructor", "acceso": "instructor"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # Try to issue certificate - should fail
        response = client.get(
            f"/certificate/issue/{course_code}/{student_usuario}/default/",
            follow_redirects=True,
        )
        assert response.status_code == 200
        # Should redirect back to certifications list with error message

    def test_certificacion_generar_post_course_success(self, full_db_setup, client):
        """Test certificate release form POST for course - successful case."""
        app = full_db_setup
        course_code, eval_id, student_usuario = self.setup_course_with_evaluation(app)

        # Create passing evaluation submission and course completion
        with app.app_context():
            from now_lms.db import CursoUsuarioAvance

            submission = EvaluationAttempt(
                evaluation_id=eval_id,
                user_id=student_usuario,
                score=85.0,
                passed=True,
            )
            database.session.add(submission)

            # Create course completion record
            avance = CursoUsuarioAvance(
                curso=course_code,
                usuario=student_usuario,
                recursos_requeridos=1,
                recursos_completados=1,
                avance=100.0,
                completado=True,
            )
            database.session.add(avance)
            database.session.commit()

        # Login as instructor
        login_response = client.post(
            "/user/login",
            data={"usuario": "instructor", "acceso": "instructor"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # Submit certificate release form for course
        response = client.post(
            "/certificate/release/",
            data={
                "content_type": "course",
                "usuario": student_usuario,
                "curso": course_code,
                "template": "default",
                "nota": "85.0",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200

        # Verify certification was created
        with app.app_context():
            cert = database.session.execute(
                database.select(Certificacion).filter_by(usuario=student_usuario, curso=course_code)
            ).first()
            assert cert is not None
            assert cert[0].nota == 85.0

    def test_certificacion_generar_post_masterclass_success(self, full_db_setup, client):
        """Test certificate release form POST for masterclass - successful case."""
        app = full_db_setup

        with app.app_context():
            # Create masterclass
            from datetime import date, time

            masterclass = MasterClass(
                slug="RELEASE_MC_001",
                title="Release Test MasterClass",
                description_public="MasterClass for release testing",
                description_private="Internal description",
                date=date.today(),
                start_time=time(10, 0),
                end_time=time(12, 0),
                platform_name="Zoom",
                platform_url="https://zoom.us/test",
                is_certificate=True,
                instructor_id="instructor",
            )
            database.session.add(masterclass)
            database.session.flush()  # Flush to get the ID

            # Create student
            student = Usuario(
                usuario="mc_release_student",
                acceso=proteger_passwd("testpass"),
                nombre="MC Release",
                apellido="Student",
                correo_electronico="mc_release@test.com",
                tipo="student",
                activo=True,
                correo_electronico_verificado=True,
            )
            database.session.add(student)

            # Create enrollment
            enrollment = MasterClassEnrollment(
                master_class_id=masterclass.id,
                user_id=student.usuario,
                is_confirmed=True,
            )
            database.session.add(enrollment)
            database.session.commit()

            masterclass_id = masterclass.id
            student_usuario = student.usuario

        # Login as instructor
        login_response = client.post(
            "/user/login",
            data={"usuario": "instructor", "acceso": "instructor"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # Submit certificate release form for masterclass
        response = client.post(
            "/certificate/release/",
            data={
                "content_type": "masterclass",
                "usuario": student_usuario,
                "master_class": str(masterclass_id),
                "template": "default",
                "nota": "90.0",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200

        # Verify certification was created
        with app.app_context():
            cert = database.session.execute(
                database.select(Certificacion).filter_by(usuario=student_usuario, master_class_id=masterclass_id)
            ).first()
            assert cert is not None
            assert cert[0].nota == 90.0

    def test_certificacion_generar_validation_errors(self, full_db_setup, client):
        """Test certificate release form validation errors."""
        app = full_db_setup

        # Login as instructor
        login_response = client.post(
            "/user/login",
            data={"usuario": "instructor", "acceso": "instructor"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # Test missing course for course content type
        response = client.post(
            "/certificate/release/",
            data={
                "content_type": "course",
                "usuario": "student1",
                "template": "default",
                "nota": "85.0",
                # Missing curso field
            },
            follow_redirects=False,
        )
        assert response.status_code == 200
        assert b"Por favor selecciona un curso" in response.data

        # Test missing masterclass for masterclass content type
        response = client.post(
            "/certificate/release/",
            data={
                "content_type": "masterclass",
                "usuario": "student1",
                "template": "default",
                "nota": "85.0",
                # Missing master_class field
            },
            follow_redirects=False,
        )
        assert response.status_code == 200
        assert b"Por favor selecciona una clase magistral" in response.data

    def test_certificacion_generar_masterclass_enrollment_required(self, full_db_setup, client):
        """Test masterclass certificate requires enrollment."""
        app = full_db_setup

        with app.app_context():
            # Create masterclass
            from datetime import date, time

            masterclass = MasterClass(
                slug="ENROLLMENT_MC",
                title="Enrollment Required MasterClass",
                description_public="MasterClass requiring enrollment",
                description_private="Internal description",
                date=date.today(),
                start_time=time(10, 0),
                end_time=time(12, 0),
                platform_name="Zoom",
                platform_url="https://zoom.us/test",
                is_certificate=True,
                instructor_id="instructor",
            )
            database.session.add(masterclass)

            # Create student (no enrollment)
            student = Usuario(
                usuario="no_enrollment_student",
                acceso=proteger_passwd("testpass"),
                nombre="No Enrollment",
                apellido="Student",
                correo_electronico="no_enrollment@test.com",
                tipo="student",
                activo=True,
                correo_electronico_verificado=True,
            )
            database.session.add(student)
            database.session.commit()

            masterclass_id = masterclass.id
            student_usuario = student.usuario

        # Login as instructor
        login_response = client.post(
            "/user/login",
            data={"usuario": "instructor", "acceso": "instructor"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # Try to issue certificate without enrollment
        response = client.post(
            "/certificate/release/",
            data={
                "content_type": "masterclass",
                "usuario": student_usuario,
                "master_class": str(masterclass_id),
                "template": "default",
                "nota": "90.0",
            },
            follow_redirects=False,
        )
        assert response.status_code == 200
        assert b"debe estar inscrito y confirmado" in response.data


class TestProgramCertificatesComprehensive:
    """Test program certificate functionality comprehensively."""

    def setup_program_certification(self, app):
        """Helper to create program certification setup."""
        with app.app_context():
            # Create user
            user = Usuario(
                usuario="program_cert_user",
                acceso=proteger_passwd("testpass"),
                nombre="Program",
                apellido="Certificate User",
                correo_electronico="program_cert@test.com",
                tipo="student",
                activo=True,
                correo_electronico_verificado=True,
            )
            database.session.add(user)

            # Create program
            program = Programa(
                codigo="PROG_CERT_001",
                nombre="Certificate Program",
                descripcion="Program that awards certificates",
                estado="open",
            )
            database.session.add(program)
            database.session.flush()  # Flush to get the ID

            # Create certificate template
            template = Certificado(
                code="PROGRAM_CERT_TEMPLATE",
                titulo="Program Certificate Template",
                html="<h1>{{usuario.nombre}} {{usuario.apellido}}</h1><p>Program: {{programa.nombre}}</p>",
                css="h1 { color: purple; } p { font-size: 16px; }",
                habilitado=True,
                publico=True,
            )
            database.session.add(template)
            database.session.flush()  # Flush to get the code

            # Create program certification
            program_cert = CertificacionPrograma(
                usuario=user.usuario,
                programa=program.id,
                certificado=template.code,
            )
            database.session.add(program_cert)
            database.session.commit()

            return program_cert.id, program.id, user.usuario

    @patch("qrcode.make")
    def test_certificacion_programa_qr(self, mock_qr_make, full_db_setup, client):
        """Test QR code generation for program certificates."""
        app = full_db_setup
        cert_id, program_id, user_id = self.setup_program_certification(app)

        # Mock QR code generation
        mock_qr = MagicMock()
        mock_qr_make.return_value = mock_qr

        def mock_save(buffer, format):
            buffer.write(b"mock_program_qr_data")

        mock_qr.save = mock_save

        # Test QR generation
        response = client.get(f"/certificate/program/get_as_qr/{cert_id}/")
        assert response.status_code == 200
        assert response.mimetype == "image/png"
        assert b"mock_program_qr_data" in response.data
        assert "QR_programa.png" in response.headers["Content-Disposition"]

        # Verify QR code generation
        mock_qr_make.assert_called_once()
        call_args = mock_qr_make.call_args[0]
        assert f"/certificate/program/view/{cert_id}" in call_args[0]

    def test_certificacion_programa_view(self, full_db_setup, client):
        """Test program certificate viewing."""
        app = full_db_setup
        cert_id, program_id, user_id = self.setup_program_certification(app)

        # Test certificate view
        response = client.get(f"/certificate/program/view/{cert_id}/")
        assert response.status_code == 200
        # Should contain user name and program name
        assert b"Program Certificate User" in response.data
        assert b"Certificate Program" in response.data

    @pytest.mark.skipif(sys.platform == "win32", reason="This test does not run on Windows.")
    @patch("weasyprint.CSS")
    @patch("flask_weasyprint.HTML")
    @patch("flask_weasyprint.render_pdf")
    def test_certificate_programa_serve_pdf(self, mock_render_pdf, mock_html, mock_css, full_db_setup, client):
        """Test program certificate PDF generation."""
        app = full_db_setup
        cert_id, program_id, user_id = self.setup_program_certification(app)

        # Mock PDF generation
        mock_render_pdf.return_value = b"mock_program_pdf_content"
        mock_html_instance = MagicMock()
        mock_html.return_value = mock_html_instance

        # Test PDF download
        response = client.get(f"/certificate/program/download/{cert_id}/")
        assert response.status_code == 200
        assert response.data == b"mock_program_pdf_content"

        # Verify PDF generation was called correctly
        mock_render_pdf.assert_called_once_with(mock_html_instance, stylesheets=[mock_css.return_value])

    @pytest.mark.skipif(sys.platform == "win32", reason="This test does not run on Windows.")
    def test_program_certificate_404_handling(self, full_db_setup, client):
        """Test 404 handling for non-existent program certificates."""
        app = full_db_setup

        # Test non-existent program certificate view
        response = client.get("/certificate/program/view/nonexistent_id/")
        assert response.status_code == 404

        # Test non-existent program certificate PDF
        response = client.get("/certificate/program/download/nonexistent_id/")
        assert response.status_code == 404

        # Test QR for non-existent program certificate
        response = client.get("/certificate/program/get_as_qr/nonexistent_id/")
        assert response.status_code == 200  # QR generation doesn't validate existence


class TestCertificateErrorHandlingAdvanced:
    """Test advanced error handling scenarios."""

    def test_certificate_creation_integrity_error_handling(self, full_db_setup, client):
        """Test certificate creation handles database errors properly."""
        app = full_db_setup

        # Login as admin
        login_response = client.post(
            "/user/login",
            data={"usuario": "lms-admin", "acceso": "lms-admin"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # Try to create certificate with invalid foreign key - this should trigger OperationalError handling
        with patch("now_lms.vistas.certificates.database.session.commit") as mock_commit:
            from sqlalchemy.exc import OperationalError

            mock_commit.side_effect = OperationalError("Mock DB error", None, None)

            response = client.post(
                "/certificate/new",
                data={
                    "titulo": "Error Test Certificate",
                    "descripcion": "Test error handling",
                    "html": "<h1>Test</h1>",
                    "css": "h1 { color: red; }",
                },
                follow_redirects=True,
            )
            assert response.status_code == 200
            # Should show error message and redirect

    def test_certificate_edit_error_handling(self, full_db_setup, client):
        """Test certificate editing error handling."""
        app = full_db_setup

        # Create test certificate
        with app.app_context():
            cert = Certificado(
                code="ERROR_TEST_CERT",
                titulo="Error Test Certificate",
                descripcion="For testing error handling",
                html="<h1>Test</h1>",
                css="h1 { color: red; }",
                habilitado=True,
                publico=True,
            )
            database.session.add(cert)
            database.session.commit()
            cert_id = cert.id

        # Login as admin
        login_response = client.post(
            "/user/login",
            data={"usuario": "lms-admin", "acceso": "lms-admin"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # Try to edit with database error
        with patch("now_lms.vistas.certificates.database.session.commit") as mock_commit:
            from sqlalchemy.exc import OperationalError

            mock_commit.side_effect = OperationalError("Mock edit error", None, None)

            response = client.post(
                f"/certificate/{cert_id}/edit",
                data={
                    "titulo": "Updated Error Test",
                    "descripcion": "Updated description",
                    "html": "<h1>Updated</h1>",
                    "css": "h1 { color: blue; }",
                    "habilitado": True,
                    "publico": True,
                },
                follow_redirects=False,
            )
            assert response.status_code == 302  # Should redirect

    def test_certificacion_generar_database_error(self, full_db_setup, client):
        """Test certificate release form database error handling."""
        app = full_db_setup

        # Login as instructor
        login_response = client.post(
            "/user/login",
            data={"usuario": "instructor", "acceso": "instructor"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # Try to generate certificate with database error
        with patch("now_lms.vistas.certificates.database.session.commit") as mock_commit:
            from sqlalchemy.exc import OperationalError

            mock_commit.side_effect = OperationalError("Mock generation error", None, None)

            response = client.post(
                "/certificate/release/",
                data={
                    "content_type": "course",
                    "usuario": "student1",
                    "curso": "now",
                    "template": "default",
                    "nota": "85.0",
                },
                follow_redirects=True,
            )
            assert response.status_code == 200
            # Should handle error and redirect to /instructor


class TestCertificateTemplateRendering:
    """Test certificate template rendering with different contexts."""

    def test_certificacion_course_vs_masterclass_context(self, full_db_setup, client):
        """Test certificate rendering properly handles course vs masterclass context."""
        app = full_db_setup

        # Create test certification with course
        with app.app_context():
            user = Usuario(
                usuario="context_test_user",
                acceso=proteger_passwd("testpass"),
                nombre="Context",
                apellido="Test",
                correo_electronico="context@test.com",
                tipo="student",
                activo=True,
                correo_electronico_verificado=True,
            )
            database.session.add(user)

            # Create a course for the certification
            course = Curso(
                codigo="CONTEXT_COURSE",
                nombre="Context Test Course",
                descripcion_corta="Course for context testing",
                descripcion="Course for testing certificate context",
                estado="open",
                certificado=True,
                plantilla_certificado="default",
            )
            database.session.add(course)
            database.session.flush()

            # Create certification with course
            certification = Certificacion(
                usuario=user.usuario,
                curso=course.codigo,
                certificado="default",
            )
            database.session.add(certification)
            database.session.commit()
            cert_id = certification.id

        # Test certificate rendering - should include course context
        response = client.get(f"/certificate/certificate/{cert_id}/")
        assert response.status_code == 200
        # Should contain rendered content with course context
        assert b"Context Test" in response.data

        # Test certificate view - should include course context
        response = client.get(f"/certificate/view/{cert_id}")
        assert response.status_code == 200
        assert b"Context Test" in response.data
