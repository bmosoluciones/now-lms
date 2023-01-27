# Copyright 2022 - 2023 BMO Soluciones, S.A.
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

"""Configuración de la aplicación."""
# Libreria standar:
from os import environ, name, path, access, W_OK, R_OK, makedirs
from pathlib import Path
from typing import Dict

# Librerias de terceros:
from appdirs import AppDirs
from loguru import logger as log

# Recursos locales:
from now_lms.version import PRERELEASE

DESARROLLO: bool = (
    (PRERELEASE is not None) or ("FLASK_DEBUG" in environ) or (environ.get("FLASK_ENV") == "development") or ("CI" in environ)
)

# < --------------------------------------------------------------------------------------------- >
# Directorios base de la aplicacion
DIRECTORIO_APP: str = path.abspath(path.dirname(__file__))
DIRECTORIO_PRINCICIPAL: Path = Path(DIRECTORIO_APP).parent.absolute()
DIRECTORIO_PLANTILLAS: str = path.join(DIRECTORIO_APP, "templates")
DIRECTORIO_ARCHIVOS: str = path.join(DIRECTORIO_APP, "static")

# < --------------------------------------------------------------------------------------------- >
# Directorios utilizados para la carga de archivos.

DIRECTORIO_BASE_ARCHIVOS_USUARIO = path.join(DIRECTORIO_ARCHIVOS, "files")

if DESARROLLO:  # pragma: no cover
    DIRECTORIO_BASE_UPLOADS = DIRECTORIO_BASE_ARCHIVOS_USUARIO

else:  # pragma: no cover

    if name == "nt":
        DIRECTORIO_BASE_APP = AppDirs("NOW-LMS", "BMO Soluciones")
        DIRECTORIO_BASE_UPLOADS = path.join(DIRECTORIO_BASE_APP.site_data_dir, "files")

    else:
        UNIX_UPLOAD_DIR = str(Path("/var/www/now-lms/data"))

        if access(UNIX_UPLOAD_DIR, R_OK) and access(UNIX_UPLOAD_DIR, W_OK):  # pragma: no cover
            DIRECTORIO_BASE_UPLOADS = UNIX_UPLOAD_DIR

        else:
            DIRECTORIO_BASE_UPLOADS = DIRECTORIO_BASE_ARCHIVOS_USUARIO

DIRECTORIO_ARCHIVOS_PUBLICOS: str = path.join(DIRECTORIO_BASE_UPLOADS, "public")
DIRECTORIO_ARCHIVOS_PRIVADOS: str = path.join(DIRECTORIO_BASE_UPLOADS, "private")
DIRECTORIO_UPLOAD_IMAGENES: str = path.join(DIRECTORIO_ARCHIVOS_PUBLICOS, "images")
DIRECTORIO_UPLOAD_ARCHIVOS: str = path.join(DIRECTORIO_ARCHIVOS_PUBLICOS, "files")
DIRECTORIO_UPLOAD_AUDIO: str = path.join(DIRECTORIO_ARCHIVOS_PUBLICOS, "audio")

if not path.isdir(DIRECTORIO_BASE_UPLOADS):  # pragma: no cover
    try:
        makedirs(DIRECTORIO_BASE_UPLOADS)
        makedirs(DIRECTORIO_ARCHIVOS_PRIVADOS)
        makedirs(DIRECTORIO_ARCHIVOS_PUBLICOS)
        makedirs(DIRECTORIO_UPLOAD_ARCHIVOS)
        makedirs(DIRECTORIO_UPLOAD_IMAGENES)
    except OSError:
        log.warning("No se puede crear directorio para carga de archivos: {directorio}", directorio=DIRECTORIO_BASE_UPLOADS)

if access(DIRECTORIO_BASE_UPLOADS, R_OK) and access(DIRECTORIO_BASE_UPLOADS, W_OK):  # pragma: no cover
    log.debug("Directorio para carga de archivos es {directorio}", directorio=DIRECTORIO_BASE_UPLOADS)
else:
    log.warning(
        "No se tiene acceso a leer/escribir en directorio de carga de archivos {directorio}",
        directorio=DIRECTORIO_BASE_UPLOADS,
    )


# < --------------------------------------------------------------------------------------------- >
# Ubicación predeterminada de base de datos SQLITE
if name == "nt":  # pragma: no cover
    SQLITE: str = "sqlite:///" + str(DIRECTORIO_PRINCICIPAL) + "\\now_lms.db"
else:
    SQLITE = "sqlite:///" + str(DIRECTORIO_PRINCICIPAL) + "/now_lms.db"


# < --------------------------------------------------------------------------------------------- >
# Configuración de la aplicación, siguiendo "Twelve Factors App" las opciones se leen del entorno
# o se utilizan valores predeterminados.
CONFIGURACION: Dict = {
    "ADMIN_USER": environ.get("LMS_USER") or "lms-admin",
    "ADMIN_PSWD": environ.get("LMS_PSWD") or "lms-admin",
    "SECRET_KEY": environ.get("LMS_KEY") or "dev",
    "SQLALCHEMY_DATABASE_URI": environ.get("LMS_DB") or environ.get("DATABASE_URL") or SQLITE,
    "SQLALCHEMY_TRACK_MODIFICATIONS": "False",
    # Carga de Archivos: https://flask-reuploaded.readthedocs.io/en/latest/configuration/
    "UPLOADS_AUTOSERVE": True,
    "UPLOADED_FILES_DEST": DIRECTORIO_UPLOAD_ARCHIVOS,
    "UPLOADED_IMAGES_DEST": DIRECTORIO_UPLOAD_IMAGENES,
    "UPLOADED_AUDIO_DEST": DIRECTORIO_UPLOAD_AUDIO,
}

