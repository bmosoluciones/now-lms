# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.

"""Unit tests for evaluation helper functions (now_lms/vistas/evaluation_helpers.py)."""

import pytest

from now_lms.auth import proteger_passwd
from now_lms.db import (
    Curso,
    CursoSeccion,
    CursoUsuarioAvance,
    Evaluation,
    EvaluationAttempt,
    Usuario,
    database,
)
from now_lms.vistas.evaluation_helpers import (
    can_user_receive_certificate,
    check_user_evaluations_completed,
    get_user_evaluation_status,
)


@pytest.fixture
def eval_setup(app, db_session):
    """Sets up a test student, a course, and a section."""
    user = Usuario(
        usuario="eval_student",
        acceso=proteger_passwd("password123"),
        nombre="Eval Student",
        correo_electronico="eval@example.com",
        tipo="student",
        activo=True,
    )
    db_session.add(user)

    course = Curso(
        nombre="Evaluation Course",
        codigo="EVAL101",
        descripcion_corta="Short desc",
        descripcion="Long desc",
        estado="open",
        certificado=True,
        publico=True,
    )
    db_session.add(course)
    db_session.commit()

    section = CursoSeccion(
        curso="EVAL101",
        nombre="Section 1",
        descripcion="Section description",
        indice=1,
        creado_por="eval_student",
    )
    db_session.add(section)
    db_session.commit()

    return {
        "user_id": user.usuario,
        "course_code": course.codigo,
        "section_id": section.id,
    }


def test_check_user_evaluations_completed_no_evaluations(app, db_session, eval_setup):
    """If a course has no evaluations, all_passed should be True."""
    all_passed, failed_count, total = check_user_evaluations_completed(
        eval_setup["course_code"], eval_setup["user_id"]
    )
    assert all_passed is True
    assert failed_count == 0
    assert total == 0


def test_check_user_evaluations_completed_with_evaluations(app, db_session, eval_setup):
    """Test various pass/fail states with multiple evaluations."""
    # Create two evaluations
    eval1 = Evaluation(
        section_id=eval_setup["section_id"],
        title="Exam 1",
        description="Exam 1 desc",
        is_exam=True,
        passing_score=70.0,
        max_attempts=3,
        creado_por="eval_student",
    )
    eval2 = Evaluation(
        section_id=eval_setup["section_id"],
        title="Exam 2",
        description="Exam 2 desc",
        is_exam=True,
        passing_score=80.0,
        max_attempts=3,
        creado_por="eval_student",
    )
    db_session.add_all([eval1, eval2])
    db_session.commit()

    # Scenario 1: No attempts yet -> 2 failed, total 2, all_passed = False
    all_passed, failed_count, total = check_user_evaluations_completed(
        eval_setup["course_code"], eval_setup["user_id"]
    )
    assert all_passed is False
    assert failed_count == 2
    assert total == 2

    # Scenario 2: Passed eval1, but not eval2 -> 1 failed, total 2, all_passed = False
    attempt1 = EvaluationAttempt(
        evaluation_id=eval1.id,
        user_id=eval_setup["user_id"],
        score=75.0,
        passed=True,
        creado_por="eval_student",
    )
    db_session.add(attempt1)
    db_session.commit()

    all_passed, failed_count, total = check_user_evaluations_completed(
        eval_setup["course_code"], eval_setup["user_id"]
    )
    assert all_passed is False
    assert failed_count == 1
    assert total == 2

    # Scenario 3: Passed both -> 0 failed, total 2, all_passed = True
    attempt2 = EvaluationAttempt(
        evaluation_id=eval2.id,
        user_id=eval_setup["user_id"],
        score=85.0,
        passed=True,
        creado_por="eval_student",
    )
    db_session.add(attempt2)
    db_session.commit()

    all_passed, failed_count, total = check_user_evaluations_completed(
        eval_setup["course_code"], eval_setup["user_id"]
    )
    assert all_passed is True
    assert failed_count == 0
    assert total == 2


