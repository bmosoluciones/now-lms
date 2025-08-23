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
from wtforms.validators import DataRequired
from wtforms.widgets import ColorInput, TextArea, html_params

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------


# Form label constants
LABEL_TITULO: str = "Título"

MONEDAS = [
    # América del Norte
    ("USD", "Dólar Estadounidense"),
    ("CAD", "Dólar Canadiense"),
    ("MXN", "Peso Mexicano"),
    # América Central
    ("GTQ", "Quetzal Guatemalteco"),
    ("BZD", "Dólar de Belice"),
    ("HNL", "Lempira Hondureño"),
    ("NIO", "Córdoba Nicaragüense"),
    ("CRC", "Colón Costarricense"),
    ("PAB", "Balboa Panameño"),
    # El Caribe
    ("DOP", "Peso Dominicano"),
    ("CUP", "Peso Cubano"),
    ("JMD", "Dólar Jamaicano"),
    ("TTD", "Dólar de Trinidad y Tobago"),
    ("BBD", "Dólar de Barbados"),
    # América del Sur
    ("COP", "Peso Colombiano"),
    ("VES", "Bolívar Venezolano"),
    ("GYD", "Dólar Guyanés"),
    ("SRD", "Dólar Surinamés"),
    ("BRL", "Real Brasileño"),
    ("PEN", "Sol Peruano"),
    ("BOB", "Boliviano"),
    ("PYG", "Guaraní Paraguayo"),
    ("UYU", "Peso Uruguayo"),
    ("ARS", "Peso Argentino"),
    ("CLP", "Peso Chileno"),
    # Europa
    ("EUR", "Euro"),
    ("GBP", "Libra Esterlina"),
    ("CHF", "Franco Suizo"),
    ("NOK", "Corona Noruega"),
    ("SEK", "Corona Sueca"),
    ("DKK", "Corona Danesa"),
    ("PLN", "Zloty Polaco"),
    ("CZK", "Corona Checa"),
    ("HUF", "Florín Húngaro"),
    ("RON", "Leu Rumano"),
    ("BGN", "Lev Búlgaro"),
    ("HRK", "Kuna Croata"),
    ("RSD", "Dinar Serbio"),
    ("BAM", "Marco Bosnio"),
    ("MKD", "Denar Macedonio"),
    ("ALL", "Lek Albanés"),
    ("MDL", "Leu Moldavo"),
    ("UAH", "Grivna Ucraniana"),
    ("BYN", "Rublo Bielorruso"),
    ("RUB", "Rublo Ruso"),
    ("TRY", "Lira Turca"),
    ("ISK", "Corona Islandesa"),
]


class ConfigForm(FlaskForm):
    """Formulario para editar la configuración del sistema."""

    titulo = StringField(validators=[DataRequired()])
    descripcion = StringField(validators=[DataRequired()])
    moneda = SelectField("Moneda", choices=MONEDAS, validators=[])

    verify_user_by_email = BooleanField(validators=[])

    # Navigation configuration
    enable_programs = BooleanField("Habilitar Programas", default=False, validators=[])
    enable_masterclass = BooleanField("Habilitar Master Class", default=False, validators=[])
    enable_resources = BooleanField("Habilitar Recursos descargables", default=False, validators=[])
    enable_blog = BooleanField("Habilitar Blog", default=False, validators=[])


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


class GrupoForm(BaseForm):
    """Formulario para crear un grupo de usuarios."""


class CurseForm(BaseForm):
    """Formulario para crear un nuevo curso."""

    # Datos basicos del curso.
    # Nombre y descripción de la base.
    codigo = StringField(validators=[DataRequired()])
    descripcion_corta = StringField(validators=[DataRequired()])
    nivel = SelectField("User", choices=[(0, "Introductorio"), (1, "Principiante"), (2, "Intermedio"), (3, "Avanzado")])
    duracion = IntegerField(validators=[])
    # Estado de publicación
    publico = BooleanField(validators=[])
    # Modalidad
    modalidad = SelectField(
        "Modalidad",
        choices=[("self_paced", "A su propio ritmo"), ("time_based", "Con tiempo definido"), ("live", "En vivo")],
    )
    # Configuración del foro
    foro_habilitado = BooleanField("Habilitar foro", validators=[])
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
        "Plantilla de certificado",
        choices=[],
        validate_choice=False,
    )
    precio = DecimalField(validators=[])
    categoria = SelectField(
        "Categoría",
        choices=[],
        validate_choice=False,
    )
    etiquetas = SelectMultipleField(
        "Etiquetas",
        choices=[],
        validate_choice=False,
    )

    def validate_foro_habilitado(self, field):
        """Validación personalizada para el campo foro_habilitado."""
        if field.data and self.modalidad.data == "self_paced":
            raise ValueError("El foro no puede habilitarse en cursos con modalidad self-paced")


