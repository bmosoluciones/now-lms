# Copyright 2022 - 2023 BMO Soluciones, S.A.
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

# Libreria standar:


# Librerias de terceros:


# Recursos locales:

# pylint: disable=R0401


def proteger_passwd(clave):
    """Devuelve una contraseña salteada con bcrytp."""
    from bcrypt import hashpw, gensalt

    return hashpw(clave.encode(), gensalt())


def validar_acceso(usuario_id, acceso):
    """Verifica el inicio de sesión del usuario."""
    from bcrypt import checkpw
    from now_lms.db import Usuario, database
    from datetime import datetime

    registro = Usuario.query.filter_by(usuario=usuario_id).first()
    if registro is not None:
        clave_validada = checkpw(acceso.encode(), registro.acceso)
    else:  # pragma: no cover
        clave_validada = False

    if clave_validada:
        registro.ultimo_acceso = datetime.now()
        database.session.commit()

    return clave_validada
