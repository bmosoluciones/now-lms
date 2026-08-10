# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.

"""A course-content edit must invalidate the cache for every signed-in member,
not just anonymous visitors.

Fork finding L1 (audit 2026-08-07): ``invalidar_cache_curso()`` — called after
every course-content mutation: add a lesson, edit a section, publish a course,
reorder resources — deleted keys ending ``/anon`` and ``/auth``. But
``cache_key_with_auth_state()`` stopped emitting ``/auth`` when commit
``c16269a`` switched authenticated keys to ``view/<path>/user:<usuario>``. The
delete list was never updated, so the anonymous half of invalidation kept
working and the authenticated half was a silent no-op — for every enrolled
student, assigned instructor, and assigned moderator on the course, at all 33
call sites. ``_obtiene_llaves_generales_cache()`` had the identical defect for
the home page and catalog.

These tests reproduce the audit's own runtime probe: build the real
``cache_key_with_auth_state()`` key for a real course member, run the real
``invalidar_cache_curso()``, and assert the key was actually deleted. Against
the pre-fix code every assertion below fails (the member's key survives,
exactly as the audit's ``HIT? False`` probe showed); against the fix they
pass.
"""

import sys

from flask_caching import Cache

from now_lms.auth import proteger_passwd
from now_lms.db import Curso, DocenteCurso, EstudianteCurso, ModeradorCurso, Usuario, database


def _real_cache_module():
    """Resolve the actual ``now_lms.cache`` submodule, not the package-level
    ``cache`` attribute re-export — ``Cache.cache`` is a read-only property,
    so patching through the package attribute silently binds nothing the
    invalidators actually read (see test_enrollment_invalidates_course_cache.py
    for the same indirection)."""
    import now_lms.cache  # noqa: F401

    return sys.modules["now_lms.cache"]


def _wire_simple_cache(monkeypatch, app):
    """Swap in a real SimpleCache so the invalidators exercise real
    delete-by-key behaviour, independent of this app's configured backend
    (tests default to NullCache, which no-ops every delete)."""
    cache_mod = _real_cache_module()
    simple = Cache(config={"CACHE_TYPE": "SimpleCache"})
    simple.init_app(app)
    monkeypatch.setattr(cache_mod, "cache", simple)
    monkeypatch.setattr(cache_mod, "CTYPE", "SimpleCache")
    return cache_mod, simple


def _make_course(code):
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


def _make_user(username, tipo="student"):
    database.session.add(
        Usuario(
            usuario=username,
            acceso=proteger_passwd("x"),
            nombre="Cache",
            apellido="Member",
            correo_electronico=f"{username}@example.com",
            tipo=tipo,
            activo=True,
            correo_electronico_verificado=True,
            creado_por="test",
        )
    )
    database.session.commit()


def test_course_edit_invalidates_enrolled_students_cached_view(monkeypatch, app):
    """The audit's own probe, reproduced: an enrolled member's real per-user
    course-view cache key must be gone after ``invalidar_cache_curso()``."""
    cache_mod, simple = _wire_simple_cache(monkeypatch, app)

    with app.app_context():
        _make_course("CCA-F")
        _make_user("founding.member")
        database.session.add(EstudianteCurso(usuario="founding.member", curso="CCA-F", vigente=True))
        database.session.commit()

        # Exactly the key cache_key_with_auth_state() produces for
        # GET /course/CCA-F/view while logged in as founding.member.
        member_key = "view//course/CCA-F/view/user:founding.member"
        simple.set(member_key, "stale pre-edit render")
        assert simple.get(member_key) == "stale pre-edit render"

        cache_mod.invalidar_cache_curso("CCA-F")

        assert simple.get(member_key) is None, (
            "content edit did not invalidate an enrolled member's cached course "
            "view — the /auth-vs-user: key desync (fork finding L1) is back"
        )


def test_course_edit_invalidates_instructor_and_moderator_admin_views(monkeypatch, app):
    """The same defect hit the admin/moderate routes for staff assigned to
    the course, not just the student-facing view/take routes."""
    cache_mod, simple = _wire_simple_cache(monkeypatch, app)

    with app.app_context():
        _make_course("CCA-G")
        _make_user("teach.er", tipo="instructor")
        _make_user("mod.er", tipo="moderator")
        database.session.add(DocenteCurso(usuario="teach.er", curso="CCA-G", vigente=True))
        database.session.add(ModeradorCurso(usuario="mod.er", curso="CCA-G", vigente=True))
        database.session.commit()

        admin_key = "view//course/CCA-G/admin/user:teach.er"
        moderate_key = "view//course/CCA-G/moderate/user:mod.er"
        simple.set(admin_key, "stale admin render")
        simple.set(moderate_key, "stale moderate render")

        cache_mod.invalidar_cache_curso("CCA-G")

        assert simple.get(admin_key) is None
        assert simple.get(moderate_key) is None


def test_course_edit_invalidates_members_home_and_catalog_cache(monkeypatch, app):
    """``_obtiene_llaves_generales_cache()`` had the identical defect for the
    home page and catalog — publishing a course did not refresh any
    logged-in member's home either."""
    cache_mod, simple = _wire_simple_cache(monkeypatch, app)

    with app.app_context():
        _make_course("CCA-H")
        _make_user("home.member")
        database.session.add(EstudianteCurso(usuario="home.member", curso="CCA-H", vigente=True))
        database.session.commit()

        home_key = "view///user:home.member"
        catalog_key = "view//course/explore/user:home.member"
        simple.set(home_key, "stale home render")
        simple.set(catalog_key, "stale catalog render")

        cache_mod.invalidar_cache_curso("CCA-H")

        assert simple.get(home_key) is None
        assert simple.get(catalog_key) is None


def test_invalidation_leaves_other_courses_and_other_members_alone(monkeypatch, app):
    """A course edit must not become a global cache flush: a different
    member's cache on a different course must survive."""
    cache_mod, simple = _wire_simple_cache(monkeypatch, app)

    with app.app_context():
        _make_course("CCA-I")
        _make_course("CCA-J")
        _make_user("in.course")
        _make_user("other.course")
        database.session.add(EstudianteCurso(usuario="in.course", curso="CCA-I", vigente=True))
        database.session.add(EstudianteCurso(usuario="other.course", curso="CCA-J", vigente=True))
        database.session.commit()

        untouched_key = "view//course/CCA-J/view/user:other.course"
        simple.set(untouched_key, "should survive")

        cache_mod.invalidar_cache_curso("CCA-I")

        assert simple.get(untouched_key) == "should survive"
