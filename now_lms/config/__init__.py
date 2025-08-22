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

"""Application configuration."""
# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------
import sys
from os import R_OK, W_OK, access, environ, makedirs, name, path
from pathlib import Path
from typing import TYPE_CHECKING, Dict

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------
from appdirs import AppDirs
from flask_uploads import AUDIO, DOCUMENTS, IMAGES, UploadSet

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms.logs import log

if TYPE_CHECKING:
    from flask import Flask

# < --------------------------------------------------------------------------------------------- >
# Configuración central de la aplicación.
VALORES_TRUE = {"1", "true", "yes", "on", "development", "dev"}

DESARROLLO = any(
    str(environ.get(var, "")).strip().lower() in VALORES_TRUE
    for var in [
        "DEBUG",  # Variable común para activar modo debug
        "CI",  # Continuous Integration flag (como GitHub Actions, Travis, etc.)
        "DEV",  # General "development" flag
        "DEVELOPMENT",  # Más explícita, común en Docker y algunas plantillas
        "FLASK_ENV",  # 'development' en Flask
        "DJANGO_DEBUG",  # Común en proyectos Django
        "NODE_ENV",  # A veces usada también fuera de Node.js
        "ENV",  # Genérica: 'development' vs 'production'
        "APP_ENV",  # Usada en entornos cloud
    ]
)


# < --------------------------------------------------------------------------------------------- >
# Directorios base de la aplicacion
DIRECTORIO_ACTUAL: Path = Path(path.abspath(path.dirname(__file__)))
DIRECTORIO_APP: Path = DIRECTORIO_ACTUAL.parent.absolute()
DIRECTORIO_PLANTILLAS_BASE: str = path.join(DIRECTORIO_APP, "templates")
DIRECTORIO_ARCHIVOS_BASE: str = path.join(DIRECTORIO_APP, "static")
DIRECTORIO_BASE_APP: AppDirs = AppDirs("NOW-LMS", "BMO Soluciones")
DIRECTORIO_PRINCICIPAL: Path = Path(DIRECTORIO_APP).parent.absolute()


# < --------------------------------------------------------------------------------------------- >
# Directorios personalizados para la aplicación.
if environ.get("CUSTOM_DATA_DIR"):
    log.trace("Data directory configuration found in environment variables.")
    DIRECTORIO_ARCHIVOS = environ.get("CUSTOM_DATA_DIR")
else:
    DIRECTORIO_ARCHIVOS = DIRECTORIO_ARCHIVOS_BASE

if environ.get("CUSTOM_THEMES_DIR"):
    log.trace("Themes directory configuration found in environment variables.")
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
        log.warning(f"Cannot create directory for file uploads: {DIRECTORIO_BASE_ARCHIVOS_USUARIO}")
if access(DIRECTORIO_BASE_ARCHIVOS_USUARIO, R_OK) and access(DIRECTORIO_BASE_ARCHIVOS_USUARIO, W_OK):  # pragma: no cover
    log.trace(f"Access verified to: {DIRECTORIO_BASE_ARCHIVOS_USUARIO}")
else:
    log.warning(f"No access to upload files to directory: {DIRECTORIO_BASE_ARCHIVOS_USUARIO}")

# < --------------------------------------------------------------------------------------------- >
# Directorio base temas.
DIRECTORIO_BASE_UPLOADS = Path(str(path.join(str(DIRECTORIO_ARCHIVOS), "files")))

# < --------------------------------------------------------------------------------------------- >
# Ubicación predeterminada de base de datos SQLITE
if (
    "PYTEST_CURRENT_TEST" in environ
    or "PYTEST_VERSION" in environ
    or hasattr(sys, "_called_from_test")
    or environ.get("CI")
    or "pytest" in sys.modules
    or path.basename(sys.argv[0]) in ["pytest", "py.test"]
):
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
CONFIGURACION["SQLALCHEMY_DATABASE_URI"] = environ.get("DATABASE_URL") or SQLITE  # nosec
# Opciones comunes de configuración.
CONFIGURACION["PRESERVE_CONTEXT_ON_EXCEPTION"] = False
# Carga de Archivos: https://flask-reuploaded.readthedocs.io/en/latest/configuration/
CONFIGURACION["UPLOADS_AUTOSERVE"] = True
CONFIGURACION["UPLOADED_FILES_DEST"] = DIRECTORIO_UPLOAD_ARCHIVOS
CONFIGURACION["UPLOADED_IMAGES_DEST"] = DIRECTORIO_UPLOAD_IMAGENES
CONFIGURACION["UPLOADED_AUDIO_DEST"] = DIRECTORIO_UPLOAD_AUDIO

