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

# Python 3.7+ - Postponed evaluation of annotations
from __future__ import annotations

# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------
import os
import sys
from os import R_OK, W_OK, access, environ, makedirs, name, path
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

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


# ---------------------------------------------------------------------------------------
# Configuration file loading functionality
# ---------------------------------------------------------------------------------------
def load_config_from_file() -> dict:
    """
    Busca y carga configuración desde archivo con ConfigObj.

    Busca en las siguientes ubicaciones en orden:
    1. Ruta especificada por NOW_LMS_CONFIG
    2. /etc/now-lms/now-lms.conf
    3. /etc/now-lms.conf
    4. ~/.config/now-lms/now-lms.conf
    5. ./now-lms.conf

    Returns:
        dict: Diccionario de configuración, vacío si no se encuentra archivo
    """
    try:
        from configobj import ConfigObj
    except ImportError:
        log.debug("ConfigObj not available, skipping file-based configuration.")
        return {}

    search_paths = [
        environ.get("NOW_LMS_CONFIG"),
        "/etc/now-lms/now-lms.conf",
        "/etc/now-lms.conf",
        path.expanduser("~/.config/now-lms/now-lms.conf"),
        path.join(os.getcwd(), "now-lms.conf"),
    ]

    for config_path in search_paths:
        if config_path and path.isfile(config_path):
            try:
                log.info(f"Loading configuration from file: {config_path}")
                config_obj = ConfigObj(config_path, encoding="utf-8")

                # Convert ConfigObj to regular dict and handle aliases
                config_dict = dict(config_obj)

                # Handle aliases as specified in the requirements
                if "DATABASE_URL" in config_dict:
                    config_dict["SQLALCHEMY_DATABASE_URI"] = config_dict["DATABASE_URL"]
                    # Keep the alias for backward compatibility

                if "REDIS_URL" in config_dict:
                    config_dict["CACHE_REDIS_URL"] = config_dict["REDIS_URL"]
                    # Keep the alias for backward compatibility

                return config_dict

            except Exception as e:
                log.warning(f"Error loading configuration from {config_path}: {e}")
                continue

    log.trace("No configuration file found in search paths.")
    return {}


# < --------------------------------------------------------------------------------------------- >
# Configuración central de la aplicación.
VALORES_TRUE = {*["1", "true", "yes", "on"], *["development", "dev"]}
DEBUG_VARS = ["DEBUG", "CI", "DEV", "DEVELOPMENT"]
FRAMEWORK_VARS = ["FLASK_ENV", "DJANGO_DEBUG", "NODE_ENV"]
GENERIC_VARS = ["ENV", "APP_ENV"]

# < --------------------------------------------------------------------------------------------- >
# Gestión de variables de entorno.
DESARROLLO = any(
    str(environ.get(var, "")).strip().lower() in VALORES_TRUE for var in [*DEBUG_VARS, *FRAMEWORK_VARS, *GENERIC_VARS]
)
FORCE_HTTPS = environ.get("NOW_LMS_FORCE_HTTPS", "0").strip().lower() in VALORES_TRUE
AUTO_MIGRATE = environ.get("NOW_LMS_AUTO_MIGRATE", "0").strip().lower() in VALORES_TRUE
DEMO_MODE = environ.get("NOW_LMS_DEMO_MODE", "0").strip().lower() in VALORES_TRUE

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
custom_data_dir = environ.get("NOW_LMS_DATA_DIR")
if custom_data_dir:
    log.trace("Data directory configuration found in environment variables.")
    DIRECTORIO_ARCHIVOS = custom_data_dir
else:
    DIRECTORIO_ARCHIVOS = DIRECTORIO_ARCHIVOS_BASE

custom_themes_dir = environ.get("NOW_LMS_THEMES_DIR")
if custom_themes_dir:
    log.trace("Themes directory configuration found in environment variables.")
    DIRECTORIO_PLANTILLAS = custom_themes_dir
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

# Crea los directorios si no existen.
if not path.isdir(DIRECTORIO_BASE_ARCHIVOS_USUARIO):
    try:
        makedirs(DIRECTORIO_BASE_ARCHIVOS_USUARIO)
        makedirs(DIRECTORIO_ARCHIVOS_PRIVADOS)
        makedirs(DIRECTORIO_ARCHIVOS_PUBLICOS)
        makedirs(DIRECTORIO_UPLOAD_ARCHIVOS)
        makedirs(DIRECTORIO_UPLOAD_IMAGENES)
        makedirs(DIRECTORIO_UPLOAD_AUDIO)
    except OSError:
        log.warning(f"Cannot create directory for file uploads: {DIRECTORIO_BASE_ARCHIVOS_USUARIO}")
