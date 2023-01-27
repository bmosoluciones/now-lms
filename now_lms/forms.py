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

"""Definición de formularios."""
# Libreria standar:

# Librerias de terceros:
from flask_mde import MdeField
from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    DecimalField,
    DateField,
    TimeField,
    IntegerField,
    PasswordField,
    SelectField,
    StringField,
    SubmitField,
)
from wtforms.validators import DataRequired

# pylint: disable=R0903

# Recursos locales:


# < --------------------------------------------------------------------------------------------- >
# Definición de formularios


class LoginForm(FlaskForm):
    """Formulario de inicio de sesión."""

    usuario = StringField(validators=[DataRequired()])
    acceso = PasswordField(validators=[DataRequired()])
    inicio_sesion = SubmitField()


class LogonForm(FlaskForm):
    """Formulario para crear un nuevo usuario."""

    usuario = StringField(validators=[DataRequired()])
    acceso = PasswordField(validators=[DataRequired()])
    nombre = StringField(validators=[DataRequired()])
    apellido = StringField(validators=[DataRequired()])
    correo_electronico = StringField(validators=[DataRequired()])


class BaseForm(FlaskForm):
    """Campos comunes a la mayoria de los campos."""

    nombre = StringField(validators=[DataRequired()])
    descripcion = StringField(validators=[DataRequired()])


class CurseForm(BaseForm):
    """Formulario para crear un nuevo curso."""

    codigo = StringField(validators=[DataRequired()])
    publico = BooleanField(validators=[])
    auditable = BooleanField(validators=[])
    certificado = BooleanField(validators=[])
    precio = DecimalField(validators=[])
    capacidad = IntegerField(validators=[])
    fecha_inicio = DateField(validators=[])
    fecha_fin = DateField(validators=[])
    duracion = IntegerField(validators=[])
    nivel = SelectField("User", choices=[(0, "Introductorio"), (1, "Principiante"), (2, "Intermedio"), (2, "Avanzado")])


class CursoRecursoForm(FlaskForm):
    """Formulario para crear un nuevo recurso."""

    tipo = SelectField(
        "Tipo",
        choices=[("link", "Vinculo"), ("youtube", "Vídeo en YouTube"), ("file", "Archivo"), ("text", "Texto")],
    )


class CursoSeccionForm(BaseForm):
    """Formulario para crear una nueva sección."""


class CursoRecursoVideoYoutube(BaseForm):
    """Formulario para un nuevo recurso Youtube."""

    youtube_url = StringField(validators=[DataRequired()])


class CursoRecursoArchivoPDF(BaseForm):
    """Formulario para un nuevo recurso PDF."""


class CursoRecursoArchivoAudio(BaseForm):
    """Formulario para un nuevo recurso de audio."""


class CursoRecursoArchivoImagen(BaseForm):
    """Formulario para un nuevo recurso de audio."""


class CursoRecursoArchivoText(BaseForm):
    """Formulario para un nuevo recurso de audio."""

    editor = MdeField()


class CursoRecursoExternalCode(BaseForm):
    """Formulario para insertar un recurso HTML"""

    html_externo = StringField(validators=[DataRequired()])


class CursoRecursoExternalLink(BaseForm):
    """Formulario para insertar un recurso HTML"""

    url = StringField(validators=[DataRequired()])


class CursoRecursoMeet(BaseForm):
    """Formulario para insertar un Meet"""

    fecha = DateField(validators=[])
    hora = TimeField(validators=[])
    url = StringField(validators=[DataRequired()])
    notes = SelectField(
        "Tema",
        choices=[
            ("beige", "Beige"),
            ("black", "Black"),
            ("blood", "Blood"),
            ("league", "League"),
            ("moon", "Moon"),
            ("night", "Night"),
            ("serif", "Serif"),
            ("simple", "Simple"),
            ("sky", "Sky"),
            ("solarized", "Solarized"),
            ("white", "White"),
        ],
    )


class CursoRecursoSlides(BaseForm):
    """Formulario para insertar un Meet"""

    notes = SelectField(
        "Plataforma", choices=[("zoom", "Zoom"), ("teams", "MS Teams"), ("meet", "Google Meet"), ("otros", "Otros")]
    )
