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

"""Tests for memory cache functionality via FileSystemCache."""

import os
import pytest
from unittest.mock import patch, MagicMock


from now_lms.cache_utils import get_memory_cache_config, init_cache


class TestMemoryCacheConfig:
    """Test memory cache configuration logic."""

    def test_memory_cache_disabled_by_default(self):
        """Test that memory cache is disabled when NOW_LMS_MEMORY_CACHE is not set."""
        with patch.dict(os.environ, {}, clear=True):
            config = get_memory_cache_config()
            assert config["CACHE_TYPE"] == "NullCache"

    def test_memory_cache_disabled_when_set_to_zero(self):
        """Test that memory cache is disabled when NOW_LMS_MEMORY_CACHE=0."""
        with patch.dict(os.environ, {"NOW_LMS_MEMORY_CACHE": "0"}):
            config = get_memory_cache_config()
            assert config["CACHE_TYPE"] == "NullCache"

    def test_memory_cache_enabled_when_set_to_one(self):
        """Test that memory cache attempts to initialize when NOW_LMS_MEMORY_CACHE=1."""
        with patch.dict(os.environ, {"NOW_LMS_MEMORY_CACHE": "1"}):
            # Mock os.path.exists and os.makedirs to simulate /dev/shm availability
            with (
                patch("os.path.exists", return_value=False),
                patch("os.makedirs") as mock_makedirs,
                patch("builtins.open", create=True) as mock_open,
                patch("os.remove"),
            ):

                config = get_memory_cache_config()

                assert config["CACHE_TYPE"] == "FileSystemCache"
                assert config["CACHE_DIR"] == "/dev/shm/now_lms_cache"
                assert config["CACHE_DEFAULT_TIMEOUT"] == 300
                assert config["CACHE_KEY_PREFIX"] == "now_lms:"
                mock_makedirs.assert_called_with("/dev/shm/now_lms_cache", mode=0o700, exist_ok=True)

    @pytest.mark.xfail(raises=AssertionError, reason="Linux only test.")
    def test_memory_cache_fallback_to_temp_dir(self):
        """Test fallback to temp directory when /dev/shm is not available."""
        with patch.dict(os.environ, {"NOW_LMS_MEMORY_CACHE": "1"}):
            # Mock /dev/shm failure and temp directory success
            with (
                patch("os.path.exists") as mock_exists,
                patch("os.makedirs") as mock_makedirs,
                patch("tempfile.gettempdir", return_value="/tmp"),
                patch("builtins.open", create=True),
                patch("os.remove"),
            ):

                # First call (for /dev/shm) raises exception, subsequent calls for temp dir succeed
                mock_makedirs.side_effect = [OSError("Permission denied"), None]
                mock_exists.side_effect = [False, False]  # /dev/shm and temp dir don't exist

                config = get_memory_cache_config()

                assert config["CACHE_TYPE"] == "FileSystemCache"
                assert config["CACHE_DIR"] == "/tmp/now_lms_cache"

    @pytest.mark.xfail(raises=AssertionError, reason="Linux only test.")
    def test_memory_cache_fallback_to_null_cache(self):
        """Test fallback to NullCache when both /dev/shm and temp directory fail."""
        with patch.dict(os.environ, {"NOW_LMS_MEMORY_CACHE": "1"}):
            # Mock both /dev/shm and temp directory failures
            with (
                patch("os.makedirs", side_effect=OSError("Permission denied")),
                patch("os.path.exists", return_value=False),
                patch("tempfile.gettempdir", return_value="/tmp"),
            ):

                config = get_memory_cache_config()

                assert config["CACHE_TYPE"] == "NullCache"

    def test_memory_cache_write_test_failure_fallback(self):
        """Test fallback when write test fails even if directory creation succeeds."""
        with patch.dict(os.environ, {"NOW_LMS_MEMORY_CACHE": "1"}):
            # Mock directory creation success but write test failure
            with (
                patch("os.path.exists", return_value=False),
                patch("os.makedirs"),
                patch("builtins.open", side_effect=PermissionError("Write failed")),
                patch("tempfile.gettempdir", return_value="/tmp"),
            ):

                config = get_memory_cache_config()

                # Should fallback to temp dir and eventually to NullCache
                assert config["CACHE_TYPE"] == "NullCache"


