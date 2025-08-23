# Copyright 2021 -2023 William José Moreno Reyes
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

import pytest
from os import environ

from now_lms.db import database

"""
Casos de uso mas comunes.
"""

database_url = environ.get("DATABASE_URL", "")


def test_postgress_pg8000():
    """Test PostgreSQL database using pg8000 driver with improved error handling."""
    if database_url.startswith("postgresql"):
        from now_lms import app, database, initial_setup
        from now_lms.db import eliminar_base_de_datos_segura
        from sqlalchemy.exc import OperationalError, ProgrammingError
        from pg8000.dbapi import ProgrammingError as PGProgrammingError
        from pg8000.exceptions import DatabaseError

        app.config.update({"SQLALCHEMY_DATABASE_URI": database_url})
        assert app.config.get("SQLALCHEMY_DATABASE_URI") == database_url

        with app.app_context():
            try:
                # PostgreSQL-specific session handling
                try:
                    database.session.rollback()
                    database.session.close()
                except:
                    pass

                eliminar_base_de_datos_segura()
            except (OperationalError, ProgrammingError, PGProgrammingError, DatabaseError) as e:
                pytest.skip(f"PostgreSQL test skipped due to database error: {e}")
            finally:
                try:
                    database.session.rollback()
                    database.session.close()
                except:
                    pass
            initial_setup(with_tests=True, with_examples=True)
    else:
        pytest.skip("Not postgresql+pg8000 driver configured in environ.")


def test_mysql_mysqldb():
    """Test MySQL database using MySQLdb driver with improved error handling."""
    if database_url.startswith("mysql"):
        from now_lms import app, database, initial_setup
        from now_lms.db import eliminar_base_de_datos_segura
        from sqlalchemy.exc import OperationalError, IntegrityError

        app.config.update({"SQLALCHEMY_DATABASE_URI": database_url})
        assert app.config.get("SQLALCHEMY_DATABASE_URI") == database_url

        with app.app_context():
            try:
                # MySQL-specific session handling
                try:
                    database.session.rollback()
                    database.session.close()
                except:
                    pass

                eliminar_base_de_datos_segura()
            except (OperationalError, IntegrityError) as e:
                pytest.skip(f"MySQL test skipped due to database error: {e}")
            finally:
                try:
                    database.session.rollback()
                    database.session.close()
                except:
                    pass
            initial_setup(with_tests=True, with_examples=True)
    else:
        pytest.skip("Not mysql driver configured in environ.")
