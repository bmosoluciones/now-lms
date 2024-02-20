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
NOW Learning Management System.

Gestión de eventos en una sesión
"""

# ---------------------------------------------------------------------------------------
# Libreria estandar
# ---------------------------------------------------------------------------------------


# ---------------------------------------------------------------------------------------
# Librerias de terceros
# ---------------------------------------------------------------------------------------
from flask import Blueprint
from flask_login import login_required

# ---------------------------------------------------------------------------------------
# Recursos locales
# ---------------------------------------------------------------------------------------
from now_lms.auth import perfil_requerido
from now_lms.config import DIRECTORIO_PLANTILLAS

# ---------------------------------------------------------------------------------------
# Interfaz de calendario.
# ---------------------------------------------------------------------------------------

calendar = Blueprint("calendar", __name__, template_folder=DIRECTORIO_PLANTILLAS)


@calendar.route("/calendar/<course_ulid>")
@login_required
@perfil_requerido("user")
def calendario(course_ulid: str):
    """Genera un calendario ical a partir de los eventos de un curso."""


@calendar.route("/calendar/<course_ulid>/export")
@login_required
@perfil_requerido("user")
def calendario_export(course_ulid: str):
    """Exporta un calendario ical a partir de los eventos de un curso."""


@calendar.route("/calendar/<course_ulid>/event/<resource_id>")
@login_required
@perfil_requerido("user")
def calendario_evento(course_ulid: str, resource_id: str):
    """Genera un evento a partir de un recurso del calendario."""


@calendar.route("/calendar/<course_ulid>/event/<resource_id>/export")
@login_required
@perfil_requerido("user")
def calendario_evento_export(course_ulid: str, resource_id: str):
    """Exporta un evento a ical."""
