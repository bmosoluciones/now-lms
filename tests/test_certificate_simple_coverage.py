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

"""Simplified comprehensive tests for Certificate views to improve coverage."""

import sys
from unittest.mock import MagicMock, patch

import pytest

from now_lms.db import Certificacion, CertificacionPrograma, Certificado, Programa, database
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


class TestCertificatePDFGenerationSimple:
    """Test PDF generation routes with minimal setup."""

    @pytest.mark.skipif(sys.platform == "win32", reason="This test does not run on Windows.")
    @patch("weasyprint.CSS")
    @patch("flask_weasyprint.HTML")
    @patch("flask_weasyprint.render_pdf")
    def test_certificate_serve_pdf_existing_data(self, mock_render_pdf, mock_html, mock_css, isolated_db_session):
        """Test PDF generation using existing data."""
        # isolated_db_session works within session_full_db_setup context
        # Get the Flask app from the current app context
        from flask import current_app

        client = current_app.test_client()

        # Use existing student and create minimal certification
        certification = Certificacion(
            usuario="student1",  # Use existing student
            curso="now",  # Use existing course
            certificado="default",  # Use existing certificate template
        )
        isolated_db_session.add(certification)
        isolated_db_session.flush()  # Get ID without committing
        cert_id = certification.id

        # Mock PDF generation
        mock_render_pdf.return_value = b"mock_pdf_content"
        mock_html_instance = MagicMock()
        mock_html.return_value = mock_html_instance

        # Test PDF download
        response = client.get(f"/certificate/download/{cert_id}/")
        assert response.status_code == 200
        assert response.data == b"mock_pdf_content"

        # Verify PDF generation was called
        mock_render_pdf.assert_called_once()


