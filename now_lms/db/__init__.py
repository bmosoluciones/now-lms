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

"""Definición de base de datos."""

# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------
from datetime import date, datetime, timezone
from typing import Self

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------
from cuid2 import Cuid
from flask import current_app, has_request_context
from flask_login import UserMixin, current_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event, select
from sqlalchemy.exc import SQLAlchemyError

__all__ = ["select", "database", "UserMixin", "eliminar_base_de_datos_segura", "UserEvent"]


# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
# pylint: disable=E1101


# < --------------------------------------------------------------------------------------------- >
# Definición principal de la clase del ORM.
database: SQLAlchemy = SQLAlchemy()


def eliminar_base_de_datos_segura():
    """Elimina todas las tablas de la base de datos de forma segura.

    Se asegura de cerrar cualquier sesión activa y evitar estados inconsistentes.
    Debe ejecutarse dentro del contexto de aplicación Flask.
    """
    app = current_app._get_current_object()  # Accede a la app real si es un proxy

    try:
        # Cierra cualquier sesión activa antes de manipular el esquema
        database.session.remove()

        # Ejecutar drop_all en el engine de la app
        database.drop_all()

        # Dispose of the engine to ensure all connections are closed
        database.engine.dispose()
    except SQLAlchemyError as e:
        # Si hay un error, hacer rollback para evitar inconsistencia
        database.session.rollback()
        app.logger.error(f"Error eliminando la base de datos: {e}")
        raise
    finally:
        # Cierra la sesión para asegurar limpieza
        database.session.close()


# < --------------------------------------------------------------------------------------------- >
# Base de datos relacional

MAXIMO_RESULTADOS_EN_CONSULTA_PAGINADA: int = 10
LLAVE_FORANEA_CURSO: str = "curso.codigo"
LLAVE_FORANEA_USUARIO: str = "usuario.usuario"
LLAVE_FORANEA_SECCION: str = "curso_seccion.id"
LLAVE_FORANEA_RECURSO: str = "curso_recurso.id"
LLAVE_FORANEA_PREGUNTA: str = "curso_recurso_pregunta.id"
LLAVE_FORANEA_FORO_MENSAJE: str = "foro_mensaje.id"
LLAVE_FORANEA_PROGRAMA: str = "programa.id"
LLAVE_FORANEA_CERTIFICADO: str = "certificado.code"

# Cascade constants
CASCADE_ALL_DELETE_ORPHAN: str = "all, delete-orphan"
FOREIGN_KEY_EVALUATION_ID: str = "evaluation.id"


def generador_de_codigos_unicos() -> str:
    """Genera codigo unicos basados en ULID."""
    from ulid import ULID

    codigo_aleatorio = ULID()
    id_unico = str(codigo_aleatorio)

    return id_unico


def generador_codigos_unicos_cuid() -> str:
    """Generado codigos unicos con CUID2."""
    CUID_GENERATOR: Cuid = Cuid(length=10)
    return CUID_GENERATOR.generate()


def utc_now() -> datetime:
    """Generate timezone-aware UTC datetime.

    Replacement for deprecated datetime.utcnow() with timezone-aware alternative.
    """
    return datetime.now(timezone.utc)


# pylint: disable=too-few-public-methods
# pylint: disable=no-member
class BaseTabla:
    """Columnas estandar para todas las tablas de la base de datos."""

    # Pistas de auditoria comunes a todas las tablas.
    id = database.Column(
        database.String(26), primary_key=True, nullable=False, index=True, default=generador_de_codigos_unicos
    )
    timestamp = database.Column(database.DateTime, default=utc_now, nullable=False)
    creado = database.Column(database.Date, default=date.today, nullable=False)
    creado_por = database.Column(database.String(150), nullable=True)
    modificado = database.Column(database.DateTime, onupdate=utc_now, nullable=True)
    modificado_por = database.Column(database.String(150), nullable=True)

    def validate_user_references(self):
        """Validate that audit fields reference existing users or set them to None."""
        from now_lms.db import Usuario

        # Use no_autoflush to prevent recursive flush during validation
        with database.session.no_autoflush:
            # Check if users are being created in this transaction to skip validation
            new_user_ids = {instance.usuario for instance in database.session.new if isinstance(instance, Usuario)}

            # Validate creado_por
            if self.creado_por:
                # Skip validation if user is being created in same transaction
                if self.creado_por not in new_user_ids:
                    user_exists = database.session.execute(
                        database.select(Usuario).filter_by(usuario=self.creado_por)
                    ).scalar_one_or_none()
                    if not user_exists:
                        self.creado_por = None

            # Validate modificado_por
            if self.modificado_por:
                # Skip validation if user is being created in same transaction
                if self.modificado_por not in new_user_ids:
                    user_exists = database.session.execute(
                        database.select(Usuario).filter_by(usuario=self.modificado_por)
                    ).scalar_one_or_none()
                    if not user_exists:
                        self.modificado_por = None


class SystemInfo(database.Model):
    """Información basica sobre la instalación."""

    param = database.Column(database.String(20), primary_key=True, nullable=False, index=True)
    val = database.Column(database.String(100))


class Usuario(UserMixin, database.Model, BaseTabla):
    """Una entidad con acceso al sistema."""

    # Información Básica
    __table_args__ = (database.UniqueConstraint("usuario", name="id_usuario_unico"),)
    __table_args__ = (database.UniqueConstraint("correo_electronico", name="correo_usuario_unico"),)
    # Info de sistema
    usuario = database.Column(database.String(150), nullable=False, index=True, unique=True)
    acceso = database.Column(database.LargeBinary(), nullable=False)
    nombre = database.Column(database.String(100))
    apellido = database.Column(database.String(100))
    correo_electronico = database.Column(database.String(150))
    correo_electronico_verificado = database.Column(database.Boolean(), default=False)
    tipo = database.Column(database.String(20))  # Puede ser: admin, user, instructor, moderator
    activo = database.Column(database.Boolean())
    # Perfil personal
    visible = database.Column(database.Boolean())
    titulo = database.Column(database.String(15))
    genero = database.Column(database.String(10))
    nacimiento = database.Column(database.Date())
    bio = database.Column(database.String(500))
    # Registro de actividad
    fecha_alta = database.Column(database.DateTime, default=utc_now)
    ultimo_acceso = database.Column(database.DateTime)
    # Social
    url = database.Column(database.String(100))
    linkedin = database.Column(database.String(50))
    facebook = database.Column(database.String(50))
    twitter = database.Column(database.String(50))
    github = database.Column(database.String(500))
    youtube = database.Column(database.String(500))
    # Relaciones
    relacion_grupo = database.relationship("UsuarioGrupoMiembro")
    # Imagen de perfil
    portada = database.Column(database.Boolean())


class UsuarioGrupo(database.Model, BaseTabla):
    """Grupo de Usuarios."""

    activo = database.Column(database.Boolean(), index=True)
    nombre = database.Column(database.String(50), nullable=False)
    descripcion = database.Column(database.String(500), nullable=False)
    tutor = database.Column(database.String(20), database.ForeignKey(LLAVE_FORANEA_USUARIO))


class UsuarioGrupoMiembro(database.Model, BaseTabla):
    """Grupo de Usuarios."""

    grupo = database.Column(database.String(26), database.ForeignKey("usuario_grupo.id"))
    usuario = database.Column(database.String(150), database.ForeignKey(LLAVE_FORANEA_USUARIO))


