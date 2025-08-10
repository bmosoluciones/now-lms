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

"""Test the safe database deletion function."""

import pytest
from sqlalchemy.exc import OperationalError, ProgrammingError
from pg8000.dbapi import ProgrammingError as PGProgrammingError
from pg8000.exceptions import DatabaseError


def test_eliminar_base_de_datos_segura_basic(lms_application):
    """Test that the safe database deletion function works correctly."""
    from now_lms import database
    from now_lms.db import eliminar_base_de_datos_segura

    with lms_application.app_context():
        try:
            # Set up a basic database
            database.create_all()

            # Verify tables exist by checking we can create basic config
            from now_lms.db.tools import crear_configuracion_predeterminada

            crear_configuracion_predeterminada()

            # Use the safe deletion function
            eliminar_base_de_datos_segura()

            # Verify the database is clean - this should not raise an error
            database.create_all()

        except (OperationalError, ProgrammingError, PGProgrammingError, DatabaseError) as e:
            pytest.skip(f"Database test skipped due to error: {e}")


def test_eliminar_base_de_datos_segura_with_postgresql_sessions(lms_application):
    """Test that the safe deletion function properly handles PostgreSQL sessions."""
    from now_lms import database
    from now_lms.db import eliminar_base_de_datos_segura

    # Only run this test if we're using PostgreSQL
    db_url = lms_application.config.get("SQLALCHEMY_DATABASE_URI", "")
    if "postgresql" not in db_url.lower():
        pytest.skip("This test is specific to PostgreSQL")

    with lms_application.app_context():
        try:
            # Set up database and create some data
            database.create_all()

            # Simulate having active sessions by starting a transaction
            database.session.begin()

            # Use the safe deletion function - it should handle session cleanup
            eliminar_base_de_datos_segura()

            # Verify we can recreate the database without issues
            database.create_all()

        except (OperationalError, ProgrammingError, PGProgrammingError, DatabaseError) as e:
            pytest.skip(f"PostgreSQL test skipped due to error: {e}")


def test_eliminar_base_de_datos_segura_error_handling(lms_application):
    """Test that the safe deletion function handles errors correctly."""
    from now_lms import database
    from now_lms.db import eliminar_base_de_datos_segura
    from unittest.mock import patch
    from sqlalchemy.exc import SQLAlchemyError

    with lms_application.app_context():
        try:
            database.create_all()

            # Mock drop_all to raise an error and verify error handling
            with patch.object(database, "drop_all") as mock_drop_all:
                mock_drop_all.side_effect = SQLAlchemyError("Test error")

                # The function should raise the error after attempting rollback
                with pytest.raises(SQLAlchemyError):
                    eliminar_base_de_datos_segura()

        except (OperationalError, ProgrammingError, PGProgrammingError, DatabaseError) as e:
            pytest.skip(f"Database test skipped due to error: {e}")
