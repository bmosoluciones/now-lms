# Copyright 2022 -2023 BMO Soluciones, S.A.
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

# ---------------------------------------------------------------------------------------
# Librerias de terceros
# ---------------------------------------------------------------------------------------
from flask import current_app

# ---------------------------------------------------------------------------------------
# Recursos locales
# ---------------------------------------------------------------------------------------
from now_lms.auth import descifrar_secreto
from now_lms.db import database, Configuracion
from now_lms.logs import log

from flask import Flask
from flask_mailing import Mail, Message

mail = Mail()


def create_app():
    app = Flask(__name__)

    app.config["MAIL_USERNAME"] = "williamjmorenor@gmail.com"
    app.config["MAIL_PASSWORD"] = "bqmzfnnltdedbjbv"
    app.config["MAIL_PORT"] = 465
    app.config["MAIL_SERVER"] = "smtp.gmail.com"
    app.config["MAIL_USE_TLS"] = False
    app.config["MAIL_USE_SSL"] = True
    mail.init_app(app)

    return app


app = create_app()


@app.route("/email")
async def enviar():
    with app.app_context():

        message = Message(
            subject="Flask-Mailing module",
            recipients=["wmoreno@montelimar.com.ni"],
            body="This is the basic email body",
        )

        await mail.send_message(message)
        return "ok"


def cargar_configuracion_correo_desde_db():
    """Carga la configuración de correo electronico desde la base de datos a la configuración de la aplicacion."""

    log.trace("Verificando configuración de correo electronico.")
    from flask_mailing import Mail

    mail: Mail = Mail()
    with current_app.app_context():
        CONFIG = database.session.execute(database.select(Configuracion)).first()[0]

        if (
            CONFIG.email
            and CONFIG.MAIL_HOST is not None
            and CONFIG.MAIL_PORT is not None
            and CONFIG.MAIL_USERNAME is not None
            and CONFIG.MAIL_PASSWORD is not None
        ):
            log.trace("Cargando configuración de correo electronico.")

            current_app.config.update(
                {
                    "MAIL_SERVER": CONFIG.MAIL_SERVER,
                    "MAIL_PORT": CONFIG.MAIL_PORT,
                    "MAIL_USERNAME": CONFIG.MAIL_USERNAME,
                    "MAIL_PASSWORD": descifrar_secreto(CONFIG.MAIL_PASSWORD),
                    "MAIL_USE_TLS": CONFIG.MAIL_USE_TLS,
                    "MAIL_USE_SSL": CONFIG.MAIL_USE_SSL,
                    "MAIL_BACKEND": "smtp",
                }
            )
            mail.init_app(current_app)

        else:
            log.trace("No se encontraron opciones de correo electronico.")

        return mail
