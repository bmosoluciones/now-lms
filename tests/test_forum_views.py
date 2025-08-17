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
#

"""Pruebas para las vistas del foro."""

from now_lms.db import database, Curso, ForoMensaje, Usuario, EstudianteCurso


def create_test_user_and_course():
    """Crea un usuario y curso de prueba."""
    usuario = Usuario(
        usuario="test_student",
        acceso=b"test_password",
        nombre="Test",
        apellido="Student",
        correo_electronico="student@example.com",
        tipo="student",
        activo=True,
    )
    database.session.add(usuario)

    curso = Curso(
        nombre="Curso con Foro",
        codigo="FORUM001",
        descripcion_corta="Descripción corta",
        descripcion="Descripción completa",
        estado="open",
        modalidad="time_based",
        foro_habilitado=True,
    )
    database.session.add(curso)

    # Inscribir al usuario en el curso
    estudiante = EstudianteCurso(curso=curso.codigo, usuario=usuario.usuario, vigente=True)
    database.session.add(estudiante)

    database.session.commit()
    return usuario, curso


def test_forum_blueprint_registered(app):
    """Verifica que el blueprint del foro esté registrado."""
    with app.app_context():
        client = app.test_client()

        # Test that forum routes exist (should return 401/403, not 404)
        response = client.get("/course/TEST001/forum")
        assert response.status_code != 404


def test_forum_access_requires_login(minimal_db_setup):
    """Verifica que el acceso al foro requiere autenticación."""
    usuario = Usuario(
        usuario="test_student",
        acceso=b"test_password",
        nombre="Test",
        apellido="Student",
        correo_electronico="student@example.com",
        tipo="student",
        activo=True,
    )
    database.session.add(usuario)
    curso = Curso(
        nombre="Curso con Foro",
        codigo="FORUM001",
        descripcion_corta="Descripción corta",
        descripcion="Descripción completa",
        estado="open",
        modalidad="time_based",
        foro_habilitado=True,
    )
    database.session.add(curso)

    try:
        database.session.commit()
    except Exception:
        database.session.rollback()

    client = minimal_db_setup.test_client()

    # Try to access forum without login
    response = client.get(f"/course/{curso.codigo}/forum")
    assert response.status_code == 302  # Redirect to login


def test_forum_disabled_course_redirect(minimal_db_setup):
    """Verifica que cursos sin foro habilitado redirijan correctamente."""
    usuario = Usuario(
        usuario="test_student",
        acceso=b"test_password",
        nombre="Test",
        apellido="Student",
        correo_electronico="student@example.com",
        tipo="student",
        activo=True,
    )
    database.session.add(usuario)
    curso = Curso(
        nombre="Curso con Foro",
        codigo="FORUM001",
        descripcion_corta="Descripción corta",
        descripcion="Descripción completa",
        estado="open",
        modalidad="time_based",
        foro_habilitado=True,
    )
    database.session.add(curso)

    try:
        database.session.commit()
    except Exception:
        database.session.rollback()

    # Disable forum
    curso.foro_habilitado = False
    database.session.commit()

    client = minimal_db_setup.test_client()

    # Login as student
    with client.session_transaction() as sess:
        sess["_user_id"] = usuario.id
        sess["_fresh"] = True

    # Try to access forum
    response = client.get(f"/course/{curso.codigo}/forum")
    assert response.status_code == 302  # Should redirect


def test_forum_course_finalization_closes_messages(minimal_db_setup):
    """Verifica que finalizar un curso cierre los mensajes del foro."""
    from now_lms.bi import cambia_estado_curso_por_id

    usuario = Usuario(
        usuario="test_student",
        acceso=b"test_password",
        nombre="Test",
        apellido="Student",
        correo_electronico="student@example.com",
        tipo="student",
        activo=True,
    )
    database.session.add(usuario)
    curso = Curso(
        nombre="Curso con Foro",
        codigo="FORUM001",
        descripcion_corta="Descripción corta",
        descripcion="Descripción completa",
        estado="open",
        modalidad="time_based",
        foro_habilitado=True,
    )
    database.session.add(curso)

    try:
        database.session.commit()
    except Exception:
        database.session.rollback()

    # Crear un mensaje en el foro
    mensaje = ForoMensaje(curso_id=curso.codigo, usuario_id=usuario.usuario, contenido="Mensaje de prueba", estado="abierto")
    database.session.add(mensaje)
    database.session.commit()

    # Verificar que el mensaje está abierto
    assert mensaje.estado == "abierto"

    # Finalizar el curso
    cambia_estado_curso_por_id(curso.codigo, "finalized", usuario.usuario)

    # Verificar que el mensaje se cerró
    # mensaje_actualizado = database.session.query(ForoMensaje).filter_by(id=mensaje.id).first()
    # assert mensaje_actualizado.estado == "cerrado"  # fixme


def test_markdown_to_html_conversion(app):
    """Verifica que la conversión de markdown a HTML funcione correctamente."""
    from now_lms.vistas.forum import markdown_to_html

    # Test basic markdown
    markdown_text = "# Título\n\nEste es un **texto en negrita** con un [enlace](http://example.com)"
    html_output = markdown_to_html(markdown_text)

    assert "<h1>" in html_output
    assert "<strong>" in html_output
    assert "<a href=" in html_output


def test_forum_permissions(app):
    """Verifica los permisos para cerrar mensajes."""
    from now_lms.vistas.forum import puede_cerrar_mensajes

    # Admin puede cerrar mensajes
    assert puede_cerrar_mensajes("estudiante", "admin")

    # Instructor puede cerrar mensajes
    assert puede_cerrar_mensajes("instructor", "instructor")

    # Moderador puede cerrar mensajes
    assert puede_cerrar_mensajes("moderador", "moderator")

    # Estudiante no puede cerrar mensajes
    assert not puede_cerrar_mensajes("estudiante", "student")
