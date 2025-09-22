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
"""Definición de formularios."""

# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------
from __future__ import annotations

# ---------------------------------------------------------------------------------------
# Third-party libraries
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
    SelectMultipleField,
    StringField,
    SubmitField,
    TextAreaField,
    TimeField,
)
from wtforms.validators import DataRequired, Length
from wtforms.widgets import ColorInput, TextArea, html_params

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms.i18n import _, _l


# ---------------------------------------------------------------------------------------
# Choice generation functions for translated SelectField options
# ---------------------------------------------------------------------------------------
def get_nivel_choices() -> list[tuple[int, str]]:
    """Return course level choices with proper translations."""
    return [(0, _l("Introductorio")), (1, _l("Principiante")), (2, _l("Intermedio")), (3, _l("Avanzado"))]


def get_modalidad_choices() -> list[tuple[str, str]]:
    """Return course modality choices with proper translations."""
    return [("self_paced", _l("A su propio ritmo")), ("time_based", _l("Con tiempo definido")), ("live", _l("En vivo"))]


def get_requerido_choices() -> list[tuple[str, str]]:
    """Return required field choices with proper translations."""
    return [("required", _l("Requerido")), ("optional", _l("Opcional")), ("substitute", _l("Alternativo"))]


def get_content_type_choices() -> list[tuple[str, str]]:
    """Return content type choices with proper translations."""
    return [("course", _l("Curso")), ("masterclass", _l("Clase Magistral"))]


def get_question_type_choices() -> list[tuple[str, str]]:
    """Return question type choices with proper translations."""
    return [("multiple", _l("Opción múltiple")), ("boolean", _l("Verdadero/Falso"))]


def get_discount_type_choices() -> list[tuple[str, str]]:
    """Return discount type choices with proper translations."""
    return [("percentage", _l("Porcentaje")), ("fixed", _l("Cantidad Fija"))]


def get_estado_choices() -> list[tuple[str, str]]:
    """Return status choices with proper translations."""
    return [
        ("draft", _l("Borrador")),
        ("open", _l("Abierto")),
        ("closed", _l("Cerrado")),
    ]


def get_blog_status_choices() -> list[tuple[str, str]]:
    """Return blog status choices with proper translations."""
    return [
        ("draft", _l("Borrador")),
        ("pending", _l("Pendiente")),
        ("published", _l("Publicado")),
        ("banned", _l("Baneado")),
    ]


def get_resource_type_choices() -> list[tuple[str, str]]:
    """Return resource type choices with proper translations."""
    return [
        ("cheat_sheet", _l("Hoja de Guía")),
        ("ebook", _l("Libro Electronico")),
        ("template", _l("Plantilla")),
        ("guide", _l("Guia")),
    ]


def get_genero_choices() -> list[tuple[str, str]]:
    """Return gender choices with proper translations."""
    return [
        ("none", _l("No especificado")),
        ("other", _l("Otros")),
        ("male", _l("Masculino")),
        ("female", _l("Femenino")),
    ]


def get_titulo_choices() -> list[tuple[str, str]]:
    """Return title choices with proper translations."""
    return [
        ("", _l("No especificado")),
        ("ing", _l("Ingeniero")),
        ("lic", _l("Licenciado")),
        ("dr", _l("Doctor")),
    ]


def get_certificate_type_choices() -> list[tuple[str, str]]:
    """Return certificate type choices with proper translations."""
    return [
        ("course", _l("Curso")),
        ("program", _l("Programa")),
    ]


