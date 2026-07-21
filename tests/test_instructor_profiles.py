# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.

"""Integration tests for instructor profiles (now_lms/vistas/profiles/instructor.py)."""

import pytest
from datetime import datetime
from unittest import mock

from now_lms.auth import proteger_passwd
from now_lms.db import (
    Curso,
    CursoSeccion,
    DocenteCurso,
    Evaluation,
    EvaluationAttempt,
    Question,
    QuestionOption,
    Usuario,
    UsuarioGrupo,
    UsuarioGrupoMiembro,
    database,
)


@pytest.fixture
def instructor_setup(app, db_session):
    """Sets up an instructor user and an admin user."""
    instructor = Usuario(
        usuario="prof_instructor",
        acceso=proteger_passwd("instructorpass"),
        nombre="Prof Instructor",
        correo_electronico="prof_inst@example.com",
        tipo="instructor",
        activo=True,
    )
    admin = Usuario(
        usuario="prof_admin",
        acceso=proteger_passwd("adminpass"),
        nombre="Prof Admin",
        correo_electronico="prof_admin@example.com",
        tipo="admin",
        activo=True,
    )
    db_session.add_all([instructor, admin])
    db_session.commit()
    return {"instructor": instructor, "admin": admin}


@pytest.fixture
def client_instructor(client, instructor_setup, app):
    """Client authenticated as instructor."""
    with app.test_request_context():
        with client.session_transaction() as sess:
            sess["_user_id"] = instructor_setup["instructor"].id
            sess["_fresh"] = True
    return client


@pytest.fixture
def client_admin(client, instructor_setup, app):
    """Client authenticated as admin."""
    with app.test_request_context():
        with client.session_transaction() as sess:
            sess["_user_id"] = instructor_setup["admin"].id
            sess["_fresh"] = True
    return client


@pytest.fixture
def test_course(app, db_session, instructor_setup):
    """Creates a test course assigned to our test instructor."""
    course = Curso(
        nombre="Instructor Course",
        codigo="INST101",
        descripcion_corta="Short desc",
        descripcion="Long desc",
        estado="open",
        certificado=True,
        publico=True,
    )
    db_session.add(course)
    db_session.commit()

    assignment = DocenteCurso(
        curso="INST101",
        usuario=instructor_setup["instructor"].usuario,
        vigente=True,
        creado_por="system",
    )
    db_session.add(assignment)
    db_session.commit()

    section = CursoSeccion(
        curso="INST101",
        nombre="Introduction",
        descripcion="Intro section",
        indice=1,
        creado_por="system",
    )
    db_session.add(section)
    db_session.commit()

    return {"course": course, "section": section}


def test_pagina_instructor(client_instructor):
    """Test instructor dashboard home page."""
    resp = client_instructor.get("/instructor")
    assert resp.status_code == 200
    assert b"Estudiantes Inscritos" in resp.data or b"Evaluaciones Creadas" in resp.data


def test_cursos_list(client_instructor, client_admin):
    """Test course list page for instructor and admin."""
    resp_inst = client_instructor.get("/instructor/courses_list")
    assert resp_inst.status_code == 200

    resp_admin = client_admin.get("/instructor/courses_list")
    assert resp_admin.status_code == 200


def test_grupos_management(client_instructor, db_session):
    """Test listing, viewing, adding, and removing users in groups."""
    # Create group
    grupo = UsuarioGrupo(
        nombre="Test Group",
        descripcion="A test group",
        creado_por="prof_instructor",
    )
    db_session.add(grupo)
    db_session.commit()

    # List groups
    resp_list = client_instructor.get("/instructor/group/list")
    assert resp_list.status_code == 200

    # View group
    resp_view = client_instructor.get(f"/group/{grupo.id}?id={grupo.id}")
    assert resp_view.status_code == 200

    # Add user to group
    post_data = {"usuario": "prof_instructor", "id": grupo.id}
    resp_add = client_instructor.post("/group/add", data=post_data, follow_redirects=True)
    assert resp_add.status_code == 200

    # Verify membership directly in database since group template doesn't render flashed notifications
    member = db_session.execute(
        database.select(UsuarioGrupoMiembro).filter_by(grupo=grupo.id, usuario="prof_instructor")
    ).scalar_one_or_none()
    assert member is not None

    # Remove user from group
    resp_remove = client_instructor.get(f"/group/remove/{grupo.id}/prof_instructor", follow_redirects=True)
    assert resp_remove.status_code == 200


def test_evaluation_management(client_instructor, db_session, test_course):
    """Test creating, editing, and listing evaluations."""
    course_code = test_course["course"].codigo
    section_id = test_course["section"].id

    # 1. List course evaluations
    resp_list = client_instructor.get(f"/instructor/courses/{course_code}/evaluations")
    assert resp_list.status_code == 200

    # 2. Create new evaluation
    eval_data = {
        "title": "Module 1 Quiz",
        "description": "Quiz description",
        "is_exam": "y",
        "passing_score": "75.0",
        "max_attempts": "3",
    }
    resp_create = client_instructor.post(
        f"/instructor/courses/{course_code}/sections/{section_id}/evaluations/new",
        data=eval_data,
        follow_redirects=True
    )
    assert resp_create.status_code == 200
    assert b"Evaluaci\xc3\xb3n creada correctamente" in resp_create.data

    # Find created evaluation
    evaluation = db_session.execute(database.select(Evaluation).filter_by(title="Module 1 Quiz")).scalar_one()

    # 3. Edit evaluation
    edit_data = {
        "title": "Module 1 Quiz Updated",
        "description": "Updated Quiz description",
        "is_exam": "",
        "passing_score": "80.0",
        "max_attempts": "2",
    }
    resp_edit = client_instructor.post(
        f"/instructor/evaluations/{evaluation.id}/edit",
        data=edit_data,
        follow_redirects=True
    )
    assert resp_edit.status_code == 200
    assert b"Evaluaci\xc3\xb3n actualizada correctamente" in resp_edit.data

    # 4. List all evaluations
    resp_all = client_instructor.get("/instructor/evaluations")
    assert resp_all.status_code == 200

    # 5. Global select new evaluation page
    resp_new_global = client_instructor.get("/instructor/new-evaluation")
    assert resp_new_global.status_code == 200

    # 6. Toggle evaluation status
    resp_toggle = client_instructor.post(f"/instructor/evaluations/{evaluation.id}/toggle", follow_redirects=True)
    assert resp_toggle.status_code == 200


