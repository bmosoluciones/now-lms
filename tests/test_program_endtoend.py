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

"""End-to-end test for complete program certificate workflow."""

from now_lms.db import (
    Certificacion,
    CertificacionPrograma,
    Curso,
    EstudianteCurso,
    Programa,
    ProgramaCurso,
    ProgramaEstudiante,
    Usuario,
    database,
)
from now_lms.auth import proteger_passwd


def test_complete_program_certificate_workflow(full_db_setup, client):
    """Test the complete workflow from program creation to certificate generation."""
    app = full_db_setup

    with app.app_context():
        # 1. Create admin and instructor users
        admin_user = Usuario(
            usuario="prog_admin",
            acceso=proteger_passwd("adminpass"),
            nombre="Program Admin",
            apellido="User",
            correo_electronico="progadmin@test.com",
            tipo="admin",
            activo=True,
            correo_electronico_verificado=True,
        )
        instructor_user = Usuario(
            usuario="prog_instructor",
            acceso=proteger_passwd("instructorpass"),
            nombre="Program Instructor",
            apellido="User",
            correo_electronico="proginstructor@test.com",
            tipo="instructor",
            activo=True,
            correo_electronico_verificado=True,
        )
        student_user = Usuario(
            usuario="prog_student",
            acceso=proteger_passwd("studentpass"),
            nombre="Program Student",
            apellido="User",
            correo_electronico="progstudent@test.com",
            tipo="student",
            activo=True,
            correo_electronico_verificado=True,
        )
        database.session.add_all([admin_user, instructor_user, student_user])
        database.session.commit()

        # 2. Login as instructor to create program and courses
        login_response = client.post(
            "/user/login",
            data={"usuario": "prog_instructor", "acceso": "instructorpass"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # 3. Create a program with certificate enabled
        program_data = {
            "nombre": "Full Stack Development",
            "descripcion": "Complete full stack development program",
            "codigo": "FULLSTACK",
            "precio": 0,
            "certificado": True,
            "plantilla_certificado": "programa",
        }

        # Create program via route test (simulating the actual form)
        # This would typically be done through the /program/new route
        programa = Programa(
            nombre=program_data["nombre"],
            descripcion=program_data["descripcion"],
            codigo=program_data["codigo"],
            precio=program_data["precio"],
            publico=True,
            estado="open",
            certificado=program_data["certificado"],
            plantilla_certificado=program_data["plantilla_certificado"],
            creado_por=instructor_user.id,
        )
        database.session.add(programa)
        database.session.commit()

        # 4. Create courses for the program
        course1 = Curso(
            nombre="Frontend Development",
            codigo="FRONTEND",
            descripcion_corta="HTML, CSS, JavaScript",
            descripcion="Complete frontend development course",
            publico=True,
            estado="open",
            modalidad="self_paced",
            certificado=True,
            plantilla_certificado="default",
            creado_por=instructor_user.id,
        )
        course2 = Curso(
            nombre="Backend Development",
            codigo="BACKEND",
            descripcion_corta="Python, Flask, Databases",
            descripcion="Complete backend development course",
            publico=True,
            estado="open",
            modalidad="self_paced",
            certificado=True,
            plantilla_certificado="default",
            creado_por=instructor_user.id,
        )
        database.session.add_all([course1, course2])
        database.session.commit()

        # 5. Add courses to program
        prog_course1 = ProgramaCurso(
            programa=programa.codigo,
            curso=course1.codigo,
            creado_por=instructor_user.usuario,
        )
        prog_course2 = ProgramaCurso(
            programa=programa.codigo,
            curso=course2.codigo,
            creado_por=instructor_user.usuario,
        )
        database.session.add_all([prog_course1, prog_course2])
        database.session.commit()

        # 6. Enroll student in program
        enrollment = ProgramaEstudiante(
            usuario=student_user.usuario,
            programa=programa.id,
            creado_por=instructor_user.usuario,
        )
        database.session.add(enrollment)
        database.session.commit()

        # 7. Enroll student in courses and mark as paid (for free courses)
        course1_enrollment = EstudianteCurso(
            usuario=student_user.usuario,
            curso=course1.codigo,
            pago=None,  # None for free courses
            creado_por=instructor_user.usuario,
        )
        course2_enrollment = EstudianteCurso(
            usuario=student_user.usuario,
            curso=course2.codigo,
            pago=None,  # None for free courses
            creado_por=instructor_user.usuario,
        )
        database.session.add_all([course1_enrollment, course2_enrollment])
        database.session.commit()

        # 8. Student completes first course - gets course certificate
        course1_cert = Certificacion(
            usuario=student_user.usuario,
            curso=course1.codigo,
            certificado="default",
            creado_por=student_user.usuario,
        )
        database.session.add(course1_cert)
        database.session.commit()

        # Verify first course certificate exists
        cert1 = database.session.execute(
            database.select(Certificacion).filter_by(usuario=student_user.usuario, curso=course1.codigo)
        ).scalar_one_or_none()
        assert cert1 is not None

        # 9. Student completes second course - gets course certificate
        course2_cert = Certificacion(
            usuario=student_user.usuario,
            curso=course2.codigo,
            certificado="default",
            creado_por=student_user.usuario,
        )
        database.session.add(course2_cert)
        database.session.commit()

        # Verify second course certificate exists
        cert2 = database.session.execute(
            database.select(Certificacion).filter_by(usuario=student_user.usuario, curso=course2.codigo)
        ).scalar_one_or_none()
        assert cert2 is not None

        # 10. Verify program completion and automatic certificate generation
        from now_lms.db.tools import verificar_programa_completo

        # Program should be complete
        assert verificar_programa_completo(student_user.usuario, programa.codigo)

        # Generate program certificate (this would happen automatically in the views)
        program_cert = CertificacionPrograma(
            programa=programa.id,
            usuario=student_user.usuario,
            certificado="programa",
            creado_por=student_user.usuario,
        )
        database.session.add(program_cert)
        database.session.commit()

        # 11. Verify program certificate was created
        program_certification = database.session.execute(
            database.select(CertificacionPrograma).filter_by(usuario=student_user.usuario, programa=programa.id)
        ).scalar_one_or_none()

        assert program_certification is not None
        assert program_certification.certificado == "programa"

        # 12. Verify program certificate contains correct course list
        completed_courses = program_certification.get_cursos_completados()
        assert len(completed_courses) == 2
        assert "FRONTEND" in completed_courses
        assert "BACKEND" in completed_courses

        # 13. Test program progress tracking
        from now_lms.db.tools import obtener_progreso_programa

        progress = obtener_progreso_programa(student_user.usuario, programa.codigo)
        assert progress["total"] == 2
        assert progress["completados"] == 2
        assert progress["porcentaje"] == 100.0

        # 14. Verify certificate template exists
        from now_lms.db.certificates_templates import CERTIFICADOS

        program_templates = [cert for cert in CERTIFICADOS if cert[4] == "programa"]
        assert len(program_templates) == 1

        template = program_templates[0]
        assert "programa" in template[2].lower()  # HTML should reference programs


def test_program_certificate_qr_generation(full_db_setup, client):
    """Test QR code generation for program certificates."""
    app = full_db_setup

    with app.app_context():
        # Create minimal test data
        student_user = Usuario(
            usuario="qr_prog_student",
            acceso=proteger_passwd("pass"),
            nombre="QR",
            apellido="Student",
            correo_electronico="qrprog@test.com",
            tipo="student",
            activo=True,
            correo_electronico_verificado=True,
        )
        programa = Programa(
            nombre="QR Test Program",
            codigo="QRTEST",
            descripcion="Program for QR testing",
            publico=True,
            estado="open",
            certificado=True,
            plantilla_certificado="programa",
        )
        database.session.add_all([student_user, programa])
        database.session.commit()

        # Create program certificate
        cert = CertificacionPrograma(
            programa=programa.id,
            usuario=student_user.usuario,
            certificado="programa",
            creado_por=student_user.usuario,
        )
        database.session.add(cert)
        database.session.commit()

        # Test QR code generation route
        qr_response = client.get(f"/certificate/program/get_as_qr/{cert.id}/")
        assert qr_response.status_code == 200
        assert qr_response.mimetype == "image/png"

        # Test certificate view route
        cert_response = client.get(f"/certificate/program/view/{cert.id}/")
        assert cert_response.status_code == 200

        # Certificate HTML should contain program information
        cert_html = cert_response.get_data(as_text=True)
        assert programa.nombre in cert_html
        assert student_user.nombre in cert_html
        assert "CERTIFICADO" in cert_html or "programa" in cert_html.lower()


def test_program_with_no_courses(full_db_setup):
    """Test edge case: program with no courses."""
    app = full_db_setup

    with app.app_context():
        # Create program with no courses
        programa = Programa(
            nombre="Empty Program",
            codigo="EMPTY",
            descripcion="Program with no courses",
            publico=True,
            estado="open",
        )
        database.session.add(programa)
        database.session.commit()

        # Progress should be 0 for all metrics
        from now_lms.db.tools import obtener_progreso_programa

        progress = obtener_progreso_programa("anyuser", "EMPTY")
        assert progress["total"] == 0
        assert progress["completados"] == 0
        assert progress["porcentaje"] == 0
