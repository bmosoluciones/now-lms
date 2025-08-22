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


"""Access control for the application."""

# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------
import base64
from datetime import datetime, timedelta, timezone
from functools import wraps

# ---------------------------------------------------------------------------------------
# Third-party libraries
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
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms.db import MailConfig, Usuario, database
from now_lms.logs import log

ph = PasswordHasher()


# ---------------------------------------------------------------------------------------
# Proteger contraseñas de usuarios.
# ---------------------------------------------------------------------------------------
def proteger_passwd(clave, /):
    """Devuelve una contraseña salteada con argon2."""
    _hash = ph.hash(clave.encode()).encode("utf-8")

    return _hash


def validar_acceso(usuario_id, acceso, /):
    """Verifica el inicio de sesión del usuario."""
    log.trace(f"Verifying access for {usuario_id}")
    registro = database.session.execute(database.select(Usuario).filter_by(usuario=usuario_id)).scalar_one_or_none()

    if not registro:
        registro = database.session.execute(
            database.select(Usuario).filter_by(correo_electronico=usuario_id)
        ).scalar_one_or_none()

    if registro is not None:
        try:
            ph.verify(registro.acceso, acceso.encode())
            clave_validada = True
        except VerifyMismatchError:
            clave_validada = False
    else:
        log.trace(f"User record not found for {usuario_id}")
        clave_validada = False

    log.trace(f"Access validation result is {clave_validada}")
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
            if not current_user.is_authenticated:
                flash("Favor iniciar sesión.", "warning")
                return redirect(url_for("user.login"))

            log.trace(f"Verifying access for user {current_user.usuario} with profile {perfil_id}")
            # Always allow admin access
            if current_user.tipo == "admin":
                return func(*args, **kwargs)

            # Handle tuple format for multiple allowed profiles
            if isinstance(perfil_id, tuple):
                if current_user.tipo in perfil_id:
                    return func(*args, **kwargs)
            # Handle string format for single profile
            elif isinstance(perfil_id, str) and current_user.tipo == perfil_id:
                return func(*args, **kwargs)

            log.warning(f"Access denied for user {current_user.usuario} with profile {current_user.tipo}")
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
        from now_lms.db import Configuracion

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


def descifrar_secreto(hash_value):
    """Devuelve el valor de una contraseña protegida."""
    with current_app.app_context():
        from now_lms.db import Configuracion

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
            s = f.decrypt(hash_value)
            return s.decode()
        except Exception:  # Catch decryption errors
            return None


# ---------------------------------------------------------------------------------------
# Validación de tokens de confirmación de correo electrónico.
# ---------------------------------------------------------------------------------------
def generate_confirmation_token(mail):
    """Generate a confirmation token for email verification."""
    expiration_time = datetime.now(timezone.utc) + timedelta(seconds=36000)
    data = {"exp": expiration_time, "confirm_id": mail}
    token = jwt.encode(data, current_app.secret_key, algorithm="HS512")
    return token


def validate_confirmation_token(token):
    """Validate a confirmation token and return the result."""
    try:
        data = jwt.decode(token, current_app.secret_key, algorithms=["HS512"])
        log.trace(f"Confirmation token decoded: {data}")
    except jwt.ExpiredSignatureError:
        log.warning("Verification attempt expired.")
        return False
    except jwt.InvalidSignatureError:
        log.warning("Invalid verification attempt.")
        return False
    except jwt.DecodeError:
        log.warning("Confirmation token has invalid format.")
        return False
    except Exception as e:
        log.warning(f"Error validating confirmation token: {e}")
        return False

    if data.get("confirm_id", None):
        log.trace(f"Validating confirmation token for {data.get('confirm_id', None)}")
        user_result = database.session.execute(
            database.select(Usuario).filter_by(correo_electronico=data.get("confirm_id", None))
        ).first()
        if user_result:
            user = user_result[0]
            log.info(f"User {user.usuario} has been verified, the account is now active.")
            user.correo_electronico_verificado = True
            user.activo = True
            database.session.commit()
            return True
        log.warning(f"User with email {data.get('confirm_id', None)} not found.")
        return False
    return False


