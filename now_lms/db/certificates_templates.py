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

"""Plantillas para certificados en Linea."""


from __future__ import annotations

# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------


# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------


# ---------------------------------------------------------------------------------------
# Local resources
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
            <img src="{{ url_for("certificate.certificacion_qr", cert_id=certificacion.id) }}" alt="QR Code" width="50" height="50">
            </div>
        </div>
    </body>
</html>
"""

CERTIFICADO_HORIZONTAL_CSS = """
@page {
    size: letter landscape;
    margin: 0.5in;
}

body {
    width: 10in;
    height: 7.5in;
    margin: 0;
    padding: 0;
    font-family: "Georgia", serif;
    background: #fdfdfd;
    color: #333;
    box-sizing: border-box;
}

.certificado {
    padding: 1.5em;
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
    box-sizing: border-box;
}

.titulo {
    font-size: 2em;
    font-weight: bold;
    margin-bottom: 0.5em;
}

.subtitulo {
    font-size: 1.1em;
    margin-bottom: 1.2em;
}

.nombre {
    font-size: 1.6em;
    font-weight: bold;
    margin: 0.5em 0;
}

.curso {
    font-size: 1.1em;
    margin-bottom: 1.5em;
}

.footer {
    display: flex;
    justify-content: space-around;
    width: 100%;
    margin-top: 2em;
    font-size: 0.9em;
}

.firma {
    text-align: center;
    width: 40%;
}

.firma .linea {
    margin-top: 2em;
    border-top: 1px solid #000;
    width: 80%;
    margin-left: auto;
    margin-right: auto;
}

img {
    width: 40px;
    height: 40px;
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
            <img src="{{ url_for("certificate.certificacion_qr", cert_id=certificacion.id) }}" alt="QR Code" width="50" height="50">
            </div>
        </div>
    </body>
</html>
"""

CERTIFICADO_VERTICAL_CSS = """
@page {
    size: letter;
    margin: 0.5in;
}

body {
    width: 7.5in;
    height: 10in;
    margin: 0;
    padding: 0;
    font-family: "Georgia", serif;
    background: #fdfdfd;
    color: #333;
    box-sizing: border-box;
}

.certificado {
    padding: 1.5em;
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: center;
    text-align: center;
    box-sizing: border-box;
}

.titulo {
    font-size: 1.6em;
    font-weight: bold;
    margin-bottom: 0.5em;
}

.subtitulo {
    font-size: 1em;
    margin-bottom: 1.5em;
}

.nombre {
    font-size: 1.4em;
    font-weight: bold;
    margin: 0.5em 0;
}

.curso {
    font-size: 1em;
    margin-bottom: 1.5em;
}

.footer {
    display: flex;
    justify-content: space-between;
    margin-top: 2em;
    font-size: 0.8em;
}

.firma {
    text-align: center;
    flex: 1;
}

.firma .linea {
    margin-top: 2em;
    border-top: 1px solid #000;
    width: 80%;
    margin-left: auto;
    margin-right: auto;
}

img {
    width: 40px;
    height: 40px;
}
"""

# ---------------------------------------------------------------------------------------
# Plantilla Elegante
# ---------------------------------------------------------------------------------------

CERTIFICADO_ELEGANTE_TITULO = "Elegante"

CERTIFICADO_ELEGANTE_DESCRIPCION = "Certificado elegante con bordes decorativos y tipografía sofisticada."

CERTIFICADO_ELEGANTE_HTML = """
<!doctype html>
<html lang="es">
    <head>
        <meta charset="UTF-8" />
        <title>Certificado de Finalización</title>
    </head>
    <body>
        <div class="certificado">
            <div class="border-decorativo"></div>
            <div class="header">
                <div class="titulo">CERTIFICADO</div>
                <div class="subtitulo">DE FINALIZACIÓN</div>
            </div>
            <div class="contenido">
                <div class="otorgado">Se otorga el presente certificado a</div>
                <div class="nombre">{{ usuario.nombre }} {{ usuario.apellido }}</div>
                <div class="reconocimiento">
                    En reconocimiento por haber completado exitosamente el curso
                </div>
                <div class="curso">{{ curso.nombre }}</div>
                <div class="fecha-firma">
                    <div class="fecha">Fecha: {{ certificacion.fecha }}</div>
                    <div class="qr-container">
                        <img src="{{ url_for("certificate.certificacion_qr", cert_id=certificacion.id) }}" alt="QR Code" width="60" height="60">
                    </div>
                </div>
            </div>
        </div>
    </body>
</html>
"""

CERTIFICADO_ELEGANTE_CSS = """
@page {
    size: letter landscape;
    margin: 0.5in;
}

body {
    width: 10in;
    height: 7.5in;
    margin: 0;
    padding: 0;
    font-family: "Times New Roman", serif;
    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    color: #2c3e50;
    box-sizing: border-box;
}

.certificado {
    width: 100%;
    height: 100%;
    position: relative;
    padding: 0.8in;
    border: 6px solid #8b4513;
    border-radius: 15px;
    background: #ffffff;
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
}

.border-decorativo {
    position: absolute;
    top: 15px;
    left: 15px;
    right: 15px;
    bottom: 15px;
    border: 1px solid #d4af37;
    border-radius: 10px;
    background: radial-gradient(circle at center, rgba(212, 175, 55, 0.1) 0%, transparent 70%);
}

.header {
    text-align: center;
    margin-bottom: 0.8in;
}

.titulo {
    font-size: 2.2em;
    font-weight: bold;
    color: #8b4513;
    letter-spacing: 0.2em;
    margin-bottom: 0.2em;
    text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
}

.subtitulo {
    font-size: 1.2em;
    color: #d4af37;
    letter-spacing: 0.3em;
    font-weight: 300;
}

.contenido {
    text-align: center;
    flex-grow: 1;
    display: flex;
    flex-direction: column;
    justify-content: center;
}

.otorgado {
    font-size: 1.1em;
    margin-bottom: 0.6em;
    font-style: italic;
    color: #34495e;
}

.nombre {
    font-size: 2.2em;
    font-weight: bold;
    margin: 0.4em 0;
    color: #8b4513;
    border-bottom: 2px solid #d4af37;
    padding-bottom: 0.2em;
    display: inline-block;
}

.reconocimiento {
    font-size: 1em;
    margin: 0.8em 0 0.4em 0;
    color: #34495e;
}

.curso {
    font-size: 1.4em;
    font-weight: bold;
    margin: 0.6em 0;
    color: #2c3e50;
    font-style: italic;
}

.fecha-firma {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 0.8in;
    padding: 0 1em;
}

.fecha {
    font-size: 0.9em;
    color: #7f8c8d;
}

.qr-container {
    border: 1px solid #d4af37;
    padding: 4px;
    border-radius: 4px;
    background: white;
}

.qr-container img {
    width: 45px;
    height: 45px;
}
"""

# ---------------------------------------------------------------------------------------
# Plantilla Moderna
# ---------------------------------------------------------------------------------------

CERTIFICADO_MODERNO_TITULO = "Moderno"

CERTIFICADO_MODERNO_DESCRIPCION = "Certificado con diseño minimalista y tipografía moderna."

CERTIFICADO_MODERNO_HTML = """
<!doctype html>
<html lang="es">
    <head>
        <meta charset="UTF-8" />
        <title>Certificado de Finalización</title>
    </head>
    <body>
        <div class="certificado">
            <div class="header-section">
                <div class="logo-area"></div>
                <div class="titulo">CERTIFICADO</div>
            </div>
            <div class="main-content">
                <div class="achievement-text">Logro Académico</div>
                <div class="nombre">{{ usuario.nombre }} {{ usuario.apellido }}</div>
                <div class="completion-text">
                    Ha completado satisfactoriamente el programa de formación
                </div>
                <div class="curso">{{ curso.nombre }}</div>
                <div class="metrics">
                    <div class="metric">
                        <div class="metric-label">Fecha de finalización</div>
                        <div class="metric-value">{{ certificacion.fecha }}</div>
                    </div>
                    <div class="qr-section">
                        <div class="qr-label">Verificación</div>
                        <img src="{{ url_for("certificate.certificacion_qr", cert_id=certificacion.id) }}" alt="QR Code" width="50" height="50">
                    </div>
                </div>
            </div>
        </div>
    </body>
</html>
"""

CERTIFICADO_MODERNO_CSS = """
@page {
    size: letter;
    margin: 0.5in;
}

body {
    width: 7.5in;
    height: 10in;
    margin: 0;
    padding: 0;
    font-family: "Helvetica Neue", "Arial", sans-serif;
    background: #ffffff;
    color: #2c3e50;
    box-sizing: border-box;
}

.certificado {
    width: 100%;
    height: 100%;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 10px;
    padding: 0.8in;
    position: relative;
    overflow: hidden;
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
}

.certificado::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(255,255,255,0.95);
    border-radius: 8px;
    margin: 15px;
}

