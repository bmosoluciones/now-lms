# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""
Tests for course promotion date (fecha_promocionado) tracking.

Regression test for a bug where editing a course to set promocionado=True
wrote datetime.today() to the promocionado Boolean column instead of the
fecha_promocionado DateTime column, so the promotion timestamp was never
recorded.
"""

from datetime import date

import pytest

from now_lms.auth import proteger_passwd
from now_lms.db import Configuracion, Curso, MailConfig, Style, Usuario, database

REDIRECT_STATUS_CODES = {301, 302, 303, 307, 308}


def _crear_instructor(db_session) -> Usuario:
    user = Usuario(
        usuario="promo_instr",
        acceso=proteger_passwd("pass"),
        nombre="Instructor",
        correo_electronico="promo_instr@example.com",
        tipo="instructor",
        activo=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


def _login_instructor(app):
    client = app.test_client()
    resp = client.post(
        "/user/login",
        data={"usuario": "promo_instr", "acceso": "pass"},
        follow_redirects=False,
    )
    assert resp.status_code in REDIRECT_STATUS_CODES | {200}
    return client


def _crear_config(db_session):
    if not db_session.execute(database.select(Configuracion)).first():
        db_session.add(Configuracion(titulo="Test", lang="es"))
    if not db_session.execute(database.select(MailConfig)).first():
        db_session.add(MailConfig())
    if not db_session.execute(database.select(Style)).first():
        db_session.add(Style())
    db_session.commit()


def _crear_curso(db_session, codigo="promo_test", promocionado=False) -> Curso:
    curso = Curso(
        nombre="Curso Promocion Test",
        codigo=codigo,
        descripcion_corta="Corta",
        descripcion="Descripcion completa del curso de prueba",
        nivel=0,
        duracion=1,
        publico=True,
        modalidad="self_paced",
        foro_habilitado=False,
        limitado=False,
        capacidad=0,
        pagado=False,
        auditable=False,
        certificado=False,
        precio=0,
        estado="open",
        promocionado=promocionado,
        fecha_promocionado=None,
    )
    db_session.add(curso)
    db_session.commit()
    return curso


def test_fecha_promocionado_set_when_promoting(app, db_session):
    """When a course is promoted (False -> True), fecha_promocionado must be set."""
    _crear_config(db_session)
    _crear_instructor(db_session)
    client = _login_instructor(app)

    curso = _crear_curso(db_session, codigo="promo1", promocionado=False)
    assert curso.fecha_promocionado is None

    resp = client.post(
        "/course/promo1/edit",
        data={
            "nombre": "Curso Promocion Test",
            "descripcion": "Descripcion completa del curso de prueba",
            "codigo": "promo1",
            "descripcion_corta": "Corta",
            "nivel": "0",
            "duracion": "1",
            "publico": "y",
            "modalidad": "self_paced",
            "foro_habilitado": "",
            "limitado": "",
            "capacidad": "0",
            "pagado": "",
            "auditable": "",
            "certificado": "",
            "precio": "0",
            "promocionado": "y",
        },
        follow_redirects=False,
    )
    assert resp.status_code in REDIRECT_STATUS_CODES | {200}

    curso_editado = db_session.execute(
        database.select(Curso).filter_by(codigo="promo1")
    ).scalars().first()
    assert curso_editado is not None
    assert curso_editado.promocionado is True
    assert curso_editado.fecha_promocionado is not None, (
        "fecha_promocionado must be set when course is promoted from False to True"
    )


def test_fecha_promocionado_not_overwritten_when_already_promoted(app, db_session):
    """If the course is already promoted, editing should not change fecha_promocionado."""
    _crear_config(db_session)
    _crear_instructor(db_session)
    client = _login_instructor(app)

    from datetime import datetime

    existing_date = datetime(2025, 1, 15, 10, 30, 0)
    curso = _crear_curso(db_session, codigo="promo2", promocionado=True)
    curso.fecha_promocionado = existing_date
    db_session.commit()

    resp = client.post(
        "/course/promo2/edit",
        data={
            "nombre": "Curso Promocion Test",
            "descripcion": "Descripcion completa del curso de prueba",
            "codigo": "promo2",
            "descripcion_corta": "Corta",
            "nivel": "0",
            "duracion": "1",
            "publico": "y",
            "modalidad": "self_paced",
            "foro_habilitado": "",
            "limitado": "",
            "capacidad": "0",
            "pagado": "",
            "auditable": "",
            "certificado": "",
            "precio": "0",
            "promocionado": "y",
        },
        follow_redirects=False,
    )
    assert resp.status_code in REDIRECT_STATUS_CODES | {200}

    curso_editado = db_session.execute(
        database.select(Curso).filter_by(codigo="promo2")
    ).scalars().first()
    assert curso_editado is not None
    assert curso_editado.promocionado is True
    assert curso_editado.fecha_promocionado == existing_date, (
        "fecha_promocionado should not change when course is already promoted"
    )


def test_promocionado_set_to_boolean_not_datetime(app, db_session):
    """The promocionado column must remain a boolean, never receive a datetime value."""
    _crear_config(db_session)
    _crear_instructor(db_session)
    client = _login_instructor(app)

    curso = _crear_curso(db_session, codigo="promo3", promocionado=False)

    resp = client.post(
        "/course/promo3/edit",
        data={
            "nombre": "Curso Promocion Test",
            "descripcion": "Descripcion completa del curso de prueba",
            "codigo": "promo3",
            "descripcion_corta": "Corta",
            "nivel": "0",
            "duracion": "1",
            "publico": "y",
            "modalidad": "self_paced",
            "foro_habilitado": "",
            "limitado": "",
            "capacidad": "0",
            "pagado": "",
            "auditable": "",
            "certificado": "",
            "precio": "0",
            "promocionado": "y",
        },
        follow_redirects=False,
    )
    assert resp.status_code in REDIRECT_STATUS_CODES | {200}

    curso_editado = db_session.execute(
        database.select(Curso).filter_by(codigo="promo3")
    ).scalars().first()
    assert curso_editado is not None
    assert curso_editado.promocionado is True
    assert isinstance(curso_editado.promocionado, bool), (
        "promocionado must be a boolean, not a datetime or other type"
    )
