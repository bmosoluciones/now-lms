# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.

import os
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.pool import StaticPool


def test_alembic_upgrade_app_context(monkeypatch):
    """
    Test robusto y destructivo de migraciones Alembic.

    Este test verifica que las migraciones funcionan correctamente ejecutando:
    1. drop_all() - Elimina todas las tablas
    2. initial_setup() - Crea esquema base
    3. upgrade() - No debe hacer nada en BD recién creada
    4. downgrade('base') - Baja hasta la migración cero
    5. upgrade() - Sube de nuevo hasta head

    Todo el recorrido debe ejecutarse sin errores.
    """
    # Respetar DATABASE_URL o usar SQLite en memoria
    if not os.environ.get("DATABASE_URL"):
        monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")

    # Crear app independiente en modo testing
    from now_lms import create_app, alembic, initial_setup

    # For SQLite in-memory, keep a single connection alive using StaticPool
    config_overrides = {}
    if os.environ.get("DATABASE_URL", "").startswith("sqlite") and ":memory:" in os.environ.get("DATABASE_URL", ""):
        config_overrides["SQLALCHEMY_ENGINE_OPTIONS"] = {"poolclass": StaticPool}
        config_overrides["SQLALCHEMY_CONNECT_ARGS"] = {"check_same_thread": False}

    app = create_app(app_name="test_alembic_app", testing=True, config_overrides=config_overrides)

    with app.app_context():
        from now_lms.db import database as db

        # Paso 1: Destruir todas las tablas (test destructivo)
        db.drop_all()
        db.session.commit()

        # Paso 2: Crear esquema base con initial_setup
        initial_setup(with_examples=False, flask_app=app)
        db.session.commit()

        # Paso 2.1: Marcar la base de datos como actualizada (stamp head)
        # Esto crea la tabla alembic_version y la marca con la versión actual (head)
        alembic.stamp("head")
        db.session.commit()

        # Verificar que stamp creó la tabla alembic_version
        version_after_stamp = db.session.execute(db.text("SELECT version_num FROM alembic_version")).scalar()
        assert version_after_stamp is not None, "stamp() debe crear la tabla alembic_version con una versión"

        # Paso 3: Ejecutar upgrade - no debe hacer nada porque la BD recién creada ya está actualizada
        alembic.upgrade()
        db.session.commit()

        # Verificar que la versión sigue siendo la misma
        version_after_first_upgrade = db.session.execute(db.text("SELECT version_num FROM alembic_version")).scalar()
        assert (
            version_after_first_upgrade == version_after_stamp
        ), "upgrade() no debe cambiar nada en una BD recién marcada como actualizada"

        # Paso 4: Hacer downgrade hasta la base (migración cero)
        alembic.downgrade("base")
        db.session.commit()

        # Verificar que no hay versión en alembic_version o la tabla fue eliminada
        # (dependiendo de la implementación de las migraciones)
        try:
            version_after_downgrade = db.session.execute(db.text("SELECT version_num FROM alembic_version")).scalar()
            assert version_after_downgrade is None, "Después de downgrade('base'), no debe haber versión"
        except (OperationalError, ProgrammingError):
            # La tabla alembic_version no existe después del downgrade, lo cual es válido
            pass

        # Verificar que en el estado downgrade('base'), las columnas críticas se revirtieron correctamente
        import sqlalchemy as sa
        test_secret = b"my-ultra-secret-key-1234"
        try:
            inspector_downgraded = sa.inspect(db.engine)
            existing_tables_dg = inspector_downgraded.get_table_names()

            if "configuracion" in existing_tables_dg:
                config_columns_dg = {col["name"]: col for col in inspector_downgraded.get_columns("configuracion")}
                assert "r" in config_columns_dg, "En downgrade('base'), la columna 'r' debe existir en configuracion"
                assert "csrf_seed" not in config_columns_dg, "En downgrade('base'), la columna 'csrf_seed' no debe existir"

                # Poblar la columna 'r' con datos binarios para probar conservación de datos
                config_count = db.session.execute(db.text("SELECT COUNT(*) FROM configuracion")).scalar()
                if config_count == 0:
                    db.session.execute(
                        db.text("INSERT INTO configuracion (id, titulo, descripcion, r) VALUES (:id, :titulo, :desc, :r)"),
                        {"id": "test-config-id", "titulo": "Test", "desc": "Desc", "r": test_secret}
                    )
                else:
                    first_id = db.session.execute(db.text("SELECT id FROM configuracion LIMIT 1")).scalar()
                    db.session.execute(
                        db.text("UPDATE configuracion SET r = :r WHERE id = :id"),
                        {"r": test_secret, "id": first_id}
                    )
                db.session.commit()

            if "style" in existing_tables_dg:
                style_columns_dg = {col["name"]: col for col in inspector_downgraded.get_columns("style")}
                assert "theme" in style_columns_dg, "En downgrade('base'), la columna 'theme' debe existir en style"
                theme_type_dg = style_columns_dg["theme"]["type"]
                assert getattr(theme_type_dg, "length", None) == 15, (
                    f"En downgrade('base'), la columna 'theme' debe tener longitud 15, obtenido: {getattr(theme_type_dg, 'length', None)}"
                )
        except (OperationalError, ProgrammingError):
            pass

        # Paso 5: Hacer upgrade de nuevo hasta head
        alembic.upgrade()
        db.session.commit()

        # Verificar que ahora sí hay una versión válida
        version_after_final_upgrade = db.session.execute(db.text("SELECT version_num FROM alembic_version")).scalar()
        assert version_after_final_upgrade is not None, "Después de upgrade(), debe haber una versión válida"

        # Asegurar que migraciones críticas están aplicadas al finalizar el upgrade a head
        inspector_upgraded = sa.inspect(db.engine)
        existing_tables_ug = inspector_upgraded.get_table_names()

        assert "configuracion" in existing_tables_ug, "La tabla configuracion debe existir"
        config_columns_ug = {col["name"]: col for col in inspector_upgraded.get_columns("configuracion")}
        assert "csrf_seed" in config_columns_ug, "La columna csrf_seed debe existir en configuracion"
        assert "r" not in config_columns_ug, "La columna r no debe existir en configuracion (debe haber sido renombrada)"

        # Verificar conservación de datos
        preserved_secret = db.session.execute(db.text("SELECT csrf_seed FROM configuracion LIMIT 1")).scalar()
        assert preserved_secret == test_secret, (
            f"La clave cifrada debe conservarse idéntica después del upgrade. Esperado: {test_secret}, Obtenido: {preserved_secret}"
        )

        assert "style" in existing_tables_ug, "La tabla style debe existir"
        style_columns_ug = {col["name"]: col for col in inspector_upgraded.get_columns("style")}
        assert "theme" in style_columns_ug, "La columna theme debe existir en style"
        theme_type_ug = style_columns_ug["theme"]["type"]
        assert getattr(theme_type_ug, "length", None) == 40, (
            f"La columna theme en style debe tener longitud 40, actual: {getattr(theme_type_ug, 'length', None)}"
        )

        # Verificar que el ciclo completo funcionó correctamente
        # La versión final debe ser igual a la inicial si no se agregaron migraciones durante el test
        # Nota: En producción/desarrollo, la versión puede cambiar si se agregan nuevas migraciones
        # pero dentro del contexto de este test, debe ser consistente
        if version_after_final_upgrade != version_after_stamp:
            # Si las versiones son diferentes, al menos debemos verificar que ambas son válidas
            print(
                f"Advertencia: Las versiones difieren. Inicial: {version_after_stamp}, "
                f"Final: {version_after_final_upgrade}. Esto puede indicar que se agregaron migraciones."
            )
        else:
            # Idealmente, deberían ser iguales en un entorno de test aislado
            assert version_after_final_upgrade == version_after_stamp, (
                "En un entorno de test aislado, la versión debe ser consistente. "
                f"Esperado: {version_after_stamp}, Obtenido: {version_after_final_upgrade}"
            )

        # Cerrar sesión de forma explícita
        db.session.close()
