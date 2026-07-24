# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.

"""Email functionality for NOW LMS."""

from __future__ import annotations

# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------
import threading
from os import environ
from types import SimpleNamespace

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
MAIL_SERVER: str | bool | dict | None = None
MAIL_PORT: str | bool | dict | None = None
MAIL_USERNAME: str | bool | dict | None = None
MAIL_PASSWORD: str | bool | dict | None = None
MAIL_USE_TLS: str | bool | dict | None = None
MAIL_USE_SSL: str | bool | dict | None = None
MAIL_DEFAULT_SENDER: str | bool | dict | None = None
mail_configured: bool = False


# ---------------------------------------------------------------------------------------
# Load setting from environment variables
# ---------------------------------------------------------------------------------------
def _load_mail_config_from_env() -> SimpleNamespace:
    """Carga la configuración de correo electrónico desde las variables de entorno."""
    logger.trace("Loading email configuration from environment variables.")
    # Server name and user credentials
    mail_server = environ.get("MAIL_SERVER", None)
    mail_port = environ.get("MAIL_PORT", None)
    mail_username = environ.get("MAIL_USERNAME", None)
    mail_password = environ.get("MAIL_PASSWORD", None)
    if mail_server and mail_port and mail_username and mail_password:
        logger.debug("Email configuration loaded from environment variables.")
        is_mail_configured = True
    else:
        logger.trace("No email configuration found in environment variables.")
        is_mail_configured = False
    # TLS/SSL settings
    mail_use_tls = environ.get("MAIL_USE_TLS", "False").capitalize()
    mail_use_ssl = environ.get("MAIL_USE_SSL", "False").capitalize()
    # Default sender
    mail_default_sender = environ.get("MAIL_DEFAULT_SENDER")

    # String to boolean conversion using pattern matching
    match mail_use_ssl:
        case "FALSE":
            mail_use_ssl = False  # type: ignore[assignment]
        case "TRUE":
            mail_use_ssl = True  # type: ignore[assignment]

    match mail_use_tls:
        case "FALSE":
            mail_use_tls = False  # type: ignore[assignment]
        case "TRUE":
            mail_use_tls = True  # type: ignore[assignment]

    return SimpleNamespace(
        mail_configured=is_mail_configured,
        MAIL_SERVER=mail_server,
        MAIL_PORT=mail_port,
        MAIL_USERNAME=mail_username,
        MAIL_PASSWORD=mail_password,
        MAIL_USE_TLS=mail_use_tls,
        MAIL_USE_SSL=mail_use_ssl,
        MAIL_DEFAULT_SENDER=mail_default_sender,
    )


def _load_mail_config_from_db() -> SimpleNamespace:
    """Carga la configuración de correo electrónico desde la base de datos."""
    logger.trace("Loading email configuration from database.")
    with current_app.app_context():
        row = database.session.execute(database.select(MailConfig)).first()
        if row is None:
            raise ValueError("No mail configuration found in database")
        mail_config = row[0]

        # If available, use the configuration from the database
        mail_server = mail_config.MAIL_SERVER
        mail_port = mail_config.MAIL_PORT
        mail_use_tls = mail_config.MAIL_USE_TLS
        mail_use_ssl = mail_config.MAIL_USE_SSL
        mail_username = mail_config.MAIL_USERNAME
        mail_password = descifrar_secreto(mail_config.MAIL_PASSWORD)
        mail_default_sender = mail_config.MAIL_DEFAULT_SENDER
        is_mail_configured = mail_config.email_verificado

        return SimpleNamespace(
            mail_configured=is_mail_configured,
            MAIL_SERVER=mail_server,
            MAIL_PORT=mail_port,
            MAIL_USERNAME=mail_username,
            MAIL_PASSWORD=mail_password,
            MAIL_USE_TLS=mail_use_tls,
            MAIL_USE_SSL=mail_use_ssl,
            MAIL_DEFAULT_SENDER=mail_default_sender,
        )


def _config() -> SimpleNamespace:

    config_from_env = _load_mail_config_from_env()

    if config_from_env.mail_configured:
        return config_from_env
    return _load_mail_config_from_db()


def send_threaded_email(app: Flask, mail: Mail, msg: Message, _log: str = "", _flush: str = ""):
    """
    Función interna que se ejecuta en un hilo para enviar el email.

    :param app: Instancia de Flask.
    :param mail: Instancia de Flask-Mail.
    :param msg: Instancia de flask_mail.Message.
    """
    logger.trace(f"Sending email to {msg.recipients} in background.")
    try:
        with app.app_context():
            logger.trace("Sending email in background.")
            mail.send(msg)
            logger.trace("Email sent to %s.", msg.recipients)
            if _log != "":
                logger.info(_log)
            if _flush != "":
                flash(_flush)
    except Exception as e:
        logger.error("Failed to send email to %s: %s", msg.recipients, e)


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

    logger.trace("Email configuration loaded into Flask application.")

    logger.trace("Creating Flask-Mail instance.")
    _mail = Mail(_app)

    if config.mail_configured or no_config:
        logger.trace("Email configuration verified.")
        if background:
            logger.trace("Sending email in background.")
            try:
                hilo = threading.Thread(target=send_threaded_email, args=(_app, _mail, msg, _log, _flush))
                hilo.start()
                logger.trace("Thread started to send email to: %s", msg.recipients)
            except Exception as e:
                logger.error("Could not start email sending thread: %s", e)
        else:
            logger.trace("Sending email synchronously.")
            with _app.app_context():
                _mail.send(msg)
                logger.trace("Email sent to %s.", msg.recipients)
