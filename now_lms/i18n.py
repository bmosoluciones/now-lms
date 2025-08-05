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


"""Internationalization utilities."""

# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------
from flask import current_app, request
from flask_babel import gettext as _

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms.logs import log


def _get_locales():
    """Get the list of available locales."""
    with current_app.app_context():
        from now_lms.db import Configuracion, database

        config = database.session.query(Configuracion).first()
        if config:
            log.trace(_("Configuración consultada correctamente desde la base de datos."))
            log.trace(f"Configuración de idioma: {config.lang}")
            return config.lang
        else:
            return request.accept_languages.best_match(["es", "en"])


def _get_timezone():
    """Get the list of available locales."""
    with current_app.app_context():
        from now_lms.db import Configuracion, database

        config = database.session.query(Configuracion).first()
        if config:
            log.trace(f"Configuración de zona horaria: {config.time_zone}")
            return config.time_zone
        else:
            return request.accept_languages.best_match(["es", "en"])


"""Guia de uso:
# Extraer textos a traducir
pybabel extract -F babel.cfg -o now_lms/translations/messages.pot .

# Crear archivo de traducción para español (si no existe)
pybabel init -i now_lms/translations/messages.pot -d now_lms/translations -l en

# Compilar traducciones
pybabel compile -d now_lms/translations

# Actualizar archivo de traducción
# Extraer nuevos textos
pybabel extract -F babel.cfg -o now_lms/translations/messages.pot .

# Actualizar archivos de idioma
pybabel update -i now_lms/translations/messages.pot -d now_lms/translations

# Luego edita los .po y recompila
pybabel compile -d now_lms/translations
"""
