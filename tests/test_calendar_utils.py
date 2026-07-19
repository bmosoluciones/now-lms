# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.

"""Unit tests for calendar utilities (now_lms/calendar_utils.py)."""

import threading
from datetime import date, datetime, time, timedelta
from unittest import mock

import pytest

from now_lms.auth import proteger_passwd
from now_lms.calendar_utils import (
    _combine_date_time,
    cleanup_events_for_course_unenrollment,
    create_events_for_student_enrollment,
    get_upcoming_events_for_user,
    update_evaluation_events,
    update_meet_resource_events,
)
from now_lms.db import (
    Curso,
    CursoRecurso,
    CursoSeccion,
    Evaluation,
    UserEvent,
    Usuario,
    database,
)


@pytest.fixture
def test_data(app, db_session):
    """Sets up a test user, course, section, meet resource, and evaluation."""
    # Create a user
    user = Usuario(
        usuario="calendar_student",
        acceso=proteger_passwd("password123"),
        nombre="Calendar Student",
        correo_electronico="cal@example.com",
        tipo="student",
        activo=True,
    )
    db_session.add(user)

    # Create a course
    course = Curso(
        nombre="Calendar Course",
        codigo="CAL101",
        descripcion_corta="Short desc",
        descripcion="Long desc",
        estado="open",
        certificado=False,
        publico=True,
    )
    db_session.add(course)
    db_session.commit()

    # Create section
    section = CursoSeccion(
        curso="CAL101",
        nombre="Week 1",
        descripcion="Section description",
        indice=1,
        creado_por="calendar_student",
    )
    db_session.add(section)
    db_session.commit()

    # Create meet resource
    meet_resource = CursoRecurso(
        curso="CAL101",
        seccion=section.id,
        nombre="Live Meet 1",
        descripcion="Meeting description",
        tipo="meet",
        fecha=(datetime.now() + timedelta(days=10)).date(),
        hora_inicio=time(10, 0),
        hora_fin=time(11, 0),
        creado_por="calendar_student",
    )
    db_session.add(meet_resource)

    # Create evaluation
    evaluation = Evaluation(
        section_id=section.id,
        title="Quiz 1",
        description="Quiz description",
        is_exam=False,
        passing_score=70.0,
        max_attempts=3,
        available_until=datetime.now() + timedelta(days=20),
        creado_por="calendar_student",
    )
    db_session.add(evaluation)
    db_session.commit()

    return {
        "user_id": user.usuario,
        "course_id": course.codigo,
        "section_id": section.id,
        "resource_id": meet_resource.id,
        "evaluation_id": evaluation.id,
        "meet_date": meet_resource.fecha,
        "eval_deadline": evaluation.available_until,
    }


def mock_thread_start(self):
    """Executes target synchronously for background thread testing."""
    self._target(*self._args, **self._kwargs)


def test_combine_date_time():
    """Test the internal datetime combiner helper."""
    d = date(2026, 3, 15)
    t = time(14, 30)
    assert _combine_date_time(None, t) is None
    assert _combine_date_time(d, None) == datetime(2026, 3, 15, 9, 0)
    assert _combine_date_time(d, t) == datetime(2026, 3, 15, 14, 30)


def test_create_events_for_student_enrollment(app, db_session, test_data):
    """Test creating events upon student enrollment."""
    # Run enrollment event creation
    create_events_for_student_enrollment(test_data["user_id"], test_data["course_id"])

    # Query created UserEvents
    events = db_session.execute(
        database.select(UserEvent).filter_by(user_id=test_data["user_id"])
    ).scalars().all()

    assert len(events) == 2

    meet_event = next(e for e in events if e.resource_type == "meet")
    assert meet_event.title == "Live Meet 1"
    assert meet_event.description == "Meeting description"
    assert meet_event.start_time == datetime.combine(test_data["meet_date"], time(10, 0))
    assert meet_event.end_time == datetime.combine(test_data["meet_date"], time(11, 0))

    eval_event = next(e for e in events if e.resource_type == "evaluation")
    assert eval_event.title == "Fecha límite: Quiz 1"
    assert eval_event.start_time == test_data["eval_deadline"]


def test_create_events_already_exists(app, db_session, test_data):
    """Test that duplicate events are not created."""
    # First creation
    create_events_for_student_enrollment(test_data["user_id"], test_data["course_id"])
    events_count_1 = len(
        db_session.execute(
            database.select(UserEvent).filter_by(user_id=test_data["user_id"])
        ).scalars().all()
    )
    assert events_count_1 == 2

    # Second creation (should skip creating new ones)
    create_events_for_student_enrollment(test_data["user_id"], test_data["course_id"])
    events_count_2 = len(
        db_session.execute(
            database.select(UserEvent).filter_by(user_id=test_data["user_id"])
        ).scalars().all()
    )
    assert events_count_2 == 2


