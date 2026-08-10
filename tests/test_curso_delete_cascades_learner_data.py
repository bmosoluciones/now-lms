# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.

"""Deleting a Curso that still has real learner data must not crash.

Found while testing the C1 --reset guard (audit 2026-08-07): `Curso.inscripciones`
and `Curso.user_events` were declared without `passive_deletes=True`, even though
their child tables (`EstudianteCurso.curso`, `UserEvent.course_id`) are already
`ondelete="CASCADE"` at the DB level and both are NOT NULL columns. Without
`passive_deletes=True`, SQLAlchemy's unit-of-work does not trust the DB's own
cascade — on `db.session.delete(curso)` it instead tries to disassociate any
LOADED children by setting their FK to NULL, and that UPDATE fails immediately
against a NOT NULL column. So deleting (or `--reset`-ing) a course that has an
enrolled student, or a calendar event, crashed with an unhandled
IntegrityError instead of either succeeding or refusing cleanly.

`secciones` and `recursos` carried the identical missing config, but the only
caller (`scripts/seed_cca_courses.py::_delete_course`) always empties them
manually before deleting the course, so that half of the defect was latent
rather than triggered. Fixed here too for consistency — the whole point of
`passive_deletes=True` is trusting the DB cascade instead of the caller having
to pre-empty every child table by hand.
"""

from now_lms.auth import proteger_passwd
from now_lms.db import Curso, EstudianteCurso, Usuario, UserEvent, database


def _make_course(code):
    course = Curso(
        nombre=f"Course {code}",
        codigo=code,
        descripcion_corta="Cascade delete test course.",
        descripcion="Cascade delete test course.",
        estado="open",
        publico=True,
        pagado=False,
        precio=0,
        certificado=False,
        modalidad="self_paced",
        creado_por="test",
    )
    database.session.add(course)
    database.session.commit()
    return course


def _make_user(username):
    user = Usuario(
        usuario=username,
        acceso=proteger_passwd("x"),
        nombre="Cascade",
        apellido="Delete",
        correo_electronico=f"{username}@example.com",
        tipo="student",
        activo=True,
        correo_electronico_verificado=True,
        creado_por="test",
    )
    database.session.add(user)
    database.session.commit()
    return user


def test_delete_course_with_enrolled_student_cascades_cleanly(app, db_session):
    _make_course("CASCADE-DEL-1")
    _make_user("cascade.student")
    database.session.add(EstudianteCurso(usuario="cascade.student", curso="CASCADE-DEL-1", vigente=True))
    database.session.commit()

    curso = database.session.execute(database.select(Curso).filter_by(codigo="CASCADE-DEL-1")).scalar_one()
    database.session.delete(curso)
    database.session.commit()  # must not raise IntegrityError

    assert database.session.execute(database.select(Curso).filter_by(codigo="CASCADE-DEL-1")).scalar_one_or_none() is None
    remaining = database.session.execute(
        database.select(EstudianteCurso).filter_by(curso="CASCADE-DEL-1")
    ).scalar_one_or_none()
    assert remaining is None, "the DB's own ON DELETE CASCADE should have removed the enrollment row"


def test_delete_course_with_calendar_event_cascades_cleanly(app, db_session):
    from datetime import datetime, timezone

    _make_course("CASCADE-DEL-2")
    _make_user("cascade.calendar.user")
    database.session.add(
        UserEvent(
            user_id="cascade.calendar.user",
            course_id="CASCADE-DEL-2",
            resource_type="meet",
            title="Live session",
            start_time=datetime.now(timezone.utc),
        )
    )
    database.session.commit()

    curso = database.session.execute(database.select(Curso).filter_by(codigo="CASCADE-DEL-2")).scalar_one()
    database.session.delete(curso)
    database.session.commit()  # must not raise IntegrityError

    remaining = database.session.execute(
        database.select(UserEvent).filter_by(course_id="CASCADE-DEL-2")
    ).scalar_one_or_none()
    assert remaining is None, "the DB's own ON DELETE CASCADE should have removed the calendar event"


def test_delete_course_with_both_still_cascades_cleanly(app, db_session):
    """The realistic case: a course with both an enrolled student and a
    calendar event tied to it, deleted in one transaction."""
    from datetime import datetime, timezone

    _make_course("CASCADE-DEL-3")
    _make_user("cascade.both.user")
    database.session.add(EstudianteCurso(usuario="cascade.both.user", curso="CASCADE-DEL-3", vigente=True))
    database.session.add(
        UserEvent(
            user_id="cascade.both.user",
            course_id="CASCADE-DEL-3",
            resource_type="meet",
            title="Live session",
            start_time=datetime.now(timezone.utc),
        )
    )
    database.session.commit()

    curso = database.session.execute(database.select(Curso).filter_by(codigo="CASCADE-DEL-3")).scalar_one()
    database.session.delete(curso)
    database.session.commit()

    assert database.session.execute(database.select(Curso).filter_by(codigo="CASCADE-DEL-3")).scalar_one_or_none() is None


def test_delete_course_after_loading_its_calendar_events(app, db_session):
    """The case `passive_deletes=True` does NOT cover, found by review on PR #78.

    `passive_deletes=True` stops SQLAlchemy loading unloaded children in order to
    disassociate them, but it does not stop it disassociating children that are
    ALREADY in the session. `UserEvent.course_id` is NOT NULL, so nulling a loaded
    row raises IntegrityError even though the database would have cascaded happily.

    The three sibling relationships are `lazy="dynamic"` and therefore can never be
    loaded into the session, which is why only `user_events` needs the stronger
    setting. Touching `curso.user_events` before the delete is all it takes, and any
    view that renders a course's calendar does exactly that.
    """
    from datetime import datetime, timezone

    _make_course("CASCADE-DEL-4")
    _make_user("cascade.loaded.user")
    database.session.add(
        UserEvent(
            user_id="cascade.loaded.user",
            course_id="CASCADE-DEL-4",
            resource_type="meet",
            title="Live session",
            start_time=datetime.now(timezone.utc),
        )
    )
    database.session.commit()

    curso = database.session.execute(database.select(Curso).filter_by(codigo="CASCADE-DEL-4")).scalar_one()

    # The difference from the sibling test: load the collection first.
    assert len(curso.user_events) == 1

    database.session.delete(curso)
    database.session.commit()  # must not raise IntegrityError

    remaining = database.session.execute(
        database.select(UserEvent).filter_by(course_id="CASCADE-DEL-4")
    ).scalar_one_or_none()
    assert remaining is None, "the DB's own ON DELETE CASCADE should have removed the loaded calendar event"
