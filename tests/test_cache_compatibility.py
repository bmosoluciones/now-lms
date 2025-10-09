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

"""Tests for cache compatibility functions refactored to use match/case."""

import os
from unittest.mock import patch


class TestCacheCompatibilityFunctions:
    """Test cache compatibility functions with match/case pattern."""

    def test_get_cache_type_redis_from_cache_redis_url(self):
        """Test that RedisCache is returned when CACHE_REDIS_URL is set."""
        with patch.dict(os.environ, {"CACHE_REDIS_URL": "redis://localhost:6379"}, clear=True):
            from now_lms.cache import _get_cache_type_for_compatibility

            assert _get_cache_type_for_compatibility() == "RedisCache"

    def test_get_cache_type_redis_from_redis_url(self):
        """Test that RedisCache is returned when REDIS_URL is set."""
        with patch.dict(os.environ, {"REDIS_URL": "redis://localhost:6379"}, clear=True):
            from now_lms.cache import _get_cache_type_for_compatibility

            assert _get_cache_type_for_compatibility() == "RedisCache"

    def test_get_cache_type_memcached(self):
        """Test that MemcachedCache is returned when CACHE_MEMCACHED_SERVERS is set."""
        with patch.dict(os.environ, {"CACHE_MEMCACHED_SERVERS": "localhost:11211"}, clear=True):
            from now_lms.cache import _get_cache_type_for_compatibility

            assert _get_cache_type_for_compatibility() == "MemcachedCache"

    def test_get_cache_type_filesystem(self):
        """Test that FileSystemCache is returned when NOW_LMS_MEMORY_CACHE=1."""
        with patch.dict(os.environ, {"NOW_LMS_MEMORY_CACHE": "1"}, clear=True):
            from now_lms.cache import _get_cache_type_for_compatibility

            assert _get_cache_type_for_compatibility() == "FileSystemCache"

    def test_get_cache_type_null_default(self):
        """Test that NullCache is returned when no cache is configured."""
        with patch.dict(os.environ, {}, clear=True):
            from now_lms.cache import _get_cache_type_for_compatibility

            assert _get_cache_type_for_compatibility() == "NullCache"

    def test_get_cache_type_null_when_memory_cache_zero(self):
        """Test that NullCache is returned when NOW_LMS_MEMORY_CACHE=0."""
        with patch.dict(os.environ, {"NOW_LMS_MEMORY_CACHE": "0"}, clear=True):
            from now_lms.cache import _get_cache_type_for_compatibility

            assert _get_cache_type_for_compatibility() == "NullCache"

    def test_get_cache_config_redis(self):
        """Test cache config for Redis."""
        with patch.dict(os.environ, {"CACHE_REDIS_URL": "redis://localhost:6379"}, clear=True):
            from now_lms.cache import _get_cache_config_for_compatibility

            config = _get_cache_config_for_compatibility()
            assert config["CACHE_TYPE"] == "RedisCache"
            assert config["CACHE_REDIS_URL"] == "redis://localhost:6379"
            assert config["CACHE_KEY_PREFIX"] == "now_lms:"
            assert config["CACHE_DEFAULT_TIMEOUT"] == 300

    def test_get_cache_config_redis_prefers_cache_redis_url(self):
        """Test that CACHE_REDIS_URL is preferred over REDIS_URL."""
        with patch.dict(os.environ, {"CACHE_REDIS_URL": "redis://cache:6379", "REDIS_URL": "redis://other:6379"}, clear=True):
            from now_lms.cache import _get_cache_config_for_compatibility

            config = _get_cache_config_for_compatibility()
            assert config["CACHE_TYPE"] == "RedisCache"
            assert config["CACHE_REDIS_URL"] == "redis://cache:6379"

    def test_get_cache_config_redis_fallback_to_redis_url(self):
        """Test that REDIS_URL is used when CACHE_REDIS_URL is not set."""
        with patch.dict(os.environ, {"REDIS_URL": "redis://localhost:6379"}, clear=True):
            from now_lms.cache import _get_cache_config_for_compatibility

            config = _get_cache_config_for_compatibility()
            assert config["CACHE_TYPE"] == "RedisCache"
            assert config["CACHE_REDIS_URL"] == "redis://localhost:6379"

    def test_get_cache_config_memcached(self):
        """Test cache config for Memcached."""
        with patch.dict(os.environ, {"CACHE_MEMCACHED_SERVERS": "localhost:11211"}, clear=True):
            from now_lms.cache import _get_cache_config_for_compatibility

            config = _get_cache_config_for_compatibility()
            assert config["CACHE_TYPE"] == "MemcachedCache"
            assert config["CACHE_MEMCACHED_SERVERS"] == "localhost:11211"
            assert config["CACHE_KEY_PREFIX"] == "now_lms:"
            assert config["CACHE_DEFAULT_TIMEOUT"] == 300

    def test_get_cache_config_filesystem(self):
        """Test cache config for FileSystemCache."""
        with patch.dict(os.environ, {"NOW_LMS_MEMORY_CACHE": "1"}, clear=True):
            from now_lms.cache import _get_cache_config_for_compatibility

            config = _get_cache_config_for_compatibility()
            assert config["CACHE_TYPE"] == "FileSystemCache"
            assert config["CACHE_KEY_PREFIX"] == "now_lms:"
            assert config["CACHE_DEFAULT_TIMEOUT"] == 300
            # CACHE_DIR should not be set - determined dynamically by cache_utils
            assert "CACHE_DIR" not in config

    def test_get_cache_config_null_default(self):
        """Test cache config for NullCache (default)."""
        with patch.dict(os.environ, {}, clear=True):
            from now_lms.cache import _get_cache_config_for_compatibility

            config = _get_cache_config_for_compatibility()
            assert config["CACHE_TYPE"] == "NullCache"
            assert config["CACHE_KEY_PREFIX"] == "now_lms:"
            assert config["CACHE_DEFAULT_TIMEOUT"] == 300

    def test_cache_priority_redis_over_memcached(self):
        """Test that Redis is preferred when both Redis and Memcached are configured."""
        with patch.dict(
            os.environ, {"CACHE_REDIS_URL": "redis://localhost:6379", "CACHE_MEMCACHED_SERVERS": "localhost:11211"}, clear=True
        ):
            from now_lms.cache import _get_cache_type_for_compatibility

            assert _get_cache_type_for_compatibility() == "RedisCache"

    def test_cache_priority_memcached_over_filesystem(self):
        """Test that Memcached is preferred when both Memcached and FileSystem are configured."""
        with patch.dict(os.environ, {"CACHE_MEMCACHED_SERVERS": "localhost:11211", "NOW_LMS_MEMORY_CACHE": "1"}, clear=True):
            from now_lms.cache import _get_cache_type_for_compatibility

            assert _get_cache_type_for_compatibility() == "MemcachedCache"
