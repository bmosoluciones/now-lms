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

Gestión de certificados.
"""

# ---------------------------------------------------------------------------------------
# Libreria estandar
# ---------------------------------------------------------------------------------------


# ---------------------------------------------------------------------------------------
# Librerias de terceros
# ---------------------------------------------------------------------------------------
from flask import Blueprint, flash, redirect, render_template, request
from flask_login import login_required
from sqlalchemy.exc import OperationalError

# ---------------------------------------------------------------------------------------
# Recursos locales
# ---------------------------------------------------------------------------------------
from now_lms.auth import perfil_requerido
from now_lms.config import DIRECTORIO_PLANTILLAS
from now_lms.db import MAXIMO_RESULTADOS_EN_CONSULTA_PAGINADA, Etiqueta, database
from now_lms.db.tools import cursos_por_etiqueta
from now_lms.forms import EtiquetaForm

# ---------------------------------------------------------------------------------------
# Administración de Etiquetas.
# ---------------------------------------------------------------------------------------

web_error = Blueprint("error", __name__, template_folder=DIRECTORIO_PLANTILLAS)


@web_error.route("/http/error/<code>")
def error_page(code):
    """HTTP error code pages."""

    url = "error_pages/" + code + ".html"

    return render_template(url)
