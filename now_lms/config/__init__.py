# Copyright 2022 - 2024 BMO Soluciones, S.A.
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
# ---------------------------------------------------------------------------------------
# Libreria estandar
# ---------------------------------------------------------------------------------------
from os import R_OK, W_OK, access, environ, makedirs, name, path
from pathlib import Path
from sys import stderr
from typing import TYPE_CHECKING, Dict

# ---------------------------------------------------------------------------------------
# Librerias de terceros
# ---------------------------------------------------------------------------------------
from appdirs import AppDirs
from flask_uploads import AUDIO, DOCUMENTS, IMAGES, UploadSet

# ---------------------------------------------------------------------------------------
# Recursos locales
# ---------------------------------------------------------------------------------------
from now_lms.logs import LOG_FORMAT, log

if TYPE_CHECKING:
    from flask import Flask

# < --------------------------------------------------------------------------------------------- >
# Configuración central de la aplicación.
DESARROLLO = environ.get("CI") or environ.get("DEBUG") or False


if DESARROLLO:
    log.remove()
    log.add(stderr, level="TRACE", format=LOG_FORMAT, colorize=True)
    log.warning("Opciones de desarrollo detectadas.")


# < --------------------------------------------------------------------------------------------- >
# Directorios base de la aplicacion
DIRECTORIO_ACTUAL: Path = Path(path.abspath(path.dirname(__file__)))
DIRECTORIO_APP: Path = DIRECTORIO_ACTUAL.parent.absolute()
DIRECTORIO_PLANTILLAS_BASE: str = path.join(DIRECTORIO_APP, "templates")
DIRECTORIO_ARCHIVOS_BASE: str = path.join(DIRECTORIO_APP, "static")
DIRECTORIO_BASE_APP: AppDirs = AppDirs("NOW-LMS", "BMO Soluciones")
DIRECTORIO_PRINCICIPAL: Path = Path(DIRECTORIO_APP).parent.absolute()

LOGS_MAX_MB = "10 MB"

# < --------------------------------------------------------------------------------------------- >
if not DESARROLLO or environ.get("NOTLOGTOFILE") == "1":
    LOG_FILE = "now_lms.log"
    GLOBAL_LOG_FILE = path.join("/var/log/nowlms", LOG_FILE)
    LOCAL_LOG_FILE = path.join(DIRECTORIO_BASE_APP.user_log_dir, LOG_FILE)
    if access(GLOBAL_LOG_FILE, W_OK):
        log.add(GLOBAL_LOG_FILE, rotation=LOGS_MAX_MB, level="INFO", format=LOG_FORMAT)
    elif access(LOCAL_LOG_FILE, W_OK):
        log.add(LOCAL_LOG_FILE, rotation=LOGS_MAX_MB, level="INFO", format=LOG_FORMAT)
    else:
        log.add(LOG_FILE, rotation=LOGS_MAX_MB, level="INFO", format=LOG_FORMAT)

# < --------------------------------------------------------------------------------------------- >
# Directorios personalizados para la aplicación.
if environ.get("CUSTOM_DATA_DIR"):
    log.trace("Configuración de directorio de datos encontrada en variables de entorno.")
    DIRECTORIO_ARCHIVOS = environ.get("CUSTOM_DATA_DIR")
else:
    DIRECTORIO_ARCHIVOS = DIRECTORIO_ARCHIVOS_BASE

if environ.get("CUSTOM_THEMES_DIR"):
    log.trace("Configuración de directorio de temas encontrada en variables de entorno.")
    DIRECTORIO_PLANTILLAS = environ.get("CUSTOM_THEMES_DIR")
else:
    DIRECTORIO_PLANTILLAS = DIRECTORIO_PLANTILLAS_BASE

# < --------------------------------------------------------------------------------------------- >
# Directorios utilizados para la carga de archivos.
DIRECTORIO_BASE_ARCHIVOS_USUARIO = Path(path.join(str(DIRECTORIO_ARCHIVOS), "files"))
DIRECTORIO_ARCHIVOS_PUBLICOS: str = path.join(DIRECTORIO_BASE_ARCHIVOS_USUARIO, "public")
DIRECTORIO_ARCHIVOS_PRIVADOS: str = path.join(DIRECTORIO_BASE_ARCHIVOS_USUARIO, "private")
DIRECTORIO_UPLOAD_IMAGENES: str = path.join(DIRECTORIO_ARCHIVOS_PUBLICOS, "images")
DIRECTORIO_UPLOAD_ARCHIVOS: str = path.join(DIRECTORIO_ARCHIVOS_PUBLICOS, "files")
DIRECTORIO_UPLOAD_AUDIO: str = path.join(DIRECTORIO_ARCHIVOS_PUBLICOS, "audio")

if not path.isdir(DIRECTORIO_BASE_ARCHIVOS_USUARIO):  # pragma: no cover
    try:
        makedirs(DIRECTORIO_BASE_ARCHIVOS_USUARIO)
        makedirs(DIRECTORIO_ARCHIVOS_PRIVADOS)
        makedirs(DIRECTORIO_ARCHIVOS_PUBLICOS)
        makedirs(DIRECTORIO_UPLOAD_ARCHIVOS)
        makedirs(DIRECTORIO_UPLOAD_IMAGENES)
        makedirs(DIRECTORIO_UPLOAD_AUDIO)
    except OSError:  # pragma: no cover
        log.warning(
            "No se puede crear directorio para carga de archivos: {directorio}", directorio=DIRECTORIO_BASE_ARCHIVOS_USUARIO
        )
if access(DIRECTORIO_BASE_ARCHIVOS_USUARIO, R_OK) and access(DIRECTORIO_BASE_ARCHIVOS_USUARIO, W_OK):  # pragma: no cover
    log.trace("Acceso verificado a: {file}", file=DIRECTORIO_BASE_ARCHIVOS_USUARIO)
