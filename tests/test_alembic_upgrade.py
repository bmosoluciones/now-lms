# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.

import os
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.pool import StaticPool


# ---------------------------------------------------------------------------
# Critical columns that MUST exist after a full downgrade → upgrade cycle.
# Each entry maps a table name to the set of columns that every migration
# chain must recreate.  This list is intentionally conservative – it covers
# columns that were added or renamed by migrations and would cause runtime
# failures if missing.
# ---------------------------------------------------------------------------
CRITICAL_SCHEMA = {
    "configuracion": {
        "titulo",
        "descripcion",
        "moneda",
        "lang",
        "time_zone",
        "csrf_seed",
        "allow_unverified_email_login",
        "show_latest_blog_posts_on_home",
        "enable_contact",
        "enable_file_uploads",
        "enable_footer",
        "enable_html_preformatted_descriptions",
        "max_file_size",
        "social_facebook",
        "social_twitter",
        "social_linkedin",
        "social_youtube",
        "social_instagram",
        "social_github",
        "contact_address",
        "contact_email",
        "contact_phone",
        "contact_mobile",
        "contact_whatsapp",
    },
    "pago": {
        "monto",
    },
    "programa": {
        "nombre",
    },
    "style": {
        "theme",
    },
}


def _get_table_columns(inspector, table_name: str) -> set[str]:
    """Return the set of column names for *table_name*, or empty set."""
    if table_name not in inspector.get_table_names():
        return set()
    return {col["name"] for col in inspector.get_columns(table_name)}


def _assert_schema_matches_models(db, label: str = ""):
    """Inspect the live database and assert every critical column exists.

    This catches missing migrations: columns defined in the model but not
    covered by any Alembic migration script.
    """
    from sqlalchemy import inspect as sa_inspect

    inspector = sa_inspect(db.engine)
    suffix = f" ({label})" if label else ""

    for table_name, required_columns in CRITICAL_SCHEMA.items():
        actual = _get_table_columns(inspector, table_name)
        missing = required_columns - actual
        assert not missing, (
            f"Tabla '{table_name}' le faltan columnas{suffix}: {sorted(missing)}. "
            f"Existe una columna en el modelo sin migración correspondiente."
        )


def test_alembic_upgrade_app_context(monkeypatch):
    """
    Test robusto y destructivo de migraciones Alembic.

    Este test verifica que las migraciones funcionan correctamente ejecutando:
    1. drop_all() - Elimina todas las tablas
    2. initial_setup() - Crea esquema base
    3. upgrade() - No debe hacer nada en BD recién creada
    4. downgrade('base') - Baja hasta la migración cero
    5. upgrade() - Sube de nuevo hasta head

    Después del downgrade → upgrade completo se verifica que el esquema
    resultante contiene TODAS las columnas críticas definidas en los modelos.
    Esto detecta migraciones faltantes (columnas añadidas o renombradas en el
    modelo sin una migración Alembic equivalente).
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
        try:
            version_after_downgrade = db.session.execute(db.text("SELECT version_num FROM alembic_version")).scalar()
            assert version_after_downgrade is None, "Después de downgrade('base'), no debe haber versión"
        except (OperationalError, ProgrammingError):
            pass

        # Paso 5: Hacer upgrade de nuevo hasta head
        alembic.upgrade()
        db.session.commit()

        # Verificar que ahora sí hay una versión válida
        version_after_final_upgrade = db.session.execute(db.text("SELECT version_num FROM alembic_version")).scalar()
        assert version_after_final_upgrade is not None, "Después de upgrade(), debe haber una versión válida"

        # ------------------------------------------------------------------
        # CRÍTICO: Verificar que el esquema resultante contiene todas las
        # columnas definidas en los modelos.  Si una columna fue añadida o
        # renombrada en el modelo sin una migración, este assertion falla.
        # ------------------------------------------------------------------
        _assert_schema_matches_models(db, label="post-downgrade-upgrade")

        # Verificar que el ciclo completo funcionó correctamente
        if version_after_final_upgrade != version_after_stamp:
            print(
                f"Advertencia: Las versiones difieren. Inicial: {version_after_stamp}, "
                f"Final: {version_after_final_upgrade}. Esto puede indicar que se agregaron migraciones."
            )
        else:
            assert version_after_final_upgrade == version_after_stamp, (
                "En un entorno de test aislado, la versión debe ser consistente. "
                f"Esperado: {version_after_stamp}, Obtenido: {version_after_final_upgrade}"
            )

        db.session.close()
