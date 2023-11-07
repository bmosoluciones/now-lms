# Copyright 2022 -2023 BMO Soluciones, S.A.
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
# Contributors:
# - William José Moreno Reyes

"""Configuración de cache."""


# ---------------------------------------------------------------------------------------
# Libreria estandar
# ---------------------------------------------------------------------------------------
from os import environ

# ---------------------------------------------------------------------------------------
# Librerias de terceros
# ---------------------------------------------------------------------------------------
from flask_caching import Cache

# ---------------------------------------------------------------------------------------
# Recursos locales
# ---------------------------------------------------------------------------------------
from now_lms.logs import log
from now_lms.config.parse_config_file import CONFIG_FROM_FILE


# < --------------------------------------------------------------------------------------------- >
# Configuracion de Cache
CACHE_CONFIG: dict = {"CACHE_KEY_PREFIX": "now_lms:"}

if CONFIG_FROM_FILE:  # pragma: no cover
    log.trace("Intentando leer configuración de cache desde archivo de configuración.")
else:  # pragma: no cover
    CONFIG_FROM_FILE = {}  # Empy dictionary to avoid errors

if not environ.get("NO_LMS_CACHE") and not CONFIG_FROM_FILE.get("NO_LMS_CACHE"):  # pragma: no cover
    CACHE_CONFIG["CACHE_DEFAULT_TIMEOUT"] = 300
    if (environ.get("CACHE_REDIS_HOST") or CONFIG_FROM_FILE.get("CACHE_REDIS_HOST")) and (
        environ.get("CACHE_REDIS_PORT") or CONFIG_FROM_FILE.get("CACHE_REDIS_PORT")
    ):
        CTYPE = "RedisCache"
        CACHE_CONFIG["CACHE_REDIS_HOST"] = environ.get("CACHE_REDIS_HOST")
        CACHE_CONFIG["CACHE_REDIS_PORT"] = environ.get("CACHE_REDIS_PORT")

    # CACHE_REDIS_URL=redis://localhost:6379/0
    elif (environ.get("CACHE_REDIS_URL") or CONFIG_FROM_FILE.get("CACHE_REDIS_URL")) or (
        environ.get("REDIS_URL") or CONFIG_FROM_FILE.get("REDIS_URL")
    ):
        CTYPE = "RedisCache"
        CACHE_CONFIG["CACHE_REDIS_URL"] = environ.get("CACHE_REDIS_URL") or environ.get("REDIS_URL")

    elif environ.get("CACHE_MEMCACHED_SERVERS") or CONFIG_FROM_FILE.get("CACHE_MEMCACHED_SERVERS"):
        CTYPE = "MemcachedCache"
        CACHE_CONFIG["CACHE_MEMCACHED_SERVERS"] = environ.get("CACHE_MEMCACHED_SERVERS")

    else:
        CTYPE = "NullCache"
        log.debug("No cache service configured.")

else:  # pragma: no cover
    CTYPE = "NullCache"

CACHE_CONFIG["CACHE_TYPE"] = CTYPE

if not CTYPE == "NullCache":
    log.trace("Utilizando para almacenamiento el servicio {type}", type=CTYPE)

cache: Cache = Cache(config=CACHE_CONFIG)
