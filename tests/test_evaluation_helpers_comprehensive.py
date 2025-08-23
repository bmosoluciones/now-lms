"""Comprehensive tests for now_lms.vistas.evaluation_helpers module to improve coverage."""

from datetime import datetime


class TestEvaluationHelpers:
    """Test evaluation helper functions."""

    def test_check_user_evaluations_completed(self, minimal_db_setup):
        """Test check_user_evaluations_completed function."""
        from now_lms.vistas.evaluation_helpers import check_user_evaluations_completed
        from now_lms.db import Curso, CursoSeccion, Evaluation, Usuario, EvaluationAttempt, database

        with minimal_db_setup.app_context():
            # Create test user
            user = Usuario(
                usuario="test_eval_user",
                acceso=b"password123",
                nombre="Test",
                apellido="User",
                correo_electronico="test@eval.com",
                tipo="student",
            )
            database.session.add(user)

            # Create test course and section
            course = Curso(
                codigo="EVAL_TEST",
                nombre="Evaluation Test Course",
                descripcion_corta="Testing evaluations",
                descripcion="Course for testing evaluation functionality",
                estado="open",
                plantilla_certificado=None,
            )
            database.session.add(course)

            section = CursoSeccion(
                curso="EVAL_TEST",
                nombre="Test Section",
                descripcion="Section for evaluation testing",
                indice=1,
                estado=True,
            )
            database.session.add(section)
            database.session.flush()

            # Test with no evaluations
            all_passed, failed_count, total_count = check_user_evaluations_completed("EVAL_TEST", user.usuario)
            assert all_passed is True
            assert failed_count == 0
            assert total_count == 0

            # Create evaluations
            evaluation1 = Evaluation(
                section_id=section.id,
                title="Test Evaluation 1",
                description="First test evaluation",
                is_exam=False,
                passing_score=70.0,
                max_attempts=3,
                available_until=datetime(2025, 12, 31, 23, 59, 59),
            )
            evaluation2 = Evaluation(
                section_id=section.id,
                title="Test Evaluation 2",
                description="Second test evaluation",
                is_exam=True,
                passing_score=75.0,
                max_attempts=2,
                available_until=datetime(2025, 12, 31, 23, 59, 59),
            )
            database.session.add_all([evaluation1, evaluation2])
            database.session.flush()

            # Test with evaluations but no attempts
            all_passed, failed_count, total_count = check_user_evaluations_completed("EVAL_TEST", user.usuario)
            assert all_passed is False
            assert failed_count == 2
            assert total_count == 2

            # Create a passing attempt for evaluation1
            attempt1 = EvaluationAttempt(
                evaluation_id=evaluation1.id,
                user_id=user.usuario,
                score=85.0,
                passed=True,
                submitted_at=datetime(2025, 1, 1, 10, 0, 0),
            )
            database.session.add(attempt1)
            database.session.commit()

            # Test with one passing evaluation
            all_passed, failed_count, total_count = check_user_evaluations_completed("EVAL_TEST", user.usuario)
            assert all_passed is False
            assert total_count == 2

            # Create a passing attempt for evaluation2
            attempt2 = EvaluationAttempt(
                evaluation_id=evaluation2.id,
                user_id=user.usuario,
                score=80.0,
                passed=True,
                submitted_at=datetime(2025, 1, 2, 10, 0, 0),
            )
            database.session.add(attempt2)
            database.session.commit()

            # Test with all evaluations passed
            all_passed, failed_count, total_count = check_user_evaluations_completed("EVAL_TEST", user.usuario)
            assert all_passed is True
            assert failed_count == 0
            assert total_count == 2

    def test_get_user_evaluation_status(self, minimal_db_setup):
        """Test get_user_evaluation_status function."""
        from now_lms.vistas.evaluation_helpers import get_user_evaluation_status
        from now_lms.db import Curso, CursoSeccion, Evaluation, Usuario, EvaluationAttempt, database

        with minimal_db_setup.app_context():
            # Create test user
            user = Usuario(
                usuario="status_user",
                acceso=b"password123",
                nombre="Status",
                apellido="User",
                correo_electronico="status@test.com",
                tipo="student",
            )
            database.session.add(user)

            # Create test course and section
            course = Curso(
                codigo="STATUS_TEST",
                nombre="Status Test Course",
                descripcion_corta="Testing status",
                descripcion="Course for testing status functionality",
                estado="open",
                plantilla_certificado=None,
            )
            database.session.add(course)

            section = CursoSeccion(
                curso="STATUS_TEST",
                nombre="Status Section",
                descripcion="Section for status testing",
                indice=1,
                estado=True,
            )
            database.session.add(section)
            database.session.flush()

            # Test with no evaluations
            status = get_user_evaluation_status("STATUS_TEST", user.usuario)
            assert status["total_evaluations"] == 0
            assert status["passed_evaluations"] == 0
            assert status["failed_evaluations"] == 0
            assert status["pending_evaluations"] == 0
            assert status["evaluation_details"] == []

            # Create evaluations
            evaluation1 = Evaluation(
                section_id=section.id,
                title="Status Evaluation 1",
                description="First status evaluation",
                is_exam=False,
                passing_score=70.0,
                max_attempts=3,
                available_until=datetime(2025, 12, 31, 23, 59, 59),
            )
            evaluation2 = Evaluation(
                section_id=section.id,
                title="Status Evaluation 2",
                description="Second status evaluation",
                is_exam=True,
                passing_score=75.0,
                max_attempts=2,
                available_until=datetime(2025, 12, 31, 23, 59, 59),
            )
            evaluation3 = Evaluation(
                section_id=section.id,
                title="Status Evaluation 3",
                description="Third status evaluation",
                is_exam=False,
                passing_score=70.0,
                max_attempts=3,
                available_until=datetime(2025, 12, 31, 23, 59, 59),
            )
            database.session.add_all([evaluation1, evaluation2, evaluation3])
            database.session.flush()

            # Create attempts with different outcomes
            # Passing attempt for evaluation1
            attempt1_pass = EvaluationAttempt(
                evaluation_id=evaluation1.id,
                user_id=user.usuario,
                score=85.0,
                passed=True,
                submitted_at=datetime(2025, 1, 1, 10, 0, 0),
            )
            database.session.add(attempt1_pass)

            # Failing attempt for evaluation2
            attempt2_fail = EvaluationAttempt(
                evaluation_id=evaluation2.id,
                user_id=user.usuario,
                score=60.0,
                passed=False,
                submitted_at=datetime(2025, 1, 2, 10, 0, 0),
            )
            database.session.add(attempt2_fail)

            # No attempt for evaluation3 (pending)
            database.session.commit()

            # Test status with mixed results
            status = get_user_evaluation_status("STATUS_TEST", user.usuario)
            assert status["total_evaluations"] == 3
            assert status["passed_evaluations"] == 1
            assert status["failed_evaluations"] == 1
            assert status["pending_evaluations"] == 1

            # Check evaluation details
            details = status["evaluation_details"]
            assert len(details) == 3

            # Find each evaluation in details
            eval1_detail = next(d for d in details if d["title"] == "Status Evaluation 1")
            eval2_detail = next(d for d in details if d["title"] == "Status Evaluation 2")
            eval3_detail = next(d for d in details if d["title"] == "Status Evaluation 3")

            assert eval1_detail["status"] == "passed"
            assert eval1_detail["best_score"] == 85.0
            assert eval1_detail["attempts_count"] == 1

            assert eval2_detail["status"] == "failed"
            assert eval2_detail["best_score"] == 60.0
            assert eval2_detail["attempts_count"] == 1

            assert eval3_detail["status"] == "pending"
            assert eval3_detail["best_score"] is None
            assert eval3_detail["attempts_count"] == 0

    def test_can_user_receive_certificate(self, minimal_db_setup):
        """Test can_user_receive_certificate function."""
        from now_lms.vistas.evaluation_helpers import can_user_receive_certificate
        from now_lms.db import Curso, CursoSeccion, Evaluation, Usuario, EvaluationAttempt, CursoUsuarioAvance, database

        with minimal_db_setup.app_context():
            # Create test user
            user = Usuario(
                usuario="cert_user",
                acceso=b"password123",
                nombre="Certificate",
                apellido="User",
                correo_electronico="cert@test.com",
                tipo="student",
            )
            database.session.add(user)

            # Create test course and section
            course = Curso(
                codigo="CERT_TEST",
                nombre="Certificate Test Course",
                descripcion_corta="Testing certificates",
                descripcion="Course for testing certificate functionality",
                estado="open",
                plantilla_certificado=None,
            )
            database.session.add(course)

            section = CursoSeccion(
                curso="CERT_TEST",
                nombre="Certificate Section",
                descripcion="Section for certificate testing",
                indice=1,
                estado=True,
            )
            database.session.add(section)
            database.session.flush()

            # Test with no evaluations and no progress
            can_receive, reason = can_user_receive_certificate("CERT_TEST", user.usuario)
            assert can_receive is False
            assert "completar todos los recursos" in reason

            # Create course progress (completed)
            progress = CursoUsuarioAvance(
                curso="CERT_TEST",
                usuario=user.usuario,
                completado=True,
                avance=100.0,
            )
            database.session.add(progress)
            database.session.commit()

            # Test with completed resources but no evaluations
            can_receive, reason = can_user_receive_certificate("CERT_TEST", user.usuario)
            assert can_receive is True
            assert "Cumple todos los requisitos" in reason

            # Create an evaluation
            evaluation = Evaluation(
                section_id=section.id,
                title="Certificate Evaluation",
                description="Evaluation for certificate",
                is_exam=False,
                passing_score=70.0,
                max_attempts=3,
                available_until=datetime(2025, 12, 31, 23, 59, 59),
            )
            database.session.add(evaluation)
            database.session.flush()

            # Test with evaluation but no passing attempt
            can_receive, reason = can_user_receive_certificate("CERT_TEST", user.usuario)
            assert can_receive is False
            assert "aprobar todas las evaluaciones" in reason

            # Create failing attempt
            failing_attempt = EvaluationAttempt(
                evaluation_id=evaluation.id,
                user_id=user.usuario,
                score=50.0,
                passed=False,
                submitted_at=datetime(2025, 1, 1, 10, 0, 0),
            )
            database.session.add(failing_attempt)
            database.session.commit()

            # Test with failing attempt
            can_receive, reason = can_user_receive_certificate("CERT_TEST", user.usuario)
            assert can_receive is False
            assert "aprobar todas las evaluaciones" in reason

            # Create passing attempt
            passing_attempt = EvaluationAttempt(
                evaluation_id=evaluation.id,
                user_id=user.usuario,
                score=85.0,
                passed=True,
                submitted_at=datetime(2025, 1, 2, 10, 0, 0),
            )
            database.session.add(passing_attempt)
            database.session.commit()

            # Test with all requirements met
            can_receive, reason = can_user_receive_certificate("CERT_TEST", user.usuario)
            assert can_receive is True
            assert "Cumple todos los requisitos" in reason

    def test_edge_cases_and_error_handling(self, minimal_db_setup):
        """Test edge cases and error handling."""
        from now_lms.vistas.evaluation_helpers import (
            check_user_evaluations_completed,
            get_user_evaluation_status,
            can_user_receive_certificate,
        )

        with minimal_db_setup.app_context():
            # Test with non-existent course
            all_passed, failed_count, total_count = check_user_evaluations_completed("NONEXISTENT", "nonexistent_user")
            assert all_passed is True  # No evaluations = all passed
            assert failed_count == 0
            assert total_count == 0

            # Test status with non-existent course
            status = get_user_evaluation_status("NONEXISTENT", "nonexistent_user")
            assert status["total_evaluations"] == 0
            assert status["passed_evaluations"] == 0
            assert status["failed_evaluations"] == 0
            assert status["pending_evaluations"] == 0

            # Test certificate with non-existent course
            can_receive, reason = can_user_receive_certificate("NONEXISTENT", "nonexistent_user")
            assert can_receive is False
            assert "completar todos los recursos" in reason

    def test_multiple_attempts_best_score(self, minimal_db_setup):
        """Test that best score is correctly identified from multiple attempts."""
        from now_lms.vistas.evaluation_helpers import get_user_evaluation_status
        from now_lms.db import Curso, CursoSeccion, Evaluation, Usuario, EvaluationAttempt, database

        with minimal_db_setup.app_context():
            # Create test user
            user = Usuario(
                usuario="multi_user",
                acceso=b"password123",
                nombre="Multiple",
                apellido="User",
                correo_electronico="multi@test.com",
                tipo="student",
            )
            database.session.add(user)

            # Create test course and section
            course = Curso(
                codigo="MULTI_TEST",
                nombre="Multiple Test Course",
                descripcion_corta="Testing multiple attempts",
                descripcion="Course for testing multiple attempts",
                estado="open",
                plantilla_certificado=None,
            )
            database.session.add(course)

            section = CursoSeccion(
                curso="MULTI_TEST",
                nombre="Multiple Section",
                descripcion="Section for multiple testing",
                indice=1,
                estado=True,
            )
            database.session.add(section)
            database.session.flush()

            # Create evaluation
            evaluation = Evaluation(
                section_id=section.id,
                title="Multiple Attempts Evaluation",
                description="Evaluation with multiple attempts",
                is_exam=False,
                passing_score=70.0,
                max_attempts=5,
                available_until=datetime(2025, 12, 31, 23, 59, 59),
            )
            database.session.add(evaluation)
            database.session.flush()

            # Create multiple attempts with different scores
            scores = [45.0, 65.0, 80.0, 75.0, 60.0]  # Best score is 80.0
            for i, score in enumerate(scores):
                attempt = EvaluationAttempt(
                    evaluation_id=evaluation.id,
                    user_id=user.usuario,
                    score=score,
                    passed=score >= 70.0,
                    submitted_at=datetime(2025, 1, i + 1, 10, 0, 0),
                )
                database.session.add(attempt)
            database.session.commit()

            # Test that best score is correctly identified
            status = get_user_evaluation_status("MULTI_TEST", user.usuario)
            eval_detail = status["evaluation_details"][0]
            assert eval_detail["best_score"] == 80.0  # Should be highest score
            assert eval_detail["status"] == "passed"  # Should be passed since best > 70
            assert eval_detail["attempts_count"] == 5

    def test_exam_vs_quiz_handling(self, minimal_db_setup):
        """Test handling of exams vs regular quizzes."""
        from now_lms.vistas.evaluation_helpers import get_user_evaluation_status
        from now_lms.db import Curso, CursoSeccion, Evaluation, Usuario, database

        with minimal_db_setup.app_context():
            # Create test user
            user = Usuario(
                usuario="exam_user",
                acceso=b"password123",
                nombre="Exam",
                apellido="User",
                correo_electronico="exam@test.com",
                tipo="student",
            )
            database.session.add(user)

            # Create test course and section
            course = Curso(
                codigo="EXAM_TEST",
                nombre="Exam Test Course",
                descripcion_corta="Testing exams",
                descripcion="Course for testing exam functionality",
                estado="open",
                plantilla_certificado=None,
            )
            database.session.add(course)

            section = CursoSeccion(
                curso="EXAM_TEST",
                nombre="Exam Section",
                descripcion="Section for exam testing",
                indice=1,
                estado=True,
            )
            database.session.add(section)
            database.session.flush()

            # Create quiz (is_exam=False)
            quiz = Evaluation(
                section_id=section.id,
                title="Regular Quiz",
                description="A regular quiz",
                is_exam=False,
                passing_score=70.0,
                max_attempts=3,
                available_until=datetime(2025, 12, 31, 23, 59, 59),
            )
            database.session.add(quiz)

            # Create exam (is_exam=True)
            exam = Evaluation(
                section_id=section.id,
                title="Final Exam",
                description="A final exam",
                is_exam=True,
                passing_score=75.0,
                max_attempts=2,
                available_until=datetime(2025, 12, 31, 23, 59, 59),
            )
            database.session.add(exam)
            database.session.commit()

            # Test status with different evaluation types
            status = get_user_evaluation_status("EXAM_TEST", user.usuario)
            details = status["evaluation_details"]

            quiz_detail = next(d for d in details if d["title"] == "Regular Quiz")
            exam_detail = next(d for d in details if d["title"] == "Final Exam")

            assert quiz_detail["is_exam"] is False
            assert quiz_detail["passing_score"] == 70.0

            assert exam_detail["is_exam"] is True
            assert exam_detail["passing_score"] == 75.0
