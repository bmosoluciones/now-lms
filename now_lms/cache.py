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

"""Configuración de cache."""


from __future__ import annotations

# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------
from os import environ

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------
from flask_caching import Cache
from flask_login import current_user

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms.logs import log

# < --------------------------------------------------------------------------------------------- >
# Configuracion de Cache


# For backward compatibility, we need to maintain CTYPE and CACHE_CONFIG
# The actual cache initialization will be handled by cache_utils.py
def _determine_cache_type() -> str:
    """Helper to determine which cache type is configured via environment variables."""
    if (environ.get("CACHE_REDIS_URL")) or (environ.get("REDIS_URL")):
        return "redis"
    if environ.get("CACHE_MEMCACHED_SERVERS"):
        return "memcached"
    if environ.get("NOW_LMS_MEMORY_CACHE", "0") == "1":
        return "filesystem"
    return "null"


def _get_cache_type_for_compatibility() -> str:
    """Determine cache type for backward compatibility with existing code."""
    cache_type = _determine_cache_type()

    match cache_type:
        case "redis":
            return "RedisCache"
        case "memcached":
            return "MemcachedCache"
        case "filesystem":
            return "FileSystemCache"
        case _:
            return "NullCache"


def _get_cache_config_for_compatibility() -> dict[str, object]:
    """Get basic cache config for backward compatibility."""
    config: dict[str, object] = {"CACHE_KEY_PREFIX": "now_lms:", "CACHE_DEFAULT_TIMEOUT": 300}

    cache_type = _determine_cache_type()

    match cache_type:
        case "redis":
            config["CACHE_TYPE"] = "RedisCache"
            config["CACHE_REDIS_URL"] = environ.get("CACHE_REDIS_URL") or environ.get("REDIS_URL")
        case "memcached":
            config["CACHE_TYPE"] = "MemcachedCache"
            config["CACHE_MEMCACHED_SERVERS"] = environ.get("CACHE_MEMCACHED_SERVERS")
        case "filesystem":
            config["CACHE_TYPE"] = "FileSystemCache"
            # Note: CACHE_DIR will be determined dynamically by cache_utils
        case _:
            config["CACHE_TYPE"] = "NullCache"

    return config


# Maintain backward compatibility
CTYPE = _get_cache_type_for_compatibility()
CACHE_CONFIG = _get_cache_config_for_compatibility()

if CTYPE != "NullCache":
    log.trace(f"Using {CTYPE} service for storage")
elif CTYPE == "NullCache" and environ.get("NOW_LMS_MEMORY_CACHE", "0") != "1":
    log.debug("No cache service configured.")

# Create cache instance (will be properly initialized via cache_utils.init_cache)
cache: Cache = Cache()


# ---------------------------------------------------------------------------------------
# Opciones de cache.
# ---------------------------------------------------------------------------------------
def no_guardar_en_cache_global() -> bool:
    """Si el usuario es anomino preferimos usar el sistema de cache."""
    # Return True (don't cache) when user is authenticated
    # Return False (do cache) when user is anonymous
    # IMPORTANT: This only controls whether to WRITE to cache, not whether to READ from it
    # If an anonymous user's cached page exists, authenticated users will still see it
    # unless we use a different cache key per authentication state
    return current_user and current_user.is_authenticated


def cache_key_with_auth_state() -> str:
    """Generate cache key that includes authentication state.

    This ensures authenticated and anonymous users get different cached versions
    of the same page, preventing authenticated users from seeing cached anonymous
    pages (and vice versa).
    """
    from flask import request

    # Include authentication state in the cache key
    auth_state = "auth" if (current_user and current_user.is_authenticated) else "anon"

    # Build key from request path and auth state
    key = f"view/{request.path}/{auth_state}"

    # Include query parameters if present
    if request.query_string:
        key += f"?{request.query_string.decode('utf-8')}"

    return key


def invalidate_all_cache() -> bool:
    """Invalida toda la cache del sistema cuando cambia el tema."""
    try:
        if CTYPE != "NullCache":
            cache.clear()
            log.trace("Cache invalidated due to theme change")
        return True
    except Exception as e:
        log.error(f"Error invalidating cache: {e}")
        return False
