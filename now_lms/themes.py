# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""Herramientas para interacturar con temas."""

from __future__ import annotations

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

# ---------------------------------------------------------------------------------------
# Theme configuration constants
# ---------------------------------------------------------------------------------------
THEMES_DIRECTORY: str = "themes/"
DIRECTORIO_TEMAS: str = str(Path(path.join(str(DIRECTORIO_PLANTILLAS), THEMES_DIRECTORY)))

# ---------------------------------------------------------------------------------------
# Theme path utilities
# ---------------------------------------------------------------------------------------


def get_theme_path() -> str:
    """Devuelve la ruta del directorio de temas."""
    if THEME := get_current_theme():
        # Build path to current active theme
        return str(Path(path.join(DIRECTORIO_TEMAS, THEME)))

    # Fall back to default theme if none set
    return str(Path(path.join(DIRECTORIO_TEMAS, "now_lms")))


# ---------------------------------------------------------------------------------------
# Template override utilities
# ---------------------------------------------------------------------------------------


def get_home_template() -> str:
    """Devuelve la ruta del template de la pagina de inicio."""
    THEME = get_current_theme()

    # Check if theme has custom home template
    HOME = Path(path.join(get_theme_path(), "overrides", "home.j2"))

    if HOME.exists():
        # Use theme-specific home template
        return THEMES_DIRECTORY + str(THEME) + "/overrides/home.j2"
    # Fall back to default home template
    return "inicio/home.html"


def get_course_list_template() -> str:
    """Devuelve la ruta del template de la lista de cursos."""
    THEME = get_current_theme()

    # Check if theme has custom course list template
    COURSE_LIST = Path(path.join(get_theme_path(), "overrides", "course_list.j2"))

    if COURSE_LIST.exists():
        # Use theme-specific course list template
        return THEMES_DIRECTORY + str(THEME) + "/overrides/course_list.j2"
    # Fall back to default course list template
    return "inicio/cursos.html"


def get_program_list_template() -> str:
    """Devuelve la ruta del template de la lista de programas."""
    THEME = get_current_theme()

    PROGRAM_LIST = Path(path.join(get_theme_path(), "overrides", "program_list.j2"))

    if PROGRAM_LIST.exists():
        # Use theme-specific program list template
        return THEMES_DIRECTORY + str(THEME) + "/overrides/program_list.j2"
    # Fall back to default program list template
    return "inicio/programas.html"


def get_course_view_template() -> str:
    """Devuelve la ruta del template de vista de curso."""
    THEME = get_current_theme()

    # Check if theme has custom course view template
    COURSE_VIEW = Path(path.join(get_theme_path(), "overrides", "course_view.j2"))

    if COURSE_VIEW.exists():
        # Use theme-specific course view template
        return THEMES_DIRECTORY + str(THEME) + "/overrides/course_view.j2"
    # Fall back to default course view template
    return "learning/curso/curso.html"


def get_program_view_template() -> str:
    """Devuelve la ruta del template de vista de programa."""
    THEME = get_current_theme()

    # Check if theme has custom program view template
    PROGRAM_VIEW = Path(path.join(get_theme_path(), "overrides", "program_view.j2"))

    if PROGRAM_VIEW.exists():
        # Use theme-specific program view template
        return THEMES_DIRECTORY + str(THEME) + "/overrides/program_view.j2"
    # Fall back to default program view template
    return "learning/programa.html"


def get_course_take_template() -> str:
    """Devuelve la ruta del template para tomar un curso (estudiante inscrito)."""
    THEME = get_current_theme()

    COURSE_TAKE = Path(path.join(get_theme_path(), "overrides", "course_take.j2"))

    if COURSE_TAKE.exists():
        return THEMES_DIRECTORY + str(THEME) + "/overrides/course_take.j2"
    return "learning/curso.html"


