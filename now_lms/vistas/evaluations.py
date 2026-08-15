# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.

"""
NOW Learning Management System.

Evaluations management.
"""

from __future__ import annotations

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
from sqlalchemy.orm import selectinload
from werkzeug.wrappers import Response

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
    Question,
    QuestionOption,
    database,
)
from now_lms.forms import EvaluationReopenRequestForm
from now_lms.i18n import _
from now_lms.themes import (
    get_evaluation_result_template,
    get_practice_template,
    get_take_evaluation_template,
)

# ---------------------------------------------------------------------------------------
# Blueprint definition
# ---------------------------------------------------------------------------------------

# <--------------------------------------------------------------------------> #
# Route constants
ROUTE_COURSE_TOMAR_CURSO = "course.tomar_curso"
EVALUATION_CREATED = _("Evaluación creada correctamente.")
EVALUATION_UPDATED = _("Evaluación actualizada correctamente.")
EVALUATION_DELETED = _("Evaluación eliminada correctamente.")
QUESTION_ADDED = _("Pregunta agregada correctamente.")
QUESTION_UPDATED = _("Pregunta actualizada correctamente.")
QUESTION_DELETED = _("Pregunta eliminada correctamente.")
EVALUATION_SUBMITTED = _("Evaluación enviada correctamente.")
REOPEN_REQUEST_SUBMITTED = _("Solicitud de reabrir evaluación enviada.")
REOPEN_REQUEST_APPROVED = _("Solicitud aprobada. El estudiante puede realizar un nuevo intento.")
REOPEN_REQUEST_REJECTED = _("Solicitud rechazada.")
NO_AUTHORIZED_MSG = _("No se encuentra autorizado a acceder al recurso solicitado.")

# <--------------------------------------------------------------------------> #
# Blueprint for evaluation management
evaluation = Blueprint("evaluation", __name__)


def can_user_access_evaluation(evaluation_obj, user) -> bool:
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


def is_evaluation_available(evaluation_obj) -> bool:
    """Check if evaluation is currently available."""
    if evaluation_obj.available_until:
        return datetime.now() <= evaluation_obj.available_until
    return True


def get_user_attempts_count(evaluation_id: int, user_id: str) -> int:
    """Get the number of attempts a user has made for an evaluation."""
    result = database.session.execute(
        database.select(func.count(EvaluationAttempt.id)).filter_by(evaluation_id=evaluation_id, user_id=user_id)
    ).scalar()
    return result or 0


def can_user_attempt_evaluation(evaluation_obj, user) -> bool:
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


def _answer_is_correct(answer) -> bool:
    """Determine whether a submitted answer is correct."""
    if not answer.selected_option_ids:
        return False
    selected_ids = json.loads(answer.selected_option_ids)
    if answer.question.type == "boolean":
        if len(selected_ids) != 1:
            return False
        option = database.session.get(QuestionOption, selected_ids[0])
        return bool(option and option.is_correct)
    if answer.question.type == "multiple":
        correct_ids = {option.id for option in answer.question.options if option.is_correct}
        return set(selected_ids) == correct_ids
    return False


def calculate_score(attempt) -> float:
    """Calculate the score for an evaluation attempt."""
    total_questions = len(attempt.evaluation.questions)
    if total_questions == 0:
        return 0.0

    correct_answers = sum(_answer_is_correct(answer) for answer in attempt.answers)

    return (correct_answers / total_questions) * 100


def _resolve_option_ids(question, selected_values: list[str]) -> list[str]:
    """Resolve form values to option IDs based on question type."""
    option_ids: list[str] = []
    for value in selected_values:
        if question.type != "boolean":
            option_ids.append(value)
            continue
        option = (
            database.session.execute(database.select(QuestionOption).filter_by(question_id=question.id, text=value))
            .scalars()
            .first()
        )
        if option:
            option_ids.append(option.id)
    return option_ids


