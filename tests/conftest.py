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

"""Shared test configuration and fixtures."""

import pytest
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError, ProgrammingError, IntegrityError
from pg8000.dbapi import ProgrammingError as PGProgrammingError
from pg8000.exceptions import DatabaseError

from now_lms import log


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Enable foreign key constraints in SQLite for test consistency with MySQL."""
    if "sqlite" in str(dbapi_connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


DB_URL = "sqlite:///:memory:"

log.info(f"Using test database URL: {DB_URL}")


def create_app(testing=True, database_uri=None, minimal=False):
    """Create Flask application with test configuration (factory pattern)."""
    from now_lms import lms_app
    from now_lms.config import CONFIGURACION

    app = lms_app

    # Base configuration
    app.config.from_mapping(CONFIGURACION)

    if testing:
        app.config.update(
            {
                "TESTING": True,
                "SECRET_KEY": "test-secret-key-for-testing",
                "SQLALCHEMY_TRACK_MODIFICATIONS": False,
                "WTF_CSRF_ENABLED": False,
                "DEBUG": True,
                "PRESERVE_CONTEXT_ON_EXCEPTION": True,
                "MAIL_SUPPRESS_SEND": True,
                "SERVER_NAME": "localhost.localdomain",
                "APPLICATION_ROOT": "/",
                "PREFERRED_URL_SCHEME": "http",
            }
        )

    if database_uri:
        app.config["SQLALCHEMY_DATABASE_URI"] = database_uri

    return app


@pytest.fixture(scope="session")
def database_url():
    """Provide the database URL for tests."""
    return DB_URL


@pytest.fixture(scope="function")
def app():
    """Create a Flask app for testing with proper setup and teardown."""
    # Use the existing LMS app but configure it for testing
    from now_lms import lms_app

    # Store original config
    original_config = dict(lms_app.config)

    # Configure for testing
    lms_app.config.update(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret-key-for-testing",
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
            "WTF_CSRF_ENABLED": False,
            "DEBUG": True,
            "PRESERVE_CONTEXT_ON_EXCEPTION": True,
            "MAIL_SUPPRESS_SEND": True,
            "SERVER_NAME": "localhost.localdomain",
            "APPLICATION_ROOT": "/",
            "PREFERRED_URL_SCHEME": "http",
            "SQLALCHEMY_DATABASE_URI": DB_URL,
        }
    )

    # Initialize database with the app context
    with lms_app.app_context():
        from now_lms import database

        database.create_all()

    yield lms_app

    # Clean teardown - this is the key to fixing MySQL hanging
    with lms_app.app_context():
        from now_lms import database

        try:
            # Ensure session is properly closed
            database.session.remove()
            # Drop all tables
            database.drop_all()
            # Dispose of the engine and all connections
            database.engine.dispose()
        except Exception as e:
            log.warning(f"Database cleanup error: {e}")

    # Restore original config
    lms_app.config.clear()
    lms_app.config.update(original_config)


@pytest.fixture(scope="function")
def client(app):
    """Flask test client."""
    return app.test_client()


@pytest.fixture(scope="function")
def db_session(app):
    """Database session with proper cleanup for each test."""
    app.config["SQLALCHEMY_DATABASE_URI"] = DB_URL
    with app.app_context():
        from now_lms import database

        yield database.session  # Use the regular Flask-SQLAlchemy session

        # Cleanup after each test - this ensures no hanging connections
        try:
            database.session.rollback()
            database.session.remove()
        except Exception as e:
            log.warning(f"Session cleanup error: {e}")


@pytest.fixture
def lms_application(database_url):
    """Legacy fixture for backwards compatibility."""
    test_app = create_app(testing=True, database_uri=database_url)
    test_app.config["SQLALCHEMY_DATABASE_URI"] = database_url

    # Initialize database within the test app context to ensure proper setup
    with test_app.app_context():
        from now_lms import database

        database.create_all()

    yield test_app

    # Clean teardown
    with test_app.app_context():
        from now_lms import database

        try:
            database.session.remove()
            database.drop_all()
            database.engine.dispose()
        except Exception as e:
            log.warning(f"Database cleanup error in lms_application: {e}")


@pytest.fixture(scope="function")
def minimal_db_setup(app, db_session):
    """
    Minimal database setup that only creates schema without full data population.
    Includes essential certificate templates needed for course creation.
    Use this for tests that don't need the complete database setup.
    """
    # Add essential certificate templates needed for course creation
    with app.app_context():
        try:
            from now_lms.db.initial_data import crear_certificados

            crear_certificados()
        except Exception as e:
            log.warning(f"Minimal setup certificate creation error: {e}")

    # db_session already provides isolated session, just return the app
    yield app


@pytest.fixture(scope="function")
def full_db_setup(app, db_session):
    """
    Full database setup with complete data population.
    Use this for tests that need the complete populated database (like test_vistas).
    """
    app.config["SQLALCHEMY_DATABASE_URI"] = DB_URL
    with app.app_context():
        try:
            # Directly create the setup data in the correct app context
            from now_lms.db.tools import crear_configuracion_predeterminada
            from now_lms.db.initial_data import (
                crear_certificados,
                crear_curso_predeterminado,
                crear_usuarios_predeterminados,
                crear_certificacion,
            )

            # Setup data that's needed for tests
            crear_configuracion_predeterminada()
            crear_certificados()
            crear_curso_predeterminado()
            crear_usuarios_predeterminados()
            crear_certificacion()

            # Create test data
            from now_lms.db.data_test import crear_data_para_pruebas

            crear_data_para_pruebas()

            log.debug("Full database setup completed.")
        except (OperationalError, ProgrammingError, PGProgrammingError, DatabaseError, IntegrityError) as e:
            log.warning(f"Full database setup error (continuing): {e}")

    yield app  # Return the application with the full database setup


@pytest.fixture(scope="function")
def full_db_setup_with_examples(app, db_session):
    """
    Full database setup with complete data population including examples.
    Use this for tests that need the complete populated database with examples.
    """
    from now_lms import initial_setup

    app.config["SQLALCHEMY_DATABASE_URI"] = DB_URL
    with app.app_context():
        try:
            # Full database setup with test data and examples
            initial_setup(with_tests=True, with_examples=True)
            log.debug("Full database setup with examples completed.")
        except (OperationalError, ProgrammingError, PGProgrammingError, DatabaseError, IntegrityError) as e:
            log.warning(f"Full database setup error (continuing): {e}")

    yield app  # Return the application with the full database setup


@pytest.fixture(scope="function")
def basic_config_setup(app, db_session):
    """
    Basic configuration setup that only creates essential configuration.
    Includes essential certificate templates needed for course creation.
    For tests that need basic config but not full database.
    """
    from now_lms.db.tools import crear_configuracion_predeterminada
    from now_lms.db.initial_data import crear_certificados

    app.config["SQLALCHEMY_DATABASE_URI"] = DB_URL
    with app.app_context():
        try:
            # Only create basic configuration
            crear_configuracion_predeterminada()
            # Add essential certificate templates needed for course creation
            crear_certificados()
            log.debug("Basic configuration setup completed.")
        except (OperationalError, ProgrammingError, PGProgrammingError, DatabaseError, IntegrityError) as e:
            log.warning(f"Basic config setup error (continuing): {e}")

    yield app  # Return the application with basic configuration


def pytest_configure(config):
    import sys

    sys._called_from_test = True  # This flag is accessible globally


def pytest_unconfigure(config):
    import sys  # This was missing from the manual

    del sys._called_from_test


# ==================================================================================
# Session-scoped fixtures for improved test performance
# These fixtures are completely independent from function-scoped fixtures
# ==================================================================================


@pytest.fixture(scope="session")
def session_basic_db_setup():
    """
    Session-scoped basic database setup with minimal data population.
    Use this for read-only tests that need basic database setup.
    Creates a completely independent app and database.
    Always uses SQLite in-memory for complete isolation between session fixtures.
    """
    from now_lms import create_app

    # Always use in-memory SQLite for session fixtures to avoid interference
    database_uri = "sqlite:///:memory:"

    # Create a completely independent app instance using the factory pattern
    test_app = create_app(
        app_name="now_lms_session_basic", testing=True, config_overrides={"SQLALCHEMY_DATABASE_URI": database_uri}
    )

    with test_app.app_context():
        from now_lms import database
        from now_lms.db.tools import crear_configuracion_predeterminada
        from now_lms.db.initial_data import crear_certificados

        # Initialize database and setup basic data
        database.create_all()
        try:
            crear_configuracion_predeterminada()
            crear_certificados()
            log.debug("Session basic database setup completed.")
        except Exception as e:
            log.warning(f"Session basic database setup error (continuing): {e}")

    yield test_app

    # Session cleanup
    with test_app.app_context():
        from now_lms import database

        try:
            database.session.remove()
            database.drop_all()
            database.engine.dispose()
        except Exception as e:
            log.warning(f"Session basic database cleanup error: {e}")


@pytest.fixture(scope="session")
def session_full_db_setup():
    """
    Session-scoped full database setup with complete data population.
    Use this for read-only tests that need populated database.
    Creates a completely independent app and database.
    Always uses SQLite in-memory for complete isolation between session fixtures.
    """
    from now_lms import create_app

    # Always use in-memory SQLite for session fixtures to avoid interference
    database_uri = "sqlite:///:memory:"

    # Create a completely independent app instance using the factory pattern
    test_app = create_app(
        app_name="now_lms_session_full", testing=True, config_overrides={"SQLALCHEMY_DATABASE_URI": database_uri}
    )

    with test_app.app_context():
        from now_lms import database
        from now_lms.db.tools import crear_configuracion_predeterminada
        from now_lms.db.initial_data import (
            crear_certificados,
            crear_curso_predeterminado,
            crear_usuarios_predeterminados,
            crear_certificacion,
        )
        from now_lms.db.data_test import crear_data_para_pruebas

        # Initialize database and setup full data
        database.create_all()
        try:
            # Setup basic configuration and data step by step
            crear_configuracion_predeterminada()

            # Create certificates - handle duplicates gracefully with session rollback
            try:
                crear_certificados()
            except Exception as e:
                log.warning(f"Certificate creation error, rolling back: {e}")
                database.session.rollback()  # Rollback to recover the session

            # Create users and courses
            try:
                crear_usuarios_predeterminados()
                crear_curso_predeterminado()
                crear_certificacion()
                crear_data_para_pruebas()
                database.session.commit()  # Commit successful operations
            except Exception as e:
                log.warning(f"User/course creation error: {e}")
                database.session.rollback()

            log.debug("Session full database setup completed.")
        except Exception as e:
            log.warning(f"Session full database setup error (continuing): {e}")
            database.session.rollback()

    yield test_app

    # Session cleanup
    with test_app.app_context():
        from now_lms import database

        try:
            database.session.remove()
            database.drop_all()
            database.engine.dispose()
        except Exception as e:
            log.warning(f"Session full database cleanup error: {e}")


@pytest.fixture(scope="session")
def session_full_db_setup_with_examples():
    """
    Session-scoped full database setup with complete data population including examples.
    Use this for read-only tests that need complete populated database with examples.
    Creates a completely independent app and database.
    Always uses SQLite in-memory for complete isolation between session fixtures.
    """
    from now_lms import create_app, initial_setup

    # Always use in-memory SQLite for session fixtures to avoid interference
    database_uri = "sqlite:///:memory:"

    # Create a completely independent app instance using the factory pattern
    test_app = create_app(
        app_name="now_lms_session_examples", testing=True, config_overrides={"SQLALCHEMY_DATABASE_URI": database_uri}
    )

    with test_app.app_context():
        from now_lms import database

        # Initialize database and setup full data with examples
        database.create_all()
        try:
            # Use the updated initial_setup function with flask_app parameter
            initial_setup(with_examples=True, with_tests=True, flask_app=test_app)
            database.session.commit()  # Ensure changes are committed
            log.debug("Session full database setup with examples completed.")
        except Exception as e:
            log.warning(f"Session full database setup with examples error (continuing): {e}")
            database.session.rollback()  # Rollback on error to recover session

    yield test_app

    # Session cleanup
    with test_app.app_context():
        from now_lms import database

        try:
            database.session.remove()
            database.drop_all()
            database.engine.dispose()
        except Exception as e:
            log.warning(f"Session full database cleanup with examples error: {e}")


@pytest.fixture(scope="function")
def isolated_db_session(session_full_db_setup):
    """
    Function-scoped database session with savepoint rollback for test isolation.
    Use this when tests need to modify data but can share schema.
    WARNING: Cannot be used with function-scoped fixtures (app, db_session, etc.).
    """
    with session_full_db_setup.app_context():
        from now_lms import database

        # Start a savepoint instead of a full transaction
        # This allows us to share the schema while isolating changes
        savepoint = database.session.begin_nested()

        try:
            yield database.session
        finally:
            # Rollback to the savepoint to undo any changes
            try:
                savepoint.rollback()
            except Exception as e:
                log.warning(f"Error during savepoint rollback: {e}")
                # If rollback fails, force session rollback
                try:
                    database.session.rollback()
                except Exception as rollback_error:
                    log.warning(f"Error during session rollback: {rollback_error}")