class UsuarioGrupoTutor(UsuarioGrupoMiembro):
    """Asigna un usuario como tutor de un curso."""


class Curso(database.Model, BaseTabla):
    """Un curso es la base del aprendizaje en NOW LMS."""

    __table_args__ = (database.UniqueConstraint("codigo", name="curso_codigo_unico"),)
    # Información básica
    nombre = database.Column(database.String(150), nullable=False)
    codigo = database.Column(database.String(20), unique=True, index=True)
    descripcion_corta = database.Column(database.String(280), nullable=False)
    descripcion = database.Column(database.String(1000), nullable=False)
    portada = database.Column(database.Boolean())
    portada_ext = database.Column(database.String(5))
    nivel = database.Column(database.Integer(), default=False)  # 0: Introductorio, 1: Principiante, 2: Intermedio, 3: Avanzado
    duracion = database.Column(database.Integer())
    # Estado de publicación
    estado = database.Column(database.String(9), nullable=False, index=True)  # draft, open, closed, finalized
    publico = database.Column(database.Boolean())
    # Modalidad
    modalidad = database.Column(database.String(10))  # self_paced, time_based, live
    # Configuración del foro
    foro_habilitado = database.Column(database.Boolean(), default=False, nullable=False)
    # Disponibilidad de cupos
    limitado = database.Column(database.Boolean())
    capacidad = database.Column(database.Integer())
    # Fechas de inicio y fin
    fecha_inicio = database.Column(database.Date())
    fecha_fin = database.Column(database.Date())
    # Información de marketing
    promocionado = database.Column(database.Boolean())
    fecha_promocionado = database.Column(database.DateTime, nullable=True)
    # Información de pago
    pagado = database.Column(database.Boolean())
    auditable = database.Column(database.Boolean())
    precio = database.Column(database.Numeric(precision=10, scale=2))
    certificado = database.Column(database.Boolean())
    plantilla_certificado = database.Column(
        database.String(25), database.ForeignKey(LLAVE_FORANEA_CERTIFICADO), nullable=True, index=True, default="default"
    )

    def validar_foro_habilitado(self):
        """Valida que el foro solo pueda habilitarse en cursos no self-paced."""
        if self.foro_habilitado and self.modalidad == "self_paced":
            return False, "El foro no puede habilitarse en cursos con modalidad self-paced"
        return True, ""

    @database.validates("foro_habilitado")
    def validate_foro_habilitado(self, key, value):
        """Validación de SQLAlchemy para foro_habilitado."""
        if value and self.modalidad == "self_paced":
            raise ValueError("El foro no puede habilitarse en cursos con modalidad self-paced")
        return value

    def is_self_paced(self):
        """Retorna True si el curso es self-paced."""
        return self.modalidad == "self_paced"

    def puede_habilitar_foro(self):
        """Retorna True si el foro puede ser habilitado para este curso."""
        return not self.is_self_paced()


class CursoRecursoDescargable(database.Model, BaseTabla):
    """Los cursos pueden tener recursos descargables incluidos."""

    curso = database.Column(database.String(20), database.ForeignKey(LLAVE_FORANEA_CURSO), nullable=False, index=True)
    recurso = database.Column(database.String(10), database.ForeignKey("recurso.codigo"), nullable=False, index=True)


class CursoSeccion(database.Model, BaseTabla):
    """Los cursos tienen secciones para dividir el contenido en secciones logicas."""

    curso = database.Column(database.String(20), database.ForeignKey(LLAVE_FORANEA_CURSO), nullable=False, index=True)
    rel_curso = database.relationship("Curso", foreign_keys=curso)
    nombre = database.Column(database.String(100), nullable=False)
    descripcion = database.Column(database.String(250), nullable=False)
    indice = database.Column(database.Integer(), index=True)
    # 0: Borrador, 1: Publico
    estado = database.Column(database.Boolean())


class CursoRecurso(database.Model, BaseTabla):
    """Una sección de un curso consta de una serie de recursos."""

    indice = database.Column(database.Integer(), index=True)
    seccion = database.Column(database.String(26), database.ForeignKey(LLAVE_FORANEA_SECCION), nullable=False, index=True)
    curso = database.Column(database.String(20), database.ForeignKey(LLAVE_FORANEA_CURSO), nullable=False, index=True)
    rel_curso = database.relationship("Curso")
    nombre = database.Column(database.String(150), nullable=False)
    descripcion = database.Column(database.Text(), nullable=False)
    # Uno de: mp3, pdf, meet, img, text, html, link, slides, youtube
    tipo = database.Column(database.String(150), nullable=False)
    # required: Requerido, optional: Optional, substitute: Alternativo
    requerido = database.Column(database.String(10), default="required")
    url = database.Column(database.String(250), unique=False)
    fecha = database.Column(database.Date())
    hora_inicio = database.Column(database.Time())
    hora_fin = database.Column(database.Time())
    publico = database.Column(database.Boolean())
    base_doc_url = database.Column(database.String(50), unique=False)
    doc = database.Column(database.String(50), unique=False)
    ext = database.Column(database.String(5), unique=True)
    text = database.Column(database.Text())
    external_code = database.Column(database.Text())
    notes = database.Column(database.String(20))


class CursoRecursoAvance(database.Model, BaseTabla):
    """Un control del avance de cada usuario de tipo estudiante de los recursos de un curso.

    Para que un curso de considere finalizado un alumno debe completar todos los recursos requeridos.
    """

    curso = database.Column(database.String(20), database.ForeignKey(LLAVE_FORANEA_CURSO), nullable=False, index=True)
    recurso = database.Column(database.String(32), database.ForeignKey(LLAVE_FORANEA_RECURSO), nullable=False, index=True)
    usuario = database.Column(database.String(150), database.ForeignKey(LLAVE_FORANEA_USUARIO), nullable=False, index=True)
    completado = database.Column(database.Boolean(), default=False)
    requerido = database.Column(database.String(10))


class CursoUsuarioAvance(database.Model, BaseTabla):
    """Control del avance de un usuario en un curso."""

    curso = database.Column(database.String(20), database.ForeignKey(LLAVE_FORANEA_CURSO), nullable=False, index=True)
    usuario = database.Column(database.String(150), database.ForeignKey(LLAVE_FORANEA_USUARIO), nullable=False, index=True)
    recursos_requeridos = database.Column(database.Integer, default=0)  # Cantidad de recursos requeridos
    recursos_completados = database.Column(database.Integer, default=0)  # Cantidad de recursos completados
    avance = database.Column(database.Float(asdecimal=True), default=0.0)  # Porcentaje de avance del curso
    completado = database.Column(database.Boolean(), default=False)  # Indica si el curso ha sido completado
    fecha_inicio = database.Column(database.DateTime, default=utc_now)  # Fecha de inicio del curso