def get_take_evaluation_template() -> str:
    """Devuelve la ruta del template para presentar una evaluación."""
    THEME = get_current_theme()

    TAKE_EVALUATION = Path(path.join(get_theme_path(), "overrides", "take_evaluation.j2"))

    if TAKE_EVALUATION.exists():
        return THEMES_DIRECTORY + str(THEME) + "/overrides/take_evaluation.j2"
    return "evaluations/take_evaluation.html"


def get_evaluation_result_template() -> str:
    """Devuelve la ruta del template del resultado de una evaluación."""
    THEME = get_current_theme()

    EVALUATION_RESULT = Path(path.join(get_theme_path(), "overrides", "evaluation_result.j2"))

    if EVALUATION_RESULT.exists():
        return THEMES_DIRECTORY + str(THEME) + "/overrides/evaluation_result.j2"
    return "evaluations/evaluation_result.html"


def get_practice_template() -> str:
    """Devuelve la ruta del template de práctica por dominio."""
    THEME = get_current_theme()

    PRACTICE = Path(path.join(get_theme_path(), "overrides", "practice.j2"))

    if PRACTICE.exists():
        return THEMES_DIRECTORY + str(THEME) + "/overrides/practice.j2"
    return "evaluations/practice.html"


def get_resource_list_template() -> str:
    """Devuelve la ruta del template de la lista de recursos."""
    THEME = get_current_theme()

    RESOURCE_LIST = Path(path.join(get_theme_path(), "overrides", "resource_list.j2"))

    if RESOURCE_LIST.exists():
        return THEMES_DIRECTORY + str(THEME) + "/overrides/resource_list.j2"
    return "inicio/recursos.html"


def get_resource_view_template() -> str:
    """Devuelve la ruta del template de vista de recurso."""
    THEME = get_current_theme()

    RESOURCE_VIEW = Path(path.join(get_theme_path(), "overrides", "resource_view.j2"))

    if RESOURCE_VIEW.exists():
        return THEMES_DIRECTORY + str(THEME) + "/overrides/resource_view.j2"
    return "learning/recursos/recurso.html"


# ---------------------------------------------------------------------------------------
# Theme loading and context utilities
# ---------------------------------------------------------------------------------------


def _load_macro(theme_name: str, filename: str, macro_name: str):
    """Carga un macro desde un tema, con fallback al tema por defecto."""
    default_path = THEMES_DIRECTORY + "now_lms/" + filename
    theme_path = THEMES_DIRECTORY + theme_name + "/" + filename

    try:
        return get_macro(theme_path, macro_name)
    except Exception:
        return get_macro(default_path, macro_name)


def current_theme() -> SimpleNamespace:
    """Carga las variables de los temas en el contexto de la aplicacion."""
    theme_name = get_current_theme() or "now_lms"

    return SimpleNamespace(
        headertags=_load_macro(theme_name, "header.j2", "headertags"),
        jslibs=_load_macro(theme_name, "js.j2", "jslibs"),
        local_style=_load_macro(theme_name, "local_style.j2", "local_style"),
        navbar=_load_macro(theme_name, "navbar.j2", "navbar"),
        notify=_load_macro(theme_name, "notify.j2", "notify"),
        rendizar_paginacion=_load_macro(theme_name, "pagination.j2", "paginate"),
        footer=_load_macro(theme_name, "footer.j2", "footer"),
    )


def list_themes() -> list[str]:
    """Devuelve una lista de los temas disponibles."""
    from os import listdir
    from os.path import isdir
    from os.path import join

    # Build path to themes directory
    THEMES_PATH = join(str(DIRECTORIO_PLANTILLAS), "themes")
    TEMPLATE_LIST = []

    # Scan directory for available themes, only including valid theme directories
    for entry in listdir(THEMES_PATH):
        entry_path = join(THEMES_PATH, entry)
        if isdir(entry_path) and path.isfile(join(entry_path, "theme.yml")):
            TEMPLATE_LIST.append(entry)

    # Return sorted list for consistent ordering
    TEMPLATE_LIST.sort()
    return TEMPLATE_LIST