def test_get_user_evaluation_status_and_details(app, db_session, eval_setup):
    """Test that get_user_evaluation_status returns correct statuses and attempt details."""
    eval1 = Evaluation(
        section_id=eval_setup["section_id"],
        title="Exam 1",
        description="Exam 1 desc",
        is_exam=True,
        passing_score=70.0,
        max_attempts=3,
        creado_por="eval_student",
    )
    eval2 = Evaluation(
        section_id=eval_setup["section_id"],
        title="Exam 2",
        description="Exam 2 desc",
        is_exam=True,
        passing_score=80.0,
        max_attempts=3,
        creado_por="eval_student",
    )
    db_session.add_all([eval1, eval2])
    db_session.commit()

    # Scenario 1: No attempts
    status = get_user_evaluation_status(eval_setup["course_code"], eval_setup["user_id"])
    assert status["total_evaluations"] == 2
    assert status["passed_evaluations"] == 0
    assert status["failed_evaluations"] == 0
    assert status["pending_evaluations"] == 2

    details = status["evaluation_details"]
    assert len(details) == 2
    assert details[0]["status"] == "pending"
    assert details[0]["best_score"] is None
    assert details[0]["attempts_count"] == 0

    # Scenario 2: Failed attempt on eval1, passed attempt on eval2
    attempt_fail = EvaluationAttempt(
        evaluation_id=eval1.id,
        user_id=eval_setup["user_id"],
        score=50.0,
        passed=False,
        creado_por="eval_student",
    )
    attempt_pass = EvaluationAttempt(
        evaluation_id=eval2.id,
        user_id=eval_setup["user_id"],
        score=90.0,
        passed=True,
        creado_por="eval_student",
    )
    db_session.add_all([attempt_fail, attempt_pass])
    db_session.commit()

    status = get_user_evaluation_status(eval_setup["course_code"], eval_setup["user_id"])
    assert status["total_evaluations"] == 2
    assert status["passed_evaluations"] == 1
    assert status["failed_evaluations"] == 1
    assert status["pending_evaluations"] == 0

    details = status["evaluation_details"]
    # Verify values for the failed one
    fail_detail = next(d for d in details if d["evaluation_id"] == eval1.id)
    assert fail_detail["status"] == "failed"
    assert fail_detail["best_score"] == 50.0
    assert fail_detail["attempts_count"] == 1

    # Verify values for the passed one
    pass_detail = next(d for d in details if d["evaluation_id"] == eval2.id)
    assert pass_detail["status"] == "passed"
    assert pass_detail["best_score"] == 90.0
    assert pass_detail["attempts_count"] == 1


def test_can_user_receive_certificate(app, db_session, eval_setup):
    """Test certificate eligibility check (evaluations + resources)."""
    # Create an evaluation
    eval1 = Evaluation(
        section_id=eval_setup["section_id"],
        title="Exam 1",
        description="Exam 1 desc",
        is_exam=True,
        passing_score=70.0,
        max_attempts=3,
        creado_por="eval_student",
    )
    db_session.add(eval1)
    db_session.commit()

    # Scenario 1: Evaluations not completed -> False
    can_receive, reason = can_user_receive_certificate(eval_setup["course_code"], eval_setup["user_id"])
    assert can_receive is False
    assert "Debe aprobar todas las evaluaciones" in reason

    # Complete evaluation
    attempt = EvaluationAttempt(
        evaluation_id=eval1.id,
        user_id=eval_setup["user_id"],
        score=80.0,
        passed=True,
        creado_por="eval_student",
    )
    db_session.add(attempt)
    db_session.commit()

    # Scenario 2: Evaluations complete, but resource progress missing/incomplete -> False
    can_receive, reason = can_user_receive_certificate(eval_setup["course_code"], eval_setup["user_id"])
    assert can_receive is False
    assert "Debe completar todos los recursos" in reason

    # Add resource progress (incomplete)
    progress = CursoUsuarioAvance(
        curso=eval_setup["course_code"],
        usuario=eval_setup["user_id"],
        completado=False,
        creado_por="eval_student",
    )
    db_session.add(progress)
    db_session.commit()

    can_receive, reason = can_user_receive_certificate(eval_setup["course_code"], eval_setup["user_id"])
    assert can_receive is False
    assert "Debe completar todos los recursos" in reason

    # Scenario 3: Complete both evaluations and resources -> True
    progress.completado = True
    db_session.commit()

    can_receive, reason = can_user_receive_certificate(eval_setup["course_code"], eval_setup["user_id"])
    assert can_receive is True
    assert "Cumple todos los requisitos" in reason