def get_monedas_choices() -> list[tuple[str, str]]:
    """Return currency choices with proper translations."""
    return [
        # América del Norte
        ("USD", _l("Dólar Estadounidense")),
        ("CAD", _l("Dólar Canadiense")),
        ("MXN", _l("Peso Mexicano")),
        # América Central
        ("GTQ", _l("Quetzal Guatemalteco")),
        ("BZD", _l("Dólar de Belice")),
        ("HNL", _l("Lempira Hondureño")),
        ("NIO", _l("Córdoba Nicaragüense")),
        ("CRC", _l("Colón Costarricense")),
        ("PAB", _l("Balboa Panameño")),
        # El Caribe
        ("DOP", _l("Peso Dominicano")),
        ("CUP", _l("Peso Cubano")),
        ("JMD", _l("Dólar Jamaicano")),
        ("TTD", _l("Dólar de Trinidad y Tobago")),
        ("BBD", _l("Dólar de Barbados")),
        # América del Sur
        ("COP", _l("Peso Colombiano")),
        ("VES", _l("Bolívar Venezolano")),
        ("GYD", _l("Dólar Guyanés")),
        ("SRD", _l("Dólar Surinamés")),
        ("BRL", _l("Real Brasileño")),
        ("PEN", _l("Sol Peruano")),
        ("BOB", _l("Boliviano")),
        ("PYG", _l("Guaraní Paraguayo")),
        ("UYU", _l("Peso Uruguayo")),
        ("ARS", _l("Peso Argentino")),
        ("CLP", _l("Peso Chileno")),
        # Europa
        ("EUR", _l("Euro")),
        ("GBP", _l("Libra Esterlina")),
        ("CHF", _l("Franco Suizo")),
        ("NOK", _l("Corona Noruega")),
        ("SEK", _l("Corona Sueca")),
        ("DKK", _l("Corona Danesa")),
        ("PLN", _l("Zloty Polaco")),
        ("CZK", _l("Corona Checa")),
        ("HUF", _l("Florín Húngaro")),
        ("RON", _l("Leu Rumano")),
        ("BGN", _l("Lev Búlgaro")),
        ("HRK", _l("Kuna Croata")),
        ("RSD", _l("Dinar Serbio")),
        ("BAM", _l("Marco Bosnio")),
        ("MKD", _l("Denar Macedonio")),
        ("ALL", _l("Lek Albanés")),
        ("MDL", _l("Leu Moldavo")),
        ("UAH", _l("Grivna Ucraniana")),
        ("BYN", _l("Rublo Bielorruso")),
        ("RUB", _l("Rublo Ruso")),
        ("TRY", _l("Lira Turca")),
        ("ISK", _l("Corona Islandesa")),
    ]


def get_zonas_horarias_choices() -> list[tuple[str, str]]:
    """Return timezone choices."""
    return [
        # UTC
        ("UTC", "UTC"),
        # América del Norte
        ("America/New_York", "America/New_York"),  # EE.UU. Este
        ("America/Chicago", "America/Chicago"),  # EE.UU. Central
        ("America/Denver", "America/Denver"),  # EE.UU. Montaña
        ("America/Los_Angeles", "America/Los_Angeles"),  # EE.UU. Pacífico
        ("America/Mexico_City", "America/Mexico_City"),  # México
        # Centroamérica
        ("America/Guatemala", "America/Guatemala"),  # Guatemala
        ("America/El_Salvador", "America/El_Salvador"),  # El Salvador
        ("America/Tegucigalpa", "America/Tegucigalpa"),  # Honduras
        ("America/Managua", "America/Managua"),  # Nicaragua
        ("America/Costa_Rica", "America/Costa_Rica"),  # Costa Rica
        ("America/Panama", "America/Panama"),  # Panamá
        # Caribe
        ("America/Havana", "America/Havana"),  # Cuba
        ("America/Santo_Domingo", "America/Santo_Domingo"),  # R. Dominicana
        ("America/Puerto_Rico", "America/Puerto_Rico"),  # Puerto Rico
        ("America/Jamaica", "America/Jamaica"),  # Jamaica
        # Sudamérica
        ("America/Bogota", "America/Bogota"),  # Colombia
        ("America/Lima", "America/Lima"),  # Perú
        ("America/Caracas", "America/Caracas"),  # Venezuela
        ("America/La_Paz", "America/La_Paz"),  # Bolivia
        ("America/Santiago", "America/Santiago"),  # Chile
        ("America/Asuncion", "America/Asuncion"),  # Paraguay
        ("America/Montevideo", "America/Montevideo"),  # Uruguay
        ("America/Argentina/Buenos_Aires", "America/Argentina/Buenos_Aires"),  # Argentina
        ("America/Sao_Paulo", "America/Sao_Paulo"),  # Brasil
        # Europa
        ("Europe/London", "Europe/London"),  # Reino Unido
        ("Europe/Madrid", "Europe/Madrid"),  # España
        ("Europe/Paris", "Europe/Paris"),  # Francia
        ("Europe/Berlin", "Europe/Berlin"),  # Alemania
        ("Europe/Rome", "Europe/Rome"),  # Italia
        ("Europe/Moscow", "Europe/Moscow"),  # Rusia
        # Asia
        ("Asia/Dubai", "Asia/Dubai"),  # Emiratos Árabes
        ("Asia/Kolkata", "Asia/Kolkata"),  # India
        ("Asia/Bangkok", "Asia/Bangkok"),  # Tailandia
        ("Asia/Shanghai", "Asia/Shanghai"),  # China
        ("Asia/Tokyo", "Asia/Tokyo"),  # Japón
        ("Asia/Seoul", "Asia/Seoul"),  # Corea del Sur
        ("Asia/Singapore", "Asia/Singapore"),  # Singapur
    ]


