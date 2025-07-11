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


"""Control de acceso a la aplicacion."""

# ---------------------------------------------------------------------------------------
# Libreria estandar
# ---------------------------------------------------------------------------------------
import base64
from datetime import datetime, timedelta
from functools import wraps

# ---------------------------------------------------------------------------------------
# Librerias de terceros
# ---------------------------------------------------------------------------------------
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from flask import abort, current_app, flash, redirect, url_for
from flask_login import current_user

# ---------------------------------------------------------------------------------------
# Recursos locales
# ---------------------------------------------------------------------------------------
from now_lms.db import Configuracion, Usuario, database
from now_lms.logs import log

ph = PasswordHasher()


# ---------------------------------------------------------------------------------------
# Proteger contraseñas de usuarios.
# ---------------------------------------------------------------------------------------
def proteger_passwd(clave):
    """Devuelve una contraseña salteada con argon2."""

    _hash = ph.hash(clave.encode()).encode("utf-8")

    return _hash


def validar_acceso(usuario_id, acceso):
    """Verifica el inicio de sesión del usuario."""

    log.trace(f"Verificando acceso de {usuario_id}")
    registro = Usuario.query.filter_by(usuario=usuario_id).first()

    if not registro:
        registro = Usuario.query.filter_by(correo_electronico=usuario_id).first()

    if registro is not None:
        try:
            ph.verify(registro.acceso, acceso.encode())
            clave_validada = True
        except VerifyMismatchError:
            clave_validada = False
    else:
        log.trace(f"No se encontro registro de usuario {usuario_id}")
        clave_validada = False

    log.trace(f"Resultado de validación de acceso es {clave_validada}")
    if clave_validada:
        registro.ultimo_acceso = datetime.now()
        database.session.commit()

    return clave_validada


# ---------------------------------------------------------------------------------------
# Comprobar el acceso a un perfil de acuerdo con el perfil del usuario.
# ---------------------------------------------------------------------------------------
def perfil_requerido(perfil_id):
    """Comprueba si un usuario tiene acceso a un recurso determinado en base a su tipo."""

    def decorator_verifica_acceso(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if (current_user.is_authenticated and current_user.tipo == perfil_id) or current_user.tipo == "admin":
                return func(*args, **kwargs)

            else:
                flash("No se encuentra autorizado a acceder al recurso solicitado.", "error")
                return abort(403)

        return wrapper

    return decorator_verifica_acceso


# ---------------------------------------------------------------------------------------
# Evita registrar información sensible en la base de datos en texto plano.
# ---------------------------------------------------------------------------------------
def proteger_secreto(password):
    """Devuelve el hash de una contraseña."""

    with current_app.app_context():
        from now_lms.db import Configuracion, database

        config = database.session.execute(database.select(Configuracion)).first()[0]

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=config.r,
            iterations=480000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(current_app.config.get("SECRET_KEY").encode()))
        f = Fernet(key)
        return f.encrypt(password.encode())


def descifrar_secreto(hash):
    """Devuelve el valor de una contraseña protegida."""

    with current_app.app_context():
        from now_lms.db import Configuracion, database

        config = database.session.execute(database.select(Configuracion)).first()[0]

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=config.r,
            iterations=480000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(current_app.config.get("SECRET_KEY").encode()))
        f = Fernet(key)
        try:
            s = f.decrypt(hash)
            return s.decode()
        except:  # noqa: E722
            return None


# ---------------------------------------------------------------------------------------
# Validación de tokens de confirmación de correo electrónico.
# ---------------------------------------------------------------------------------------
def generate_confirmation_token():
    expiration_time = datetime.utcnow() + timedelta(seconds=36000)
    data = {"exp": expiration_time, "confirm_id": current_user.id}
    token = jwt.encode(data, current_app.secret_key, algorithm="HS512")
    return token


def validate_confirmation_token(token):
    try:
        data = jwt.decode(token, current_app.secret_key, algorithms=["HS512"])
    except jwt.ExpiredSignatureError:
        return False
    except jwt.InvalidSignatureError:
        return False

    if data.get("confirm_id") != current_user.id:
        return False
    else:
        consulta = database.session.execute(database.select(Configuracion)).first()[0]
        consulta.email_verificado = True
        database.session.commit()
        return True


def send_confirmation_email(user):
    from flask_mail import Mail, Message

    from now_lms.mail import load_email_setup, enviar_correo_asincrono

    app_ = load_email_setup(current_app)
    mail = Mail()
    mail.init_app(app_)
    msg = Message(
        subject="Email verification",
        recipients=[user.correo_electronico],
    )
    token = generate_confirmation_token()
    url = url_for("user.check_mail", token=token, _external=True)
    msg.html = f"""
    <div class="container">
        <div class="header">
          <h1>Email verification</h1>
        </div>
        <div class="content">
          <p>Please confirm your email:</p>
          <p>
              <a href="{url}">{url}</a>
          </p>
        </div>
        <div class="footer">
          <p>This is an automated message. Please do not reply to this email.</p>
        </div>
      </div>
    """
    try:
        enviar_correo_asincrono(mail, msg)
        log.info(f"Correo de confirmación enviado al usuario {user.usuario}")
        flash("Correo de confirmación enviado exitosamente.", "success")
        return redirect(url_for("home.pagina_de_inicio"))
    except Exception as e:  # noqa: E722
        log.warning(f"Error al enviar un correo de confirmació el usuario {user.usuario}: {e}")
