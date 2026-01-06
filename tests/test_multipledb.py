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
Tests específicos para múltiples motores de base de datos.

Este archivo solo ejecuta tests cuando:
1. La variable de entorno CI está establecida
2. DATABASE_URL contiene una conexión válida a PostgreSQL o MySQL

Los tests en este archivo validan que la aplicación funciona
correctamente con diferentes motores de base de datos.
"""

import os

import pytest


def is_ci_environment():
    """Verifica si estamos en entorno CI."""
    return os.environ.get("CI", "").lower() in ("true", "1", "yes")


def get_database_type():
    """
    Obtiene el tipo de base de datos desde DATABASE_URL.

    Returns:
        str: 'postgresql', 'mysql', 'sqlite', o None si no está configurado
    """
    db_url = os.environ.get("DATABASE_URL", "")

    if not db_url:
        return None

    if "postgresql" in db_url.lower():
        return "postgresql"
    elif "mysql" in db_url.lower():
        return "mysql"
    elif "sqlite" in db_url.lower():
        return "sqlite"

    return None


def should_run_multidb_tests():
    """
    Determina si deben ejecutarse los tests de múltiples bases de datos.

    Returns:
        bool: True si CI está configurado y hay una base de datos PostgreSQL o MySQL
    """
    if not is_ci_environment():
        return False

    db_type = get_database_type()
    return db_type in ("postgresql", "mysql")


# Skip todos los tests en este archivo si no cumple los requisitos
pytestmark = pytest.mark.skipif(
    not should_run_multidb_tests(), reason="Tests de múltiples DB solo se ejecutan en CI con PostgreSQL o MySQL configurado"
)


class TestMultipleDatabaseSupport:
    """Tests para validar soporte de múltiples bases de datos."""

    def test_database_connection(self, app):
        """Verifica que la aplicación puede conectarse a la base de datos."""
        from now_lms.db import database

        with app.app_context():
            # Intentar una consulta simple
            result = database.session.execute(database.text("SELECT 1")).scalar()
            assert result == 1

    def test_database_type_is_correct(self, app):
        """Verifica que el tipo de base de datos es el esperado."""
        db_type = get_database_type()
        expected_types = ("postgresql", "mysql")

        assert db_type in expected_types, f"Tipo de BD esperado: {expected_types}, obtenido: {db_type}"

    def test_create_tables(self, app, db_session):
        """Verifica que se pueden crear tablas en la base de datos."""
        from now_lms.db import Usuario, Curso, Categoria

        # Verificar que las tablas existen consultándolas
        usuarios = db_session.query(Usuario).count()
        cursos = db_session.query(Curso).count()
        categorias = db_session.query(Categoria).count()

        # No importa el número, solo que las queries funcionan
        assert usuarios >= 0
        assert cursos >= 0
        assert categorias >= 0

    def test_create_user(self, app, db_session):
        """Verifica que se puede crear un usuario en la base de datos."""
        from now_lms.auth import proteger_passwd
        from now_lms.db import Usuario

        # Crear usuario
        user = Usuario(
            id="multidb-test-user-001",
            usuario="multidb-testuser",
            acceso=proteger_passwd("test123"),
            nombre="MultiDB",
            apellido="Test",
            correo_electronico="multidb@test.com",
            tipo="student",
            activo=True,
            visible=True,
            correo_electronico_verificado=True,
        )

        db_session.add(user)
        db_session.commit()

        # Verificar que se creó
        found_user = db_session.query(Usuario).filter_by(usuario="multidb-testuser").first()
        assert found_user is not None
        assert found_user.nombre == "MultiDB"
        assert found_user.apellido == "Test"

        # Limpiar
        db_session.delete(found_user)
        db_session.commit()

    def test_create_course(self, app, db_session):
        """Verifica que se puede crear un curso en la base de datos."""
        from now_lms.db import Curso
        from datetime import datetime, timedelta

        # Crear curso
        course = Curso(
            id="multidb-test-course-001",
            nombre="Test Course MultiDB",
            codigo="TESTMULTIDB",
            descripcion_corta="Test course for multiple databases",
            descripcion="A test course to validate multiple database support",
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

        db_session.add(course)
        db_session.commit()

        # Verificar que se creó
        found_course = db_session.query(Curso).filter_by(codigo="TESTMULTIDB").first()
        assert found_course is not None
        assert found_course.nombre == "Test Course MultiDB"

        # Limpiar
        db_session.delete(found_course)
        db_session.commit()

    def test_database_transactions(self, app, db_session):
        """Verifica que las transacciones funcionan correctamente."""
        from now_lms.auth import proteger_passwd
        from now_lms.db import Usuario

        # Crear usuario
        user = Usuario(
            id="multidb-transaction-test-001",
            usuario="transaction-test",
            acceso=proteger_passwd("test123"),
            nombre="Transaction",
            apellido="Test",
            correo_electronico="transaction@test.com",
            tipo="student",
            activo=True,
            visible=True,
            correo_electronico_verificado=True,
        )

        db_session.add(user)
        db_session.commit()

        # Verificar que existe
        assert db_session.query(Usuario).filter_by(usuario="transaction-test").count() == 1

        # Hacer un rollback
        user.nombre = "Modified"
        db_session.rollback()

        # Verificar que no se guardó el cambio
        found_user = db_session.query(Usuario).filter_by(usuario="transaction-test").first()
        assert found_user.nombre == "Transaction"

        # Limpiar
        db_session.delete(found_user)
        db_session.commit()

    def test_query_filtering(self, app, db_session):
        """Verifica que el filtrado de queries funciona en la base de datos."""
        from now_lms.auth import proteger_passwd
        from now_lms.db import Usuario

        # Crear múltiples usuarios
        users = [
            Usuario(
                id=f"multidb-filter-test-{i:03d}",
                usuario=f"filtertest{i}",
                acceso=proteger_passwd("test123"),
                nombre=f"User{i}",
                apellido="Filter",
                correo_electronico=f"filter{i}@test.com",
                tipo="student" if i % 2 == 0 else "instructor",
                activo=True,
                visible=True,
                correo_electronico_verificado=True,
            )
            for i in range(5)
        ]

        for user in users:
            db_session.add(user)
        db_session.commit()

        # Filtrar por tipo
        students = db_session.query(Usuario).filter_by(tipo="student").filter(Usuario.usuario.like("filtertest%")).all()

        instructors = db_session.query(Usuario).filter_by(tipo="instructor").filter(Usuario.usuario.like("filtertest%")).all()

        assert len(students) == 3  # 0, 2, 4
        assert len(instructors) == 2  # 1, 3

        # Limpiar
        for user in users:
            db_session.delete(user)
        db_session.commit()

    def test_database_constraints(self, app, db_session):
        """Verifica que las restricciones de base de datos funcionan."""
        from now_lms.auth import proteger_passwd
        from now_lms.db import Usuario
        from sqlalchemy.exc import IntegrityError

        # Crear usuario
        user1 = Usuario(
            id="multidb-constraint-test-001",
            usuario="constraint-test",
            acceso=proteger_passwd("test123"),
            nombre="Constraint",
            apellido="Test",
            correo_electronico="constraint@test.com",
            tipo="student",
            activo=True,
            visible=True,
            correo_electronico_verificado=True,
        )

        db_session.add(user1)
        db_session.commit()

        # Intentar crear usuario con mismo ID (debe fallar)
        user2 = Usuario(
            id="multidb-constraint-test-001",  # Mismo ID
            usuario="constraint-test-2",
            acceso=proteger_passwd("test123"),
            nombre="Constraint2",
            apellido="Test2",
            correo_electronico="constraint2@test.com",
            tipo="student",
            activo=True,
            visible=True,
            correo_electronico_verificado=True,
        )

        with pytest.raises(IntegrityError):
            db_session.add(user2)
            db_session.commit()

        # Rollback para limpiar el error
        db_session.rollback()

        # Limpiar
        db_session.delete(user1)
        db_session.commit()


class TestDatabaseSpecificFeatures:
    """Tests para características específicas de cada base de datos."""

    def test_postgresql_specific_features(self, app):
        """Tests específicos para PostgreSQL."""
        db_type = get_database_type()

        if db_type != "postgresql":
            pytest.skip("Test solo para PostgreSQL")

        from now_lms.db import database

        with app.app_context():
            # Verificar que estamos usando PostgreSQL
            result = database.session.execute(database.text("SELECT version()")).scalar()
            assert "PostgreSQL" in result

    def test_mysql_specific_features(self, app):
        """Tests específicos para MySQL."""
        db_type = get_database_type()

        if db_type != "mysql":
            pytest.skip("Test solo para MySQL")

        from now_lms.db import database

        with app.app_context():
            # Verificar que estamos usando MySQL
            result = database.session.execute(database.text("SELECT version()")).scalar()
            assert any(x in result.lower() for x in ["mysql", "mariadb"])
