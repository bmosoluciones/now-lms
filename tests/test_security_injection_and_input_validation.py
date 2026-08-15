# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.

"""Regression tests for the injection / input-validation security fixes.

Each test pins one upstream security fix that this fork already carries. The
fixes themselves are one-liners that a refactor can silently undo, and upstream
shipped none of them with a test, so the guarantees were unenforced here:

* ``2ff37af`` — error-page template whitelist (SSTI, upstream issue #186)
* ``5e57454`` — numeric validation of course-action URL parameters (issue #197)
* ``5c348f7`` — POST-only endpoints must not read query parameters (S8370)
* ``601621a`` — no WTForms validation bypass in user creation (issue #188)
"""

from now_lms.auth import proteger_passwd
from now_lms.db import (
    Curso,
    CursoRecurso,
    CursoSeccion,
    Usuario,
    UsuarioGrupo,
    UsuarioGrupoMiembro,
    database,
)

REDIRECT_STATUS_CODES = {301, 302, 303, 307, 308}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _crear_instructor(db_session, usuario: str = "sec_instr") -> Usuario:
    """Create an active instructor account."""
    user = Usuario(
        usuario=usuario,
        acceso=proteger_passwd("instrpass"),
        nombre="Security Instructor",
        apellido="Tester",
        correo_electronico=f"{usuario}@example.com",
        tipo="instructor",
        activo=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


def _crear_admin(db_session, usuario: str = "sec_admin") -> Usuario:
    """Create an active admin account."""
    user = Usuario(
        usuario=usuario,
        acceso=proteger_passwd("adminpass"),
        nombre="Security Admin",
        apellido="Tester",
        correo_electronico=f"{usuario}@example.com",
        tipo="admin",
        activo=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


def _crear_curso(db_session, code: str = "sec_actions") -> Curso:
    """Create a minimal open course."""
    curso = Curso(
        nombre="Curso Seguridad",
        codigo=code,
        descripcion_corta="Desc corta",
        descripcion="Desc",
        estado="open",
        publico=True,
        modalidad="self_paced",
        foro_habilitado=False,
    )
    db_session.add(curso)
    db_session.commit()
    return curso


def _login(app, usuario: str, acceso: str):
    """Return a test client logged in through the real login form."""
    client = app.test_client()
    resp = client.post("/user/login", data={"usuario": usuario, "acceso": acceso}, follow_redirects=False)
    assert resp.status_code in REDIRECT_STATUS_CODES | {200}
    return client


def _login_session(client, app, user_id: str):
    """Log a client in by seeding the session (for accounts without a password flow)."""
    with app.test_request_context():
        with client.session_transaction() as sess:
            sess["_user_id"] = user_id
            sess["_fresh"] = True
    return client


# ---------------------------------------------------------------------------
# 2ff37af — server-side template injection in the error-page route
# ---------------------------------------------------------------------------


def test_error_page_renders_whitelisted_codes(client):
    """The four whitelisted HTTP error codes still render."""
    for code in ("403", "404", "405", "500"):
        resp = client.get(f"/http/error/{code}")
        assert resp.status_code == 200, f"error page {code} should render"


def test_error_page_refuses_arbitrary_template_name(client):
    """A non-error template under error_pages/ must not be reachable.

    ``error_pages/verify_mail.html`` really exists in the tree, so without the
    whitelist an unauthenticated caller picks which template the server renders
    just by naming it in the URL.
    """
    resp = client.get("/http/error/verify_mail")
    assert resp.status_code == 404


def test_error_page_refuses_unknown_and_traversal_codes(client):
    """Unknown codes and traversal payloads are refused, never 500."""
    for code in ("999", "401", "..%2f..%2fbase", "%2e%2e%2fbase"):
        resp = client.get(f"/http/error/{code}")
        assert resp.status_code == 404, f"code {code!r} should be rejected"


# ---------------------------------------------------------------------------
# 5e57454 — unvalidated int() conversion of course-action URL parameters
# ---------------------------------------------------------------------------


def test_section_index_routes_reject_non_numeric_index(app, db_session):
    """Non-numeric section indexes redirect instead of raising ValueError."""
    _crear_instructor(db_session)
    curso = _crear_curso(db_session)
    seccion = CursoSeccion(curso=curso.codigo, nombre="S1", descripcion="D", indice=1, estado=True)
    db_session.add(seccion)
    db_session.commit()
    seccion_id = seccion.id

    client = _login(app, "sec_instr", "instrpass")

    for action in ("increment", "decrement"):
        resp = client.get(f"/course/{curso.codigo}/seccion/{action}/abc", follow_redirects=False)
        assert resp.status_code in REDIRECT_STATUS_CODES
        assert f"/course/{curso.codigo}/admin" in (resp.headers.get("Location") or "")

    db_session.expire_all()
    assert db_session.get(CursoSeccion, seccion_id).indice == 1


def test_resource_order_route_rejects_non_numeric_index(app, db_session):
    """Non-numeric resource indexes redirect instead of raising ValueError."""
    _crear_instructor(db_session)
    curso = _crear_curso(db_session)
    seccion = CursoSeccion(curso=curso.codigo, nombre="S1", descripcion="D", indice=1, estado=True)
    db_session.add(seccion)
    db_session.commit()

    recurso = CursoRecurso(
        curso=curso.codigo,
        seccion=seccion.id,
        nombre="R1",
        descripcion="D",
        tipo="text",
        indice=1,
        publico=True,
    )
    db_session.add(recurso)
    db_session.commit()
    recurso_id = recurso.id

    client = _login(app, "sec_instr", "instrpass")

    resp = client.get(
        f"/course/resource/{curso.codigo}/{seccion.id}/increment/not-a-number",
        follow_redirects=False,
    )
    assert resp.status_code in REDIRECT_STATUS_CODES
    assert f"/course/{curso.codigo}/admin" in (resp.headers.get("Location") or "")

    db_session.expire_all()
    assert db_session.get(CursoRecurso, recurso_id).indice == 1


# ---------------------------------------------------------------------------
# 5c348f7 — POST endpoint must ignore query parameters (S8370)
# ---------------------------------------------------------------------------


def test_group_add_uses_the_form_supplied_group(app, client, db_session):
    """The normal path still works: the group named in the form body is used."""
    instructor = _crear_instructor(db_session)
    destino = UsuarioGrupo(nombre="Grupo Destino", descripcion="Destino", creado_por=instructor.usuario)
    db_session.add(destino)
    db_session.commit()
    destino_id = destino.id

    _login_session(client, app, instructor.id)

    resp = client.post(
        "/group/add",
        data={"usuario": instructor.usuario, "id": destino_id},
        follow_redirects=False,
    )
    assert resp.status_code in REDIRECT_STATUS_CODES | {200}

    miembro = db_session.execute(
        database.select(UsuarioGrupoMiembro).filter_by(grupo=destino_id, usuario=instructor.usuario)
    ).scalar_one_or_none()
    assert miembro is not None


def test_group_add_ignores_query_string_id(app, client, db_session):
    """/group/add must not fall back to the query string for the target group.

    The request carries no usable group in the body, so the only group named
    anywhere is the one in the query string. A membership must not be written
    into it — reading mutation input from the URL of a POST is the S8370 defect.
    """
    instructor = _crear_instructor(db_session)
    victima = UsuarioGrupo(nombre="Grupo Privilegiado", descripcion="No tocar", creado_por=instructor.usuario)
    db_session.add(victima)
    db_session.commit()
    victima_id = victima.id

    _login_session(client, app, instructor.id)

    try:
        client.post(
            f"/group/add?id={victima_id}",
            data={"usuario": instructor.usuario, "id": ""},
            follow_redirects=False,
        )
    except Exception:  # noqa: BLE001 - a hard failure is acceptable; a silent write is not
        pass

    db_session.rollback()
    en_victima = db_session.execute(
        database.select(UsuarioGrupoMiembro).filter_by(grupo=victima_id, usuario=instructor.usuario)
    ).scalar_one_or_none()
    assert en_victima is None, "the query-string group must never be used as the mutation target"


# ---------------------------------------------------------------------------
# 601621a — WTForms validation bypass in the user creation endpoints
# ---------------------------------------------------------------------------


def test_crear_cuenta_rejects_invalid_form(client, db_session):
    """Self-service registration with an empty password creates no account."""
    resp = client.post(
        "/user/logon",
        data={
            "usuario": "",
            "acceso": "",
            "nombre": "Attacker",
            "apellido": "",
            "correo_electronico": "bypass_logon@example.com",
        },
        follow_redirects=False,
    )
    db_session.rollback()
    creado = db_session.execute(
        database.select(Usuario).filter_by(correo_electronico="bypass_logon@example.com")
    ).scalar_one_or_none()
    assert creado is None, "invalid registration must not create an account"
    assert resp.status_code not in REDIRECT_STATUS_CODES, "the form should be re-rendered, not treated as a success"


def test_crear_usuario_rejects_invalid_form(app, client, db_session):
    """Admin-side user creation with invalid data creates no account."""
    admin = _crear_admin(db_session)
    _login_session(client, app, admin.id)

    resp = client.post(
        "/user/new_user",
        data={
            "usuario": "bypass_admin",
            "acceso": "",
            "nombre": "",
            "apellido": "",
            "correo_electronico": "bypass_admin@example.com",
        },
        follow_redirects=False,
    )
    db_session.rollback()
    creado = db_session.execute(database.select(Usuario).filter_by(usuario="bypass_admin")).scalar_one_or_none()
    assert creado is None, "invalid admin user creation must not create an account"
    assert resp.status_code not in REDIRECT_STATUS_CODES, "the form should be re-rendered, not treated as a success"
