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


"""Miscellaneous utilities."""

# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------
from collections import OrderedDict
from typing import NamedTuple

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------
from bleach import clean, linkify
from flask import redirect
from markdown import markdown

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------


INICIO_SESION = redirect("/user/login")
PANEL_DE_USUARIO = redirect("/home/panel")


def concatenar_parametros_a_url(parametros: OrderedDict | None, arg: str | None, val: str | None, char: str = "") -> str:
    """Return list of parameters as a URL string.

    Args:
        parametros: Dictionary of existing parameters
        arg: New parameter name to add
        val: New parameter value to add
        char: Character to prefix the string with

    Returns:
        String representation of URL parameters
    """
    argumentos: str = char

    if parametros:
        if arg and val:
            parametros[arg] = val

        for key, value in parametros.items():
            argumentos = argumentos + "&" + key + "=" + value
    elif arg and val:
        argumentos = argumentos + "&" + arg + "=" + val

    if char is not None and argumentos.find("&") == 1:
        argumentos = char + argumentos[2:]

    return argumentos


TIPOS_DE_USUARIO: list = ["admin", "user", "instructor", "moderator"]

ICONOS_RECURSOS: dict = {
    "html": "bi bi-code-square",
    "img": "bi bi-image",
    "link": "bi bi-link",
    "meet": "bi bi-broadcast",
    "mp3": "bi bi-soundwave",
    "pdf": "bi bi-file-pdf-fill",
    "slides": "bi bi-file-slides",
    "text": "bi bi-blockquote-left",
    "youtube": "bi bi-youtube",
}


class EstiloLocal(NamedTuple):
    """Customizable style configuration.

    Attributes:
        navbar: Navigation bar style settings
        texto: Text style settings
        logo: Logo style settings
        buttom: Button style settings
    """

    navbar: dict
    texto: dict
    logo: dict
    buttom: dict


HTML_TAGS = [
    "a",
    "abbr",
    "acronym",
    "b",
    "blockquote",
    "br",
    "code",
    "dd",
    "del",
    "div",
    "dl",
    "dt",
    "em",
    "em",
    "h1",
    "h2",
    "h3",
    "hr",
    "i",
    "img",
    "li",
    "ol",
    "p",
    "pre",
    "s",
    "strong",
    "sub",
    "sup",
    "table",
    "tbody",
    "td",
    "th",
    "thead",
    "tr",
    "ul",
]


def markdown_to_clean_html(text: str):
    """Return clean HTML from a MarkDown text.

    Args:
        text: MarkDown formatted text

    Returns:
        Clean HTML string with allowed tags and attributes
    """
    allowed_tags = HTML_TAGS
    allowed_attrs = {"*": ["class"], "a": ["href", "rel"], "img": ["src", "alt"]}

    html = markdown(text)
    html_limpio = clean(linkify(html), tags=allowed_tags, attributes=allowed_attrs)

    return html_limpio


def sanitize_slide_content(html_content: str) -> str:
    """Sanitiza el contenido HTML de una diapositiva según los requerimientos."""
    # Etiquetas permitidas según la especificación
    allowed_tags = ["p", "b", "i", "ul", "li", "strong", "em", "a", "br", "img", "h1", "h2", "h3", "h4"]

    # Atributos permitidos
    allowed_attrs = {
        "a": ["href", "rel", "target"],
        "img": ["src", "alt", "width", "height", "class"],
        "*": ["class", "id"],
    }

    # Limpiar el HTML
    clean_html = clean(html_content, tags=allowed_tags, attributes=allowed_attrs, strip=True)

    return clean_html


CURSO_NIVEL: dict = {
    0: """<i class="bi bi-circle" aria-hidden="true"></i> Nivel Introductorio""",
    1: """<i class="bi bi-circle-fill" aria-hidden="true"></i> Nivel Principiante""",
    2: """<i class="bi bi-circle-fill" aria-hidden="true"></i> <i class="bi bi-circle-fill" aria-hidden="true"></i> Nivel Intermedio""",
    3: """
    <i class="bi bi-circle-fill" aria-hidden="true">
    </i> <i class="bi bi-circle-fill" aria-hidden="true">
    </i> <i class="bi bi-circle-fill" aria-hidden="true"></i>
    Nivel Avanzado
    """,
}

GENEROS: dict = {
    "male": """<i class="bi bi-gender-male" aria-hidden="true"></i>""",
    "female": """<i class="bi bi-gender-female" aria-hidden="true"></i>""",
    "other": """<i class="bi bi-gender-ambiguous" aria-hidden="true"></i>""",
    "none": """No espeficicado.""",
}

TIPOS_RECURSOS: dict = {
    "cheat_sheet": """<i class="bi bi-card-checklist" aria-hidden="true"></i>""",
    "ebook": """<i class="bi bi-book" aria-hidden="true"></i>""",
    "template": """<i class="bi bi-pencil-square" aria-hidden="true"></i>""",
}


class EstiloAlterta(NamedTuple):
    """Alert style configuration.

    Attributes:
        icono: Icon styles for alerts
        clase: CSS class styles for alerts
    """

    icono: dict
    clase: dict


ICONOS_ALERTAS: dict = {
    "info": "bi bi-info-circle",
    "success": "bi bi-check-circle",
    "error": "bi bi-slash-circle",
    "warning": "bi bi-radioactive",
}

ESTILOS_ALERTAS: dict = {
    "info": "alert alert-primary",
    "success": "alert alert-success",
    "error": "alert alert-danger",
    "warning": "alert alert-warning",
}

ESTILO_ALERTAS = EstiloAlterta(icono=ICONOS_ALERTAS, clase=ESTILOS_ALERTAS)
