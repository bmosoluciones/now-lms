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

"""Test comprehensive cache invalidation in settings."""


from __future__ import annotations

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms.vistas.settings import invalidar_cache


class TestCacheInvalidation:
    """Test comprehensive cache invalidation functionality."""

    def test_invalidar_cache_function_exists(self, isolated_db_session):
        """Test that the invalidar_cache function exists and is callable."""
        assert callable(invalidar_cache)

    def test_invalidar_cache_returns_boolean(self, isolated_db_session):
        """Test that invalidar_cache returns a boolean result."""
        result = invalidar_cache()
        assert isinstance(result, bool)

    def test_invalidar_cache_success(self, app, isolated_db_session):
        """Test that invalidar_cache executes successfully."""
        with app.app_context():
            # Call invalidar_cache - should work regardless of cache type
            result = invalidar_cache()

            # Should return True for successful invalidation
            assert result is True

    def test_comprehensive_cache_invalidation(self, app, isolated_db_session):
        """Test that comprehensive cache invalidation works properly."""
        with app.app_context():
            # Test that the function clears cache without errors
            result = invalidar_cache()
            assert result is True
