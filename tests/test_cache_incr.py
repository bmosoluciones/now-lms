# pylint: disable=redefined-outer-name
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.

"""Unit tests for cache_incr function (now_lms/cache.py)."""

from unittest import mock

import pytest
from flask import Flask


@pytest.fixture()
def app():
    """Minimal Flask app with cache initialized."""
    _app = Flask("test_app")
    _app.config["CACHE_TYPE"] = "SimpleCache"
    _app.config["CACHE_DEFAULT_TIMEOUT"] = 300
    from now_lms.cache import cache

    cache.init_app(_app, config={"CACHE_TYPE": "SimpleCache"})
    return _app


def _make_mock_cache(write_client=None, prefix=""):
    """Build a mock cache object with a controllable backend."""
    mock_cache = mock.MagicMock()
    mock_cache.get = mock.MagicMock(return_value=None)
    mock_cache.set = mock.MagicMock()

    mock_backend = mock.MagicMock()
    mock_backend._write_client = write_client
    mock_backend._get_prefix.return_value = prefix
    mock_cache.cache = mock_backend

    return mock_cache


class TestCacheIncrRedisNative:
    """Tests for the Redis native INCR path."""

    def test_uses_redis_incr_when_client_available(self, app):
        """cache_incr calls Redis INCR when _write_client exists."""
        mock_client = mock.MagicMock()
        mock_client.incr.return_value = 1
        mock_cache = _make_mock_cache(write_client=mock_client)

        with app.app_context(), mock.patch("now_lms.cache.cache", mock_cache):
            from now_lms.cache import cache_incr

            result = cache_incr("test_key")

        assert result == 1
        mock_client.incr.assert_called_once()

    def test_redis_incr_returns_correct_value(self, app):
        """Redis INCR return value is forwarded correctly."""
        mock_client = mock.MagicMock()
        mock_client.incr.return_value = 42
        mock_cache = _make_mock_cache(write_client=mock_client)

        with app.app_context(), mock.patch("now_lms.cache.cache", mock_cache):
            from now_lms.cache import cache_incr

            result = cache_incr("counter")

        assert result == 42

    def test_redis_incr_passes_prefix(self, app):
        """Key prefix from backend is prepended to the key."""
        mock_client = mock.MagicMock()
        mock_client.incr.return_value = 1
        mock_cache = _make_mock_cache(write_client=mock_client, prefix="now_lms:")

        with app.app_context(), mock.patch("now_lms.cache.cache", mock_cache):
            from now_lms.cache import cache_incr

            cache_incr("login_limit")

        mock_client.incr.assert_called_once_with(name="now_lms:login_limit", amount=1)

    def test_redis_incr_falls_back_on_exception(self, app):
        """Falls back to get+set when Redis INCR raises."""
        mock_client = mock.MagicMock()
        mock_client.incr.side_effect = Exception("Redis down")

        mock_cache = _make_mock_cache(write_client=mock_client)
        stored = {}

        def fake_get(key):
            return stored.get(key)

        def fake_set(key, value, timeout=None):
            stored[key] = value

        mock_cache.get = fake_get
        mock_cache.set = fake_set
        stored["fb_key"] = 5

        with app.app_context(), mock.patch("now_lms.cache.cache", mock_cache):
            from now_lms.cache import cache_incr

            result = cache_incr("fb_key", timeout=60)

        assert result == 6
        assert stored["fb_key"] == 6

    def test_redis_incr_no_client_fallback(self, app):
        """Falls back when _write_client is None (non-Redis backend)."""
        mock_cache = _make_mock_cache(write_client=None)
        stored = {}

        def fake_get(key):
            return stored.get(key)

        def fake_set(key, value, timeout=None):
            stored[key] = value

        mock_cache.get = fake_get
        mock_cache.set = fake_set
        stored["nc_key"] = 3

        with app.app_context(), mock.patch("now_lms.cache.cache", mock_cache):
            from now_lms.cache import cache_incr

            result = cache_incr("nc_key", timeout=60)

        assert result == 4
        assert stored["nc_key"] == 4


class TestCacheIncrFallback:
    """Tests for the get+set fallback path (non-Redis backends)."""

    def test_increments_from_none(self, app):
        """First call initializes counter at 1."""
        from now_lms.cache import cache_incr

        with app.app_context():
            result = cache_incr("new_key")

        assert result == 1

    def test_increments_existing_value(self, app):
        """Subsequent calls increment the stored value."""
        from now_lms.cache import cache, cache_incr

        with app.app_context():
            cache.set("counter", 10, timeout=60)
            result = cache_incr("counter", timeout=60)

        assert result == 11

    def test_multiple_increments(self, app):
        """Successive calls produce correct sequential values."""
        from now_lms.cache import cache_incr

        with app.app_context():
            results = [cache_incr("seq", timeout=60) for _ in range(5)]

        assert results == [1, 2, 3, 4, 5]

    def test_independent_keys(self, app):
        """Different keys maintain independent counters."""
        from now_lms.cache import cache_incr

        with app.app_context():
            a1 = cache_incr("key_a", timeout=60)
            b1 = cache_incr("key_b", timeout=60)
            a2 = cache_incr("key_a", timeout=60)
            b2 = cache_incr("key_b", timeout=60)

        assert a1 == 1
        assert b1 == 1
        assert a2 == 2
        assert b2 == 2

    def test_timeout_is_respected(self, app):
        """Timeout parameter is forwarded to cache.set."""
        from now_lms.cache import cache, cache_incr

        with app.app_context(), mock.patch.object(cache, "set") as mock_set:
            cache_incr("ttl_key", timeout=120)

        mock_set.assert_called_once_with("ttl_key", 1, timeout=120)


class TestCacheIncrIntegration:
    """Integration-style tests exercising the rate limit pattern."""

    def test_rate_limit_flow(self, app):
        """Simulates the _check_rate_limit pattern used in views."""
        from now_lms.cache import cache, cache_incr

        with app.app_context():
            key = "rate_limit_test"
            max_attempts = 3

            # First request: allowed, counter set to 1
            current = cache.get(key)
            assert current is None
            cache.set(key, 1, timeout=60)
            assert cache.get(key) == 1

            # Second request: allowed, counter incremented to 2
            current = cache.get(key)
            assert int(current) < max_attempts
            cache_incr(key, timeout=60)
            assert cache.get(key) == 2

            # Third request: allowed, counter incremented to 3
            current = cache.get(key)
            assert int(current) < max_attempts
            cache_incr(key, timeout=60)
            assert cache.get(key) == 3

            # Fourth request: blocked
            current = cache.get(key)
            assert int(current) >= max_attempts
