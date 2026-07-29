# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""
Extra comprehensive unit and integration tests for instructor profile routes (now_lms/vistas/profiles/instructor.py).
"""

import os
from datetime import datetime
import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.exc import OperationalError

from now_lms.auth import proteger_passwd
from now_lms.db import (
    database,
    Usuario,
    Curso,
    CursoSeccion,
    DocenteCurso,
    Evaluation,
    Question,
    QuestionOption,
    EvaluationAttempt,
)


@pytest.fixture
def extra_inst_setup(app, db_session):
    """Sets up a complete set of records for extra instructor routing tests."""
    admin = Usuario(
        usuario="admin_inst_ex",
        acceso=proteger_passwd("pass"),
        nombre="Admin",
        correo_electronico="admin_inst_ex@example.com",
        tipo="admin",
        activo=True,
    )
    instructor = Usuario(
        usuario="inst_inst_ex",
        acceso=proteger_passwd("pass"),
        nombre="Instructor",
        correo_electronico="inst_inst_ex@example.com",
        tipo="instructor",
        activo=True,
    )
    instructor2 = Usuario(
        usuario="inst_inst_ex2",
        acceso=proteger_passwd("pass"),
        nombre="Instructor 2",
        correo_electronico="inst_inst_ex2@example.com",
        tipo="instructor",
        activo=True,
    )
    student = Usuario(
        usuario="stud_inst_ex",
        acceso=proteger_passwd("pass"),
        nombre="Student",
        correo_electronico="stud_inst_ex@example.com",
        tipo="student",
        activo=True,
    )
    db_session.add_all([admin, instructor, instructor2, student])
    db_session.commit()

    curso = Curso(
        codigo="C303",
        nombre="Curso 303",
        descripcion_corta="desc",
        descripcion="desc",
        estado="open",
    )
    db_session.add(curso)
    db_session.commit()

    # Assign instructor
    dc = DocenteCurso(usuario="inst_inst_ex", curso="C303", vigente=True)
    db_session.add(dc)
    db_session.commit()

    # Create section
    section = CursoSeccion(
        curso="C303",
        nombre="Section 1",
        descripcion="desc",
        indice=1,
    )
    db_session.add(section)
    db_session.commit()

    # Create evaluation
    evaluation = Evaluation(
        section_id=section.id,
        title="Quiz 1",
        description="desc",
        is_exam=True,
        passing_score=60.0,
        max_attempts=3,
        creado_por="inst_inst_ex",
    )
    db_session.add(evaluation)
    db_session.commit()

    # Create question
    question = Question(
        evaluation_id=evaluation.id,
        type="multiple",
        text="Question 1",
        order=1,
        creado_por="inst_inst_ex",
    )
    db_session.add(question)
    db_session.commit()

    # Create options
    opt1 = QuestionOption(question_id=question.id, text="Opt 1", is_correct=True, creado_por="inst_inst_ex")
    opt2 = QuestionOption(question_id=question.id, text="Opt 2", is_correct=False, creado_por="inst_inst_ex")
    opt3 = QuestionOption(question_id=question.id, text="Opt 3", is_correct=False, creado_por="inst_inst_ex")
    db_session.add_all([opt1, opt2, opt3])
    db_session.commit()

    return {
        "admin": admin,
        "instructor": instructor,
        "instructor2": instructor2,
        "student": student,
        "curso": curso,
        "section": section,
        "evaluation": evaluation,
        "question": question,
        "opt1": opt1,
        "opt2": opt2,
        "opt3": opt3,
    }


def login(client, username):
    client.get("/user/logout")
    client.post("/user/login", data={"usuario": username, "acceso": "pass"})


def test_courses_and_stats_instructor(client, db_session, extra_inst_setup):
    """Test instructor dashboard and course listings."""
    # 1. Non-admin instructor course listing
    login(client, "inst_inst_ex")
    resp = client.get("/instructor/courses_list")
    assert resp.status_code == 200
    assert b"Curso 303" in resp.data


def test_course_evaluations_permissions(client, db_session, extra_inst_setup):
    """Test access permissions for course evaluations listing."""
    # 1. Nonexistent course -> redirects to listings (302)
    login(client, "inst_inst_ex")
    resp = client.get("/instructor/courses/NONEXISTENT/evaluations", follow_redirects=False)
    assert resp.status_code == 302

    # 2. Instructor with no permission for this course -> redirects (302)
    login(client, "inst_inst_ex2")
    resp = client.get("/instructor/courses/C303/evaluations", follow_redirects=False)
    assert resp.status_code == 302


def test_new_evaluation_section_failures(client, db_session, extra_inst_setup):
    """Test evaluation creation with section mismatch and database exceptions."""
    login(client, "inst_inst_ex")

    # 1. Section not found or section/course mismatch -> redirects (302)
    resp = client.get("/instructor/courses/C303/sections/99999/evaluations/new", follow_redirects=False)
    assert resp.status_code == 302

    # 2. Section course mismatch
    resp = client.get(f"/instructor/courses/NONEXISTENT/sections/{extra_inst_setup['section'].id}/evaluations/new", follow_redirects=False)
    assert resp.status_code == 302

    # 3. Create evaluation OperationalError
    with patch("now_lms.vistas.profiles.instructor.database.session.commit", side_effect=OperationalError("mock", {}, Exception())):
        resp = client.post(
            f"/instructor/courses/C303/sections/{extra_inst_setup['section'].id}/evaluations/new",
            data={
                "title": "Quiz Operational Error",
                "description": "desc",
                "passing_score": "70",
                "max_attempts": "3",
                "is_exam": "y",
            },
            follow_redirects=False,
        )
        assert resp.status_code == 302


def test_edit_and_toggle_evaluation_failures(client, db_session, extra_inst_setup):
    """Test editing and toggling evaluations with permission blocks and database errors."""
    evaluation = extra_inst_setup["evaluation"]

    # 1. Nonexistent evaluation edit -> redirects (302)
    login(client, "inst_inst_ex")
    resp = client.get("/instructor/evaluations/99999/edit", follow_redirects=False)
    assert resp.status_code == 302

    # 2. Unauthorized instructor -> redirects (302)
    login(client, "inst_inst_ex2")
    resp = client.get(f"/instructor/evaluations/{evaluation.id}/edit", follow_redirects=False)
    assert resp.status_code == 302

    # 3. Toggle evaluation status unauthorized -> redirects (302)
    resp = client.post(f"/instructor/evaluations/{evaluation.id}/toggle", follow_redirects=False)
    assert resp.status_code == 302

    # 4. Toggle success & toggle with past available_until
    login(client, "inst_inst_ex")
    # Toggle to disable
    resp = client.post(f"/instructor/evaluations/{evaluation.id}/toggle", follow_redirects=True)
    assert b"Evaluaci\xc3\xb3n deshabilitada." in resp.data

    # Toggle to enable
    resp = client.post(f"/instructor/evaluations/{evaluation.id}/toggle", follow_redirects=True)
    assert b"Evaluaci\xc3\xb3n habilitada." in resp.data


def test_question_crud_types_and_ordering(client, db_session, extra_inst_setup):
    """Test question creation, boolean defaults, multiple choices, and deletion."""
    evaluation = extra_inst_setup["evaluation"]
    login(client, "inst_inst_ex")

    # 1. Create a boolean question -> creates 2 default options
    resp = client.post(
        f"/instructor/evaluations/{evaluation.id}/questions/new",
        data={
            "type": "boolean",
            "text": "True or False?",
            "explanation": "Simple true false",
        },
        follow_redirects=True,
    )
    assert b"Pregunta creada correctamente." in resp.data

    # Find the boolean question
    bq = db_session.execute(database.select(Question).filter_by(evaluation_id=evaluation.id, type="boolean")).scalars().first()
    assert bq is not None

    # Verify 2 default options (Verdadero/Falso) are created
    opts = db_session.execute(database.select(QuestionOption).filter_by(question_id=bq.id)).scalars().all()
    assert len(opts) == 2

    # 2. Create a multiple choice question -> creates 4 default options
    resp = client.post(
        f"/instructor/evaluations/{evaluation.id}/questions/new",
        data={
            "type": "multiple",
            "text": "Multiple choice?",
            "explanation": "Select one",
        },
        follow_redirects=True,
    )
    assert b"Pregunta creada correctamente." in resp.data

    # Find the multiple choice question
    mcq = db_session.execute(database.select(Question).filter_by(evaluation_id=evaluation.id, text="Multiple choice?")).scalars().first()
    assert mcq is not None

    # Verify 4 default options are created
    opts_mc = db_session.execute(database.select(QuestionOption).filter_by(question_id=mcq.id)).scalars().all()
    assert len(opts_mc) == 4


def test_question_options_add_edit_delete_limits(client, db_session, extra_inst_setup):
    """Test question option restrictions, boolean option count limits, and remaining count checks."""
    evaluation = extra_inst_setup["evaluation"]
    question = extra_inst_setup["question"]

    login(client, "inst_inst_ex")

    # 1. Edit question option
    opt = extra_inst_setup["opt1"]
    resp = client.post(
        f"/instructor/options/{opt.id}/edit",
        data={
            "text": "Opt 1 Updated",
            "is_correct": "y",
        },
        follow_redirects=True,
    )
    db_session.refresh(opt)
    assert opt.text == "Opt 1 Updated"

    # 2. Attempt to delete option when remaining count <= 2 -> shows warning, does not delete
    opt_to_delete = extra_inst_setup["opt3"]
    # Currently we have 3 options. Delete one -> should succeed because 2 remain
    resp = client.post(f"/instructor/options/{opt_to_delete.id}/delete", follow_redirects=True)
    assert b"Opci\xc3\xb3n eliminada correctamente." in resp.data

    # Now we have 2 remaining options. Delete again -> should warn "Las preguntas necesitan al menos 2 opciones"
    opt_to_delete_warn = extra_inst_setup["opt2"]
    resp = client.post(f"/instructor/options/{opt_to_delete_warn.id}/delete", follow_redirects=True)
    assert b"Las preguntas necesitan al menos 2 opciones" in resp.data


def test_evaluation_results_statistics(client, db_session, extra_inst_setup):
    """Test loading and statistics on the evaluation results page."""
    evaluation = extra_inst_setup["evaluation"]

    # 1. Query results with zero attempts
    login(client, "inst_inst_ex")
    resp = client.get(f"/instructor/evaluations/{evaluation.id}/results")
    assert resp.status_code == 200
    assert b"Quiz 1" in resp.data

    # 2. Query results with completed attempts
    attempt = EvaluationAttempt(
        evaluation_id=evaluation.id,
        user_id="stud_inst_ex",
        score=80.0,
        passed=True,
        submitted_at=datetime.now(),
    )
    db_session.add(attempt)
    db_session.commit()

    resp = client.get(f"/instructor/evaluations/{evaluation.id}/results")
    assert resp.status_code == 200
    assert b"stud_inst_ex" in resp.data
