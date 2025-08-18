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

"""
Comprehensive evaluation workflow tests covering instructor and student flows.
"""

from now_lms.db import database


def test_instructor_complete_evaluation_workflow(full_db_setup, client):
    """Test complete instructor evaluation workflow: create evaluation, add questions, add options, edit everything."""
    app = full_db_setup
    from now_lms.db import (
        Usuario,
        Curso,
        CursoSeccion,
        Evaluation,
        Question,
        QuestionOption,
        DocenteCurso,
    )
    from now_lms.auth import proteger_passwd

    # Step 1: Create instructor user
    with app.app_context():
        instructor = Usuario(
            usuario="workflow_instructor",
            acceso=proteger_passwd("instructor_pass"),
            nombre="Workflow",
            apellido="Instructor",
            correo_electronico="workflow_instructor@nowlms.com",
            tipo="instructor",
            activo=True,
            correo_electronico_verificado=True,
        )
        database.session.add(instructor)
        database.session.commit()

    # Step 2: Login as instructor
    login_response = client.post(
        "/user/login",
        data={"usuario": "workflow_instructor", "acceso": "instructor_pass"},
        follow_redirects=True,
    )
    assert login_response.status_code == 200

    # Step 3: Create a course
    course_response = client.post(
        "/course/new_curse",
        data={
            "nombre": "Complete Workflow Test Course",
            "codigo": "workflow_course",
            "descripcion": "A course for testing complete workflow.",
            "descripcion_corta": "Complete workflow test course.",
            "nivel": "beginner",
            "duracion": "4 semanas",
            "publico": True,
            "modalidad": "online",
            "foro_habilitado": True,
            "limitado": False,
            "capacidad": 0,
            "fecha_inicio": "2025-08-10",
            "fecha_fin": "2025-09-10",
            "pagado": False,
            "auditable": True,
            "certificado": False,
            "precio": 0,
        },
        follow_redirects=False,
    )
    assert course_response.status_code == 302

    # Step 4: Add instructor to course
    with app.app_context():
        course = database.session.execute(database.select(Curso).filter_by(codigo="workflow_course")).scalars().first()
        assert course is not None

        # Add instructor assignment
        instructor_assignment = DocenteCurso(
            curso="workflow_course",
            usuario="workflow_instructor",
            vigente=True,
        )
        database.session.add(instructor_assignment)
        database.session.commit()

    # Step 5: Add a section to the course
    section_response = client.post(
        "/course/workflow_course/new_seccion",
        data={
            "nombre": "Workflow Section",
            "descripcion": "Section for workflow testing.",
        },
        follow_redirects=False,
    )
    assert section_response.status_code == 302

    # Get the section ID
    with app.app_context():
        section = (
            database.session.execute(
                database.select(CursoSeccion).filter_by(curso="workflow_course", nombre="Workflow Section")
            )
            .scalars()
            .first()
        )
        assert section is not None
        section_id = section.id

    # Step 6: Create an evaluation for the section
    evaluation_response = client.post(
        f"/instructor/courses/workflow_course/sections/{section_id}/evaluations/new",
        data={
            "title": "Complete Workflow Evaluation",
            "description": "A comprehensive test evaluation for the complete workflow",
            "is_exam": False,
            "passing_score": 75.0,
            "max_attempts": 2,
        },
        follow_redirects=False,
    )
    assert evaluation_response.status_code == 302

    # Get the evaluation ID
    with app.app_context():
        evaluation = (
            database.session.execute(
                database.select(Evaluation).filter_by(section_id=section_id, title="Complete Workflow Evaluation")
            )
            .scalars()
            .first()
        )
        assert evaluation is not None
        evaluation_id = evaluation.id

    # Step 7: Test accessing evaluation edit page
    edit_eval_response = client.get(f"/instructor/evaluations/{evaluation_id}/edit")
    assert edit_eval_response.status_code == 200
    assert b"Complete Workflow Evaluation" in edit_eval_response.data

    # Step 8: Add a multiple choice question
    question_response = client.post(
        f"/instructor/evaluations/{evaluation_id}/questions/new",
        data={
            "text": "What is the capital of Spain?",
            "type": "multiple",
            "explanation": "Madrid is the capital and largest city of Spain.",
        },
        follow_redirects=False,
    )
    assert question_response.status_code == 302

    # Get the question ID
    with app.app_context():
        question = (
            database.session.execute(
                database.select(Question).filter_by(evaluation_id=evaluation_id, text="What is the capital of Spain?")
            )
            .scalars()
            .first()
        )
        assert question is not None
        question_id = question.id

        # Verify default options were created
        options = database.session.execute(database.select(QuestionOption).filter_by(question_id=question_id)).scalars().all()
        assert len(options) == 4  # Default 4 options for multiple choice
        default_option_id = options[0].id

    # Step 9: Edit the first option to be "Madrid" (correct)
    edit_option_response = client.post(
        f"/instructor/options/{default_option_id}/edit",
        data={
            "text": "Madrid",
            "is_correct": True,
        },
        follow_redirects=False,
    )
    assert edit_option_response.status_code == 302

    # Step 10: Add a new option to the question
    add_option_response = client.post(
        f"/instructor/questions/{question_id}/options/new",
        data={
            "text": "Barcelona",
            "is_correct": False,
        },
        follow_redirects=False,
    )
    assert add_option_response.status_code == 302

    # Step 11: Add a boolean question
    bool_question_response = client.post(
        f"/instructor/evaluations/{evaluation_id}/questions/new",
        data={
            "text": "Spain is in Europe.",
            "type": "boolean",
            "explanation": "Spain is indeed located in southwestern Europe.",
        },
        follow_redirects=False,
    )
    assert bool_question_response.status_code == 302

    # Get the boolean question ID
    with app.app_context():
        bool_question = (
            database.session.execute(
                database.select(Question).filter_by(evaluation_id=evaluation_id, text="Spain is in Europe.")
            )
            .scalars()
            .first()
        )
        assert bool_question is not None
        bool_question_id = bool_question.id

        # Get the "Verdadero" option and edit it to be correct
        verdadero_option = (
            database.session.execute(database.select(QuestionOption).filter_by(question_id=bool_question_id, text="Verdadero"))
            .scalars()
            .first()
        )
        assert verdadero_option is not None
        verdadero_option_id = verdadero_option.id

    # Step 12: Edit the "Verdadero" option to be correct
    edit_bool_option_response = client.post(
        f"/instructor/options/{verdadero_option_id}/edit",
        data={
            "text": "Verdadero",
            "is_correct": True,
        },
        follow_redirects=False,
    )
    assert edit_bool_option_response.status_code == 302

    # Step 13: Edit the evaluation itself
    edit_evaluation_response = client.post(
        f"/instructor/evaluations/{evaluation_id}/edit",
        data={
            "title": "Updated Complete Workflow Evaluation",
            "description": "Updated description for the comprehensive test evaluation",
            "is_exam": True,  # Change to exam
            "passing_score": 80.0,  # Increase passing score
            "max_attempts": 3,  # Allow more attempts
        },
        follow_redirects=False,
    )
    assert edit_evaluation_response.status_code == 302

    # Step 14: Edit a question
    edit_question_response = client.post(
        f"/instructor/questions/{question_id}/edit",
        data={
            "text": "What is the capital and largest city of Spain?",  # Updated text
            "type": "multiple",
            "explanation": "Madrid is both the capital and the largest city of Spain by population.",
        },
        follow_redirects=False,
    )
    assert edit_question_response.status_code == 302

    # Step 15: Verify all changes were saved correctly
    with app.app_context():
        # Check updated evaluation
        updated_evaluation = database.session.get(Evaluation, evaluation_id)
        assert updated_evaluation.title == "Updated Complete Workflow Evaluation"
        assert updated_evaluation.is_exam is True
        assert updated_evaluation.passing_score == 80.0
        assert updated_evaluation.max_attempts == 3

        # Check updated question
        updated_question = database.session.get(Question, question_id)
        assert updated_question.text == "What is the capital and largest city of Spain?"

        # Check updated option
        updated_option = database.session.get(QuestionOption, default_option_id)
        assert updated_option.text == "Madrid"
        assert updated_option.is_correct is True

        # Check all options for the multiple choice question
        all_options = (
            database.session.execute(database.select(QuestionOption).filter_by(question_id=question_id)).scalars().all()
        )
        assert len(all_options) == 5  # 4 default + 1 added

        # Check boolean question has correct answer set
        bool_options = (
            database.session.execute(database.select(QuestionOption).filter_by(question_id=bool_question_id)).scalars().all()
        )
        correct_options = [opt for opt in bool_options if opt.is_correct]
        assert len(correct_options) == 1
        assert correct_options[0].text == "Verdadero"

    # Step 16: Test evaluation toggle (publish/unpublish)
    toggle_response = client.post(f"/instructor/evaluations/{evaluation_id}/toggle")
    assert toggle_response.status_code == 302

    # Step 17: Test evaluation results page (should be empty but accessible)
    results_response = client.get(f"/instructor/evaluations/{evaluation_id}/results")
    assert results_response.status_code == 200

    print("✓ Complete instructor evaluation workflow test completed successfully!")