def get_plataforma_choices() -> list[tuple[str, str]]:
    """Return platform choices with proper translations."""
    return [
        ("none", _l("Seleccione")),
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
        ("otros", _l("Otros")),
    ]


def get_slideshow_theme_choices() -> list[tuple[str, str]]:
    """Return slideshow theme choices with proper translations."""
    return [
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
        ("ocean_blue", "Ocean Blue"),
        ("rose_pink", "Rose Pink"),
        ("corporativo", _l("Corporativo")),
    ]


def get_reveal_theme_choices() -> list[tuple[str, str]]:
    """Return reveal.js theme choices."""
    return [
        ("black", "Black"),
        ("white", "White"),
        ("league", "League"),
        ("beige", "Beige"),
        ("sky", "Sky"),
        ("night", "Night"),
        ("serif", "Serif"),
        ("simple", "Simple"),
        ("solarized", "Solarized"),
    ]


# Form label constants
LABEL_TITULO: str = _("Título")


# ---------------------------------------------------------------------------------------
# Forms definitions
# ---------------------------------------------------------------------------------------
class ConfigForm(FlaskForm):
    """Formulario para editar la configuración del sistema."""

    titulo = StringField(validators=[DataRequired()])
    descripcion = StringField(validators=[DataRequired()])

    # Localización
    moneda = SelectField(_("Moneda"), choices=[], validators=[])
    lang = SelectField(
        _("Idioma"), choices=[("es", "Español"), ("en", "English"), ("pt_BR", "Português do Brasil")], validators=[]
    )
    timezone = SelectField(_("Zona Horaria"), choices=[], validators=[])

    verify_user_by_email = BooleanField(validators=[])

    # Navigation configuration
    enable_programs = BooleanField(_("Habilitar Programas"), default=False, validators=[])
    enable_masterclass = BooleanField(_("Habilitar Master Class"), default=False, validators=[])
    enable_resources = BooleanField(_("Habilitar Recursos descargables"), default=False, validators=[])
    enable_blog = BooleanField(_("Habilitar Blog"), default=False, validators=[])

    # Custom information
    titulo_html = StringField(validators=[])
    hero = StringField(validators=[])
    enable_feature_section = BooleanField(validators=[])
    custom_feature_section = TextAreaField(validators=[])
    eslogan = StringField(validators=[])

    # Custom text for template designers
    custom_text1 = StringField(validators=[])
    custom_text2 = StringField(validators=[])
    custom_text3 = StringField(validators=[])
    custom_text4 = StringField(validators=[])

    # File upload configuration
    enable_file_uploads = BooleanField(_("Habilitar subida de archivos descargables"), default=False, validators=[])
    max_file_size = IntegerField(_("Tamaño máximo de archivo (MB)"), default=1, validators=[])

    # HTML preformatted descriptions configuration
    enable_html_preformatted_descriptions = BooleanField(
        _("Permitir HTML preformateado en la descripción de recursos"), default=False, validators=[]
    )

    def __init__(self, *args, **kwargs):
        """Initialize form with translated choices."""
        super().__init__(*args, **kwargs)
        self.moneda.choices = get_monedas_choices()
        self.timezone.choices = get_zonas_horarias_choices()


