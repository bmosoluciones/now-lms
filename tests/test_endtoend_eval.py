# Copyright 2021 -2023 William José Moreno Reyes
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

import pytest

from now_lms.db import database

"""
Comprehensive end-to-end tests for evaluation system using session-scoped fixtures.
"""


class TestEndToEndEvaluationSessionFixtures:
    """End-to-end evaluation tests converted to use session-scoped fixtures."""

    @pytest.fixture(scope="function")
    def test_client(self, session_full_db_setup):
        """Provide test client using session fixture."""
        return session_full_db_setup.test_client()

    @pytest.mark.slow
    def test_comprehensive_evaluation_workflow_session(self, session_full_db_setup, test_client):
        """Test complete evaluation workflow from course creation to student completion using session fixture."""
        import time

        # Generate unique identifiers to avoid conflicts
        unique_suffix = int(time.time() * 1000) % 1000000
        instructor_username = f"eval_instructor_{unique_suffix}"
        instructor_email = f"eval_instructor_{unique_suffix}@nowlms.com"
        student_username = f"eval_student_{unique_suffix}"
        student_email = f"eval_student_{unique_suffix}@nowlms.com"
        course_code = f"eval_course_{unique_suffix}"

        from now_lms.auth import proteger_passwd
        from now_lms.db import (
            Curso,
            CursoSeccion,
            EstudianteCurso,
            Evaluation,
            EvaluationAttempt,
            Pago,
            Question,
            QuestionOption,
            Usuario,
        )

        # Step 1: Create instructor user
        with session_full_db_setup.app_context():
            instructor = Usuario(
                usuario=instructor_username,
                acceso=proteger_passwd("instructor_pass"),
                nombre="Evaluation",
                apellido="Instructor",
                correo_electronico=instructor_email,
                tipo="instructor",
                activo=True,
                correo_electronico_verificado=True,
            )
            database.session.add(instructor)
            database.session.commit()

        # Step 2: Login as instructor
        login_response = test_client.post(
            "/user/login",
            data={"usuario": instructor_username, "acceso": "instructor_pass"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # Step 3: Create a free course
        course_response = test_client.post(
            "/course/new_curse",
            data={
                "nombre": "Evaluation Test Course",
                "codigo": course_code,
                "descripcion": "A course for testing evaluations.",
                "descripcion_corta": "Evaluation test course.",
                "nivel": 1,
                "duracion": 4,  # Use integer for weeks
                "publico": True,
                "modalidad": "online",
                "foro_habilitado": True,
                "limitado": False,
                "capacidad": 0,
                "fecha_inicio": "2025-08-10",
                "fecha_fin": "2025-09-10",
                "pagado": False,  # Free course
                "auditable": True,
                "certificado": False,  # Disable certificates to avoid template requirement
                "precio": 0,
            },
            follow_redirects=True,
        )
        assert course_response.status_code == 200  # Success after redirect

        # Verify course was created
        with session_full_db_setup.app_context():
            course = database.session.execute(database.select(Curso).filter_by(codigo=course_code)).scalars().first()
            assert course is not None
            assert course.nombre == "Evaluation Test Course"
            # Course is effectively free if price is 0, regardless of pagado flag
            assert course.precio == 0  # Ensure it's free

        # Step 4: Add a section to the course
        section_response = test_client.post(
            f"/course/{course_code}/new_seccion",
            data={
                "nombre": "Evaluation Section",
                "descripcion": "Section for evaluation testing.",
            },
            follow_redirects=True,
        )
        assert section_response.status_code == 200  # Success after redirect

        # Get the section ID
        with session_full_db_setup.app_context():
            section = (
                database.session.execute(
                    database.select(CursoSeccion).filter_by(curso=course_code, nombre="Evaluation Section")
                )
                .scalars()
                .first()
            )
            assert section is not None
            section_id = section.id

        # Step 5: Create an evaluation for the section
        evaluation_response = test_client.post(
            f"/instructor/courses/{course_code}/sections/{section_id}/evaluations/new",
            data={
                "title": "Test Evaluation",
                "description": "A comprehensive test evaluation",
                "is_exam": False,
                "passing_score": 70.0,
                "max_attempts": 3,
            },
            follow_redirects=True,
        )
        assert evaluation_response.status_code == 200  # Success after redirect

        # Get the evaluation ID
        with session_full_db_setup.app_context():
            evaluation = (
                database.session.execute(database.select(Evaluation).filter_by(section_id=section_id, title="Test Evaluation"))
                .scalars()
                .first()
            )
            assert evaluation is not None
            evaluation_id = evaluation.id

        # Step 6: Add questions to the evaluation
        # Note: Question management would typically be done through instructor interface
        # Since I don't see question creation routes in the instructor views,
        # I'll create questions directly in the database for this test
        with session_full_db_setup.app_context():
            # Create a multiple choice question
            question1 = Question(
                evaluation_id=evaluation_id,
                type="multiple",
                text="What is the capital of France?",
                order=1,
                creado_por=instructor_username,
                modificado_por=instructor_username,
            )
            database.session.add(question1)
            database.session.flush()

            # Add options for the multiple choice question
            option1_1 = QuestionOption(
                question_id=question1.id,
                text="Paris",
                is_correct=True,
                creado_por=instructor_username,
                modificado_por=instructor_username,
            )
            option1_2 = QuestionOption(
                question_id=question1.id,
                text="London",
                is_correct=False,
                creado_por=instructor_username,
                modificado_por=instructor_username,
            )
            option1_3 = QuestionOption(
                question_id=question1.id,
                text="Berlin",
                is_correct=False,
                creado_por=instructor_username,
                modificado_por=instructor_username,
            )

            # Create a boolean question
            question2 = Question(
                evaluation_id=evaluation_id,
                type="boolean",
                text="The Earth is round.",
                order=2,
                creado_por=instructor_username,
                modificado_por=instructor_username,
            )
            database.session.add(question2)
            database.session.flush()

            # Add options for the boolean question
            option2_1 = QuestionOption(
                question_id=question2.id,
                text="true",
                is_correct=True,
                creado_por=instructor_username,
                modificado_por=instructor_username,
            )
            option2_2 = QuestionOption(
                question_id=question2.id,
                text="false",
                is_correct=False,
                creado_por=instructor_username,
                modificado_por=instructor_username,
            )

            database.session.add_all([option1_1, option1_2, option1_3, option2_1, option2_2])
            database.session.commit()

            # Store IDs for later use outside the session
            question1_id = question1.id
            question2_id = question2.id
            option1_1_id = option1_1.id

        # Step 7: Create a student user
        with session_full_db_setup.app_context():
            student = Usuario(
                usuario=student_username,
                acceso=proteger_passwd("student_pass"),
                nombre="Evaluation",
                apellido="Student",
                correo_electronico=student_email,
                tipo="student",
                activo=True,
                correo_electronico_verificado=True,
            )
            database.session.add(student)
            database.session.commit()

        # Logout instructor and login as student
        test_client.get("/user/logout")
        student_login = test_client.post(
            "/user/login",
            data={"usuario": student_username, "acceso": "student_pass"},
            follow_redirects=True,
        )
        assert student_login.status_code == 200

        # Step 8: Enroll student in the free course
        enroll_response = test_client.post(
            f"/course/{course_code}/enroll",
            data={
                "nombre": "Evaluation",
                "apellido": "Student",
                "correo_electronico": student_email,
                "direccion1": "Test Street 123",
                "direccion2": "",
                "pais": "Test Country",
                "provincia": "Test State",
                "codigo_postal": "12345",
            },
            follow_redirects=True,
        )
        assert enroll_response.status_code == 200

        # Verify enrollment
        with session_full_db_setup.app_context():
            enrollment = (
                database.session.execute(
                    database.select(EstudianteCurso).filter_by(usuario=student_username, curso=course_code)
                )
                .scalars()
                .first()
            )
            assert enrollment is not None

            # Verify payment record for free course
            payment = (
                database.session.execute(database.select(Pago).filter_by(usuario=student_username, curso=course_code))
                .scalars()
                .first()
            )
            assert payment is not None
            assert payment.estado == "completed"

        # Step 9: Student takes the evaluation
        take_eval_response = test_client.post(
            f"/evaluation/{evaluation_id}/take",
            data={
                f"question_{question1_id}": option1_1_id,  # Correct answer: Paris
                f"question_{question2_id}": "true",  # Correct answer: true
            },
            follow_redirects=True,
        )
        assert take_eval_response.status_code == 200  # Success after redirect

        # Step 10: Verify evaluation results
        with session_full_db_setup.app_context():
            attempt = (
                database.session.execute(
                    database.select(EvaluationAttempt).filter_by(evaluation_id=evaluation_id, user_id=student_username)
                )
                .scalars()
                .first()
            )
            assert attempt is not None
            assert attempt.score == 100.0  # Both answers correct
            assert attempt.passed is True  # Passed with 100% score
            assert attempt.submitted_at is not None

        # Step 11: Access evaluation results page
        result_response = test_client.get(f"/evaluation/attempt/{attempt.id}/result")
        assert result_response.status_code == 200
        assert b"Test Evaluation" in result_response.data

        print("✓ Comprehensive evaluation workflow test completed successfully!")

    def test_evaluation_failure_and_retry_session(self, session_full_db_setup, test_client):
        """Test evaluation failure and retry functionality using session fixture."""
        import time

        # Generate unique identifiers to avoid conflicts
        unique_suffix = int(time.time() * 1000) % 1000000
        instructor_username = f"retry_instructor_{unique_suffix}"
        instructor_email = f"retry_instructor_{unique_suffix}@nowlms.com"
        student_username = f"retry_student_{unique_suffix}"
        student_email = f"retry_student_{unique_suffix}@nowlms.com"
        course_code = f"retry_course_{unique_suffix}"

        from now_lms.auth import proteger_passwd
        from now_lms.db import CursoSeccion, Evaluation, EvaluationAttempt, Question, QuestionOption, Usuario

        # Create instructor and course setup (similar to previous test)
        with session_full_db_setup.app_context():
            instructor = Usuario(
                usuario=instructor_username,
                acceso=proteger_passwd("instructor_pass"),
                nombre="Retry",
                apellido="Instructor",
                correo_electronico=instructor_email,
                tipo="instructor",
                activo=True,
                correo_electronico_verificado=True,
            )
            database.session.add(instructor)
            database.session.commit()

        # Login and create course
        test_client.post("/user/login", data={"usuario": instructor_username, "acceso": "instructor_pass"})

        test_client.post(
            "/course/new_curse",
            data={
                "nombre": "Retry Test Course",
                "codigo": course_code,
                "descripcion": "Course for testing retries.",
                "descripcion_corta": "Retry test course.",
                "nivel": 1,
                "duracion": 2,  # Use integer for weeks
                "publico": True,
                "modalidad": "online",
                "foro_habilitado": True,
                "limitado": False,
                "capacidad": 0,
                "fecha_inicio": "2025-08-10",
                "fecha_fin": "2025-09-10",
                "pagado": False,
                "auditable": True,
                "certificado": False,  # Disable certificates to avoid template requirement
                "precio": 0,
            },
        )

        test_client.post(
            f"/course/{course_code}/new_seccion",
            data={
                "nombre": "Retry Section",
                "descripcion": "Section for retry testing.",
            },
        )

        with session_full_db_setup.app_context():
            section = database.session.execute(database.select(CursoSeccion).filter_by(curso=course_code)).scalars().first()
            section_id = section.id

        # Create evaluation with limited attempts
        test_client.post(
            f"/instructor/courses/{course_code}/sections/{section_id}/evaluations/new",
            data={
                "title": "Retry Test Evaluation",
                "description": "Evaluation for testing retry functionality",
                "is_exam": False,
                "passing_score": 80.0,  # Higher passing score
                "max_attempts": 2,  # Limited attempts
            },
        )

        with session_full_db_setup.app_context():
            evaluation = (
                database.session.execute(database.select(Evaluation).filter_by(section_id=section_id)).scalars().first()
            )
            evaluation_id = evaluation.id

            # Add a question
            question = Question(
                evaluation_id=evaluation_id,
                type="multiple",
                text="What is 2 + 2?",
                order=1,
                creado_por=instructor_username,
                modificado_por=instructor_username,
            )
            database.session.add(question)
            database.session.flush()

            # Add options
            correct_option = QuestionOption(
                question_id=question.id,
                text="4",
                is_correct=True,
                creado_por=instructor_username,
                modificado_por=instructor_username,
            )
            wrong_option = QuestionOption(
                question_id=question.id,
                text="5",
                is_correct=False,
                creado_por=instructor_username,
                modificado_por=instructor_username,
            )
            database.session.add_all([correct_option, wrong_option])
            database.session.commit()

            # Store IDs for later use
            question_id = question.id
            correct_option_id = correct_option.id
            wrong_option_id = wrong_option.id

        # Create and enroll student
        with session_full_db_setup.app_context():
            student = Usuario(
                usuario=student_username,
                acceso=proteger_passwd("student_pass"),
                nombre="Retry",
                apellido="Student",
                correo_electronico=student_email,
                tipo="student",
                activo=True,
                correo_electronico_verificado=True,
            )
            database.session.add(student)
            database.session.commit()

        test_client.get("/user/logout")
        test_client.post("/user/login", data={"usuario": student_username, "acceso": "student_pass"})

        test_client.post(
            f"/course/{course_code}/enroll",
            data={
                "nombre": "Retry",
                "apellido": "Student",
                "correo_electronico": student_email,
                "direccion1": "Test Street 123",
                "direccion2": "",
                "pais": "Test Country",
                "provincia": "Test State",
                "codigo_postal": "12345",
            },
        )

        # First attempt - fail with wrong answer
        attempt1_response = test_client.post(
            f"/evaluation/{evaluation_id}/take",
            data={
                f"question_{question_id}": wrong_option_id,
            },
            follow_redirects=True,
        )
        assert attempt1_response.status_code == 200

        # Verify first attempt failed
        with session_full_db_setup.app_context():
            attempt1 = (
                database.session.execute(
                    database.select(EvaluationAttempt).filter_by(evaluation_id=evaluation_id, user_id=student_username)
                )
                .scalars()
                .first()
            )
            assert attempt1.score == 0.0
            assert attempt1.passed is False

        # Second attempt - pass with correct answer
        attempt2_response = test_client.post(
            f"/evaluation/{evaluation_id}/take",
            data={
                f"question_{question_id}": correct_option_id,
            },
            follow_redirects=True,
        )
        assert attempt2_response.status_code == 200

        # Verify second attempt passed
        with session_full_db_setup.app_context():
            attempts = (
                database.session.execute(
                    database.select(EvaluationAttempt).filter_by(evaluation_id=evaluation_id, user_id=student_username)
                )
                .scalars()
                .all()
            )
            assert len(attempts) == 2

            # Find the passing attempt
            passing_attempt = next((a for a in attempts if a.passed), None)
            assert passing_attempt is not None
            assert passing_attempt.score == 100.0

        print("✓ Evaluation failure and retry test completed successfully!")

    def test_evaluation_reopen_request_session(self, session_full_db_setup, test_client):
        """Test evaluation reopen request functionality using session fixture."""
        import time

        # Generate unique identifiers to avoid conflicts
        unique_suffix = int(time.time() * 1000) % 1000000
        instructor_username = f"reopen_instructor_{unique_suffix}"
        instructor_email = f"reopen_instructor_{unique_suffix}@nowlms.com"
        student_username = f"reopen_student_{unique_suffix}"
        student_email = f"reopen_student_{unique_suffix}@nowlms.com"
        course_code = f"reopen_course_{unique_suffix}"

        from now_lms.auth import proteger_passwd
        from now_lms.db import (
            CursoSeccion,
            Evaluation,
            EvaluationAttempt,
            EvaluationReopenRequest,
            Question,
            QuestionOption,
            Usuario,
        )

        # Setup similar to previous tests but with exhausted attempts
        with session_full_db_setup.app_context():
            instructor = Usuario(
                usuario=instructor_username,
                acceso=proteger_passwd("instructor_pass"),
                nombre="Reopen",
                apellido="Instructor",
                correo_electronico=instructor_email,
                tipo="instructor",
                activo=True,
                correo_electronico_verificado=True,
            )
            student = Usuario(
                usuario=student_username,
                acceso=proteger_passwd("student_pass"),
                nombre="Reopen",
                apellido="Student",
                correo_electronico=student_email,
                tipo="student",
                activo=True,
                correo_electronico_verificado=True,
            )
            database.session.add_all([instructor, student])
            database.session.commit()

        # Quick setup for course, section, and evaluation
        test_client.post("/user/login", data={"usuario": instructor_username, "acceso": "instructor_pass"})

        test_client.post(
            "/course/new_curse",
            data={
                "nombre": "Reopen Test Course",
                "codigo": course_code,
                "descripcion": "Course for testing reopen requests.",
                "descripcion_corta": "Reopen test course.",
                "nivel": 1,
                "duracion": 2,  # Use integer for weeks
                "publico": True,
                "modalidad": "online",
                "foro_habilitado": True,
                "limitado": False,
                "capacidad": 0,
                "fecha_inicio": "2025-08-10",
                "fecha_fin": "2025-09-10",
                "pagado": False,
                "auditable": True,
                "certificado": False,  # Disable certificates to avoid template requirement
                "precio": 0,
            },
        )

        test_client.post(
            f"/course/{course_code}/new_seccion",
            data={
                "nombre": "Reopen Section",
                "descripcion": "Section for reopen testing.",
            },
        )

        with session_full_db_setup.app_context():
            section = database.session.execute(database.select(CursoSeccion).filter_by(curso=course_code)).scalars().first()
            section_id = section.id

        test_client.post(
            f"/instructor/courses/{course_code}/sections/{section_id}/evaluations/new",
            data={
                "title": "Reopen Test Evaluation",
                "description": "Evaluation for testing reopen requests",
                "is_exam": False,
                "passing_score": 100.0,  # Impossible to pass with wrong answers
                "max_attempts": 1,  # Only one attempt
            },
        )

        with session_full_db_setup.app_context():
            evaluation = (
                database.session.execute(database.select(Evaluation).filter_by(section_id=section_id)).scalars().first()
            )
            evaluation_id = evaluation.id

            # Add question and options
            question = Question(
                evaluation_id=evaluation_id,
                type="multiple",
                text="What is impossible?",
                order=1,
                creado_por=instructor_username,
                modificado_por=instructor_username,
            )
            database.session.add(question)
            database.session.flush()

            wrong_option = QuestionOption(
                question_id=question.id,
                text="This answer",
                is_correct=False,
                creado_por=instructor_username,
                modificado_por=instructor_username,
            )
            database.session.add(wrong_option)
            database.session.commit()

            # Store IDs for later use
            question_id = question.id
            wrong_option_id = wrong_option.id

        # Enroll student and exhaust attempts
        test_client.get("/user/logout")
        test_client.post("/user/login", data={"usuario": student_username, "acceso": "student_pass"})

        test_client.post(
            f"/course/{course_code}/enroll",
            data={
                "nombre": "Reopen",
                "apellido": "Student",
                "correo_electronico": student_email,
                "direccion1": "Test Street 123",
                "direccion2": "",
                "pais": "Test Country",
                "provincia": "Test State",
                "codigo_postal": "12345",
            },
        )

        # Take evaluation and fail (exhaust attempts)
        test_client.post(
            f"/evaluation/{evaluation_id}/take",
            data={
                f"question_{question_id}": wrong_option_id,
            },
        )

        # Verify attempt was made and failed
        with session_full_db_setup.app_context():
            attempt = (
                database.session.execute(
                    database.select(EvaluationAttempt).filter_by(evaluation_id=evaluation_id, user_id=student_username)
                )
                .scalars()
                .first()
            )
            assert attempt.passed is False

        # Request to reopen evaluation
        reopen_response = test_client.post(
            f"/evaluation/{evaluation_id}/request-reopen",
            data={"justification_text": "I need another chance to demonstrate my knowledge."},
            follow_redirects=True,
        )
        assert reopen_response.status_code == 200

        # Verify reopen request was created
        with session_full_db_setup.app_context():
            reopen_request = (
                database.session.execute(
                    database.select(EvaluationReopenRequest).filter_by(user_id=student_username, evaluation_id=evaluation_id)
                )
                .scalars()
                .first()
            )
            assert reopen_request is not None
            assert reopen_request.status == "pending"
            assert "another chance" in reopen_request.justification_text

        print("✓ Evaluation reopen request test completed successfully!")
