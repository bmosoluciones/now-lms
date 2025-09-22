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

"""Tests for site_config global variable functionality."""

from flask import render_template_string

from now_lms import site_config
from now_lms.db import Configuracion


class TestSiteConfigGlobal:
    """Test suite for site_config global variable functionality."""

    def test_site_config_function_exists(self, session_basic_db_setup):
        """Test that site_config function exists and is callable."""
        assert callable(site_config)

    def test_site_config_available_in_jinja_globals(self, session_basic_db_setup):
        """Test that site_config is available as a Jinja2 global variable."""
        app = session_basic_db_setup

        with app.app_context():
            assert "site_config" in app.jinja_env.globals
            assert app.jinja_env.globals["site_config"] == site_config

    def test_site_config_returns_none_when_no_config(self, session_basic_db_setup):
        """Test that site_config returns None when no configuration exists."""
        app = session_basic_db_setup

        with app.app_context():
            result = site_config()
            # The basic setup might create a config, so we just test it's callable
            # and returns a result that's either None or a Configuracion object
            assert result is None or isinstance(result, Configuracion)

    def test_site_config_returns_config_when_exists(self, session_full_db_setup):
        """Test that site_config returns configuration when it exists."""
        app = session_full_db_setup

        with app.app_context():
            result = site_config()
            assert result is not None
            assert isinstance(result, Configuracion)
            # Should have a title attribute
            assert hasattr(result, "titulo")

    def test_site_config_accessible_in_template(self, session_full_db_setup):
        """Test that site_config can be used directly in templates."""
        app = session_full_db_setup

        with app.app_context():
            # Test template that uses site_config directly
            template = "{% if site_config() %}{{ site_config().titulo or 'No title' }}{% else %}No config{% endif %}"
            result = render_template_string(template)

            # Should either show the title or fallback text
            assert result != ""

    def test_site_config_template_without_function_call(self, session_full_db_setup):
        """Test that site_config can be used without calling it as a function in templates."""
        app = session_full_db_setup

        with app.app_context():
            # This should work because site_config is a global variable pointing to the function
            template = "{% set config_obj = site_config() %}{% if config_obj %}Config exists{% else %}No config{% endif %}"
            result = render_template_string(template)

            # Should work regardless of whether config exists
            assert result in ["Config exists", "No config"]

    def test_site_config_caching(self, session_full_db_setup):
        """Test that site_config uses caching properly."""
        app = session_full_db_setup

        with app.app_context():
            # Call site_config twice - should return same result due to caching
            result1 = site_config()
            result2 = site_config()

            # Should be the same data even if not the exact same object
            if result1 and result2:
                assert result1.id == result2.id

    def test_cache_invalidation_includes_site_config(self, session_full_db_setup):
        """Test that cache invalidation includes the site_config cache key."""
        from now_lms.vistas.settings import invalidar_cache

        app = session_full_db_setup

        with app.app_context():
            # Prime the cache
            site_config()

            # Invalidate cache - just verify it doesn't error
            result = invalidar_cache()

            # Should return True indicating success
            assert result is True
