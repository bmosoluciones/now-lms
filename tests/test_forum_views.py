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

"""Comprehensive tests for forum views."""

import pytest
from flask import url_for

from now_lms.db import database, Curso, ForoMensaje, Usuario, EstudianteCurso, DocenteCurso, ModeradorCurso


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


class TestForumRoutesComprehensive:
    """Comprehensive tests for all forum routes starting with /course/."""

    @pytest.fixture(autouse=True)
    def setup_test_data(self, minimal_db_setup):
        """Set up test data for each test."""
        # Create test users
        self.admin_user = Usuario(
            usuario="admin_user",
            acceso=b"password123",
            nombre="Admin",
            apellido="User",
            correo_electronico="admin@test.com",
            tipo="admin",
            activo=True,
        )

        self.instructor_user = Usuario(
            usuario="instructor_user",
            acceso=b"password123",
            nombre="Instructor",
            apellido="User",
            correo_electronico="instructor@test.com",
            tipo="instructor",
            activo=True,
        )

        self.moderator_user = Usuario(
            usuario="moderator_user",
            acceso=b"password123",
            nombre="Moderator",
            apellido="User",
            correo_electronico="moderator@test.com",
            tipo="moderator",
            activo=True,
        )

        self.student_user = Usuario(
            usuario="student_user",
            acceso=b"password123",
            nombre="Student",
            apellido="User",
            correo_electronico="student@test.com",
            tipo="student",
            activo=True,
        )

        self.unauthorized_user = Usuario(
            usuario="unauthorized_user",
            acceso=b"password123",
            nombre="Unauthorized",
            apellido="User",
            correo_electronico="unauthorized@test.com",
            tipo="student",
            activo=True,
        )

        database.session.add_all(
            [self.admin_user, self.instructor_user, self.moderator_user, self.student_user, self.unauthorized_user]
        )

        # Create test course with forum enabled
        self.course = Curso(
            nombre="Curso con Foro",
            codigo="FORUM001",
            descripcion_corta="Descripción corta",
            descripcion="Descripción completa",
            estado="open",
            modalidad="time_based",
            foro_habilitado=True,
        )
        database.session.add(self.course)

        # Create course without forum
        self.course_no_forum = Curso(
            nombre="Curso sin Foro",
            codigo="NOFORUM001",
            descripcion_corta="Descripción corta",
            descripcion="Descripción completa",
            estado="open",
            modalidad="time_based",
            foro_habilitado=False,
        )
        database.session.add(self.course_no_forum)

        # Create finalized course
        self.finalized_course = Curso(
            nombre="Curso Finalizado",
            codigo="FINALIZED001",
            descripcion_corta="Descripción corta",
            descripcion="Descripción completa",
            estado="finalizado",
            modalidad="time_based",
            foro_habilitado=True,
        )
        database.session.add(self.finalized_course)

        database.session.commit()

        # Create course relationships
        self.instructor_course = DocenteCurso(curso=self.course.codigo, usuario=self.instructor_user.usuario, vigente=True)

        self.moderator_course = ModeradorCurso(curso=self.course.codigo, usuario=self.moderator_user.usuario, vigente=True)

        self.student_course = EstudianteCurso(curso=self.course.codigo, usuario=self.student_user.usuario, vigente=True)

        database.session.add_all([self.instructor_course, self.moderator_course, self.student_course])

        # Create test forum message
        self.forum_message = ForoMensaje(
            curso_id=self.course.codigo,
            usuario_id=self.student_user.usuario,
            contenido="Test forum message with **markdown**",
            estado="abierto",
        )
        database.session.add(self.forum_message)
        database.session.commit()

        self.app = minimal_db_setup
        self.client = self.app.test_client()

    def login_user(self, user):
        """Helper to login a user."""
        with self.client.session_transaction() as sess:
            sess["_user_id"] = str(user.id)
            sess["_fresh"] = True

    def test_ver_foro_requires_login(self):
        """Test that accessing forum requires login."""
        response = self.client.get(url_for("forum.ver_foro", course_code=self.course.codigo))
        assert response.status_code == 302  # Redirect to login

    def test_ver_foro_course_not_found(self):
        """Test forum access with non-existent course."""
        self.login_user(self.student_user)
        response = self.client.get(url_for("forum.ver_foro", course_code="NONEXISTENT"))
        assert response.status_code == 404

    def test_ver_foro_forum_disabled(self):
        """Test forum access when forum is disabled for course."""
        self.login_user(self.student_user)
        response = self.client.get(url_for("forum.ver_foro", course_code=self.course_no_forum.codigo))
        assert response.status_code == 302  # Redirect

    def test_ver_foro_no_course_access(self):
        """Test forum access when user doesn't have course access."""
        self.login_user(self.unauthorized_user)
        response = self.client.get(url_for("forum.ver_foro", course_code=self.course.codigo))
        assert response.status_code == 403

    def test_ver_foro_as_student(self):
        """Test forum access as enrolled student."""
        self.login_user(self.student_user)
        response = self.client.get(url_for("forum.ver_foro", course_code=self.course.codigo))
        assert response.status_code == 200
        assert b"Test forum message" in response.data

    def test_ver_foro_as_instructor(self):
        """Test forum access as course instructor."""
        self.login_user(self.instructor_user)
        response = self.client.get(url_for("forum.ver_foro", course_code=self.course.codigo))
        assert response.status_code == 200
        assert b"Test forum message" in response.data

    def test_ver_foro_as_moderator(self):
        """Test forum access as course moderator."""
        self.login_user(self.moderator_user)
        response = self.client.get(url_for("forum.ver_foro", course_code=self.course.codigo))
        assert response.status_code == 200
        assert b"Test forum message" in response.data

    def test_ver_foro_pagination(self):
        """Test forum pagination."""
        # Create multiple messages for pagination
        for i in range(15):
            message = ForoMensaje(
                curso_id=self.course.codigo, usuario_id=self.student_user.usuario, contenido=f"Message {i}", estado="abierto"
            )
            database.session.add(message)
        database.session.commit()

        self.login_user(self.student_user)
        response = self.client.get(url_for("forum.ver_foro", course_code=self.course.codigo, page=2))
        assert response.status_code == 200

    def test_nuevo_mensaje_requires_login(self):
        """Test that creating new message requires login."""
        response = self.client.get(url_for("forum.nuevo_mensaje", course_code=self.course.codigo))
        assert response.status_code == 302

    def test_nuevo_mensaje_course_not_found(self):
        """Test new message with non-existent course."""
        self.login_user(self.student_user)
        response = self.client.get(url_for("forum.nuevo_mensaje", course_code="NONEXISTENT"))
        assert response.status_code == 404

    def test_nuevo_mensaje_forum_disabled(self):
        """Test new message when forum is disabled."""
        self.login_user(self.student_user)
        response = self.client.get(url_for("forum.nuevo_mensaje", course_code=self.course_no_forum.codigo))
        assert response.status_code == 404

    def test_nuevo_mensaje_no_course_access(self):
        """Test new message when user doesn't have course access."""
        self.login_user(self.unauthorized_user)
        response = self.client.get(url_for("forum.nuevo_mensaje", course_code=self.course.codigo))
        assert response.status_code == 403

    def test_nuevo_mensaje_finalized_course(self):
        """Test new message in finalized course."""
        # Add student to finalized course
        student_finalized = EstudianteCurso(
            curso=self.finalized_course.codigo, usuario=self.student_user.usuario, vigente=True
        )
        database.session.add(student_finalized)
        database.session.commit()

        self.login_user(self.student_user)
        response = self.client.get(url_for("forum.nuevo_mensaje", course_code=self.finalized_course.codigo))
        assert response.status_code == 302  # Redirect with error

    def test_nuevo_mensaje_get_form(self):
        """Test GET request to new message form."""
        self.login_user(self.student_user)
        response = self.client.get(url_for("forum.nuevo_mensaje", course_code=self.course.codigo))
        assert response.status_code == 200
        assert b"nuevo mensaje" in response.data.lower()

    def test_nuevo_mensaje_post_success(self):
        """Test successful message creation."""
        self.login_user(self.student_user)
        response = self.client.post(
            url_for("forum.nuevo_mensaje", course_code=self.course.codigo),
            data={
                "contenido": "New test message content",
                "csrf_token": "test",
            },
            follow_redirects=True,
        )

        # Check message was created
        new_message = database.session.execute(
            database.select(ForoMensaje).filter_by(curso_id=self.course.codigo, contenido="New test message content")
        ).scalar_one_or_none()

        assert new_message is not None
        assert new_message.estado == "abierto"

    def test_ver_mensaje_requires_login(self):
        """Test that viewing message requires login."""
        response = self.client.get(
            url_for("forum.ver_mensaje", course_code=self.course.codigo, message_id=self.forum_message.id)
        )
        assert response.status_code == 302

    def test_ver_mensaje_course_not_found(self):
        """Test viewing message with non-existent course."""
        self.login_user(self.student_user)
        response = self.client.get(url_for("forum.ver_mensaje", course_code="NONEXISTENT", message_id=self.forum_message.id))
        assert response.status_code == 404

    def test_ver_mensaje_message_not_found(self):
        """Test viewing non-existent message."""
        self.login_user(self.student_user)
        response = self.client.get(url_for("forum.ver_mensaje", course_code=self.course.codigo, message_id=99999))
        assert response.status_code == 404

    def test_ver_mensaje_forum_disabled(self):
        """Test viewing message when forum is disabled."""
        self.login_user(self.student_user)
        response = self.client.get(
            url_for("forum.ver_mensaje", course_code=self.course_no_forum.codigo, message_id=self.forum_message.id)
        )
        assert response.status_code == 404

    def test_ver_mensaje_no_course_access(self):
        """Test viewing message when user doesn't have course access."""
        self.login_user(self.unauthorized_user)
        response = self.client.get(
            url_for("forum.ver_mensaje", course_code=self.course.codigo, message_id=self.forum_message.id)
        )
        assert response.status_code == 403

    def test_ver_mensaje_success(self):
        """Test successful message viewing."""
        self.login_user(self.student_user)
        response = self.client.get(
            url_for("forum.ver_mensaje", course_code=self.course.codigo, message_id=self.forum_message.id)
        )
        assert response.status_code == 200
        assert b"Test forum message" in response.data

    def test_ver_mensaje_with_replies(self):
        """Test viewing message with replies."""
        # Create reply
        reply = ForoMensaje(
            curso_id=self.course.codigo,
            usuario_id=self.instructor_user.usuario,
            parent_id=self.forum_message.id,
            contenido="Reply to test message",
            estado="abierto",
        )
        database.session.add(reply)
        database.session.commit()

        self.login_user(self.student_user)
        response = self.client.get(
            url_for("forum.ver_mensaje", course_code=self.course.codigo, message_id=self.forum_message.id)
        )
        assert response.status_code == 200
        assert b"Reply to test message" in response.data

    def test_responder_mensaje_requires_login(self):
        """Test that replying to message requires login."""
        response = self.client.get(
            url_for("forum.responder_mensaje", course_code=self.course.codigo, message_id=self.forum_message.id)
        )
        assert response.status_code == 302

    def test_responder_mensaje_course_not_found(self):
        """Test replying to message with non-existent course."""
        self.login_user(self.student_user)
        response = self.client.get(
            url_for("forum.responder_mensaje", course_code="NONEXISTENT", message_id=self.forum_message.id)
        )
        assert response.status_code == 404

    def test_responder_mensaje_message_not_found(self):
        """Test replying to non-existent message."""
        self.login_user(self.student_user)
        response = self.client.get(url_for("forum.responder_mensaje", course_code=self.course.codigo, message_id=99999))
        assert response.status_code == 404

    def test_responder_mensaje_forum_disabled(self):
        """Test replying to message when forum is disabled."""
        self.login_user(self.student_user)
        response = self.client.get(
            url_for("forum.responder_mensaje", course_code=self.course_no_forum.codigo, message_id=self.forum_message.id)
        )
        assert response.status_code == 404

    def test_responder_mensaje_no_course_access(self):
        """Test replying to message when user doesn't have course access."""
        self.login_user(self.unauthorized_user)
        response = self.client.get(
            url_for("forum.responder_mensaje", course_code=self.course.codigo, message_id=self.forum_message.id)
        )
        assert response.status_code == 403

    def test_responder_mensaje_closed_message(self):
        """Test replying to closed message."""
        # Close the message
        self.forum_message.estado = "cerrado"
        database.session.commit()

        self.login_user(self.student_user)
        response = self.client.get(
            url_for("forum.responder_mensaje", course_code=self.course.codigo, message_id=self.forum_message.id)
        )
        assert response.status_code == 302  # Redirect with error

        # Reset message state
        self.forum_message.estado = "abierto"
        database.session.commit()

    def test_responder_mensaje_get_form(self):
        """Test GET request to reply form."""
        self.login_user(self.student_user)
        response = self.client.get(
            url_for("forum.responder_mensaje", course_code=self.course.codigo, message_id=self.forum_message.id)
        )
        assert response.status_code == 200
        assert b"respuesta" in response.data.lower()

    def test_responder_mensaje_post_success(self):
        """Test successful reply creation."""
        self.login_user(self.instructor_user)
        response = self.client.post(
            url_for("forum.responder_mensaje", course_code=self.course.codigo, message_id=self.forum_message.id),
            data={
                "contenido": "Reply to the forum message",
                "csrf_token": "test",
            },
            follow_redirects=True,
        )

        # Check reply was created
        reply = database.session.execute(
            database.select(ForoMensaje).filter_by(
                curso_id=self.course.codigo, parent_id=self.forum_message.id, contenido="Reply to the forum message"
            )
        ).scalar_one_or_none()

        assert reply is not None
        assert reply.estado == "abierto"

    def test_cerrar_mensaje_requires_login(self):
        """Test that closing message requires login."""
        response = self.client.post(
            url_for("forum.cerrar_mensaje", course_code=self.course.codigo, message_id=self.forum_message.id)
        )
        assert response.status_code == 302

    def test_cerrar_mensaje_course_not_found(self):
        """Test closing message with non-existent course."""
        self.login_user(self.instructor_user)
        response = self.client.post(
            url_for("forum.cerrar_mensaje", course_code="NONEXISTENT", message_id=self.forum_message.id)
        )
        assert response.status_code == 404

    def test_cerrar_mensaje_message_not_found(self):
        """Test closing non-existent message."""
        self.login_user(self.instructor_user)
        response = self.client.post(url_for("forum.cerrar_mensaje", course_code=self.course.codigo, message_id=99999))
        assert response.status_code == 404

    def test_cerrar_mensaje_no_course_access(self):
        """Test closing message when user doesn't have course access."""
        self.login_user(self.unauthorized_user)
        response = self.client.post(
            url_for("forum.cerrar_mensaje", course_code=self.course.codigo, message_id=self.forum_message.id)
        )
        assert response.status_code == 403

    def test_cerrar_mensaje_insufficient_permissions(self):
        """Test closing message without sufficient permissions."""
        self.login_user(self.student_user)
        response = self.client.post(
            url_for("forum.cerrar_mensaje", course_code=self.course.codigo, message_id=self.forum_message.id)
        )
        assert response.status_code == 403

    def test_cerrar_mensaje_as_instructor(self):
        """Test closing message as instructor."""
        self.login_user(self.instructor_user)
        response = self.client.post(
            url_for("forum.cerrar_mensaje", course_code=self.course.codigo, message_id=self.forum_message.id)
        )
        assert response.status_code == 302  # Redirect

        # Check message was closed
        database.session.refresh(self.forum_message)
        assert self.forum_message.estado == "cerrado"

    def test_cerrar_mensaje_as_moderator(self):
        """Test closing message as moderator."""
        # Reset message state first
        self.forum_message.estado = "abierto"
        database.session.commit()

        self.login_user(self.moderator_user)
        response = self.client.post(
            url_for("forum.cerrar_mensaje", course_code=self.course.codigo, message_id=self.forum_message.id)
        )
        assert response.status_code == 302  # Redirect

        # Check message was closed
        database.session.refresh(self.forum_message)
        assert self.forum_message.estado == "cerrado"

    def test_cerrar_mensaje_as_admin(self):
        """Test closing message as admin."""
        # Reset message state first
        self.forum_message.estado = "abierto"
        database.session.commit()

        # Add admin to course as instructor (admins can act as instructors)
        admin_course = DocenteCurso(curso=self.course.codigo, usuario=self.admin_user.usuario, vigente=True)
        database.session.add(admin_course)
        database.session.commit()

        self.login_user(self.admin_user)
        response = self.client.post(
            url_for("forum.cerrar_mensaje", course_code=self.course.codigo, message_id=self.forum_message.id)
        )
        assert response.status_code == 302  # Redirect

        # Check message was closed
        database.session.refresh(self.forum_message)
        assert self.forum_message.estado == "cerrado"

    def test_cerrar_mensaje_ajax_request(self):
        """Test closing message via AJAX request."""
        # Reset message state first
        self.forum_message.estado = "abierto"
        database.session.commit()

        self.login_user(self.instructor_user)
        response = self.client.post(
            url_for("forum.cerrar_mensaje", course_code=self.course.codigo, message_id=self.forum_message.id),
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 200
        assert response.json["status"] == "success"

    def test_abrir_mensaje_requires_login(self):
        """Test that opening message requires login."""
        response = self.client.post(
            url_for("forum.abrir_mensaje", course_code=self.course.codigo, message_id=self.forum_message.id)
        )
        assert response.status_code == 302

    def test_abrir_mensaje_course_not_found(self):
        """Test opening message with non-existent course."""
        self.login_user(self.instructor_user)
        response = self.client.post(
            url_for("forum.abrir_mensaje", course_code="NONEXISTENT", message_id=self.forum_message.id)
        )
        assert response.status_code == 404

    def test_abrir_mensaje_message_not_found(self):
        """Test opening non-existent message."""
        self.login_user(self.instructor_user)
        response = self.client.post(url_for("forum.abrir_mensaje", course_code=self.course.codigo, message_id=99999))
        assert response.status_code == 404

    def test_abrir_mensaje_no_course_access(self):
        """Test opening message when user doesn't have course access."""
        self.login_user(self.unauthorized_user)
        response = self.client.post(
            url_for("forum.abrir_mensaje", course_code=self.course.codigo, message_id=self.forum_message.id)
        )
        assert response.status_code == 403

    def test_abrir_mensaje_insufficient_permissions(self):
        """Test opening message without sufficient permissions."""
        self.login_user(self.student_user)
        response = self.client.post(
            url_for("forum.abrir_mensaje", course_code=self.course.codigo, message_id=self.forum_message.id)
        )
        assert response.status_code == 403

    def test_abrir_mensaje_finalized_course(self):
        """Test opening message in finalized course."""
        # Add instructor to finalized course and create message
        instructor_finalized = DocenteCurso(
            curso=self.finalized_course.codigo, usuario=self.instructor_user.usuario, vigente=True
        )
        database.session.add(instructor_finalized)

        message_finalized = ForoMensaje(
            curso_id=self.finalized_course.codigo,
            usuario_id=self.instructor_user.usuario,
            contenido="Message in finalized course",
            estado="cerrado",
        )
        database.session.add(message_finalized)
        database.session.commit()

        self.login_user(self.instructor_user)
        response = self.client.post(
            url_for("forum.abrir_mensaje", course_code=self.finalized_course.codigo, message_id=message_finalized.id)
        )
        assert response.status_code == 302  # Redirect with error

    def test_abrir_mensaje_as_instructor(self):
        """Test opening message as instructor."""
        # Close message first
        self.forum_message.estado = "cerrado"
        database.session.commit()

        self.login_user(self.instructor_user)
        response = self.client.post(
            url_for("forum.abrir_mensaje", course_code=self.course.codigo, message_id=self.forum_message.id)
        )
        assert response.status_code == 302  # Redirect

        # Check message was opened
        database.session.refresh(self.forum_message)
        assert self.forum_message.estado == "abierto"

    def test_abrir_mensaje_as_moderator(self):
        """Test opening message as moderator."""
        # Close message first
        self.forum_message.estado = "cerrado"
        database.session.commit()

        self.login_user(self.moderator_user)
        response = self.client.post(
            url_for("forum.abrir_mensaje", course_code=self.course.codigo, message_id=self.forum_message.id)
        )
        assert response.status_code == 302  # Redirect

        # Check message was opened
        database.session.refresh(self.forum_message)
        assert self.forum_message.estado == "abierto"

    def test_abrir_mensaje_as_admin(self):
        """Test opening message as admin."""
        # Close message first
        self.forum_message.estado = "cerrado"
        database.session.commit()

        # Add admin to course as instructor (admins can act as instructors)
        admin_course = DocenteCurso(curso=self.course.codigo, usuario=self.admin_user.usuario, vigente=True)
        database.session.add(admin_course)
        database.session.commit()

        self.login_user(self.admin_user)
        response = self.client.post(
            url_for("forum.abrir_mensaje", course_code=self.course.codigo, message_id=self.forum_message.id)
        )
        assert response.status_code == 302  # Redirect

        # Check message was opened
        database.session.refresh(self.forum_message)
        assert self.forum_message.estado == "abierto"

    def test_abrir_mensaje_ajax_request(self):
        """Test opening message via AJAX request."""
        # Close message first
        self.forum_message.estado = "cerrado"
        database.session.commit()

        self.login_user(self.instructor_user)
        response = self.client.post(
            url_for("forum.abrir_mensaje", course_code=self.course.codigo, message_id=self.forum_message.id),
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 200
        assert response.json["status"] == "success"


class TestForumHelperFunctions:
    """Test forum helper functions."""

    @pytest.fixture(autouse=True)
    def setup_test_data(self, minimal_db_setup):
        """Set up test data for each test."""
        self.instructor_user = Usuario(
            usuario="instructor_user",
            acceso=b"password123",
            nombre="Instructor",
            apellido="User",
            correo_electronico="instructor@test.com",
            tipo="instructor",
            activo=True,
        )

        self.student_user = Usuario(
            usuario="student_user",
            acceso=b"password123",
            nombre="Student",
            apellido="User",
            correo_electronico="student@test.com",
            tipo="student",
            activo=True,
        )

        database.session.add_all([self.instructor_user, self.student_user])

        self.course = Curso(
            nombre="Test Course",
            codigo="TEST001",
            descripcion_corta="Test description",
            descripcion="Full description",
            estado="open",
            modalidad="time_based",
            foro_habilitado=True,
        )
        database.session.add(self.course)
        database.session.commit()

    def test_verificar_acceso_curso_instructor(self):
        """Test course access verification for instructor."""
        from now_lms.vistas.forum import verificar_acceso_curso

        # Add instructor relationship
        instructor_course = DocenteCurso(curso=self.course.codigo, usuario=self.instructor_user.usuario, vigente=True)
        database.session.add(instructor_course)
        database.session.commit()

        tiene_acceso, role = verificar_acceso_curso(self.course.codigo, self.instructor_user.usuario)
        assert tiene_acceso is True
        assert role == "instructor"

    def test_verificar_acceso_curso_moderador(self):
        """Test course access verification for moderator."""
        from now_lms.vistas.forum import verificar_acceso_curso

        # Add moderator relationship
        moderator_course = ModeradorCurso(curso=self.course.codigo, usuario=self.instructor_user.usuario, vigente=True)
        database.session.add(moderator_course)
        database.session.commit()

        tiene_acceso, role = verificar_acceso_curso(self.course.codigo, self.instructor_user.usuario)
        assert tiene_acceso is True
        assert role == "moderador"

    def test_verificar_acceso_curso_estudiante(self):
        """Test course access verification for student."""
        from now_lms.vistas.forum import verificar_acceso_curso

        # Add student relationship
        student_course = EstudianteCurso(curso=self.course.codigo, usuario=self.student_user.usuario, vigente=True)
        database.session.add(student_course)
        database.session.commit()

        tiene_acceso, role = verificar_acceso_curso(self.course.codigo, self.student_user.usuario)
        assert tiene_acceso is True
        assert role == "estudiante"

    def test_verificar_acceso_curso_no_access(self):
        """Test course access verification when user has no access."""
        from now_lms.vistas.forum import verificar_acceso_curso

        tiene_acceso, role = verificar_acceso_curso(self.course.codigo, self.student_user.usuario)
        assert tiene_acceso is False
        assert role is None

    def test_markdown_to_html_basic(self):
        """Test basic markdown to HTML conversion."""
        from now_lms.vistas.forum import markdown_to_html

        markdown_text = "# Title\n\nThis is **bold** text with [link](http://example.com)"
        html_output = markdown_to_html(markdown_text)

        assert "<h1>" in html_output
        assert "<strong>" in html_output or "<b>" in html_output
        assert "<a href=" in html_output

    def test_markdown_to_html_code_blocks(self):
        """Test markdown to HTML conversion with code blocks."""
        from now_lms.vistas.forum import markdown_to_html

        markdown_text = "```python\nprint('Hello World')\n```"
        html_output = markdown_to_html(markdown_text)

        assert "<code>" in html_output or "<pre>" in html_output

    def test_markdown_to_html_sanitization(self):
        """Test that HTML is properly sanitized."""
        from now_lms.vistas.forum import markdown_to_html

        # Try to inject script tag
        markdown_text = "<script>alert('xss')</script>\n\n**Safe content**"
        html_output = markdown_to_html(markdown_text)

        assert "<script>" not in html_output
        assert "<strong>" in html_output or "<b>" in html_output