if access(DIRECTORIO_BASE_ARCHIVOS_USUARIO, R_OK) and access(DIRECTORIO_BASE_ARCHIVOS_USUARIO, W_OK):
    log.trace(f"Access verified to: {DIRECTORIO_BASE_ARCHIVOS_USUARIO}")
else:
    log.warning(f"No access to upload files to directory: {DIRECTORIO_BASE_ARCHIVOS_USUARIO}")

# < --------------------------------------------------------------------------------------------- >
# Directorio base temas.
DIRECTORIO_BASE_UPLOADS = Path(str(path.join(str(DIRECTORIO_ARCHIVOS), "files")))

# < --------------------------------------------------------------------------------------------- >
# Ubicación predeterminada de base de datos SQLITE
if TESTING := (
    "PYTEST_CURRENT_TEST" in environ
    or "PYTEST_VERSION" in environ
    or hasattr(sys, "_called_from_test")
    or environ.get("CI")
    or "pytest" in sys.modules
    or path.basename(sys.argv[0]) in ["pytest", "py.test"]
):
    SQLITE: str = "sqlite://"
else:
    if name == "nt":
        SQLITE = "sqlite:///" + str(DIRECTORIO_PRINCICIPAL) + "\\now_lms.db"
    else:
        SQLITE = "sqlite:///" + str(DIRECTORIO_PRINCICIPAL) + "/now_lms.db"

# < --------------------------------------------------------------------------------------------- >
# Configuración de la aplicación:
# Se siguen las recomendaciones de "Twelve Factors App" y las opciones se leen del entorno.
CONFIGURACION: dict[str, str | bool | Path] = {}
CONFIGURACION["SECRET_KEY"] = environ.get("SECRET_KEY") or "dev"  # nosec

# Warn if using default SECRET_KEY in production
if not DESARROLLO and CONFIGURACION["SECRET_KEY"] == "dev":
    log.warning(
        "Using default SECRET_KEY in production! This will cause session issues "
        "with Gunicorn multi-worker setup. Set SECRET_KEY environment variable."
    )

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

# < --------------------------------------------------------------------------------------------- >
# Corrige la URI de conexión a la base de datos si el usuario omite el driver apropiado.

if DATABASE_URL_BASE := CONFIGURACION.get("SQLALCHEMY_DATABASE_URI"):

    DATABASE_URL_CORREGIDA = DATABASE_URL_BASE

    prefix = DATABASE_URL_BASE.split(":", 1)[0]  # Extraer prefijo: "postgres", "mysql", etc.

    # Caso especial: Heroku + PostgreSQL
    if environ.get("DYNO") and prefix in ("postgres", "postgresql"):  # type: ignore[operator]
        parsed = urlparse(DATABASE_URL_BASE)  # type: ignore[arg-type]
        query = parse_qs(parsed.query)
        query["sslmode"] = ["require"]
        DATABASE_URL_CORREGIDA = urlunparse(parsed._replace(scheme="postgresql", query=urlencode(query, doseq=True)))

    else:
        # Corrige el esquema según el prefijo detectado
        match prefix:
            case "postgresql":
                DATABASE_URL_CORREGIDA = "postgresql+pg8000" + DATABASE_URL_BASE[10:]  # type: ignore[index]
            case "postgres":
                DATABASE_URL_CORREGIDA = "postgresql+pg8000" + DATABASE_URL_BASE[8:]  # type: ignore[index]
            case "mysql":
                DATABASE_URL_CORREGIDA = "mysql+pymysql" + DATABASE_URL_BASE[5:]  # type: ignore[index]
            case "mariadb":  # Not tested, but should work.
                DATABASE_URL_CORREGIDA = "mariadb+mariadbconnector" + DATABASE_URL_BASE[7:]  # type: ignore[index]
            case _:
                pass  # Prefijo desconocido o ya corregido

    # Actualizar configuración si hubo cambio
    if DATABASE_URL_BASE != DATABASE_URL_CORREGIDA:
        log.info(f"Database URI corrected: {DATABASE_URL_BASE} → {DATABASE_URL_CORREGIDA}")
        CONFIGURACION["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL_CORREGIDA

# < --------------------------------------------------------------------------------------------- >
# Configuración de Directorio de carga de archivos.
images = UploadSet("images", IMAGES)
files = UploadSet("files", DOCUMENTS)
audio = UploadSet("audio", AUDIO)


# < --------------------------------------------------------------------------------------------- >
# Información del sistema en que se ejecuta la aplicación.
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