class ThemeForm(FlaskForm):
    """Formulario para editar el tema del sistema."""

    style = SelectField(
        "Estilo",
        choices=[],
    )


class LoginForm(FlaskForm):
    """Formulario de inicio de sesión."""

    usuario = StringField(validators=[DataRequired()])
    acceso = PasswordField(validators=[DataRequired()])
    inicio_sesion = SubmitField()


class MailForm(FlaskForm):
    """Formulario de configuración de correo electronico."""

    MAIL_SERVER = StringField(validators=[DataRequired()])
    MAIL_DEFAULT_SENDER = StringField(validators=[])
    MAIL_DEFAULT_SENDER_NAME = StringField(validators=[])
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
    descripcion_html_preformateado = BooleanField(_("Descripción en HTML preformateado"), default=False, validators=[])


class GrupoForm(BaseForm):
    """Formulario para crear un grupo de usuarios."""


class CurseForm(BaseForm):
    """Formulario para crear un nuevo curso."""

    # Datos basicos del curso.
    # Nombre y descripción de la base.
    codigo = StringField(validators=[DataRequired()])
    descripcion_corta = StringField(validators=[DataRequired()])
    nivel = SelectField(_("Nivel"), choices=[], validators=[])
    duracion = IntegerField(validators=[])
    # Estado de publicación
    publico = BooleanField(validators=[])
    # Modalidad
    modalidad = SelectField(_("Modalidad"), choices=[], validators=[])
    # Configuración del foro
    foro_habilitado = BooleanField(_("Habilitar foro"), validators=[])
    # Disponibilidad de cupos
    limitado = BooleanField(validators=[])
    capacidad = IntegerField(validators=[])
    # Fechas de inicio y fin
    fecha_inicio = DateField(validators=[])
    fecha_fin = DateField(validators=[])
    # Información de marketing
    promocionado = BooleanField(validators=[])
    # Información de pago
    pagado = BooleanField(validators=[])
    auditable = BooleanField(validators=[])
    certificado = BooleanField(validators=[])
    plantilla_certificado = SelectField(
        _("Plantilla de certificado"),
        choices=[],
        validate_choice=False,
    )
    precio = DecimalField(validators=[])
    categoria = SelectField(
        _("Categoría"),
        choices=[],
        validate_choice=False,
    )
    etiquetas = SelectMultipleField(
        _("Etiquetas"),
        choices=[],
        validate_choice=False,
    )

    def __init__(self, *args, **kwargs):
        """Initialize form with translated choices."""
        super().__init__(*args, **kwargs)
        self.nivel.choices = get_nivel_choices()
        self.modalidad.choices = get_modalidad_choices()

    def validate_foro_habilitado(self, field):
        """Validación personalizada para el campo foro_habilitado."""
        if field.data and self.modalidad.data == "self_paced":
            raise ValueError(_("El foro no puede habilitarse en cursos con modalidad self-paced"))


class CursoSeccionForm(BaseForm):
    """Formulario para crear una nueva sección."""


class CursoRecursoForm(BaseForm):
    """Base para los recursos del curso."""

    requerido = SelectField(_("Requerido"), choices=[], validators=[])

    def __init__(self, *args, **kwargs):
        """Initialize form with translated choices."""
        super().__init__(*args, **kwargs)
        self.requerido.choices = get_requerido_choices()


class CursoRecursoVideoYoutube(CursoRecursoForm):
    """Formulario para un nuevo recurso Youtube."""

    youtube_url = StringField(validators=[DataRequired()])


class CursoRecursoArchivoPDF(CursoRecursoForm):
    """Formulario para un nuevo recurso PDF."""


class CursoRecursoArchivoAudio(CursoRecursoForm):
    """Formulario para un nuevo recurso de audio."""


class CursoRecursoArchivoImagen(CursoRecursoForm):
    """Formulario para un nuevo recurso de audio."""


class CursoRecursoArchivoDescargable(CursoRecursoForm):
    """Formulario para un nuevo recurso descargable."""


