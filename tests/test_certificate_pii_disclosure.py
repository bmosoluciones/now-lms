# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""
Regression tests for personal-data disclosure on the public certificate routes.

Certificate bodies are admin-authored Jinja stored in the database
(`Certificado.html`) and rendered by five routes that require no authentication.
Those routes used to inject the full `Usuario` ORM row into the template context, so
any customised template could read `correo_electronico`, `nacimiento`, `bio` and
`tipo` - none of which belongs on a certificate - and serve them to anyone holding
the certification ULID.

The context now carries `CertificateHolder`, which exposes only `id`, `nombre` and
`apellido`. These tests render a deliberately hostile template that asks for every
personal field, and assert the sensitive values never reach the response while the
legitimate ones still do.

Reverting `CertificateHolder(usuario)` back to `usuario` at any of the five context
sites must fail at least one test here.
"""

import datetime

from now_lms.auth import proteger_passwd
from now_lms.db import Certificacion, Certificado, Curso, Usuario

# A template that asks for everything a hostile or careless admin might reference.
HOSTILE_TEMPLATE = """
<h1>{{ usuario.nombre }} {{ usuario.apellido }}</h1>
<p id="email">{{ usuario.correo_electronico }}</p>
<p id="dob">{{ usuario.nacimiento }}</p>
<p id="bio">{{ usuario.bio }}</p>
<p id="tipo">{{ usuario.tipo }}</p>
"""

LEAKED_EMAIL = "titular.privado@example.com"
LEAKED_BIO = "biografia-secreta-del-titular"


def _build(db_session):
    """Create an admin, a certificate holder, a course, a template and a certification."""
    admin = Usuario(
        usuario="cert_admin",
        acceso=proteger_passwd("cert_admin"),
        nombre="Admin",
        apellido="Root",
        correo_electronico="cert_admin@example.com",
        tipo="admin",
        activo=True,
    )
    titular = Usuario(
        usuario="cert_titular",
        acceso=proteger_passwd("cert_titular"),
        nombre="Ada",
        apellido="Lovelace",
        correo_electronico=LEAKED_EMAIL,
        nacimiento=datetime.date(1815, 12, 10),
        bio=LEAKED_BIO,
        tipo="student",
        activo=True,
    )
    db_session.add_all([admin, titular])
    db_session.commit()

    curso = Curso(
        codigo="C_PII",
        nombre="Curso PII",
        descripcion_corta="desc",
        descripcion="desc",
        estado="open",
        certificado=True,
    )
    db_session.add(curso)
    db_session.commit()

    plantilla = Certificado(
        code="TEMP_PII",
        titulo="Plantilla hostil",
        descripcion="desc",
        html=HOSTILE_TEMPLATE,
        css="",
        tipo="course",
        habilitado=True,
        publico=True,
        usuario=admin.usuario,
    )
    db_session.add(plantilla)
    db_session.commit()

    cert = Certificacion(usuario=titular.usuario, curso=curso.codigo, certificado=plantilla.code)
    db_session.add(cert)
    db_session.commit()
    return cert


def test_certificate_view_does_not_disclose_personal_fields(app, db_session):
    """The headline defect: an unauthenticated render must not carry PII."""
    cert = _build(db_session)

    with app.test_client() as client:
        resp = client.get(f"/certificate/certificate/{cert.id}/")

    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert LEAKED_EMAIL not in body
    assert LEAKED_BIO not in body
    assert "1815-12-10" not in body


def test_certificate_view_still_prints_the_holder_name(app, db_session):
    """Control case: narrowing the context must not break real certificates."""
    cert = _build(db_session)

    with app.test_client() as client:
        resp = client.get(f"/certificate/certificate/{cert.id}/")

    body = resp.get_data(as_text=True)
    assert "Ada" in body
    assert "Lovelace" in body


def test_public_certificate_route_does_not_disclose_personal_fields(app, db_session):
    """`/certificate/view/<ulid>` is the second unauthenticated HTML route."""
    cert = _build(db_session)

    with app.test_client() as client:
        resp = client.get(f"/certificate/view/{cert.id}")

    body = resp.get_data(as_text=True)
    assert LEAKED_EMAIL not in body
    assert LEAKED_BIO not in body


def test_certificate_holder_exposes_only_the_allowed_attributes(app, db_session):
    """Guard the allowlist itself, so widening it is a deliberate act.

    `__slots__` also means an accidental assignment of a personal field raises
    rather than silently attaching it.
    """
    from now_lms.vistas.certificates import CertificateHolder

    titular = Usuario(
        usuario="solo_lectura",
        acceso=proteger_passwd("solo_lectura"),
        nombre="Grace",
        apellido="Hopper",
        correo_electronico="grace@example.com",
        bio="secreta",
        tipo="student",
        activo=True,
    )
    db_session.add(titular)
    db_session.commit()

    holder = CertificateHolder(titular)

    assert holder.nombre == "Grace"
    assert holder.apellido == "Hopper"
    assert set(CertificateHolder.__slots__) == {"id", "nombre", "apellido"}
    assert not hasattr(holder, "correo_electronico")
    assert not hasattr(holder, "bio")
    assert not hasattr(holder, "tipo")
    assert not hasattr(holder, "acceso")
