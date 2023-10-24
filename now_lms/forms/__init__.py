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
# ---------------------------------------------------------------------------------------
# Libreria estandar
# ---------------------------------------------------------------------------------------


# ---------------------------------------------------------------------------------------
# Librerias de terceros
# ---------------------------------------------------------------------------------------
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
    TextAreaField,
)
from wtforms.validators import DataRequired
from wtforms.widgets import ColorInput

# ---------------------------------------------------------------------------------------
# Recursos locales
# ---------------------------------------------------------------------------------------
# pylint: disable=R0903


# < --------------------------------------------------------------------------------------------- >
# Definición de formularios

MONEDAS = [
    ("C$", "Córdobas Oro"),
    ("USD", "Dólares"),
]


class ConfigForm(FlaskForm):
    """Formulario para editar la configuración del sistema."""

    titulo = StringField(validators=[DataRequired()])
    descripcion = StringField(validators=[DataRequired()])
    modo = SelectField(
        "Modo",
        choices=[
            ("mooc", "Cursos Masivos en Linea"),
            ("school", "Escuela"),
            ("training", "Corporativo"),
        ],
    )
    # Formas de pago.
    stripe = BooleanField(validators=[])
    paypal = BooleanField(validators=[])
    # Configuración de Stripe
    stripe_secret = StringField(validators=[])
    stripe_public = StringField(validators=[])
    moneda = SelectField(
        "Moneda",
        choices=MONEDAS,
    )


class ThemeForm(FlaskForm):
    """Formulario para editar el tema del sistema."""

    style = SelectField(
        "Estilo",
        choices=[
            ("dark", "Oscuro"),
            ("light", "Claro"),
            # ("transparent", "Transparente"),
        ],
    )


class LoginForm(FlaskForm):
    """Formulario de inicio de sesión."""

    usuario = StringField(validators=[DataRequired()])
    acceso = PasswordField(validators=[DataRequired()])
    inicio_sesion = SubmitField()


class MailForm(FlaskForm):
    """Formulario de configuración de correo electronico."""

    email = BooleanField(validators=[])
    mail_server = StringField(validators=[DataRequired()])
    mail_port = StringField(validators=[DataRequired()])
    mail_use_tls = BooleanField(validators=[])
    mail_use_ssl = BooleanField(validators=[])
    mail_username = StringField(validators=[DataRequired()])
    mail_password = StringField(validators=[DataRequired()])


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
    descripcion = MdeField(validators=[DataRequired()])


class GrupoForm(BaseForm):
    """Formulario para crear un grupo de usuarios."""


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
    nivel = SelectField("User", choices=[(0, "Introductorio"), (1, "Principiante"), (2, "Intermedio"), (3, "Avanzado")])
    promocionado = BooleanField(validators=[])


class CursoSeccionForm(BaseForm):
    """Formulario para crear una nueva sección."""


class CursoRecursoForm(BaseForm):
    """Base para los recursos del curso."""

    requerido = SelectField("Requerido", choices=[(1, "Requerido"), (2, "Opcinal"), (3, "Alternativo")])


class CursoRecursoVideoYoutube(CursoRecursoForm):
    """Formulario para un nuevo recurso Youtube."""

    youtube_url = StringField(validators=[DataRequired()])


class CursoRecursoArchivoPDF(CursoRecursoForm):
    """Formulario para un nuevo recurso PDF."""


class CursoRecursoArchivoAudio(CursoRecursoForm):
    """Formulario para un nuevo recurso de audio."""


class CursoRecursoArchivoImagen(CursoRecursoForm):
    """Formulario para un nuevo recurso de audio."""


class CursoRecursoArchivoText(CursoRecursoForm):
    """Formulario para un nuevo recurso de audio."""

    editor = MdeField()


class CursoRecursoExternalCode(CursoRecursoForm):
    """Formulario para insertar un recurso HTML"""

    html_externo = StringField(validators=[DataRequired()])


class CursoRecursoExternalLink(CursoRecursoForm):
    """Formulario para insertar un recurso HTML"""

    url = StringField(validators=[DataRequired()])


class CursoRecursoSlides(CursoRecursoForm):
    """Formulario para insertar un SlideShow."""

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


class CursoRecursoMeet(CursoRecursoForm):
    """Formulario para insertar un Meet"""

    fecha = DateField(validators=[])
    hora_inicio = TimeField(validators=[])
    hora_fin = TimeField(validators=[])
    url = StringField(validators=[DataRequired()])
    notes = SelectField(
        "Plataforma",
        choices=[
            ("none", "Seleccione"),
            ("bluejeans", "BlueJeans"),
            ("zoom", "Zoom"),
            ("teams", "MS Teams"),
            ("meet", "Google Meet"),
            ("zoho", "Zoho Backstage"),
            ("click", "ClickMeeting"),
            ("goto", "GoTo Meeting"),
            ("webex", "Webex"),
            ("intermedia", "Intermedia AnyMeeting"),
            ("whatsapp", "WhatsApp"),
            ("otros", "Otros"),
        ],
    )


class CategoriaForm(BaseForm):
    """Formulario para crear una categoria"""


class EtiquetaForm(BaseForm):
    """Formulario para crear una etiqueta"""

    color = StringField(widget=ColorInput())


class ProgramaForm(BaseForm):
    """Formulario para crear un programa."""

    codigo = StringField(validators=[DataRequired()])
    precio = DecimalField()
    publico = BooleanField(validators=[])
    estado = SelectField(
        "Estado",
        choices=[
            ("draft", "Borrador"),
            ("open", "Abierto"),
            ("closed", "Cerrado"),
        ],
    )
    promocionado = BooleanField(validators=[])


class RecursoForm(BaseForm):
    """Formulario para crear un recurso."""

    codigo = StringField(validators=[DataRequired()])
    precio = DecimalField()
    publico = BooleanField(validators=[])
    promocionado = BooleanField(validators=[])
    tipo = SelectField(
        "Tipo",
        choices=[
            ("cheat_sheet", "Hoja de Guía"),
            ("ebook", "Libro Electronico"),
            ("template", "Plantilla"),
        ],
    )


class UserForm(FlaskForm):
    """Formulario para el perfil de usuario."""

    nombre = StringField(validators=[])
    apellido = StringField(validators=[])
    correo_electronico = StringField(validators=[])
    url = StringField(validators=[])
    linkedin = StringField(validators=[])
    facebook = StringField(validators=[])
    twitter = StringField(validators=[])
    github = StringField(validators=[])
    youtube = StringField(validators=[])
    genero = SelectField(
        "Genero",
        choices=[
            ("none", "No especificado"),
            ("other", "Otros"),
            ("male", "Masculino"),
            ("female", "Femenino"),
        ],
    )
    titulo = SelectField(
        "Titulo",
        choices=[
            ("", "No especificado"),
            ("ing", "Ingenioero"),
            ("lic", "Licenciado"),
            ("dr", "Doctor"),
        ],
    )
    nacimiento = DateField()
    bio = TextAreaField()
