# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.

"""Tests for the fork-local member dashboard.

Failure-first: every test here fails against the pre-change tree. The ones that
matter most are the two that encode why this page exists at all — a member can
see their own stored progress, and ``/my-credentials`` is reachable.
"""

from __future__ import annotations

import pytest
from now_lms.auth import proteger_passwd
from now_lms.db import (
    Announcement,
    Curso,
    CursoUsuarioAvance,
    EstudianteCurso,
    Usuario,
    database,
)


def _limpiar(*, usuarios: tuple[str, ...], cursos: tuple[str, ...]) -> None:
    """Remove this module's fixture rows if a previous test left them behind.

    On PostgreSQL the conftest TRUNCATEs between tests and this is a no-op. On
    the SQLite path the conftest builds a fresh *app* per test but not a fresh
    *database*, so a file-backed URL keeps rows across tests and fixed codes
    collide. Deleting first makes the fixture idempotent on both.
    """
    for modelo, columna, valores in (
        (CursoUsuarioAvance, CursoUsuarioAvance.usuario, usuarios),
        (EstudianteCurso, EstudianteCurso.usuario, usuarios),
        (Announcement, Announcement.created_by_id, usuarios),
        (Curso, Curso.codigo, cursos),
        (Usuario, Usuario.usuario, usuarios),
    ):
        database.session.execute(database.delete(modelo).where(columna.in_(valores)))
    database.session.commit()


@pytest.fixture
def dashboard_setup(app, db_session):
    """A student with one course in progress, plus a global announcement."""
    with app.app_context():
        _limpiar(usuarios=("dash_student", "dash_other", "dash_empty"), cursos=("DASH01", "DASH02"))
        alumno = Usuario(
            usuario="dash_student",
            acceso=proteger_passwd("pass"),
            nombre="Dash",
            apellido="Student",
            correo_electronico="dash_student@example.test",
            tipo="student",
            activo=True,
            correo_electronico_verificado=True,
        )
        otro = Usuario(
            usuario="dash_other",
            acceso=proteger_passwd("pass"),
            nombre="Other",
            apellido="Member",
            correo_electronico="dash_other@example.test",
            tipo="student",
            activo=True,
            correo_electronico_verificado=True,
        )
        curso = Curso(
            nombre="Dashboard Course",
            codigo="DASH01",
            descripcion_corta="Short",
            descripcion="Long",
            estado="open",
            modalidad="self_paced",
            publico=False,
            pagado=False,
            certificado=False,
        )
        # A course the student dropped. The upstream panel counted these; the
        # dashboard must not, because /my_courses does not.
        curso_viejo = Curso(
            nombre="Dropped Course",
            codigo="DASH02",
            descripcion_corta="Short",
            descripcion="Long",
            estado="open",
            modalidad="self_paced",
            publico=False,
            pagado=False,
            certificado=False,
        )
        database.session.add_all([alumno, otro, curso, curso_viejo])
        database.session.commit()

        database.session.add_all(
            [
                EstudianteCurso(usuario="dash_student", curso="DASH01", vigente=True, pago=None),
                EstudianteCurso(usuario="dash_student", curso="DASH02", vigente=False, pago=None),
                CursoUsuarioAvance(
                    usuario="dash_student",
                    curso="DASH01",
                    recursos_requeridos=4,
                    recursos_completados=3,
                    avance=75.0,
                    completado=False,
                ),
                # Another member's progress on the same course. Must never leak.
                CursoUsuarioAvance(
                    usuario="dash_other",
                    curso="DASH01",
                    recursos_requeridos=4,
                    recursos_completados=4,
                    avance=100.0,
                    completado=True,
                ),
                Announcement(
                    title="Cohort call moved",
                    message="Now on Thursday.",
                    course_id=None,
                    created_by_id="dash_student",
                    is_sticky=True,
                ),
            ]
        )
        database.session.commit()
        yield app


def _entrar(client, usuario: str) -> None:
    """Sign a member in through the real login form.

    Note for anyone running this outside CI: ``inicio_sesion`` rate-limits to
    five attempts per minute per IP through ``_check_rate_limit``, which is
    backed by the cache. CI leaves the cache unconfigured, so it resolves to
    NullCache and the limiter is a no-op. Export ``NOW_LMS_MEMORY_CACHE=1``
    locally and you get a *filesystem* cache that persists the counter between
    runs, and the sixth login in any rolling minute redirects to the login page
    instead of signing in.
    """
    respuesta = client.post(
        "/user/login", data={"usuario": usuario, "acceso": "pass"}, follow_redirects=False
    )
    assert respuesta.status_code == 302, f"login for {usuario} did not redirect"
    assert not respuesta.headers["Location"].endswith("/user/login"), (
        f"login for {usuario} bounced back to the login form — if you are running locally with "
        "NOW_LMS_MEMORY_CACHE set, the login rate limiter is holding a counter from a previous run"
    )


def test_dashboard_requires_login(dashboard_setup, client):
    """Logged out, /dashboard must not render."""
    respuesta = client.get("/dashboard", follow_redirects=False)
    assert respuesta.status_code in (301, 302, 401, 403)
    assert "Welcome back" not in respuesta.get_data(as_text=True)


