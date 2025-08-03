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


# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------
import threading
from os import environ
from types import SimpleNamespace
from typing import Mapping, Union

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------
from flask import Flask, current_app, flash
from flask_mail import Mail, Message

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms.auth import descifrar_secreto
from now_lms.config import DESARROLLO
from now_lms.db import MailConfig, database
from now_lms.logs import LOG_LEVEL
from now_lms.logs import log as logger

# ---------------------------------------------------------------------------------------
# Configuración de tipos.
# ---------------------------------------------------------------------------------------
MAIL_SERVER: Union[str, bool, Mapping, None] = None
MAIL_PORT: Union[str, bool, Mapping, None] = None
MAIL_USERNAME: Union[str, bool, Mapping, None] = None
MAIL_PASSWORD: Union[str, bool, Mapping, None] = None
MAIL_USE_TLS: Union[str, bool, Mapping, None] = None
MAIL_USE_SSL: Union[str, bool, Mapping, None] = None
MAIL_DEFAULT_SENDER: Union[str, bool, Mapping, None] = None
mail_configured: bool = False


# ---------------------------------------------------------------------------------------
# Load setting from environment variables
# ---------------------------------------------------------------------------------------
def _load_mail_config_from_env() -> SimpleNamespace:
    """Carga la configuración de correo electrónico desde las variables de entorno."""

    logger.trace("Obteniendo configuración de correo electronico desde variables de entorno.")
    # Server name and user credentials
    MAIL_SERVER = environ.get("MAIL_SERVER", None)
    MAIL_PORT = environ.get("MAIL_PORT", None)
    MAIL_USERNAME = environ.get("MAIL_USERNAME", None)
    MAIL_PASSWORD = environ.get("MAIL_PASSWORD", None)
    if MAIL_SERVER and MAIL_PORT and MAIL_USERNAME and MAIL_PASSWORD:
        logger.debug("Configuración de correo electrónico cargada desde variables de entorno.")
        mail_configured = True
    else:
        logger.trace("No se encontró configuración de correo electrónico en variables de entorno.")
        mail_configured = False
    # TLS/SSL settings
    MAIL_USE_TLS = environ.get("MAIL_USE_TLS", "False").capitalize()
    MAIL_USE_SSL = environ.get("MAIL_USE_SSL", "False").capitalize()
    # Default sender
    MAIL_DEFAULT_SENDER = environ.get("MAIL_DEFAULT_SENDER")

    # Strin to boolean
    if MAIL_USE_SSL == "FALSE":
        MAIL_USE_SSL = False  # type: ignore[assignment]
    elif MAIL_USE_SSL == "TRUE":
        MAIL_USE_SSL = True  # type: ignore[assignment]
    if MAIL_USE_TLS == "FALSE":
        MAIL_USE_TLS = False  # type: ignore[assignment]
    elif MAIL_USE_TLS == "TRUE":
        MAIL_USE_TLS = True  # type: ignore[assignment]

    return SimpleNamespace(
        mail_configured=mail_configured,
        MAIL_SERVER=MAIL_SERVER,
        MAIL_PORT=MAIL_PORT,
        MAIL_USERNAME=MAIL_USERNAME,
        MAIL_PASSWORD=MAIL_PASSWORD,
        MAIL_USE_TLS=MAIL_USE_TLS,
        MAIL_USE_SSL=MAIL_USE_SSL,
        MAIL_DEFAULT_SENDER=MAIL_DEFAULT_SENDER,
    )


def _load_mail_config_from_db() -> SimpleNamespace:
    """Carga la configuración de correo electrónico desde la base de datos."""
    logger.trace("Obteniendo configuración de correo electronico desde base de datos.")
    with current_app.app_context():
        mail_config = database.session.execute(database.select(MailConfig)).first()[0]

        # If available, use the configuration from the database
        MAIL_SERVER = mail_config.MAIL_SERVER
        MAIL_PORT = mail_config.MAIL_PORT
        MAIL_USE_TLS = mail_config.MAIL_USE_TLS
        MAIL_USE_SSL = mail_config.MAIL_USE_SSL
        MAIL_USERNAME = mail_config.MAIL_USERNAME
        MAIL_PASSWORD = descifrar_secreto(mail_config.MAIL_PASSWORD)
        MAIL_DEFAULT_SENDER = mail_config.MAIL_DEFAULT_SENDER
        mail_configured = mail_config.email_verificado

        return SimpleNamespace(
            mail_configured=mail_configured,
            MAIL_SERVER=MAIL_SERVER,
            MAIL_PORT=MAIL_PORT,
            MAIL_USERNAME=MAIL_USERNAME,
            MAIL_PASSWORD=MAIL_PASSWORD,
            MAIL_USE_TLS=MAIL_USE_TLS,
            MAIL_USE_SSL=MAIL_USE_SSL,
            MAIL_DEFAULT_SENDER=MAIL_DEFAULT_SENDER,
        )


def _config() -> SimpleNamespace:

    config_from_env = _load_mail_config_from_env()

    if config_from_env.mail_configured:
        return config_from_env
    else:
        return _load_mail_config_from_db()


def send_threaded_email(app: Flask, mail: Mail, msg: Message, _log: str = "", _flush: str = ""):
    """
    Función interna que se ejecuta en un hilo para enviar el email.

    :param app: Instancia de Flask.
    :param mail: Instancia de Flask-Mail.
    :param msg: Instancia de flask_mail.Message.
    """

    logger.trace(f"Enviando correo a {msg.recipients} en segundo plano.")
    try:
        with app.app_context():
            logger.trace("Intentando enviar correo electrónico en segundo plano.")
            mail.send(msg)
            logger.trace(f"Correo enviado a {msg.recipients}.")
            if _log != "":
                logger.info(_log)
            if _flush != "":
                flash(_flush)
    except Exception as e:
        logger.error(f"Error al enviar correo a {msg.recipients}: {e}")


def send_mail(msg: Message, background: bool = True, no_config: bool = False, _log: str = "", _flush: str = ""):
    """
    Envía un mensaje de correo electrónico de forma asincrónica usando hilos.

    :param mail: Instancia de Flask.
    :param msg: Instancia de flask_mail.Message.
    :param background: Si es True, envía el correo en segundo plano.
    """

    _app = current_app
    config = _config()

    for key, value in vars(config).items():
        if key.startswith("MAIL_"):
            _app.config[key] = value

    if LOG_LEVEL < 20:
        _app.config["MAIL_DEBUG"] = True

    if DESARROLLO:
        _app.config["MAIL_SUPPRESS_SEND"] = True

    logger.trace("Configuración de correo electrónico cargada en la aplicación Flask.")

    logger.trace("Creando instancia de Flask-Mail.")
    _mail = Mail(_app)

    if config.mail_configured or no_config:
        logger.trace("Configuración de correo electrónico verificada.")
        if background:
            logger.trace("Enviando correo en segundo plano.")
            try:
                hilo = threading.Thread(target=send_threaded_email, args=(_app, _mail, msg, _log, _flush))
                hilo.start()
                logger.trace(f"Hilo iniciado para enviar email a: {msg.recipients}")
            except Exception as e:
                logger.error(f"No se pudo iniciar el hilo de envío de correo: {e}")
        else:
            logger.trace("Enviando correo de forma síncrona.")
            with _app.app_context():
                _mail.send(msg)
                logger.trace(f"Correo enviado a {msg.recipients}.")
