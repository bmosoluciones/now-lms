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

from os import environ
import pytest


"""
Casos de uso mas comunes.
"""


@pytest.fixture
def lms_application():
    from now_lms import app

    app.config.update(
        {
            "TESTING": True,
            "SECRET_KEY": "jgjañlsldaksjdklasjfkjj",
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
            "WTF_CSRF_ENABLED": False,
            "DEBUG": True,
            "PRESERVE_CONTEXT_ON_EXCEPTION": True,
            "SQLALCHEMY_ECHO": True,
            "MAIL_SUPPRESS_SEND": True,
        }
    )

    yield app


def test_postgress_pg8000(lms_application):
    if environ.get("DATABASE_URL", "").startswith("postgresql+pg8000"):
        lms_application.config.update({"SQLALCHEMY_DATABASE_URI": environ.get("DATABASE_URL")})
        assert lms_application.config.get("SQLALCHEMY_DATABASE_URI") == environ.get("DATABASE_URL")
        from now_lms import database, initial_setup

        with lms_application.app_context():
            database.drop_all()
            initial_setup(with_tests=True, with_examples=True)
    else:
        pytest.skip("Not postgresql driver configured in environ.")


def test_postgress_psycopg2(lms_application):
    if environ.get("DATABASE_URL", "").startswith("postgresql+psycopg2"):
        lms_application.config.update({"SQLALCHEMY_DATABASE_URI": environ.get("DATABASE_URL")})
        assert lms_application.config.get("SQLALCHEMY_DATABASE_URI") == environ.get("DATABASE_URL")
        from now_lms import database, initial_setup

        with lms_application.app_context():
            database.drop_all()
            initial_setup(with_tests=True, with_examples=True)
    else:
        pytest.skip("Not postgresql driver configured in environ.")


def test_mysql_mysqldb(lms_application, request):
    if environ.get("DATABASE_URL", "").startswith("mysql+mysqldb"):
        lms_application.config.update({"SQLALCHEMY_DATABASE_URI": environ.get("DATABASE_URL")})
        assert lms_application.config.get("SQLALCHEMY_DATABASE_URI") == environ.get("DATABASE_URL")
        from now_lms import database, initial_setup

        with lms_application.app_context():
            database.drop_all()
            initial_setup(with_tests=True, with_examples=True)
    else:
        pytest.skip("Not mysql driver configured in environ.")
