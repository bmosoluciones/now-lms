# Copyright 2025 BMO Soluciones, S.A.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime


from now_lms.auth import proteger_passwd
from now_lms.db import (
    Curso,
    CursoRecurso,
    CursoRecursoAvance,
    CursoSeccion,
    CursoUsuarioAvance,
    EstudianteCurso,
    Pago,
    Usuario,
)

REDIRECT_STATUS_CODES = {301, 302, 303, 307, 308}


def _crear_instructor(db_session) -> Usuario:
    user = Usuario(
        usuario="instr",
        acceso=proteger_passwd("instr"),
        nombre="Instructor",
        correo_electronico="instr@example.com",
        tipo="instructor",
        activo=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


def _crear_estudiante(db_session) -> Usuario:
    user = Usuario(
        usuario="alumno",
        acceso=proteger_passwd("alumno"),
        nombre="Alumno",
        correo_electronico="alumno@example.com",
        tipo="student",
        activo=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


def _crear_curso(db_session, code: str = "c_resources") -> Curso:
    curso = Curso(
        nombre="Curso Recursos",
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


def _login(client, username: str, password: str) -> None:
    resp = client.post("/user/login", data={"usuario": username, "acceso": password}, follow_redirects=False)
    assert resp.status_code in REDIRECT_STATUS_CODES | {200}


def _inscribir_estudiante(db_session, curso: Curso, estudiante: Usuario) -> None:
    pago = Pago(
        usuario=estudiante.usuario,
        curso=curso.codigo,
        moneda="USD",
        monto=0,
        estado="completed",
        metodo="paypal",
        referencia="test-ref",
        descripcion="test pago",
        audit=True,
        nombre="Alumno",
        apellido="Ejemplo",
        correo_electronico=estudiante.correo_electronico,
    )
    db_session.add(pago)
    db_session.commit()

    enrolment = EstudianteCurso(curso=curso.codigo, usuario=estudiante.usuario, vigente=True, pago=pago.id)
    db_session.add(enrolment)
    db_session.commit()


def _crear_seccion(db_session, curso: Curso, indice: int = 1) -> CursoSeccion:
    seccion = CursoSeccion(curso=curso.codigo, nombre="S1", descripcion="D", indice=indice, estado=True)
    db_session.add(seccion)
    db_session.commit()
    return seccion


def _crear_recurso_meet(db_session, curso: Curso, seccion: CursoSeccion) -> CursoRecurso:
    recurso = CursoRecurso(
        curso=curso.codigo,
        seccion=seccion.id,
        tipo="meet",
        nombre="Sesion sincrona",
        descripcion="Detalles de la sesion",
        requerido="required",
        indice=1,
        publico=True,
        url="https://example.com/meet",
        fecha=datetime.date(2024, 1, 1),
        hora_inicio=datetime.time(10, 0, 0),
        hora_fin=datetime.time(11, 0, 0),
        notes="Sala virtual",
    )
    db_session.add(recurso)
    db_session.commit()
    return recurso


def _crear_recurso_texto(db_session, curso: Curso, seccion: CursoSeccion) -> CursoRecurso:
    recurso = CursoRecurso(
        curso=curso.codigo,
        seccion=seccion.id,
        tipo="text",
        nombre="Texto",
        descripcion="Contenido",
        requerido="required",
        indice=1,
        publico=True,
        text="Contenido del recurso",
    )
    db_session.add(recurso)
    db_session.commit()
    return recurso


def test_marcar_recurso_completado_crea_avance(app, db_session):
    _crear_instructor(db_session)
    estudiante = _crear_estudiante(db_session)
    curso = _crear_curso(db_session)
    seccion = _crear_seccion(db_session, curso)
    recurso = _crear_recurso_texto(db_session, curso, seccion)
    _inscribir_estudiante(db_session, curso, estudiante)

    client = app.test_client()
    _login(client, estudiante.usuario, "alumno")

    resp = client.get(
        f"/course/{curso.codigo}/resource/{recurso.tipo}/{recurso.id}/complete",
        follow_redirects=False,
    )

    assert resp.status_code in REDIRECT_STATUS_CODES | {200}
    avance = (
        db_session.query(CursoRecursoAvance)
        .filter_by(curso=curso.codigo, recurso=recurso.id, usuario=estudiante.usuario)
        .one()
    )
    assert avance.completado is True

    progreso = db_session.query(CursoUsuarioAvance).filter_by(curso=curso.codigo, usuario=estudiante.usuario).first()
    assert progreso is not None
    assert progreso.recursos_requeridos == 1


def test_descargar_calendario_meet_generado(app, db_session):
    _crear_instructor(db_session)
    curso = _crear_curso(db_session, code="c_meet")
    seccion = _crear_seccion(db_session, curso)
    recurso = _crear_recurso_meet(db_session, curso, seccion)

    client = app.test_client()
    _login(client, "instr", "instr")

    resp = client.get(f"/course/{curso.codigo}/resource/meet/{recurso.id}/calendar.ics")

    assert resp.status_code == 200
    assert resp.mimetype == "text/calendar"
    body = resp.data.decode("utf-8")
    assert "BEGIN:VCALENDAR" in body
    assert f"SUMMARY:{recurso.nombre}" in body
    assert "DTSTART:" in body and "DTEND:" in body


def test_google_calendar_link_redirecciona(app, db_session):
    _crear_instructor(db_session)
    curso = _crear_curso(db_session, code="c_google")
    seccion = _crear_seccion(db_session, curso)
    recurso = _crear_recurso_meet(db_session, curso, seccion)

    client = app.test_client()
    _login(client, "instr", "instr")

    resp = client.get(f"/course/{curso.codigo}/resource/meet/{recurso.id}/google-calendar", follow_redirects=False)

    assert resp.status_code in REDIRECT_STATUS_CODES
    location = resp.headers.get("Location") or ""
    assert "calendar.google.com" in location
    assert "action=TEMPLATE" in location
