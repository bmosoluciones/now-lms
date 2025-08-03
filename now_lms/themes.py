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


"""Herramientas para interacturar con temas."""

# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------
from os import path
from pathlib import Path
from types import SimpleNamespace

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------
from flask import get_template_attribute as get_macro

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms.config import DIRECTORIO_PLANTILLAS
from now_lms.db.tools import get_current_theme

# < --------------------------------------------------------------------------------------------- >
THEMES_DIRECTORY = "themes/"
DIRECTORIO_TEMAS = str(Path(path.join(str(DIRECTORIO_PLANTILLAS), THEMES_DIRECTORY)))


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

    HOME = Path(path.join(get_theme_path(), "overrides", "home.j2"))

    if HOME.exists():
        return THEMES_DIRECTORY + str(THEME) + "/overrides/home.j2"
    else:
        return "inicio/home.html"


def get_course_list_template() -> str:
    """Devuelve la ruta del template de la lista de cursos."""
    THEME = get_current_theme()

    COURSE_LIST = Path(path.join(get_theme_path(), "overrides", "course_list.j2"))

    if COURSE_LIST.exists():
        return THEMES_DIRECTORY + str(THEME) + "/overrides/course_list.j2"
    else:
        return "inicio/cursos.html"


def get_program_list_template() -> str:
    """Devuelve la ruta del template de la lista de programas."""
    THEME = get_current_theme()

    PROGRAM_LIST = Path(path.join(get_theme_path(), "overrides", "program_list.j2"))

    if PROGRAM_LIST.exists():
        return THEMES_DIRECTORY + str(THEME) + "/overrides/program_list.j2"
    else:
        return "inicio/programas.html"


def get_course_view_template() -> str:
    """Devuelve la ruta del template de vista de curso."""
    THEME = get_current_theme()

    COURSE_VIEW = Path(path.join(get_theme_path(), "overrides", "course_view.j2"))

    if COURSE_VIEW.exists():
        return THEMES_DIRECTORY + str(THEME) + "/overrides/course_view.j2"
    else:
        return "learning/curso/curso.html"


def get_program_view_template() -> str:
    """Devuelve la ruta del template de vista de programa."""
    THEME = get_current_theme()

    PROGRAM_VIEW = Path(path.join(get_theme_path(), "overrides", "program_view.j2"))

    if PROGRAM_VIEW.exists():
        return THEMES_DIRECTORY + str(THEME) + "/overrides/program_view.j2"
    else:
        return "learning/programa.html"


def current_theme():
    """Carga las variables de los temas en el contexto de la aplicacion."""

    theme = get_current_theme
    dir_ = THEMES_DIRECTORY
    return SimpleNamespace(
        headertags=get_macro(dir_ + theme() + "/header.j2", "headertags"),
        jslibs=get_macro(dir_ + theme() + "/js.j2", "jslibs"),
        local_style=get_macro(dir_ + theme() + "/local_style.j2", "local_style"),
        navbar=get_macro(dir_ + theme() + "/navbar.j2", "navbar"),
        notify=get_macro(dir_ + theme() + "/notify.j2", "notify"),
        rendizar_paginacion=get_macro(dir_ + theme() + "/pagination.j2", "paginate"),
    )


def list_themes():
    """Devuelve una lista de los temas disponibles."""

    from os import listdir
    from os.path import join

    THEMES_PATH = join(str(DIRECTORIO_PLANTILLAS), "themes")
    TEMPLATE_LIST = []
    for template in listdir(THEMES_PATH):
        TEMPLATE_LIST.append(template)
    TEMPLATE_LIST.sort()
    return TEMPLATE_LIST
