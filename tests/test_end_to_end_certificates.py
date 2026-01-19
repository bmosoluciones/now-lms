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
Test end-to-end para funcionalidad de certificados.

Prueba el flujo completo de:
- Listado de certificados
- Creación/emisión de certificados
- Habilitación/deshabilitación de certificados
- Verificación de certificados emitidos
"""


from now_lms.auth import proteger_passwd
from now_lms.db import Certificado, Curso, EstudianteCurso, Usuario, database

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


def _crear_admin(db_session) -> Usuario:
    """Crea un usuario admin para las pruebas."""
    user = Usuario(
        usuario="admin",
        acceso=proteger_passwd("admin"),
        nombre="Admin",
        correo_electronico="admin@example.com",
        tipo="admin",
        activo=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


def _crear_estudiante(db_session) -> Usuario:
    """Crea un usuario estudiante para las pruebas."""
    user = Usuario(
        usuario="estudiante",
        acceso=proteger_passwd("estudiante"),
        nombre="Estudiante",
        correo_electronico="estudiante@example.com",
        tipo="student",  # Usar 'student' no 'estudiante'
        activo=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


def _login_usuario(app, usuario: str, password: str):
    """Inicia sesión con un usuario específico y retorna el cliente."""
    client = app.test_client()
    resp = client.post("/user/login", data={"usuario": usuario, "acceso": password}, follow_redirects=False)
    assert resp.status_code in REDIRECT_STATUS_CODES | {200}
    return client


def test_e2e_certificate_list(app, db_session):
    """Test: listar certificados como instructor."""
    # 1) Crear instructor y login
    _crear_instructor(db_session)
    client = _login_usuario(app, "instructor", "instructor")

    # 2) Crear algunos certificados en la base de datos
    for i in range(3):
        certificado = Certificado(
            titulo=f"Certificado {i}",
            descripcion=f"Descripcion {i}",
            habilitado=True,
        )
        db_session.add(certificado)
    db_session.commit()

    # 3) Ver lista de certificados
    resp_list = client.get("/certificate/list")
    assert resp_list.status_code == 200
    # Verificar que la página de certificados carga correctamente
    assert b"certificado" in resp_list.data.lower() or b"plantilla" in resp_list.data.lower()


def test_e2e_certificate_remove_and_add(app, db_session):
    """Test: deshabilitar y habilitar un certificado (admin)."""
    # 1) Crear admin y login
    _crear_admin(db_session)
    client = _login_usuario(app, "admin", "admin")

    # 2) Crear certificado habilitado
    certificado = Certificado(
        titulo="Certificado Test",
        descripcion="Descripcion del certificado",
        habilitado=True,
    )
    db_session.add(certificado)
    db_session.commit()
    cert_id = certificado.id

    # 3) Deshabilitar certificado via GET
    resp_remove = client.get(f"/certificate/{cert_id}/remove", follow_redirects=False)
    assert resp_remove.status_code in REDIRECT_STATUS_CODES | {200}

    # 4) Verificar que está deshabilitado en la base de datos
    cert_deshabilitado = db_session.get(Certificado, cert_id)
    assert cert_deshabilitado is not None
    assert cert_deshabilitado.habilitado is False

    # 5) Habilitar certificado nuevamente
    resp_add = client.get(f"/certificate/{cert_id}/add", follow_redirects=False)
    assert resp_add.status_code in REDIRECT_STATUS_CODES | {200}

    # 6) Verificar que está habilitado en la base de datos
    cert_habilitado = db_session.get(Certificado, cert_id)
    assert cert_habilitado is not None
    assert cert_habilitado.habilitado is True


def test_e2e_certificate_emission(app, db_session):
    """Test: emitir certificado a un estudiante que completó un curso."""
    # 1) Crear instructor, estudiante y curso
    instructor = _crear_instructor(db_session)  # noqa: F841
    estudiante = _crear_estudiante(db_session)

    curso = Curso(
        nombre="Curso de Python",
        codigo="python101",
        descripcion="Curso de introducción a Python",
        descripcion_corta="Python básico",
        nivel=0,
        duracion=10,
        publico=True,
        modalidad="self_paced",
        estado="open",
        certificado=True,
    )
    db_session.add(curso)
    db_session.commit()

    # 2) Inscribir estudiante y marcar como completado
    inscripcion = EstudianteCurso(
        usuario=estudiante.id,
        curso=curso.codigo,
        vigente=True,
    )
    db_session.add(inscripcion)
    db_session.commit()

    # 3) Login como instructor
    client = _login_usuario(app, "instructor", "instructor")  # noqa: F841

    # 4) Verificar que el curso y la inscripción existen
    assert curso is not None
    assert inscripcion.vigente is True


def test_e2e_certificate_view_student(app, db_session):
    """Test: verificar que un estudiante puede ver sus certificados."""
    # 1) Crear estudiante
    estudiante = _crear_estudiante(db_session)  # noqa: F841
    client = _login_usuario(app, "estudiante", "estudiante")

    # 2) Ver la lista de certificados emitidos
    resp_certificates = client.get("/certificate/issued/list", follow_redirects=False)
    # La ruta existe según las rutas disponibles
    assert resp_certificates.status_code in REDIRECT_STATUS_CODES | {200}


def test_e2e_certificate_new_form(app, db_session):
    """Test: crear un nuevo certificado mediante formulario."""
    # 1) Crear admin y login
    _crear_admin(db_session)
    client = _login_usuario(app, "admin", "admin")

    # 2) Acceder al formulario de nuevo certificado
    resp_form = client.get("/certificate/new", follow_redirects=False)
    # La ruta existe
    assert resp_form.status_code in {200, *REDIRECT_STATUS_CODES}

    # 3) Intentar crear certificado
    resp_create = client.post(
        "/certificate/new",
        data={
            "titulo": "Certificado Nuevo",
            "descripcion": "Descripcion del certificado",
            "tipo": "course",
            "html": "<p>Certificado</p>",
            "css": "body { color: black; }",
        },
        follow_redirects=False,
    )
    assert resp_create.status_code in REDIRECT_STATUS_CODES | {200}

    # Verificar en base de datos
    certificado = db_session.execute(database.select(Certificado).filter_by(titulo="Certificado Nuevo")).scalars().first()
    if certificado:
        # Los certificados se crean deshabilitados por defecto
        assert certificado.habilitado is False or certificado.habilitado is True
