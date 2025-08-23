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
)


class TestCertificateTemplateManagement:
    """Test certificate template creation and management."""

    def test_certificate_template_creation(self, isolated_db_session):
        """Test basic certificate template creation."""
        template = Certificado(
            code="TEMPLATE001",
            titulo="Basic Certificate Template",
            habilitado=True,
            publico=True,
        )
        isolated_db_session.add(template)
        isolated_db_session.flush()

        # Verify template creation
        from now_lms.db import select

        retrieved = isolated_db_session.execute(select(Certificado).filter_by(code="TEMPLATE001")).scalar_one()

        assert retrieved.titulo == "Basic Certificate Template"
        assert retrieved.habilitado is True
        assert retrieved.publico is True

    def test_certificate_template_with_content(self, isolated_db_session):
        """Test certificate template with HTML and CSS content."""
        template = Certificado(
            code="CONTENT_TEMPLATE",
            titulo="Certificate with Content",
            html="<h1>Certificate of Completion</h1><p>{{student_name}}</p>",
            css="h1 { color: blue; } p { font-size: 14px; }",
            habilitado=True,
            publico=True,
        )
        isolated_db_session.add(template)
        isolated_db_session.flush()

        # Verify content
        from now_lms.db import select

        retrieved = isolated_db_session.execute(select(Certificado).filter_by(code="CONTENT_TEMPLATE")).scalar_one()

        assert "Certificate of Completion" in retrieved.html
        assert "{{student_name}}" in retrieved.html
        assert "color: blue" in retrieved.css


class TestCertificationForCourses:
    """Test certification generation and management for courses."""

    def test_course_certification_basic(self, isolated_db_session):
        """Test basic certification for course completion."""
        # Create certificate template
        template = Certificado(
            code="COURSE_CERT",
            titulo="Course Completion Certificate",
            habilitado=True,
        )
        isolated_db_session.add(template)

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
        isolated_db_session.add(course)
        isolated_db_session.flush()

        # Verify course is configured for certification
        from now_lms.db import select

        retrieved_course = isolated_db_session.execute(select(Curso).filter_by(codigo="CERT001")).scalar_one()

        assert retrieved_course.certificado is True
        assert retrieved_course.plantilla_certificado == "COURSE_CERT"

    def test_certificate_generation_process(self, isolated_db_session):
        """Test certificate generation for completed course."""
        from now_lms.auth import proteger_passwd

        # Create user
        user = Usuario(
            usuario="cert_student",
            acceso=proteger_passwd("password123"),
            nombre="Certificate",
            apellido="Student",
            correo_electronico="cert@test.com",
            tipo="student",
        )
        isolated_db_session.add(user)

        # Create certificate template
        template = Certificado(
            code="COMPLETION_CERT",
            titulo="Course Completion Certificate",
            html="<h1>Certificate of Completion</h1><p>{{student_name}} has completed the course</p>",
            habilitado=True,
        )
        isolated_db_session.add(template)

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
        isolated_db_session.add(course)
        isolated_db_session.flush()

        # Create certification record
        certification = Certificacion(
            usuario=user.usuario,
            curso=course.codigo,
            certificado="COMPLETION_CERT",
        )
        isolated_db_session.add(certification)
        isolated_db_session.flush()

        # Verify certification
        from now_lms.db import select

        retrieved = isolated_db_session.execute(select(Certificacion).filter_by(usuario=user.usuario)).scalar_one()

        assert retrieved.certificado == "COMPLETION_CERT"
        assert retrieved.curso == course.codigo