def test_student_complete_evaluation_workflow(full_db_setup, client):
    """Test complete student evaluation workflow: enroll, take evaluation, get certificate."""
    app = full_db_setup
    from now_lms.db import (
        Usuario,
        CursoSeccion,
        Evaluation,
        Question,
        QuestionOption,
        EvaluationAttempt,
        EstudianteCurso,
        Pago,
        DocenteCurso,
    )
    from now_lms.auth import proteger_passwd

    # Setup: Create instructor and course with evaluation
    with app.app_context():
        instructor = Usuario(
            usuario="student_test_instructor",
            acceso=proteger_passwd("instructor_pass"),
            nombre="Student Test",
            apellido="Instructor",
            correo_electronico="student_test_instructor@nowlms.com",
            tipo="instructor",
            activo=True,
            correo_electronico_verificado=True,
        )
        database.session.add(instructor)
        database.session.commit()

    # Login as instructor and create course
    client.post("/user/login", data={"usuario": "student_test_instructor", "acceso": "instructor_pass"})

    client.post(
        "/course/new_curse",
        data={
            "nombre": "Student Workflow Test Course",
            "codigo": "student_course",
            "descripcion": "A course for testing student workflow.",
            "descripcion_corta": "Student workflow test course.",
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
            "certificado": True,  # Enable certificates
            "precio": 0,
        },
    )

    # Add instructor to course and create section
    with app.app_context():
        instructor_assignment = DocenteCurso(
            curso="student_course",
            usuario="student_test_instructor",
            vigente=True,
        )
        database.session.add(instructor_assignment)
        database.session.commit()

    client.post(
        "/course/student_course/new_seccion",
        data={
            "nombre": "Student Section",
            "descripcion": "Section for student testing.",
        },
    )

    with app.app_context():
        section = database.session.execute(database.select(CursoSeccion).filter_by(curso="student_course")).scalars().first()
        section_id = section.id

    # Create evaluation
    client.post(
        f"/instructor/courses/student_course/sections/{section_id}/evaluations/new",
        data={
            "title": "Student Test Evaluation",
            "description": "Evaluation for testing student workflow",
            "is_exam": False,
            "passing_score": 70.0,
            "max_attempts": 2,
        },
    )

    with app.app_context():
        evaluation = database.session.execute(database.select(Evaluation).filter_by(section_id=section_id)).scalars().first()
        evaluation_id = evaluation.id

        # Create a question with options
        question = Question(
            evaluation_id=evaluation_id,
            type="multiple",
            text="What is 5 + 3?",
            order=1,
            creado_por="student_test_instructor",
        )
        database.session.add(question)
        database.session.flush()

        correct_option = QuestionOption(
            question_id=question.id,
            text="8",
            is_correct=True,
            creado_por="student_test_instructor",
        )
        wrong_option = QuestionOption(
            question_id=question.id,
            text="7",
            is_correct=False,
            creado_por="student_test_instructor",
        )
        database.session.add_all([correct_option, wrong_option])
        database.session.commit()

        # Store IDs for later use
        question_id = question.id
        correct_option_id = correct_option.id

    # Step 1: Create student user
    with app.app_context():
        student = Usuario(
            usuario="workflow_student",
            acceso=proteger_passwd("student_pass"),
            nombre="Workflow",
            apellido="Student",
            correo_electronico="workflow_student@nowlms.com",
            tipo="student",
            activo=True,
            correo_electronico_verificado=True,
        )
        database.session.add(student)
        database.session.commit()

    # Step 2: Logout instructor and login as student
    client.get("/user/logout")
    student_login = client.post(
        "/user/login",
        data={"usuario": "workflow_student", "acceso": "student_pass"},
        follow_redirects=True,
    )
    assert student_login.status_code == 200

    # Step 3: Enroll in the course
    enroll_response = client.post(
        "/course/student_course/enroll",
        data={
            "nombre": "Workflow",
            "apellido": "Student",
            "correo_electronico": "workflow_student@nowlms.com",
            "direccion1": "Test Street 123",
            "direccion2": "",
            "pais": "Test Country",
            "provincia": "Test State",
            "codigo_postal": "12345",
        },
        follow_redirects=True,
    )
    assert enroll_response.status_code == 200

    # Step 4: Verify enrollment
    with app.app_context():
        enrollment = (
            database.session.execute(
                database.select(EstudianteCurso).filter_by(usuario="workflow_student", curso="student_course")
            )
            .scalars()
            .first()
        )
        assert enrollment is not None

        payment = (
            database.session.execute(database.select(Pago).filter_by(usuario="workflow_student", curso="student_course"))
            .scalars()
            .first()
        )
        assert payment is not None
        assert payment.estado == "completed"

    # Step 5: Access course page and see available evaluations
    course_page_response = client.get("/course/student_course/take")
    assert course_page_response.status_code == 200
    assert b"Student Test Evaluation" in course_page_response.data

    # Step 6: Take the evaluation
    take_eval_response = client.post(
        f"/evaluation/{evaluation_id}/take",
        data={
            f"question_{question_id}": correct_option_id,
        },
        follow_redirects=False,
    )
    assert take_eval_response.status_code == 302

    # Step 7: Verify evaluation results
    with app.app_context():
        attempt = (
            database.session.execute(
                database.select(EvaluationAttempt).filter_by(evaluation_id=evaluation_id, user_id="workflow_student")
            )
            .scalars()
            .first()
        )
        assert attempt is not None
        assert attempt.score == 100.0
        assert attempt.passed is True

    # Step 8: Access evaluation results page
    result_response = client.get(f"/evaluation/attempt/{attempt.id}/result")
    assert result_response.status_code == 200
    assert b"Student Test Evaluation" in result_response.data

    print("✓ Complete student evaluation workflow test completed successfully!")


