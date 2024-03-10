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
from os import environ, path
from pathlib import Path

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
from now_lms.config import DIRECTORIO_ARCHIVOS_PRIVADOS
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


def obtener_clave_de_cifrado():
    """
    Retorna una clave en bytes para utilizarla para proteger información sencible.

    Los usuario de NOW_LMS pueden almacenar información sencible como contraseñas y claves
    de acceso a otros servicios en sus perfiles, para proteger la privacidad del usuario
    estos valores no se almacen como texto plano en la base de datos si no que se almacen como
    hashes.

    La implementación actual esta inspirada por la forma en que Apache Airflow almacena los datos
    accesos que sus usuarios guardan.

    El sistema utiliza una llave segura para cifrar y desifrar estos valores, de esta forma un tercero
    requerira tanto acceso a la base de datos como a la clave de cifrado para acceder a la información
    cifrada.

    Se recomienda utilizar una clave de cifrado guardada como clave de entorno, en caso de proveerse una
    el sistema generara una clave aleatoria y la almacenara en la carpeta de archivos privados de su
    implementación.

    Referencias:
     - https://airflow.apache.org/docs/apache-airflow/stable/security/secrets/fernet.html
     - https://cryptography.io/en/latest/fernet/
    """

    if environ.get("LMS_FERNET_KEY"):
        return environ.get("LMS_FERNET_KEY").encode()
    else:
        SECURE_KEY_FILE: Path = Path(path.join(DIRECTORIO_ARCHIVOS_PRIVADOS, "secret.key"))
        if Path.exists(SECURE_KEY_FILE):
            with open(SECURE_KEY_FILE) as f:
                return f.readline().encode()
        else:
            SECURE_KEY = Fernet.generate_key()
            with open(SECURE_KEY_FILE, "x") as f:
                f.write(SECURE_KEY.decode())
            return SECURE_KEY


def proteger_secreto(password):
    """
    Devuelve el hash de un valor sencible a almancenar en la base de datos.

    Si la variable de entorno "LMS_FERNET_KEY" esta definida se utiliza este valor por defecto, en
    caso contrario se utilizara una clave generada aleatoriamente que sera almacenada en el directorio
    de archivos privados de su implementación.
    """

    f = Fernet(obtener_clave_de_cifrado())

    if isinstance(password, bytes):

        return f.encrypt(password)

    else:

        return f.encrypt(password.encode())


def descifrar_secreto(hash):
    """
    Devuelve el valor de una contraseña protegida.

    Si la variable de entorno "LMS_FERNET_KEY" esta definida se utiliza este valor por defecto, en
    caso contrario se utilizara una clave generada aleatoriamente que sera almacenada en el directorio
    de archivos privados de su implementación.
    """

    f = Fernet(obtener_clave_de_cifrado())
    return f.decrypt(hash)
