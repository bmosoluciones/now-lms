# Copyright 2022 - 2024 BMO Soluciones, S.A.
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

"""Plantillas para certificados en Linea."""

# ---------------------------------------------------------------------------------------
# Libreria estandar
# ---------------------------------------------------------------------------------------


# ---------------------------------------------------------------------------------------
# Librerias de terceros
# ---------------------------------------------------------------------------------------


# ---------------------------------------------------------------------------------------
# Recursos locales
# ---------------------------------------------------------------------------------------

CERTIFICADO_HORIZONTAL_TITULO = "Basico Horizontal"

CERTIFICADO_HORIZONTAL_DESCRIPCION = "Certificado básico en formato horizontal."

CERTIFICADO_HORIZONTAL_HTML = """
<!doctype html>
<html lang="es">
    <head>
        <meta charset="UTF-8" />
        <title>Certificado de Finalización</title>
    </head>
    <body>
        <div class="certificado">
            <div class="titulo">Certificado de Finalización</div>
            <div class="subtitulo">Otorgado a</div>
            <div class="nombre">{{ usuario.nombre }} {{ usuario.apellido }}</div>
            <div class="curso">
                Por haber completado satisfactoriamente el curso<br /><strong
                    >{{ curso.nombre }}</strong
                >
            </div>
            <div class="footer">
                <div class="firma">
                    Fecha: {{ certificacion.fecha }}<br />
                </div>
            </div>
            <div>
            <img src="{{ url_for("certificate.certificacion_qr", id=certificacion.id) }}" alt="QR Code" width="50" height="50">
            </div>
        </div>
    </body>
</html>
"""

CERTIFICADO_HORIZONTAL_CSS = """
@page {
                size: letter landscape;
                margin: 0;
            }

            body {
                width: 11in;
                height: 8.5in;
                margin: 0;
                padding: 1in;
                font-family: "Georgia", serif;
                background: #fdfdfd;
                color: #333;
                box-sizing: border-box;
            }

            .certificado {
                padding: 2em;
                height: 100%;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                text-align: center;
            }

            .titulo {
                font-size: 2.5em;
                font-weight: bold;
                margin-bottom: 0.5em;
            }

            .subtitulo {
                font-size: 1.3em;
                margin-bottom: 1.5em;
            }

            .nombre {
                font-size: 2em;
                font-weight: bold;
                margin: 0.5em 0;
            }

            .curso {
                font-size: 1.3em;
                margin-bottom: 2em;
            }

            .footer {
                display: flex;
                justify-content: space-around;
                width: 100%;
                margin-top: 3em;
                font-size: 1em;
            }

            .firma {
                text-align: center;
                width: 40%;
            }

            .firma .linea {
                margin-top: 3em;
                border-top: 1px solid #000;
                width: 80%;
                margin-left: auto;
                margin-right: auto;
            }
"""


CERTIFICADO_VERTICAL_TITULO = "Basico Vertical"

CERTIFICADO_VERTICAL_DESCRIPCION = "Certificado basico vertical"

CERTIFICADO_VERTICAL_HTML = """
<!doctype html>
<html lang="es">
    <head>
        <meta charset="UTF-8" />
        <title>Certificado de Finalización</title>
    </head>
    <body>
        <div class="certificado">
            <div class="titulo">Certificado de Finalización</div>
            <div class="subtitulo">Otorgado a</div>
            <div class="nombre">{{ usuario.nombre }} {{ usuario.apellido }}</div>
            <div class="curso">
                Por haber completado satisfactoriamente el curso<br /><strong
                    >{{ curso.nombre }}</strong
                >
            </div>
            <div class="footer">
                <div class="firma">
                    Fecha: {{ certificacion.fecha }}<br />
                </div>
            </div>
            <div>
            <img src="{{ url_for("certificate.certificacion_qr", id=certificacion.id) }}" alt="QR Code" width="50" height="50">
            </div>
        </div>
    </body>
</html>
"""

CERTIFICADO_VERTICAL_CSS = """
@page {
                size: letter;
                margin: 0;
            }

            body {
                width: 8.5in;
                height: 11in;
                margin: 0;
                padding: 1in;
                font-family: "Georgia", serif;
                background: #fdfdfd;
                color: #333;
                box-sizing: border-box;
            }

            .certificado {
                padding: 2em;
                height: 100%;
                display: flex;
                flex-direction: column;
                justify-content: center;
                text-align: center;
            }

            .titulo {
                font-size: 2em;
                font-weight: bold;
                margin-bottom: 0.5em;
            }

            .subtitulo {
                font-size: 1.2em;
                margin-bottom: 2em;
            }

            .nombre {
                font-size: 1.8em;
                font-weight: bold;
                margin: 0.5em 0;
            }

            .curso {
                font-size: 1.2em;
                margin-bottom: 2em;
            }

            .footer {
                display: flex;
                justify-content: space-between;
                margin-top: 3em;
                font-size: 0.9em;
            }

            .firma {
                text-align: center;
                flex: 1;
            }

            .firma .linea {
                margin-top: 3em;
                border-top: 1px solid #000;
                width: 80%;
                margin-left: auto;
                margin-right: auto;
            }
"""

CERTIFICADOS = (
    (
        CERTIFICADO_HORIZONTAL_TITULO,
        CERTIFICADO_HORIZONTAL_DESCRIPCION,
        CERTIFICADO_HORIZONTAL_HTML,
        CERTIFICADO_HORIZONTAL_CSS,
    ),
    (
        CERTIFICADO_VERTICAL_TITULO,
        CERTIFICADO_VERTICAL_DESCRIPCION,
        CERTIFICADO_VERTICAL_HTML,
        CERTIFICADO_VERTICAL_CSS,
    ),
)
