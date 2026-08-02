# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.

"""A signed-in member may preview any open course; anonymity stays gated.

Fork issue #52 found ``/course/<code>/view`` returning 403 for a signed-in,
non-enrolled member while ``/course/<code>/take`` rendered its full (locked)
outline to that same member — the deeper page was more permissive than the
summary page, and members had no way to discover the courses they are invited
to enroll in. Ruling (2026-08-02): the preview opens to authenticated members
for OPEN courses; ``publico`` keeps governing the anonymous world; drafts stay
hidden from everyone but their staff.
"""

from now_lms.auth import proteger_passwd
from now_lms.db import Curso, Usuario, database

PASSWORD = "preview-walk-pw"
REDIRECTS = {301, 302, 303, 307, 308}


def _make_course(app, code, *, estado="open", publico=False):
    with app.app_context():
        database.session.add(
            Curso(
                nombre=f"Course {code}",
                codigo=code,
                descripcion="Preview access test course.",
                descripcion_corta="Preview test.",
                estado=estado,
                publico=publico,
                pagado=False,
                precio=0,
                certificado=False,
                modalidad="self_paced",
                creado_por="test",
            )
        )
        database.session.commit()


def _student_client(app, username):
    with app.app_context():
        database.session.add(
            Usuario(
                usuario=username,
                acceso=proteger_passwd(PASSWORD),
                nombre="Preview",
                apellido="Walker",
                correo_electronico=username,
                tipo="student",
                activo=True,
                correo_electronico_verificado=True,
                creado_por="test",
            )
        )
        database.session.commit()
    client = app.test_client()
    resp = client.post("/user/login", data={"usuario": username, "acceso": PASSWORD}, follow_redirects=False)
    assert resp.status_code in REDIRECTS | {200}
    return client


def test_member_can_preview_open_gated_course(app, db_session):
    """Signed-in, NOT enrolled, course open but publico=False: 200, not 403."""
    _make_course(app, "prevw1", estado="open", publico=False)
    client = _student_client(app, "preview-walker@example.com")
    resp = client.get("/course/prevw1/view")
    assert resp.status_code == 200, (
        "a signed-in member must be able to preview an open course — "
        "the take page already shows them its locked outline"
    )


def test_anonymous_still_lands_on_the_intake(app, db_session):
    """Anonymous + gated course: still a redirect to request-access, not 200."""
    _make_course(app, "prevw2", estado="open", publico=False)
    client = app.test_client()
    resp = client.get("/course/prevw2/view", follow_redirects=False)
    assert resp.status_code in REDIRECTS
    assert "request-access" in (resp.headers.get("Location") or "")


def test_member_cannot_preview_a_draft_course(app, db_session):
    """estado != open stays hidden from members: drafts are staff-only."""
    _make_course(app, "prevw3", estado="draft", publico=False)
    client = _student_client(app, "draft-walker@example.com")
    resp = client.get("/course/prevw3/view")
    assert resp.status_code == 403
