"""
Test to demonstrate and fix the certificate issuance bug.

This test shows that certificates are incorrectly issued when all resources
are completed, even when evaluations exist and haven't been passed.
"""

from datetime import datetime


class TestCertificateBug:
    """Test class for certificate issuance bug."""

    def test_certificate_bug_reproduction(self, session_full_db_setup):
        """
        Test that reproduces the bug where certificates are issued
        when resources are completed but evaluations haven't been passed.
        """
        from now_lms.db import (
            Curso,
            CursoSeccion,
            CursoRecurso,
            CursoUsuarioAvance,
            CursoRecursoAvance,
            Evaluation,
            Usuario,
            Certificacion,
            database,
        )
        from now_lms.vistas.courses import _actualizar_avance_curso

        with session_full_db_setup.app_context():
            # Create test user
            user = Usuario(
                usuario="bug_test_student",
                acceso=b"password123",
                nombre="Bug Test",
                apellido="Student",
                correo_electronico="bugtest@example.com",
                tipo="student",
            )
            database.session.add(user)

            # Create test course with certificate enabled
            course = Curso(
                codigo="BUG_COURSE",
                nombre="Bug Test Course",
                descripcion_corta="Test course for bug",
                descripcion="Course for testing the certificate bug",
                estado="open",
                certificado=True,
                plantilla_certificado="default",
            )
            database.session.add(course)

            # Create course section
            section = CursoSeccion(
                curso="BUG_COURSE",
                nombre="Bug Test Section",
                descripcion="Test section",
                indice=1,
            )
            database.session.add(section)
            database.session.flush()  # Get section ID

            # Create required resource
            resource = CursoRecurso(
                curso="BUG_COURSE",
                seccion=section.id,
                nombre="Bug Test Resource",
                descripcion="Test resource",
                tipo="text",
                requerido="required",
                indice=1,
            )
            database.session.add(resource)
            database.session.flush()  # Get resource ID

            # Create evaluation for the course (this makes it so certificate should NOT be issued automatically)
            evaluation = Evaluation(
                section_id=section.id,
                title="Bug Test Evaluation",
                description="Test evaluation that must be passed for certificate",
                is_exam=False,
                passing_score=70.0,
                max_attempts=3,
            )
            database.session.add(evaluation)
            database.session.commit()

            # Mark resource as completed
            resource_progress = CursoRecursoAvance(
                usuario="bug_test_student",
                curso="BUG_COURSE",
                recurso=resource.id,
                completado=True,
                requerido="required",
            )
            database.session.add(resource_progress)
            database.session.commit()

            # Check that no certificate exists yet
            cert_count_before = (
                database.session.execute(
                    database.select(Certificacion).filter_by(usuario="bug_test_student", curso="BUG_COURSE")
                )
                .scalars()
                .all()
            )

            print(f"Certificates before update: {len(cert_count_before)}")
            assert len(cert_count_before) == 0, "No certificate should exist before course update"

            # Call the function that updates course progress within a test client context
            # This should trigger the bug - issuing a certificate without checking evaluations
            with session_full_db_setup.test_request_context():
                _actualizar_avance_curso("BUG_COURSE", "bug_test_student")

            # Check if a certificate was incorrectly issued
            cert_count_after = (
                database.session.execute(
                    database.select(Certificacion).filter_by(usuario="bug_test_student", curso="BUG_COURSE")
                )
                .scalars()
                .all()
            )

            # Check if course is marked as completed
            course_progress = (
                database.session.execute(
                    database.select(CursoUsuarioAvance).filter_by(usuario="bug_test_student", curso="BUG_COURSE")
                )
                .scalars()
                .first()
            )

            print(f"Certificates after update: {len(cert_count_after)}")
            print(f"Course marked as completed: {course_progress.completado if course_progress else 'No progress record'}")

            # The bug: certificate is issued even though evaluation wasn't passed
            if len(cert_count_after) > 0:
                print("BUG REPRODUCED: Certificate was issued without passing evaluations!")
                print(f"Certificate ID: {cert_count_after[0].id}")
                # This should fail to show the bug exists
                assert False, "Certificate was incorrectly issued without passing evaluations"
            else:
                print("Bug not reproduced - certificate was not issued (this is the correct behavior)")
                # This means the bug is already fixed or test setup is wrong
                assert True

    def test_certificate_correctly_issued_after_evaluation_passed(self, session_full_db_setup):
        """
        Test that certificates ARE issued when both resources and evaluations are completed.
        """
        from now_lms.db import (
            Curso,
            CursoSeccion,
            CursoRecurso,
            CursoUsuarioAvance,
            CursoRecursoAvance,
            Evaluation,
            EvaluationAttempt,
            Usuario,
            Certificacion,
            database,
        )
        from now_lms.vistas.courses import _actualizar_avance_curso

        with session_full_db_setup.app_context():
            # Create test user
            user = Usuario(
                usuario="good_test_student",
                acceso=b"password123",
                nombre="Good Test",
                apellido="Student",
                correo_electronico="goodtest@example.com",
                tipo="student",
            )
            database.session.add(user)

            # Create test course with certificate enabled
            course = Curso(
                codigo="GOOD_COURSE",
                nombre="Good Test Course",
                descripcion_corta="Test course for correct behavior",
                descripcion="Course for testing correct certificate issuance",
                estado="open",
                certificado=True,
                plantilla_certificado="default",
            )
            database.session.add(course)

            # Create course section
            section = CursoSeccion(
                curso="GOOD_COURSE",
                nombre="Good Test Section",
                descripcion="Test section",
                indice=1,
            )
            database.session.add(section)
            database.session.flush()  # Get section ID

            # Create required resource
            resource = CursoRecurso(
                curso="GOOD_COURSE",
                seccion=section.id,
                nombre="Good Test Resource",
                descripcion="Test resource",
                tipo="text",
                requerido="required",
                indice=1,
            )
            database.session.add(resource)
            database.session.flush()  # Get resource ID

            # Create evaluation for the course
            evaluation = Evaluation(
                section_id=section.id,
                title="Good Test Evaluation",
                description="Test evaluation that will be passed",
                is_exam=False,
                passing_score=70.0,
                max_attempts=3,
            )
            database.session.add(evaluation)
            database.session.flush()  # Get evaluation ID

            # Create a PASSING attempt for the evaluation
            passing_attempt = EvaluationAttempt(
                evaluation_id=evaluation.id,
                user_id="good_test_student",
                score=85.0,
                passed=True,
                submitted_at=datetime.now(),
            )
            database.session.add(passing_attempt)

            # Mark resource as completed
            resource_progress = CursoRecursoAvance(
                usuario="good_test_student",
                curso="GOOD_COURSE",
                recurso=resource.id,
                completado=True,
                requerido="required",
            )
            database.session.add(resource_progress)
            database.session.commit()

            # Check that no certificate exists yet
            cert_count_before = (
                database.session.execute(
                    database.select(Certificacion).filter_by(usuario="good_test_student", curso="GOOD_COURSE")
                )
                .scalars()
                .all()
            )

            print(f"Certificates before update: {len(cert_count_before)}")
            assert len(cert_count_before) == 0, "No certificate should exist before course update"

            # Call the function that updates course progress
            # This should now correctly issue a certificate because all requirements are met
            with session_full_db_setup.test_request_context():
                _actualizar_avance_curso("GOOD_COURSE", "good_test_student")

            # Check if a certificate was correctly issued
            cert_count_after = (
                database.session.execute(
                    database.select(Certificacion).filter_by(usuario="good_test_student", curso="GOOD_COURSE")
                )
                .scalars()
                .all()
            )

            # Check if course is marked as completed
            course_progress = (
                database.session.execute(
                    database.select(CursoUsuarioAvance).filter_by(usuario="good_test_student", curso="GOOD_COURSE")
                )
                .scalars()
                .first()
            )

            print(f"Certificates after update: {len(cert_count_after)}")
            print(f"Course marked as completed: {course_progress.completado if course_progress else 'No progress record'}")

            # Should issue certificate because all requirements are met
            assert len(cert_count_after) == 1, "Certificate should be issued when all requirements are met"
            assert course_progress.completado is True, "Course should be marked as completed"
            print("SUCCESS: Certificate correctly issued after both resources and evaluations completed")

    def test_certificate_issued_for_course_without_evaluations(self, session_full_db_setup):
        """
        Test that certificates ARE still issued for courses without evaluations when resources are completed.
        """
        from now_lms.db import (
            Curso,
            CursoSeccion,
            CursoRecurso,
            CursoUsuarioAvance,
            CursoRecursoAvance,
            Usuario,
            Certificacion,
            database,
        )
        from now_lms.vistas.courses import _actualizar_avance_curso

        with session_full_db_setup.app_context():
            # Create test user
            user = Usuario(
                usuario="no_eval_student",
                acceso=b"password123",
                nombre="No Eval",
                apellido="Student",
                correo_electronico="noeval@example.com",
                tipo="student",
            )
            database.session.add(user)

            # Create test course with certificate enabled but NO evaluations
            course = Curso(
                codigo="NO_EVAL_COURSE",
                nombre="No Evaluation Course",
                descripcion_corta="Course without evaluations",
                descripcion="Course for testing certificate issuance without evaluations",
                estado="open",
                certificado=True,
                plantilla_certificado="default",
            )
            database.session.add(course)

            # Create course section
            section = CursoSeccion(
                curso="NO_EVAL_COURSE",
                nombre="No Eval Section",
                descripcion="Test section",
                indice=1,
            )
            database.session.add(section)
            database.session.flush()  # Get section ID

            # Create required resource
            resource = CursoRecurso(
                curso="NO_EVAL_COURSE",
                seccion=section.id,
                nombre="No Eval Resource",
                descripcion="Test resource",
                tipo="text",
                requerido="required",
                indice=1,
            )
            database.session.add(resource)
            database.session.flush()  # Get resource ID

            # Note: NO evaluations are created for this course

            # Mark resource as completed
            resource_progress = CursoRecursoAvance(
                usuario="no_eval_student",
                curso="NO_EVAL_COURSE",
                recurso=resource.id,
                completado=True,
                requerido="required",
            )
            database.session.add(resource_progress)
            database.session.commit()

            # Check that no certificate exists yet
            cert_count_before = (
                database.session.execute(
                    database.select(Certificacion).filter_by(usuario="no_eval_student", curso="NO_EVAL_COURSE")
                )
                .scalars()
                .all()
            )

            print(f"Certificates before update: {len(cert_count_before)}")
            assert len(cert_count_before) == 0, "No certificate should exist before course update"

            # Call the function that updates course progress
            # This should issue a certificate because there are no evaluations to check
            with session_full_db_setup.test_request_context():
                _actualizar_avance_curso("NO_EVAL_COURSE", "no_eval_student")

            # Check if a certificate was correctly issued
            cert_count_after = (
                database.session.execute(
                    database.select(Certificacion).filter_by(usuario="no_eval_student", curso="NO_EVAL_COURSE")
                )
                .scalars()
                .all()
            )

            # Check if course is marked as completed
            course_progress = (
                database.session.execute(
                    database.select(CursoUsuarioAvance).filter_by(usuario="no_eval_student", curso="NO_EVAL_COURSE")
                )
                .scalars()
                .first()
            )

            print(f"Certificates after update: {len(cert_count_after)}")
            print(f"Course marked as completed: {course_progress.completado if course_progress else 'No progress record'}")

            # Should issue certificate because no evaluations exist
            assert len(cert_count_after) == 1, "Certificate should be issued for courses without evaluations"
            assert course_progress.completado is True, "Course should be marked as completed"
            print("SUCCESS: Certificate correctly issued for course without evaluations")
