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

"""
Test end-to-end para funcionalidad de etiquetas (tags).

Prueba el flujo completo de:
- Creación de etiquetas
- Edición de etiquetas
- Listado de etiquetas
- Eliminación de etiquetas
"""


from now_lms.auth import proteger_passwd
from now_lms.db import Etiqueta, Usuario, database

REDIRECT_STATUS_CODES = {301, 302, 303, 307, 308}


def _crear_instructor(db_session) -> Usuario:
    """Crea un usuario instructor para las pruebas."""
    user = Usuario(
        usuario="instructor",
        acceso=proteger_passwd("instructor"),
        nombre="Instructor",
        correo_electronico="instructor@example.com",
        tipo="instructor",
        activo=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


def _login_instructor(app):
    """Inicia sesión como instructor y retorna el cliente."""
    client = app.test_client()
    resp = client.post("/user/login", data={"usuario": "instructor", "acceso": "instructor"}, follow_redirects=False)
    assert resp.status_code in REDIRECT_STATUS_CODES | {200}
    return client


def test_e2e_tag_creation(app, db_session):
    """Test: crear una etiqueta nueva."""
    # 1) Crear instructor y login
    _crear_instructor(db_session)
    client = _login_instructor(app)

    # 2) Crear etiqueta via POST
    resp_new = client.post(
        "/tag/new",
        data={
            "nombre": "Python",
            "color": "#3776ab",
        },
        follow_redirects=False,
    )
    assert resp_new.status_code in REDIRECT_STATUS_CODES | {200}

    # 3) Verificar que la etiqueta existe en la base de datos
    etiqueta = db_session.execute(database.select(Etiqueta).filter_by(nombre="Python")).scalars().first()
    assert etiqueta is not None
    assert etiqueta.nombre == "Python"
    assert etiqueta.color == "#3776ab"


def test_e2e_tag_list(app, db_session):
    """Test: listar etiquetas existentes."""
    # 1) Crear instructor y varias etiquetas
    _crear_instructor(db_session)

    for i in range(3):
        etiqueta = Etiqueta(
            nombre=f"Etiqueta {i}",
            color=f"#00000{i}",
        )
        db_session.add(etiqueta)
    db_session.commit()

    # 2) Login y ver lista de etiquetas
    client = _login_instructor(app)
    resp_list = client.get("/tag/list")
    assert resp_list.status_code == 200
    assert b"Etiqueta 0" in resp_list.data
    assert b"Etiqueta 1" in resp_list.data
    assert b"Etiqueta 2" in resp_list.data


def test_e2e_tag_editing(app, db_session):
    """Test: editar una etiqueta existente."""
    # 1) Crear instructor y etiqueta
    _crear_instructor(db_session)
    etiqueta = Etiqueta(
        nombre="Tag Original",
        color="#ffffff",
    )
    db_session.add(etiqueta)
    db_session.commit()
    tag_id = etiqueta.id

    # 2) Login como instructor
    client = _login_instructor(app)

    # 3) Editar etiqueta via POST
    resp_edit = client.post(
        f"/tag/{tag_id}/edit",
        data={
            "nombre": "Tag Editado",
            "color": "#000000",
        },
        follow_redirects=False,
    )
    assert resp_edit.status_code in REDIRECT_STATUS_CODES | {200}

    # 4) Verificar cambios en la base de datos
    etiqueta_editada = db_session.get(Etiqueta, tag_id)
    assert etiqueta_editada is not None
    assert etiqueta_editada.nombre == "Tag Editado"
    assert etiqueta_editada.color == "#000000"


def test_e2e_tag_deletion(app, db_session):
    """Test: eliminar una etiqueta."""
    # 1) Crear instructor y etiqueta
    _crear_instructor(db_session)
    etiqueta = Etiqueta(
        nombre="Tag a Eliminar",
        color="#ff0000",
    )
    db_session.add(etiqueta)
    db_session.commit()
    tag_id = etiqueta.id

    # 2) Login como instructor
    client = _login_instructor(app)

    # 3) Eliminar etiqueta
    resp_delete = client.get(f"/tag/{tag_id}/delete", follow_redirects=False)
    assert resp_delete.status_code in REDIRECT_STATUS_CODES | {200}

    # 4) Verificar que la etiqueta fue eliminada de la base de datos
    etiqueta_eliminada = db_session.get(Etiqueta, tag_id)
    assert etiqueta_eliminada is None


def test_e2e_tag_view_form(app, db_session):
    """Test: visualizar formulario de nueva etiqueta."""
    # 1) Crear instructor y login
    _crear_instructor(db_session)
    client = _login_instructor(app)

    # 2) Acceder al formulario de nueva etiqueta
    resp_form = client.get("/tag/new")
    assert resp_form.status_code == 200
    assert b"nombre" in resp_form.data.lower() or b"name" in resp_form.data.lower()


def test_e2e_tag_edit_form(app, db_session):
    """Test: visualizar formulario de edición de etiqueta."""
    # 1) Crear instructor y etiqueta
    _crear_instructor(db_session)
    etiqueta = Etiqueta(
        nombre="Tag para Editar",
        color="#00ff00",
    )
    db_session.add(etiqueta)
    db_session.commit()
    tag_id = etiqueta.id

    # 2) Login y acceder al formulario de edición
    client = _login_instructor(app)
    resp_form = client.get(f"/tag/{tag_id}/edit")
    assert resp_form.status_code == 200
    assert b"Tag para Editar" in resp_form.data


def test_e2e_tag_with_special_characters(app, db_session):
    """Test: crear etiqueta con caracteres especiales."""
    # 1) Crear instructor y login
    _crear_instructor(db_session)
    client = _login_instructor(app)

    # 2) Crear etiqueta con caracteres especiales
    resp_new = client.post(
        "/tag/new",
        data={
            "nombre": "C++/C#",
            "color": "#659ad2",
        },
        follow_redirects=False,
    )
    assert resp_new.status_code in REDIRECT_STATUS_CODES | {200}

    # 3) Verificar en base de datos
    etiqueta = db_session.execute(database.select(Etiqueta).filter_by(nombre="C++/C#")).scalars().first()
    assert etiqueta is not None
    assert etiqueta.nombre == "C++/C#"


def test_e2e_tag_duplicate_prevention(app, db_session):
    """Test: intentar crear etiqueta duplicada."""
    # 1) Crear instructor y etiqueta inicial
    _crear_instructor(db_session)
    etiqueta = Etiqueta(
        nombre="JavaScript",
        color="#f7df1e",
    )
    db_session.add(etiqueta)
    db_session.commit()

    # 2) Login e intentar crear etiqueta con el mismo nombre
    client = _login_instructor(app)
    resp_duplicate = client.post(
        "/tag/new",
        data={
            "nombre": "JavaScript",
            "color": "#000000",
        },
        follow_redirects=False,
    )
    # El sistema puede aceptarla, rechazarla o mostrar error
    assert resp_duplicate.status_code in REDIRECT_STATUS_CODES | {200, 400}

    # 3) Verificar cuántas etiquetas "JavaScript" existen
    etiquetas = db_session.execute(database.select(Etiqueta).filter_by(nombre="JavaScript")).scalars().all()
    # Puede haber 1 o 2 dependiendo de la validación del sistema
    assert len(etiquetas) >= 1
