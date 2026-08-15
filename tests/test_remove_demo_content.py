# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.

"""Upstream's sample content is removed, and only when nobody is using it.

`initial_setup()` creates four demo courses and a sample blog post on a fresh
database, and they then simply stay. On 2026-08-09 all five were still served
publicly on production — the removal existed as a script nobody had a reason to run.

These tests pin the two refusals, because this deletes real rows: a course somebody
is enrolled in, and a blog post somebody has commented on, must both survive.
"""

import importlib.util
import pathlib

import pytest

from now_lms.db import BlogPost, Curso, EstudianteCurso, Usuario, database

_PATH = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "seed_practice_tracks.py"
_spec = importlib.util.spec_from_file_location("seed_practice_tracks", _PATH)
tracks = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tracks)


@pytest.fixture
def db_session(app):
    with app.app_context():
        database.create_all()
        yield database.session
        database.session.rollback()


def _ensure_user(usuario, correo, tipo="student"):
    """Get-or-create. The fixture does not roll back committed rows between tests, so a
    plain insert of the same admin twice raises and poisons the session for whatever
    runs next."""
    existing = database.session.execute(database.select(Usuario).filter_by(usuario=usuario)).scalars().first()
    if existing is not None:
        return existing
    user = Usuario(
        usuario=usuario,
        acceso=b"x",
        nombre="Test",
        apellido="User",
        correo_electronico=correo,
        tipo=tipo,
        activo=True,
    )
    database.session.add(user)
    database.session.commit()
    return user


def _ensure_course(code):
    """Get-or-create.

    The shared `app` fixture runs `initial_setup()`, which already seeds upstream's
    demo courses — which is exactly the state this feature exists to clean up, so the
    tests use it rather than fighting it.
    """
    existing = database.session.execute(database.select(Curso).filter_by(codigo=code)).scalars().first()
    if existing is not None:
        return existing
    curso = Curso(
        # Use the name upstream actually seeds, so the fixture is real demo content
        # rather than something the identity guard would rightly refuse to touch.
        nombre=tracks.DEMO_COURSES.get(code, f"Demo {code}"),
        codigo=code,
        descripcion_corta="short",
        descripcion="long",
        estado="open",
        publico=True,
        modalidad="self_paced",
        nivel=1,
        duracion=1,
        pagado=False,
        auditable=False,
        certificado=False,
    )
    database.session.add(curso)
    database.session.commit()
    return curso


def test_a_demo_course_nobody_is_using_is_removed(db_session):
    """Uses `resources`, not `now`: upstream seeds a Certificacion against `now`."""
    _ensure_course("resources")

    tracks.remove_demo_courses(database)

    assert (
        database.session.execute(database.select(Curso).filter_by(codigo="resources")).scalars().first() is None
    )


def test_a_demo_course_with_an_enrollment_survives(db_session):
    """The guard that matters: a member's course is never deleted to tidy the catalog."""
    _ensure_course("free")
    _ensure_user("a-member", "member@example.invalid")
    db_session.add(EstudianteCurso(usuario="a-member", curso="free", vigente=True))
    db_session.commit()

    tracks.remove_demo_courses(database)

    survivor = database.session.execute(database.select(Curso).filter_by(codigo="free")).scalars().first()
    assert survivor is not None, "a course with an enrollment must not be deleted"


def test_lms_training_is_never_touched(db_session):
    """It is upstream's operator manual, not demo content, and it is role-gated upstream."""
    assert "lms-training" not in tracks.DEMO_COURSE_CODES
    _ensure_course("lms-training")

    tracks.remove_demo_courses(database)

    assert (
        database.session.execute(database.select(Curso).filter_by(codigo="lms-training")).scalars().first() is not None
    )


def _ensure_blog_post(**overrides):
    """Get-or-create, for the same reason the courses are.

    `initial_setup()` seeds this exact post, so each test already starts with it
    present — which is the real-world state the removal has to handle.
    """
    existing = (
        database.session.execute(database.select(BlogPost).filter_by(slug=tracks.DEMO_BLOG_SLUG)).scalars().first()
    )
    if existing is not None:
        for key, value in overrides.items():
            setattr(existing, key, value)
        database.session.commit()
        return existing
    fields = {
        "title": "The Importance of Online Learning in Today's World",
        "slug": tracks.DEMO_BLOG_SLUG,
        "content": "sample",
        "author_id": "lms-admin",
        "status": "published",
        "allow_comments": True,
        "comment_count": 0,
    }
    fields.update(overrides)
    post = BlogPost(**fields)
    database.session.add(post)
    database.session.commit()
    return post


def test_the_untouched_sample_blog_post_is_removed(db_session):
    _ensure_user("lms-admin", "admin@example.invalid", tipo="admin")
    _ensure_blog_post(comment_count=0)

    tracks.remove_demo_blog_post(database)

    assert (
        database.session.execute(database.select(BlogPost).filter_by(slug=tracks.DEMO_BLOG_SLUG)).scalars().first()
        is None
    )


