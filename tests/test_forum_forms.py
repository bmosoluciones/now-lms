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

"""Pruebas para la validación de formularios del foro."""

from unittest import TestCase
from now_lms import app
from now_lms.forms import CurseForm


class TestForumFormValidation(TestCase):
    """Pruebas para la validación de formularios."""

    def setUp(self):
        """Configuración inicial para cada prueba."""
        self.app = app
        self.app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        self.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        self.app.config["WTF_CSRF_ENABLED"] = False

    def test_course_form_forum_validation_self_paced(self):
        """Verifica que el formulario valide correctamente cursos self-paced."""
        with self.app.app_context():
            form_data = {
                "nombre": "Curso de Prueba",
                "codigo": "TEST001",
                "descripcion_corta": "Descripción corta",
                "descripcion": "Descripción completa del curso",
                "modalidad": "self_paced",
                "foro_habilitado": True,  # Esto debería fallar
                "nivel": "1",
                "duracion": "40",
                "publico": False,
                "limitado": False,
                "pagado": False,
                "auditable": False,
                "certificado": False,
                "precio": "0",
            }

            form = CurseForm(data=form_data)
            # Set choices manually for test
            form.plantilla_certificado.choices = [("", "-- Seleccionar --")]

            # El formulario no debería ser válido debido a la validación personalizada
            try:
                is_valid = form.validate()
                self.assertFalse(is_valid)
                # Si no se lanza excepción, debería haber un error en el campo
                self.assertIn("foro_habilitado", form.errors)
            except ValueError as e:
                # La excepción es esperada
                self.assertIn("self-paced", str(e))

    def test_course_form_forum_validation_time_based(self):
        """Verifica que el formulario permita foro en cursos time-based."""
        with self.app.app_context():
            form_data = {
                "nombre": "Curso de Prueba",
                "codigo": "TEST002",
                "descripcion_corta": "Descripción corta",
                "descripcion": "Descripción completa del curso",
                "modalidad": "time_based",
                "foro_habilitado": True,  # Esto debería ser válido
                "nivel": "1",
                "duracion": "40",
                "publico": False,
                "limitado": False,
                "pagado": False,
                "auditable": False,
                "certificado": False,
                "precio": "0",
            }

            form = CurseForm(data=form_data)
            # Set choices manually for test
            form.plantilla_certificado.choices = [("", "-- Seleccionar --")]

            # El formulario debería ser válido para el campo foro_habilitado
            # (otros campos pueden fallar por otras validaciones)
            try:
                form.validate()
                # Si no se lanza excepción, verificamos que NO haya error en foro_habilitado
                self.assertNotIn("foro_habilitado", form.errors)
            except ValueError:
                # No debería haber excepción de validación para foro_habilitado
                self.fail("No debería haber error de validación para time_based con foro habilitado")

    def test_course_form_forum_validation_self_paced_disabled(self):
        """Verifica que cursos self-paced con foro deshabilitado sean válidos."""
        with self.app.app_context():
            form_data = {
                "nombre": "Curso de Prueba",
                "codigo": "TEST003",
                "descripcion_corta": "Descripción corta",
                "descripcion": "Descripción completa del curso",
                "modalidad": "self_paced",
                "foro_habilitado": False,  # Esto debería ser válido
                "nivel": "1",
                "duracion": "40",
                "publico": False,
                "limitado": False,
                "pagado": False,
                "auditable": False,
                "certificado": False,
                "precio": "0",
            }

            form = CurseForm(data=form_data)
            # Set choices manually for test
            form.plantilla_certificado.choices = [("", "-- Seleccionar --")]

            # El formulario debería ser válido para el campo foro_habilitado
            try:
                form.validate()
                # Si no se lanza excepción, verificamos que NO haya error en foro_habilitado
                self.assertNotIn("foro_habilitado", form.errors)
            except ValueError:
                # No debería haber excepción de validación para foro_habilitado
                self.fail("No debería haber error de validación para self_paced con foro deshabilitado")