class CursoRecursoPregunta(database.Model, BaseTabla):
    """Los recursos de tipo prueba estan conformados por una serie de preguntas que el usario debe contestar."""

    __table_args__ = (database.UniqueConstraint("codigo", name="curso_recurso_pregunta_unico"),)
    indice = database.Column(database.Integer())
    codigo = database.Column(database.String(32), unique=False)
    curso = database.Column(database.String(20), database.ForeignKey(LLAVE_FORANEA_CURSO), nullable=False, index=True)
    seccion = database.Column(database.String(32), database.ForeignKey(LLAVE_FORANEA_SECCION), nullable=False, index=True)
    recurso = database.Column(database.String(32), database.ForeignKey(LLAVE_FORANEA_RECURSO), nullable=False, index=True)
    # Tipo:
    # boleano: Verdadero o Falso
    # seleccionar: El usuario debe seleccionar una de varias opciónes.
    # texto: El alunmo debe desarrollar una respuesta, normalmente el instructor/moderador
    # debera calificar la respuesta
    tipo = database.Column(database.String(15))
    # Es posible que el instructor decida modificar las evaluaciones, pero se debe conservar el historial.
    evaluar = database.Column(database.Boolean())


class CursoRecursoPreguntaOpcion(database.Model, BaseTabla):
    """Las preguntas tienen opciones."""

    curso = database.Column(database.String(20), database.ForeignKey(LLAVE_FORANEA_CURSO), nullable=False, index=True)
    recurso = database.Column(database.String(32), database.ForeignKey(LLAVE_FORANEA_RECURSO), nullable=False, index=True)
    pregunta = database.Column(database.String(32), database.ForeignKey(LLAVE_FORANEA_PREGUNTA), nullable=False, index=True)
    texto = database.Column(database.String(50))
    boleano = database.Column(database.Boolean())
    correcta = database.Column(database.Boolean())


class CursoRecursoPreguntaRespuesta(database.Model, BaseTabla):
    """Respuestas de los usuarios a las preguntas del curso."""

    curso = database.Column(database.String(20), database.ForeignKey(LLAVE_FORANEA_CURSO), nullable=False, index=True)
    recurso = database.Column(database.String(32), database.ForeignKey(LLAVE_FORANEA_RECURSO), nullable=False, index=True)
    pregunta = database.Column(database.String(32), database.ForeignKey(LLAVE_FORANEA_PREGUNTA), nullable=False, index=True)
    usuario = database.Column(database.String(150), database.ForeignKey(LLAVE_FORANEA_USUARIO), nullable=False, index=True)
    texto = database.Column(database.String(500))
    boleano = database.Column(database.Boolean())
    correcta = database.Column(database.Boolean())
    nota = database.Column(database.Float(asdecimal=True))


class CursoRecursoConsulta(database.Model, BaseTabla):
    """Un usuario debe poder hacer consultas a su tutor/moderador."""

    curso = database.Column(database.String(20), database.ForeignKey(LLAVE_FORANEA_CURSO), nullable=False)
    recurso = database.Column(database.String(32), database.ForeignKey(LLAVE_FORANEA_RECURSO), nullable=False)
    usuario = database.Column(database.String(150), database.ForeignKey(LLAVE_FORANEA_USUARIO), nullable=False)
    pregunta = database.Column(database.String(500))
    respuesta = database.Column(database.String(500))


class SlideShowResource(database.Model, BaseTabla):
    """Una presentación basada en reveal.js."""

    __tablename__ = "slide_show_resource"

    course_id = database.Column(database.String(20), database.ForeignKey(LLAVE_FORANEA_CURSO), nullable=False, index=True)
    title = database.Column(database.String(150), nullable=False)
    theme = database.Column(database.String(20), nullable=False, default="simple")

    # Relationships
    course = database.relationship("Curso", foreign_keys=[course_id])
    slides = database.relationship(
        "Slide", back_populates="slide_show", cascade=CASCADE_ALL_DELETE_ORPHAN, order_by="Slide.order"
    )


class Slide(database.Model, BaseTabla):
    """Una diapositiva individual dentro de una presentación."""

    __tablename__ = "slide"

    slide_show_id = database.Column(
        database.String(26), database.ForeignKey("slide_show_resource.id"), nullable=False, index=True
    )
    title = database.Column(database.String(150), nullable=False)
    content = database.Column(database.Text, nullable=False)
    order = database.Column(database.Integer, nullable=False, default=1)

    # Relationships
    slide_show = database.relationship("SlideShowResource", back_populates="slides")


# Keep legacy models for backward compatibility but mark as deprecated
class CursoRecursoSlideShow(database.Model, BaseTabla):
    """DEPRECATED: Una presentación basada en reveal.js - use SlideShowResource instead."""

    __table_args__ = (database.UniqueConstraint("codigo", name="codigo_slideshow_unico"),)
    titulo = database.Column(database.String(100), nullable=False)
    descripcion = database.Column(database.String(250), nullable=False)
    codigo = database.Column(database.String(32), unique=False)
    curso = database.Column(database.String(20), database.ForeignKey(LLAVE_FORANEA_CURSO), nullable=False, index=True)
    recurso = database.Column(database.String(32), database.ForeignKey(LLAVE_FORANEA_RECURSO), nullable=False, index=True)
    usuario = database.Column(database.String(20), database.ForeignKey(LLAVE_FORANEA_USUARIO), nullable=False)


class CursoRecursoSlides(database.Model, BaseTabla):
    """DEPRECATED: Una diapositiva individual - use Slide instead."""

    titulo = database.Column(database.String(100), nullable=False)
    texto = database.Column(database.String(500), nullable=False)
    indice = database.Column(database.Integer())
    curso = database.Column(database.String(20), database.ForeignKey(LLAVE_FORANEA_CURSO), nullable=False)
    recurso = database.Column(database.String(32), database.ForeignKey(LLAVE_FORANEA_RECURSO), nullable=False)
    slide_show = database.Column(database.String(32), database.ForeignKey("curso_recurso_slide_show.codigo"), nullable=False)


class Files(database.Model, BaseTabla):
    """Listado de archivos que se han cargado a la aplicacion."""

    archivo = database.Column(database.String(100), nullable=False)
    tipo = database.Column(database.String(15), nullable=False)
    hashtag = database.Column(database.String(50), nullable=False)
    url = database.Column(database.String(100), nullable=False)


class DocenteCurso(database.Model, BaseTabla):
    """Uno o mas usuario de tipo intructor pueden estar a cargo de un curso."""

    curso = database.Column(database.String(20), database.ForeignKey(LLAVE_FORANEA_CURSO), nullable=False, index=True)
    usuario = database.Column(database.String(150), database.ForeignKey(LLAVE_FORANEA_USUARIO), nullable=False, index=True)
    vigente = database.Column(database.Boolean())


class ModeradorCurso(database.Model, BaseTabla):
    """Uno o mas usuario de tipo moderator pueden estar a cargo de un curso."""

    curso = database.Column(database.String(20), database.ForeignKey(LLAVE_FORANEA_CURSO), nullable=False, index=True)
    usuario = database.Column(database.String(150), database.ForeignKey(LLAVE_FORANEA_USUARIO), nullable=False, index=True)
    vigente = database.Column(database.Boolean())


class EstudianteCurso(database.Model, BaseTabla):
    """Uno o mas usuario de tipo user pueden estar a cargo de un curso."""

    curso = database.Column(database.String(20), database.ForeignKey(LLAVE_FORANEA_CURSO), nullable=False, index=True)
    usuario = database.Column(database.String(150), database.ForeignKey(LLAVE_FORANEA_USUARIO), nullable=False, index=True)
    vigente = database.Column(database.Boolean())
    pago = database.Column(database.String(26), database.ForeignKey("pago.id"), nullable=True, index=True)


