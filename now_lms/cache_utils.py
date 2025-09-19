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

"""Utilidades de inicialización de cache en memoria."""


from __future__ import annotations

# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------
import os
import tempfile

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------
from flask import Flask

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms.logs import log


def get_memory_cache_config() -> dict[str, object]:
    """
    Determine cache configuration for memory-based cache.

    Returns:
        Dictionary with cache configuration.
        Falls back to NullCache if FileSystemCache cannot be initialized.
    """
    use_memory_cache = os.getenv("NOW_LMS_MEMORY_CACHE", "0") == "1"
    if not use_memory_cache:
        log.debug("Memory cache disabled via environment variable.")
        return {"CACHE_TYPE": "NullCache"}

    # Try to set up FileSystemCache with fallback logic
    cache_dir = None

    # First try: /dev/shm (Linux tmpfs in memory)
    try:
        cache_dir = "/dev/shm/now_lms_cache"  # nosec B108 - Intentional use of /dev/shm for memory-based cache
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir, mode=0o700, exist_ok=True)

        # Test if we can write to this directory
        with open(test_file := os.path.join(cache_dir, ".test_write"), "w", encoding="utf-8") as f:
            f.write("test")
        os.remove(test_file)

        log.info(f"Using memory cache directory: {cache_dir}")

    except OSError as e:
        log.debug(f"Cannot use /dev/shm for cache: {e}")
        cache_dir = None

    # Second try: system temp directory
    if cache_dir is None:
        try:
            if not os.path.exists(cache_dir := os.path.join(tempfile.gettempdir(), "now_lms_cache")):
                os.makedirs(cache_dir, mode=0o700, exist_ok=True)

            # Test write access
            with open(test_file := os.path.join(cache_dir, ".test_write"), "w", encoding="utf-8") as f:
                f.write("test")
            os.remove(test_file)

            log.info(f"Using temp cache directory: {cache_dir}")

        except OSError as e:
            log.warning(f"Cannot use temp directory for cache: {e}")
            cache_dir = None

    # Final fallback: NullCache
    if cache_dir is None:
        log.warning("FileSystemCache initialization failed, falling back to NullCache")
        return {"CACHE_TYPE": "NullCache"}

    return {
        "CACHE_TYPE": "FileSystemCache",
        "CACHE_DIR": cache_dir,
        "CACHE_DEFAULT_TIMEOUT": 300,
        "CACHE_KEY_PREFIX": "now_lms:",
    }


def init_cache(app: Flask) -> None:
    """
    Initialize cache for the Flask application.

    This function handles the logic for determining which cache backend to use
    based on environment variables, with proper fallback behavior.

    Args:
        app: Flask application instance
    """
    # Get existing cache configuration from environment variables
    from os import environ

    from now_lms.cache import cache

    # Check for external cache services first (Redis, Memcached)
    cache_config: dict[str, object]
    if (environ.get("CACHE_REDIS_URL")) or (environ.get("REDIS_URL")):
        # Redis cache takes precedence
        cache_config = {
            "CACHE_TYPE": "RedisCache",
            "CACHE_REDIS_URL": environ.get("CACHE_REDIS_URL") or environ.get("REDIS_URL"),
            "CACHE_KEY_PREFIX": "now_lms:",
            "CACHE_DEFAULT_TIMEOUT": 300,
        }
        log.trace("Using RedisCache service for storage")

    elif environ.get("CACHE_MEMCACHED_SERVERS"):
        # Memcached cache
        cache_config = {
            "CACHE_TYPE": "MemcachedCache",
            "CACHE_MEMCACHED_SERVERS": environ.get("CACHE_MEMCACHED_SERVERS"),
            "CACHE_KEY_PREFIX": "now_lms:",
            "CACHE_DEFAULT_TIMEOUT": 300,
        }
        log.trace("Using MemcachedCache service for storage")

    else:
        # Check for memory cache or fall back to NullCache
        cache_config = get_memory_cache_config()
        if cache_config["CACHE_TYPE"] == "FileSystemCache":
            log.trace("Using FileSystemCache for storage")
        else:
            log.debug("No cache service configured.")

    # Allow config_overrides to override cache settings if needed
    if hasattr(app, "config") and "CACHE_TYPE" in app.config:
        # If app config explicitly sets CACHE_TYPE, respect it
        cache_config.update({key: value for key, value in app.config.items() if key.startswith("CACHE_")})
        log.debug("Using cache configuration from app config overrides")

    # Initialize cache with the determined configuration
    try:
        cache.init_app(app, config=cache_config)
        log.trace(f"Cache initialized successfully with type: {cache_config['CACHE_TYPE']}")
    except Exception as e:
        log.error(f"Failed to initialize cache, falling back to NullCache: {e}")
        # Last resort fallback to NullCache
        fallback_config = {"CACHE_TYPE": "NullCache"}
        cache.init_app(app, config=fallback_config)
