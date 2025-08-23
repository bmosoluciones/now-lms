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

"""Master Class forms."""

# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------
from datetime import date

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------
from flask_wtf import FlaskForm
from wtforms import BooleanField, DateField, SelectField, StringField, TextAreaField, TimeField
from wtforms.validators import URL, DataRequired, Length, Optional, ValidationError

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms.db import Certificado, database

# ---------------------------------------------------------------------------------------
# Master Class forms
# ---------------------------------------------------------------------------------------


class MasterClassForm(FlaskForm):
    """Form for creating and editing master classes."""

    # Basic information fields
    title = StringField(
        "Título",
        validators=[
            DataRequired(message="El título es requerido"),
            Length(min=5, max=150, message="El título debe tener entre 5 y 150 caracteres"),
        ],
        render_kw={"placeholder": "Título de la clase magistral"},
    )

    description_public = TextAreaField(
        "Descripción Pública",
        validators=[
            DataRequired(message="La descripción pública es requerida"),
            Length(min=20, max=2000, message="La descripción pública debe tener entre 20 y 2000 caracteres"),
        ],
        render_kw={"rows": 4, "placeholder": "Descripción visible para todos los usuarios"},
    )

    description_private = TextAreaField(
        "Descripción Privada",
        validators=[Optional(), Length(max=2000, message="La descripción privada no puede exceder 2000 caracteres")],
        render_kw={"rows": 3, "placeholder": "Descripción visible solo para usuarios inscritos"},
    )

    # Date and time fields
    date = DateField(
        "Fecha del Evento", validators=[DataRequired(message="La fecha del evento es requerida")], format="%Y-%m-%d"
    )

    start_time = TimeField(
        "Hora de Inicio", validators=[DataRequired(message="La hora de inicio es requerida")], format="%H:%M"
    )

    end_time = TimeField("Hora de Fin", validators=[DataRequired(message="La hora de fin es requerida")], format="%H:%M")

    # Platform configuration
    platform_name = SelectField(
        "Plataforma",
        choices=[
            ("Zoom", "Zoom"),
            ("Google Meet", "Google Meet"),
            ("Microsoft Teams", "Microsoft Teams"),
            ("Jitsi Meet", "Jitsi Meet"),
            ("Discord", "Discord"),
            ("Otra", "Otra"),
        ],
        validators=[DataRequired(message="La plataforma es requerida")],
    )

    platform_url = StringField(
        "Enlace de la Plataforma",
        validators=[
            DataRequired(message="El enlace de la plataforma es requerido"),
            URL(message="Debe ser una URL válida"),
            Length(max=500, message="El enlace no puede exceder 500 caracteres"),
        ],
        render_kw={"placeholder": "https://zoom.us/j/123456789"},
    )

    # Certification fields
    is_certificate = BooleanField("Otorga Certificación")

    diploma_template_id = SelectField("Plantilla de Certificado", coerce=str, validators=[Optional()])

    # Optional recording URL
    video_recording_url = StringField(
        "URL de Grabación",
        validators=[
            Optional(),
            URL(message="Debe ser una URL válida"),
            Length(max=500, message="La URL no puede exceder 500 caracteres"),
        ],
        render_kw={"placeholder": "https://ejemplo.com/grabacion"},
    )

    def __init__(self, *args, **kwargs):
        """Initialize form with dynamic choices for diploma templates."""
        super().__init__(*args, **kwargs)

        # Populate diploma template choices from database
        templates = database.session.execute(database.select(Certificado).filter_by(habilitado=True)).scalars().all()
        self.diploma_template_id.choices = [("", "Seleccionar plantilla")] + [
            (template.code, template.titulo) for template in templates
        ]

    # Custom validators
    def validate_end_time(self, field):
        """Validate that end time is after start time."""
        if self.start_time.data and field.data:
            if field.data <= self.start_time.data:
                raise ValidationError("La hora de fin debe ser posterior a la hora de inicio")

    def validate_date(self, field):
        """Validate that date is not in the past."""
        if field.data and field.data < date.today():
            raise ValidationError("La fecha del evento no puede ser en el pasado")

    def validate_diploma_template_id(self, field):
        """Validate diploma template when is_certificate is True."""
        if self.is_certificate.data and not field.data:
            raise ValidationError("La plantilla de certificado es requerida para clases con certificación")


class MasterClassEnrollmentForm(FlaskForm):
    """Simple form for master class enrollment confirmation."""

    def __init__(self, *args, **kwargs):
        """Initialize enrollment form."""
        super().__init__(*args, **kwargs)