def test_question_and_options_management(client_instructor, db_session, test_course):
    """Test creating, editing, and deleting questions and options."""
    section_id = test_course["section"].id

    # Pre-create an evaluation
    evaluation = Evaluation(
        section_id=section_id,
        title="Comprehensive Quiz",
        description="Quiz",
        is_exam=False,
        passing_score=70.0,
        max_attempts=3,
        creado_por="prof_instructor",
    )
    db_session.add(evaluation)
    db_session.commit()

    # 1. Create a boolean question (this creates 2 options by default: Verdadero, Falso)
    q_data_bool = {
        "type": "boolean",
        "text": "Is Flask a framework?",
        "explanation": "Yes, Flask is a micro-framework.",
    }
    resp_q_bool = client_instructor.post(
        f"/instructor/evaluations/{evaluation.id}/questions/new",
        data=q_data_bool,
        follow_redirects=True
    )
    assert resp_q_bool.status_code == 200
    assert b"Pregunta creada correctamente" in resp_q_bool.data

    # Find question
    question = db_session.execute(database.select(Question).filter_by(text="Is Flask a framework?")).scalar_one()

    # 2. Edit question
    q_edit_data = {
        "type": "multiple",
        "text": "Is Flask a Python micro-framework?",
        "explanation": "Indeed it is.",
    }
    resp_q_edit = client_instructor.post(
        f"/instructor/questions/{question.id}/edit",
        data=q_edit_data,
        follow_redirects=True
    )
    assert resp_q_edit.status_code == 200
    assert b"Pregunta actualizada correctamente" in resp_q_edit.data

    # At this stage, we have 2 default options. Let's try to delete one of them.
    # It should block because a question needs at least 2 options.
    rem_option = db_session.execute(database.select(QuestionOption).filter_by(question_id=question.id)).scalars().first()
    resp_opt_del_block = client_instructor.post(f"/instructor/options/{rem_option.id}/delete", follow_redirects=True)
    assert resp_opt_del_block.status_code == 200
    assert b"necesitan al menos 2 opciones" in resp_opt_del_block.data

    # 3. Create question option (this adds a 3rd option)
    opt_data = {
        "text": "Absolutely Yes",
        "is_correct": "y",
    }
    resp_opt = client_instructor.post(
        f"/instructor/questions/{question.id}/options/new",
        data=opt_data,
        follow_redirects=True
    )
    assert resp_opt.status_code == 200
    assert b"Opci\xc3\xb3n agregada correctamente" in resp_opt.data

    # Find option
    option = db_session.execute(database.select(QuestionOption).filter_by(text="Absolutely Yes")).scalar_one()

    # 4. Edit option
    opt_edit = {
        "text": "Absolutely Yes - Verified",
        "is_correct": "y",
    }
    resp_opt_edit = client_instructor.post(
        f"/instructor/options/{option.id}/edit",
        data=opt_edit,
        follow_redirects=True
    )
    assert resp_opt_edit.status_code == 200
    assert b"Opci\xc3\xb3n actualizada correctamente" in resp_opt_edit.data

    # 5. Delete question option (now we have 3 options, so deleting this 3rd option should succeed!)
    resp_opt_del_success = client_instructor.post(f"/instructor/options/{option.id}/delete", follow_redirects=True)
    assert resp_opt_del_success.status_code == 200
    assert b"Opci\xc3\xb3n eliminada correctamente" in resp_opt_del_success.data

    # 6. Delete question
    resp_q_del = client_instructor.post(f"/instructor/questions/{question.id}/delete", follow_redirects=True)
    assert resp_q_del.status_code == 200
    assert b"Pregunta eliminada correctamente" in resp_q_del.data


def test_evaluation_results(client_instructor, db_session, test_course):
    """Test viewing results/statistics for an evaluation."""
    section_id = test_course["section"].id

    evaluation = Evaluation(
        section_id=section_id,
        title="Results Quiz",
        description="Quiz",
        is_exam=False,
        passing_score=70.0,
        max_attempts=3,
        creado_por="prof_instructor",
    )
    db_session.add(evaluation)
    db_session.commit()

    # Create attempts
    attempt1 = EvaluationAttempt(
        evaluation_id=evaluation.id,
        user_id="prof_instructor",
        score=85.0,
        passed=True,
        submitted_at=datetime.now(),
        creado_por="prof_instructor",
    )
    attempt2 = EvaluationAttempt(
        evaluation_id=evaluation.id,
        user_id="prof_instructor",
        score=50.0,
        passed=False,
        submitted_at=datetime.now(),
        creado_por="prof_instructor",
    )
    db_session.add_all([attempt1, attempt2])
    db_session.commit()

    resp = client_instructor.get(f"/instructor/evaluations/{evaluation.id}/results")
    assert resp.status_code == 200
    assert b"Resultados de Evaluaci\xc3\xb3n" in resp.data
