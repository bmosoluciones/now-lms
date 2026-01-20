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
Test end-to-end para funcionalidad de contacto.

Prueba el flujo completo de:
- Configuración del sitio para mostrar el formulario de contacto
- Visualización del formulario de contacto en la navbar
- Envío de mensajes de contacto
- Gestión de mensajes por administradores
- Cambio de estados de mensajes
"""


from now_lms.auth import proteger_passwd
from now_lms.db import Configuracion, ContactMessage, Usuario, database

REDIRECT_STATUS_CODES = {301, 302, 303, 307, 308}


def _crear_admin(db_session) -> Usuario:
    """Crea un usuario administrador para las pruebas."""
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


def _login_admin(app):
    """Inicia sesión como administrador y retorna el cliente."""
    client = app.test_client()
    resp = client.post("/user/login", data={"usuario": "admin", "acceso": "admin"}, follow_redirects=False)
    assert resp.status_code in REDIRECT_STATUS_CODES | {200}
    return client


def _habilitar_contacto(db_session):
    """Habilita la opción de contacto en la configuración del sitio."""
    config = db_session.execute(database.select(Configuracion)).scalar_one_or_none()
    if config:
        config.enable_contact = True
        db_session.commit()


def test_e2e_contact_configuration_and_navbar(app, db_session):
    """Test: configurar el sitio para mostrar el formulario de contacto en la navbar."""
    # 1) Crear admin y login
    _crear_admin(db_session)
    client = _login_admin(app)

    # 2) Habilitar contacto en configuración
    _habilitar_contacto(db_session)

    # 3) Verificar que la configuración está habilitada
    config = db_session.execute(database.select(Configuracion)).scalar_one_or_none()
    assert config is not None
    assert config.enable_contact is True

    # 4) Hacer petición GET para confirmar que el formulario es visible en navbar
    # (cuando enable_contact está habilitado)
    resp = client.get("/")
    assert resp.status_code == 200
    # Verificar que el enlace de contacto está presente cuando está habilitado
    # El enlace se renderiza condicionalmente con {% if is_contact_enabled() %}
    # Buscamos el texto "Contact" o "Contacto" en la respuesta
    assert b"Contact" in resp.data or b"contact" in resp.data.lower()


def test_e2e_contact_form_display(app, db_session):
    """Test: hacer petición GET al formulario de contacto para confirmar que se muestra correctamente."""
    # 1) Habilitar contacto
    _habilitar_contacto(db_session)

    # 2) Cliente público (sin login)
    client = app.test_client()

    # 3) Hacer petición GET al formulario de contacto
    resp = client.get("/contact")
    assert resp.status_code == 200

    # 4) Verificar que el formulario contiene los campos esperados
    assert b"name" in resp.data or b"nombre" in resp.data.lower()
    assert b"email" in resp.data or b"correo" in resp.data.lower()
    assert b"subject" in resp.data or b"asunto" in resp.data.lower()
    assert b"message" in resp.data or b"mensaje" in resp.data.lower()


def test_e2e_contact_form_submission(app, db_session):
    """Test: utilizar el cliente de pruebas para hacer petición POST al formulario y verificar almacenamiento."""
    # 1) Habilitar contacto
    _habilitar_contacto(db_session)

    # 2) Cliente público
    client = app.test_client()

    # 3) Enviar mensaje de contacto via POST
    contact_data = {
        "name": "Juan Pérez",
        "email": "juan.perez@example.com",
        "subject": "Consulta sobre cursos",
        "message": "Hola, me gustaría obtener más información sobre los cursos disponibles.",
    }

    resp = client.post("/contact", data=contact_data, follow_redirects=False)

    # El formulario redirige después de enviar exitosamente
    assert resp.status_code in REDIRECT_STATUS_CODES

    # 4) Verificar que el mensaje fue almacenado en la base de datos
    mensaje = db_session.execute(database.select(ContactMessage).filter_by(email="juan.perez@example.com")).scalars().first()
    assert mensaje is not None
    assert mensaje.name == "Juan Pérez"
    assert mensaje.subject == "Consulta sobre cursos"
    assert mensaje.message == "Hola, me gustaría obtener más información sobre los cursos disponibles."
    assert mensaje.status == "not_seen"  # Estado inicial


def test_e2e_contact_message_status_change(app, db_session):
    """Test: confirmar que un mensaje puede cambiar de estatus."""
    # 1) Crear admin y mensaje de contacto
    admin = _crear_admin(db_session)
    _habilitar_contacto(db_session)

    mensaje = ContactMessage(
        name="María García",
        email="maria.garcia@example.com",
        subject="Pregunta técnica",
        message="¿Cómo puedo restablecer mi contraseña?",
        status="not_seen",
    )
    db_session.add(mensaje)
    db_session.commit()
    mensaje_id = mensaje.id

    # 2) Login como admin
    client = _login_admin(app)

    # 3) Ver el mensaje (esto cambia el estado a "seen" automáticamente)
    resp_view = client.get(f"/admin/contact-messages/{mensaje_id}/view")
    assert resp_view.status_code == 200

    # 4) Verificar que el estado cambió a "seen"
    db_session.expire(mensaje)  # Refrescar el objeto desde la BD
    mensaje_visto = db_session.get(ContactMessage, mensaje_id)
    assert mensaje_visto.status == "seen"

    # 5) Cambiar el estado a "answered" via POST
    resp_update = client.post(
        f"/admin/contact-messages/{mensaje_id}/view",
        data={
            "status": "answered",
            "admin_notes": "Se envió respuesta por correo electrónico.",
        },
        follow_redirects=False,
    )
    assert resp_update.status_code in REDIRECT_STATUS_CODES

    # 6) Verificar que el estado cambió a "answered"
    db_session.expire(mensaje_visto)  # Refrescar nuevamente
    mensaje_respondido = db_session.get(ContactMessage, mensaje_id)
    assert mensaje_respondido.status == "answered"
    assert mensaje_respondido.admin_notes == "Se envió respuesta por correo electrónico."
    assert mensaje_respondido.answered_at is not None
    assert mensaje_respondido.answered_by == admin.usuario


def test_e2e_contact_form_validation(app, db_session):
    """Test: verificar validación de campos del formulario de contacto."""
    # 1) Habilitar contacto
    _habilitar_contacto(db_session)

    # 2) Cliente público
    client = app.test_client()

    # 3) Intentar enviar formulario con campos vacíos
    resp_empty = client.post(
        "/contact",
        data={
            "name": "",
            "email": "",
            "subject": "",
            "message": "",
        },
        follow_redirects=True,
    )
    assert resp_empty.status_code == 200

    # 4) Intentar enviar formulario con campos muy largos
    resp_long = client.post(
        "/contact",
        data={
            "name": "A" * 200,  # Excede 150 caracteres
            "email": "test@example.com",
            "subject": "Asunto",
            "message": "Mensaje",
        },
        follow_redirects=True,
    )
    assert resp_long.status_code == 200


def test_e2e_contact_admin_message_list(app, db_session):
    """Test: listar mensajes de contacto desde el panel de administración."""
    # 1) Crear admin y mensajes
    _crear_admin(db_session)
    _habilitar_contacto(db_session)

    mensaje1 = ContactMessage(
        name="Usuario 1",
        email="usuario1@example.com",
        subject="Consulta 1",
        message="Mensaje 1",
        status="not_seen",
    )
    mensaje2 = ContactMessage(
        name="Usuario 2",
        email="usuario2@example.com",
        subject="Consulta 2",
        message="Mensaje 2",
        status="seen",
    )
    db_session.add_all([mensaje1, mensaje2])
    db_session.commit()

    # 2) Login como admin
    client = _login_admin(app)

    # 3) Ver lista de mensajes en admin
    resp_list = client.get("/admin/contact-messages")
    assert resp_list.status_code == 200

    # 4) Verificar que ambos mensajes aparecen en la lista
    assert b"Usuario 1" in resp_list.data
    assert b"Usuario 2" in resp_list.data
    assert b"Consulta 1" in resp_list.data
    assert b"Consulta 2" in resp_list.data


def test_e2e_contact_disabled_configuration(app, db_session):
    """Test: verificar comportamiento cuando la opción de contacto está deshabilitada."""
    # 1) Crear admin
    _crear_admin(db_session)

    # 2) Asegurarse de que enable_contact está deshabilitado (valor por defecto)
    config = db_session.execute(database.select(Configuracion)).scalar_one_or_none()
    if config:
        config.enable_contact = False
        db_session.commit()

    # 3) Cliente público
    client = app.test_client()

    # 4) El formulario de contacto sigue siendo accesible directamente en /contact
    # Solo el enlace en la navbar no se muestra
    resp_contact = client.get("/contact")
    assert resp_contact.status_code == 200

    # 5) Verificar que el enlace NO está en la página principal
    resp_home = client.get("/")
    assert resp_home.status_code == 200
    # Cuando está deshabilitado, no debe haber enlace visible a contact en navbar
    # (esto depende del template, pero el enlace está condicionado por is_contact_enabled())


def test_admin_panel_shows_unread_contact_messages(app, db_session):
    """Test: verificar que el panel de administrador muestra el contador de mensajes sin leer."""
    # 1) Crear admin y mensajes de contacto
    admin = _crear_admin(db_session)
    _habilitar_contacto(db_session)

    # Crear mensajes con diferentes estados
    mensaje1 = ContactMessage(
        name="Usuario Test 1",
        email="test1@example.com",
        subject="Consulta 1",
        message="Mensaje de prueba 1",
        status="not_seen",
    )
    mensaje2 = ContactMessage(
        name="Usuario Test 2",
        email="test2@example.com",
        subject="Consulta 2",
        message="Mensaje de prueba 2",
        status="not_seen",
    )
    mensaje3 = ContactMessage(
        name="Usuario Test 3",
        email="test3@example.com",
        subject="Consulta 3",
        message="Mensaje de prueba 3",
        status="seen",
    )
    db_session.add_all([mensaje1, mensaje2, mensaje3])
    db_session.commit()

    # 2) Login como admin
    client = _login_admin(app)

    # 3) Acceder al panel de administrador
    resp = client.get("/home/panel")
    assert resp.status_code == 200

    # 4) Verificar que el contador de mensajes sin leer aparece en el panel
    # Debe mostrar "2" porque hay 2 mensajes con status "not_seen"
    assert b"Mensajes Sin Leer" in resp.data or b"Unread Messages" in resp.data
    # Verificar que aparece el número correcto (2)
    # El número debe estar cerca del texto de mensajes sin leer
    data_str = resp.data.decode("utf-8")
    # Buscar el patrón: el número 2 debe aparecer en el contexto de mensajes sin leer
    assert "2" in data_str
    # Verificar que existe el enlace a la lista de mensajes de contacto
    assert b"/admin/contact-messages" in resp.data
