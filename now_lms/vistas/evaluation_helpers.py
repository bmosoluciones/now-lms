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

"""
NOW Learning Management System.

Evaluation helper functions.
"""


from __future__ import annotations

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------
from sqlalchemy import and_, func

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms.db import CursoSeccion, Evaluation, EvaluationAttempt, database


def check_user_evaluations_completed(course_code: str, user_id: str) -> tuple[bool, int, int]:
    """
    Check if a user has passed all evaluations for a course.

    Args:
        course_code (str): The course code
        user_id (str): The user ID

    Returns:
        tuple: (all_passed, failed_evaluations_count, total_evaluations_count)
    """
    # Get all evaluations for the course
    evaluations = (
        database.session.execute(database.select(Evaluation).join(CursoSeccion).filter(CursoSeccion.curso == course_code))
        .scalars()
        .all()
    )

    if not evaluations:
        # No evaluations = all passed
        return True, 0, 0

    total_evaluations = len(evaluations)
    failed_count = 0

    for evaluation in evaluations:
        # Check if user has passed this evaluation
        passed_attempt = (
            database.session.execute(
                database.select(EvaluationAttempt).filter(
                    and_(
                        EvaluationAttempt.evaluation_id == evaluation.id,
                        EvaluationAttempt.user_id == user_id,
                        EvaluationAttempt.passed,
                    )
                )
            )
            .scalars()
            .first()
        )

        if not passed_attempt:
            failed_count += 1

    all_passed = failed_count == 0
    return all_passed, failed_count, total_evaluations


def get_user_evaluation_status(course_code: str, user_id: str) -> dict[str, object]:
    """
    Get detailed evaluation status for a user in a course.

    Args:
        course_code (str): The course code
        user_id (str): The user ID

    Returns:
        dict: Evaluation status information
    """
    evaluations = (
        database.session.execute(database.select(Evaluation).join(CursoSeccion).filter(CursoSeccion.curso == course_code))
        .scalars()
        .all()
    )

    status: dict[str, object] = {
        "total_evaluations": len(evaluations),
        "passed_evaluations": 0,
        "failed_evaluations": 0,
        "pending_evaluations": 0,
        "evaluation_details": [],
    }

    for evaluation in evaluations:
        # Get user's best attempt for this evaluation
        best_attempt = (
            database.session.execute(
                database.select(EvaluationAttempt)
                .filter(and_(EvaluationAttempt.evaluation_id == evaluation.id, EvaluationAttempt.user_id == user_id))
                .order_by(EvaluationAttempt.score.desc())
            )
            .scalars()
            .first()
        )

        passed_evaluations = status["passed_evaluations"]
        failed_evaluations = status["failed_evaluations"]
        pending_evaluations = status["pending_evaluations"]
        evaluation_details = status["evaluation_details"]

        assert isinstance(passed_evaluations, int)
        assert isinstance(failed_evaluations, int)
        assert isinstance(pending_evaluations, int)
        assert isinstance(evaluation_details, list)

        if best_attempt:
            if best_attempt.passed:
                status["passed_evaluations"] = passed_evaluations + 1
                eval_status = "passed"
            else:
                status["failed_evaluations"] = failed_evaluations + 1
                eval_status = "failed"
        else:
            status["pending_evaluations"] = pending_evaluations + 1
            eval_status = "pending"

        evaluation_details.append(
            {
                "evaluation_id": evaluation.id,
                "title": evaluation.title,
                "is_exam": evaluation.is_exam,
                "passing_score": evaluation.passing_score,
                "status": eval_status,
                "best_score": best_attempt.score if best_attempt else None,
                "attempts_count": database.session.execute(
                    database.select(func.count(EvaluationAttempt.id)).filter(
                        and_(EvaluationAttempt.evaluation_id == evaluation.id, EvaluationAttempt.user_id == user_id)
                    )
                ).scalar(),
            }
        )
        status["evaluation_details"] = evaluation_details

    return status


def can_user_receive_certificate(course_code: str, user_id: str) -> tuple[bool, str]:
    """Check if a user can receive a certificate for a course.

    This includes checking both resource completion and evaluation completion.

    Args:
        course_code (str): The course code
        user_id (str): The user ID

    Returns:
        tuple: (can_receive, blocking_reason)
    """
    # Check evaluation completion
    all_evaluations_passed, failed_count, total_evaluations = check_user_evaluations_completed(course_code, user_id)

    if not all_evaluations_passed:
        return (
            False,
            f"Debe aprobar todas las evaluaciones. {failed_count} de {total_evaluations} evaluaciones no aprobadas.",
        )

    # Check resource completion (existing functionality)
    from now_lms.db import CursoUsuarioAvance

    avance = (
        database.session.execute(
            database.select(CursoUsuarioAvance).filter(
                and_(CursoUsuarioAvance.curso == course_code, CursoUsuarioAvance.usuario == user_id)
            )
        )
        .scalars()
        .first()
    )

    if not avance or not avance.completado:
        return False, "Debe completar todos los recursos del curso."

    return True, "Cumple todos los requisitos para recibir el certificado."