class Configuracion(database.Model, BaseTabla):
    """Repositorio Central para la configuración de la aplicacion."""

    titulo = database.Column(database.String(150), nullable=False)
    descripcion = database.Column(database.String(500), nullable=False)
    moneda = database.Column(database.String(5))
    # Send a message to the user to verify his email
    verify_user_by_email = database.Column(database.Boolean())
    # Internationalization
    lang = database.Column(database.String(5), default="en")
    time_zone = database.Column(database.String(50), default="UTC")
    r = database.Column(database.LargeBinary())

    # Navigation configuration options
    enable_programs = database.Column(database.Boolean(), default=False, nullable=False)
    enable_masterclass = database.Column(database.Boolean(), default=False, nullable=False)
    enable_resources = database.Column(database.Boolean(), default=False, nullable=False)
    enable_blog = database.Column(database.Boolean(), default=False, nullable=False)


class Style(database.Model, BaseTabla):
    """Configuration for site appearance and theming."""

    theme = database.Column(database.String(15))
    custom_logo = database.Column(database.Boolean())
    custom_logo_ext = database.Column(database.String(5))
    custom_favicon = database.Column(database.Boolean())  # png


class MailConfig(database.Model, BaseTabla):
    """E-mail settings."""

    MAIL_SERVER = database.Column(database.String(100))
    MAIL_PORT = database.Column(database.String(6))
    MAIL_USERNAME = database.Column(database.String(100))
    MAIL_PASSWORD = database.Column(database.LargeBinary())
    MAIL_USE_TLS = database.Column(database.Boolean())
    MAIL_USE_SSL = database.Column(database.Boolean())
    MAIL_DEFAULT_SENDER = database.Column(database.String(100))
    MAIL_DEFAULT_SENDER_NAME = database.Column(database.String(100))
    email_verificado = database.Column(database.Boolean())


class Categoria(database.Model, BaseTabla):
    """Permite Clasificar los cursos por categoria."""

    nombre = database.Column(database.String(100), nullable=False)
    descripcion = database.Column(database.String(250), nullable=False)


class CategoriaCurso(database.Model, BaseTabla):
    """Listado de Cursos Permite Clasificar los cursos por categoria."""

    curso = database.Column(database.String(20), database.ForeignKey(LLAVE_FORANEA_CURSO), nullable=False, index=True)
    categoria = database.Column(database.String(26), database.ForeignKey("categoria.id"), nullable=False, index=True)
    relacion_curso = database.relationship("Curso", foreign_keys=curso)
    relacion_categoria = database.relationship("Categoria", foreign_keys=categoria)


class Etiqueta(database.Model, BaseTabla):
    """Permite Clasificar los cursos por etiquetas."""

    nombre = database.Column(database.String(20), nullable=False)
    color = database.Column(database.String(10), nullable=False)


class EtiquetaCurso(database.Model, BaseTabla):
    """Listado de Cursos Permite Clasificar los cursos por categoria."""

    curso = database.Column(database.String(20), database.ForeignKey(LLAVE_FORANEA_CURSO), nullable=False, index=True)
    etiqueta = database.Column(database.String(26), database.ForeignKey("etiqueta.id"), nullable=False, index=True)
    relacion_curso = database.relationship("Curso", foreign_keys=curso)
    relacion_etiqueta = database.relationship("Etiqueta", foreign_keys=etiqueta)


class Programa(database.Model, BaseTabla):
    """Un programa agrupa una serie de cursos."""

    __table_args__ = (database.UniqueConstraint("codigo", name="codigo_programa_unico"),)
    nombre = database.Column(database.String(20), nullable=False)
    codigo = database.Column(database.String(10), nullable=False, unique=True)
    descripcion = database.Column(database.String(200))
    texto = database.Column(database.String(1500))
    pagado = database.Column(database.Boolean())
    precio = database.Column(database.Float())
    publico = database.Column(database.Boolean())
    # draft, open, closed
    estado = database.Column(database.String(20))
    logo = database.Column(database.Boolean(), default=False)
    promocionado = database.Column(database.Boolean())
    fecha_promocionado = database.Column(database.DateTime, nullable=True)
    certificado = database.Column(database.Boolean(), default=False)
    plantilla_certificado = database.Column(
        database.String(25), database.ForeignKey(LLAVE_FORANEA_CERTIFICADO), nullable=True, index=True, default="default"
    )


class ProgramaCurso(database.Model, BaseTabla):
    """Cursos en un programa."""

    curso = database.Column(database.String(20), database.ForeignKey(LLAVE_FORANEA_CURSO), nullable=False, index=True)
    programa = database.Column(database.String(10), database.ForeignKey("programa.codigo"), nullable=False, index=True)
    relacion_curso = database.relationship("Curso", foreign_keys=curso)
    relacion_programa = database.relationship("Programa", foreign_keys=programa)


class ProgramaEstudiante(database.Model, BaseTabla):
    """Cursos en un programa."""

    usuario = database.Column(database.String(150), database.ForeignKey(LLAVE_FORANEA_USUARIO), nullable=False, index=True)
    programa = database.Column(database.String(26), database.ForeignKey(LLAVE_FORANEA_PROGRAMA), nullable=False, index=True)
    relacion_usuario = database.relationship("Usuario", foreign_keys=usuario)
    relacion_programa = database.relationship("Programa", foreign_keys=programa)


class CategoriaPrograma(database.Model, BaseTabla):
    """Permite clasificar los programas por categoria."""

    programa = database.Column(database.String(26), database.ForeignKey(LLAVE_FORANEA_PROGRAMA), nullable=False, index=True)
    categoria = database.Column(database.String(26), database.ForeignKey("categoria.id"), nullable=False, index=True)
    relacion_programa = database.relationship("Programa", foreign_keys=programa)
    relacion_categoria = database.relationship("Categoria", foreign_keys=categoria)


class EtiquetaPrograma(database.Model, BaseTabla):
    """Permite clasificar los programas por etiquetas."""

    programa = database.Column(database.String(26), database.ForeignKey(LLAVE_FORANEA_PROGRAMA), nullable=False, index=True)
    etiqueta = database.Column(database.String(26), database.ForeignKey("etiqueta.id"), nullable=False, index=True)
    relacion_programa = database.relationship("Programa", foreign_keys=programa)
    relacion_etiqueta = database.relationship("Etiqueta", foreign_keys=etiqueta)


class Recurso(database.Model, BaseTabla):
    """Un recurso descargable."""

    __table_args__ = (database.UniqueConstraint("codigo", name="codigo_recurso_unico"),)
    nombre = database.Column(database.String(50), nullable=False)
    codigo = database.Column(database.String(10), nullable=False, index=True, unique=True)
    tipo = database.Column(database.String(15))
    descripcion = database.Column(database.String(500))
    precio = database.Column(database.Float())
    publico = database.Column(database.Boolean())
    logo = database.Column(database.Boolean(), default=False)
    file_name = database.Column(database.String(200))
    promocionado = database.Column(database.Boolean())
    fecha_promocionado = database.Column(database.DateTime, nullable=True)
    usuario = database.Column(database.String(20), database.ForeignKey(LLAVE_FORANEA_USUARIO))
    pagado = database.Column(database.Boolean())


class Certificado(database.Model, BaseTabla):
    """Plantilla para generar un certificado."""

    code = database.Column(database.String(25), unique=True, index=True)
    titulo = database.Column(database.String(50))
    descripcion = database.Column(database.String(500))
    html = database.Column(database.Text())
    css = database.Column(database.Text())
    habilitado = database.Column(database.Boolean())
    publico = database.Column(database.Boolean())
    usuario = database.Column(database.String(20), database.ForeignKey(LLAVE_FORANEA_USUARIO))


