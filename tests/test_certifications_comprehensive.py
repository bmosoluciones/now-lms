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

"""Comprehensive tests for Certification functionality - Basic version."""


from now_lms.db import (
    Certificacion,
    Certificado,
    Curso,
    Usuario,
    database,
)


class TestCertificateTemplateManagement:
    """Test certificate template creation and management."""

    def test_certificate_template_creation(self, minimal_db_setup):
        """Test basic certificate template creation."""
        template = Certificado(
            code="TEMPLATE001",
            titulo="Basic Certificate Template",
            habilitado=True,
            publico=True,
        )
        database.session.add(template)
        database.session.commit()

        # Verify template creation
        retrieved = database.session.execute(database.select(Certificado).filter_by(code="TEMPLATE001")).scalar_one()

        assert retrieved.titulo == "Basic Certificate Template"
        assert retrieved.habilitado is True
        assert retrieved.publico is True

    def test_certificate_template_with_content(self, minimal_db_setup):
        """Test certificate template with HTML and CSS content."""
        template = Certificado(
            code="CONTENT_TEMPLATE",
            titulo="Certificate with Content",
            html="<h1>Certificate of Completion</h1><p>{{student_name}}</p>",
            css="h1 { color: blue; } p { font-size: 14px; }",
            habilitado=True,
            publico=True,
        )
        database.session.add(template)
        database.session.commit()

        # Verify content
        retrieved = database.session.execute(database.select(Certificado).filter_by(code="CONTENT_TEMPLATE")).scalar_one()

        assert "Certificate of Completion" in retrieved.html
        assert "{{student_name}}" in retrieved.html
        assert "color: blue" in retrieved.css


class TestCertificationForCourses:
    """Test certification generation and management for courses."""

    def test_course_certification_basic(self, minimal_db_setup):
        """Test basic certification for course completion."""
        # Create certificate template
        template = Certificado(
            code="COURSE_CERT",
            titulo="Course Completion Certificate",
            habilitado=True,
        )
        database.session.add(template)

        # Create course
        course = Curso(
            codigo="CERT001",
            nombre="Certification Course",
            descripcion_corta="Course that awards certificates",
            descripcion="Course that awards certificates",
            estado="open",
            certificado=True,
            plantilla_certificado="COURSE_CERT",
        )
        database.session.add(course)
        database.session.commit()

        # Verify course is configured for certification
        retrieved_course = database.session.execute(database.select(Curso).filter_by(codigo="CERT001")).scalar_one()

        assert retrieved_course.certificado is True
        assert retrieved_course.plantilla_certificado == "COURSE_CERT"

    def test_certificate_generation_process(self, minimal_db_setup):
        """Test certificate generation for completed course."""
        # Create user
        user = Usuario(
            usuario="cert_student",
            acceso=b"password123",
            nombre="Certificate",
            apellido="Student",
            correo_electronico="cert@test.com",
            tipo="student",
        )
        database.session.add(user)

        # Create certificate template
        template = Certificado(
            code="COMPLETION_CERT",
            titulo="Course Completion Certificate",
            html="<h1>Certificate of Completion</h1><p>{{student_name}} has completed the course</p>",
            habilitado=True,
        )
        database.session.add(template)

        # Create course with certification
        course = Curso(
            codigo="CERT002",
            nombre="Certificate Course",
            descripcion_corta="Course with certificate",
            descripcion="Course with certificate",
            estado="open",
            certificado=True,
            plantilla_certificado="COMPLETION_CERT",
        )
        database.session.add(course)
        database.session.commit()

        # Create certification record
        certification = Certificacion(
            usuario=user.usuario,
            curso=course.codigo,
            certificado="COMPLETION_CERT",
        )
        database.session.add(certification)
        database.session.commit()

        # Verify certification
        retrieved = database.session.execute(database.select(Certificacion).filter_by(usuario=user.usuario)).scalar_one()

        assert retrieved.certificado == "COMPLETION_CERT"
        assert retrieved.curso == course.codigo
