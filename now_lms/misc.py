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

from typing import NamedTuple

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