class Certificacion(database.Model, BaseTabla):
    """Una certificación generada a un estudiante."""

    usuario = database.Column(database.String(26), database.ForeignKey(LLAVE_FORANEA_USUARIO), nullable=False, index=True)
    curso = database.Column(database.String(20), database.ForeignKey(LLAVE_FORANEA_CURSO), nullable=True, index=True)
    master_class_id = database.Column(database.String(26), database.ForeignKey("master_classes.id"), nullable=True, index=True)
    certificado = database.Column(
        database.String(26), database.ForeignKey(LLAVE_FORANEA_CERTIFICADO), nullable=False, index=True
    )
    fecha = database.Column(database.Date, default=date.today, nullable=False)
    nota = database.Column(database.Numeric(precision=5, scale=2))

    # Relationships
    master_class_rel = database.relationship("MasterClass", foreign_keys=[master_class_id])

    def get_content_info(self):
        """Get the course or master class information for this certificate."""
        if self.curso:
            return database.session.execute(database.select(Curso).filter_by(codigo=self.curso)).first()[0]
        elif self.master_class_id:
            return database.session.execute(database.select(MasterClass).filter_by(id=self.master_class_id)).first()[0]
        return None

    def get_content_type(self):
        """Return 'course' or 'masterclass' depending on the content type."""
        if self.curso:
            return "course"
        elif self.master_class_id:
            return "masterclass"
        return None


class CertificacionPrograma(database.Model, BaseTabla):
    """Una certificación generada a un estudiante por completar un programa."""

    usuario = database.Column(database.String(26), database.ForeignKey(LLAVE_FORANEA_USUARIO), nullable=False, index=True)
    programa = database.Column(database.String(26), database.ForeignKey(LLAVE_FORANEA_PROGRAMA), nullable=False, index=True)
    certificado = database.Column(
        database.String(26), database.ForeignKey(LLAVE_FORANEA_CERTIFICADO), nullable=False, index=True
    )
    fecha = database.Column(database.Date, default=date.today, nullable=False)

    # Relationships
    relacion_usuario = database.relationship("Usuario", foreign_keys=usuario)
    relacion_programa = database.relationship("Programa", foreign_keys=programa)
    relacion_certificado = database.relationship("Certificado", foreign_keys=certificado)

    def get_cursos_completados(self):
        """Get list of completed courses for this program certificate."""
        from now_lms.db.tools import obtener_cursos_completados_en_programa_por_id

        return obtener_cursos_completados_en_programa_por_id(self.usuario, self.programa)


class Mensaje(database.Model, BaseTabla):
    """Mensajes de usuarios - DEPRECATED: Use MessageThread and Message instead."""

    usuario = database.Column(database.String(26), database.ForeignKey(LLAVE_FORANEA_USUARIO), index=True)
    curso = database.Column(database.String(20), database.ForeignKey(LLAVE_FORANEA_CURSO), index=True)
    recurso = database.Column(database.String(10), database.ForeignKey(LLAVE_FORANEA_RECURSO), index=True)
    cerrado = database.Column(database.Boolean(), default=False)
    publico = database.Column(database.Boolean(), default=False)
    titulo = database.Column(database.String(100))
    texto = database.Column(database.String(1000))
    parent = database.Column(database.String(26), database.ForeignKey("mensaje.id"), nullable=True, index=True)


class MessageThread(database.Model, BaseTabla):
    """Message threads for course communication between students and instructors/moderators."""

    course_id = database.Column(database.String(20), database.ForeignKey(LLAVE_FORANEA_CURSO), nullable=False)
    student_id = database.Column(database.String(150), database.ForeignKey(LLAVE_FORANEA_USUARIO), nullable=False)
    status = database.Column(database.String(10), default="open", nullable=False)  # open, fixed, closed
    closed_at = database.Column(database.DateTime, nullable=True)

    # Relationships
    course = database.relationship("Curso", foreign_keys=[course_id])
    student = database.relationship("Usuario", foreign_keys=[student_id])
    messages = database.relationship("Message", backref="thread", lazy="dynamic", cascade=CASCADE_ALL_DELETE_ORPHAN)


class Message(database.Model, BaseTabla):
    """Individual messages within a thread."""

    thread_id = database.Column(database.String(26), database.ForeignKey("message_thread.id"), nullable=False)
    sender_id = database.Column(database.String(150), database.ForeignKey(LLAVE_FORANEA_USUARIO), nullable=False)
    content = database.Column(database.Text, nullable=False)
    read_at = database.Column(database.DateTime, nullable=True)
    is_reported = database.Column(database.Boolean(), default=False, nullable=False)
    reported_reason = database.Column(database.Text, nullable=True)

    # Relationships
    sender = database.relationship("Usuario", foreign_keys=[sender_id])


class ForoMensaje(database.Model, BaseTabla):
    """Mensajes del foro de un curso."""

    curso_id = database.Column(database.String(20), database.ForeignKey(LLAVE_FORANEA_CURSO), nullable=False, index=True)
    usuario_id = database.Column(database.String(150), database.ForeignKey(LLAVE_FORANEA_USUARIO), nullable=False, index=True)
    parent_id = database.Column(database.String(26), database.ForeignKey("foro_mensaje.id"), nullable=True, index=True)
    contenido = database.Column(database.Text, nullable=False)
    fecha_creacion = database.Column(database.DateTime, default=utc_now, nullable=False)
    fecha_modificacion = database.Column(database.DateTime, onupdate=utc_now, nullable=True)
    estado = database.Column(database.String(10), default="abierto", nullable=False)  # abierto, cerrado

    # Relationships
    curso = database.relationship("Curso", foreign_keys=[curso_id])
    usuario = database.relationship("Usuario", foreign_keys=[usuario_id])
    parent = database.relationship("ForoMensaje", remote_side="ForoMensaje.id", backref="replies")

    def is_thread_open(self):
        """Retorna True si el hilo está abierto para nuevas respuestas."""
        if self.parent_id:
            # Es una respuesta, verificar el mensaje padre
            return self.parent.estado == "abierto"
        else:
            # Es un hilo principal
            return self.estado == "abierto"

    def is_course_forum_active(self):
        """Retorna True si el foro del curso está activo."""
        return self.curso.foro_habilitado and self.curso.estado != "finalizado"

    def can_reply(self):
        """Retorna True si se puede responder a este mensaje."""
        return self.is_thread_open() and self.is_course_forum_active()

    def get_thread_root(self) -> Self:
        """Retorna el mensaje raíz del hilo."""
        if self.parent_id:
            return self.parent.get_thread_root()
        return self

    @classmethod
    def close_all_for_course(cls, curso_codigo):
        """Cierra todos los mensajes del foro cuando un curso se finaliza."""
        mensajes = database.session.execute(database.select(cls).filter_by(curso_id=curso_codigo)).scalars().all()
        for mensaje in mensajes:
            mensaje.estado = "cerrado"
        database.session.commit()


class PagosConfig(database.Model):
    """Configuración de pagos."""

    id = database.Column(
        database.String(26), primary_key=True, nullable=False, index=True, default=generador_de_codigos_unicos
    )


