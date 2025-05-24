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

"""Definición de formularios."""
# ---------------------------------------------------------------------------------------
# Libreria estandar
# ---------------------------------------------------------------------------------------
from os import listdir
from os.path import join

# ---------------------------------------------------------------------------------------
# Librerias de terceros
# ---------------------------------------------------------------------------------------
from flask_mde import MdeField
from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    DateField,
    DecimalField,
    HiddenField,
    IntegerField,
    PasswordField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
    TimeField,
)
from wtforms.validators import DataRequired
from wtforms.widgets import ColorInput, TextArea, html_params

# ---------------------------------------------------------------------------------------
# Recursos locales
# ---------------------------------------------------------------------------------------
from now_lms.config import DIRECTORIO_PLANTILLAS

# < --------------------------------------------------------------------------------------------- >
# Definición de formularios

MONEDAS = [
    ("C$", "Córdobas Oro"),
    ("USD", "Dólares"),
]

THEMES_PATH = join(str(DIRECTORIO_PLANTILLAS), "themes")
TEMPLATE_LIST = listdir(THEMES_PATH)
TEMPLATE_CHOICES = []

for template in TEMPLATE_LIST:
    TEMPLATE_CHOICES.append((template, template))


class ConfigForm(FlaskForm):
    """Formulario para editar la configuración del sistema."""

    titulo = StringField(validators=[DataRequired()])
    descripcion = StringField(validators=[DataRequired()])


class ThemeForm(FlaskForm):
    """Formulario para editar el tema del sistema."""

    style = SelectField(
        "Estilo",
        choices=TEMPLATE_CHOICES,
    )


class LoginForm(FlaskForm):
    """Formulario de inicio de sesión."""

    usuario = StringField(validators=[DataRequired()])
    acceso = PasswordField(validators=[DataRequired()])
    inicio_sesion = SubmitField()


class MailForm(FlaskForm):
    """Formulario de configuración de correo electronico."""

    email = BooleanField(validators=[])
    MAIL_SERVER = StringField(validators=[DataRequired()])
    MAIL_DEFAULT_SENDER = StringField(validators=[])
    MAIL_PORT = StringField(validators=[DataRequired()])
    MAIL_USERNAME = StringField(validators=[DataRequired()])
    MAIL_PASSWORD = PasswordField()
    MAIL_USE_TLS = BooleanField(validators=[])
    MAIL_USE_SSL = BooleanField(validators=[])


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
    pagado = BooleanField(validators=[])


class CursoSeccionForm(BaseForm):
    """Formulario para crear una nueva sección."""


class CursoRecursoForm(BaseForm):
    """Base para los recursos del curso."""

    requerido = SelectField("Requerido", choices=[(1, "Requerido"), (2, "Opcional"), (3, "Alternativo")])


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
    pagado = BooleanField(validators=[])


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
            ("guide", "Guia"),
        ],
    )
    pagado = BooleanField(validators=[])


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
            ("ing", "Ingeniero"),
            ("lic", "Licenciado"),
            ("dr", "Doctor"),
        ],
    )
    nacimiento = DateField()
    bio = TextAreaField()


class MsgForm(FlaskForm):
    """Formulario para crear un mensaje en el sistema."""

    titulo = StringField(validators=[])
    editor = MdeField()
    parent = HiddenField(validators=[])


class TextAreaNoEscape(TextArea):
    """
    Renders a multi-line text area.
    """

    validation_attrs = ["required", "disabled", "readonly", "maxlength", "minlength"]

    def __call__(self, field, **kwargs):
        kwargs.setdefault("id", field.id)
        flags = getattr(field, "flags", {})
        for k in dir(flags):
            if k in self.validation_attrs and k not in kwargs:
                kwargs[k] = getattr(flags, k)
        textarea_params = html_params(name=field.name, **kwargs)
        textarea_innerhtml = field._value()
        return f"<textarea {textarea_params}>\r\n{textarea_innerhtml}</textarea>"


class CertificateForm(FlaskForm):
    """Formulario para crear un certificado en el sistema."""

    titulo = StringField(validators=[])
    descripcion = StringField(validators=[])
    habilitado = BooleanField(validators=[])
    publico = BooleanField(validators=[])
    html = TextAreaField(widget=TextAreaNoEscape())
    css = TextAreaField(widget=TextAreaNoEscape())


class AdSenseForm(FlaskForm):
    """AdSbse"""

    meta_tag = TextAreaField(validators=[])
    meta_tag_include = BooleanField(validators=[])
    pub_id = StringField(validators=[])
    add_code = TextAreaField(validators=[])
    show_ads = BooleanField(validators=[])


class PayaplForm(FlaskForm):
    """Paypal"""

    habilitado = BooleanField(validators=[])


class EmitCertificateForm(FlaskForm):

    usuario = SelectField(
        "Usuario",
    )

    curso = SelectField(
        "Curso",
    )

    template = SelectField(
        "Plantilla",
    )
    nota = DecimalField(validators=[])


class CheckMailForm(FlaskForm):
    """Formulario para crear un certificado en el sistema."""

    email = StringField(validators=[])
