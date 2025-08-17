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
CACHE_CONFIG: dict = {"CACHE_KEY_PREFIX": "now_lms:"}
CACHE_CONFIG["CACHE_DEFAULT_TIMEOUT"] = 300

if (environ.get("CACHE_REDIS_URL")) or (environ.get("REDIS_URL")):
    # EXAMPLE= REDIS_URL=redis://localhost:6379/0
    CTYPE = "RedisCache"
    CACHE_CONFIG["CACHE_REDIS_URL"] = environ.get("CACHE_REDIS_URL") or environ.get("REDIS_URL")

elif environ.get("CACHE_MEMCACHED_SERVERS"):
    CTYPE = "MemcachedCache"
    CACHE_CONFIG["CACHE_MEMCACHED_SERVERS"] = environ.get("CACHE_MEMCACHED_SERVERS")

else:
    CTYPE = "NullCache"
    log.debug("No cache service configured.")


CACHE_CONFIG["CACHE_TYPE"] = CTYPE

if CTYPE != "NullCache":
    log.trace(f"Using {CTYPE} service for storage")

cache: Cache = Cache(config=CACHE_CONFIG)


# ---------------------------------------------------------------------------------------
# Opciones de cache.
# ---------------------------------------------------------------------------------------
def no_guardar_en_cache_global():
    """Si el usuario es anomino preferimos usar el sistema de cache."""
    return current_user and current_user.is_authenticated


def invalidate_all_cache():
    """Invalida toda la cache del sistema cuando cambia el tema."""
    try:
        if CTYPE != "NullCache":
            cache.clear()
            log.trace("Cache invalidated due to theme change")
        return True
    except Exception as e:
        log.error(f"Error invalidating cache: {e}")
        return False
