# Copyright 2022 BMO Soluciones, S.A.
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
from os import environ, name, path
from pathlib import Path
from typing import Dict

# Librerias de terceros:
from flask_uploads import IMAGES, UploadSet
from loguru import logger as log

# Recursos locales:
from now_lms.version import PRERELEASE

DESARROLLO: bool = (
    (PRERELEASE is not None) or ("FLASK_DEBUG" in environ) or (environ.get("FLASK_ENV") == "development") or ("CI" in environ)
)

# < --------------------------------------------------------------------------------------------- >
# Directorios de la aplicacion
DIRECTORIO_APP: str = path.abspath(path.dirname(__file__))
DIRECTORIO_PRINCICIPAL: Path = Path(DIRECTORIO_APP).parent.absolute()
DIRECTORIO_PLANTILLAS: str = path.join(DIRECTORIO_APP, "templates")
DIRECTORIO_ARCHIVOS: str = path.join(DIRECTORIO_APP, "static")
DIRECTORIO_BASE_ARCHIVOS_DE_USUARIO: str = path.join(DIRECTORIO_APP, "static", "files")
DIRECTORIO_ARCHIVOS_PUBLICOS: str = path.join(DIRECTORIO_BASE_ARCHIVOS_DE_USUARIO, "public")
DIRECTORIO_ARCHIVOS_PRIVADOS: str = path.join(DIRECTORIO_BASE_ARCHIVOS_DE_USUARIO, "private")


# < --------------------------------------------------------------------------------------------- >
# Directorios utilizados para la carga de archivos.
DIRECTORIO_IMAGENES: str = path.join(DIRECTORIO_ARCHIVOS_PUBLICOS, "img")
CARGA_IMAGENES = UploadSet("photos", IMAGES)

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
    # Carga de archivos
    "UPLOADED_PHOTOS_DEST": DIRECTORIO_IMAGENES,
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
    log.debug("Database type is Postgres.")  # pragma: no cover
if "mysql" in CONFIGURACION.get("SQLALCHEMY_DATABASE_URI"):  # type: ignore[operator]
    log.debug("Database type is MySQL.")  # pragma: no cover
if "mariadb" in CONFIGURACION.get("SQLALCHEMY_DATABASE_URI"):  # type: ignore[operator]
    log.debug("Database type is MariaDB.")  # pragma: no cover
if "sqlite" in CONFIGURACION.get("SQLALCHEMY_DATABASE_URI"):  # type: ignore[operator]
    log.debug("Database type is SQLite.")  # pragma: no cover


# < --------------------------------------------------------------------------------------------- >
# Configuracion de Cache
CACHE_CONFIG: dict = {}
CACHE_CONFIG["CACHE_DEFAULT_TIMEOUT"] = 300

REDIS = (
    environ.get("CACHE_REDIS_HOST")
    and environ.get("CACHE_REDIS_PORT")  # noqa: W503
    and environ.get("CACHE_REDIS_PASSWORD")  # noqa: W503
    and environ.get("CACHE_REDIS_DB")  # noqa: W503
) or environ.get(
    "CACHE_REDIS_URL"
)  # noqa: W503

MEMCACHED = environ.get("CACHE_MEMCACHED_SERVERS")

if REDIS:
    CACHE_CONFIG["CACHE_TYPE"] = "RedisCache"
elif MEMCACHED:
    CACHE_CONFIG["CACHE_TYPE"] = "MemcachedCache"
else:
    CACHE_CONFIG["CACHE_TYPE"] = "SimpleCache"