class CursoLibraryFileForm(BaseForm):
    """Formulario para subir archivos a la biblioteca del curso."""

    nombre = StringField(
        _("Nombre del archivo"),
        validators=[DataRequired(), Length(min=1, max=255)],
        render_kw={"placeholder": _("Nombre descriptivo para el archivo")},
    )

    descripcion = TextAreaField(
        _("Descripción"),
        validators=[DataRequired(), Length(min=1, max=1000)],
        render_kw={"placeholder": _("Describe el uso o contenido del archivo"), "rows": 3},
    )


class CursoRecursoArchivoText(CursoRecursoForm):
    """Formulario para un nuevo recurso de audio."""

    editor = MdeField()


class CursoRecursoExternalCode(CursoRecursoForm):
    """Formulario para insertar un recurso HTML."""

    html_externo = TextAreaField(validators=[DataRequired()])


class CursoRecursoExternalLink(CursoRecursoForm):
    """Formulario para insertar un recurso HTML."""

    url = StringField(validators=[DataRequired()])


class CursoRecursoSlides(CursoRecursoForm):
    """Formulario para insertar un SlideShow."""

    notes = SelectField(_("Tema"), choices=[], validators=[])

    def __init__(self, *args, **kwargs):
        """Initialize form with translated choices."""
        super().__init__(*args, **kwargs)
        self.notes.choices = get_slideshow_theme_choices()


class SlideShowForm(BaseForm):
    """Formulario para crear una nueva presentación de diapositivas."""

    theme = SelectField(
        _("Tema Reveal.js"),
        choices=[],
        default="simple",
        validators=[DataRequired()],
    )

    def __init__(self, *args, **kwargs):
        """Initialize form with translated choices."""
        super().__init__(*args, **kwargs)
        self.theme.choices = get_reveal_theme_choices()


class SlideForm(FlaskForm):
    """Formulario para crear/editar una diapositiva individual."""

    title = StringField(_("Título de la Diapositiva"), validators=[DataRequired()])
    content = MdeField(_("Contenido de la Diapositiva"), validators=[DataRequired()])
    order = IntegerField(_("Orden"), validators=[DataRequired()], default=1)


class SlideShowEditForm(SlideShowForm):
    """Formulario para editar una presentación existente."""

    slides = []  # type: ignore[var-annotated]


class CursoRecursoMeet(CursoRecursoForm):
    """Formulario para insertar un Meet."""

    fecha = DateField(validators=[])
    hora_inicio = TimeField(validators=[])
    hora_fin = TimeField(validators=[])
    url = StringField(validators=[DataRequired()])
    notes = SelectField(_("Plataforma"), choices=[], validators=[])

    def __init__(self, *args, **kwargs):
        """Initialize form with translated choices."""
        super().__init__(*args, **kwargs)
        self.notes.choices = get_plataforma_choices()


class CategoriaForm(BaseForm):
    """Formulario para crear una categoria."""


class EtiquetaForm(BaseForm):
    """Formulario para crear una etiqueta."""

    color = StringField(widget=ColorInput())


class ProgramaForm(BaseForm):
    """Formulario para crear un programa."""

    codigo = StringField(validators=[DataRequired()])
    precio = DecimalField()
    publico = BooleanField(validators=[])
    estado = SelectField(_("Estado"), choices=[], validators=[])
    promocionado = BooleanField(validators=[])
    pagado = BooleanField(validators=[])
    certificado = BooleanField(validators=[])
    plantilla_certificado = SelectField(
        _("Plantilla de certificado"),
        choices=[],
        validate_choice=False,
    )
    categoria = SelectField(
        _("Categoría"),
        choices=[],
        validate_choice=False,
    )
    etiquetas = SelectMultipleField(
        _("Etiquetas"),
        choices=[],
        validate_choice=False,
    )

    def __init__(self, *args, **kwargs):
        """Initialize form with translated choices."""
        super().__init__(*args, **kwargs)
        self.estado.choices = get_estado_choices()