def send_confirmation_email(user):
    """Send confirmation email to user."""
    from flask_mail import Message

    from now_lms.mail import send_mail

    config = database.session.execute(database.select(MailConfig)).first()[0]

    msg = Message(
        subject="Email verification",
        recipients=[user.correo_electronico],
        sender=((config.MAIL_DEFAULT_SENDER_NAME or "NOW LMS"), config.MAIL_DEFAULT_SENDER),
    )
    token = generate_confirmation_token(user.correo_electronico)
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
        send_mail(
            msg,
            background=False,
            no_config=True,
            _log="Correo de confirmación enviado",
            _flush="Correo de confirmación enviado.",
        )
        log.info(f"Confirmation email sent to user {user.usuario}")
    except Exception as e:  # noqa: E722
        log.warning(f"Error sending confirmation email to user {user.usuario}: {e}")


# ---------------------------------------------------------------------------------------
# Password reset functionality
# ---------------------------------------------------------------------------------------
def generate_password_reset_token(email):
    """Generate a password reset token."""
    expiration_time = datetime.now(timezone.utc) + timedelta(seconds=3600)  # 1 hour expiration
    data = {"exp": expiration_time, "reset_email": email, "action": "password_reset"}
    token = jwt.encode(data, current_app.secret_key, algorithm="HS512")
    return token


def validate_password_reset_token(token):
    """Validate a password reset token and return the email if valid."""
    try:
        data = jwt.decode(token, current_app.secret_key, algorithms=["HS512"])
        log.trace(f"Password reset token decoded: {data}")
    except jwt.ExpiredSignatureError:
        log.warning("Password reset token expired.")
        return None
    except jwt.InvalidSignatureError:
        log.warning("Invalid password reset token.")
        return None
    except jwt.DecodeError:
        log.warning("Password reset token has invalid format.")
        return None
    except Exception as e:
        log.warning(f"Error validating password reset token: {e}")
        return None

    if data.get("reset_email", None) and data.get("action") == "password_reset":
        return data.get("reset_email")
    return None


def send_password_reset_email(user):
    """Send password reset email to user."""
    from flask_mail import Message

    from now_lms.mail import send_mail

    config = database.session.execute(database.select(MailConfig)).first()[0]

    msg = Message(
        subject="Recuperación de Contraseña - NOW LMS",
        recipients=[user.correo_electronico],
        sender=((config.MAIL_DEFAULT_SENDER_NAME or "NOW LMS"), config.MAIL_DEFAULT_SENDER),
    )
    token = generate_password_reset_token(user.correo_electronico)
    url = url_for("user.reset_password", token=token, _external=True)
    msg.html = f"""
    <div class="container">
        <div class="header">
          <h1>Recuperación de Contraseña</h1>
        </div>
        <div class="content">
          <p>Hola {user.nombre},</p>
          <p>Has solicitado recuperar tu contraseña. Haz clic en el siguiente enlace para establecer una nueva contraseña:</p>
          <p>
              <a href="{url}" style="background-color: #007bff; color: white; padding: 10px 15px; text-decoration: none; border-radius: 5px;">Restablecer Contraseña</a>
          </p>
          <p>Si no puedes hacer clic en el botón, copia y pega la siguiente URL en tu navegador:</p>
          <p>{url}</p>
          <p>Este enlace expirará en 1 hora por seguridad.</p>
          <p>Si no solicitaste este cambio, puedes ignorar este correo.</p>
        </div>
        <div class="footer">
          <p>Este es un mensaje automático. Por favor no respondas a este correo.</p>
        </div>
      </div>
    """
    try:
        send_mail(
            msg,
            background=False,
            no_config=True,
            _log="Correo de recuperación de contraseña enviado",
            _flush="Correo de recuperación de contraseña enviado.",
        )
        log.info(f"Recovery email sent to user {user.usuario}")
        return True
    except Exception as e:  # noqa: E722
        log.warning(f"Error sending recovery email to user {user.usuario}: {e}")
        return False
