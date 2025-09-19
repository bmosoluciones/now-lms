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
def _get_cache_type_for_compatibility() -> str:
    """Determine cache type for backward compatibility with existing code."""
    if (environ.get("CACHE_REDIS_URL")) or (environ.get("REDIS_URL")):
        return "RedisCache"
    if environ.get("CACHE_MEMCACHED_SERVERS"):
        return "MemcachedCache"
    if environ.get("NOW_LMS_MEMORY_CACHE", "0") == "1":
        return "FileSystemCache"
    return "NullCache"


def _get_cache_config_for_compatibility() -> dict[str, object]:
    """Get basic cache config for backward compatibility."""
    config = {"CACHE_KEY_PREFIX": "now_lms:", "CACHE_DEFAULT_TIMEOUT": 300}

    if (environ.get("CACHE_REDIS_URL")) or (environ.get("REDIS_URL")):
        config["CACHE_TYPE"] = "RedisCache"
        config["CACHE_REDIS_URL"] = environ.get("CACHE_REDIS_URL") or environ.get("REDIS_URL")
    elif environ.get("CACHE_MEMCACHED_SERVERS"):
        config["CACHE_TYPE"] = "MemcachedCache"
        config["CACHE_MEMCACHED_SERVERS"] = environ.get("CACHE_MEMCACHED_SERVERS")
    elif environ.get("NOW_LMS_MEMORY_CACHE", "0") == "1":
        config["CACHE_TYPE"] = "FileSystemCache"
        # Note: CACHE_DIR will be determined dynamically by cache_utils
    else:
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
    return current_user and current_user.is_authenticated


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