class CursoSeccionForm(BaseForm):
    """Formulario para crear una nueva sección."""


class CursoRecursoForm(BaseForm):
    """Base para los recursos del curso."""

    requerido = SelectField(
        "Requerido", choices=[("required", "Requerido"), ("optional", "Opcional"), ("substitute", "Alternativo")]
    )


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
    """Formulario para insertar un recurso HTML."""

    html_externo = StringField(validators=[DataRequired()])


class CursoRecursoExternalLink(CursoRecursoForm):
    """Formulario para insertar un recurso HTML."""

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
            ("ocean_blue", "Ocean Blue"),
            ("rose_pink", "Rose Pink"),
            ("corporativo", "Corporativo"),
        ],
    )


class SlideShowForm(BaseForm):
    """Formulario para crear una nueva presentación de diapositivas."""

    theme = SelectField(
        "Tema Reveal.js",
        choices=[
            ("black", "Black"),
            ("white", "White"),
            ("league", "League"),
            ("beige", "Beige"),
            ("sky", "Sky"),
            ("night", "Night"),
            ("serif", "Serif"),
            ("simple", "Simple"),
            ("solarized", "Solarized"),
        ],
        default="simple",
        validators=[DataRequired()],
    )


class SlideForm(FlaskForm):
    """Formulario para crear/editar una diapositiva individual."""

    title = StringField("Título de la Diapositiva", validators=[DataRequired()])
    content = MdeField("Contenido de la Diapositiva", validators=[DataRequired()])
    order = IntegerField("Orden", validators=[DataRequired()], default=1)


class SlideShowEditForm(SlideShowForm):
    """Formulario para editar una presentación existente."""

    slides = []  # type: ignore[var-annotated]


class CursoRecursoMeet(CursoRecursoForm):
    """Formulario para insertar un Meet."""

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
    """Formulario para crear una categoria."""


class EtiquetaForm(BaseForm):
    """Formulario para crear una etiqueta."""

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
    certificado = BooleanField(validators=[])
    plantilla_certificado = SelectField(
        "Plantilla de certificado",
        choices=[],
        validate_choice=False,
    )
    categoria = SelectField(
        "Categoría",
        choices=[],
        validate_choice=False,
    )
    etiquetas = SelectMultipleField(
        "Etiquetas",
        choices=[],
        validate_choice=False,
    )


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
    """Formulario para crear un mensaje en el sistema - DEPRECATED."""

    titulo = StringField(validators=[])
    editor = MdeField()
    parent = HiddenField(validators=[])


class MessageThreadForm(FlaskForm):
    """Form for creating a new message thread."""

    subject = StringField("Asunto", validators=[DataRequired()])
    content = MdeField("Mensaje", validators=[DataRequired()])
    course_id = HiddenField(validators=[DataRequired()])


class MessageReplyForm(FlaskForm):
    """Form for replying to a message thread."""

    content = MdeField("Respuesta", validators=[DataRequired()])
    thread_id = HiddenField(validators=[DataRequired()])


class MessageReportForm(FlaskForm):
    """Form for reporting a message or thread."""

    reason = TextAreaField("Motivo del reporte", validators=[DataRequired()])
    message_id = HiddenField(validators=[])
    thread_id = HiddenField(validators=[])


class TextAreaNoEscape(TextArea):
    """Renders a multi-line text area."""

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

    usuario = SelectField(
        "Usuario",
    )

    content_type = SelectField("Tipo de Contenido", choices=[("course", "Curso"), ("masterclass", "Clase Magistral")])

    curso = SelectField(
        "Curso",
    )

    master_class = SelectField(
        "Clase Magistral",
    )

    template = SelectField(
        "Plantilla",
    )
    nota = DecimalField(validators=[])


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
    description = TextAreaField("Descripción")
    is_exam = BooleanField("Es un examen")
    passing_score = DecimalField("Puntuación mínima para aprobar", default=70.0, validators=[DataRequired()])
    max_attempts = IntegerField("Máximo número de intentos (vacío = ilimitado)")


