# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.

"""Unit tests for cache utilities (now_lms/cache_utils.py)."""

import os
import tempfile
from unittest import mock

import pytest
from flask import Flask

from now_lms.cache_utils import get_memory_cache_config, init_cache


def test_get_memory_cache_config_disabled():
    """Test get_memory_cache_config when memory cache is disabled."""
    with mock.patch.dict(os.environ, {"NOW_LMS_MEMORY_CACHE": "0"}):
        config = get_memory_cache_config()
        assert config == {"CACHE_TYPE": "NullCache"}


def test_get_memory_cache_config_enabled_shm_success():
    """Test get_memory_cache_config when /dev/shm is writeable."""
    with mock.patch.dict(os.environ, {"NOW_LMS_MEMORY_CACHE": "1"}):
        with mock.patch("os.path.exists", return_value=True), \
             mock.patch("builtins.open", mock.mock_open()), \
             mock.patch("os.remove") as mock_remove:
            config = get_memory_cache_config()
            assert config["CACHE_TYPE"] == "FileSystemCache"
            assert config["CACHE_DIR"] == "/dev/shm/now_lms_cache"
            mock_remove.assert_called_once()


def test_get_memory_cache_config_shm_fails_temp_success():
    """Test fallback to system temp dir when /dev/shm is not writeable."""
    with mock.patch.dict(os.environ, {"NOW_LMS_MEMORY_CACHE": "1"}):
        # Raise OSError when writing to /dev/shm, but succeed on temp directory
        def side_effect(filename, mode="r", encoding=None):
            if "/dev/shm" in filename:
                raise OSError("No permission")
            return mock.mock_open()()

        with mock.patch("os.path.exists", return_value=False), \
             mock.patch("os.makedirs"), \
             mock.patch("builtins.open", side_effect=side_effect), \
             mock.patch("os.remove"):
            config = get_memory_cache_config()
            assert config["CACHE_TYPE"] == "FileSystemCache"
            assert config["CACHE_DIR"] == os.path.join(tempfile.gettempdir(), "now_lms_cache")


def test_get_memory_cache_config_all_fail():
    """Test fallback to NullCache when both shm and temp dir fail."""
    with mock.patch.dict(os.environ, {"NOW_LMS_MEMORY_CACHE": "1"}):
        with mock.patch("os.path.exists", return_value=False), \
             mock.patch("os.makedirs", side_effect=OSError("Drive full")), \
             mock.patch("builtins.open", side_effect=OSError("No write access")):
            config = get_memory_cache_config()
            assert config == {"CACHE_TYPE": "NullCache"}


def test_init_cache_redis():
    """Test init_cache when Redis environment variables are configured."""
    app = Flask("test_app")
    with mock.patch.dict(os.environ, {"CACHE_REDIS_URL": "redis://localhost:6379/0"}):
        from now_lms.cache import cache
        with mock.patch.object(cache, "init_app") as mock_init_app:
            init_cache(app)
            # The config passed should use RedisCache
            called_config = mock_init_app.call_args[1]["config"]
            assert called_config["CACHE_TYPE"] == "RedisCache"
            assert called_config["CACHE_REDIS_URL"] == "redis://localhost:6379/0"


def test_init_cache_redis_fallback():
    """Test init_cache with REDIS_URL fallback."""
    app = Flask("test_app")
    with mock.patch.dict(os.environ, {"REDIS_URL": "redis://localhost:6379/1"}):
        from now_lms.cache import cache
        with mock.patch.object(cache, "init_app") as mock_init_app:
            init_cache(app)
            called_config = mock_init_app.call_args[1]["config"]
            assert called_config["CACHE_TYPE"] == "RedisCache"
            assert called_config["CACHE_REDIS_URL"] == "redis://localhost:6379/1"


def test_init_cache_memcached():
    """Test init_cache when Memcached servers are configured."""
    app = Flask("test_app")
    with mock.patch.dict(os.environ, {"CACHE_MEMCACHED_SERVERS": "localhost:11211"}):
        from now_lms.cache import cache
        with mock.patch.object(cache, "init_app") as mock_init_app:
            init_cache(app)
            called_config = mock_init_app.call_args[1]["config"]
            assert called_config["CACHE_TYPE"] == "MemcachedCache"
            assert called_config["CACHE_MEMCACHED_SERVERS"] == "localhost:11211"


def test_init_cache_app_overrides():
    """Test init_cache respects explicitly set app config overrides."""
    app = Flask("test_app")
    app.config["CACHE_TYPE"] = "SimpleCache"
    app.config["CACHE_THRESHOLD"] = 1000

    from now_lms.cache import cache
    with mock.patch.object(cache, "init_app") as mock_init_app:
        init_cache(app)
        called_config = mock_init_app.call_args[1]["config"]
        assert called_config["CACHE_TYPE"] == "SimpleCache"
        assert called_config["CACHE_THRESHOLD"] == 1000


def test_init_cache_exception_fallback():
    """Test that cache initialization exception falls back to NullCache."""
    app = Flask("test_app")
    from now_lms.cache import cache
    with mock.patch.object(cache, "init_app", side_effect=[Exception("Initialization failed"), None]) as mock_init_app:
        init_cache(app)
        # Should be called twice (the first fail, then fallback)
        assert mock_init_app.call_count == 2
        # The second call must be with NullCache
        last_called_config = mock_init_app.call_args_list[-1][1]["config"]
        assert last_called_config == {"CACHE_TYPE": "NullCache"}