class RecursoForm(BaseForm):
    """Formulario para crear un recurso."""

    codigo = StringField(validators=[DataRequired()])
    precio = DecimalField()
    publico = BooleanField(validators=[])
    promocionado = BooleanField(validators=[])
    tipo = SelectField(_("Tipo"), choices=[], validators=[])
    pagado = BooleanField(validators=[])

    def __init__(self, *args, **kwargs):
        """Initialize form with translated choices."""
        super().__init__(*args, **kwargs)
        self.tipo.choices = get_resource_type_choices()


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
    genero = SelectField(_("Genero"), choices=[], validators=[])
    titulo = SelectField(_("Titulo"), choices=[], validators=[])
    nacimiento = DateField()
    bio = TextAreaField()

    def __init__(self, *args, **kwargs):
        """Initialize form with translated choices."""
        super().__init__(*args, **kwargs)
        self.genero.choices = get_genero_choices()
        self.titulo.choices = get_titulo_choices()


class MsgForm(FlaskForm):
    """Formulario para crear un mensaje en el sistema - DEPRECATED."""

    titulo = StringField(validators=[])
    editor = MdeField()
    parent = HiddenField(validators=[])


class MessageThreadForm(FlaskForm):
    """Form for creating a new message thread."""

    subject = StringField(_("Asunto"), validators=[DataRequired()])
    content = MdeField(_("Mensaje"), validators=[DataRequired()])
    course_id = HiddenField(validators=[DataRequired()])


class MessageReplyForm(FlaskForm):
    """Form for replying to a message thread."""

    content = MdeField(_("Respuesta"), validators=[DataRequired()])
    thread_id = HiddenField(validators=[DataRequired()])


class MessageReportForm(FlaskForm):
    """Form for reporting a message or thread."""

    reason = TextAreaField(_("Motivo del reporte"), validators=[DataRequired()])
    message_id = HiddenField(validators=[])
    thread_id = HiddenField(validators=[])


class TextAreaNoEscape(TextArea):
    """Renders a multi_ine text area."""

    validation_attrs = ["required", "disabled", "readonly", "maxlength", "minlength"]

    def __call__(self, field, **kwargs):
        """Render the field."""
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
    tipo = SelectField(_("Tipo"), choices=[], validators=[])

    def __init__(self, *args, **kwargs):
        """Initialize form with translated choices."""
        super().__init__(*args, **kwargs)
        self.tipo.choices = get_certificate_type_choices()


class AdSenseForm(FlaskForm):
    """AdSense form with specific ad sizes."""

    meta_tag = TextAreaField(validators=[])
    meta_tag_include = BooleanField(validators=[])
    pub_id = StringField(validators=[])
    add_code = TextAreaField(validators=[])
    show_ads = BooleanField(validators=[])

    # Specific ad size fields
    add_leaderboard = TextAreaField(validators=[])  # 728x90
    add_medium_rectangle = TextAreaField(validators=[])  # 300x250
    add_large_rectangle = TextAreaField(validators=[])  # 336x280
    add_mobile_banner = TextAreaField(validators=[])  # 300x50
    add_wide_skyscraper = TextAreaField(validators=[])  # 160x600
    add_skyscraper = TextAreaField(validators=[])  # 120x600
    add_large_skyscraper = TextAreaField(validators=[])  # 300x600
    add_billboard = TextAreaField(validators=[])  # 970x250


class PayaplForm(FlaskForm):
    """Paypal."""

    habilitado = BooleanField(validators=[])
    sandbox = BooleanField(validators=[])
    paypal_id = StringField(validators=[])
    paypal_sandbox = StringField(validators=[])
    paypal_secret = PasswordField(validators=[])
    paypal_sandbox_secret = PasswordField(validators=[])


class EmitCertificateForm(FlaskForm):
    """Form for emitting certificates."""

    usuario = SelectField(_("Usuario"), choices=[], validators=[])
    content_type = SelectField(_("Tipo de Contenido"), choices=[], validators=[])
    curso = SelectField(_("Curso"), choices=[], validators=[])
    master_class = SelectField(_("Clase Magistral"), choices=[], validators=[])
    template = SelectField(_("Plantilla"), choices=[], validators=[])
    nota = DecimalField(validators=[])

    def __init__(self, *args, **kwargs):
        """Initialize form with translated choices."""
        super().__init__(*args, **kwargs)
        self.content_type.choices = get_content_type_choices()


class CheckMailForm(FlaskForm):
    """Formulario para crear un certificado en el sistema."""

    email = StringField(validators=[])


