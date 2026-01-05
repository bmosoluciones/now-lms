# Copyright 2022 - 2024 BMO Soluciones, S.A.
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
"""
Tests para modelos de base de datos.

Cada test crea sus propios datos, los valida y se limpian automáticamente.
"""

from datetime import datetime, timedelta


def test_crear_usuario(app, db_session):
    """Se debe poder crear un usuario en la base de datos."""
    from now_lms.auth import proteger_passwd
    from now_lms.db import Usuario

    # Crear usuario con campos mínimos
    user = Usuario(
        usuario="testuser",
        acceso=proteger_passwd("password123"),
        nombre="Test",
        correo_electronico="test@example.com",
        tipo="student",
        activo=True,
    )

    db_session.add(user)
    db_session.commit()

    # Verificar que se creó
    found = db_session.query(Usuario).filter_by(usuario="testuser").first()
    assert found is not None
    assert found.nombre == "Test"


def test_crear_curso(app, db_session):
    """Se debe poder crear un curso en la base de datos."""
    from now_lms.db import Curso

    # Crear curso
    curso = Curso(
        nombre="Curso de Prueba",
        codigo="TEST001",
        descripcion_corta="Un curso de prueba",
        descripcion="Descripción completa del curso de prueba",
        estado="open",
        certificado=False,
        publico=True,
        duracion=7,
        nivel=1,
        auditable=False,
        portada=False,
        fecha_inicio=datetime.now() + timedelta(days=7),
        fecha_fin=datetime.now() + timedelta(days=14),
    )

    db_session.add(curso)
    db_session.commit()

    # Verificar que se creó
    found = db_session.query(Curso).filter_by(codigo="TEST001").first()
    assert found is not None
    assert found.nombre == "Curso de Prueba"


def test_crear_categoria(app, db_session):
    """Se debe poder crear una categoría en la base de datos."""
    from now_lms.db import Categoria

    # Crear categoría
    categoria = Categoria(
        nombre="Categoría de Prueba",
        descripcion="Una categoría de prueba",
    )

    db_session.add(categoria)
    db_session.commit()

    # Verificar que se creó
    found = db_session.query(Categoria).filter_by(nombre="Categoría de Prueba").first()
    assert found is not None
    assert found.descripcion == "Una categoría de prueba"
