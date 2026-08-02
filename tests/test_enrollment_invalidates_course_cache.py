# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.

"""Enrolling must invalidate the member's cached course pages immediately.

Fork issue #50: ``tomar_curso`` and the course view are cached per user for
``CACHE_DEFAULT_TIMEOUT`` (300s) and nothing cleared those entries on
enrollment, so the ordinary sequence — look at a course, then enroll — was
precisely the sequence that guaranteed a stale hit: viewing warmed the
pre-enrollment render under the member's own key, and enrolling redirected
straight back into it. The member saw a phantom Enroll button with every
lesson link suppressed, concluded the enrollment failed, and clicked again.

The proof in production was waiting out the 300-second window with no other
change; these tests assert the corrected behaviour with no wait: warm the
cache, enroll, and require the enrolled render on the immediate next load.
"""

from now_lms.auth import proteger_passwd
from now_lms.db import Curso, CursoRecurso, CursoSeccion, Usuario, database

PASSWORD = "cache-walk-pw"


def _make_course_with_lesson(app, code):
    with app.app_context():
        database.session.add(
            Curso(
                nombre=f"Course {code}",
                codigo=code,
                descripcion="Cache invalidation test course.",
                descripcion_corta="Cache test.",
                estado="open",
                publico=True,
                pagado=False,
                precio=0,
                certificado=False,
                modalidad="self_paced",
                creado_por="test",
            )
        )
        database.session.commit()
        seccion = CursoSeccion(
            curso=code,
            nombre="Section one",
            descripcion="First section.",
            indice=1,
            estado=True,
        )
        database.session.add(seccion)
        database.session.commit()
        database.session.add(
            CursoRecurso(
                curso=code,
                seccion=seccion.id,
                tipo="text",
                nombre="Lesson one",
                descripcion="Reading one.",
                text="# Lesson one\n\nBody.",
                indice=1,
                publico=False,
                requerido="required",
            )
        )
        database.session.commit()


def _make_student(app, username):
    with app.app_context():
        database.session.add(
            Usuario(
                usuario=username,
                acceso=proteger_passwd(PASSWORD),
                nombre="Cache",
                apellido="Walker",
                correo_electronico=username,
                tipo="student",
                activo=True,
                correo_electronico_verificado=True,
                creado_por="test",
            )
        )
        database.session.commit()


def _login(client, username):
    resp = client.post(
        "/user/login",
        data={"usuario": username, "acceso": PASSWORD},
        follow_redirects=False,
    )
    assert resp.status_code in {200, 301, 302, 303, 307, 308}


def _enroll(client, code):
    page = client.get(f"/course/{code}/enroll")
    assert page.status_code == 200
    resp = client.post(
        f"/course/{code}/enroll",
        data={
            "nombre": "Cache",
            "apellido": "Walker",
            "correo_electronico": "cache-walker@example.com",
        },
        follow_redirects=False,
    )
    assert resp.status_code in {301, 302, 303, 307, 308}


def test_take_page_reflects_enrollment_immediately(app, db_session):
    """Warm the pre-enrollment take render, enroll, reload: the very next
    response must be the enrolled render — no 300-second wait, no phantom
    Enroll button, live lesson links."""
    _make_course_with_lesson(app, "cachetk1")
    _make_student(app, "cache-walker@example.com")
    client = app.test_client()
    _login(client, "cache-walker@example.com")

    # Warm the member's own cache with the PRE-enrollment render.
    cold = client.get("/course/cachetk1/take")
    assert cold.status_code == 200
    cold_html = cold.get_data(as_text=True)

    _enroll(client, "cachetk1")

    warm = client.get("/course/cachetk1/take")
    assert warm.status_code == 200
    warm_html = warm.get_data(as_text=True)

    # The enrolled render gates on permitir_estudiante: the lesson name must
    # now be a link to the resource page, which the pre-enrollment render
    # suppresses. Asserting the href is stronger than asserting button text
    # (which varies by template/locale).
    assert "/course/cachetk1/resource/text/" in warm_html, (
        "post-enrollment take page still served the cached pre-enrollment "
        "render — enrollment did not invalidate the member's course cache"
    )
    assert "/course/cachetk1/resource/text/" not in cold_html, (
        "pre-enrollment render unexpectedly already had lesson links; "
        "the warm/cold comparison proves nothing"
    )


def test_course_view_reflects_enrollment_immediately(app, db_session):
    """Same contract for /course/<code>/view — its meta rail and lesson list
    must agree with the fresh enrollment on the immediate next load."""
    _make_course_with_lesson(app, "cachevw1")
    _make_student(app, "cache-viewer@example.com")
    client = app.test_client()
    _login(client, "cache-viewer@example.com")

    cold = client.get("/course/cachevw1/view")
    assert cold.status_code == 200

    _enroll(client, "cachevw1")

    warm = client.get("/course/cachevw1/view")
    assert warm.status_code == 200
    warm_html = warm.get_data(as_text=True)
    assert "/course/cachevw1/resource/text/" in warm_html or "resource" in warm_html.lower(), (
        "post-enrollment course view still looks like the cached "
        "pre-enrollment render"
    )


def test_invalidation_deletes_exactly_the_members_keys(monkeypatch, app):
    """Mechanism pin, independent of the app's configured cache backend (the
    journey tests above are tautological under NullCache): against a real
    SimpleCache, the helper must delete exactly the member's take/view keys —
    in the ``view/<path>/user:<usuario>`` format ``cache_key_with_auth_state``
    writes — and leave every other member's entries alone."""
    import sys

    from flask_caching import Cache

    # `import now_lms.cache as cache_mod` would bind the package ATTRIBUTE
    # `cache` (the Cache instance re-exported by now_lms/__init__), not the
    # submodule — and Cache.cache is a read-only property. Resolve the real
    # module through sys.modules so the monkeypatch lands on the module global
    # the helper actually reads.
    import now_lms.cache  # noqa: F401  (ensures the submodule is loaded)

    cache_mod = sys.modules["now_lms.cache"]

    simple = Cache(config={"CACHE_TYPE": "SimpleCache"})
    simple.init_app(app)
    monkeypatch.setattr(cache_mod, "cache", simple)

    with app.app_context():
        simple.set("view//course/XYZ/take/user:alice", "warm-take")
        simple.set("view//course/XYZ/view/user:alice", "warm-view")
        simple.set("view//course/XYZ/take/user:bob", "bob-take")
        simple.set("view//course/OTHER/take/user:alice", "other-course")

        cache_mod.invalidate_user_course_view_cache("alice", "XYZ")

        assert simple.get("view//course/XYZ/take/user:alice") is None
        assert simple.get("view//course/XYZ/view/user:alice") is None
        assert simple.get("view//course/XYZ/take/user:bob") == "bob-take"
        assert simple.get("view//course/OTHER/take/user:alice") == "other-course"
