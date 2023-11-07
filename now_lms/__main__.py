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

"""
Modulo para ejecutar NOW LMS.

"""
# ---------------------------------------------------------------------------------------
# Libreria estandar
# ---------------------------------------------------------------------------------------


# ---------------------------------------------------------------------------------------
# Librerias de terceros
# ---------------------------------------------------------------------------------------


# ---------------------------------------------------------------------------------------
# Recursos locales
# ---------------------------------------------------------------------------------------
from now_lms import serve, init_app
from now_lms.config import DESARROLLO
from now_lms.logs import log


if __name__ == "__main__":
    log.info("Iniciando NOW Learning Management System.")
    if DESARROLLO:
        log.trace("Ejecutando NOW-LMS con opciones de desarrollo.")
        init_app(with_examples=True)
    else:
        log.trace("Iniciando NOW-MLS como modulo importable.")
        init_app(with_examples=False)
    serve()