def test_student_login_lands_on_dashboard(dashboard_setup, client):
    """The post-login redirect for a student is /dashboard, not /home/panel."""
    respuesta = client.post(
        "/user/login", data={"usuario": "dash_student", "acceso": "pass"}, follow_redirects=False
    )
    assert respuesta.status_code == 302
    assert respuesta.headers["Location"].endswith("/dashboard")


def test_dashboard_shows_the_members_own_progress(dashboard_setup, client):
    """The whole point: the stored percentage reaches the person who earned it.

    Before this change ``CursoUsuarioAvance.avance`` was read by
    ``ops/lms/lms-progress-digest.sh`` for staff and by no member-facing
    template at all.
    """
    _entrar(client, "dash_student")
    cuerpo = client.get("/dashboard").get_data(as_text=True)
    assert "75%" in cuerpo
    assert "Dashboard Course" in cuerpo
    # One translatable string with placeholders, not fragments glued together in
    # the template — split fragments can't be reordered by a translator.
    assert "3 of 4 required items complete" in cuerpo


def test_dashboard_does_not_leak_another_members_progress(dashboard_setup, client):
    """dash_other is at 100% on the same course. It must not appear."""
    _entrar(client, "dash_student")
    cuerpo = client.get("/dashboard").get_data(as_text=True)
    assert "100%" not in cuerpo
    assert "Other" not in cuerpo


def test_dashboard_excludes_dropped_enrolments(dashboard_setup, client):
    """vigente=False must not appear, matching /my_courses rather than the old panel."""
    _entrar(client, "dash_student")
    cuerpo = client.get("/dashboard").get_data(as_text=True)
    assert "Dropped Course" not in cuerpo


def test_dashboard_links_to_prior_credentials(dashboard_setup, client):
    """/my-credentials had zero entry points in the entire template tree."""
    _entrar(client, "dash_student")
    cuerpo = client.get("/dashboard").get_data(as_text=True)
    assert "/my-credentials" in cuerpo


def test_dashboard_shows_pinned_announcements(dashboard_setup, client):
    """Announcements stay in the native model and surface here."""
    _entrar(client, "dash_student")
    cuerpo = client.get("/dashboard").get_data(as_text=True)
    assert "Cohort call moved" in cuerpo


def test_announcements_beyond_the_dashboard_cap_stay_reachable(dashboard_setup, client, app):
    """Regression: the dashboard cap must not make older announcements unreachable.

    An earlier revision redirected /dashboard/announcements to the dashboard, on
    the reasoning that one channel beats two. But the dashboard shows only
    MAX_ANNOUNCEMENTS, so everything past the newest few silently disappeared for
    every authenticated role. Found by Greptile on PR #79.

    The dashboard stays the primary door; this page is its overflow, linked from
    the card only when there is more to see.
    """
    from now_lms.vistas.member_dashboard import MAX_ANNOUNCEMENTS

    extra = MAX_ANNOUNCEMENTS + 2
    with app.app_context():
        for i in range(extra):
            database.session.add(
                Announcement(
                    title=f"Announcement number {i}",
                    message="body",
                    course_id=None,
                    created_by_id="dash_student",  # NOT NULL, matching the fixture above
                    is_sticky=False,
                    expires_at=None,
                )
            )
        database.session.commit()

    _entrar(client, "dash_student")

    # The archive renders and carries the oldest one, which the dashboard cannot show.
    archivo = client.get("/dashboard/announcements")
    assert archivo.status_code == 200, "the announcements archive must render, not redirect"
    assert "Announcement number 0" in archivo.get_data(as_text=True)

    # And the dashboard admits it is truncating, rather than hiding it.
    panel = client.get("/dashboard").get_data(as_text=True)
    assert "/dashboard/announcements" in panel, "the dashboard must link to the full archive"


def test_upcoming_event_dates_follow_the_site_locale(dashboard_setup, client, app):
    """The 'Coming up' card must render dates through Babel, not strftime.

    ``strftime('%b %d, %H:%M')`` hardcodes English month abbreviations no matter
    what the site locale is. Rendering through flask-babel's ``datetimeformat``
    filter localises the month name. Found by MiniMax review on PR #79.
    """
    from datetime import datetime

    import flask_babel

    from now_lms.db import Configuracion, UserEvent
    from now_lms.i18n import invalidate_configuracion_cache

    def _set_lang(lang: str) -> None:
        # Deliberately NOT inside a nested app.app_context(): the fixtures keep
        # an app context open for the whole test, so test-client requests reuse
        # its session. A commit made in a nested context would not expire that
        # ambient session's identity map, and requests would keep reading the
        # stale Configuracion row.
        config = database.session.execute(database.select(Configuracion)).scalars().first()
        config.lang = lang
        database.session.commit()
        invalidate_configuracion_cache()
        # flask-babel memoises the resolved locale on g, and g lives as long as
        # the fixture-held app context, i.e. across test-client requests.
        flask_babel.refresh()

    with app.app_context():
        database.session.add(
            UserEvent(
                user_id="dash_student",
                course_id="DASH01",
                resource_type="meet",
                title="Cohort call",
                start_time=datetime(2099, 12, 1, 10, 30),
            )
        )
        database.session.commit()

    _entrar(client, "dash_student")

    # English site locale: abbreviated English month, no leading zero on the day.
    _set_lang("en")
    cuerpo = client.get("/dashboard").get_data(as_text=True)
    assert "Dec 1, 10:30" in cuerpo

    # Flip the site locale and the same event renders a Spanish month name.
    _set_lang("es")
    cuerpo = client.get("/dashboard").get_data(as_text=True)
    assert "dic 1, 10:30" in cuerpo, "the event date must follow the site locale, not strftime's English"


