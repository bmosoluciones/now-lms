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
from dataclasses import dataclass
from os import environ
from typing import TYPE_CHECKING

# ---------------------------------------------------------------------------------------
# Librerias de terceros
# ---------------------------------------------------------------------------------------


# ---------------------------------------------------------------------------------------
# Recursos locales
# ---------------------------------------------------------------------------------------
from now_lms.db import MailConfig, database
from now_lms.logs import log


if TYPE_CHECKING:
    from flask import Flask


@dataclass
class MailConfigFromEnv:
    MAIL_SERVER = environ.get("MAIL_SERVER")
    MAIL_PORT = environ.get("MAIL_PORT")
    MAIL_USE_TLS = environ.get("MAIL_USE_TLS")
    MAIL_USE_SSL = environ.get("MAIL_USE_SSL")
    MAIL_USERNAME = environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = environ.get("MAIL_DEFAULT_SENDER")
    # Must be a integer
    if MAIL_PORT:
        MAIL_PORT = int(MAIL_PORT)
    # Must be a boolean
    if MAIL_USE_SSL == "False" or MAIL_USE_SSL == "false" or MAIL_USE_SSL == "FALSE":
        MAIL_USE_SSL = False
    elif MAIL_USE_SSL == "True" or MAIL_USE_SSL == "true" or MAIL_USE_SSL == "TRUE":
        MAIL_USE_SSL = True
    # Must be a boolean
    if MAIL_USE_TLS == "False" or MAIL_USE_TLS == "false" or MAIL_USE_TLS == "FALSE":
        MAIL_USE_TLS = False
    elif MAIL_USE_TLS == "True" or MAIL_USE_TLS == "true" or MAIL_USE_TLS == "TRUE":
        MAIL_USE_TLS = True


def load_email_setup(flask_app: "Flask"):
    """Inicia la configuración de correo electronico."""

    log.trace("Iniciando configuración correo electronico.")
    with flask_app.app_context():
        mail_config = database.session.execute(database.select(MailConfig)).first()[0]
        mail_config_from_env = MailConfigFromEnv()

        if mail_config.email:
            flask_app.config["MAIL_SERVER"] = mail_config_from_env.MAIL_SERVER or mail_config.MAIL_SERVER
            flask_app.config["MAIL_PORT"] = mail_config_from_env.MAIL_PORT or mail_config.MAIL_PORT
            flask_app.config["MAIL_USE_TLS"] = mail_config_from_env.MAIL_USE_TLS or mail_config.MAIL_USE_TLS
            flask_app.config["MAIL_USE_SSL"] = mail_config_from_env.MAIL_USE_SSL or mail_config.MAIL_USE_SSL
            flask_app.config["MAIL_USERNAME"] = mail_config_from_env.MAIL_USERNAME or mail_config.MAIL_USERNAME
            flask_app.config["MAIL_PASSWORD"] = mail_config_from_env.MAIL_PASSWORD or mail_config.MAIL_PASSWORD
            flask_app.config["MAIL_DEFAULT_SENDER"] = (
                mail_config_from_env.MAIL_DEFAULT_SENDER or mail_config.MAIL_DEFAULT_SENDER
            )