class AdSense(database.Model):
    """Configuration for Google AdSense integration."""

    id = database.Column(database.Integer, primary_key=True)
    meta_tag = database.Column(database.String(100))
    meta_tag_include = database.Column(database.Boolean(), default=False)
    pub_id = database.Column(database.String(20))
    add_code = database.Column(database.String(500))
    show_ads = database.Column(database.Boolean(), default=False)

    # Specific ad size codes
    add_leaderboard = database.Column(database.Text())  # 728x90
    add_medium_rectangle = database.Column(database.Text())  # 300x250
    add_large_rectangle = database.Column(database.Text())  # 336x280
    add_mobile_banner = database.Column(database.Text())  # 300x50
    add_wide_skyscraper = database.Column(database.Text())  # 160x600
    add_skyscraper = database.Column(database.Text())  # 120x600
    add_large_skyscraper = database.Column(database.Text())  # 300x600
    add_billboard = database.Column(database.Text())  # 970x250


class PaypalConfig(database.Model):
    """Configuration for PayPal payment integration."""

    id = database.Column(database.Integer, primary_key=True)
    enable = database.Column(database.Boolean(), default=False)
    sandbox = database.Column(database.Boolean(), default=False)
    paypal_id = database.Column(database.String(200))
    paypal_sandbox = database.Column(database.String(200))
    paypal_secret = database.Column(database.LargeBinary())
    paypal_sandbox_secret = database.Column(database.LargeBinary())


class Pago(database.Model):
    """Registro de pagos."""

    id = database.Column(
        database.String(26), primary_key=True, nullable=False, index=True, default=generador_de_codigos_unicos
    )
    usuario = database.Column(database.String(150), database.ForeignKey(LLAVE_FORANEA_USUARIO), nullable=False, index=True)
    curso = database.Column(database.String(20), database.ForeignKey(LLAVE_FORANEA_CURSO), nullable=False, index=True)
    moneda = database.Column(database.String(5))  # Ejemplo: USD, EUR, CRC
    monto = database.Column(database.Numeric(asdecimal=True))
    fecha = database.Column(database.DateTime, default=utc_now)
    estado = database.Column(database.String(20), default="pending")  # pending, completed, failed
    metodo = database.Column(database.String(20))  # paypal, stripe, bank_transfer
    referencia = database.Column(database.String(100), nullable=True)  # Referencia de pago
    descripcion = database.Column(database.String(500), nullable=True)  # Descripción del pago
    audit = database.Column(database.Boolean(), default=False)
    # Información de facturación
    nombre = database.Column(database.String(100), nullable=False)
    apellido = database.Column(database.String(100), nullable=False)
    correo_electronico = database.Column(database.String(150), nullable=False)
    direccion1 = database.Column(database.String(200), nullable=True)
    direccion2 = database.Column(database.String(200), nullable=True)
    pais = database.Column(database.String(100), nullable=True)
    provincia = database.Column(database.String(100), nullable=True)
    codigo_postal = database.Column(database.String(20), nullable=True)


# ---------------------------------------------------------------------------------------
# Evaluations System Models
# ---------------------------------------------------------------------------------------


class Evaluation(database.Model, BaseTabla):
    """An evaluation (quiz/exam) associated with a course section."""

    __tablename__ = "evaluation"

    section_id = database.Column(database.String(26), database.ForeignKey(LLAVE_FORANEA_SECCION), nullable=False, index=True)
    title = database.Column(database.String(200), nullable=False)
    description = database.Column(database.String(1000), nullable=True)
    is_exam = database.Column(database.Boolean(), default=False)
    passing_score = database.Column(database.Float(), nullable=False, default=70.0)
    max_attempts = database.Column(database.Integer(), nullable=True)  # null means unlimited
    available_until = database.Column(database.DateTime(), nullable=True)
    reopened_at = database.Column(database.DateTime(), nullable=True)
    reopened_for_user_id = database.Column(database.String(150), database.ForeignKey(LLAVE_FORANEA_USUARIO), nullable=True)
    penalty_percent = database.Column(database.Float(), nullable=True, default=0.0)

    # Relationships
    section = database.relationship("CursoSeccion", foreign_keys=[section_id])
    questions = database.relationship("Question", back_populates="evaluation", cascade=CASCADE_ALL_DELETE_ORPHAN)
    attempts = database.relationship("EvaluationAttempt", back_populates="evaluation", cascade=CASCADE_ALL_DELETE_ORPHAN)


class Question(database.Model, BaseTabla):
    """A question within an evaluation."""

    __tablename__ = "question"

    evaluation_id = database.Column(
        database.String(26), database.ForeignKey(FOREIGN_KEY_EVALUATION_ID), nullable=False, index=True
    )
    type = database.Column(database.String(20), nullable=False)  # 'multiple' or 'boolean'
    text = database.Column(database.String(1000), nullable=False)
    explanation = database.Column(database.String(1000), nullable=True)
    order = database.Column(database.Integer(), nullable=False, default=1)

    # Relationships
    evaluation = database.relationship("Evaluation", back_populates="questions")
    options = database.relationship("QuestionOption", back_populates="question", cascade=CASCADE_ALL_DELETE_ORPHAN)
    answers = database.relationship("Answer", back_populates="question", cascade=CASCADE_ALL_DELETE_ORPHAN)


class QuestionOption(database.Model, BaseTabla):
    """An option for a multiple choice question."""

    __tablename__ = "question_option"

    question_id = database.Column(database.String(26), database.ForeignKey("question.id"), nullable=False, index=True)
    text = database.Column(database.String(500), nullable=False)
    is_correct = database.Column(database.Boolean(), default=False)

    # Relationships
    question = database.relationship("Question", back_populates="options")


class EvaluationAttempt(database.Model, BaseTabla):
    """A student's attempt at an evaluation."""

    __tablename__ = "evaluation_attempt"

    evaluation_id = database.Column(
        database.String(26), database.ForeignKey(FOREIGN_KEY_EVALUATION_ID), nullable=False, index=True
    )
    user_id = database.Column(database.String(150), database.ForeignKey(LLAVE_FORANEA_USUARIO), nullable=False, index=True)
    score = database.Column(database.Float(), nullable=True)  # null until submitted
    passed = database.Column(database.Boolean(), nullable=True)  # null until graded
    started_at = database.Column(database.DateTime(), default=utc_now)
    submitted_at = database.Column(database.DateTime(), nullable=True)
    was_late = database.Column(database.Boolean(), default=False)

    # Relationships
    evaluation = database.relationship("Evaluation", back_populates="attempts")
    user = database.relationship("Usuario", foreign_keys=[user_id])
    answers = database.relationship("Answer", back_populates="attempt", cascade=CASCADE_ALL_DELETE_ORPHAN)


class Answer(database.Model, BaseTabla):
    """A student's answer to a question in an evaluation attempt."""

    __tablename__ = "answer"

    attempt_id = database.Column(database.String(26), database.ForeignKey("evaluation_attempt.id"), nullable=False, index=True)
    question_id = database.Column(database.String(26), database.ForeignKey("question.id"), nullable=False, index=True)
    selected_option_ids = database.Column(database.Text(), nullable=True)  # JSON array of UUIDs

    # Relationships
    attempt = database.relationship("EvaluationAttempt", back_populates="answers")
    question = database.relationship("Question", back_populates="answers")


# ---------------------------------------------------------------------------------------
# Coupon System Models
# ---------------------------------------------------------------------------------------