class TestCertificateIssuanceSimple:
    """Test certificate issuance with mocked evaluations."""

    @patch("now_lms.vistas.evaluation_helpers.can_user_receive_certificate")
    def test_certificacion_crear_with_mocked_evaluation(self, mock_can_receive, isolated_db_session):
        """Test certificate issuance with mocked evaluation check."""
        from flask import current_app

        client = current_app.test_client()

        # Mock successful evaluation check
        mock_can_receive.return_value = (True, "")

        # Login as instructor
        login_response = client.post(
            "/user/login",
            data={"usuario": "instructor", "acceso": "instructor"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # Issue certificate
        response = client.get(
            "/certificate/issue/now/student1/default/",
            follow_redirects=True,
        )
        assert response.status_code == 200

        # Verify certification was created
        cert = isolated_db_session.execute(database.select(Certificacion).filter_by(usuario="student1", curso="now")).first()
        assert cert is not None

    @patch("now_lms.vistas.evaluation_helpers.can_user_receive_certificate")
    def test_certificacion_crear_failed_evaluation(self, mock_can_receive, session_full_db_setup):
        """Test certificate issuance failure due to evaluation."""
        client = session_full_db_setup.test_client()

        # Mock failed evaluation check
        mock_can_receive.return_value = (False, "No aprobó las evaluaciones")

        # Login as instructor
        login_response = client.post(
            "/user/login",
            data={"usuario": "instructor", "acceso": "instructor"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # Try to issue certificate - should fail
        response = client.get(
            "/certificate/issue/now/student1/default/",
            follow_redirects=True,
        )
        assert response.status_code == 200
        # Should redirect with error message

    def test_certificacion_generar_get_form(self, session_full_db_setup):
        """Test certificate release form GET."""
        client = session_full_db_setup.test_client()

        # Login as instructor
        login_response = client.post(
            "/user/login",
            data={"usuario": "instructor", "acceso": "instructor"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # Access certificate release form
        response = client.get("/certificate/release/")
        assert response.status_code == 200
        assert b"certificado" in response.data.lower() or b"certificate" in response.data.lower()

    @patch("now_lms.vistas.evaluation_helpers.can_user_receive_certificate")
    def test_certificacion_generar_post_course(self, mock_can_receive, isolated_db_session):
        """Test certificate release form POST for course."""
        from flask import current_app

        client = current_app.test_client()

        # Mock successful evaluation check
        mock_can_receive.return_value = (True, "")

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
                "usuario": "student1",
                "curso": "now",
                "template": "default",
                "nota": "85.0",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200

    def test_certificacion_generar_validation_errors(self, session_full_db_setup):
        """Test certificate release form validation errors."""
        client = session_full_db_setup.test_client()

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


class TestProgramCertificatesSimple:
    """Test program certificate functionality with simplified setup."""

    def setup_minimal_program_certification(self, app):
        """Helper to create minimal program certification."""
        with app.app_context():
            # Create minimal program
            program = Programa(
                nombre="Test Program",
                codigo="PROG001",
                descripcion="Test program for certificates",
                publico=True,
            )
            database.session.add(program)
            database.session.flush()  # Get the ID

            # Create program certification using the actual program ID
            program_cert = CertificacionPrograma(
                usuario="student1",  # Use existing student
                programa=program.id,  # Use the actual program ID
                certificado="default",  # Use existing certificate template
            )
            database.session.add(program_cert)
            database.session.commit()

            return program_cert.id, program.id

    @patch("qrcode.make")
    def test_certificacion_programa_qr(self, mock_qr_make, isolated_db_session):
        """Test QR code generation for program certificates."""
        from flask import current_app

        client = current_app.test_client()

        cert_id, program_id = self.setup_minimal_program_certification_isolated(isolated_db_session)

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

    def setup_minimal_program_certification_isolated(self, db_session):
        """Helper to create minimal program certification with isolated session."""
        # Create minimal program
        program = Programa(
            nombre="Test Program",
            codigo="PROG001",
            descripcion="Test program for certificates",
            publico=True,
        )
        db_session.add(program)
        db_session.flush()  # Get the ID

        # Create program certification using the actual program ID
        program_cert = CertificacionPrograma(
            usuario="student1",  # Use existing student
            programa=program.id,  # Use the actual program ID
            certificado="default",  # Use existing certificate template
        )
        db_session.add(program_cert)
        db_session.flush()  # Get the ID without committing

        return program_cert.id, program.id

    @pytest.mark.skipif(sys.platform == "win32", reason="This test does not run on Windows.")
    def test_program_certificate_404_handling(self, session_full_db_setup):
        """Test 404 handling for non-existent program certificates."""
        client = session_full_db_setup.test_client()

        # Test non-existent program certificate view
        response = client.get("/certificate/program/view/nonexistent_id/")
        assert response.status_code == 404

        # Test non-existent program certificate PDF
        response = client.get("/certificate/program/download/nonexistent_id/")
        assert response.status_code == 404


class TestCertificateErrorHandlingAdvanced:
    """Test advanced error handling scenarios."""

    def test_certificate_creation_error_handling(self, session_full_db_setup):
        """Test certificate creation handles database errors."""
        client = session_full_db_setup.test_client()

        # Login as admin
        login_response = client.post(
            "/user/login",
            data={"usuario": "lms-admin", "acceso": "lms-admin"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # Test error handling by mocking commit to raise OperationalError
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

    def test_certificate_edit_error_handling(self, isolated_db_session):
        """Test certificate editing error handling."""
        import uuid
        from flask import current_app

        client = current_app.test_client()

        # Create test certificate with unique identifier
        unique_suffix = str(uuid.uuid4())[:8]
        cert = Certificado(
            code=f"ERROR_TEST_CERT_{unique_suffix}",
            titulo=f"Error Test Certificate {unique_suffix}",
            descripcion="For testing error handling",
            html="<h1>Test</h1>",
            css="h1 { color: red; }",
            habilitado=True,
            publico=True,
        )
        isolated_db_session.add(cert)
        isolated_db_session.flush()  # Get the ID
        cert_id = cert.id

        # Login as admin
        login_response = client.post(
            "/user/login",
            data={"usuario": "lms-admin", "acceso": "lms-admin"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # Test error handling
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

    def test_certificacion_generar_database_error(self, session_full_db_setup):
        """Test certificate release form database error handling."""
        client = session_full_db_setup.test_client()

        # Login as instructor
        login_response = client.post(
            "/user/login",
            data={"usuario": "instructor", "acceso": "instructor"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # Mock database error during certificate generation
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


class TestCertificateTemplateRendering:
    """Test certificate template rendering contexts."""

    def test_certificacion_rendering_with_existing_data(self, isolated_db_session):
        """Test certificate rendering with existing certification."""
        from flask import current_app

        client = current_app.test_client()

        # Create test certification
        certification = Certificacion(
            usuario="student1",  # Use existing student
            curso="now",  # Use existing course
            certificado="default",
        )
        isolated_db_session.add(certification)
        isolated_db_session.flush()  # Get the ID
        cert_id = certification.id

        # Test certificate rendering
        response = client.get(f"/certificate/certificate/{cert_id}/")
        assert response.status_code == 200

        # Test certificate view
        response = client.get(f"/certificate/view/{cert_id}")
        assert response.status_code == 200


class TestCertificateContextHandling:
    """Test certificate context handling for course vs masterclass."""

    def test_certificacion_course_context(self, isolated_db_session):
        """Test certificate with course context."""
        from flask import current_app

        client = current_app.test_client()

        # Create certification with course (no master_class_id)
        certification = Certificacion(
            usuario="student1",
            curso="now",
            master_class_id=None,  # Explicitly no masterclass
            certificado="default",
        )
        isolated_db_session.add(certification)
        isolated_db_session.flush()  # Get the ID
        cert_id = certification.id

        # Test rendering - should use course context
        response = client.get(f"/certificate/certificate/{cert_id}/")
        assert response.status_code == 200
