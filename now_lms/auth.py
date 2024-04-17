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
from datetime import datetime
from functools import wraps

# ---------------------------------------------------------------------------------------
# Librerias de terceros
# ---------------------------------------------------------------------------------------
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from flask import abort, flash, current_app
from flask_login import current_user

# ---------------------------------------------------------------------------------------
# Recursos locales
# ---------------------------------------------------------------------------------------
from now_lms.db import Usuario, database
from now_lms.logs import log


ph = PasswordHasher()


def proteger_passwd(clave):
    """Devuelve una contraseña salteada con argon2."""

    _hash = ph.hash(clave.encode()).encode("utf-8")

    return _hash


def validar_acceso(usuario_id, acceso):
    """Verifica el inicio de sesión del usuario."""

    log.trace("Verificando acceso de {usuario}", usuario=usuario_id)
    registro = Usuario.query.filter_by(usuario=usuario_id).first()
    if registro is not None:
        try:
            clave_validada = ph.verify(registro.acceso, acceso.encode())
        except VerifyMismatchError:
            clave_validada = False
    else:  # pragma: no cover
        log.trace("No se encontro registro de usuario {usuario}", usuario=usuario_id)
        clave_validada = False

    log.trace("Resultado de validación de acceso es {resultado}", resultado=clave_validada)
    if clave_validada:
        registro.ultimo_acceso = datetime.now()
        database.session.commit()

    return clave_validada


def perfil_requerido(perfil_id):
    """Comprueba si un usuario tiene acceso a un recurso determinado en base a su tipo."""

    def decorator_verifica_acceso(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if (current_user.is_authenticated and current_user.tipo == perfil_id) or current_user.tipo == "admin":
                return func(*args, **kwargs)

            else:  # pragma: no cover
                flash("No se encuentra autorizado a acceder al recurso solicitado.", "error")
                return abort(403)

        return wrapper

    return decorator_verifica_acceso


def proteger_secreto(password):
    """
    Devuelve el hash de una contraseña.

    Se requiere que el parametro "SECRET_KEY" este establecido en la configuración de la aplicacion,
    si cambia el valor de este parametro debera actualizar la configuración ya se utiliza el mismo
    parametro para obtener la contraseña original.
    """

    with current_app.app_context():
        from now_lms.db import database, Configuracion

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
    """
    Devuelve el valor de una contraseña protegida.

    Se utiliza el valor del parametro "SECRET_KEY" de la configuración de la aplicación para decodificar
    la contraseña original, si el parametro "SECRET_KEY" cambia en la configuración no se posible desifrar
    la contraseña original, debera generar una nueva.
    """

    with current_app.app_context():
        from now_lms.db import database, Configuracion

        config = database.session.execute(database.select(Configuracion)).first()[0]

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=config.r,
            iterations=480000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(current_app.config.get("SECRET_KEY").encode()))
        f = Fernet(key)
        return f.decrypt(hash)