class Coupon(database.Model, BaseTabla):
    """Discount coupons for paid courses."""

    __tablename__ = "coupon"

    course_id = database.Column(database.String(20), database.ForeignKey(LLAVE_FORANEA_CURSO), nullable=False, index=True)
    code = database.Column(database.String(50), nullable=False, index=True)
    discount_type = database.Column(database.String(20), nullable=False)  # 'percentage' or 'fixed'
    discount_value = database.Column(database.Float(), nullable=False)
    max_uses = database.Column(database.Integer(), nullable=True)  # null means unlimited
    expires_at = database.Column(database.DateTime(), nullable=True)  # null means no expiration
    current_uses = database.Column(database.Integer(), nullable=False, default=0)
    created_by = database.Column(database.String(150), database.ForeignKey(LLAVE_FORANEA_USUARIO), nullable=False, index=True)

    # Constraints
    __table_args__ = (database.UniqueConstraint("course_id", "code", name="unique_coupon_per_course"),)

    # Relationships
    course = database.relationship("Curso", foreign_keys=[course_id])
    creator = database.relationship("Usuario", foreign_keys=[created_by])

    def is_valid(self):
        """Check if coupon is valid (not expired and under usage limit)."""
        from datetime import datetime

        # Check expiration
        if self.expires_at and datetime.now() > self.expires_at:
            return False, "Cupón expirado"

        # Check usage limit
        current_uses = self.current_uses or 0
        if self.max_uses and current_uses >= self.max_uses:
            return False, "Cupón ha alcanzado el límite de usos"

        return True, ""

    def calculate_discount(self, original_price):
        """Calculate the discount amount for a given price."""
        if self.discount_type == "percentage":
            discount = float(original_price) * (self.discount_value / 100)
        else:  # fixed
            discount = min(self.discount_value, float(original_price))

        return min(discount, float(original_price))  # Cannot discount more than original price

    def calculate_final_price(self, original_price):
        """Calculate the final price after applying the coupon."""
        discount = self.calculate_discount(original_price)
        final_price = float(original_price) - discount
        return max(0, final_price)  # Price cannot be negative


class EvaluationReopenRequest(database.Model, BaseTabla):
    """A student's request to reopen an evaluation after exhausting attempts."""

    __tablename__ = "evaluation_reopen_request"

    user_id = database.Column(database.String(150), database.ForeignKey(LLAVE_FORANEA_USUARIO), nullable=False, index=True)
    evaluation_id = database.Column(
        database.String(26), database.ForeignKey(FOREIGN_KEY_EVALUATION_ID), nullable=False, index=True
    )
    justification_text = database.Column(database.String(1000), nullable=False)
    status = database.Column(database.String(20), default="pending")  # 'pending', 'approved', 'rejected'
    reviewed_at = database.Column(database.DateTime(), nullable=True)
    approved_by = database.Column(database.String(150), database.ForeignKey(LLAVE_FORANEA_USUARIO), nullable=True)

    # Relationships
    user = database.relationship("Usuario", foreign_keys=[user_id])
    evaluation = database.relationship("Evaluation")
    reviewer = database.relationship("Usuario", foreign_keys=[approved_by])


class Announcement(database.Model, BaseTabla):
    """Sistema de anuncios para administradores e instructores."""

    __tablename__ = "announcement"

    # Información básica del anuncio
    title = database.Column(database.String(255), nullable=False)
    message = database.Column(database.Text, nullable=False)  # Formato Markdown

    # Relaciones
    course_id = database.Column(database.String(20), database.ForeignKey(LLAVE_FORANEA_CURSO), nullable=True, index=True)
    created_by_id = database.Column(
        database.String(150), database.ForeignKey(LLAVE_FORANEA_USUARIO), nullable=False, index=True
    )

    # Fechas
    expires_at = database.Column(database.DateTime, nullable=True)  # Fecha de expiración opcional

    # Configuración
    is_sticky = database.Column(database.Boolean, default=False, nullable=False)  # Anuncio destacado

    # Relationships
    course = database.relationship("Curso", foreign_keys=[course_id])
    created_by = database.relationship("Usuario", foreign_keys=[created_by_id])

    def is_global(self):
        """Retorna True si es un anuncio global (sin curso asignado)."""
        return self.course_id is None

    def is_course_announcement(self):
        """Retorna True si es un anuncio de curso específico."""
        return self.course_id is not None

    def is_active(self):
        """Retorna True si el anuncio está activo (no ha expirado)."""
        if self.expires_at is None:
            return True
        from datetime import datetime

        return datetime.now() <= self.expires_at

    def __repr__(self):
        return f"<Announcement {self.title}>"


# Master Class System Models
class MasterClass(database.Model, BaseTabla):
    """Master Class live sessions with optional certification and payment."""

    __tablename__ = "master_classes"

    # Basic information
    title = database.Column(database.String(150), nullable=False)
    slug = database.Column(database.String(200), unique=True, nullable=False, index=True)
    description_public = database.Column(database.Text, nullable=False)
    description_private = database.Column(database.Text, nullable=True)

    # Scheduling
    date = database.Column(database.Date, nullable=False)
    start_time = database.Column(database.Time, nullable=False)
    end_time = database.Column(database.Time, nullable=False)

    # Payment configuration
    is_paid = database.Column(database.Boolean, default=False, nullable=False)
    price = database.Column(database.Numeric(precision=10, scale=2), nullable=True)
    early_discount = database.Column(database.Numeric(precision=5, scale=2), nullable=True)  # Percentage
    discount_deadline = database.Column(database.DateTime, nullable=True)

    # Platform information
    platform_name = database.Column(database.String(50), nullable=False)  # Zoom, Google Meet, etc.
    platform_url = database.Column(database.String(500), nullable=False)  # Join link

    # Certification
    is_certificate = database.Column(database.Boolean, default=False, nullable=False)
    diploma_template_id = database.Column(
        database.String(26), database.ForeignKey(LLAVE_FORANEA_CERTIFICADO), nullable=True, index=True
    )

    # Media
    video_recording_url = database.Column(database.String(500), nullable=True)  # After event
    image_path = database.Column(database.String(200), nullable=True)  # Cover image

    # Ownership
    instructor_id = database.Column(
        database.String(150), database.ForeignKey(LLAVE_FORANEA_USUARIO), nullable=False, index=True
    )

    # Relationships
    instructor = database.relationship("Usuario", foreign_keys=[instructor_id])
    diploma_template = database.relationship("Certificado", foreign_keys=[diploma_template_id])
    enrollments = database.relationship(
        "MasterClassEnrollment", back_populates="master_class", cascade=CASCADE_ALL_DELETE_ORPHAN
    )

    def __repr__(self):
        return f"<MasterClass {self.title}>"

    def is_upcoming(self):
        """Check if the master class is in the future."""
        from datetime import datetime

        event_datetime = datetime.combine(self.date, self.start_time)
        return event_datetime > datetime.now()

    def is_ongoing(self):
        """Check if the master class is currently happening."""
        from datetime import datetime

        now = datetime.now()
        event_date = self.date
        start_datetime = datetime.combine(event_date, self.start_time)
        end_datetime = datetime.combine(event_date, self.end_time)
        return start_datetime <= now <= end_datetime

    def is_finished(self):
        """Check if the master class has ended."""
        from datetime import datetime

        end_datetime = datetime.combine(self.date, self.end_time)
        return end_datetime < datetime.now()

    def get_effective_price(self):
        """Get the current effective price considering early discount."""
        # Master Classes are now always free for marketing purposes
        return 0