else:
    log.error("No se tiene acceso a subir archivos al directorio: {dir}", dir=DIRECTORIO_BASE_ARCHIVOS_USUARIO)

# < --------------------------------------------------------------------------------------------- >
# Directorio base temas.
DIRECTORIO_BASE_UPLOADS = Path(str(path.join(str(DIRECTORIO_ARCHIVOS), "files")))

# < --------------------------------------------------------------------------------------------- >
# Ubicación predeterminada de base de datos SQLITE
if environ.get("CI"):
    SQLITE: str = "sqlite://"
else:
    if name == "nt":  # pragma: no cover
        SQLITE = "sqlite:///" + str(DIRECTORIO_PRINCICIPAL) + "\\now_lms.db"
    else:
        SQLITE = "sqlite:///" + str(DIRECTORIO_PRINCICIPAL) + "/now_lms.db"


# < --------------------------------------------------------------------------------------------- >
# Configuración de la aplicación:
# Se siguen las recomendaciones de "Twelve Factors App" y las opciones se leen del entorno.

CONFIGURACION: Dict = {}
CONFIGURACION["SECRET_KEY"] = environ.get("SECRET_KEY") or "dev"  # nosec
CONFIGURACION["SQLALCHEMY_DATABASE_URI"] = environ.get("LMS_DB") or environ.get("DATABASE_URL") or SQLITE  # nosec
# Opciones comunes de configuración.
CONFIGURACION["PRESERVE_CONTEXT_ON_EXCEPTION"] = False
# Carga de Archivos: https://flask-reuploaded.readthedocs.io/en/latest/configuration/
CONFIGURACION["UPLOADS_AUTOSERVE"] = True
CONFIGURACION["UPLOADED_FILES_DEST"] = DIRECTORIO_UPLOAD_ARCHIVOS
CONFIGURACION["UPLOADED_IMAGES_DEST"] = DIRECTORIO_UPLOAD_IMAGENES
CONFIGURACION["UPLOADED_AUDIO_DEST"] = DIRECTORIO_UPLOAD_AUDIO

if DESARROLLO:
    log.warning("Utilizando configuración predeterminada.")
    log.info("La configuración predeterminada no se recomienda para uso en entornos reales.")
    CONFIGURACION["SQLALCHEMY_TRACK_MODIFICATIONS"] = "False"
    CONFIGURACION["TEMPLATES_AUTO_RELOAD"] = True


# Corrige URI de conexion a la base de datos si el usuario omite el driver apropiado.
if CONFIGURACION.get("SQLALCHEMY_DATABASE_URI"):  # pragma: no cover
    # En Heroku va a estar disponible psycopg2.
    # - https://devcenter.heroku.com/articles/connecting-heroku-postgres#connecting-in-python
    # - https://devcenter.heroku.com/changelog-items/2035
    if (environ.get("DYNO")) and ("postgres:" in CONFIGURACION.get("SQLALCHEMY_DATABASE_URI")):  # type: ignore[operator]
        DBURI: str = str(
            "postgresql" + CONFIGURACION.get("SQLALCHEMY_DATABASE_URI")[8:] + "?sslmode=require"  # type: ignore[index]
        )
        CONFIGURACION["SQLALCHEMY_DATABASE_URI"] = DBURI

    # La mayor parte de servicios en linea ofrecen una cadena de conexión a Postgres que comienza con "postgres"
    # cadena de conexión va a fallar con SQLAlchemy:
    # - https://docs.sqlalchemy.org/en/20/core/engines.html#postgresql
    # Se utiliza por defecto el driver pg8000 que no requere compilarse y es mas amigable  en entornos de contenedores
    # donde es mas complejo compilar psycopg2.
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


def log_messages(_app: "Flask"):
    """Emite mensages de log luego de haber cargado la configuración."""

    if "postgres" in _app.config.get("SQLALCHEMY_DATABASE_URI"):  # type: ignore[operator]
        DBType = "PostgreSQL"  # pragma: no cover
    if "mysql" in _app.config.get("SQLALCHEMY_DATABASE_URI"):  # type: ignore[operator]
        DBType = "MySQL"  # pragma: no cover
    if "mariadb" in _app.config.get("SQLALCHEMY_DATABASE_URI"):  # type: ignore[operator]
        DBType = "MariaDB"  # pragma: no cover
    if "sqlite" in _app.config.get("SQLALCHEMY_DATABASE_URI"):  # type: ignore[operator]
        DBType = "SQLite"  # pragma: no cover

    log.info("Utilizando el motor de base de datos {type}.", type=DBType)

    log.trace("Directorio base de la aplicación es {dir}", dir=DIRECTORIO_APP)
    log.trace("Directorio para cargas de archivos: {dir}", dir=DIRECTORIO_BASE_UPLOADS)
    log.trace("Directorio de archivos publicos es {directorio}", directorio=DIRECTORIO_ARCHIVOS_PUBLICOS)
    log.trace("Directorio de archivos privados es {directorio}", directorio=DIRECTORIO_ARCHIVOS_PRIVADOS)
    log.trace("Directorio de imagenes es {directorio}", directorio=DIRECTORIO_UPLOAD_IMAGENES)
    log.trace("Directorio de archivos es {directorio}", directorio=DIRECTORIO_UPLOAD_ARCHIVOS)
    log.trace("Directorio de audios es {directorio}", directorio=DIRECTORIO_UPLOAD_AUDIO)


# Configuración de Directorio de carga de archivos.
images = UploadSet("images", IMAGES)
files = UploadSet("files", DOCUMENTS)
audio = UploadSet("audio", AUDIO)