def test_a_commented_blog_post_survives(db_session):
    """Deleting a member's words to tidy the blog is worse than a stale post."""
    _ensure_user("lms-admin", "admin@example.invalid", tipo="admin")
    _ensure_blog_post(comment_count=3)

    tracks.remove_demo_blog_post(database)

    survivor = (
        database.session.execute(database.select(BlogPost).filter_by(slug=tracks.DEMO_BLOG_SLUG)).scalars().first()
    )
    assert survivor is not None, "a post with comments must not be deleted"


def test_removal_is_idempotent(db_session):
    """The deploy runs this every time; a second pass must be a silent no-op."""
    _ensure_course("details")

    tracks.remove_demo_courses(database)
    tracks.remove_demo_blog_post(database)
    tracks.remove_demo_courses(database)
    tracks.remove_demo_blog_post(database)

    assert database.session.execute(database.select(Curso).filter_by(codigo="details")).scalars().first() is None


def test_a_repurposed_course_code_is_not_treated_as_demo(db_session):
    """A course code is an address, not an identity.

    An administrator can rename "free" into real content. With no enrollments yet, a
    cleanup keyed on the code alone would delete it on the next deploy — and this now
    runs automatically, so the blast radius is every deploy rather than one manual run.
    """
    curso = _ensure_course("free")
    curso.nombre = "Prompt Engineering Fundamentals"
    database.session.commit()

    tracks.remove_demo_courses(database)

    survivor = database.session.execute(database.select(Curso).filter_by(codigo="free")).scalars().first()
    assert survivor is not None, "a renamed course is not upstream's sample"
    assert survivor.nombre == "Prompt Engineering Fundamentals"


def test_a_rewritten_blog_post_survives(db_session):
    """The slug comes from the title, so rewriting the body leaves it unchanged."""
    _ensure_user("lms-admin", "admin@example.invalid", tipo="admin")
    _ensure_blog_post(comment_count=0, content="Our own article, written from scratch by Intent Solutions.")

    tracks.remove_demo_blog_post(database)

    survivor = (
        database.session.execute(database.select(BlogPost).filter_by(slug=tracks.DEMO_BLOG_SLUG)).scalars().first()
    )
    assert survivor is not None, "a rewritten post must not be deleted"


def test_the_seeded_body_is_what_marks_a_post_as_upstreams(db_session):
    """The positive case, so the guard above cannot pass by simply never deleting."""
    _ensure_user("lms-admin", "admin@example.invalid", tipo="admin")
    _ensure_blog_post(comment_count=0, content=tracks.DEMO_BLOG_OPENING + " And the rest of upstream's article.")

    tracks.remove_demo_blog_post(database)

    assert (
        database.session.execute(database.select(BlogPost).filter_by(slug=tracks.DEMO_BLOG_SLUG)).scalars().first()
        is None
    )


def test_a_seeded_certificate_does_not_protect_a_demo_course(db_session):
    """Intent Solutions does not issue certifications — these are practice tests.

    `crear_certificacion()` seeds a Certificacion against course "now" for the admin,
    with no matching enrollment. It is upstream demo data, not a member asset, so it
    must not block the cleanup — otherwise `now`, the most visible demo course on the
    front door, could never be removed.

    The enrollment, payment, forum, message and progress guards are unaffected: those
    are things a real person owns.
    """
    _ensure_course("now")

    tracks.remove_demo_courses(database)

    assert database.session.execute(database.select(Curso).filter_by(codigo="now")).scalars().first() is None


def test_a_payment_still_protects_a_course(db_session):
    """The guard that replaced the enrollment-only check still does its job."""
    from now_lms.db import Pago

    _ensure_course("details")
    _ensure_user("payer", "payer@example.invalid")
    database.session.add(
        Pago(
            curso="details",
            usuario="payer",
            estado="completed",
            monto=0,
            nombre="Payer",
            apellido="Person",
            correo_electronico="payer@example.invalid",
        )
    )
    database.session.commit()

    tracks.remove_demo_courses(database)

    survivor = database.session.execute(database.select(Curso).filter_by(codigo="details")).scalars().first()
    assert survivor is not None, "a course with a payment record must not be deleted"


def test_modification_time_is_deliberately_not_the_guard(db_session):
    """`modificado` looks like a stronger identity test than it is.

    An automated reviewer suggested refusing any row whose `modificado` is set. It is
    tempting — BaseTabla stamps it via `onupdate` on every write — but it is set by
    ANY update, including the platform's own: the seeder flips course visibility, and
    simply re-saving a row marks it. Using it would have made this cleanup refuse
    almost everything on a real database, i.e. a destructive routine that silently
    never runs, which is the exact defect this PR exists to fix.

    So identity stays content-based (seeded name, seeded opening sentence) and safety
    stays ownership-based (does anybody own a row hanging off it). This test pins the
    decision so nobody re-adds the check believing it is free.
    """
    from datetime import datetime

    curso = _ensure_course("details")
    curso.modificado = datetime.now()
    database.session.commit()

    tracks.remove_demo_courses(database)

    gone = database.session.execute(database.select(Curso).filter_by(codigo="details")).scalars().first()
    assert gone is None, "a touched-but-unmodified demo course is still demo content"
