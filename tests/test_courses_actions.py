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


from now_lms.auth import proteger_passwd
from now_lms.db import Curso, CursoSeccion, CursoRecurso, Usuario

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


def _crear_curso_minimo(db_session, code: str = "c_actions") -> Curso:
    curso = Curso(
        nombre="Curso Actions",
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


def _login_instructor(app) -> object:
    client = app.test_client()
    resp = client.post("/user/login", data={"usuario": "instr", "acceso": "instr"}, follow_redirects=False)
    assert resp.status_code in REDIRECT_STATUS_CODES | {200}
    return client


def test_incrementar_indice_seccion_redirect(app, db_session):
    _crear_instructor(db_session)
    curso = _crear_curso_minimo(db_session)
    client = _login_instructor(app)

    s = CursoSeccion(curso=curso.codigo, nombre="S1", descripcion="D", indice=1, estado=True)
    db_session.add(s)
    db_session.commit()

    r = client.get(f"/course/{curso.codigo}/seccion/increment/1", follow_redirects=False)
    assert r.status_code in REDIRECT_STATUS_CODES
    assert f"/course/{curso.codigo}/admin" in (r.headers.get("Location") or "")


def test_reducir_indice_seccion_redirect(app, db_session):
    _crear_instructor(db_session)
    curso = _crear_curso_minimo(db_session)
    client = _login_instructor(app)

    s = CursoSeccion(curso=curso.codigo, nombre="S2", descripcion="D", indice=2, estado=True)
    db_session.add(s)
    db_session.commit()

    r = client.get(f"/course/{curso.codigo}/seccion/decrement/2", follow_redirects=False)
    assert r.status_code in REDIRECT_STATUS_CODES
    assert f"/course/{curso.codigo}/admin" in (r.headers.get("Location") or "")


def test_modificar_orden_recurso_redirect(app, db_session):
    _crear_instructor(db_session)
    curso = _crear_curso_minimo(db_session)
    client = _login_instructor(app)

    s = CursoSeccion(curso=curso.codigo, nombre="S3", descripcion="D", indice=3, estado=True)
    db_session.add(s)
    db_session.commit()
    rsrc = CursoRecurso(curso=curso.codigo, seccion=s.id, nombre="R1", descripcion="D", tipo="text", indice=1, publico=True)
    db_session.add(rsrc)
    db_session.commit()

    r = client.get(f"/course/resource/{curso.codigo}/{s.id}/increment/1", follow_redirects=False)
    assert r.status_code in REDIRECT_STATUS_CODES
    assert f"/course/{curso.codigo}/admin" in (r.headers.get("Location") or "")


def test_eliminar_recurso_redirect(app, db_session):
    _crear_instructor(db_session)
    curso = _crear_curso_minimo(db_session)
    client = _login_instructor(app)

    s = CursoSeccion(curso=curso.codigo, nombre="S4", descripcion="D", indice=4, estado=True)
    db_session.add(s)
    db_session.commit()
    rsrc = CursoRecurso(curso=curso.codigo, seccion=s.id, nombre="R2", descripcion="D", tipo="text", indice=1, publico=True)
    db_session.add(rsrc)
    db_session.commit()

    r = client.get(f"/course/{curso.codigo}/delete_recurso/{s.id}/{rsrc.id}", follow_redirects=False)
    assert r.status_code in REDIRECT_STATUS_CODES
    assert f"/course/{curso.codigo}/admin" in (r.headers.get("Location") or "")


def test_eliminar_seccion_redirect(app, db_session):
    _crear_instructor(db_session)
    curso = _crear_curso_minimo(db_session)
    client = _login_instructor(app)

    s = CursoSeccion(curso=curso.codigo, nombre="S5", descripcion="D", indice=5, estado=True)
    db_session.add(s)
    db_session.commit()

    r = client.get(f"/course/{curso.codigo}/delete_seccion/{s.id}", follow_redirects=False)
    assert r.status_code in REDIRECT_STATUS_CODES
    assert f"/course/{curso.codigo}/admin" in (r.headers.get("Location") or "")


def test_cambiar_estatus_curso_redirect(app, db_session):
    _crear_instructor(db_session)
    curso = _crear_curso_minimo(db_session)
    client = _login_instructor(app)

    r = client.get(f"/course/change_curse_status?curse={curso.codigo}&status=open&usuario=instr", follow_redirects=False)
    assert r.status_code in REDIRECT_STATUS_CODES
    assert f"/course/{curso.codigo}/admin" in (r.headers.get("Location") or "")


def test_cambiar_curso_publico_redirect(app, db_session):
    _crear_instructor(db_session)
    curso = _crear_curso_minimo(db_session)
    client = _login_instructor(app)

    r = client.get(f"/course/change_curse_public?curse={curso.codigo}", follow_redirects=False)
    assert r.status_code in REDIRECT_STATUS_CODES
    assert f"/course/{curso.codigo}/admin" in (r.headers.get("Location") or "")


def test_cambiar_seccion_publico_redirect(app, db_session):
    _crear_instructor(db_session)
    curso = _crear_curso_minimo(db_session)
    client = _login_instructor(app)

    s = CursoSeccion(curso=curso.codigo, nombre="S6", descripcion="D", indice=6, estado=True)
    db_session.add(s)
    db_session.commit()

    r = client.get(f"/course/change_curse_seccion_public?codigo={s.id}&course_code={curso.codigo}", follow_redirects=False)
    assert r.status_code in REDIRECT_STATUS_CODES
    assert f"/course/{curso.codigo}/view" in (r.headers.get("Location") or "")


def test_cambiar_seccion_publico_toggle_estado(app, db_session):
    _crear_instructor(db_session)
    curso = _crear_curso_minimo(db_session)
    client = _login_instructor(app)

    # Sección inicialmente privada (estado False)
    s = CursoSeccion(curso=curso.codigo, nombre="S_toggle", descripcion="D", indice=1, estado=False)
    db_session.add(s)
    db_session.commit()

    # Primera llamada: debe cambiar a True
    r1 = client.get(f"/course/change_curse_seccion_public?codigo={s.id}&course_code={curso.codigo}", follow_redirects=False)
    assert r1.status_code in REDIRECT_STATUS_CODES
    s_refreshed = db_session.get(CursoSeccion, s.id)
    assert s_refreshed.estado is True

    # Segunda llamada: debe volver a False
    r2 = client.get(f"/course/change_curse_seccion_public?codigo={s.id}&course_code={curso.codigo}", follow_redirects=False)
    assert r2.status_code in REDIRECT_STATUS_CODES
    s_refreshed2 = db_session.get(CursoSeccion, s.id)
    assert s_refreshed2.estado is False


def test_eliminar_recurso_inexistente_no_op(app, db_session):
    _crear_instructor(db_session)
    curso = _crear_curso_minimo(db_session)
    client = _login_instructor(app)

    s = CursoSeccion(curso=curso.codigo, nombre="S7", descripcion="D", indice=1, estado=True)
    db_session.add(s)
    db_session.commit()
    rsrc = CursoRecurso(curso=curso.codigo, seccion=s.id, nombre="R3", descripcion="D", tipo="text", indice=1, publico=True)
    db_session.add(rsrc)
    db_session.commit()

    before = db_session.query(CursoRecurso).filter_by(seccion=s.id).count()
    r = client.get(f"/course/{curso.codigo}/delete_recurso/{s.id}/no-such-id", follow_redirects=False)
    after = db_session.query(CursoRecurso).filter_by(seccion=s.id).count()

    assert r.status_code in REDIRECT_STATUS_CODES
    assert before == after == 1


def test_eliminar_seccion_inexistente_no_op(app, db_session):
    _crear_instructor(db_session)
    curso = _crear_curso_minimo(db_session)
    client = _login_instructor(app)

    s = CursoSeccion(curso=curso.codigo, nombre="S8", descripcion="D", indice=1, estado=True)
    db_session.add(s)
    db_session.commit()

    before = db_session.query(CursoSeccion).filter_by(curso=curso.codigo).count()
    r = client.get(f"/course/{curso.codigo}/delete_seccion/no-such-id", follow_redirects=False)
    after = db_session.query(CursoSeccion).filter_by(curso=curso.codigo).count()

    assert r.status_code in REDIRECT_STATUS_CODES
    assert before == after == 1


def test_modificar_orden_recurso_inexistente_no_change(app, db_session):
    _crear_instructor(db_session)
    curso = _crear_curso_minimo(db_session)
    client = _login_instructor(app)

    s = CursoSeccion(curso=curso.codigo, nombre="S9", descripcion="D", indice=1, estado=True)
    db_session.add(s)
    db_session.commit()

    r1 = CursoRecurso(curso=curso.codigo, seccion=s.id, nombre="R1", descripcion="D", tipo="text", indice=1, publico=True)
    r2 = CursoRecurso(curso=curso.codigo, seccion=s.id, nombre="R2", descripcion="D", tipo="text", indice=2, publico=True)
    db_session.add_all([r1, r2])
    db_session.commit()

    r = client.get(f"/course/resource/{curso.codigo}/{s.id}/increment/5", follow_redirects=False)
    assert r.status_code in REDIRECT_STATUS_CODES

    indices = [x.indice for x in db_session.query(CursoRecurso).filter_by(seccion=s.id).order_by(CursoRecurso.indice).all()]
    assert indices == [1, 2]


def test_cambiar_estatus_curso_inexistente_redirect_no_change(app, db_session):
    _crear_instructor(db_session)
    client = _login_instructor(app)

    # Asegurar inexistente
    assert db_session.query(Curso).filter_by(codigo="nope").count() == 0
    r = client.get("/course/change_curse_status?curse=nope&status=open&usuario=instr", follow_redirects=False)
    assert r.status_code in REDIRECT_STATUS_CODES
    assert db_session.query(Curso).filter_by(codigo="nope").count() == 0


def test_cambiar_curso_publico_inexistente_redirect_no_change(app, db_session):
    _crear_instructor(db_session)
    client = _login_instructor(app)

    assert db_session.query(Curso).filter_by(codigo="nope").count() == 0
    r = client.get("/course/change_curse_public?curse=nope", follow_redirects=False)
    assert r.status_code in REDIRECT_STATUS_CODES
    assert db_session.query(Curso).filter_by(codigo="nope").count() == 0
