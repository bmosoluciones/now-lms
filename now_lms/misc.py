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


"""Utilerias varias."""

# ---------------------------------------------------------------------------------------
# Libreria estandar
# ---------------------------------------------------------------------------------------
from collections import OrderedDict
from typing import NamedTuple, Union

# ---------------------------------------------------------------------------------------
# Librerias de terceros
# ---------------------------------------------------------------------------------------


# ---------------------------------------------------------------------------------------
# Recursos locales
# ---------------------------------------------------------------------------------------


def concatenar_parametros_a_url(
    parametros: Union[OrderedDict, None], arg: Union[str, None], val: Union[str, None], char: str = ""
) -> str:
    """Devuelve lista de paramentros como una cadena de URL."""

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
    """Configuraciòn de estilo personalizable."""

    navbar: dict
    texto: dict
    logo: dict
    buttom: dict


NAV_BAR = {
    "dark": "navbar-dark bg-dark",
    "light": "",
    "transparent": "",
}

TEXTO = {
    "dark": "text-white",
    "light": "link-dark",
    "transparent": "",
}

LOGO = {
    "dark": "logo_horizontal_blanco.svg",
    "light": "logo_horizontal.svg",
    "transparent": "",
}

BUTTOM = {
    "dark": "btn-outline-light",
    "light": "btn-info",
    "transparent": "",
}

ESTILO = EstiloLocal(NAV_BAR, TEXTO, LOGO, BUTTOM)

TEMPLATES_BY_TYPE: dict = {
    "html": "type_html.html",
    "img": "type_img.html",
    "link": "type_link.html",
    "meet": "type_meet.html",
    "mp3": "type_audio.html",
    "pdf": "type_pdf.html",
    "slides": "type_slides.html",
    "text": "type_text.html",
    "youtube": "type_youtube.html",
}

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
    """Estilo de alertas."""

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
    "error": "alert alert-dange",
    "warning": "alert alert-warning",
}

ESTILO_ALERTAS = EstiloAlterta(icono=ICONOS_ALERTAS, clase=ESTILOS_ALERTAS)