def test_create_events_exception_handling(app, db_session, test_data):
    """Test that exceptions in create_events are gracefully caught and logged."""
    with mock.patch("now_lms.calendar_utils.database.session.execute", side_effect=Exception("Database error")):
        # Should not raise an exception
        create_events_for_student_enrollment(test_data["user_id"], test_data["course_id"])


def test_update_meet_resource_events(app, db_session, test_data):
    """Test modifying a meet resource updates associated calendar events."""
    # Create the event first
    create_events_for_student_enrollment(test_data["user_id"], test_data["course_id"])

    # Modify the resource
    resource = db_session.get(CursoRecurso, test_data["resource_id"])
    resource.nombre = "Updated Meet Name"
    resource.descripcion = "Updated Meet Desc"
    resource.fecha = date(2026, 5, 25)
    db_session.commit()

    # Call update with thread mocked to run synchronously
    with mock.patch.object(threading.Thread, "start", mock_thread_start):
        update_meet_resource_events(test_data["resource_id"])

    # Query event to check if updated
    event = db_session.execute(
        database.select(UserEvent).filter_by(user_id=test_data["user_id"], resource_type="meet")
    ).scalar_one()

    assert event.title == "Updated Meet Name"
    assert event.description == "Updated Meet Desc"
    assert event.start_time == datetime(2026, 5, 25, 10, 0)


def test_update_meet_resource_not_found(app, db_session):
    """Test update with invalid or non-meet resource doesn't crash."""
    with mock.patch.object(threading.Thread, "start", mock_thread_start):
        # Invalid ID should not crash
        update_meet_resource_events("nonexistent_id")


def test_update_evaluation_events(app, db_session, test_data):
    """Test modifying an evaluation updates associated calendar events."""
    # Create the event first
    create_events_for_student_enrollment(test_data["user_id"], test_data["course_id"])

    # Modify evaluation
    evaluation = db_session.get(Evaluation, test_data["evaluation_id"])
    evaluation.title = "Updated Evaluation Title"
    evaluation.available_until = datetime(2026, 6, 15, 12, 0, 0)
    db_session.commit()

    # Call update with thread mocked to run synchronously
    with mock.patch.object(threading.Thread, "start", mock_thread_start):
        update_evaluation_events(test_data["evaluation_id"])

    # Query event
    event = db_session.execute(
        database.select(UserEvent).filter_by(user_id=test_data["user_id"], resource_type="evaluation")
    ).scalar_one()

    assert event.title == "Fecha límite: Updated Evaluation Title"
    assert event.start_time == datetime(2026, 6, 15, 12, 0, 0)


def test_update_evaluation_not_found(app, db_session):
    """Test update with invalid evaluation ID doesn't crash."""
    with mock.patch.object(threading.Thread, "start", mock_thread_start):
        update_evaluation_events("nonexistent_eval")


def test_get_upcoming_events_for_user(app, db_session, test_data):
    """Test getting upcoming events for a user."""
    # Create events
    create_events_for_student_enrollment(test_data["user_id"], test_data["course_id"])

    # Call upcoming events helper
    upcoming = get_upcoming_events_for_user(test_data["user_id"], limit=5)
    assert len(upcoming) == 2

    # Verify order (sorted by start_time)
    assert upcoming[0].start_time < upcoming[1].start_time

    # Test edge case with invalid inputs
    assert get_upcoming_events_for_user("", limit=5) == []
    assert get_upcoming_events_for_user(test_data["user_id"], limit=-1) == []


def test_cleanup_events_for_course_unenrollment(app, db_session, test_data):
    """Test cleaning up calendar events when student unenrolls."""
    # Create events
    create_events_for_student_enrollment(test_data["user_id"], test_data["course_id"])
    events_count_before = len(
        db_session.execute(
            database.select(UserEvent).filter_by(user_id=test_data["user_id"])
        ).scalars().all()
    )
    assert events_count_before == 2

    # Unenroll/cleanup
    cleanup_events_for_course_unenrollment(test_data["user_id"], test_data["course_id"])

    events_count_after = len(
        db_session.execute(
            database.select(UserEvent).filter_by(user_id=test_data["user_id"])
        ).scalars().all()
    )
    assert events_count_after == 0


def test_cleanup_events_exception_handling(app, db_session, test_data):
    """Test cleanup exceptions are caught gracefully."""
    with mock.patch("now_lms.calendar_utils.database.session.execute", side_effect=Exception("Database error")):
        cleanup_events_for_course_unenrollment(test_data["user_id"], test_data["course_id"])
