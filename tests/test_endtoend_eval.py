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

from now_lms.db import database

"""
Comprehensive end-to-end tests for evaluation system.
"""


def test_comprehensive_evaluation_workflow(full_db_setup, client):
    """Test complete evaluation workflow from course creation to student completion."""
    app = full_db_setup
    from now_lms.db import (
        Usuario,
        Curso,
        CursoSeccion,
        Evaluation,
        Question,
        QuestionOption,
        EvaluationAttempt,
        EstudianteCurso,
        Pago,
    )
    from now_lms.auth import proteger_passwd

    # Step 1: Create instructor user
    with app.app_context():
        instructor = Usuario(
            usuario="eval_instructor",
            acceso=proteger_passwd("instructor_pass"),
            nombre="Evaluation",
            apellido="Instructor",
            correo_electronico="eval_instructor@nowlms.com",
            tipo="instructor",
            activo=True,
            correo_electronico_verificado=True,
        )
        database.session.add(instructor)
        database.session.commit()

    # Step 2: Login as instructor
    login_response = client.post(
        "/user/login",
        data={"usuario": "eval_instructor", "acceso": "instructor_pass"},
        follow_redirects=True,
    )
    assert login_response.status_code == 200

    # Step 3: Create a free course
    course_response = client.post(
        "/course/new_curse",
        data={
            "nombre": "Evaluation Test Course",
            "codigo": "eval_course",
            "descripcion": "A course for testing evaluations.",
            "descripcion_corta": "Evaluation test course.",
            "nivel": "beginner",
            "duracion": "4 semanas",
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
        follow_redirects=False,
    )
    assert course_response.status_code == 302  # Redirect after creation

    # Verify course was created
    with app.app_context():
        course = database.session.execute(database.select(Curso).filter_by(codigo="eval_course")).scalars().first()
        assert course is not None
        assert course.nombre == "Evaluation Test Course"
        # Course is effectively free if price is 0, regardless of pagado flag
        assert course.precio == 0  # Ensure it's free

    # Step 4: Add a section to the course
    section_response = client.post(
        "/course/eval_course/new_seccion",
        data={
            "nombre": "Evaluation Section",
            "descripcion": "Section for evaluation testing.",
        },
        follow_redirects=False,
    )
    assert section_response.status_code == 302  # Redirect after creation

    # Get the section ID
    with app.app_context():
        section = (
            database.session.execute(database.select(CursoSeccion).filter_by(curso="eval_course", nombre="Evaluation Section"))
            .scalars()
            .first()
        )
        assert section is not None
        section_id = section.id

    # Step 5: Create an evaluation for the section
    evaluation_response = client.post(
        f"/instructor/courses/eval_course/sections/{section_id}/evaluations/new",
        data={
            "title": "Test Evaluation",
            "description": "A comprehensive test evaluation",
            "is_exam": False,
            "passing_score": 70.0,
            "max_attempts": 3,
        },
        follow_redirects=False,
    )
    assert evaluation_response.status_code == 302  # Redirect after creation

    # Get the evaluation ID
    with app.app_context():
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
    with app.app_context():
        # Create a multiple choice question
        question1 = Question(
            evaluation_id=evaluation_id,
            type="multiple",
            text="What is the capital of France?",
            order=1,
            creado_por="eval_instructor",
            modificado_por="eval_instructor",
        )
        database.session.add(question1)
        database.session.flush()

        # Add options for the multiple choice question
        option1_1 = QuestionOption(
            question_id=question1.id,
            text="Paris",
            is_correct=True,
            creado_por="eval_instructor",
            modificado_por="eval_instructor",
        )
        option1_2 = QuestionOption(
            question_id=question1.id,
            text="London",
            is_correct=False,
            creado_por="eval_instructor",
            modificado_por="eval_instructor",
        )
        option1_3 = QuestionOption(
            question_id=question1.id,
            text="Berlin",
            is_correct=False,
            creado_por="eval_instructor",
            modificado_por="eval_instructor",
        )

        # Create a boolean question
        question2 = Question(
            evaluation_id=evaluation_id,
            type="boolean",
            text="The Earth is round.",
            order=2,
            creado_por="eval_instructor",
            modificado_por="eval_instructor",
        )
        database.session.add(question2)
        database.session.flush()

        # Add options for the boolean question
        option2_1 = QuestionOption(
            question_id=question2.id,
            text="true",
            is_correct=True,
            creado_por="eval_instructor",
            modificado_por="eval_instructor",
        )
        option2_2 = QuestionOption(
            question_id=question2.id,
            text="false",
            is_correct=False,
            creado_por="eval_instructor",
            modificado_por="eval_instructor",
        )

        database.session.add_all([option1_1, option1_2, option1_3, option2_1, option2_2])
        database.session.commit()

        # Store IDs for later use outside the session
        question1_id = question1.id
        question2_id = question2.id
        option1_1_id = option1_1.id

    # Step 7: Create a student user
    with app.app_context():
        student = Usuario(
            usuario="eval_student",
            acceso=proteger_passwd("student_pass"),
            nombre="Evaluation",
            apellido="Student",
            correo_electronico="eval_student@nowlms.com",
            tipo="student",
            activo=True,
            correo_electronico_verificado=True,
        )
        database.session.add(student)
        database.session.commit()

    # Logout instructor and login as student
    client.get("/user/logout")
    student_login = client.post(
        "/user/login",
        data={"usuario": "eval_student", "acceso": "student_pass"},
        follow_redirects=True,
    )
    assert student_login.status_code == 200

    # Step 8: Enroll student in the free course
    enroll_response = client.post(
        "/course/eval_course/enroll",
        data={
            "nombre": "Evaluation",
            "apellido": "Student",
            "correo_electronico": "eval_student@nowlms.com",
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
    with app.app_context():
        enrollment = (
            database.session.execute(database.select(EstudianteCurso).filter_by(usuario="eval_student", curso="eval_course"))
            .scalars()
            .first()
        )
        assert enrollment is not None

        # Verify payment record for free course
        payment = (
            database.session.execute(database.select(Pago).filter_by(usuario="eval_student", curso="eval_course"))
            .scalars()
            .first()
        )
        assert payment is not None
        assert payment.estado == "completed"

    # Step 9: Student takes the evaluation
    take_eval_response = client.post(
        f"/evaluation/{evaluation_id}/take",
        data={
            f"question_{question1_id}": option1_1_id,  # Correct answer: Paris
            f"question_{question2_id}": "true",  # Correct answer: true
        },
        follow_redirects=False,
    )
    assert take_eval_response.status_code == 302  # Redirect to results

    # Step 10: Verify evaluation results
    with app.app_context():
        attempt = (
            database.session.execute(
                database.select(EvaluationAttempt).filter_by(evaluation_id=evaluation_id, user_id="eval_student")
            )
            .scalars()
            .first()
        )
        assert attempt is not None
        assert attempt.score == 100.0  # Both answers correct
        assert attempt.passed is True  # Passed with 100% score
        assert attempt.submitted_at is not None

    # Step 11: Access evaluation results page
    result_response = client.get(f"/evaluation/attempt/{attempt.id}/result")
    assert result_response.status_code == 200
    assert b"Test Evaluation" in result_response.data

    print("✓ Comprehensive evaluation workflow test completed successfully!")


def test_evaluation_failure_and_retry(full_db_setup, client):
    """Test evaluation failure and retry functionality."""
    app = full_db_setup
    from now_lms.db import (
        Usuario,
        CursoSeccion,
        Evaluation,
        Question,
        QuestionOption,
        EvaluationAttempt,
    )
    from now_lms.auth import proteger_passwd

    # Create instructor and course setup (similar to previous test)
    with app.app_context():
        instructor = Usuario(
            usuario="retry_instructor",
            acceso=proteger_passwd("instructor_pass"),
            nombre="Retry",
            apellido="Instructor",
            correo_electronico="retry_instructor@nowlms.com",
            tipo="instructor",
            activo=True,
            correo_electronico_verificado=True,
        )
        database.session.add(instructor)
        database.session.commit()

    # Login and create course
    client.post("/user/login", data={"usuario": "retry_instructor", "acceso": "instructor_pass"})

    client.post(
        "/course/new_curse",
        data={
            "nombre": "Retry Test Course",
            "codigo": "retry_course",
            "descripcion": "Course for testing retries.",
            "descripcion_corta": "Retry test course.",
            "nivel": "beginner",
            "duracion": "2 semanas",
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

    client.post(
        "/course/retry_course/new_seccion",
        data={
            "nombre": "Retry Section",
            "descripcion": "Section for retry testing.",
        },
    )

    with app.app_context():
        section = database.session.execute(database.select(CursoSeccion).filter_by(curso="retry_course")).scalars().first()
        section_id = section.id

    # Create evaluation with limited attempts
    client.post(
        f"/instructor/courses/retry_course/sections/{section_id}/evaluations/new",
        data={
            "title": "Retry Test Evaluation",
            "description": "Evaluation for testing retry functionality",
            "is_exam": False,
            "passing_score": 80.0,  # Higher passing score
            "max_attempts": 2,  # Limited attempts
        },
    )

    with app.app_context():
        evaluation = database.session.execute(database.select(Evaluation).filter_by(section_id=section_id)).scalars().first()
        evaluation_id = evaluation.id

        # Add a question
        question = Question(
            evaluation_id=evaluation_id,
            type="multiple",
            text="What is 2 + 2?",
            order=1,
            creado_por="retry_instructor",
            modificado_por="retry_instructor",
        )
        database.session.add(question)
        database.session.flush()

        # Add options
        correct_option = QuestionOption(
            question_id=question.id,
            text="4",
            is_correct=True,
            creado_por="retry_instructor",
            modificado_por="retry_instructor",
        )
        wrong_option = QuestionOption(
            question_id=question.id,
            text="5",
            is_correct=False,
            creado_por="retry_instructor",
            modificado_por="retry_instructor",
        )
        database.session.add_all([correct_option, wrong_option])
        database.session.commit()

        # Store IDs for later use
        question_id = question.id
        correct_option_id = correct_option.id
        wrong_option_id = wrong_option.id

    # Create and enroll student
    with app.app_context():
        student = Usuario(
            usuario="retry_student",
            acceso=proteger_passwd("student_pass"),
            nombre="Retry",
            apellido="Student",
            correo_electronico="retry_student@nowlms.com",
            tipo="student",
            activo=True,
            correo_electronico_verificado=True,
        )
        database.session.add(student)
        database.session.commit()

    client.get("/user/logout")
    client.post("/user/login", data={"usuario": "retry_student", "acceso": "student_pass"})

    client.post(
        "/course/retry_course/enroll",
        data={
            "nombre": "Retry",
            "apellido": "Student",
            "correo_electronico": "retry_student@nowlms.com",
            "direccion1": "Test Street 123",
            "direccion2": "",
            "pais": "Test Country",
            "provincia": "Test State",
            "codigo_postal": "12345",
        },
    )

    # First attempt - fail with wrong answer
    attempt1_response = client.post(
        f"/evaluation/{evaluation_id}/take",
        data={
            f"question_{question_id}": wrong_option_id,
        },
    )
    assert attempt1_response.status_code == 302

    # Verify first attempt failed
    with app.app_context():
        attempt1 = (
            database.session.execute(
                database.select(EvaluationAttempt).filter_by(evaluation_id=evaluation_id, user_id="retry_student")
            )
            .scalars()
            .first()
        )
        assert attempt1.score == 0.0
        assert attempt1.passed is False

    # Second attempt - pass with correct answer
    attempt2_response = client.post(
        f"/evaluation/{evaluation_id}/take",
        data={
            f"question_{question_id}": correct_option_id,
        },
    )
    assert attempt2_response.status_code == 302

    # Verify second attempt passed
    with app.app_context():
        attempts = (
            database.session.execute(
                database.select(EvaluationAttempt).filter_by(evaluation_id=evaluation_id, user_id="retry_student")
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


def test_evaluation_reopen_request(full_db_setup, client):
    """Test evaluation reopen request functionality."""
    app = full_db_setup
    from now_lms.db import (
        Usuario,
        CursoSeccion,
        Evaluation,
        Question,
        QuestionOption,
        EvaluationAttempt,
        EvaluationReopenRequest,
    )
    from now_lms.auth import proteger_passwd

    # Setup similar to previous tests but with exhausted attempts
    with app.app_context():
        instructor = Usuario(
            usuario="reopen_instructor",
            acceso=proteger_passwd("instructor_pass"),
            nombre="Reopen",
            apellido="Instructor",
            correo_electronico="reopen_instructor@nowlms.com",
            tipo="instructor",
            activo=True,
            correo_electronico_verificado=True,
        )
        student = Usuario(
            usuario="reopen_student",
            acceso=proteger_passwd("student_pass"),
            nombre="Reopen",
            apellido="Student",
            correo_electronico="reopen_student@nowlms.com",
            tipo="student",
            activo=True,
            correo_electronico_verificado=True,
        )
        database.session.add_all([instructor, student])
        database.session.commit()

    # Quick setup for course, section, and evaluation
    client.post("/user/login", data={"usuario": "reopen_instructor", "acceso": "instructor_pass"})

    client.post(
        "/course/new_curse",
        data={
            "nombre": "Reopen Test Course",
            "codigo": "reopen_course",
            "descripcion": "Course for testing reopen requests.",
            "descripcion_corta": "Reopen test course.",
            "nivel": "beginner",
            "duracion": "2 semanas",
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

    client.post(
        "/course/reopen_course/new_seccion",
        data={
            "nombre": "Reopen Section",
            "descripcion": "Section for reopen testing.",
        },
    )

    with app.app_context():
        section = database.session.execute(database.select(CursoSeccion).filter_by(curso="reopen_course")).scalars().first()
        section_id = section.id

    client.post(
        f"/instructor/courses/reopen_course/sections/{section_id}/evaluations/new",
        data={
            "title": "Reopen Test Evaluation",
            "description": "Evaluation for testing reopen requests",
            "is_exam": False,
            "passing_score": 100.0,  # Impossible to pass with wrong answers
            "max_attempts": 1,  # Only one attempt
        },
    )

    with app.app_context():
        evaluation = database.session.execute(database.select(Evaluation).filter_by(section_id=section_id)).scalars().first()
        evaluation_id = evaluation.id

        # Add question and options
        question = Question(
            evaluation_id=evaluation_id,
            type="multiple",
            text="What is impossible?",
            order=1,
            creado_por="reopen_instructor",
            modificado_por="reopen_instructor",
        )
        database.session.add(question)
        database.session.flush()

        wrong_option = QuestionOption(
            question_id=question.id,
            text="This answer",
            is_correct=False,
            creado_por="reopen_instructor",
            modificado_por="reopen_instructor",
        )
        database.session.add(wrong_option)
        database.session.commit()

        # Store IDs for later use
        question_id = question.id
        wrong_option_id = wrong_option.id

    # Enroll student and exhaust attempts
    client.get("/user/logout")
    client.post("/user/login", data={"usuario": "reopen_student", "acceso": "student_pass"})

    client.post(
        "/course/reopen_course/enroll",
        data={
            "nombre": "Reopen",
            "apellido": "Student",
            "correo_electronico": "reopen_student@nowlms.com",
            "direccion1": "Test Street 123",
            "direccion2": "",
            "pais": "Test Country",
            "provincia": "Test State",
            "codigo_postal": "12345",
        },
    )

    # Take evaluation and fail (exhaust attempts)
    client.post(
        f"/evaluation/{evaluation_id}/take",
        data={
            f"question_{question_id}": wrong_option_id,
        },
    )

    # Verify attempt was made and failed
    with app.app_context():
        attempt = (
            database.session.execute(
                database.select(EvaluationAttempt).filter_by(evaluation_id=evaluation_id, user_id="reopen_student")
            )
            .scalars()
            .first()
        )
        assert attempt.passed is False

    # Request to reopen evaluation
    reopen_response = client.post(
        f"/evaluation/{evaluation_id}/request-reopen",
        data={"justification_text": "I need another chance to demonstrate my knowledge."},
    )
    assert reopen_response.status_code == 302

    # Verify reopen request was created
    with app.app_context():
        reopen_request = (
            database.session.execute(
                database.select(EvaluationReopenRequest).filter_by(user_id="reopen_student", evaluation_id=evaluation_id)
            )
            .scalars()
            .first()
        )
        assert reopen_request is not None
        assert reopen_request.status == "pending"
        assert "another chance" in reopen_request.justification_text

    print("✓ Evaluation reopen request test completed successfully!")