class ChangePasswordForm(FlaskForm):
    """Formulario para cambiar la contraseña del usuario."""

    current_password = PasswordField("Contraseña Actual", validators=[DataRequired()])
    new_password = PasswordField("Nueva Contraseña", validators=[DataRequired()])
    confirm_password = PasswordField("Confirmar Nueva Contraseña", validators=[DataRequired()])


class ForgotPasswordForm(FlaskForm):
    """Formulario para solicitar recuperación de contraseña."""

    email = StringField("Correo Electrónico", validators=[DataRequired()])


class ResetPasswordForm(FlaskForm):
    """Formulario para restablecer contraseña con token."""

    new_password = PasswordField("Nueva Contraseña", validators=[DataRequired()])
    confirm_password = PasswordField("Confirmar Nueva Contraseña", validators=[DataRequired()])


class PagoForm(FlaskForm):
    """Formulario para crear un pago."""

    nombre = StringField(validators=[DataRequired()])
    apellido = StringField(validators=[DataRequired()])
    correo_electronico = StringField(validators=[DataRequired()])
    direccion1 = StringField(validators=[DataRequired()])
    direccion2 = StringField()
    pais = StringField(validators=[DataRequired()])
    provincia = StringField(validators=[DataRequired()])
    codigo_postal = StringField(validators=[DataRequired()])


# ---------------------------------------------------------------------------------------
# Evaluation Forms
# ---------------------------------------------------------------------------------------


class EvaluationForm(FlaskForm):
    """Formulario para crear/editar una evaluación."""

    title = StringField(LABEL_TITULO, validators=[DataRequired()])
    description = TextAreaField(_("Descripción"))
    is_exam = BooleanField(_("Es un examen"))
    passing_score = DecimalField(_("Puntuación mínima para aprobar"), default=70.0, validators=[DataRequired()])
    max_attempts = IntegerField(_("Máximo número de intentos (vacío = ilimitado)"))


class QuestionForm(FlaskForm):
    """Formulario para crear/editar una pregunta."""

    text = TextAreaField(_("Texto de la pregunta"), validators=[DataRequired()])
    type = SelectField(_("Tipo"), choices=[], validators=[DataRequired()])
    explanation = TextAreaField(_("Explicación (opcional)"))

    def __init__(self, *args, **kwargs):
        """Initialize form with translated choices."""
        super().__init__(*args, **kwargs)
        self.type.choices = get_question_type_choices()


class QuestionOptionForm(FlaskForm):
    """Formulario para crear/editar una opción de pregunta."""

    text = StringField(_("Texto de la opción"), validators=[DataRequired()])
    is_correct = BooleanField(_("Es correcta"))


class EvaluationReopenRequestForm(FlaskForm):
    """Formulario para solicitar reabrir una evaluación."""

    justification_text = TextAreaField(_("Justificación"), validators=[DataRequired()], render_kw={"rows": 4})


class TakeEvaluationForm(FlaskForm):
    """Formulario dinámico para tomar una evaluación.

    This will be dynamically populated with questions.
    """

    pass  # pylint: disable=unnecessary-pass


class ForoMensajeForm(FlaskForm):
    """Formulario para crear un nuevo mensaje del foro."""

    contenido = MdeField(_("Mensaje"), validators=[DataRequired()])
    parent_id = HiddenField()


class ForoMensajeRespuestaForm(FlaskForm):
    """Formulario para responder a un mensaje del foro."""

    contenido = MdeField(_("Respuesta"), validators=[DataRequired()])


class AnnouncementBaseForm(FlaskForm):
    """Formulario base para crear/editar anuncios sin campos de BaseForm."""

    title = StringField(LABEL_TITULO, validators=[DataRequired()])
    message = MdeField(_("Mensaje"), validators=[DataRequired()])
    expires_at = DateField(_("Fecha de expiración"), validators=[], render_kw={"placeholder": _("Opcional")})


class AnnouncementForm(BaseForm):
    """Formulario para anuncios que requiere campos de BaseForm."""

    title = StringField(LABEL_TITULO, validators=[DataRequired()])
    message = MdeField(_("Mensaje"), validators=[DataRequired()])
    expires_at = DateField(_("Fecha de expiración"), validators=[], render_kw={"placeholder": _("Opcional")})


