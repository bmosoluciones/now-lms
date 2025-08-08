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

import os
import pytest
from sqlalchemy.exc import OperationalError, ProgrammingError
from pg8000.dbapi import ProgrammingError as PGProgrammingError
from pg8000.exceptions import DatabaseError

from now_lms import log

# Database URL configuration following the requirements:
# 1. If DATABASE_URL environment variable is defined with valid URL, use it
# 2. If not defined, use SQLite in-memory database by default
DB_URL = os.environ.get("DATABASE_URL")
if not DB_URL:
    # Default to SQLite in-memory database for tests
    DB_URL = "sqlite:///:memory:"

log.info(f"Using test database URL: {DB_URL}")


@pytest.fixture(scope="session")
def database_url():
    """Provide the database URL for tests."""
    return DB_URL


@pytest.fixture
def lms_application(database_url):
    """Create Flask application with test configuration."""
    from now_lms import app

    # Configure the application for testing
    app.config.update(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret-key-for-testing",
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
            "WTF_CSRF_ENABLED": False,
            "DEBUG": True,
            "PRESERVE_CONTEXT_ON_EXCEPTION": True,
            "SQLALCHEMY_DATABASE_URI": database_url,
            "MAIL_SUPPRESS_SEND": True,
        }
    )

    yield app


@pytest.fixture
def minimal_db_setup(lms_application):
    """
    Minimal database setup that only creates schema without full data population.
    Use this for tests that don't need the complete database setup.
    """
    from now_lms import database
    from now_lms.db import eliminar_base_de_datos_segura

    with lms_application.app_context():
        try:
            # Only create schema, don't populate with full data
            database.create_all()
            log.debug("Minimal database schema created.")
        except (OperationalError, ProgrammingError, PGProgrammingError, DatabaseError) as e:
            log.warning(f"Database setup error (continuing): {e}")

    yield lms_application  # Return the application with minimal database setup

    # Clean up after test
    with lms_application.app_context():
        try:
            # For PostgreSQL, handle potential rollback issues
            db_url = lms_application.config.get("SQLALCHEMY_DATABASE_URI", "")
            if "postgresql" in db_url.lower():
                database.session.rollback()
                database.session.close()
            eliminar_base_de_datos_segura()
            log.debug("Minimal database cleaned up.")
        except (OperationalError, ProgrammingError, PGProgrammingError, DatabaseError) as e:
            log.warning(f"Database cleanup warning: {e}")


@pytest.fixture
def full_db_setup(lms_application):
    """
    Full database setup with complete data population.
    Use this for tests that need the complete populated database (like test_vistas).
    """
    from now_lms import database, initial_setup
    from now_lms.db import eliminar_base_de_datos_segura

    with lms_application.app_context():
        try:
            # For PostgreSQL, ensure clean state before setup
            db_url = lms_application.config.get("SQLALCHEMY_DATABASE_URI", "")
            if "postgresql" in db_url.lower():
                try:
                    database.session.rollback()
                    database.session.close()
                except:
                    pass

            # Full database setup with test data
            eliminar_base_de_datos_segura()
            initial_setup(with_tests=True, with_examples=False)
            log.debug("Full database setup completed.")
        except (OperationalError, ProgrammingError, PGProgrammingError, DatabaseError) as e:
            log.warning(f"Full database setup error (continuing): {e}")

    yield lms_application  # Return the application with the full database setup

    # Clean up after test
    with lms_application.app_context():
        try:
            # For PostgreSQL, handle potential rollback issues
            db_url = lms_application.config.get("SQLALCHEMY_DATABASE_URI", "")
            if "postgresql" in db_url.lower():
                database.session.rollback()
                database.session.close()
            eliminar_base_de_datos_segura()
            log.debug("Full database cleaned up.")
        except (OperationalError, ProgrammingError, PGProgrammingError, DatabaseError) as e:
            log.warning(f"Database cleanup warning: {e}")


@pytest.fixture
def basic_config_setup(lms_application):
    """
    Basic configuration setup that only creates essential configuration.
    For tests that need basic config but not full database.
    """
    from now_lms import database
    from now_lms.db import eliminar_base_de_datos_segura
    from now_lms.db.tools import crear_configuracion_predeterminada

    with lms_application.app_context():
        try:
            # Only create schema and basic configuration
            database.create_all()
            crear_configuracion_predeterminada()
            log.debug("Basic configuration setup completed.")
        except (OperationalError, ProgrammingError, PGProgrammingError, DatabaseError) as e:
            log.warning(f"Basic config setup error (continuing): {e}")

    yield lms_application  # Return the application with basic configuration

    # Clean up after test
    with lms_application.app_context():
        try:
            # For PostgreSQL, handle potential rollback issues
            db_url = lms_application.config.get("SQLALCHEMY_DATABASE_URI", "")
            if "postgresql" in db_url.lower():
                database.session.rollback()
                database.session.close()
            eliminar_base_de_datos_segura()
            log.debug("Basic configuration cleaned up.")
        except (OperationalError, ProgrammingError, PGProgrammingError, DatabaseError) as e:
            log.warning(f"Database cleanup warning: {e}")