class TestInitCache:
    """Test cache initialization logic."""

    def test_init_cache_redis_precedence(self):
        """Test that Redis cache takes precedence over memory cache."""
        with patch.dict(os.environ, {"REDIS_URL": "redis://localhost:6379/0", "NOW_LMS_MEMORY_CACHE": "1"}):
            # Create a mock Flask app
            mock_app = MagicMock()
            mock_app.config = {}

            # Mock the cache import within init_cache function
            with patch("now_lms.cache.cache") as mock_cache:
                init_cache(mock_app)

                # Verify Redis config was used
                mock_cache.init_app.assert_called_once()
                call_args = mock_cache.init_app.call_args
                config = call_args[1]["config"]
                assert config["CACHE_TYPE"] == "RedisCache"
                assert config["CACHE_REDIS_URL"] == "redis://localhost:6379/0"

    def test_init_cache_memcached_precedence(self):
        """Test that Memcached cache takes precedence over memory cache."""
        with patch.dict(os.environ, {"CACHE_MEMCACHED_SERVERS": "localhost:11211", "NOW_LMS_MEMORY_CACHE": "1"}, clear=True):
            mock_app = MagicMock()
            mock_app.config = {}

            with patch("now_lms.cache.cache") as mock_cache:
                init_cache(mock_app)

                call_args = mock_cache.init_app.call_args
                config = call_args[1]["config"]
                assert config["CACHE_TYPE"] == "MemcachedCache"
                assert config["CACHE_MEMCACHED_SERVERS"] == "localhost:11211"

    def test_init_cache_memory_cache_enabled(self):
        """Test memory cache initialization when enabled."""
        with patch.dict(os.environ, {"NOW_LMS_MEMORY_CACHE": "1"}, clear=True):
            mock_app = MagicMock()
            mock_app.config = {}

            # Mock the filesystem operations for memory cache
            with (
                patch("now_lms.cache.cache") as mock_cache,
                patch("now_lms.cache_utils.get_memory_cache_config") as mock_get_config,
            ):

                mock_get_config.return_value = {
                    "CACHE_TYPE": "FileSystemCache",
                    "CACHE_DIR": "/dev/shm/now_lms_cache",
                    "CACHE_DEFAULT_TIMEOUT": 300,
                    "CACHE_KEY_PREFIX": "now_lms:",
                }

                init_cache(mock_app)

                call_args = mock_cache.init_app.call_args
                config = call_args[1]["config"]
                assert config["CACHE_TYPE"] == "FileSystemCache"
                assert config["CACHE_DIR"] == "/dev/shm/now_lms_cache"

    def test_init_cache_null_cache_fallback(self):
        """Test fallback to NullCache when no cache is configured."""
        with patch.dict(os.environ, {}, clear=True):
            mock_app = MagicMock()
            mock_app.config = {}

            with patch("now_lms.cache.cache") as mock_cache:
                init_cache(mock_app)

                call_args = mock_cache.init_app.call_args
                config = call_args[1]["config"]
                assert config["CACHE_TYPE"] == "NullCache"

    def test_init_cache_config_override_respected(self):
        """Test that app config overrides are respected."""
        with patch.dict(os.environ, {"NOW_LMS_MEMORY_CACHE": "1"}, clear=True):
            mock_app = MagicMock()
            mock_app.config = {"CACHE_TYPE": "RedisCache", "CACHE_REDIS_URL": "redis://override:6379/0"}

            with (
                patch("now_lms.cache.cache") as mock_cache,
                patch("now_lms.cache_utils.get_memory_cache_config") as mock_get_config,
            ):

                mock_get_config.return_value = {"CACHE_TYPE": "FileSystemCache", "CACHE_DIR": "/dev/shm/now_lms_cache"}

                init_cache(mock_app)

                call_args = mock_cache.init_app.call_args
                config = call_args[1]["config"]
                # App config should override the memory cache config
                assert config["CACHE_TYPE"] == "RedisCache"
                assert config["CACHE_REDIS_URL"] == "redis://override:6379/0"

    def test_init_cache_exception_fallback(self):
        """Test fallback to NullCache when cache initialization fails."""
        with patch.dict(os.environ, {"NOW_LMS_MEMORY_CACHE": "1"}, clear=True):
            mock_app = MagicMock()
            mock_app.config = {}

            with patch("now_lms.cache.cache") as mock_cache:
                # First call raises exception, second call should succeed with NullCache
                mock_cache.init_app.side_effect = [Exception("Cache init failed"), None]

                init_cache(mock_app)

                # Should be called twice: once with original config, once with fallback
                assert mock_cache.init_app.call_count == 2

                # Second call should be with NullCache fallback
                fallback_call = mock_cache.init_app.call_args_list[1]
                fallback_config = fallback_call[1]["config"]
                assert fallback_config["CACHE_TYPE"] == "NullCache"


class TestDirectoryPermissions:
    """Test that cache directories are created with secure permissions."""

    def test_dev_shm_directory_permissions(self):
        """Test that /dev/shm cache directory is created with 0o700 permissions."""
        with patch.dict(os.environ, {"NOW_LMS_MEMORY_CACHE": "1"}):
            with (
                patch("os.path.exists", return_value=False),
                patch("os.makedirs") as mock_makedirs,
                patch("builtins.open", create=True),
                patch("os.remove"),
            ):

                get_memory_cache_config()

                mock_makedirs.assert_called_with("/dev/shm/now_lms_cache", mode=0o700, exist_ok=True)

    def test_temp_directory_permissions(self):
        """Test that temp cache directory is created with 0o700 permissions."""
        with patch.dict(os.environ, {"NOW_LMS_MEMORY_CACHE": "1"}):
            with (
                patch("os.makedirs") as mock_makedirs,
                patch("os.path.exists", return_value=False),
                patch("tempfile.gettempdir", return_value="/tmp"),
                patch("builtins.open", create=True),
                patch("os.remove"),
            ):

                # First call (for /dev/shm) raises exception, second call (for temp) succeeds
                mock_makedirs.side_effect = [OSError("No /dev/shm"), None]

                get_memory_cache_config()

                # Check that both calls used secure permissions
                calls = mock_makedirs.call_args_list
                assert len(calls) == 2
                assert calls[0][1]["mode"] == 0o700  # /dev/shm call
                assert calls[1][1]["mode"] == 0o700  # temp dir call