class QuestionForm(FlaskForm):
    """Formulario para crear/editar una pregunta."""

    text = TextAreaField("Texto de la pregunta", validators=[DataRequired()])
    type = SelectField(
        "Tipo", choices=[("multiple", "Opción múltiple"), ("boolean", "Verdadero/Falso")], validators=[DataRequired()]
    )
    explanation = TextAreaField("Explicación (opcional)")


class QuestionOptionForm(FlaskForm):
    """Formulario para crear/editar una opción de pregunta."""

    text = StringField("Texto de la opción", validators=[DataRequired()])
    is_correct = BooleanField("Es correcta")


class EvaluationReopenRequestForm(FlaskForm):
    """Formulario para solicitar reabrir una evaluación."""

    justification_text = TextAreaField("Justificación", validators=[DataRequired()], render_kw={"rows": 4})


class TakeEvaluationForm(FlaskForm):
    """Formulario dinámico para tomar una evaluación.

    This will be dynamically populated with questions.
    """

    pass  # pylint: disable=unnecessary-pass


class ForoMensajeForm(FlaskForm):
    """Formulario para crear un nuevo mensaje del foro."""

    contenido = MdeField("Mensaje", validators=[DataRequired()])
    parent_id = HiddenField()


class ForoMensajeRespuestaForm(FlaskForm):
    """Formulario para responder a un mensaje del foro."""

    contenido = MdeField("Respuesta", validators=[DataRequired()])


class AnnouncementBaseForm(FlaskForm):
    """Formulario base para crear/editar anuncios sin campos de BaseForm."""

    title = StringField(LABEL_TITULO, validators=[DataRequired()])
    message = MdeField("Mensaje", validators=[DataRequired()])
    expires_at = DateField("Fecha de expiración", validators=[], render_kw={"placeholder": "Opcional"})


class AnnouncementForm(BaseForm):
    """Formulario para anuncios que requiere campos de BaseForm."""

    title = StringField(LABEL_TITULO, validators=[DataRequired()])
    message = MdeField("Mensaje", validators=[DataRequired()])
    expires_at = DateField("Fecha de expiración", validators=[], render_kw={"placeholder": "Opcional"})


class GlobalAnnouncementForm(AnnouncementForm):
    """Formulario para anuncios globales (solo administradores)."""

    is_sticky = BooleanField("Anuncio destacado")


class CourseAnnouncementForm(AnnouncementBaseForm):
    """Formulario para anuncios de curso (instructores)."""

    course_id = SelectField("Curso", coerce=str, validators=[DataRequired()])


# ---------------------------------------------------------------------------------------
# Coupon Forms
# ---------------------------------------------------------------------------------------


class CouponForm(BaseForm):
    """Formulario para crear y editar cupones de descuento."""

    code = StringField("Código del Cupón", validators=[DataRequired()], render_kw={"placeholder": "Ej: DESCUENTO50"})
    discount_type = SelectField(
        "Tipo de Descuento",
        choices=[("percentage", "Porcentaje"), ("fixed", "Cantidad Fija")],
        default="percentage",
        validators=[DataRequired()],
    )
    discount_value = DecimalField("Valor del Descuento", validators=[DataRequired()], render_kw={"min": "0"})
    max_uses = IntegerField("Máximo de Usos", render_kw={"min": "1", "placeholder": "Dejar vacío para ilimitado"})
    expires_at = DateField("Fecha de Expiración", render_kw={"placeholder": "Dejar vacío si no expira"})


class CouponApplicationForm(FlaskForm):
    """Formulario para aplicar un cupón durante la inscripción."""

    coupon_code = StringField("Código de Cupón", render_kw={"placeholder": "Código de cupón (opcional)"})


# Blog forms
class BlogPostForm(BaseForm):
    """Formulario para crear/editar entradas de blog."""

    title = StringField(LABEL_TITULO, validators=[DataRequired()])
    content = MdeField("Contenido", validators=[DataRequired()])
    allow_comments = BooleanField("Permitir comentarios", default=True)
    tags = StringField("Etiquetas (separadas por comas)")
    status = SelectField(
        "Estado",
        choices=[("draft", "Borrador"), ("pending", "Pendiente"), ("published", "Publicado"), ("banned", "Baneado")],
    )


class BlogTagForm(BaseForm):
    """Formulario para crear etiquetas de blog."""

    name = StringField("Nombre", validators=[DataRequired()])


class BlogCommentForm(BaseForm):
    """Formulario para comentarios de blog."""

    content = TextAreaField("Comentario", validators=[DataRequired()])
