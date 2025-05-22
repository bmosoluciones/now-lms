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
# Contributors:
# - William José Moreno Reyes


"""Herramientas para interacturar con temas."""

# ---------------------------------------------------------------------------------------
# Libreria estandar
# ---------------------------------------------------------------------------------------
from os import path
from pathlib import Path

# ---------------------------------------------------------------------------------------
# Librerias de terceros
# ---------------------------------------------------------------------------------------
from flask import get_template_attribute

# ---------------------------------------------------------------------------------------
# Recursos locales
# ---------------------------------------------------------------------------------------
from now_lms.config import DIRECTORIO_PLANTILLAS
from now_lms.db.tools import get_current_theme

# < --------------------------------------------------------------------------------------------- >
DIRECTORIO_TEMAS = Path(path.join(DIRECTORIO_PLANTILLAS, "themes"))


def get_theme_path() -> str:
    """Devuelve la ruta del directorio de temas."""
    THEME = get_current_theme()
    if THEME:
        # Obtenemos la ruta del tema actual
        THEME_PATH = Path(path.join(DIRECTORIO_TEMAS, THEME))
    else:
        THEME_PATH = Path(path.join(DIRECTORIO_TEMAS, "now_lms"))

    return str(THEME_PATH)


def get_home_template() -> str:
    """Devuelve la ruta del template de la pagina de inicio."""
    THEME = get_current_theme()

    HOME = Path(path.join(get_theme_path(), "home.j2"))

    if HOME.exists():
        return "themes/" + str(THEME) + "/home.j2"
    else:
        return "inicio/home.html"


def load_theme_variables(app):
    """Carga las variables de los temas en el contexto de la aplicacion."""
    with app.app_context():
        app.jinja_env.globals["headertags"] = get_template_attribute(
            "themes/" + get_current_theme() + "/header_tags.j2", "headertags"
        )
        app.jinja_env.globals["local_style"] = get_template_attribute(
            "themes/" + get_current_theme() + "/local_style.j2", "local_style"
        )
        app.jinja_env.globals["navbar"] = get_template_attribute("themes/" + get_current_theme() + "/navbar.j2", "navbar")
        app.jinja_env.globals["notify"] = get_template_attribute("themes/" + get_current_theme() + "/notify.j2", "notify")
        app.jinja_env.globals["rendizar_paginacion"] = get_template_attribute(
            "themes/" + get_current_theme() + "/pagination.j2", "rendizar_paginacion"
        )
