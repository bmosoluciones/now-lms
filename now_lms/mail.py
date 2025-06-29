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
from os import environ
from typing import TYPE_CHECKING

# ---------------------------------------------------------------------------------------
# Recursos locales
# ---------------------------------------------------------------------------------------
from now_lms.auth import descifrar_secreto
from now_lms.config import DESARROLLO
from now_lms.db import MailConfig, database
from now_lms.logs import log as logger

# ---------------------------------------------------------------------------------------
# Librerias de terceros
# ---------------------------------------------------------------------------------------


if TYPE_CHECKING:
    from flask import Flask


# ---------------------------------------------------------------------------------------
# Load setting from environment variables
# ---------------------------------------------------------------------------------------
MAIL_SERVER = environ.get("MAIL_SERVER")
MAIL_PORT = environ.get("MAIL_PORT")
MAIL_USE_TLS = environ.get("MAIL_USE_TLS")
MAIL_USE_SSL = environ.get("MAIL_USE_SSL")
MAIL_USERNAME = environ.get("MAIL_USERNAME")
MAIL_PASSWORD = environ.get("MAIL_PASSWORD")
MAIL_DEFAULT_SENDER = environ.get("MAIL_DEFAULT_SENDER")

# ---------------------------------------------------------------------------------------
# Convert string values to boolean
# ---------------------------------------------------------------------------------------
if MAIL_USE_SSL == "False" or MAIL_USE_SSL == "false" or MAIL_USE_SSL == "FALSE":
    MAIL_USE_SSL = False  # type: ignore[assignment]
elif MAIL_USE_SSL == "True" or MAIL_USE_SSL == "true" or MAIL_USE_SSL == "TRUE":
    MAIL_USE_SSL = True  # type: ignore[assignment]
if MAIL_USE_TLS == "False" or MAIL_USE_TLS == "false" or MAIL_USE_TLS == "FALSE":
    MAIL_USE_TLS = False  # type: ignore[assignment]
elif MAIL_USE_TLS == "True" or MAIL_USE_TLS == "true" or MAIL_USE_TLS == "TRUE":
    MAIL_USE_TLS = True  # type: ignore[assignment]


def load_email_setup(flask_app: "Flask"):
    """Inicia la configuración de correo electronico."""

    logger.trace("Iniciando configuración correo electronico.")
    with flask_app.app_context():
        mail_config = database.session.execute(database.select(MailConfig)).first()[0]

        # If available, use the configuration from the database
        flask_app.config["MAIL_SERVER"] = MAIL_SERVER or mail_config.MAIL_SERVER
        flask_app.config["MAIL_PORT"] = MAIL_PORT or mail_config.MAIL_PORT
        flask_app.config["MAIL_USE_TLS"] = MAIL_USE_TLS or mail_config.MAIL_USE_TLS
        flask_app.config["MAIL_USE_SSL"] = MAIL_USE_SSL or mail_config.MAIL_USE_SSL
        flask_app.config["MAIL_USERNAME"] = MAIL_USERNAME or mail_config.MAIL_USERNAME
        flask_app.config["MAIL_PASSWORD"] = MAIL_PASSWORD or descifrar_secreto(mail_config.MAIL_PASSWORD)
        flask_app.config["MAIL_DEFAULT_SENDER"] = MAIL_DEFAULT_SENDER or mail_config.MAIL_DEFAULT_SENDER

        if DESARROLLO:
            logger.warning("Opciones de Desarollo activas. Correo electronico deshabilitado.")
            flask_app.config["MAIL_SUPPRESS_SEND"] = True
            from now_lms.logs import log

            for key, value in flask_app.config.items():
                if key.startswith("MAIL_"):
                    log.debug(f"{key} = {value}")

        return flask_app
