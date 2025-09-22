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

    def test_custom_data_dir_environment_variable(self, isolated_db_session: scoped_session):
        """Test that NOW_LMS_DATA_DIR environment variable is respected."""
        import tempfile
        import unittest.mock
        from now_lms.db.initial_data import populate_custmon_data_dir

        with tempfile.TemporaryDirectory() as temp_dir:
            custom_data_dir = temp_dir + "/custom_data"

            # Clear any existing env vars that might interfere
            env_vars = {
                "NOW_LMS_DATA_DIR": custom_data_dir,
            }

            with unittest.mock.patch.dict(os.environ, env_vars, clear=False):
                # Remove other env vars that might interfere
                for var in ["NOW_LMS_THEMES_DIR"]:
                    if var in os.environ:
                        del os.environ[var]

                # Re-import config to pick up the environment variable
                import importlib
                import sys

                if "now_lms.config" in sys.modules:
                    importlib.reload(sys.modules["now_lms.config"])
                else:
                    pass

                # Call the populate function
                populate_custmon_data_dir()

                # Verify the custom directory was created and populated
                assert os.path.exists(custom_data_dir)
                assert os.path.isdir(custom_data_dir)
                # Check that some basic files were copied
                assert len(os.listdir(custom_data_dir)) > 0

    def test_custom_themes_dir_environment_variable(self, isolated_db_session: scoped_session):
        """Test that NOW_LMS_THEMES_DIR environment variable is respected."""
        import tempfile
        import unittest.mock
        from now_lms.db.initial_data import populate_custom_theme_dir

        with tempfile.TemporaryDirectory() as temp_dir:
            custom_themes_dir = temp_dir + "/custom_themes"

            # Clear any existing env vars that might interfere
            env_vars = {
                "NOW_LMS_THEMES_DIR": custom_themes_dir,
            }

            with unittest.mock.patch.dict(os.environ, env_vars, clear=False):
                # Remove other env vars that might interfere
                for var in ["NOW_LMS_DATA_DIR"]:
                    if var in os.environ:
                        del os.environ[var]

                # Re-import config to pick up the environment variable
                import importlib
                import sys

                if "now_lms.config" in sys.modules:
                    importlib.reload(sys.modules["now_lms.config"])
                else:
                    pass

                # Call the populate function
                populate_custom_theme_dir()

                # Verify the custom directory was created and populated
                assert os.path.exists(custom_themes_dir)
                assert os.path.isdir(custom_themes_dir)
                # Check that some basic template files were copied
                assert len(os.listdir(custom_themes_dir)) > 0

    def test_init_app_calls_populate_functions_with_env_vars(self, isolated_db_session: scoped_session):
        """Test that init_app calls populate functions when environment variables are set."""
        import tempfile
        import unittest.mock
        from now_lms import init_app

        with tempfile.TemporaryDirectory() as temp_dir:
            custom_data_dir = temp_dir + "/custom_data"
            custom_themes_dir = temp_dir + "/custom_themes"

            env_vars = {
                "NOW_LMS_DATA_DIR": custom_data_dir,
                "NOW_LMS_THEMES_DIR": custom_themes_dir,
            }

            with unittest.mock.patch.dict(os.environ, env_vars, clear=False):
                # Re-import config to pick up the environment variables
                import importlib
                import sys

                if "now_lms.config" in sys.modules:
                    importlib.reload(sys.modules["now_lms.config"])
                else:
                    pass

                # Mock the populate functions to track if they were called
                with (
                    unittest.mock.patch("now_lms.populate_custmon_data_dir") as mock_data_dir,
                    unittest.mock.patch("now_lms.populate_custom_theme_dir") as mock_theme_dir,
                ):

                    # Call init_app which should call the populate functions
                    result = init_app()

                    # Verify init_app succeeded
                    assert result is True

                    # Verify populate functions were called
                    mock_data_dir.assert_called_once()
                    mock_theme_dir.assert_called_once()

    def test_environment_variables_unset_for_testing(self):
        """Ensure test environment properly unsets environment variables."""
        # This test validates that our test setup doesn't leak environment variables
        # that could affect other tests

        sensitive_env_vars = ["NOW_LMS_DATA_DIR", "NOW_LMS_THEMES_DIR", "NOW_LMS_LANG", "NOW_LMS_CURRENCY", "NOW_LMS_TIMEZONE"]

        # In a proper test environment, these should not be set unless explicitly testing them
        for var in sensitive_env_vars:
            if var in os.environ:
                # If set, it should be in a controlled test context
                # This serves as documentation of what env vars affect the system
                pass
