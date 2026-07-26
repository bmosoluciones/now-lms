# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""
Comprehensive and rigorous unit tests for all forms in the system.
Ensures zero regressions are introduced on form validation, choices, and processing.
"""

from __future__ import annotations
import datetime
import pytest
from wtforms.validators import ValidationError
from wtforms import Form
from werkzeug.datastructures import MultiDict

from now_lms.forms import (
    get_nivel_choices,
    get_modalidad_choices,
    get_requerido_choices,
    get_content_type_choices,
    get_question_type_choices,
    get_discount_type_choices,
    get_estado_choices,
    get_blog_status_choices,
    get_resource_type_choices,
    get_genero_choices,
    get_titulo_choices,
    get_certificate_type_choices,
    get_monedas_choices,
    get_zonas_horarias_choices,
    get_plataforma_choices,
    get_slideshow_theme_choices,
    get_reveal_theme_choices,
    # Custom fields
    MultiFormatDateField,
    FlexibleDecimalField,
    FlexibleIntegerField,
    # Forms
    ConfigForm,
    ThemeForm,
    LoginForm,
    MailForm,
    LogonForm,
    GrupoForm,
    CurseForm,
    CursoSeccionForm,
    CursoRecursoVideoYoutube,
    CursoRecursoArchivoPDF,
    CursoRecursoArchivoAudio,
    CursoRecursoArchivoImagen,
    CursoRecursoArchivoDescargable,
    CursoLibraryFileForm,
    CursoRecursoArchivoText,
    CursoRecursoExternalCode,
    CursoRecursoExternalLink,
    CursoRecursoSlides,
    SlideShowForm,
    SlideForm,
    CursoRecursoMeet,
    CategoriaForm,
    EtiquetaForm,
    ProgramaForm,
    RecursoForm,
    UserForm,
    MessageThreadForm,
    MessageReplyForm,
    MessageReportForm,
    CertificateForm,
    TextAreaNoEscape,
    AdSenseForm,
    PayaplForm,
    EmitCertificateForm,
    CheckMailForm,
    ChangePasswordForm,
    ForgotPasswordForm,
    ResetPasswordForm,
    PagoForm,
    EvaluationForm,
    QuestionForm,
    QuestionOptionForm,
    EvaluationReopenRequestForm,
    ForoMensajeForm,
    ForoMensajeRespuestaForm,
    AnnouncementForm,
    GlobalAnnouncementForm,
    CourseAnnouncementForm,
    CouponForm,
    CouponApplicationForm,
    BlogPostForm,
    BlogTagForm,
    BlogCommentForm,
    AdminCourseEnrollmentForm,
    AdminProgramEnrollmentForm,
    CustomPageFooterForm,
    EnlaceUtilForm,
    ExternalApiKeyForm,
)
from now_lms.forms.masterclass import get_platform_choices


def test_choice_generators(app):
    """Test all choice generation helper functions to ensure they return valid list of tuples."""
    with app.app_context():
        # Test get_nivel_choices
        nivel_choices = get_nivel_choices()
        assert isinstance(nivel_choices, list)
        assert len(nivel_choices) > 0
        assert all(isinstance(opt, tuple) and len(opt) == 2 for opt in nivel_choices)

        # Test get_modalidad_choices
        modalidad_choices = get_modalidad_choices()
        assert isinstance(modalidad_choices, list)
        assert len(modalidad_choices) > 0
        assert all(isinstance(opt, tuple) and len(opt) == 2 for opt in modalidad_choices)

        # Test get_requerido_choices
        requerido_choices = get_requerido_choices()
        assert isinstance(requerido_choices, list)
        assert len(requerido_choices) > 0

        # Test get_content_type_choices
        content_choices = get_content_type_choices()
        assert isinstance(content_choices, list)
        assert len(content_choices) > 0

        # Test get_question_type_choices
        question_choices = get_question_type_choices()
        assert isinstance(question_choices, list)
        assert len(question_choices) > 0

        # Test get_discount_type_choices
        discount_choices = get_discount_type_choices()
        assert isinstance(discount_choices, list)
        assert len(discount_choices) > 0

        # Test get_estado_choices
        estado_choices = get_estado_choices()
        assert isinstance(estado_choices, list)
        assert len(estado_choices) > 0

        # Test get_blog_status_choices
        blog_status_choices = get_blog_status_choices()
        assert isinstance(blog_status_choices, list)
        assert len(blog_status_choices) > 0

        # Test get_resource_type_choices
        resource_choices = get_resource_type_choices()
        assert isinstance(resource_choices, list)
        assert len(resource_choices) > 0

        # Test get_genero_choices
        genero_choices = get_genero_choices()
        assert isinstance(genero_choices, list)
        assert len(genero_choices) > 0

        # Test get_titulo_choices
        titulo_choices = get_titulo_choices()
        assert isinstance(titulo_choices, list)
        assert len(titulo_choices) > 0

        # Test get_certificate_type_choices
        cert_type_choices = get_certificate_type_choices()
        assert isinstance(cert_type_choices, list)
        assert len(cert_type_choices) > 0

        # Test get_monedas_choices
        monedas_choices = get_monedas_choices()
        assert isinstance(monedas_choices, list)
        assert len(monedas_choices) > 0

        # Test get_zonas_horarias_choices
        tz_choices = get_zonas_horarias_choices()
        assert isinstance(tz_choices, list)
        assert len(tz_choices) > 0

        # Test get_plataforma_choices
        plataforma_choices = get_plataforma_choices()
        assert isinstance(plataforma_choices, list)
        assert len(plataforma_choices) > 0

        # Test get_slideshow_theme_choices
        slideshow_theme_choices = get_slideshow_theme_choices()
        assert isinstance(slideshow_theme_choices, list)
        assert len(slideshow_theme_choices) > 0

        # Test get_reveal_theme_choices
        reveal_choices = get_reveal_theme_choices()
        assert isinstance(reveal_choices, list)
        assert len(reveal_choices) > 0

        # Test get_platform_choices from masterclass
        mc_platform_choices = get_platform_choices()
        assert isinstance(mc_platform_choices, list)
        assert len(mc_platform_choices) > 0


# ---------------------------------------------------------------------------
# Custom Fields Tests
# ---------------------------------------------------------------------------

class DummyForm(Form):
    """Form containing custom fields to test process_formdata."""
    date_field = MultiFormatDateField(formats=["%Y-%m-%d", "%d/%m/%Y"])
    decimal_field = FlexibleDecimalField()
    integer_field = FlexibleIntegerField()


def test_multi_format_date_field(app):
    """Test MultiFormatDateField validation, formats, and empty handling."""
    with app.test_request_context():
        # Valid ISO format
        form = DummyForm(MultiDict({"date_field": "2026-10-15"}))
        assert form.validate()
        assert form.date_field.data == datetime.date(2026, 10, 15)

        # Valid custom Spanish format
        form = DummyForm(MultiDict({"date_field": "15/10/2026"}))
        assert form.validate()
        assert form.date_field.data == datetime.date(2026, 10, 15)

        # Trimming whitespace
        form = DummyForm(MultiDict({"date_field": "  15/10/2026  "}))
        assert form.validate()
        assert form.date_field.data == datetime.date(2026, 10, 15)

        # Empty/None values
        form = DummyForm(MultiDict({"date_field": ""}))
        assert form.validate()
        assert form.date_field.data is None

        form = DummyForm(MultiDict({"date_field": None}))
        assert form.validate()
        assert form.date_field.data is None

        # Invalid date format raises ValueError inside process_formdata
        form = DummyForm(MultiDict({"date_field": "not-a-date"}))
        assert not form.validate()
        assert "date" in form.errors["date_field"][0].lower()


def test_flexible_decimal_field(app):
    """Test FlexibleDecimalField handles comma-separated decimals and spaces."""
    with app.test_request_context():
        # Dot separated
        form = DummyForm(MultiDict({"decimal_field": "12.34"}))
        assert form.validate()
        assert float(form.decimal_field.data) == 12.34

        # Comma separated (normalized to dot)
        form = DummyForm(MultiDict({"decimal_field": "12,34"}))
        assert form.validate()
        assert float(form.decimal_field.data) == 12.34

        # Trimming spaces
        form = DummyForm(MultiDict({"decimal_field": "  15,5  "}))
        assert form.validate()
        assert float(form.decimal_field.data) == 15.5

        # Empty values
        form = DummyForm(MultiDict({"decimal_field": ""}))
        assert form.validate()
        assert form.decimal_field.data is None

        form = DummyForm(MultiDict({"decimal_field": None}))
        assert form.validate()
        assert form.decimal_field.data is None


def test_flexible_integer_field(app):
    """Test FlexibleIntegerField handles spaces and empty strings."""
    with app.test_request_context():
        # Valid integer
        form = DummyForm(MultiDict({"integer_field": "42"}))
        assert form.validate()
        assert form.integer_field.data == 42

        # Trimming spaces
        form = DummyForm(MultiDict({"integer_field": "  100  "}))
        assert form.validate()
        assert form.integer_field.data == 100

        # Empty values
        form = DummyForm(MultiDict({"integer_field": ""}))
        assert form.validate()
        assert form.integer_field.data is None

        form = DummyForm(MultiDict({"integer_field": None}))
        assert form.validate()
        assert form.integer_field.data is None


# ---------------------------------------------------------------------------
# Forms defined in __init__.py Tests
# ---------------------------------------------------------------------------

def test_config_form(app):
    """Test ConfigForm initialization and validation."""
    with app.test_request_context():
        form = ConfigForm(
            MultiDict({
                "titulo": "NOW LMS",
                "descripcion": "Plataforma de educación online",
                "moneda": "USD",
                "lang": "es",
                "timezone": "UTC",
            })
        )
        assert form.validate()
        assert form.titulo.data == "NOW LMS"
        assert form.descripcion.data == "Plataforma de educación online"
        assert form.moneda.data == "USD"
        assert form.lang.data == "es"
        assert form.timezone.data == "UTC"

        # Missing required fields
        form = ConfigForm(MultiDict({}))
        assert not form.validate()
        assert "titulo" in form.errors
        assert "descripcion" in form.errors


def test_theme_form(app):
    """Test ThemeForm validation."""
    with app.test_request_context():
        form = ThemeForm(MultiDict({"style": "modern"}))
        form.style.choices = [("modern", "Modern")]
        assert form.validate()
        assert form.style.data == "modern"


def test_login_form(app):
    """Test LoginForm validation."""
    with app.test_request_context():
        form = LoginForm(MultiDict({"usuario": "admin", "acceso": "password"}))
        assert form.validate()

        form = LoginForm(MultiDict({}))
        assert not form.validate()
        assert "usuario" in form.errors
        assert "acceso" in form.errors


def test_mail_form(app):
    """Test MailForm validation."""
    with app.test_request_context():
        form = MailForm(
            MultiDict({
                "MAIL_SERVER": "smtp.example.com",
                "MAIL_PORT": "587",
                "MAIL_USERNAME": "smtp_user",
                "MAIL_PASSWORD": "smtp_password",
            })
        )
        assert form.validate()

        form = MailForm(MultiDict({}))
        assert not form.validate()
        assert "MAIL_SERVER" in form.errors


def test_logon_form(app):
    """Test LogonForm validation."""
    with app.test_request_context():
        form = LogonForm(
            MultiDict({
                "usuario": "newuser",
                "acceso": "password123",
                "nombre": "Juan",
                "apellido": "Perez",
                "correo_electronico": "juan@example.com",
            })
        )
        assert form.validate()

        form = LogonForm(MultiDict({}))
        assert not form.validate()
        assert "usuario" in form.errors
        assert "acceso" in form.errors


def test_grupo_form(app):
    """Test GrupoForm validation."""
    with app.test_request_context():
        form = GrupoForm(
            MultiDict({
                "nombre": "Grupo A",
                "descripcion": "Descripción del grupo",
            })
        )
        assert form.validate()


def test_curse_form_validation(app):
    """Test CurseForm custom validation rule validate_foro_habilitado."""
    with app.test_request_context():
        # Valid: live modality with forum enabled
        form = CurseForm(
            MultiDict({
                "nombre": "Curso de Python",
                "descripcion": "Aprende Python",
                "codigo": "PY-101",
                "descripcion_corta": "Python para principiantes",
                "nivel": "1",
                "modalidad": "live",
                "foro_habilitado": "y",
            })
        )
        assert form.validate()

        # Valid: self_paced modality with forum disabled
        form = CurseForm(
            MultiDict({
                "nombre": "Curso de Python",
                "descripcion": "Aprende Python",
                "codigo": "PY-101",
                "descripcion_corta": "Python para principiantes",
                "nivel": "1",
                "modalidad": "self_paced",
            })
        )
        assert form.validate()

        # Invalid: self_paced modality with forum enabled (raises ValidationError)
        form = CurseForm(
            MultiDict({
                "nombre": "Curso de Python",
                "descripcion": "Aprende Python",
                "codigo": "PY-101",
                "descripcion_corta": "Python para principiantes",
                "nivel": "1",
                "modalidad": "self_paced",
                "foro_habilitado": "y",
            })
        )
        assert not form.validate()
        assert "foro_habilitado" in form.errors


def test_curso_seccion_form(app):
    """Test CursoSeccionForm validation."""
    with app.test_request_context():
        form = CursoSeccionForm(
            MultiDict({
                "nombre": "Sección 1",
                "descripcion": "Intro",
            })
        )
        assert form.validate()


def test_curso_recurso_forms(app):
    """Test all course resource forms."""
    with app.test_request_context():
        # YouTube Recurso
        form = CursoRecursoVideoYoutube(
            MultiDict({
                "nombre": "Youtube",
                "descripcion": "Desc",
                "requerido": "required",
                "youtube_url": "https://youtube.com/watch?v=123",
            })
        )
        assert form.validate()

        form = CursoRecursoVideoYoutube(
            MultiDict({
                "nombre": "Youtube",
                "descripcion": "Desc",
                "requerido": "required",
                "youtube_url": "",
            })
        )
        assert not form.validate()

        # PDF Recurso
        form = CursoRecursoArchivoPDF(
            MultiDict({
                "nombre": "PDF",
                "descripcion": "Desc",
                "requerido": "optional",
            })
        )
        assert form.validate()

        # Audio Recurso
        form = CursoRecursoArchivoAudio(
            MultiDict({
                "nombre": "Audio",
                "descripcion": "Desc",
                "requerido": "optional",
            })
        )
        assert form.validate()

        # Image Recurso
        form = CursoRecursoArchivoImagen(
            MultiDict({
                "nombre": "Imagen",
                "descripcion": "Desc",
                "requerido": "optional",
            })
        )
        assert form.validate()

        # Descargable Recurso
        form = CursoRecursoArchivoDescargable(
            MultiDict({
                "nombre": "Descargable",
                "descripcion": "Desc",
                "requerido": "optional",
            })
        )
        assert form.validate()

        # Text Recurso
        form = CursoRecursoArchivoText(
            MultiDict({
                "nombre": "Texto",
                "descripcion": "Desc",
                "requerido": "optional",
                "editor": "Contenido MDE",
            })
        )
        assert form.validate()

        # External Code Recurso
        form = CursoRecursoExternalCode(
            MultiDict({
                "nombre": "Code",
                "descripcion": "Desc",
                "requerido": "optional",
                "html_externo": "<div></div>",
            })
        )
        assert form.validate()

        # External Link Recurso
        form = CursoRecursoExternalLink(
            MultiDict({
                "nombre": "Link",
                "descripcion": "Desc",
                "requerido": "optional",
                "url": "https://example.com",
            })
        )
        assert form.validate()

        # Slides Recurso
        form = CursoRecursoSlides(
            MultiDict({
                "nombre": "Slides",
                "descripcion": "Desc",
                "requerido": "optional",
                "notes": "beige",
            })
        )
        assert form.validate()


def test_curso_library_file_form(app):
    """Test CursoLibraryFileForm validation."""
    with app.test_request_context():
        form = CursoLibraryFileForm(
            MultiDict({
                "nombre": "Guia de estudio",
                "descripcion": "Descripción de la guia de estudio",
            })
        )
        assert form.validate()

        form = CursoLibraryFileForm(MultiDict({}))
        assert not form.validate()


def test_slideshow_and_slide_forms(app):
    """Test SlideShowForm and SlideForm validation."""
    with app.test_request_context():
        # SlideShow
        form = SlideShowForm(
            MultiDict({
                "nombre": "Slides",
                "descripcion": "Desc",
                "theme": "night",
            })
        )
        assert form.validate()

        form = SlideShowForm(MultiDict({}))
        assert not form.validate()

        # Slide
        slide_form = SlideForm(
            MultiDict({
                "title": "Slide 1",
                "content": "Content",
                "order": "1",
            })
        )
        assert slide_form.validate()

        slide_form = SlideForm(MultiDict({}))
        assert not slide_form.validate()


def test_curso_recurso_meet(app):
    """Test CursoRecursoMeet validation."""
    with app.test_request_context():
        form = CursoRecursoMeet(
            MultiDict({
                "nombre": "Meet",
                "descripcion": "Desc",
                "requerido": "required",
                "url": "https://zoom.us/meet",
                "notes": "zoom",
                "fecha": "2026-12-01",
                "hora_inicio": "10:00",
                "hora_fin": "11:00",
            })
        )
        assert form.validate()


def test_categoria_and_etiqueta_forms(app):
    """Test CategoriaForm and EtiquetaForm validation."""
    with app.test_request_context():
        # Categoria
        form_cat = CategoriaForm(
            MultiDict({
                "nombre": "Programación",
                "descripcion": "Cursos de código",
            })
        )
        assert form_cat.validate()

        # Etiqueta
        form_tag = EtiquetaForm(
            MultiDict({
                "nombre": "Python",
                "descripcion": "Etiqueta Python",
                "color": "#ff0000",
            })
        )
        assert form_tag.validate()


def test_programa_form(app):
    """Test ProgramaForm validation."""
    with app.test_request_context():
        form = ProgramaForm(
            MultiDict({
                "nombre": "Master en Python",
                "descripcion": "Curso completo",
                "codigo": "M-PY",
                "precio": "99.99",
                "publico": "y",
                "estado": "open",
                "promocionado": "y",
                "pagado": "y",
                "certificado": "y",
            })
        )
        assert form.validate()


def test_recurso_form(app):
    """Test RecursoForm validation."""
    with app.test_request_context():
        form = RecursoForm(
            MultiDict({
                "nombre": "Guia de Docker",
                "descripcion": "Docker",
                "codigo": "G-DOCKER",
                "precio": "9.99",
                "publico": "y",
                "promocionado": "y",
                "tipo": "ebook",
                "pagado": "y",
            })
        )
        assert form.validate()


def test_user_form(app):
    """Test UserForm validation."""
    with app.test_request_context():
        form = UserForm(
            MultiDict({
                "nombre": "Alex",
                "apellido": "Smith",
                "correo_electronico": "alex@example.com",
                "genero": "male",
                "titulo": "ing",
            })
        )
        assert form.validate()


def test_messages_forms(app):
    """Test MessageThreadForm, MessageReplyForm, MessageReportForm validation."""
    with app.test_request_context():
        # Thread
        thread_form = MessageThreadForm(
            MultiDict({
                "subject": "Duda",
                "content": "Tengo una duda",
                "course_id": "PY-101",
            })
        )
        assert thread_form.validate()

        # Reply
        reply_form = MessageReplyForm(
            MultiDict({
                "content": "Respuesta",
                "thread_id": "1",
            })
        )
        assert reply_form.validate()

        # Report
        report_form = MessageReportForm(
            MultiDict({
                "reason": "Spam",
                "thread_id": "1",
            })
        )
        assert report_form.validate()


def test_certificate_form_and_text_area_no_escape(app):
    """Test CertificateForm and TextAreaNoEscape custom widget."""
    with app.test_request_context():
        form = CertificateForm(
            MultiDict({
                "titulo": "Certificado",
                "descripcion": "Otorgado por NOW LMS",
                "habilitado": "y",
                "publico": "y",
                "html": "<h1>Certificado</h1>",
                "css": "h1 { color: red; }",
                "tipo": "course",
            })
        )
        assert form.validate()

        # Test widget rendering
        widget = TextAreaNoEscape()
        rendered = widget(form.html)
        assert "<h1>Certificado</h1>" in rendered
        assert "<textarea" in rendered


def test_adsense_form(app):
    """Test AdSenseForm validation."""
    with app.test_request_context():
        form = AdSenseForm(
            MultiDict({
                "meta_tag": "<meta>",
                "pub_id": "pub-12345",
                "show_ads": "y",
            })
        )
        assert form.validate()


def test_paypal_form(app):
    """Test PayaplForm validation."""
    with app.test_request_context():
        form = PayaplForm(
            MultiDict({
                "habilitado": "y",
                "sandbox": "y",
                "paypal_id": "id123",
                "paypal_sandbox": "sandbox123",
            })
        )
        assert form.validate()


def test_emit_certificate_form(app):
    """Test EmitCertificateForm validation."""
    with app.test_request_context():
        form = EmitCertificateForm(
            MultiDict({
                "usuario": "user1",
                "content_type": "course",
                "curso": "PY-101",
                "master_class": "",
                "template": "tpl1",
                "nota": "95.00",
            })
        )
        form.usuario.choices = [("user1", "User 1")]
        form.curso.choices = [("PY-101", "Python")]
        form.master_class.choices = [("", "Select Class")]
        form.template.choices = [("tpl1", "Template 1")]
        if not form.validate():
            print("EmitCertificateForm validation errors:", form.errors)
        assert form.validate()


def test_password_forms(app):
    """Test CheckMailForm, ChangePasswordForm, ForgotPasswordForm, ResetPasswordForm validation."""
    with app.test_request_context():
        # CheckMail
        assert CheckMailForm(MultiDict({"email": "alex@example.com"})).validate()

        # ChangePassword
        change_form = ChangePasswordForm(
            MultiDict({
                "current_password": "old",
                "new_password": "new",
                "confirm_password": "new",
            })
        )
        assert change_form.validate()

        # ForgotPassword
        assert ForgotPasswordForm(MultiDict({"email": "alex@example.com"})).validate()

        # ResetPassword
        reset_form = ResetPasswordForm(
            MultiDict({
                "new_password": "new",
                "confirm_password": "new",
            })
        )
        assert reset_form.validate()


def test_pago_form(app):
    """Test PagoForm validation."""
    with app.test_request_context():
        form = PagoForm(
            MultiDict({
                "nombre": "Juan",
                "apellido": "Perez",
                "correo_electronico": "juan@example.com",
                "direccion1": "Calle 123",
                "pais": "Guatemala",
                "provincia": "Guatemala",
                "codigo_postal": "01001",
            })
        )
        assert form.validate()


def test_evaluation_forms(app):
    """Test EvaluationForm, QuestionForm, QuestionOptionForm, EvaluationReopenRequestForm validation."""
    with app.test_request_context():
        # Evaluation
        form_eval = EvaluationForm(
            MultiDict({
                "title": "Examen Final",
                "description": "Examen de salida",
                "is_exam": "y",
                "passing_score": "75.0",
                "max_attempts": "3",
            })
        )
        assert form_eval.validate()

        # Question
        form_q = QuestionForm(
            MultiDict({
                "text": "¿Qué es Python?",
                "type": "multiple",
                "explanation": "Lenguaje interpretado",
            })
        )
        assert form_q.validate()

        # Option
        form_opt = QuestionOptionForm(
            MultiDict({
                "text": "Un lenguaje de programación",
                "is_correct": "y",
            })
        )
        assert form_opt.validate()

        # Reopen
        form_reopen = EvaluationReopenRequestForm(
            MultiDict({
                "justification_text": "Se cortó la luz",
            })
        )
        assert form_reopen.validate()


def test_foro_mensaje_forms(app):
    """Test ForoMensajeForm and ForoMensajeRespuestaForm validation."""
    with app.test_request_context():
        # Mensaje
        form_msg = ForoMensajeForm(MultiDict({"contenido": "Duda con el ejercicio"}))
        assert form_msg.validate()

        # Respuesta
        form_resp = ForoMensajeRespuestaForm(MultiDict({"contenido": "Revisa el video de nuevo"}))
        assert form_resp.validate()


def test_announcements_forms(app):
    """Test AnnouncementForm, GlobalAnnouncementForm, CourseAnnouncementForm validation."""
    with app.test_request_context():
        # Announcement
        form_ann = AnnouncementForm(
            MultiDict({
                "nombre": "Importante",
                "descripcion": "Mensaje",
                "title": "Importante",
                "message": "No habrá clases mañana",
                "expires_at": "2026-12-01",
            })
        )
        assert form_ann.validate()

        # Global
        form_glob = GlobalAnnouncementForm(
            MultiDict({
                "nombre": "Global",
                "descripcion": "Msg",
                "title": "Mantenimiento",
                "message": "Mantenimiento del servidor",
                "is_sticky": "y",
            })
        )
        assert form_glob.validate()

        # Course
        form_course = CourseAnnouncementForm(
            MultiDict({
                "title": "Examen mañana",
                "message": "Estudien mucho",
                "course_id": "PY-101",
            })
        )
        form_course.course_id.choices = [("PY-101", "Python")]
        assert form_course.validate()


def test_coupon_forms(app):
    """Test CouponForm and CouponApplicationForm validation."""
    with app.test_request_context():
        # Coupon
        form_coupon = CouponForm(
            MultiDict({
                "code": "DESCUENTO50",
                "discount_type": "percentage",
                "discount_value": "50.0",
                "max_uses": "100",
                "expires_at": "2026-12-31",
            })
        )
        assert form_coupon.validate()

        # Coupon Application
        form_app = CouponApplicationForm(MultiDict({"coupon_code": "DESCUENTO50"}))
        assert form_app.validate()


def test_blog_forms(app):
    """Test BlogPostForm, BlogTagForm, BlogCommentForm validation."""
    with app.test_request_context():
        # Post
        form_post = BlogPostForm(
            MultiDict({
                "nombre": "Post 1",
                "descripcion": "Desc",
                "title": "Bienvenidos",
                "content": "Este es nuestro primer post",
                "allow_comments": "y",
                "tags": "bienvenida, intro",
                "status": "published",
            })
        )
        assert form_post.validate()

        # Tag
        form_tag = BlogTagForm(
            MultiDict({
                "nombre": "Tech",
                "descripcion": "Desc",
                "name": "Tech",
            })
        )
        assert form_tag.validate()

        # Comment
        form_comment = BlogCommentForm(
            MultiDict({
                "nombre": "Comentario",
                "descripcion": "Desc",
                "content": "Excelente artículo",
            })
        )
        assert form_comment.validate()


def test_admin_enrollment_forms(app):
    """Test AdminCourseEnrollmentForm and AdminProgramEnrollmentForm validation."""
    with app.test_request_context():
        # Course enrollment
        form_course = AdminCourseEnrollmentForm(
            MultiDict({
                "student_username": "estudiante1",
                "bypass_payment": "y",
                "notes": "Inscripción especial",
            })
        )
        assert form_course.validate()

        # Program enrollment
        form_prog = AdminProgramEnrollmentForm(
            MultiDict({
                "student_username": "estudiante1",
                "bypass_payment": "y",
                "notes": "Inscripción especial",
            })
        )
        assert form_prog.validate()


def test_footer_and_api_key_forms(app):
    """Test EnlaceUtilForm, CustomPageFooterForm, and ExternalApiKeyForm validation."""
    with app.test_request_context():
        # EnlaceUtil
        form_link = EnlaceUtilForm(
            MultiDict({
                "titulo": "Google",
                "url": "https://google.com",
                "orden": "1",
                "activo": "y",
            })
        )
        assert form_link.validate()

        # CustomPageFooter
        form_footer = CustomPageFooterForm(MultiDict({"mostrar_en_footer": "y"}))
        assert form_footer.validate()

        # ExternalApiKey
        form_key = ExternalApiKeyForm(
            MultiDict({
                "name": "Integracion 1",
                "allowed_origin": "*",
                "notes": "API Key",
            })
        )
        assert form_key.validate()


def test_masterclass_forms(app, db_session):
    """Test MasterClassForm and MasterClassEnrollmentForm validation and custom rules."""
    from now_lms.db import Certificado
    from now_lms.forms.masterclass import MasterClassForm, MasterClassEnrollmentForm

    # Add a mock certificate template to database so it gets loaded on form initialization
    with app.app_context():
        cert = Certificado(
            code="test-cert-code",
            titulo="Certificado Test",
            habilitado=True,
            html="test",
            css="test",
            tipo="course",
        )
        db_session.add(cert)
        db_session.commit()

    with app.test_request_context():
        tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")

        # 1. Valid MasterClassForm without certification
        form = MasterClassForm(
            MultiDict({
                "title": "AWS Cloud Practitioner",
                "description_public": "Clase magistral completa sobre AWS con laboratorios.",
                "description_private": "La clave de acceso zoom es 123456.",
                "date": tomorrow,
                "start_time": "14:00",
                "end_time": "16:00",
                "platform_name": "Zoom",
                "platform_url": "https://zoom.us/j/123",
                "is_certificate": "",
                "diploma_template_id": "",
            })
        )
        assert form.validate()

        # 2. Valid MasterClassForm with certification
        form_cert = MasterClassForm(
            MultiDict({
                "title": "AWS Cloud Practitioner",
                "description_public": "Clase magistral completa sobre AWS con laboratorios.",
                "description_private": "La clave de acceso zoom es 123456.",
                "date": tomorrow,
                "start_time": "14:00",
                "end_time": "16:00",
                "platform_name": "Zoom",
                "platform_url": "https://zoom.us/j/123",
                "is_certificate": "y",
                "diploma_template_id": "test-cert-code",
            })
        )
        assert form_cert.validate()

        # 3. Invalid: end_time before/equal start_time
        form_invalid_time = MasterClassForm(
            MultiDict({
                "title": "AWS Cloud Practitioner",
                "description_public": "Clase magistral completa sobre AWS con laboratorios.",
                "date": tomorrow,
                "start_time": "14:00",
                "end_time": "13:00",
                "platform_name": "Zoom",
                "platform_url": "https://zoom.us/j/123",
            })
        )
        assert not form_invalid_time.validate()
        assert "end_time" in form_invalid_time.errors
        assert "posterior" in form_invalid_time.errors["end_time"][0].lower()

        # 4. Invalid: date in the past
        past_date = (datetime.date.today() - datetime.timedelta(days=5)).strftime("%Y-%m-%d")
        form_invalid_date = MasterClassForm(
            MultiDict({
                "title": "AWS Cloud Practitioner",
                "description_public": "Clase magistral completa sobre AWS con laboratorios.",
                "date": past_date,
                "start_time": "14:00",
                "end_time": "16:00",
                "platform_name": "Zoom",
                "platform_url": "https://zoom.us/j/123",
            })
        )
        assert not form_invalid_date.validate()
        assert "date" in form_invalid_date.errors
        assert "pasado" in form_invalid_date.errors["date"][0].lower()

        # 5. Invalid: certificate requested but no template chosen
        form_no_template = MasterClassForm(
            MultiDict({
                "title": "AWS Cloud Practitioner",
                "description_public": "Clase magistral completa sobre AWS con laboratorios.",
                "date": tomorrow,
                "start_time": "14:00",
                "end_time": "16:00",
                "platform_name": "Zoom",
                "platform_url": "https://zoom.us/j/123",
                "is_certificate": "y",
                "diploma_template_id": "",
            })
        )
        assert not form_no_template.validate()
        assert "diploma_template_id" in form_no_template.errors
        assert "requerida" in form_no_template.errors["diploma_template_id"][0].lower()

        # 6. Test MasterClassEnrollmentForm
        enroll_form = MasterClassEnrollmentForm()
        assert enroll_form.validate()