class MasterClassEnrollment(database.Model, BaseTabla):
    """User enrollment in a Master Class."""

    __tablename__ = "master_class_enrollments"

    master_class_id = database.Column(
        database.String(26), database.ForeignKey("master_classes.id"), nullable=False, index=True
    )
    user_id = database.Column(database.String(150), database.ForeignKey(LLAVE_FORANEA_USUARIO), nullable=False, index=True)
    is_confirmed = database.Column(database.Boolean, default=False, nullable=False)
    payment_id = database.Column(database.String(26), database.ForeignKey("pago.id"), nullable=True, index=True)
    enrolled_at = database.Column(database.DateTime, default=utc_now, nullable=False)

    # Constraints
    __table_args__ = (database.UniqueConstraint("master_class_id", "user_id", name="unique_enrollment_per_user"),)

    # Relationships
    master_class = database.relationship("MasterClass", back_populates="enrollments")
    user = database.relationship("Usuario", foreign_keys=[user_id])
    payment = database.relationship("Pago", foreign_keys=[payment_id])

    def __repr__(self):
        return f"<MasterClassEnrollment {self.user_id} in {self.master_class_id}>"

    def is_access_granted(self):
        """Check if user has access to private content."""
        # Since Master Classes are now free, just check if confirmed
        return self.is_confirmed


# Blog feature models
blog_post_tags = database.Table(
    "blog_post_tags",
    database.Column("post_id", database.String(26), database.ForeignKey("blog_post.id"), primary_key=True),
    database.Column("tag_id", database.String(26), database.ForeignKey("blog_tag.id"), primary_key=True),
)


class BlogPost(database.Model, BaseTabla):
    """Blog post model."""

    __tablename__ = "blog_post"

    title = database.Column(database.String(200), nullable=False)
    slug = database.Column(database.String(250), unique=True, nullable=False, index=True)
    content = database.Column(database.Text, nullable=False)
    author_id = database.Column(database.String(150), database.ForeignKey(LLAVE_FORANEA_USUARIO), nullable=False, index=True)
    status = database.Column(
        database.String(20), default="draft", nullable=False, index=True
    )  # draft, pending, published, banned
    allow_comments = database.Column(database.Boolean(), default=True, nullable=False)
    published_at = database.Column(database.DateTime(), nullable=True)
    comment_count = database.Column(database.Integer(), default=0, nullable=False)

    # Relationships
    author = database.relationship("Usuario", backref="blog_posts")
    tags = database.relationship("BlogTag", secondary=blog_post_tags, backref="posts")
    comments = database.relationship("BlogComment", backref="post", cascade=CASCADE_ALL_DELETE_ORPHAN)


class BlogTag(database.Model, BaseTabla):
    """Blog tag model."""

    __tablename__ = "blog_tag"

    name = database.Column(database.String(50), unique=True, nullable=False, index=True)
    slug = database.Column(database.String(60), unique=True, nullable=False, index=True)


class BlogComment(database.Model, BaseTabla):
    """Blog comment model."""

    __tablename__ = "blog_comment"

    post_id = database.Column(database.String(26), database.ForeignKey("blog_post.id"), nullable=False, index=True)
    user_id = database.Column(database.String(150), database.ForeignKey(LLAVE_FORANEA_USUARIO), nullable=False, index=True)
    content = database.Column(database.Text, nullable=False)
    status = database.Column(database.String(20), default="visible", nullable=False, index=True)  # visible, flagged, banned

    # Relationships
    user = database.relationship("Usuario", backref="blog_comments")


class UserEvent(database.Model, BaseTabla):
    """User events for calendar functionality - tracks key dates for students."""

    __tablename__ = "user_events"

    user_id = database.Column(database.String(150), database.ForeignKey(LLAVE_FORANEA_USUARIO), nullable=False, index=True)
    course_id = database.Column(database.String(20), database.ForeignKey(LLAVE_FORANEA_CURSO), nullable=False, index=True)
    section_id = database.Column(database.String(26), database.ForeignKey(LLAVE_FORANEA_SECCION), nullable=True, index=True)
    resource_id = database.Column(database.String(26), database.ForeignKey(LLAVE_FORANEA_RECURSO), nullable=True, index=True)
    evaluation_id = database.Column(
        database.String(26), database.ForeignKey(FOREIGN_KEY_EVALUATION_ID), nullable=True, index=True
    )
    resource_type = database.Column(database.String(20), nullable=False, index=True)  # meet, evaluation
    title = database.Column(database.String(255), nullable=False)
    description = database.Column(database.Text, nullable=True)
    start_time = database.Column(database.DateTime, nullable=False, index=True)
    end_time = database.Column(database.DateTime, nullable=True)
    timezone = database.Column(database.String(50), nullable=True)
    status = database.Column(database.String(20), default="pending", nullable=False, index=True)  # pending, ongoing, completed

    # Relationships
    user = database.relationship("Usuario", backref="calendar_events")
    course = database.relationship("Curso", backref="user_events")
    section = database.relationship("CursoSeccion", backref="user_events")
    resource = database.relationship("CursoRecurso", backref="user_events")
    evaluation = database.relationship("Evaluation", backref="user_events")


# Event listeners for audit field population and validation
@event.listens_for(database.session, "before_flush")
def populate_audit_fields_before_flush(session, flush_context, instances):
    """Automatically populate audit fields for BaseTabla instances before flushing."""
    # Get current user context if available
    current_user_id = None
    if has_request_context() and current_user.is_authenticated:
        current_user_id = current_user.usuario

    current_time = utc_now()
    current_date = current_time.date()

    # Handle new instances
    for instance in session.new:
        if isinstance(instance, BaseTabla):
            # Set creation audit fields if not already set
            if instance.creado_por is None and current_user_id:
                instance.creado_por = current_user_id
            # creado field has a default, but ensure it's set to today if somehow null
            if instance.creado is None:
                instance.creado = current_date

    # Handle modified instances
    for instance in session.dirty:
        if isinstance(instance, BaseTabla):
            # Set modification audit fields
            if current_user_id:
                instance.modificado_por = current_user_id
            # The modificado field has onupdate=utc_now, but ensure it's set
            instance.modificado = current_time


@event.listens_for(database.session, "before_commit")
def validate_audit_fields_before_commit(session):
    """Validate that audit fields reference existing users before committing."""
    for instance in session.new:
        if isinstance(instance, BaseTabla):
            instance.validate_user_references()

    for instance in session.dirty:
        if isinstance(instance, BaseTabla):
            instance.validate_user_references()


@event.listens_for(database.session, "before_commit")
def populate_audit_fields_before_commit(session):
    """Automatically populate audit fields for BaseTabla instances before committing."""
    # Get current user context if available
    if has_request_context() and current_user.is_authenticated:
        pass  # User context available for future use

    # Track which instances had manually set audit fields before validation
    manually_set_creado_por = {}
    manually_set_modificado_por = {}

    # Store manually set audit fields before validation potentially clears them
    for instance in session.new:
        if isinstance(instance, BaseTabla) and instance.creado_por is not None:
            manually_set_creado_por[id(instance)] = instance.creado_por

    for instance in session.dirty:
        if isinstance(instance, BaseTabla) and instance.modificado_por is not None:
            manually_set_modificado_por[id(instance)] = instance.modificado_por
