# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""
Configuración de pytest para NOW LMS.

Fixtures simples y claras para facilitar los tests.
Soporta SQLite, MySQL y PostgreSQL.

Estrategia:
- SQLite (archivo temporal): app y base de datos frescas por test (ver
  ``_fresh_sqlite_url`` para el motivo por el que NO se usa ``:memory:``).
- MySQL/PostgreSQL: app y tablas se crean una vez por sesión; entre tests
  se limpian las tablas con TRUNCATE y se re-pueblan los datos iniciales.
  Esto evita el costo de DROP/CREATE TABLE por test.
"""

import os
import shutil
import tempfile

import pytest

# DATABASE_URL provisto por el operador (p. ej. MySQL/PostgreSQL en CI).
# Se captura al importar el conftest, ANTES de que los fixtures lo sobrescriban
# con la ruta temporal de cada test.
_EXTERNAL_DATABASE_URL = os.environ.get("DATABASE_URL")


def _set_env():
    """Configura las variables de entorno comunes a todos los tests."""
    os.environ["CI"] = "True"
    os.environ["SECRET_KEY"] = "test-secret-key"
    os.environ["LOG_LEVEL"] = "ERROR"


def _is_sqlite(url: str) -> bool:
    """Retorna True si la URL corresponde a SQLite."""
    return "sqlite" in url


def _external_engine_url():
    """URL de un motor real (MySQL/PostgreSQL) provisto por el operador, si lo hay.

    Un DATABASE_URL de SQLite se ignora a propósito: la suite administra su
    propio archivo temporal por test (ver ``_fresh_sqlite_url``).
    """
    if _EXTERNAL_DATABASE_URL and not _is_sqlite(_EXTERNAL_DATABASE_URL):
        return _EXTERNAL_DATABASE_URL
    return None


def _directorio_temporal_para_db() -> str:
    """Crea el directorio temporal que alojará la base de datos de UN test.

    Se prefiere un directorio respaldado por RAM (``/dev/shm`` en Linux) cuando
    está disponible: el archivo sigue siendo un archivo real - que es lo que
    hace falta para sobrevivir a la invalidación de conexión descrita en
    ``_fresh_sqlite_url`` - pero sin tocar disco. La diferencia no es marginal:
    el bootstrap por test (``create_all()`` de ~70 tablas más los datos
    iniciales) baja de ~12 s a ~1 s.

    Si no existe o no es escribible se usa el temporal por defecto del sistema;
    la suite sigue siendo correcta, sólo más lenta.
    """
    respaldado_en_ram = "/dev/shm"
    if os.path.isdir(respaldado_en_ram) and os.access(respaldado_en_ram, os.W_OK):
        return tempfile.mkdtemp(prefix="now-lms-test-db-", dir=respaldado_en_ram)
    return tempfile.mkdtemp(prefix="now-lms-test-db-")


def _fresh_sqlite_url(directorio: str) -> str:
    """Retorna la URL de un SQLite en archivo, exclusivo de un test.

    NO USAR ``sqlite:///:memory:`` AQUÍ.

    flask-alembic registra un ``teardown_appcontext`` (``_Cache.clear``) que
    llama ``context.connection.invalidate()`` sobre la conexión que usó la
    última operación de Alembic. ``initial_setup()`` ejecuta ``alembic.stamp()``,
    así que a partir de ese momento existe una conexión cacheada y CUALQUIER
    salida de un application context la invalida.

    Con un SQLite en memoria esa conexión *es* la base de datos completa
    (StaticPool mantiene una sola): invalidarla descarta el esquema y los datos
    recién creados, y la siguiente conexión abre una base vacía. El síntoma era
    ``OperationalError: no such table: ad_sense`` durante el setup del fixture
    (``ad_sense`` es simplemente la primera tabla del flush en orden alfabético,
    no la única ausente: no quedaba ninguna).

    Con un archivo, invalidar la conexión sólo fuerza una reconexión y el
    esquema sigue en disco, que es la suposición que hace flask-alembic.
    """
    return "sqlite:///" + os.path.join(directorio, "now_lms_test.db")


def _drop_all(app):
    """Elimina todas las tablas."""
    from now_lms.db import database

    url = app.config.get("SQLALCHEMY_DATABASE_URI", "")
    with app.app_context():
        database.session.remove()
        try:
            with database.engine.connect() as conn:
                if url.startswith("mysql"):
                    conn.execute(database.text("SET FOREIGN_KEY_CHECKS=0"))
                database.metadata.drop_all(conn)
                if url.startswith("mysql"):
                    conn.execute(database.text("SET FOREIGN_KEY_CHECKS=1"))
                conn.commit()
        except Exception:
            pass


def _truncate_all(app):
    """Elimina todos los datos de todas las tablas sin borrar el esquema."""
    from now_lms.db import database

    url = app.config.get("SQLALCHEMY_DATABASE_URI", "")
    with app.app_context():
        database.session.remove()
        with database.engine.connect() as conn:
            if url.startswith("mysql"):
                conn.execute(database.text("SET FOREIGN_KEY_CHECKS=0"))
                for table in reversed(database.metadata.sorted_tables):
                    conn.execute(database.text(f"TRUNCATE TABLE {table.name}"))
                conn.execute(database.text("SET FOREIGN_KEY_CHECKS=1"))
            elif "postgresql" in url:
                table_names = ", ".join(f'"{t.name}"' for t in database.metadata.tables.values())
                if table_names:
                    conn.execute(database.text(f"TRUNCATE TABLE {table_names} RESTART IDENTITY CASCADE"))
            conn.commit()


def _configure_sqlite_pragmas(app):
    """Aplica pragmas de rendimiento para SQLite en memoria."""
    from now_lms.db import database

    with app.app_context():
        database.session.execute(database.text("PRAGMA journal_mode=MEMORY"))
        database.session.execute(database.text("PRAGMA synchronous=OFF"))
        database.session.execute(database.text("PRAGMA cache_size=-10000"))
        database.session.execute(database.text("PRAGMA temp_store=MEMORY"))
        database.session.commit()


# ---------------------------------------------------------------------------
# Fixture de sesión para motores reales: crea app y tablas una sola vez
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def _session_real_app():
    """Crea app y tablas una sola vez para MySQL/PostgreSQL."""
    _set_env()
    url = _external_engine_url()

    if url is None:
        yield None
        return

    os.environ["DATABASE_URL"] = url

    from now_lms import create_app, init_app
    from now_lms.db import database

    app = create_app()
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    init_app(flask_app=app)

    yield app

    _drop_all(app)
    with app.app_context():
        database.engine.dispose()


# ---------------------------------------------------------------------------
# Fixture principal: selecciona estrategia según el motor
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def app(_session_real_app):
    """
    Proporciona una aplicación aislada para cada test.

    - SQLite: app y archivo de base de datos frescos por test.
    - MySQL/PostgreSQL: app de sesión con limpieza TRUNCATE entre tests.
    """
    _set_env()

    if _external_engine_url() is None:
        # SQLite: cada test recibe su propio archivo temporal.
        from now_lms import create_app, init_app
        from now_lms.db import database

        directorio = _directorio_temporal_para_db()
        anterior = os.environ.get("DATABASE_URL")
        os.environ["DATABASE_URL"] = _fresh_sqlite_url(directorio)

        try:
            new_app = create_app()
            new_app.config["TESTING"] = True
            new_app.config["WTF_CSRF_ENABLED"] = False
            init_app(flask_app=new_app)
            _configure_sqlite_pragmas(new_app)

            yield new_app
        finally:
            # El engine debe soltar el archivo antes de borrar el directorio, y
            # DATABASE_URL debe volver a su valor previo: los tests que leen la
            # variable directamente no deben ver una ruta ya eliminada.
            try:
                with new_app.app_context():
                    try:
                        database.session.rollback()
                    except Exception:
                        pass
                    database.session.remove()
                    database.engine.dispose()
            except (NameError, UnboundLocalError):
                pass

            if anterior is None:
                os.environ.pop("DATABASE_URL", None)
            else:
                os.environ["DATABASE_URL"] = anterior

            shutil.rmtree(directorio, ignore_errors=True)
    else:
        # MySQL/PostgreSQL: limpiar tablas con TRUNCATE y re-poblar datos.
        from now_lms import init_app
        from now_lms.db import database

        _truncate_all(_session_real_app)
        # init_app detecta que la DB no está poblada y re-carga datos iniciales
        init_app(flask_app=_session_real_app)

        yield _session_real_app

        with _session_real_app.app_context():
            try:
                database.session.rollback()
            except Exception:
                pass
            database.session.remove()


@pytest.fixture(scope="function")
def client(app):
    """Cliente HTTP para hacer requests a la aplicación."""
    return app.test_client()


@pytest.fixture(scope="function")
def db_session(app):
    """
    Sesión de base de datos para el test.

    init_app() ya creó tablas y datos iniciales.
    Este fixture solo limpia al final del test.
    """
    from now_lms.db import database

    with app.app_context():
        yield database.session
        try:
            database.session.rollback()
        except Exception:
            pass
        database.session.remove()