if DESARROLLO:
    log.warning("Using default configuration.")
    log.info("Default configuration is not recommended for use in production environments.")
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
        DBURI = "mysql+mysqlconnector" + CONFIGURACION.get("SQLALCHEMY_DATABASE_URI")[5:]  # type: ignore[index]
        CONFIGURACION["SQLALCHEMY_DATABASE_URI"] = DBURI

    elif "mariadb:" in CONFIGURACION.get("SQLALCHEMY_DATABASE_URI"):  # type: ignore[operator]
        DBURI = "mariadb+mariadbconnector" + CONFIGURACION.get("SQLALCHEMY_DATABASE_URI")[7:]  # type: ignore[index]
        CONFIGURACION["SQLALCHEMY_DATABASE_URI"] = DBURI


# Configuración de Directorio de carga de archivos.
images = UploadSet("images", IMAGES)
files = UploadSet("files", DOCUMENTS)
audio = UploadSet("audio", AUDIO)


def is_running_in_container() -> bool:
    """Detecta si se está ejecutando en un contenedor como Docker."""
    # Revisión común en Docker/Linux
    try:
        with open("/proc/1/cgroup", "rt", encoding="utf-8") as f:
            content = f.read()
            return "docker" in content or "kubepods" in content
    except FileNotFoundError:
        return False


def log_system_info():
    """Emit información útil del entorno del sistema."""
    import os
    import platform
    import socket

    log.info("=== System Information ===")

    os_name = platform.system()
    os_version = platform.version()
    os_release = platform.release()
    architecture = platform.machine()
    python_version = platform.python_version()
    hostname = socket.gethostname()
    container = is_running_in_container()
    cpu_count = os.cpu_count()

    log.info(f"Operating system: {os_name} {os_release} (version: {os_version})")
    log.info(f"Architecture: {architecture}")
    log.info(f"Python version: {python_version}")
    log.info(f"Hostname: {hostname}")
    log.info(f"Number of CPUs: {cpu_count}")
    log.info(f"In container?: {'Yes' if container else 'No'}")

    # Detalles adicionales como trace
    log.trace(f"Execution path: {sys.executable}")
    log.trace(f"Process arguments: {sys.argv}")


def log_messages(_app: "Flask"):
    """Emit mensajes de log útiles para debugging luego de haber cargado la configuración."""
    import logging

    db_uri = _app.config.get("SQLALCHEMY_DATABASE_URI", "").lower()
    db_type = "Desconocido"

    if "postgres" in db_uri:
        db_type = "PostgreSQL"
    elif "mysql" in db_uri:
        db_type = "MySQL"
    elif "mariadb" in db_uri:
        db_type = "MariaDB"
    elif "sqlite" in db_uri:
        db_type = "SQLite"

    log.info(f"Database engine detected: {db_type}")

    # Log detallado de configuraciones clave
    configuraciones_interes = [
        "DEBUG",
        "ENV",
        "TESTING",
        "MAX_CONTENT_LENGTH",
        "SERVER_NAME",
        "PREFERRED_URL_SCHEME",
    ]
    for clave in configuraciones_interes:
        valor = _app.config.get(clave, "No definido")
        log.trace(f"Configuration '{clave}': {valor}")

    # Logueo de directorios relevantes
    log.trace(f"Application base directory: {DIRECTORIO_APP}")
    log.trace(f"File uploads directory: {DIRECTORIO_BASE_UPLOADS}")
    log.trace(f"Public files directory: {DIRECTORIO_ARCHIVOS_PUBLICOS}")
    log.trace(f"Private files directory: {DIRECTORIO_ARCHIVOS_PRIVADOS}")
    log.trace(f"Images directory: {DIRECTORIO_UPLOAD_IMAGENES}")
    log.trace(f"Files directory: {DIRECTORIO_UPLOAD_ARCHIVOS}")
    log.trace(f"Audio directory: {DIRECTORIO_UPLOAD_AUDIO}")

    # Rutas registradas en la aplicación (útil para depuración de endpoints)
    for rule in _app.url_map.iter_rules():
        log.trace(f"Registered route: {rule.rule} -> {rule.endpoint} ({', '.join(rule.methods)})")  # type: ignore[arg-type]

    # Extensiones activas (si aplica)
    for ext_nombre, ext_instancia in _app.extensions.items():
        log.trace(f"Loaded extension: {ext_nombre} -> {type(ext_instancia)}")

    if log.getEffectiveLevel() < logging.INFO:
        log_system_info()