def _save_question_answers(attempt, evaluation_obj) -> None:
    """Process and save answers for all questions in an evaluation attempt."""
    for question in evaluation_obj.questions:
        answer_key = f"question_{question.id}"
        if answer_key not in request.form:
            continue
        selected_values = request.form.getlist(answer_key)
        selected_option_ids = _resolve_option_ids(question, selected_values)
        answer = Answer(
            attempt_id=attempt.id,
            question_id=question.id,
            selected_option_ids=json.dumps(selected_option_ids),
        )
        database.session.add(answer)


def _try_issue_certificate(section) -> None:
    """Attempt to issue a certificate if the user is eligible."""
    if not section:
        return
    from now_lms.vistas.courses import _emitir_certificado
    from now_lms.vistas.evaluation_helpers import can_user_receive_certificate

    can_receive, _reason = can_user_receive_certificate(section.curso, current_user.usuario)
    if not can_receive:
        return
    curso = database.session.execute(database.select(Curso).filter(Curso.codigo == section.curso)).scalars().first()
    if curso and curso.certificado and curso.plantilla_certificado:
        _emitir_certificado(section.curso, current_user.usuario, curso.plantilla_certificado)


@evaluation.route("/evaluation/<evaluation_id>/take", methods=["GET", "POST"])
@login_required
@perfil_requerido("student")
def take_evaluation(evaluation_id: int) -> str | Response:
    """Take an evaluation."""
    eval_obj = database.session.get(Evaluation, evaluation_id)
    if not eval_obj:
        abort(404)

    if not can_user_access_evaluation(eval_obj, current_user):
        flash(_("No tiene acceso a esta evaluación."), "warning")
        abort(403)

    if not can_user_attempt_evaluation(eval_obj, current_user):
        flash(_("No puede realizar más intentos en esta evaluación."), "warning")
        section = database.session.get(CursoSeccion, eval_obj.section_id)
        return redirect(url_for(ROUTE_COURSE_TOMAR_CURSO, course_code=section.curso))

    if request.method == "POST":
        attempt = EvaluationAttempt(evaluation_id=evaluation_id, user_id=current_user.usuario, started_at=datetime.now())
        database.session.add(attempt)
        database.session.flush()

        _save_question_answers(attempt, eval_obj)

        attempt.submitted_at = datetime.now()
        attempt.score = calculate_score(attempt)
        attempt.passed = attempt.score >= eval_obj.passing_score

        database.session.commit()

        if attempt.passed:
            section = database.session.get(CursoSeccion, eval_obj.section_id)
            _try_issue_certificate(section)

        flash(EVALUATION_SUBMITTED, "success")
        return redirect(url_for("evaluation.evaluation_result", attempt_id=attempt.id))

    return render_template(get_take_evaluation_template(), evaluation=eval_obj)


@evaluation.route("/evaluation/attempt/<attempt_id>/result", methods=["GET"])
@login_required
@perfil_requerido("student")
def evaluation_result(attempt_id: int) -> str:
    """Show evaluation attempt result."""
    attempt = database.session.get(EvaluationAttempt, attempt_id)
    if not attempt:
        abort(404)

    # Check if user owns this attempt
    if attempt.user_id != current_user.usuario:
        abort(403)

    return render_template(get_evaluation_result_template(), attempt=attempt)


