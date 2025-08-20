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

Evaluations management.
"""

# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------
import json
from datetime import datetime

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import func

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms.auth import perfil_requerido
from now_lms.db import (
    Answer,
    Curso,
    CursoSeccion,
    EstudianteCurso,
    Evaluation,
    EvaluationAttempt,
    EvaluationReopenRequest,
    QuestionOption,
    database,
)
from now_lms.forms import EvaluationReopenRequestForm

# ---------------------------------------------------------------------------------------
# Blueprint definition
# ---------------------------------------------------------------------------------------

# <--------------------------------------------------------------------------> #
# Route constants
ROUTE_COURSE_TOMAR_CURSO = "course.tomar_curso"
EVALUATION_CREATED = "Evaluación creada correctamente."
EVALUATION_UPDATED = "Evaluación actualizada correctamente."
EVALUATION_DELETED = "Evaluación eliminada correctamente."
QUESTION_ADDED = "Pregunta agregada correctamente."
QUESTION_UPDATED = "Pregunta actualizada correctamente."
QUESTION_DELETED = "Pregunta eliminada correctamente."
EVALUATION_SUBMITTED = "Evaluación enviada correctamente."
REOPEN_REQUEST_SUBMITTED = "Solicitud de reabrir evaluación enviada."
REOPEN_REQUEST_APPROVED = "Solicitud aprobada. El estudiante puede realizar un nuevo intento."
REOPEN_REQUEST_REJECTED = "Solicitud rechazada."
NO_AUTHORIZED_MSG = "No se encuentra autorizado a acceder al recurso solicitado."

# <--------------------------------------------------------------------------> #
# Blueprint for evaluation management
evaluation = Blueprint("evaluation", __name__)


def can_user_access_evaluation(evaluation_obj, user):
    """Check if user can access evaluation based on course payment status."""
    # Get the course from the section
    section = database.session.get(CursoSeccion, evaluation_obj.section_id)
    if not section:
        return False

    course_code = section.curso

    # Check if user is enrolled in the course
    inscription = (
        database.session.execute(database.select(EstudianteCurso).filter_by(curso=course_code, usuario=user.usuario))
        .scalars()
        .first()
    )
    if not inscription:
        return False

    # Check if course is paid and user has paid

    course = database.session.execute(database.select(Curso).filter_by(codigo=course_code)).scalars().first()
    if course and course.pagado:
        # Check if user has paid for the course
        enrollment = (
            database.session.execute(database.select(EstudianteCurso).filter_by(curso=course_code, usuario=user.usuario))
            .scalars()
            .first()
        )

        if not enrollment or not enrollment.pago:
            return False  # User hasn't paid for paid course

    return True


def is_evaluation_available(evaluation_obj):
    """Check if evaluation is currently available."""
    if evaluation_obj.available_until:
        return datetime.now() <= evaluation_obj.available_until
    return True


def get_user_attempts_count(evaluation_id, user_id):
    """Get the number of attempts a user has made for an evaluation."""
    return database.session.execute(
        database.select(func.count(EvaluationAttempt.id)).filter_by(evaluation_id=evaluation_id, user_id=user_id)
    ).scalar()


def can_user_attempt_evaluation(evaluation_obj, user):
    """Check if user can attempt the evaluation."""
    if not can_user_access_evaluation(evaluation_obj, user):
        return False

    if not is_evaluation_available(evaluation_obj):
        return False

    if evaluation_obj.max_attempts:
        attempts_count = get_user_attempts_count(evaluation_obj.id, user.usuario)
        if attempts_count >= evaluation_obj.max_attempts:
            return False

    return True


def calculate_score(attempt):
    """Calculate the score for an evaluation attempt."""
    total_questions = len(attempt.evaluation.questions)
    if total_questions == 0:
        return 0.0

    correct_answers = 0

    for answer in attempt.answers:
        question = answer.question
        if question.type == "boolean":
            # For boolean questions, check if the selected option is correct
            if answer.selected_option_ids:
                selected_ids = json.loads(answer.selected_option_ids)
                if len(selected_ids) == 1:
                    option = database.session.get(QuestionOption, selected_ids[0])
                    if option and option.is_correct:
                        correct_answers += 1
        elif question.type == "multiple":
            # For multiple choice, check if all correct options are selected and no incorrect ones
            if answer.selected_option_ids:
                selected_ids = json.loads(answer.selected_option_ids)
                correct_option_ids = [opt.id for opt in question.options if opt.is_correct]

                if set(selected_ids) == set(correct_option_ids):
                    correct_answers += 1

    return (correct_answers / total_questions) * 100


@evaluation.route("/evaluation/<evaluation_id>/take", methods=["GET", "POST"])
@login_required
@perfil_requerido("student")
def take_evaluation(evaluation_id):
    """Take an evaluation."""
    eval_obj = database.session.get(Evaluation, evaluation_id)
    if not eval_obj:
        abort(404)

    # Check if user can access this evaluation
    if not can_user_access_evaluation(eval_obj, current_user):
        flash("No tiene acceso a esta evaluación.", "warning")
        abort(403)

    # Check if user can attempt this evaluation
    if not can_user_attempt_evaluation(eval_obj, current_user):
        flash("No puede realizar más intentos en esta evaluación.", "warning")
        section = database.session.get(CursoSeccion, eval_obj.section_id)
        return redirect(url_for(ROUTE_COURSE_TOMAR_CURSO, course_code=section.curso))

    if request.method == "POST":
        # Create new attempt
        attempt = EvaluationAttempt(evaluation_id=evaluation_id, user_id=current_user.usuario, started_at=datetime.now())
        database.session.add(attempt)
        database.session.flush()  # Get the attempt ID

        # Save answers
        for question in eval_obj.questions:
            answer_key = f"question_{question.id}"
            if answer_key in request.form:
                selected_values = request.form.getlist(answer_key)

                # Find the corresponding option IDs
                selected_option_ids = []
                for value in selected_values:
                    if question.type == "boolean":
                        # For boolean questions, value is "true" or "false"
                        option = (
                            database.session.execute(
                                database.select(QuestionOption).filter_by(question_id=question.id, text=value)
                            )
                            .scalars()
                            .first()
                        )
                        if option:
                            selected_option_ids.append(option.id)
                    else:
                        # For multiple choice, value is the option ID
                        selected_option_ids.append(value)

                answer = Answer(
                    attempt_id=attempt.id, question_id=question.id, selected_option_ids=json.dumps(selected_option_ids)
                )
                database.session.add(answer)

        # Calculate score and determine if passed
        attempt.submitted_at = datetime.now()
        attempt.score = calculate_score(attempt)
        attempt.passed = attempt.score >= eval_obj.passing_score

        database.session.commit()

        flash(EVALUATION_SUBMITTED, "success")
        return redirect(url_for("evaluation.evaluation_result", attempt_id=attempt.id))

    return render_template("evaluations/take_evaluation.html", evaluation=eval_obj)


@evaluation.route("/evaluation/attempt/<attempt_id>/result")
@login_required
@perfil_requerido("student")
def evaluation_result(attempt_id):
    """Show evaluation attempt result."""
    attempt = database.session.get(EvaluationAttempt, attempt_id)
    if not attempt:
        abort(404)

    # Check if user owns this attempt
    if attempt.user_id != current_user.usuario:
        abort(403)

    return render_template("evaluations/evaluation_result.html", attempt=attempt)


@evaluation.route("/evaluation/<evaluation_id>/request-reopen", methods=["GET", "POST"])
@login_required
@perfil_requerido("student")
def request_reopen(evaluation_id):
    """Request to reopen an evaluation."""
    eval_obj = database.session.get(Evaluation, evaluation_id)
    if not eval_obj:
        abort(404)

    # Check if user can access this evaluation
    if not can_user_access_evaluation(eval_obj, current_user):
        abort(403)

    # Check if user has exhausted attempts and not passed
    attempts_count = get_user_attempts_count(evaluation_id, current_user.usuario)
    if not eval_obj.max_attempts or attempts_count < eval_obj.max_attempts:
        flash("Aún tiene intentos disponibles.", "info")
        section = database.session.get(CursoSeccion, eval_obj.section_id)
        return redirect(url_for(ROUTE_COURSE_TOMAR_CURSO, course_code=section.curso))

    # Check if user has passed any attempt
    passed_attempt = (
        database.session.execute(
            database.select(EvaluationAttempt).filter_by(
                evaluation_id=evaluation_id, user_id=current_user.usuario, passed=True
            )
        )
        .scalars()
        .first()
    )

    if passed_attempt:
        flash("Ya ha aprobado esta evaluación.", "info")
        section = database.session.get(CursoSeccion, eval_obj.section_id)
        return redirect(url_for(ROUTE_COURSE_TOMAR_CURSO, course_code=section.curso))

    form = EvaluationReopenRequestForm()

    if form.validate_on_submit():
        # Check if there's already a pending request
        existing_request = (
            database.session.execute(
                database.select(EvaluationReopenRequest).filter_by(
                    user_id=current_user.usuario, evaluation_id=evaluation_id, status="pending"
                )
            )
            .scalars()
            .first()
        )

        if existing_request:
            flash("Ya tiene una solicitud pendiente para esta evaluación.", "warning")
            section = database.session.get(CursoSeccion, eval_obj.section_id)
            return redirect(url_for(ROUTE_COURSE_TOMAR_CURSO, course_code=section.curso))

        reopen_request = EvaluationReopenRequest(
            user_id=current_user.usuario, evaluation_id=evaluation_id, justification_text=form.justification_text.data
        )

        database.session.add(reopen_request)
        database.session.commit()

        flash(REOPEN_REQUEST_SUBMITTED, "success")
        section = database.session.get(CursoSeccion, eval_obj.section_id)
        return redirect(url_for(ROUTE_COURSE_TOMAR_CURSO, course_code=section.curso))

    return render_template("evaluations/request_reopen.html", evaluation=eval_obj, form=form)


# Instructor routes will be added to the instructor profile blueprint