def test_dashboard_has_no_fabricated_counters(dashboard_setup, client):
    """The upstream panel hardcoded the literal 0 with the caption 'Soon'."""
    _entrar(client, "dash_student")
    cuerpo = client.get("/dashboard").get_data(as_text=True)
    assert "Próximamente" not in cuerpo
    assert "Soon" not in cuerpo


def test_empty_dashboard_does_not_send_a_member_to_an_empty_catalog(app, db_session, client):
    """A member with no courses gets an honest state, not a loop.

    The upstream empty state pointed at /course/explore, which filters on
    ``publico=True`` while every course on this deployment is gated, so the
    member arrived somewhere with no course in it and a link back.
    """
    with app.app_context():
        _limpiar(usuarios=("dash_empty",), cursos=())
        database.session.add(
            Usuario(
                usuario="dash_empty",
                acceso=proteger_passwd("pass"),
                nombre="Empty",
                apellido="Member",
                correo_electronico="dash_empty@example.test",
                tipo="student",
                activo=True,
                correo_electronico_verificado=True,
            )
        )
        database.session.commit()

    client.post("/user/login", data={"usuario": "dash_empty", "acceso": "pass"})
    respuesta = client.get("/dashboard")
    assert respuesta.status_code == 200
    cuerpo = respuesta.get_data(as_text=True)
    assert "not enrolled in a course yet" in cuerpo
    # The upstream empty state's copy and its call to action are both gone. The
    # navbar still carries its own courses link, which is why this asserts on
    # the wording rather than on the URL appearing anywhere in the document.
    assert "Explore our wide range of courses" not in cuerpo
    assert "Explorar Cursos" not in cuerpo
    assert "Start your learning journey" not in cuerpo


def test_dashboard_query_count_is_flat_in_courses(dashboard_setup, client, app):
    """Adding courses must not add queries.

    Asserting an absolute ceiling would measure the navbar and footer, which
    issue their own uncached ``configuracion`` / ``custom_pages`` /
    ``enlaces_utiles`` reads under the test cache. The property that matters is
    the slope: enrol the member in four more courses and the query count must
    not move. Guards against reaching for the per-course helpers in
    ``evaluation_helpers``, each of which runs a query per evaluation plus a
    count.
    """
    from sqlalchemy import event

    def _contar_selects() -> int:
        consultas: list[str] = []

        def _registrar(conn, cursor, statement, parameters, context, executemany):
            consultas.append(statement)

        motor = database.engine
        event.listen(motor, "before_cursor_execute", _registrar)
        try:
            assert client.get("/dashboard").status_code == 200
        finally:
            event.remove(motor, "before_cursor_execute", _registrar)
        return len([q for q in consultas if q.lstrip().upper().startswith("SELECT")])

    _entrar(client, "dash_student")
    con_un_curso = _contar_selects()

    with app.app_context():
        for indice in range(4):
            codigo = f"DASHX{indice}"
            database.session.add(
                Curso(
                    nombre=f"Extra Course {indice}",
                    codigo=codigo,
                    descripcion_corta="Short",
                    descripcion="Long",
                    estado="open",
                    modalidad="self_paced",
                    publico=False,
                    pagado=False,
                    certificado=False,
                )
            )
            database.session.commit()
            database.session.add(
                EstudianteCurso(usuario="dash_student", curso=codigo, vigente=True, pago=None)
            )
            database.session.add(
                CursoUsuarioAvance(
                    usuario="dash_student",
                    curso=codigo,
                    recursos_requeridos=2,
                    recursos_completados=1,
                    avance=50.0,
                    completado=False,
                )
            )
        database.session.commit()

    con_cinco_cursos = _contar_selects()

    try:
        assert con_cinco_cursos == con_un_curso, (
            f"query count grew from {con_un_curso} to {con_cinco_cursos} when four courses were added — "
            "the dashboard is issuing work per course"
        )
    finally:
        with app.app_context():
            codigos = [f"DASHX{i}" for i in range(4)]
            database.session.execute(
                database.delete(CursoUsuarioAvance).where(CursoUsuarioAvance.curso.in_(codigos))
            )
            database.session.execute(database.delete(EstudianteCurso).where(EstudianteCurso.curso.in_(codigos)))
            database.session.execute(database.delete(Curso).where(Curso.codigo.in_(codigos)))
            database.session.commit()