class GlobalAnnouncementForm(AnnouncementForm):
    """Formulario para anuncios globales (solo administradores)."""

    is_sticky = BooleanField(_("Anuncio destacado"))


class CourseAnnouncementForm(AnnouncementBaseForm):
    """Formulario para anuncios de curso (instructores)."""

    course_id = SelectField(_("Curso"), coerce=str, validators=[DataRequired()])


# ---------------------------------------------------------------------------------------
# Coupon Forms
# ---------------------------------------------------------------------------------------


class CouponForm(BaseForm):
    """Formulario para crear y editar cupones de descuento."""

    code = StringField(_("Código del Cupón"), validators=[DataRequired()], render_kw={"placeholder": _("Ej: DESCUENTO50")})
    discount_type = SelectField(
        _("Tipo de Descuento"),
        choices=[],
        default="percentage",
        validators=[DataRequired()],
    )
    discount_value = DecimalField(_("Valor del Descuento"), validators=[DataRequired()], render_kw={"min": "0"})
    max_uses = IntegerField(_("Máximo de Usos"), render_kw={"min": "1", "placeholder": _("Dejar vacío para ilimitado")})
    expires_at = DateField(_("Fecha de Expiración"), render_kw={"placeholder": _("Dejar vacío si no expira")})

    def __init__(self, *args, **kwargs):
        """Initialize form with translated choices."""
        super().__init__(*args, **kwargs)
        self.discount_type.choices = get_discount_type_choices()


class CouponApplicationForm(FlaskForm):
    """Formulario para aplicar un cupón durante la inscripción."""

    coupon_code = StringField(_("Código de Cupón"), render_kw={"placeholder": _("Código de cupón (opcional)")})


# Blog forms
class BlogPostForm(BaseForm):
    """Formulario para crear/editar entradas de blog."""

    title = StringField(LABEL_TITULO, validators=[DataRequired()])
    content = MdeField(_("Contenido"), validators=[DataRequired()])
    allow_comments = BooleanField(_("Permitir comentarios"), default=True)
    tags = StringField(_("Etiquetas (separadas por comas)"))
    status = SelectField(_("Estado"), choices=[], validators=[])

    def __init__(self, *args, **kwargs):
        """Initialize form with translated choices."""
        super().__init__(*args, **kwargs)
        self.status.choices = get_blog_status_choices()


class BlogTagForm(BaseForm):
    """Formulario para crear etiquetas de blog."""

    name = StringField(_("Nombre"), validators=[DataRequired()])


class BlogCommentForm(BaseForm):
    """Formulario para comentarios de blog."""

    content = TextAreaField(_("Comentario"), validators=[DataRequired()])


# ---------------------------------------------------------------------------------------
# Administrative Enrollment Forms
# ---------------------------------------------------------------------------------------


class AdminCourseEnrollmentForm(FlaskForm):
    """Formulario para inscripción administrativa de estudiantes a cursos."""

    student_username = StringField(
        _("Usuario del Estudiante"),
        validators=[DataRequired()],
        render_kw={"placeholder": _("Nombre de usuario del estudiante")},
    )
    bypass_payment = BooleanField(
        _("Omitir Pago"),
        default=True,
        render_kw={"title": _("Si está marcado, el estudiante tendrá acceso completo sin importar si el curso es pagado")},
    )
    notes = TextAreaField(
        _("Notas (opcional)"), render_kw={"rows": 3, "placeholder": _("Notas adicionales sobre la inscripción")}
    )


class AdminProgramEnrollmentForm(FlaskForm):
    """Formulario para inscripción administrativa de estudiantes a programas."""

    student_username = StringField(
        _("Usuario del Estudiante"),
        validators=[DataRequired()],
        render_kw={"placeholder": _("Nombre de usuario del estudiante")},
    )
    bypass_payment = BooleanField(
        _("Omitir Pago"),
        default=True,
        render_kw={
            "title": _("Si está marcado, el estudiante tendrá acceso completo a todos los cursos sin importar si son pagados")
        },
    )
    notes = TextAreaField(
        _("Notas (opcional)"), render_kw={"rows": 3, "placeholder": _("Notas adicionales sobre la inscripción")}
    )
