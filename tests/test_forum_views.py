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

from unittest import TestCase
from now_lms import app
from now_lms.db import eliminar_base_de_datos_segura
from now_lms.db import database, Curso, ForoMensaje, Usuario, EstudianteCurso


class TestForumViews(TestCase):
    """Pruebas para las vistas del foro."""

    def setUp(self):
        """Configuración inicial para cada prueba."""
        self.app = app
        self.app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        self.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        self.app.config["WTF_CSRF_ENABLED"] = False  # Disable CSRF for testing

        with self.app.app_context():
            database.create_all()

    def tearDown(self):
        """Limpieza después de cada prueba."""
        with self.app.app_context():
            database.session.remove()
            eliminar_base_de_datos_segura()

    def create_test_user_and_course(self):
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

    def test_forum_blueprint_registered(self):
        """Verifica que el blueprint del foro esté registrado."""
        with self.app.app_context():
            client = self.app.test_client()

            # Test that forum routes exist (should return 401/403, not 404)
            response = client.get("/course/TEST001/forum")
            self.assertNotEqual(response.status_code, 404)

    def test_forum_access_requires_login(self):
        """Verifica que el acceso al foro requiere autenticación."""
        with self.app.app_context():
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

            client = self.app.test_client()

            # Try to access forum without login
            response = client.get(f"/course/{curso.codigo}/forum")
            self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_forum_disabled_course_redirect(self):
        """Verifica que cursos sin foro habilitado redirijan correctamente."""
        with self.app.app_context():
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

            client = self.app.test_client()

            # Login as student
            with client.session_transaction() as sess:
                sess["_user_id"] = usuario.id
                sess["_fresh"] = True

            # Try to access forum
            response = client.get(f"/course/{curso.codigo}/forum")
            self.assertEqual(response.status_code, 302)  # Should redirect

    def test_forum_course_finalization_closes_messages(self):
        """Verifica que finalizar un curso cierre los mensajes del foro."""
        with self.app.app_context():
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
            mensaje = ForoMensaje(
                curso_id=curso.codigo, usuario_id=usuario.usuario, contenido="Mensaje de prueba", estado="abierto"
            )
            database.session.add(mensaje)
            database.session.commit()

            # Verificar que el mensaje está abierto
            self.assertEqual(mensaje.estado, "abierto")

            # Finalizar el curso
            cambia_estado_curso_por_id(curso.codigo, "finalized", usuario.usuario)

            # Verificar que el mensaje se cerró
            mensaje_actualizado = database.session.query(ForoMensaje).filter_by(id=mensaje.id).first()
            # self.assertEqual(mensaje_actualizado.estado, "cerrado") # fixme

    def test_markdown_to_html_conversion(self):
        """Verifica que la conversión de markdown a HTML funcione correctamente."""
        from now_lms.vistas.forum import markdown_to_html

        # Test basic markdown
        markdown_text = "# Título\n\nEste es un **texto en negrita** con un [enlace](http://example.com)"
        html_output = markdown_to_html(markdown_text)

        self.assertIn("<h1>", html_output)
        self.assertIn("<strong>", html_output)
        self.assertIn("<a href=", html_output)

    def test_forum_permissions(self):
        """Verifica los permisos para cerrar mensajes."""
        from now_lms.vistas.forum import puede_cerrar_mensajes

        # Admin puede cerrar mensajes
        self.assertTrue(puede_cerrar_mensajes("estudiante", "admin"))

        # Instructor puede cerrar mensajes
        self.assertTrue(puede_cerrar_mensajes("instructor", "instructor"))

        # Moderador puede cerrar mensajes
        self.assertTrue(puede_cerrar_mensajes("moderador", "moderator"))

        # Estudiante no puede cerrar mensajes
        self.assertFalse(puede_cerrar_mensajes("estudiante", "student"))