def _certification_practice(usuario: str, certification_key: str | None = None):
    """Every labelled question, grouped by certification and then by domain.

    Practice is its own area of the product, not a feature of a course (Max,
    2026-08-09: "practice tests are their own domain ... outside of courses"). Keying
    it by course was actively wrong: CCA-F alone carries questions for two credentials,
    so a member drilling "their" domains saw 12 of them — the 5 for Architect
    Foundations mashed together with the 7 for Architect Professional.

    De-duplicated by question text for the same reason the course view was: the same
    bank item is seeded into a section quiz and again into that course's mock exam.
    """
    query = database.select(Question).filter(Question.certification_key.isnot(None))
    if certification_key:
        query = query.filter(Question.certification_key == certification_key)
    rows = list(
        database.session.execute(
            query.options(selectinload(Question.options)).order_by(Question.order, Question.id)
        ).scalars()
    )

    seen: set = set()
    questions = []
    for question in rows:
        identity = (question.certification_key, question.text)
        if identity in seen:
            continue
        seen.add(identity)
        questions.append(question)

    latest = _latest_answers(usuario)

    certifications: dict = {}
    for question in questions:
        cert = certifications.setdefault(
            question.certification_key,
            {
                "key": question.certification_key,
                "name": question.certification_name or question.certification_key,
                "domains": {},
                "total": 0,
            },
        )
        cert["total"] += 1
        domain = cert["domains"].setdefault(
            question.domain_key or "unlabelled",
            {
                "key": question.domain_key or "unlabelled",
                "name": question.domain_name or question.domain_key or "Unlabelled",
                "questions": [],
                "seen": 0,
                "correct": 0,
            },
        )
        domain["questions"].append(question)
        chosen = latest.get(question.text)
        if chosen is not None:
            domain["seen"] += 1
            if chosen == sorted(option.text for option in question.options if option.is_correct):
                domain["correct"] += 1
    return certifications


def _latest_answers(usuario: str) -> dict:
    """The member's most recent answer to each question, keyed by question TEXT.

    Text rather than id because the same bank item exists as several rows, and each
    copy owns its own QuestionOption rows — so comparing ids across copies could only
    ever say "wrong". Values are sorted option TEXT for the same reason.
    """
    latest: dict = {}
    attempts = list(
        database.session.execute(
            database.select(EvaluationAttempt)
            .options(
                selectinload(EvaluationAttempt.answers)
                .selectinload(Answer.question)
                .selectinload(Question.options)
            )
            .filter_by(user_id=usuario)
            .order_by(EvaluationAttempt.started_at)
        ).scalars()
    )
    for attempt in attempts:
        for answer in attempt.answers:
            if not answer.selected_option_ids or answer.question is None:
                continue
            chosen = set(json.loads(answer.selected_option_ids))
            latest[answer.question.text] = sorted(
                option.text for option in answer.question.options if option.id in chosen
            )
    return latest


@evaluation.route("/practice")
@evaluation.route("/practice/<certification_key>")
@evaluation.route("/practice/<certification_key>/<domain_key>")
@login_required
@perfil_requerido("student")
def practice(certification_key: str | None = None, domain_key: str | None = None) -> str | Response:
    """Practice by certification, then by domain. Outside courses entirely.

    Records nothing: a drill is rehearsal, and the exam surface stays the only place a
    score is earned. No course enrollment is required — practice is its own area, open
    to any signed-in member.
    """
    certifications = _certification_practice(current_user.usuario)

    selected_cert = None
    if certification_key:
        selected_cert = certifications.get(certification_key)
        if selected_cert is None:
            abort(404)

    selected_domain = None
    if domain_key:
        selected_domain = selected_cert["domains"].get(domain_key)
        if selected_domain is None:
            abort(404)

    return render_template(
        get_practice_template(),
        certifications=sorted(certifications.values(), key=lambda c: c["name"]),
        selected_cert=selected_cert,
        selected_domain=selected_domain,
        domains=sorted(selected_cert["domains"].values(), key=lambda d: d["name"]) if selected_cert else [],
        questions=selected_domain["questions"] if selected_domain else [],
    )


@evaluation.route("/evaluation/<evaluation_id>/request-reopen", methods=["GET", "POST"])
@login_required
@perfil_requerido("student")
def request_reopen(evaluation_id: int) -> str | Response:
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
        flash(_("Aún tiene intentos disponibles."), "info")
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
        flash(_("Ya ha aprobado esta evaluación."), "info")
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
            flash(_("Ya tiene una solicitud pendiente para esta evaluación."), "warning")
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
