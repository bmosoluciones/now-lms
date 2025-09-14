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

"""Test environment variable detection in configuration creation."""

import os
import unittest.mock

import pytest
from sqlalchemy.orm import scoped_session

from now_lms.db import Configuracion, database
from now_lms.db.tools import crear_configuracion_predeterminada


class TestEnvironmentVariables:
    """Test environment variable detection for NOW_LMS configuration."""

    def test_default_configuration_without_env_vars(self, isolated_db_session: scoped_session):
        """Test that default configuration works without environment variables."""
        # Clear existing configuration first
        database.session.execute(database.delete(Configuracion))
        database.session.commit()

        # Ensure no environment variables are set
        with unittest.mock.patch.dict(os.environ, {}, clear=False):
            if "NOW_LMS_LANG" in os.environ:
                del os.environ["NOW_LMS_LANG"]
            if "NOW_LMS_CURRENCY" in os.environ:
                del os.environ["NOW_LMS_CURRENCY"]
            if "NOW_LMS_TIMEZONE" in os.environ:
                del os.environ["NOW_LMS_TIMEZONE"]

            crear_configuracion_predeterminada()

            config = database.session.execute(database.select(Configuracion)).scalars().first()
            assert config is not None

            # Check defaults (testing mode uses Spanish, production uses English)
            assert config.lang in ["es", "en"]  # Depends on testing mode
            assert config.moneda == "USD"
            assert config.time_zone == "UTC"

    def test_now_lms_lang_environment_variable(self, isolated_db_session: scoped_session):
        """Test that NOW_LMS_LANG environment variable is respected."""
        # Clear existing configuration first
        database.session.execute(database.delete(Configuracion))
        database.session.commit()

        with unittest.mock.patch.dict(os.environ, {"NOW_LMS_LANG": "pt_BR"}):
            crear_configuracion_predeterminada()

            config = database.session.execute(database.select(Configuracion)).scalars().first()
            assert config is not None
            assert config.lang == "pt_BR"

    def test_now_lms_currency_environment_variable(self, isolated_db_session: scoped_session):
        """Test that NOW_LMS_CURRENCY environment variable is respected."""
        # Clear existing configuration first
        database.session.execute(database.delete(Configuracion))
        database.session.commit()

        with unittest.mock.patch.dict(os.environ, {"NOW_LMS_CURRENCY": "EUR"}):
            crear_configuracion_predeterminada()

            config = database.session.execute(database.select(Configuracion)).scalars().first()
            assert config is not None
            assert config.moneda == "EUR"

    def test_now_lms_timezone_environment_variable(self, isolated_db_session: scoped_session):
        """Test that NOW_LMS_TIMEZONE environment variable is respected."""
        # Clear existing configuration first
        database.session.execute(database.delete(Configuracion))
        database.session.commit()

        with unittest.mock.patch.dict(os.environ, {"NOW_LMS_TIMEZONE": "America/New_York"}):
            crear_configuracion_predeterminada()

            config = database.session.execute(database.select(Configuracion)).scalars().first()
            assert config is not None
            assert config.time_zone == "America/New_York"

    def test_all_environment_variables_together(self, isolated_db_session: scoped_session):
        """Test that all environment variables work together."""
        # Clear existing configuration first
        database.session.execute(database.delete(Configuracion))
        database.session.commit()

        env_vars = {"NOW_LMS_LANG": "pt_BR", "NOW_LMS_CURRENCY": "BRL", "NOW_LMS_TIMEZONE": "America/Sao_Paulo"}

        with unittest.mock.patch.dict(os.environ, env_vars):
            crear_configuracion_predeterminada()

            config = database.session.execute(database.select(Configuracion)).scalars().first()
            assert config is not None
            assert config.lang == "pt_BR"
            assert config.moneda == "BRL"
            assert config.time_zone == "America/Sao_Paulo"

    def test_environment_variables_take_precedence_over_defaults(self, isolated_db_session: scoped_session):
        """Test that environment variables override default logic."""
        # Clear existing configuration first
        database.session.execute(database.delete(Configuracion))
        database.session.commit()

        # Set environment variables that would override both testing and production defaults
        env_vars = {
            "NOW_LMS_LANG": "pt_BR",  # Override both "es" (testing) and "en" (production)
            "NOW_LMS_CURRENCY": "JPY",  # Override "USD"
            "NOW_LMS_TIMEZONE": "Asia/Tokyo",  # Override "UTC"
        }

        with unittest.mock.patch.dict(os.environ, env_vars):
            crear_configuracion_predeterminada()

            config = database.session.execute(database.select(Configuracion)).scalars().first()
            assert config is not None
            assert config.lang == "pt_BR"
            assert config.moneda == "JPY"
            assert config.time_zone == "Asia/Tokyo"

    def test_empty_environment_variables_use_defaults(self, isolated_db_session: scoped_session):
        """Test that empty environment variables fall back to defaults."""
        # Clear existing configuration first
        database.session.execute(database.delete(Configuracion))
        database.session.commit()

        env_vars = {
            "NOW_LMS_LANG": "",  # Empty string should use default
            "NOW_LMS_CURRENCY": "",  # Empty string should use default
            "NOW_LMS_TIMEZONE": "",  # Empty string should use default
        }

        with unittest.mock.patch.dict(os.environ, env_vars):
            crear_configuracion_predeterminada()

            config = database.session.execute(database.select(Configuracion)).scalars().first()
            assert config is not None

            # Empty strings should fallback to defaults
            assert config.lang in ["es", "en"]  # Depends on testing mode
            assert config.moneda == "USD"
            assert config.time_zone == "UTC"
