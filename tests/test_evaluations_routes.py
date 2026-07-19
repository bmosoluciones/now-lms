# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""
Tests unitarios y de integración para las evaluaciones.
"""

from datetime import datetime, timedelta
import json
import pytest
from flask_login import login_user, logout_user
from now_lms.db import (
    database,
    Usuario,
    Curso,
    CursoSeccion,
    EstudianteCurso,
    Evaluation,
    EvaluationAttempt,
    EvaluationReopenRequest,
    Question,
    QuestionOption,
    Answer,
)
from now_lms.auth import proteger_passwd
from now_lms.vistas.evaluations import (
    can_user_access_evaluation,
    is_evaluation_available,
    get_user_attempts_count,
    can_user_attempt_evaluation,
    calculate_score,
)

@pytest.fixture
def eval_setup(app, db_session):
    """Configura un curso, una sección, una evaluación y un estudiante de prueba."""
    student = Usuario(
        usuario="stud_eval",
        acceso=proteger_passwd("pass"),
        nombre="Student",
        correo_electronico="stud_e@example.com",
        tipo="student",
        activo=True,
        correo_electronico_verificado=True,
    )
    db_session.add(student)

    curso = Curso(
        codigo="EVAL01",
        nombre="Evaluation Course",
        descripcion_corta="eval",
        descripcion="eval",
        estado="open",
        pagado=False,
    )
    db_session.add(curso)

    seccion = CursoSeccion(
        curso="EVAL01",
        nombre="Sección 1",
        descripcion="Descripción de la sección 1",
        indice=1,
    )
    db_session.add(seccion)
    db_session.commit()

    evaluation_obj = Evaluation(
        section_id=seccion.id,
        title="Prueba de Progreso",
        description="Eval de prueba",
        passing_score=70.0,
        max_attempts=2,
    )
    db_session.add(evaluation_obj)
    db_session.commit()

    return {
        "student": student,
        "curso": curso,
        "seccion": seccion,
        "evaluation": evaluation_obj,
    }

def test_can_user_access_evaluation_no_inscription(app, db_session, eval_setup):
    """Debe denegar acceso si el usuario no está inscrito."""
    assert can_user_access_evaluation(eval_setup["evaluation"], eval_setup["student"]) is False

def test_can_user_access_evaluation_success(app, db_session, eval_setup):
    """Debe permitir acceso si el usuario está inscrito."""
    inscription = EstudianteCurso(
        curso="EVAL01",
        usuario=eval_setup["student"].usuario,
        vigente=True,
    )
    db_session.add(inscription)
    db_session.commit()

    assert can_user_access_evaluation(eval_setup["evaluation"], eval_setup["student"]) is True

def test_is_evaluation_available(app, db_session, eval_setup):
    """Verifica si la evaluación está disponible en base a la fecha límite."""
    ev = eval_setup["evaluation"]
    assert is_evaluation_available(ev) is True

    ev.available_until = datetime.now() - timedelta(days=1)
    db_session.commit()
    assert is_evaluation_available(ev) is False

def test_attempts_count_and_can_attempt(app, db_session, eval_setup):
    """Verifica el límite de intentos de la evaluación."""
    student = eval_setup["student"]
    ev = eval_setup["evaluation"]

    # Inscribir estudiante
    inscription = EstudianteCurso(
        curso="EVAL01",
        usuario=student.usuario,
        vigente=True,
    )
    db_session.add(inscription)
    db_session.commit()

    assert get_user_attempts_count(ev.id, student.usuario) == 0
    assert can_user_attempt_evaluation(ev, student) is True

    # Agregar intentos
    attempt1 = EvaluationAttempt(evaluation_id=ev.id, user_id=student.usuario, started_at=datetime.now())
    attempt2 = EvaluationAttempt(evaluation_id=ev.id, user_id=student.usuario, started_at=datetime.now())
    db_session.add_all([attempt1, attempt2])
    db_session.commit()

    assert get_user_attempts_count(ev.id, student.usuario) == 2
    # Superó el límite de max_attempts (que es 2)
    assert can_user_attempt_evaluation(ev, student) is False

def test_calculate_score_multiple_and_boolean(app, db_session, eval_setup):
    """Verifica que el puntaje se calcule correctamente."""
    ev = eval_setup["evaluation"]

    # Crear preguntas
    q1 = Question(evaluation_id=ev.id, type="boolean", text="¿1 es igual a 1?")
    q2 = Question(evaluation_id=ev.id, type="multiple", text="Elige los pares:")
    db_session.add_all([q1, q2])
    db_session.commit()

    # Opciones q1 (boolean)
    opt1_v = QuestionOption(question_id=q1.id, text="true", is_correct=True)
    opt1_f = QuestionOption(question_id=q1.id, text="false", is_correct=False)
    # Opciones q2 (multiple choice)
    opt2_a = QuestionOption(question_id=q2.id, text="2", is_correct=True)
    opt2_b = QuestionOption(question_id=q2.id, text="3", is_correct=False)
    opt2_c = QuestionOption(question_id=q2.id, text="4", is_correct=True)
    db_session.add_all([opt1_v, opt1_f, opt2_a, opt2_b, opt2_c])
    db_session.commit()

    # Intentar intento
    attempt = EvaluationAttempt(evaluation_id=ev.id, user_id=eval_setup["student"].usuario, started_at=datetime.now())
    db_session.add(attempt)
    db_session.commit()

    # Respuestas correctas
    ans1 = Answer(attempt_id=attempt.id, question_id=q1.id, selected_option_ids=json.dumps([opt1_v.id]))
    ans2 = Answer(attempt_id=attempt.id, question_id=q2.id, selected_option_ids=json.dumps([opt2_a.id, opt2_c.id]))
    db_session.add_all([ans1, ans2])
    db_session.commit()

    # Refrescar intento para cargar relaciones
    db_session.refresh(attempt)

    score = calculate_score(attempt)
    assert score == 100.0

def test_routes_take_and_result(client, db_session, eval_setup):
    """Prueba las rutas de responder evaluación y ver el resultado."""
    student = eval_setup["student"]
    ev = eval_setup["evaluation"]

    # Inscribir estudiante
    inscription = EstudianteCurso(
        curso="EVAL01",
        usuario=student.usuario,
        vigente=True,
    )
    db_session.add(inscription)
    db_session.commit()

    # Iniciar sesión
    client.post("/user/login", data={"usuario": "stud_eval", "acceso": "pass"})

    # 1. GET take
    response_get = client.get(f"/evaluation/{ev.id}/take")
    assert response_get.status_code == 200

    # 2. POST take
    response_post = client.post(
        f"/evaluation/{ev.id}/take",
        data={},
        follow_redirects=True,
    )
    assert response_post.status_code == 200

    # Obtener el intento creado
    attempt = db_session.execute(database.select(EvaluationAttempt).filter_by(evaluation_id=ev.id)).scalars().first()
    assert attempt is not None

    # 3. Ver resultado
    response_result = client.get(f"/evaluation/attempt/{attempt.id}/result")
    assert response_result.status_code == 200

def test_routes_request_reopen(client, db_session, eval_setup):
    """Prueba solicitar reabrir la evaluación."""
    student = eval_setup["student"]
    ev = eval_setup["evaluation"]

    # Inscribir estudiante
    inscription = EstudianteCurso(
        curso="EVAL01",
        usuario=student.usuario,
        vigente=True,
    )
    db_session.add(inscription)
    db_session.commit()

    # Iniciar sesión
    client.post("/user/login", data={"usuario": "stud_eval", "acceso": "pass"})

    # Registrar 2 intentos fallidos para agotar max_attempts
    attempt1 = EvaluationAttempt(evaluation_id=ev.id, user_id=student.usuario, started_at=datetime.now(), passed=False, score=20.0)
    attempt2 = EvaluationAttempt(evaluation_id=ev.id, user_id=student.usuario, started_at=datetime.now(), passed=False, score=10.0)
    db_session.add_all([attempt1, attempt2])
    db_session.commit()

    # GET request-reopen
    response_get = client.get(f"/evaluation/{ev.id}/request-reopen")
    assert response_get.status_code == 200

    # POST request-reopen
    response_post = client.post(
        f"/evaluation/{ev.id}/request-reopen",
        data={"justification_text": "Tuve problemas de conexión."},
        follow_redirects=True,
    )
    assert response_post.status_code == 200

    # Verificar que se creó la solicitud
    reopen_req = db_session.execute(database.select(EvaluationReopenRequest).filter_by(evaluation_id=ev.id)).scalars().first()
    assert reopen_req is not None
    assert reopen_req.justification_text == "Tuve problemas de conexión."
    assert reopen_req.status == "pending"