def test_instructor_question_option_management(full_db_setup, client):
    """Test detailed question and option management functionality."""
    app = full_db_setup
    from now_lms.db import (
        Usuario,
        CursoSeccion,
        Evaluation,
        Question,
        QuestionOption,
        DocenteCurso,
    )
    from now_lms.auth import proteger_passwd

    # Setup instructor and course
    with app.app_context():
        instructor = Usuario(
            usuario="option_instructor",
            acceso=proteger_passwd("instructor_pass"),
            nombre="Option",
            apellido="Instructor",
            correo_electronico="option_instructor@nowlms.com",
            tipo="instructor",
            activo=True,
            correo_electronico_verificado=True,
        )
        database.session.add(instructor)
        database.session.commit()

    client.post("/user/login", data={"usuario": "option_instructor", "acceso": "instructor_pass"})

    client.post(
        "/course/new_curse",
        data={
            "nombre": "Option Management Course",
            "codigo": "option_course",
            "descripcion": "Course for testing option management.",
            "descripcion_corta": "Option management course.",
            "nivel": "beginner",
            "duracion": "1 semana",
            "publico": True,
            "modalidad": "online",
            "foro_habilitado": True,
            "limitado": False,
            "capacidad": 0,
            "fecha_inicio": "2025-08-10",
            "fecha_fin": "2025-09-10",
            "pagado": False,
            "auditable": True,
            "certificado": False,
            "precio": 0,
        },
    )

    with app.app_context():
        instructor_assignment = DocenteCurso(
            curso="option_course",
            usuario="option_instructor",
            vigente=True,
        )
        database.session.add(instructor_assignment)
        database.session.commit()

    client.post(
        "/course/option_course/new_seccion",
        data={
            "nombre": "Option Section",
            "descripcion": "Section for option testing.",
        },
    )

    with app.app_context():
        section = database.session.execute(database.select(CursoSeccion).filter_by(curso="option_course")).scalars().first()
        section_id = section.id

    client.post(
        f"/instructor/courses/option_course/sections/{section_id}/evaluations/new",
        data={
            "title": "Option Management Evaluation",
            "description": "Evaluation for testing option management",
            "is_exam": False,
            "passing_score": 60.0,
            "max_attempts": 1,
        },
    )

    with app.app_context():
        evaluation = database.session.execute(database.select(Evaluation).filter_by(section_id=section_id)).scalars().first()
        evaluation_id = evaluation.id

    # Test 1: Create multiple choice question with default options
    client.post(
        f"/instructor/evaluations/{evaluation_id}/questions/new",
        data={
            "text": "Which programming languages are object-oriented?",
            "type": "multiple",
            "explanation": "Multiple languages support object-oriented programming.",
        },
    )

    with app.app_context():
        question = database.session.execute(database.select(Question).filter_by(evaluation_id=evaluation_id)).scalars().first()
        question_id = question.id

        # Verify 4 default options were created
        options = database.session.execute(database.select(QuestionOption).filter_by(question_id=question_id)).scalars().all()
        assert len(options) == 4
        option_ids = [opt.id for opt in options]

    # Test 2: Edit default options to real values
    client.post(
        f"/instructor/options/{option_ids[0]}/edit",
        data={"text": "Python", "is_correct": "y"},  # Send 'y' for checked
    )
    client.post(
        f"/instructor/options/{option_ids[1]}/edit",
        data={"text": "Java", "is_correct": "y"},  # Send 'y' for checked
    )
    client.post(
        f"/instructor/options/{option_ids[2]}/edit",
        data={"text": "C"},  # Don't send is_correct for unchecked
    )
    client.post(
        f"/instructor/options/{option_ids[3]}/edit",
        data={"text": "Assembly"},  # Don't send is_correct for unchecked
    )

    # Test 3: Add a new option
    client.post(
        f"/instructor/questions/{question_id}/options/new",
        data={"text": "C++", "is_correct": "y"},  # Send 'y' for checked
    )

    # Test 4: Verify all options are correct
    with app.app_context():
        all_options = (
            database.session.execute(database.select(QuestionOption).filter_by(question_id=question_id)).scalars().all()
        )
        assert len(all_options) == 5

        option_texts = [opt.text for opt in all_options]
        assert "Python" in option_texts
        assert "Java" in option_texts
        assert "C++" in option_texts

        # Debug: Print all options and their correct status
        print(f"Debug: All options for question {question_id}:")
        for opt in all_options:
            print(f"  {opt.text}: is_correct={opt.is_correct}")

        correct_options = [opt for opt in all_options if opt.is_correct]
        print(f"Debug: Found {len(correct_options)} correct options")
        expected_correct = ["Python", "Java", "C++"]
        actual_correct = [opt.text for opt in correct_options]
        print(f"Debug: Expected correct: {expected_correct}, Actual correct: {actual_correct}")

        assert len(correct_options) == 3  # Python, Java, C++

    # Test 5: Try to delete an option (should work)
    delete_response = client.post(f"/instructor/options/{option_ids[3]}/delete")
    assert delete_response.status_code == 302

    with app.app_context():
        remaining_options = (
            database.session.execute(database.select(QuestionOption).filter_by(question_id=question_id)).scalars().all()
        )
        assert len(remaining_options) == 4  # One deleted

    # Test 6: Test boolean question option limits
    client.post(
        f"/instructor/evaluations/{evaluation_id}/questions/new",
        data={
            "text": "Is Python a programming language?",
            "type": "boolean",
            "explanation": "Python is indeed a programming language.",
        },
    )

    with app.app_context():
        bool_question = (
            database.session.execute(database.select(Question).filter_by(evaluation_id=evaluation_id, type="boolean"))
            .scalars()
            .first()
        )
        bool_question_id = bool_question.id

        # Should have exactly 2 options for boolean
        bool_options = (
            database.session.execute(database.select(QuestionOption).filter_by(question_id=bool_question_id)).scalars().all()
        )
        assert len(bool_options) == 2

    # Test 7: Try to add third option to boolean question (should be rejected)
    reject_response = client.post(
        f"/instructor/questions/{bool_question_id}/options/new",
        data={"text": "Maybe", "is_correct": False},
    )
    assert reject_response.status_code == 302  # Redirects with warning

    with app.app_context():
        bool_options_after = (
            database.session.execute(database.select(QuestionOption).filter_by(question_id=bool_question_id)).scalars().all()
        )
        assert len(bool_options_after) == 2  # Still only 2 options

    # Test 8: Delete question (should delete all options)
    delete_question_response = client.post(f"/instructor/questions/{question_id}/delete")
    assert delete_question_response.status_code == 302

    with app.app_context():
        deleted_question = database.session.get(Question, question_id)
        assert deleted_question is None

        # All options should be deleted too
        orphaned_options = (
            database.session.execute(database.select(QuestionOption).filter_by(question_id=question_id)).scalars().all()
        )
        assert len(orphaned_options) == 0

    print("✓ Question and option management test completed successfully!")