if DESARROLLO:  # pragma: no cover
    log.warning("Opciones de desarrollo detectadas, revise su configuración.")


if environ.get("SQLALCHEMY_ECHO"):  # pragma: no cover
    CONFIGURACION["SQLALCHEMY_ECHO"] = True


# Corrige URI de conexion a la base de datos si el usuario omite el drive apropiado.
if CONFIGURACION.get("SQLALCHEMY_DATABASE_URI"):  # pragma: no cover
    # En Heroku va a estar disponible psycopg2.
    # - https://devcenter.heroku.com/articles/connecting-heroku-postgres#connecting-in-python
    # - https://devcenter.heroku.com/changelog-items/2035
    if (environ.get("DYNO")) and ("postgres:" in CONFIGURACION.get("SQLALCHEMY_DATABASE_URI")):  # type: ignore[operator]
        DBURI: str = str(
            "postgresql" + CONFIGURACION.get("SQLALCHEMY_DATABASE_URI")[8:] + "?sslmode=require"  # type: ignore[index]
        )
        CONFIGURACION["SQLALCHEMY_DATABASE_URI"] = DBURI

    # Servicios como Elephantsql, Digital Ocean proveen una direccion de corrección que comienza con "postgres"
    # esta va a fallar con SQLAlchemy, se prefiere el drive pg8000 que no requere compilarse.
    elif "postgresql:" in CONFIGURACION.get("SQLALCHEMY_DATABASE_URI"):  # type: ignore[operator]
        DBURI = "postgresql+pg8000" + CONFIGURACION.get("SQLALCHEMY_DATABASE_URI")[10:]  # type: ignore[index]
        CONFIGURACION["SQLALCHEMY_DATABASE_URI"] = DBURI

    elif "postgres:" in CONFIGURACION.get("SQLALCHEMY_DATABASE_URI"):  # type: ignore[operator]
        DBURI = "postgresql+pg8000" + CONFIGURACION.get("SQLALCHEMY_DATABASE_URI")[8:]  # type: ignore[index]
        CONFIGURACION["SQLALCHEMY_DATABASE_URI"] = DBURI

    # Agrega driver de mysql:
    # - https://docs.sqlalchemy.org/en/14/dialects/mysql.html#module-sqlalchemy.dialects.mysql.pymysql
    elif "mysql:" in CONFIGURACION.get("SQLALCHEMY_DATABASE_URI"):  # type: ignore[operator]
        DBURI = "mysql+pymysql" + CONFIGURACION.get("SQLALCHEMY_DATABASE_URI")[5:]  # type: ignore[index]
        CONFIGURACION["SQLALCHEMY_DATABASE_URI"] = DBURI

    elif "mariadb:" in CONFIGURACION.get("SQLALCHEMY_DATABASE_URI"):  # type: ignore[operator]
        DBURI = "mariadb+pymysql" + CONFIGURACION.get("SQLALCHEMY_DATABASE_URI")[7:]  # type: ignore[index]
        CONFIGURACION["SQLALCHEMY_DATABASE_URI"] = DBURI

if "postgres" in CONFIGURACION.get("SQLALCHEMY_DATABASE_URI"):  # type: ignore[operator]
    DBType = "Postgres"  # pragma: no cover
if "mysql" in CONFIGURACION.get("SQLALCHEMY_DATABASE_URI"):  # type: ignore[operator]
    DBType = "MySQL"  # pragma: no cover
if "mariadb" in CONFIGURACION.get("SQLALCHEMY_DATABASE_URI"):  # type: ignore[operator]
    DBType = "MariaDB"  # pragma: no cover
if "sqlite" in CONFIGURACION.get("SQLALCHEMY_DATABASE_URI"):  # type: ignore[operator]
    DBType = "SQLite"  # pragma: no cover


# < --------------------------------------------------------------------------------------------- >
# Configuracion de Cache
CACHE_CONFIG: dict = {}

if not environ.get("NO_LMS_CACHE"):  # pragma: no cover

    CACHE_CONFIG["CACHE_DEFAULT_TIMEOUT"] = 300
    if environ.get("CACHE_REDIS_HOST") and environ.get("CACHE_REDIS_PORT"):
        CTYPE = "RedisCache"
        CACHE_CONFIG["CACHE_REDIS_HOST"] = environ.get("CACHE_REDIS_HOST")
        CACHE_CONFIG["CACHE_REDIS_PORT"] = environ.get("CACHE_REDIS_PORT")

    elif environ.get("CACHE_REDIS_URL") or environ.get("REDIS_URL"):
        CTYPE = "RedisCache"
        CACHE_CONFIG["CACHE_REDIS_URL"] = environ.get("CACHE_REDIS_URL") or environ.get("REDIS_URL")

    elif environ.get("CACHE_MEMCACHED_SERVERS"):
        CTYPE = "MemcachedCache"
        CACHE_CONFIG["CACHE_MEMCACHED_SERVERS"] = environ.get("CACHE_MEMCACHED_SERVERS")

    else:
        CTYPE = "SimpleCache"

else:
    CTYPE = "NullCache"

CACHE_CONFIG["CACHE_TYPE"] = CTYPE

log.info("Database: {type}.", type=DBType)
log.info("Cache: {type}", type=CTYPE)
