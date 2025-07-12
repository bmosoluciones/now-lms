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
# Contributors:
# - William José Moreno Reyes


# ---------------------------------------------------------------------------------------
# Libreria estandar
# ---------------------------------------------------------------------------------------
import threading
from os import environ
from types import SimpleNamespace
from typing import Union, Mapping

# ---------------------------------------------------------------------------------------
# Librerias de terceros
# ---------------------------------------------------------------------------------------
from flask import current_app
from flask_mail import Mail, Message

# ---------------------------------------------------------------------------------------
# Recursos locales
# ---------------------------------------------------------------------------------------
from now_lms.auth import descifrar_secreto
from now_lms.db import MailConfig, database
from now_lms.config import DESARROLLO
from now_lms.logs import log as logger, LOG_LEVEL


mail = Mail()

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
mail_enabled: bool = False


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
        mail_enabled = True
    else:
        logger.trace("No se encontró configuración de correo electrónico en variables de entorno.")
        mail_configured = False
        mail_enabled = False
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
        mail_enabled=mail_enabled,
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
        mail_enabled = mail_config.email_habilitado

        return SimpleNamespace(
            mail_configured=mail_configured,
            mail_enabled=mail_enabled,
            MAIL_SERVER=MAIL_SERVER,
            MAIL_PORT=MAIL_PORT,
            MAIL_USERNAME=MAIL_USERNAME,
            MAIL_PASSWORD=MAIL_PASSWORD,
            MAIL_USE_TLS=MAIL_USE_TLS,
            MAIL_USE_SSL=MAIL_USE_SSL,
            MAIL_DEFAULT_SENDER=MAIL_DEFAULT_SENDER,
        )


def send_threaded_email(mail: Mail, msg: Message):
    """Función interna que se ejecuta en un hilo para enviar el email."""
    logger.trace(f"Enviando correo a {msg.recipients} en segundo plano.")
    try:
        mail.send(msg)
        logger.trace(f"Correo enviado a {msg.recipients}.")
    except Exception as e:
        logger.error(f"Error al enviar correo a {msg.recipients}: {e}")


def _config() -> SimpleNamespace:

    config_from_env = _load_mail_config_from_env()

    if config_from_env.mail_configured:
        return config_from_env
    else:
        return _load_mail_config_from_db()


def _mail(config: SimpleNamespace):
    """Configura y devuelve una instancia de Flask-Mail."""

    app = current_app

    for key, value in vars(config).items():
        if key.startswith("MAIL_"):
            app.config[key] = value

    if LOG_LEVEL < 20:
        app.config["MAIL_DEBUG"] = True

    if DESARROLLO:
        app.config["MAIL_SUPPRESS_SEND"] = True

    return mail.init_app(app)


def send_mail(msg: Message, background: bool = True):
    """
    Envía un mensaje de correo electrónico de forma asincrónica usando hilos.

    :param mail: Instancia de Flask.
    :param msg: Instancia de flask_mail.Message.
    :param background: Si es True, envía el correo en segundo plano.
    """

    config = _config()
    mail = _mail(config)

    if config.mail_configured and config.mail_enabled:
        if background:
            try:
                hilo = threading.Thread(target=send_threaded_email, args=(mail, msg))
                hilo.start()
                logger.trace(f"Hilo iniciado para enviar email a: {msg.recipients}")
            except Exception as e:
                logger.error(f"No se pudo iniciar el hilo de envío de correo: {e}")
        else:
            mail.send(msg)
            logger.trace(f"Correo enviado a {msg.recipients}.")
    else:
        logger.warning("No se ha configurado el correo electrónico.")