.header-section {
    position: relative;
    z-index: 1;
    text-align: center;
    margin-bottom: 1in;
    padding-top: 0.3in;
}

.logo-area {
    width: 50px;
    height: 3px;
    background: linear-gradient(90deg, #667eea, #764ba2);
    margin: 0 auto 0.8em auto;
    border-radius: 2px;
}

.titulo {
    font-size: 2em;
    font-weight: 100;
    letter-spacing: 0.3em;
    color: #2c3e50;
    margin: 0;
}

.main-content {
    position: relative;
    z-index: 1;
    text-align: center;
    flex-grow: 1;
    display: flex;
    flex-direction: column;
    justify-content: center;
}

.achievement-text {
    font-size: 0.9em;
    color: #7f8c8d;
    font-weight: 300;
    margin-bottom: 0.8em;
    text-transform: uppercase;
    letter-spacing: 0.1em;
}

.nombre {
    font-size: 1.8em;
    font-weight: 300;
    color: #2c3e50;
    margin: 0.6em 0;
    line-height: 1.2;
}

.completion-text {
    font-size: 0.9em;
    color: #34495e;
    margin: 1em 0 0.6em 0;
    font-weight: 300;
    line-height: 1.4;
}

.curso {
    font-size: 1.3em;
    font-weight: 500;
    color: #667eea;
    margin: 0.8em 0 1.2em 0;
    line-height: 1.3;
}

.metrics {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 1.2in;
    padding: 0 0.8em;
}

.metric {
    text-align: left;
}

.metric-label {
    font-size: 0.7em;
    color: #7f8c8d;
    font-weight: 300;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.metric-value {
    font-size: 0.9em;
    color: #2c3e50;
    font-weight: 500;
    margin-top: 0.2em;
}

.qr-section {
    text-align: center;
}

.qr-label {
    font-size: 0.6em;
    color: #7f8c8d;
    margin-bottom: 0.4em;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.qr-section img {
    width: 40px;
    height: 40px;
}
"""

# ---------------------------------------------------------------------------------------
# Plantilla Clásica
# ---------------------------------------------------------------------------------------

CERTIFICADO_CLASICO_TITULO = "Clásico"

CERTIFICADO_CLASICO_DESCRIPCION = "Certificado con estilo tradicional formal y académico."

CERTIFICADO_CLASICO_HTML = """
<!doctype html>
<html lang="es">
    <head>
        <meta charset="UTF-8" />
        <title>Certificado de Finalización</title>
    </head>
    <body>
        <div class="certificado">
            <div class="header-ornament"></div>
            <div class="institution">
                <div class="institution-name">INSTITUCIÓN EDUCATIVA</div>
                <div class="institution-subtitle">Centro de Excelencia Académica</div>
            </div>
            <div class="certificate-title">
                <div class="main-title">CERTIFICADO</div>
                <div class="subtitle">DE FINALIZACIÓN EXITOSA</div>
            </div>
            <div class="content">
                <div class="present-text">Por la presente se certifica que</div>
                <div class="student-name">{{ usuario.nombre }} {{ usuario.apellido }}</div>
                <div class="completion-text">
                    ha completado satisfactoriamente todos los requisitos del programa de estudios
                </div>
                <div class="course-name">{{ curso.nombre }}</div>
                <div class="footer-section">
                    <div class="date-section">
                        <div class="date-label">Expedido el día</div>
                        <div class="date-value">{{ certificacion.fecha }}</div>
                    </div>
                    <div class="verification">
                        <div class="verification-label">Código de verificación</div>
                        <img src="{{ url_for("certificate.certificacion_qr", cert_id=certificacion.id) }}" alt="QR Code" width="55" height="55">
                    </div>
                </div>
            </div>
            <div class="footer-ornament"></div>
        </div>
    </body>
</html>
"""

CERTIFICADO_CLASICO_CSS = """
@page {
    size: letter;
    margin: 0.5in;
}

body {
    width: 7.5in;
    height: 10in;
    margin: 0;
    padding: 0;
    font-family: "Garamond", "Times New Roman", serif;
    background: #fefefe;
    color: #2c3e50;
    box-sizing: border-box;
}

.certificado {
    width: 100%;
    height: 100%;
    border: 4px double #8b4513;
    padding: 0.6in;
    background: #ffffff;
    position: relative;
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
}

.header-ornament {
    width: 80px;
    height: 80px;
    margin: 0 auto 0.8em auto;
    border: 2px solid #d4af37;
    border-radius: 50%;
    position: relative;
    background: radial-gradient(circle, #f8f9fa 0%, #e9ecef 100%);
}

.header-ornament::before {
    content: '★';
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    font-size: 2em;
    color: #d4af37;
}

.institution {
    text-align: center;
    margin-bottom: 1em;
}

.institution-name {
    font-size: 1em;
    font-weight: bold;
    color: #8b4513;
    letter-spacing: 0.1em;
}

.institution-subtitle {
    font-size: 0.8em;
    color: #7f8c8d;
    font-style: italic;
    margin-top: 0.3em;
}

.certificate-title {
    text-align: center;
    margin-bottom: 1.2em;
}

.main-title {
    font-size: 2.2em;
    font-weight: bold;
    color: #8b4513;
    letter-spacing: 0.2em;
    margin-bottom: 0.2em;
}

.subtitle {
    font-size: 1em;
    color: #d4af37;
    letter-spacing: 0.1em;
    font-weight: normal;
}

.content {
    text-align: center;
    flex-grow: 1;
    display: flex;
    flex-direction: column;
    justify-content: center;
}

.present-text {
    font-size: 1em;
    margin-bottom: 0.8em;
    color: #34495e;
    font-style: italic;
}

.student-name {
    font-size: 2em;
    font-weight: bold;
    margin: 0.6em 0;
    color: #2c3e50;
    border-bottom: 2px solid #d4af37;
    padding-bottom: 0.2em;
    display: inline-block;
}

.completion-text {
    font-size: 0.9em;
    margin: 1em 0 0.6em 0;
    color: #34495e;
    line-height: 1.4;
}

.course-name {
    font-size: 1.4em;
    font-weight: bold;
    margin: 0.8em 0 1.2em 0;
    color: #8b4513;
    font-style: italic;
}

.footer-section {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 1.5em;
    padding: 0 1em;
}

.date-section {
    text-align: left;
}

.date-label {
    font-size: 0.8em;
    color: #7f8c8d;
    margin-bottom: 0.3em;
}

.date-value {
    font-size: 1em;
    font-weight: bold;
    color: #2c3e50;
}

.verification {
    text-align: center;
}

.verification-label {
    font-size: 0.7em;
    color: #7f8c8d;
    margin-bottom: 0.4em;
}

.verification img {
    width: 45px;
    height: 45px;
}

.footer-ornament {
    position: absolute;
    bottom: 0.3in;
    left: 50%;
    transform: translateX(-50%);
    width: 150px;
    height: 1px;
    background: linear-gradient(90deg, transparent 0%, #d4af37 50%, transparent 100%);
}
"""

# ---------------------------------------------------------------------------------------
# Plantilla Corporativa
# ---------------------------------------------------------------------------------------

CERTIFICADO_CORPORATIVO_TITULO = "Corporativo"

CERTIFICADO_CORPORATIVO_DESCRIPCION = "Certificado profesional con estilo empresarial moderno."

CERTIFICADO_CORPORATIVO_HTML = """
<!doctype html>
<html lang="es">
    <head>
        <meta charset="UTF-8" />
        <title>Certificado de Finalización</title>
    </head>
    <body>
        <div class="certificado">
            <div class="header">
                <div class="company-logo"></div>
                <div class="header-text">
                    <div class="certificate-type">CERTIFICADO PROFESIONAL</div>
                    <div class="certificate-number">Nº {{ certificacion.id }}</div>
                </div>
            </div>
            <div class="main-section">
                <div class="certifies">CERTIFICA QUE</div>
                <div class="recipient-name">{{ usuario.nombre }} {{ usuario.apellido }}</div>
                <div class="achievement">
                    Ha completado exitosamente el programa de capacitación profesional
                </div>
                <div class="course-title">{{ curso.nombre }}</div>
                <div class="completion-details">
                    Cumpliendo con todos los estándares de calidad y requisitos establecidos
                    por nuestra institución educativa.
                </div>
            </div>
            <div class="footer">
                <div class="credentials">
                    <div class="date-issued">
                        <strong>Fecha de emisión:</strong><br>
                        {{ certificacion.fecha }}
                    </div>
                    <div class="validation">
                        <strong>Validación digital:</strong><br>
                        <img src="{{ url_for("certificate.certificacion_qr", cert_id=certificacion.id) }}" alt="QR Code" width="50" height="50">
                    </div>
                </div>
                <div class="signature-line"></div>
            </div>
        </div>
    </body>
</html>
"""

CERTIFICADO_CORPORATIVO_CSS = """
@page {
    size: letter landscape;
    margin: 0.5in;
}

body {
    width: 10in;
    height: 7.5in;
    margin: 0;
    padding: 0;
    font-family: "Segoe UI", "Calibri", sans-serif;
    background: #f8f9fa;
    color: #2c3e50;
    box-sizing: border-box;
}

.certificado {
    width: 100%;
    height: 100%;
    background: #ffffff;
    border-left: 6px solid #3498db;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    padding: 0.8in;
    position: relative;
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
}

.header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1em;
    padding-bottom: 0.8em;
    border-bottom: 1px solid #ecf0f1;
}

.company-logo {
    width: 60px;
    height: 60px;
    background: linear-gradient(135deg, #3498db, #2980b9);
    border-radius: 6px;
    position: relative;
}

.company-logo::before {
    content: '🎓';
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    font-size: 1.5em;
}

.header-text {
    text-align: right;
}

.certificate-type {
    font-size: 1.1em;
    font-weight: 600;
    color: #2c3e50;
    letter-spacing: 0.05em;
}

.certificate-number {
    font-size: 0.8em;
    color: #7f8c8d;
    margin-top: 0.3em;
}

.main-section {
    text-align: center;
    flex-grow: 1;
    display: flex;
    flex-direction: column;
    justify-content: center;
}

.certifies {
    font-size: 1em;
    color: #7f8c8d;
    font-weight: 300;
    letter-spacing: 0.1em;
    margin-bottom: 0.8em;
}

.recipient-name {
    font-size: 2.2em;
    font-weight: 300;
    color: #2c3e50;
    margin: 0.6em 0;
    line-height: 1.1;
}

.achievement {
    font-size: 1.1em;
    color: #34495e;
    margin: 1em 0 0.6em 0;
    font-weight: 400;
    line-height: 1.3;
}

.course-title {
    font-size: 1.6em;
    font-weight: 600;
    color: #3498db;
    margin: 0.8em 0;
    line-height: 1.2;
}

.completion-details {
    font-size: 0.9em;
    color: #7f8c8d;
    margin: 1em 0;
    line-height: 1.4;
    max-width: 80%;
    margin-left: auto;
    margin-right: auto;
}

.footer {
    margin-top: 1em;
}

.credentials {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 1em;
}

.date-issued, .validation {
    font-size: 0.8em;
    color: #34495e;
    line-height: 1.4;
}

.validation img {
    width: 40px;
    height: 40px;
}

.signature-line {
    width: 200px;
    height: 1px;
    background: #bdc3c7;
    margin: 0 auto;
    position: relative;
}

.signature-line::after {
    content: 'Dirección Académica';
    position: absolute;
    top: 8px;
    left: 50%;
    transform: translateX(-50%);
    font-size: 0.7em;
    color: #7f8c8d;
    background: white;
    padding: 0 0.8em;
}
"""

# ---------------------------------------------------------------------------------------
# Default Certificate Template (English)
# ---------------------------------------------------------------------------------------

CERTIFICADO_DEFAULT_TITULO = "Default"

CERTIFICADO_DEFAULT_DESCRIPCION = "Professional default certificate template in English with comprehensive features including QR verification, security elements, and multi-language support."

CERTIFICADO_DEFAULT_HTML = """
<!doctype html>
<html lang="en">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Certificate of Completion</title>
    </head>
    <body>
        <div class="certificate-container">
            <!-- Header with Institution Branding -->
            <header class="certificate-header">
                <div class="institution-logo">
                    <div class="logo-placeholder">🎓</div>
                </div>
                <div class="institution-info">
                    <h1 class="institution-name">NOW - Learning Management System</h1>
                    <p class="institution-subtitle">Center of Excellence in Education</p>
                </div>
                <div class="certificate-seal">
                    <div class="seal-inner">LMS</div>
                </div>
            </header>

            <!-- Certificate Title -->
            <div class="certificate-title-section">
                <h2 class="certificate-title">CERTIFICATE</h2>
                <p class="certificate-subtitle">OF COMPLETION</p>
            </div>

            <!-- Main Content -->
            <main class="certificate-content">
                <!-- Achievement Statement -->
                <div class="achievement-statement">
                    <p class="certify-text">This is to certify that</p>

                    <!-- Learner Identification -->
                    <div class="recipient-section">
                        <h3 class="recipient-name">{{ usuario.nombre }} {{ usuario.apellido }}</h3>
                        <div class="recipient-details">
                            <p class="student-id">Student ID: {{ usuario.id }}</p>
                        </div>
                    </div>

                    <!-- Course Information -->
                    <div class="course-section">
                        <p class="completion-text">has successfully completed the course</p>
                        <h4 class="course-title">{{ curso.nombre }}</h4>
                        <div class="course-details">
                            <p class="course-type">Course Type:
                                {% if content_type == 'masterclass' %}
                                    Master Class
                                {% else %}
                                    Course
                                {% endif %}
                            </p>
                            {% if curso.instructor %}
                            <p class="instructor-name">Instructor: {{ curso.instructor }}</p>
                            {% endif %}
                        </div>
                    </div>

                    <!-- Completion Details -->
                    <div class="completion-section">
                        <p class="completion-date">Completion Date: {{ certificacion.fecha.strftime('%B %d, %Y') }}</p>
                        {% if certificacion.nota %}
                            <p class="grade-info">
                                Grade: {{ certificacion.nota }}
                                {% if certificacion.nota >= 90 %} with distinction{% endif %}
                            </p>
                        {% endif %}
                    </div>
                </div>
            </main>

            <!-- Footer with Signatures & Validation -->
            <footer class="certificate-footer">
                <div class="signatures-section">
                    <div class="signature-block">
                        <div class="signature-line"></div>
                        <p class="signature-title">Academic Director</p>
                        <p class="signature-date">{{ certificacion.fecha.strftime('%B %d, %Y') }}</p>
                    </div>

                    <div class="validation-section">
                        <div class="qr-code-container">
                            <img src="{{ url_for('certificate.certificacion_qr', cert_id=certificacion.id) }}"
                                 alt=QR Code for certificate verification"
                                 class="qr-code">
                            <p class="qr-label">Scan to verify</p>
                        </div>
                    </div>
                </div>

                <!-- Certificate Metadata -->
                <div class="certificate-metadata">
                    <div class="metadata-item">
                        <span class="metadata-label">Certificate ID:</span>
                        <span class="metadata-value">{{ certificacion.id }}</span>
                    </div>
                    <div class="metadata-item">
                        <span class="metadata-label">Issue Date:</span>
                        <span class="metadata-value">{{ certificacion.fecha.strftime('%Y-%m-%d') }}</span>
                    </div>
                    <div class="metadata-item">
                        <span class="metadata-label">Verification URL:</span>
                        <span class="metadata-value verification-url">{{ url_for('certificate.certificado', ulid=certificacion.id, _external=True) }}</span>
                    </div>
                </div>
            </footer>

            <!-- Security Watermark -->
            <div class="security-watermark" aria-hidden="true">AUTHENTIC</div>
        </div>
    </body>
</html>
"""

CERTIFICADO_DEFAULT_CSS = """
/* Letter size page setup for PDF generation */
@page {
    size: letter; /* 8.5in x 11in portrait */
    margin: 0.5in;
}

/* CSS Variables for theme consistency */
:root {
    --primary-color: #2c3e50;
    --secondary-color: #3498db;
    --accent-color: #f39c12;
    --text-color: #2c3e50;
    --light-text: #7f8c8d;
    --border-color: #bdc3c7;
    --background: #ffffff;
    --light-background: #f8f9fa;
    --success-color: #27ae60;
    --seal-color: #e74c3c;
}

/* Base styles */
body {
    width: 7.5in;
    height: 10in;
    margin: 0;
    padding: 0;
    font-family: "Georgia", "Times New Roman", serif;
    background: var(--background);
    color: var(--text-color);
    box-sizing: border-box;
    line-height: 1.4;
}

/* Certificate container */
.certificate-container {
    width: 100%;
    height: 100%;
    padding: 0.5in;
    border: 3px solid var(--primary-color);
    border-radius: 8px;
    background: var(--background);
    position: relative;
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
    box-shadow: inset 0 0 0 1px var(--border-color);
}

/* Header with Institution Branding */
.certificate-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 0.8in;
    padding-bottom: 0.3in;
    border-bottom: 2px solid var(--border-color);
}

.institution-logo {
    flex: 0 0 auto;
}

.logo-placeholder {
    width: 60px;
    height: 60px;
    background: linear-gradient(135deg, var(--secondary-color), var(--primary-color));
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.8em;
    color: white;
    font-weight: bold;
}

.institution-info {
    flex: 1;
    text-align: center;
    margin: 0 1em;
}

.institution-name {
    font-size: 1.1em;
    font-weight: bold;
    color: var(--primary-color);
    margin: 0 0 0.2em 0;
    letter-spacing: 0.05em;
}

.institution-subtitle {
    font-size: 0.8em;
    color: var(--light-text);
    font-style: italic;
    margin: 0;
}

.certificate-seal {
    flex: 0 0 auto;
    width: 60px;
    height: 60px;
    border: 3px solid var(--accent-color);
    border-radius: 50%;
    background: radial-gradient(circle, var(--light-background) 0%, var(--background) 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
}

.seal-inner {
    font-size: 0.8em;
    font-weight: bold;
    color: var(--accent-color);
    letter-spacing: 0.1em;
}

/* Certificate Title */
.certificate-title-section {
    text-align: center;
    margin-bottom: 0.8in;
}

.certificate-title {
    font-size: 2.2em;
    font-weight: bold;
    color: var(--primary-color);
    letter-spacing: 0.2em;
    margin: 0 0 0.2em 0;
    text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
}

.certificate-subtitle {
    font-size: 1.1em;
    color: var(--secondary-color);
    letter-spacing: 0.1em;
    font-weight: normal;
    margin: 0;
}

/* Main Content */
.certificate-content {
    flex: 1;
    text-align: center;
}

/* Achievement Statement */
.achievement-statement {
    margin-bottom: 0.8in;
}

.certify-text {
    font-size: 1em;
    color: var(--text-color);
    font-style: italic;
    margin: 0 0 0.8em 0;
}

/* Learner Identification */
.recipient-section {
    margin: 0.8em 0;
}

.recipient-name {
    font-size: 1.8em;
    font-weight: bold;
    color: var(--primary-color);
    margin: 0 0 0.3em 0;
    border-bottom: 2px solid var(--accent-color);
    padding-bottom: 0.2em;
    display: inline-block;
    line-height: 1.2;
}

.recipient-details {
    margin: 0.5em 0;
}

.student-id {
    font-size: 0.8em;
    color: var(--light-text);
    margin: 0;
}

/* Course Information */
.course-section {
    margin: 1em 0;
}

.completion-text {
    font-size: 1em;
    color: var(--text-color);
    margin: 0 0 0.6em 0;
}

.course-title {
    font-size: 1.4em;
    font-weight: bold;
    color: var(--secondary-color);
    margin: 0.5em 0;
    line-height: 1.3;
    font-style: italic;
}

.course-details {
    margin: 0.6em 0;
}

.course-type,
.instructor-name {
    font-size: 0.9em;
    color: var(--text-color);
    margin: 0.3em 0;
}

/* Completion Details */
.completion-section {
    margin: 1em 0;
}

.completion-date,
.grade-info {
    font-size: 0.9em;
    color: var(--text-color);
    margin: 0.3em 0;
}

.grade-info {
    font-weight: 600;
    color: var(--success-color);
}

/* Footer */
.certificate-footer {
    margin-top: auto;
    padding-top: 0.5in;
    border-top: 1px solid var(--border-color);
}

/* Signatures & Validation */
.signatures-section {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    margin-bottom: 0.8em;
}

.signature-block {
    flex: 1;
    text-align: left;
}

.signature-line {
    width: 180px;
    height: 1px;
    background: var(--border-color);
    margin-bottom: 0.3em;
}

.signature-title {
    font-size: 0.8em;
    font-weight: bold;
    color: var(--text-color);
    margin: 0.2em 0;
}

.signature-date {
    font-size: 0.7em;
    color: var(--light-text);
    margin: 0;
}

/* QR Code Validation */
.validation-section {
    flex: 0 0 auto;
    text-align: center;
}

.qr-code-container {
    border: 1px solid var(--border-color);
    padding: 8px;
    border-radius: 4px;
    background: var(--background);
}

.qr-code {
    width: 50px;
    height: 50px;
    display: block;
}

.qr-label {
    font-size: 0.6em;
    color: var(--light-text);
    margin: 0.3em 0 0 0;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* Certificate Metadata */
.certificate-metadata {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.7em;
    color: var(--light-text);
    padding: 0.3em 0;
    border-top: 1px solid var(--border-color);
    flex-wrap: wrap;
    gap: 0.5em;
}

.metadata-item {
    flex: 1;
    min-width: 150px;
}

.metadata-label {
    font-weight: 600;
}

.metadata-value {
    margin-left: 0.3em;
}

.verification-url {
    font-family: "Monaco", "Courier New", monospace;
    font-size: 0.9em;
    word-break: break-all;
}

/* Security Watermark */
.security-watermark {
    position: absolute;
    top: 45%;
    left: 35%;
    font-size: 3em;
    color: rgba(52, 73, 94, 0.03);
    font-weight: bold;
    letter-spacing: 0.2em;
    transform: rotate(-25deg);
    pointer-events: none;
    z-index: 0;
    font-family: "Arial Black", sans-serif;
}

/* Ensure content is above watermark */
.certificate-header,
.certificate-title-section,
.certificate-content,
.certificate-footer {
    position: relative;
    z-index: 1;
}

/* Print optimization */
@media print {
    body {
        width: 100%;
        height: 100vh;
        margin: 0;
        padding: 0;
    }

    .certificate-container {
        border-radius: 0;
        box-shadow: none;
        width: 100%;
        height: 100%;
    }

    /* Remove any interactive elements for print */
    .verification-url {
        color: var(--text-color) !important;
    }
}

/* Responsive design for preview */
@media screen and (max-width: 1024px) {
    .certificate-container {
        width: 100%;
        max-width: 800px;
        height: auto;
        min-height: 800px;
        padding: 30px;
    }

    .certificate-title {
        font-size: 1.8em;
    }

    .recipient-name {
        font-size: 1.5em;
    }

    .course-title {
        font-size: 1.2em;
    }

    .certificate-header {
        flex-direction: column;
        align-items: center;
        gap: 1em;
        text-align: center;
    }

    .signatures-section {
        flex-direction: column;
        align-items: center;
        gap: 1em;
    }

    .certificate-metadata {
        flex-direction: column;
        gap: 0.3em;
    }

    .metadata-item {
        text-align: center;
    }
}

/* Accessibility improvements */
@media (prefers-reduced-motion: reduce) {
    * {
        transition: none !important;
        animation: none !important;
    }
}

/* High contrast mode support */
@media (prefers-contrast: high) {
    :root {
        --primary-color: #000000;
        --secondary-color: #0066cc;
        --text-color: #000000;
        --border-color: #666666;
    }

    .certificate-container {
        border-width: 2px;
    }
}
"""

# ---------------------------------------------------------------------------------------
# Professional Course Certificate Template (Inspired by Safety Training Design)
# ---------------------------------------------------------------------------------------

CERTIFICADO_PROFESIONAL_TITULO = "Profesional"

CERTIFICADO_PROFESIONAL_DESCRIPCION = "Certificado profesional moderno inspirado en diseños corporativos de alta calidad con elementos de seguridad y verificación."

CERTIFICADO_PROFESIONAL_HTML = """
<!doctype html>
<html lang="es">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Certificado Profesional</title>
    </head>
    <body>
        <div class="certificate-container">
            <!-- Header Section -->
            <header class="certificate-header">
                <div class="brand-section">
                    <div class="brand-logo">🎓</div>
                    <div class="provider-info">
                        <div class="provider-text">Your CE Provider Logo</div>
                    </div>
                </div>
            </header>

            <!-- Title Section -->
            <div class="title-section">
                <h1 class="certificate-title">Certificate of Safety Training</h1>
            </div>

            <!-- Content Section -->
            <main class="content-section">
                <div class="proudly-text">Proudly presented to</div>

                <div class="recipient-name">{{ usuario.nombre }} {{ usuario.apellido }}</div>

                <div class="completion-statement">
                    <span class="completion-text">Successfully completed a</span>
                    <span class="course-name">{{ curso.nombre }}</span>
                </div>

                <!-- Metrics Section -->
                <div class="metrics-section">
                    <div class="metric-item">
                        <div class="metric-label">Credits earned:</div>
                        <div class="metric-value">{{ curso.creditos or '4.6' }}</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-label">Certificate ID:</div>
                        <div class="metric-value">{{ certificacion.id }}</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-label">Certified on:</div>
                        <div class="metric-value">{{ certificacion.fecha.strftime('%d.%m.%Y') }}</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-label">Expiry Date:</div>
                        <div class="metric-value">{{ (certificacion.fecha.replace(year=certificacion.fecha.year + 2)).strftime('%d.%m.%Y') }}</div>
                    </div>
                </div>
            </main>

            <!-- Footer Section -->
            <footer class="certificate-footer">
                <div class="signatures-section">
                    <div class="signature-block">
                        <div class="signature-line"></div>
                        <div class="signature-name">{{ curso.instructor or 'Bonnie Wilson' }}</div>
                        <div class="signature-title">Course Instructor</div>
                    </div>
                    <div class="signature-block">
                        <div class="signature-line"></div>
                        <div class="signature-name">Mark Allford</div>
                        <div class="signature-title">Program Director</div>
                    </div>
                </div>

                <!-- Accreditation and QR -->
                <div class="accreditation-section">
                    <div class="accreditation-badge">
                        <div class="badge-icon">🛡️</div>
                        <div class="badge-text">
                            <div class="association-name">Safety Association</div>
                            <div class="accreditation-text">ACCREDITED<br>TRAINING<br>PROVIDER</div>
                        </div>
                    </div>
                    <div class="qr-section">
                        <img src="{{ url_for('certificate.certificacion_qr', cert_id=certificacion.id) }}"
                             alt="QR Code"
                             class="qr-code">
                    </div>
                </div>
            </footer>
        </div>
    </body>
</html>
"""

CERTIFICADO_PROFESIONAL_CSS = """
/* Letter size landscape page setup for PDF generation */
@page {
    size: letter landscape; /* 11in x 8.5in landscape */
    margin: 0.3in;
}

/* Color scheme inspired by the safety training certificate */
:root {
    --primary-purple: #4a2c7a;
    --accent-purple: #6441a4;
    --light-purple: #8b6bb1;
    --background-light: #f7f5ff;
    --text-dark: #2c1810;
    --text-light: #5a4a6a;
    --white: #ffffff;
    --border-light: #e0d0f0;
    --metric-bg: #e8e0f5;
}

/* Base styles */
body {
    width: 10.5in;
    height: 8in;
    margin: 0;
    padding: 0;
    font-family: "Arial", "Helvetica", sans-serif;
    background: var(--background-light);
    color: var(--text-dark);
    box-sizing: border-box;
}

/* Certificate container */
.certificate-container {
    width: 100%;
    height: 100%;
    background: var(--white);
    border-radius: 20px;
    padding: 0.6in;
    position: relative;
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
    border: 8px solid var(--primary-purple);
    box-shadow: 0 4px 20px rgba(74, 44, 122, 0.15);
}

/* Header Section */
.certificate-header {
    display: flex;
    justify-content: flex-end;
    align-items: flex-start;
    margin-bottom: 0.4in;
}

.brand-section {
    display: flex;
    align-items: center;
    gap: 0.5em;
}

.brand-logo {
    width: 40px;
    height: 40px;
    background: var(--primary-purple);
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.2em;
    color: var(--white);
}

.provider-info {
    background: var(--primary-purple);
    color: var(--white);
    padding: 0.3em 0.8em;
    border-radius: 8px;
    font-size: 0.8em;
    font-weight: 500;
}

/* Title Section */
.title-section {
    text-align: left;
    margin-bottom: 0.8in;
}

.certificate-title {
    font-size: 2.4em;
    font-weight: 600;
    color: var(--primary-purple);
    margin: 0;
    line-height: 1.1;
}

/* Content Section */
.content-section {
    flex: 1;
    display: flex;
    flex-direction: column;
    justify-content: center;
}

.proudly-text {
    font-size: 1.1em;
    color: var(--text-light);
    margin-bottom: 0.6em;
    font-weight: 400;
}

.recipient-name {
    font-size: 3.2em;
    font-weight: 700;
    color: var(--primary-purple);
    margin: 0.3em 0 0.8em 0;
    line-height: 1;
}

.completion-statement {
    margin-bottom: 1.2em;
    font-size: 1.2em;
    line-height: 1.4;
}

.completion-text {
    color: var(--text-dark);
    font-weight: 400;
}

.course-name {
    font-weight: 700;
    color: var(--primary-purple);
}

/* Metrics Section */
.metrics-section {
    display: flex;
    gap: 1.5em;
    margin: 1em 0;
    flex-wrap: wrap;
}

.metric-item {
    background: var(--metric-bg);
    padding: 0.4em 0.8em;
    border-radius: 12px;
    text-align: center;
    min-width: 120px;
}

.metric-label {
    font-size: 0.8em;
    color: var(--text-light);
    font-weight: 500;
    margin-bottom: 0.2em;
}

.metric-value {
    font-size: 1em;
    font-weight: 700;
    color: var(--primary-purple);
}

/* Footer Section */
.certificate-footer {
    margin-top: auto;
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    padding-top: 0.6in;
}

/* Signatures */
.signatures-section {
    display: flex;
    gap: 2em;
    flex: 1;
}

.signature-block {
    text-align: center;
}

.signature-line {
    width: 140px;
    height: 2px;
    background: var(--text-light);
    margin-bottom: 0.4em;
}

.signature-name {
    font-size: 0.9em;
    font-weight: 600;
    color: var(--text-dark);
    margin-bottom: 0.2em;
}

.signature-title {
    font-size: 0.8em;
    color: var(--text-light);
    font-weight: 400;
}

/* Accreditation Section */
.accreditation-section {
    display: flex;
    align-items: flex-end;
    gap: 1em;
}

.accreditation-badge {
    display: flex;
    align-items: center;
    gap: 0.5em;
    background: var(--white);
    border: 2px solid var(--border-light);
    border-radius: 8px;
    padding: 0.5em;
}

.badge-icon {
    font-size: 1.5em;
}

.badge-text {
    text-align: left;
}

.association-name {
    font-size: 0.8em;
    font-weight: 600;
    color: var(--primary-purple);
    margin-bottom: 0.1em;
}

.accreditation-text {
    font-size: 0.6em;
    color: var(--text-light);
    font-weight: 500;
    line-height: 1.1;
    text-align: center;
}

.qr-section {
    border: 2px solid var(--border-light);
    border-radius: 8px;
    padding: 0.3em;
    background: var(--white);
}

.qr-code {
    width: 60px;
    height: 60px;
    display: block;
}

/* Print optimization */
@media print {
    body {
        width: 100%;
        height: 100vh;
        margin: 0;
        padding: 0;
    }

    .certificate-container {
        border-radius: 0;
        box-shadow: none;
        width: 100%;
        height: 100%;
        border-width: 6px;
    }
}

/* Responsive adjustments */
@media screen and (max-width: 1200px) {
    .certificate-container {
        padding: 0.4in;
    }

    .certificate-title {
        font-size: 2em;
    }

    .recipient-name {
        font-size: 2.5em;
    }

    .metrics-section {
        gap: 1em;
    }

    .signatures-section {
        flex-direction: column;
        gap: 1em;
        align-items: center;
    }

    .accreditation-section {
        flex-direction: column;
        align-items: center;
        gap: 0.5em;
    }
}
"""

# ---------------------------------------------------------------------------------------
# Professional Program Certificate Template
# ---------------------------------------------------------------------------------------

CERTIFICADO_PROGRAMA_PROFESIONAL_TITULO = "Programa Profesional"

CERTIFICADO_PROGRAMA_PROFESIONAL_DESCRIPCION = (
    "Certificado de programa profesional con diseño corporativo moderno y elementos de verificación avanzados."
)

CERTIFICADO_PROGRAMA_PROFESIONAL_HTML = """
<!doctype html>
<html lang="es">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Certificado de Programa Profesional</title>
    </head>
    <body>
        <div class="certificate-container">
            <!-- Header Section -->
            <header class="certificate-header">
                <div class="brand-section">
                    <div class="brand-logo">🏆</div>
                    <div class="provider-info">
                        <div class="provider-text">Your CE Provider Logo</div>
                    </div>
                </div>
            </header>

            <!-- Title Section -->
            <div class="title-section">
                <h1 class="certificate-title">Certificate of Professional Program</h1>
            </div>

            <!-- Content Section -->
            <main class="content-section">
                <div class="proudly-text">Proudly presented to</div>

                <div class="recipient-name">{{ usuario.nombre }} {{ usuario.apellido }}</div>

                <div class="completion-statement">
                    <span class="completion-text">Successfully completed the comprehensive program</span>
                    <span class="program-name">{{ programa.nombre }}</span>
                </div>

                <!-- Program Description -->
                <div class="program-description">
                    {{ programa.descripcion or 'A comprehensive professional development program designed to enhance skills and knowledge in the specified field of study.' }}
                </div>

                <!-- Courses Summary -->
                <div class="courses-summary">
                    <div class="courses-header">Including completion of the following courses:</div>
                    <div class="courses-grid">
                        {% set cursos_completados = certificacion_programa.get_cursos_completados() %}
                        {% for curso_codigo in cursos_completados[:6] %}
                            {% set curso = database.session.execute(database.select(Curso).filter_by(codigo=curso_codigo)).scalar_one_or_none() %}
                            {% if curso %}
                            <div class="course-item">{{ curso.nombre }}</div>
                            {% endif %}
                        {% endfor %}
                        {% if cursos_completados|length > 6 %}
                        <div class="course-item more-courses">+{{ cursos_completados|length - 6 }} more courses</div>
                        {% endif %}
                    </div>
                </div>

                <!-- Metrics Section -->
                <div class="metrics-section">
                    <div class="metric-item">
                        <div class="metric-label">Total Credits:</div>
                        <div class="metric-value">{{ cursos_completados|length * 4.6 }}</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-label">Certificate ID:</div>
                        <div class="metric-value">{{ certificacion_programa.id }}</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-label">Certified on:</div>
                        <div class="metric-value">{{ certificacion_programa.fecha.strftime('%d.%m.%Y') }}</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-label">Expiry Date:</div>
                        <div class="metric-value">{{ (certificacion_programa.fecha.replace(year=certificacion_programa.fecha.year + 3)).strftime('%d.%m.%Y') }}</div>
                    </div>
                </div>
            </main>

            <!-- Footer Section -->
            <footer class="certificate-footer">
                <div class="signatures-section">
                    <div class="signature-block">
                        <div class="signature-line"></div>
                        <div class="signature-name">Dr. Sarah Johnson</div>
                        <div class="signature-title">Academic Director</div>
                    </div>
                    <div class="signature-block">
                        <div class="signature-line"></div>
                        <div class="signature-name">Mark Allford</div>
                        <div class="signature-title">Program Director</div>
                    </div>
                </div>

                <!-- Accreditation and QR -->
                <div class="accreditation-section">
                    <div class="accreditation-badge">
                        <div class="badge-icon">🎖️</div>
                        <div class="badge-text">
                            <div class="association-name">Professional Association</div>
                            <div class="accreditation-text">ACCREDITED<br>PROGRAM<br>PROVIDER</div>
                        </div>
                    </div>
                    <div class="qr-section">
                        <img src="{{ url_for('certificate.certificacion_programa_qr', certificate_id=certificacion_programa.id) }}"
                             alt="QR Code"
                             class="qr-code">
                    </div>
                </div>
            </footer>
        </div>
    </body>
</html>
"""

CERTIFICADO_PROGRAMA_PROFESIONAL_CSS = """
/* Letter size landscape page setup for PDF generation */
@page {
    size: letter landscape; /* 11in x 8.5in landscape */
    margin: 0.3in;
}

/* Color scheme for program certificates - darker, more prestigious */
:root {
    --primary-navy: #1e2a78;
    --accent-navy: #2d3a9f;
    --light-navy: #4a5bc4;
    --gold-accent: #d4af37;
    --background-light: #f8f9fd;
    --text-dark: #1a1a2e;
    --text-light: #4a4a6a;
    --white: #ffffff;
    --border-light: #d0d8f0;
    --metric-bg: #e6eaff;
    --course-bg: #f0f3ff;
}

/* Base styles */
body {
    width: 10.5in;
    height: 8in;
    margin: 0;
    padding: 0;
    font-family: "Arial", "Helvetica", sans-serif;
    background: var(--background-light);
    color: var(--text-dark);
    box-sizing: border-box;
}

/* Certificate container */
.certificate-container {
    width: 100%;
    height: 100%;
    background: var(--white);
    border-radius: 20px;
    padding: 0.5in;
    position: relative;
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
    border: 8px solid var(--primary-navy);
    box-shadow: 0 4px 20px rgba(30, 42, 120, 0.15);
}

/* Header Section */
.certificate-header {
    display: flex;
    justify-content: flex-end;
    align-items: flex-start;
    margin-bottom: 0.3in;
}

.brand-section {
    display: flex;
    align-items: center;
    gap: 0.5em;
}

.brand-logo {
    width: 40px;
    height: 40px;
    background: var(--primary-navy);
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.2em;
    color: var(--white);
}

.provider-info {
    background: var(--primary-navy);
    color: var(--white);
    padding: 0.3em 0.8em;
    border-radius: 8px;
    font-size: 0.8em;
    font-weight: 500;
}

/* Title Section */
.title-section {
    text-align: left;
    margin-bottom: 0.6in;
}

.certificate-title {
    font-size: 2.2em;
    font-weight: 600;
    color: var(--primary-navy);
    margin: 0;
    line-height: 1.1;
}

/* Content Section */
.content-section {
    flex: 1;
    display: flex;
    flex-direction: column;
    justify-content: center;
}

.proudly-text {
    font-size: 1em;
    color: var(--text-light);
    margin-bottom: 0.5em;
    font-weight: 400;
}

.recipient-name {
    font-size: 2.8em;
    font-weight: 700;
    color: var(--primary-navy);
    margin: 0.2em 0 0.6em 0;
    line-height: 1;
}

.completion-statement {
    margin-bottom: 0.8em;
    font-size: 1.1em;
    line-height: 1.4;
}

.completion-text {
    color: var(--text-dark);
    font-weight: 400;
}

.program-name {
    font-weight: 700;
    color: var(--primary-navy);
}

/* Program Description */
.program-description {
    font-size: 0.9em;
    color: var(--text-light);
    margin-bottom: 0.8em;
    line-height: 1.4;
    font-style: italic;
}

/* Courses Summary */
.courses-summary {
    margin-bottom: 1em;
}

.courses-header {
    font-size: 0.9em;
    color: var(--text-dark);
    font-weight: 600;
    margin-bottom: 0.5em;
}

.courses-grid {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 0.3em;
    margin-bottom: 0.8em;
}

.course-item {
    background: var(--course-bg);
    padding: 0.3em 0.6em;
    border-radius: 6px;
    font-size: 0.7em;
    color: var(--text-dark);
    text-align: center;
    font-weight: 500;
    border: 1px solid var(--border-light);
}

.course-item.more-courses {
    background: var(--gold-accent);
    color: var(--white);
    font-weight: 600;
}

/* Metrics Section */
.metrics-section {
    display: flex;
    gap: 1.2em;
    margin: 0.8em 0;
    flex-wrap: wrap;
}

.metric-item {
    background: var(--metric-bg);
    padding: 0.4em 0.8em;
    border-radius: 12px;
    text-align: center;
    min-width: 110px;
    border: 1px solid var(--border-light);
}

.metric-label {
    font-size: 0.75em;
    color: var(--text-light);
    font-weight: 500;
    margin-bottom: 0.2em;
}

.metric-value {
    font-size: 0.95em;
    font-weight: 700;
    color: var(--primary-navy);
}

/* Footer Section */
.certificate-footer {
    margin-top: auto;
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    padding-top: 0.5in;
}

/* Signatures */
.signatures-section {
    display: flex;
    gap: 2em;
    flex: 1;
}

.signature-block {
    text-align: center;
}

.signature-line {
    width: 140px;
    height: 2px;
    background: var(--text-light);
    margin-bottom: 0.4em;
}

.signature-name {
    font-size: 0.9em;
    font-weight: 600;
    color: var(--text-dark);
    margin-bottom: 0.2em;
}

.signature-title {
    font-size: 0.8em;
    color: var(--text-light);
    font-weight: 400;
}

/* Accreditation Section */
.accreditation-section {
    display: flex;
    align-items: flex-end;
    gap: 1em;
}

.accreditation-badge {
    display: flex;
    align-items: center;
    gap: 0.5em;
    background: var(--white);
    border: 2px solid var(--gold-accent);
    border-radius: 8px;
    padding: 0.5em;
}

.badge-icon {
    font-size: 1.5em;
}

.badge-text {
    text-align: left;
}

.association-name {
    font-size: 0.8em;
    font-weight: 600;
    color: var(--primary-navy);
    margin-bottom: 0.1em;
}

.accreditation-text {
    font-size: 0.6em;
    color: var(--text-light);
    font-weight: 500;
    line-height: 1.1;
    text-align: center;
}

.qr-section {
    border: 2px solid var(--border-light);
    border-radius: 8px;
    padding: 0.3em;
    background: var(--white);
}

.qr-code {
    width: 60px;
    height: 60px;
    display: block;
}

/* Print optimization */
@media print {
    body {
        width: 100%;
        height: 100vh;
        margin: 0;
        padding: 0;
    }

    .certificate-container {
        border-radius: 0;
        box-shadow: none;
        width: 100%;
        height: 100%;
        border-width: 6px;
    }
}

/* Responsive adjustments */
@media screen and (max-width: 1200px) {
    .certificate-container {
        padding: 0.4in;
    }

    .certificate-title {
        font-size: 1.8em;
    }

    .recipient-name {
        font-size: 2.2em;
    }

    .courses-grid {
        grid-template-columns: 1fr 1fr;
    }

    .metrics-section {
        gap: 0.8em;
    }

    .signatures-section {
        flex-direction: column;
        gap: 1em;
        align-items: center;
    }

    .accreditation-section {
        flex-direction: column;
        align-items: center;
        gap: 0.5em;
    }
}
"""

# ---------------------------------------------------------------------------------------
# Program Certificate Template
# ---------------------------------------------------------------------------------------

CERTIFICADO_PROGRAMA_TITULO = "Programa"

CERTIFICADO_PROGRAMA_DESCRIPCION = "Certificado de finalización de programa con lista de cursos completados."

CERTIFICADO_PROGRAMA_HTML = """
<!doctype html>
<html lang="es">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Certificado de Programa</title>
    </head>
    <body>
        <div class="certificate-container">
            <!-- Header -->
            <header class="certificate-header">
                <div class="institution-logo">
                    <div class="logo-placeholder">🏆</div>
                </div>
                <div class="institution-info">
                    <h1 class="institution-name">NOW Learning Management System</h1>
                    <p class="institution-subtitle">Centro de Excelencia en Educación</p>
                </div>
                <div class="certificate-seal">
                    <div class="seal-inner">PROG</div>
                </div>
            </header>

            <!-- Certificate Title -->
            <div class="certificate-title-section">
                <h2 class="certificate-title">CERTIFICADO</h2>
                <p class="certificate-subtitle">DE FINALIZACIÓN DE PROGRAMA</p>
            </div>

            <!-- Main Content -->
            <main class="certificate-content">
                <div class="achievement-statement">
                    <p class="certify-text">Se certifica que</p>

                    <!-- Recipient Name -->
                    <div class="recipient-section">
                        <h3 class="recipient-name">{{ usuario.nombre }} {{ usuario.apellido }}</h3>
                    </div>

                    <!-- Program Information -->
                    <div class="program-section">
                        <p class="completion-text">ha completado exitosamente el programa</p>
                        <h4 class="program-title">{{ programa.nombre }}</h4>
                        <p class="program-description">{{ programa.descripcion }}</p>
                    </div>

                    <!-- Courses List -->
                    <div class="courses-section">
                        <p class="courses-header">completando los siguientes cursos:</p>
                        <div class="courses-list">
                            {% set cursos_completados = certificacion_programa.get_cursos_completados() %}
                            {% for curso_codigo in cursos_completados %}
                                {% set curso = database.session.execute(database.select(Curso).filter_by(codigo=curso_codigo)).scalar_one_or_none() %}
                                {% if curso %}
                                <div class="course-item">
                                    <span class="course-bullet">•</span>
                                    <span class="course-name">{{ curso.nombre }}</span>
                                </div>
                                {% endif %}
                            {% endfor %}
                        </div>
                    </div>

                    <!-- Completion Date -->
                    <div class="completion-section">
                        <p class="completion-date">Fecha de Finalización: {{ certificacion_programa.fecha.strftime('%d de %B de %Y') }}</p>
                    </div>
                </div>
            </main>

            <!-- Footer -->
            <footer class="certificate-footer">
                <div class="signatures-section">
                    <div class="signature-block">
                        <div class="signature-line"></div>
                        <p class="signature-title">Director Académico</p>
                        <p class="signature-date">{{ certificacion_programa.fecha.strftime('%d/%m/%Y') }}</p>
                    </div>

                    <div class="validation-section">
                        <div class="qr-code-container">
                            <img src="{{ url_for('certificate.certificacion_programa_qr', certificate_id=certificacion_programa.id) }}"
                                 alt="Código QR para verificación"
                                 class="qr-code">
                            <p class="qr-label">Escanear para verificar</p>
                        </div>
                    </div>
                </div>

                <!-- Certificate Metadata -->
                <div class="certificate-metadata">
                    <div class="metadata-item">
                        <span class="metadata-label">ID Certificado:</span>
                        <span class="metadata-value">{{ certificacion_programa.id }}</span>
                    </div>
                    <div class="metadata-item">
                        <span class="metadata-label">Fecha de Emisión:</span>
                        <span class="metadata-value">{{ certificacion_programa.fecha.strftime('%Y-%m-%d') }}</span>
                    </div>
                </div>
            </footer>

            <!-- Security Watermark -->
            <div class="security-watermark" aria-hidden="true">COMPLETADO</div>
        </div>
    </body>
</html>
"""

CERTIFICADO_PROGRAMA_CSS = """
/* Letter size page setup for PDF generation */
@page {
    size: letter; /* 8.5in x 11in portrait */
    margin: 0.5in;
}

/* CSS Variables for theme consistency */
:root {
    --primary-color: #2c3e50;
    --secondary-color: #3498db;
    --accent-color: #f39c12;
    --success-color: #27ae60;
    --text-color: #2c3e50;
    --light-text: #7f8c8d;
    --border-color: #bdc3c7;
    --background: #ffffff;
    --light-background: #f8f9fa;
    --program-primary: #8e44ad;
    --program-accent: #e67e22;
}

/* Base styles */
body {
    width: 7.5in;
    height: 10in;
    margin: 0;
    padding: 0;
    font-family: "Georgia", "Times New Roman", serif;
    background: var(--background);
    color: var(--text-color);
    box-sizing: border-box;
    line-height: 1.4;
}

/* Certificate container */
.certificate-container {
    width: 100%;
    height: 100%;
    padding: 0.5in;
    border: 4px solid var(--program-primary);
    border-radius: 8px;
    background: var(--background);
    position: relative;
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
    box-shadow: inset 0 0 0 2px var(--program-accent);
}

/* Header */
.certificate-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 0.6in;
    padding-bottom: 0.3in;
    border-bottom: 2px solid var(--border-color);
}

.logo-placeholder {
    width: 60px;
    height: 60px;
    background: linear-gradient(135deg, var(--program-primary), var(--program-accent));
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.8em;
    color: white;
    font-weight: bold;
}

.institution-info {
    flex: 1;
    text-align: center;
    margin: 0 1em;
}

.institution-name {
    font-size: 1.1em;
    font-weight: bold;
    color: var(--program-primary);
    margin: 0 0 0.2em 0;
    letter-spacing: 0.05em;
}

.institution-subtitle {
    font-size: 0.8em;
    color: var(--light-text);
    font-style: italic;
    margin: 0;
}

.certificate-seal {
    width: 60px;
    height: 60px;
    border: 3px solid var(--program-accent);
    border-radius: 50%;
    background: radial-gradient(circle, var(--light-background) 0%, var(--background) 100%);
    display: flex;
    align-items: center;
    justify-content: center;
}

.seal-inner {
    font-size: 0.7em;
    font-weight: bold;
    color: var(--program-accent);
    letter-spacing: 0.05em;
}

/* Certificate Title */
.certificate-title-section {
    text-align: center;
    margin-bottom: 0.6in;
}

.certificate-title {
    font-size: 2.2em;
    font-weight: bold;
    color: var(--program-primary);
    letter-spacing: 0.2em;
    margin: 0 0 0.2em 0;
    text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
}

.certificate-subtitle {
    font-size: 1em;
    color: var(--program-accent);
    letter-spacing: 0.1em;
    font-weight: normal;
    margin: 0;
}

/* Main Content */
.certificate-content {
    flex: 1;
    text-align: center;
}

.certify-text {
    font-size: 1em;
    color: var(--text-color);
    font-style: italic;
    margin: 0 0 0.6em 0;
}

/* Recipient */
.recipient-section {
    margin: 0.6em 0;
}

.recipient-name {
    font-size: 1.8em;
    font-weight: bold;
    color: var(--program-primary);
    margin: 0 0 0.3em 0;
    border-bottom: 2px solid var(--program-accent);
    padding-bottom: 0.2em;
    display: inline-block;
    line-height: 1.2;
}

/* Program Information */
.program-section {
    margin: 0.8em 0;
}

.completion-text {
    font-size: 1em;
    color: var(--text-color);
    margin: 0 0 0.5em 0;
}

.program-title {
    font-size: 1.4em;
    font-weight: bold;
    color: var(--program-primary);
    margin: 0.5em 0;
    line-height: 1.3;
    font-style: italic;
}

.program-description {
    font-size: 0.9em;
    color: var(--light-text);
    margin: 0.3em 0;
    font-style: italic;
}

/* Courses List */
.courses-section {
    margin: 0.8em 0;
    background: var(--light-background);
    padding: 0.8em;
    border-radius: 8px;
    border: 1px solid var(--border-color);
}

.courses-header {
    font-size: 0.9em;
    color: var(--text-color);
    margin: 0 0 0.5em 0;
    font-weight: bold;
}

.courses-list {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.3em;
    text-align: left;
    max-width: 5in;
    margin: 0 auto;
}

.course-item {
    display: flex;
    align-items: flex-start;
    font-size: 0.8em;
    color: var(--text-color);
    padding: 0.2em 0;
}

.course-bullet {
    color: var(--program-accent);
    font-weight: bold;
    margin-right: 0.5em;
    font-size: 1.2em;
}

.course-name {
    line-height: 1.3;
}

/* Completion Date */
.completion-section {
    margin: 0.8em 0;
}

.completion-date {
    font-size: 0.9em;
    color: var(--success-color);
    margin: 0;
    font-weight: 600;
}

/* Footer */
.certificate-footer {
    margin-top: auto;
    padding-top: 0.4in;
    border-top: 1px solid var(--border-color);
}

/* Signatures & Validation */
.signatures-section {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    margin-bottom: 0.6em;
}

.signature-block {
    flex: 1;
    text-align: left;
}

.signature-line {
    width: 160px;
    height: 1px;
    background: var(--border-color);
    margin-bottom: 0.3em;
}

.signature-title {
    font-size: 0.8em;
    font-weight: bold;
    color: var(--text-color);
    margin: 0.2em 0;
}

.signature-date {
    font-size: 0.7em;
    color: var(--light-text);
    margin: 0;
}

/* QR Code Validation */
.validation-section {
    flex: 0 0 auto;
    text-align: center;
}

.qr-code-container {
    border: 1px solid var(--border-color);
    padding: 8px;
    border-radius: 4px;
    background: var(--background);
}

.qr-code {
    width: 50px;
    height: 50px;
    display: block;
}

.qr-label {
    font-size: 0.6em;
    color: var(--light-text);
    margin: 0.3em 0 0 0;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* Certificate Metadata */
.certificate-metadata {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.7em;
    color: var(--light-text);
    padding: 0.3em 0;
    border-top: 1px solid var(--border-color);
    flex-wrap: wrap;
    gap: 0.5em;
}

.metadata-item {
    flex: 1;
    min-width: 150px;
}

.metadata-label {
    font-weight: 600;
}

.metadata-value {
    margin-left: 0.3em;
}

/* Security Watermark */
.security-watermark {
    position: absolute;
    top: 45%;
    left: 35%;
    font-size: 2.5em;
    color: rgba(142, 68, 173, 0.05);
    font-weight: bold;
    letter-spacing: 0.2em;
    transform: rotate(-25deg);
    pointer-events: none;
    z-index: 0;
    font-family: "Arial Black", sans-serif;
}

/* Ensure content is above watermark */
.certificate-header,
.certificate-title-section,
.certificate-content,
.certificate-footer {
    position: relative;
    z-index: 1;
}

/* Responsive design for small courses lists */
@media (max-width: 5in) {
    .courses-list {
        grid-template-columns: 1fr;
    }
}
"""

CERTIFICADOS = (
    (
        CERTIFICADO_DEFAULT_TITULO,
        CERTIFICADO_DEFAULT_DESCRIPCION,
        CERTIFICADO_DEFAULT_HTML,
        CERTIFICADO_DEFAULT_CSS,
        "default",
        "course",
    ),
    (
        CERTIFICADO_HORIZONTAL_TITULO,
        CERTIFICADO_HORIZONTAL_DESCRIPCION,
        CERTIFICADO_HORIZONTAL_HTML,
        CERTIFICADO_HORIZONTAL_CSS,
        "horizontal",
        "course",
    ),
    (
        CERTIFICADO_VERTICAL_TITULO,
        CERTIFICADO_VERTICAL_DESCRIPCION,
        CERTIFICADO_VERTICAL_HTML,
        CERTIFICADO_VERTICAL_CSS,
        "vertical",
        "course",
    ),
    (
        CERTIFICADO_ELEGANTE_TITULO,
        CERTIFICADO_ELEGANTE_DESCRIPCION,
        CERTIFICADO_ELEGANTE_HTML,
        CERTIFICADO_ELEGANTE_CSS,
        "elegante",
        "course",
    ),
    (
        CERTIFICADO_MODERNO_TITULO,
        CERTIFICADO_MODERNO_DESCRIPCION,
        CERTIFICADO_MODERNO_HTML,
        CERTIFICADO_MODERNO_CSS,
        "moderno",
        "course",
    ),
    (
        CERTIFICADO_CLASICO_TITULO,
        CERTIFICADO_CLASICO_DESCRIPCION,
        CERTIFICADO_CLASICO_HTML,
        CERTIFICADO_CLASICO_CSS,
        "clasico",
        "course",
    ),
    (
        CERTIFICADO_CORPORATIVO_TITULO,
        CERTIFICADO_CORPORATIVO_DESCRIPCION,
        CERTIFICADO_CORPORATIVO_HTML,
        CERTIFICADO_CORPORATIVO_CSS,
        "corporativo",
        "course",
    ),
    (
        CERTIFICADO_PROFESIONAL_TITULO,
        CERTIFICADO_PROFESIONAL_DESCRIPCION,
        CERTIFICADO_PROFESIONAL_HTML,
        CERTIFICADO_PROFESIONAL_CSS,
        "profesional",
        "course",
    ),
    (
        CERTIFICADO_PROGRAMA_TITULO,
        CERTIFICADO_PROGRAMA_DESCRIPCION,
        CERTIFICADO_PROGRAMA_HTML,
        CERTIFICADO_PROGRAMA_CSS,
        "programa",
        "program",
    ),
    (
        CERTIFICADO_PROGRAMA_PROFESIONAL_TITULO,
        CERTIFICADO_PROGRAMA_PROFESIONAL_DESCRIPCION,
        CERTIFICADO_PROGRAMA_PROFESIONAL_HTML,
        CERTIFICADO_PROGRAMA_PROFESIONAL_CSS,
        "programa_profesional",
        "program",
    ),
)
