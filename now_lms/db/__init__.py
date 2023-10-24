# Copyright 2022 - 2023 BMO Soluciones, S.A.
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

"""Definición de base de datos."""

# ---------------------------------------------------------------------------------------
# Libreria estandar
# ---------------------------------------------------------------------------------------


# ---------------------------------------------------------------------------------------
# Librerias de terceros
# ---------------------------------------------------------------------------------------
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy

# ---------------------------------------------------------------------------------------
# Recursos locales
# ---------------------------------------------------------------------------------------
# pylint: disable=E1101


# < --------------------------------------------------------------------------------------------- >
# Definición principal de la clase del ORM.
database: SQLAlchemy = SQLAlchemy()

# < --------------------------------------------------------------------------------------------- >
# Base de datos relacional

MAXIMO_RESULTADOS_EN_CONSULTA_PAGINADA: int = 10
LLAVE_FORANEA_CURSO: str = "curso.codigo"
LLAVE_FORANEA_USUARIO: str = "usuario.usuario"
LLAVE_FORANEA_SECCION: str = "curso_seccion.id"
LLAVE_FORANEA_RECURSO: str = "curso_recurso.id"
LLAVE_FORANEA_PREGUNTA: str = "curso_recurso_pregunta.id"


def generador_de_codigos_unicos() -> str:
    """Genera codigo unicos basados en ULID."""
    from ulid import ULID

    codigo_aleatorio = ULID()
    id_unico = str(codigo_aleatorio)

    return id_unico


# pylint: disable=too-few-public-methods
# pylint: disable=no-member
class BaseTabla:
    """Columnas estandar para todas las tablas de la base de datos."""

    # Pistas de auditoria comunes a todas las tablas.
    id = database.Column(
        database.String(26), primary_key=True, nullable=False, index=True, default=generador_de_codigos_unicos
    )
    creado = database.Column(database.DateTime, default=database.func.now(), nullable=False)
    creado_por = database.Column(database.String(15), nullable=True)
    modificado = database.Column(database.DateTime, onupdate=database.func.now(), nullable=True)
    modificado_por = database.Column(database.String(15), nullable=True)


class Usuario(UserMixin, database.Model, BaseTabla):  # type: ignore[name-defined]
    """Una entidad con acceso al sistema."""

    # Información Básica
    __table_args__ = (database.UniqueConstraint("usuario", name="id_usuario_unico"),)
    __table_args__ = (database.UniqueConstraint("correo_electronico", name="correo_usuario_unico"),)
    # Info de sistema
    usuario = database.Column(database.String(20), nullable=False, index=True, unique=True)
    acceso = database.Column(database.LargeBinary(), nullable=False)
    nombre = database.Column(database.String(100))
    apellido = database.Column(database.String(100))
    correo_electronico = database.Column(database.String(100))
    correo_electronico_verificado = database.Column(database.Boolean(), default=False)
    tipo = database.Column(database.String(20))  # Puede ser: admin, user, instructor, moderator
    activo = database.Column(database.Boolean())
    # Perfil personal
    visible = database.Column(database.Boolean())
    titulo = database.Column(database.String(15))
    genero = database.Column(database.String(10))  # Puede ser: male, female, other, none
    nacimiento = database.Column(database.Date())
    bio = database.Column(database.String(500))
    # Registro de actividad
    fecha_alta = database.Column(database.DateTime, default=database.func.now())
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


class UsuarioGrupo(database.Model, BaseTabla):  # type: ignore[name-defined]
    """Grupo de Usuarios"""

    activo = database.Column(database.Boolean(), index=True)
    nombre = database.Column(database.String(50), nullable=False)
    descripcion = database.Column(database.String(500), nullable=False)
    tutor = database.Column(database.String(20), database.ForeignKey(LLAVE_FORANEA_USUARIO))


class UsuarioGrupoMiembro(database.Model, BaseTabla):  # type: ignore[name-defined]
    """Grupo de Usuarios"""

    grupo = database.Column(database.String(26), database.ForeignKey("usuario_grupo.id"))
    usuario = database.Column(database.String(20), database.ForeignKey(LLAVE_FORANEA_USUARIO))


class UsuarioGrupoTutor(UsuarioGrupoMiembro):  # type: ignore[name-defined]
    """Asigna un usuario como tutor de un curso"""


class Curso(database.Model, BaseTabla):  # type: ignore[name-defined]
    """Un curso es la base del aprendizaje en NOW LMS."""

    __table_args__ = (database.UniqueConstraint("codigo", name="curso_codigo_unico"),)
    nombre = database.Column(database.String(150), nullable=False)
    codigo = database.Column(database.String(10), unique=True, index=True)
    descripcion = database.Column(database.String(1000), nullable=False)
    # draft, open, closed
    estado = database.Column(database.String(10), nullable=False, index=True)
    # mooc
    publico = database.Column(database.Boolean(), index=True)
    certificado = database.Column(database.Boolean())
    auditable = database.Column(database.Boolean())
    precio = database.Column(database.Numeric())
    capacidad = database.Column(database.Integer())
    fecha_inicio = database.Column(database.Date())
    fecha_fin = database.Column(database.Date())
    duracion = database.Column(database.Integer())
    portada = database.Column(database.Boolean())
    nivel = database.Column(database.Integer())
    promocionado = database.Column(database.Boolean())
    fecha_promocionado = database.Column(database.DateTime, nullable=True)


class CursoRecursoDescargable(database.Model, BaseTabla):  # type: ignore[name-defined]
    """Los cursos pueden tener recursos descargables incluidos."""

    curso = database.Column(database.String(10), database.ForeignKey(LLAVE_FORANEA_CURSO), nullable=False, index=True)
    recurso = database.Column(database.String(10), database.ForeignKey("recurso.codigo"), nullable=False, index=True)


class CursoSeccion(database.Model, BaseTabla):  # type: ignore[name-defined]
    """Los cursos tienen secciones para dividir el contenido en secciones logicas."""

    curso = database.Column(database.String(10), database.ForeignKey(LLAVE_FORANEA_CURSO), nullable=False, index=True)
    rel_curso = database.relationship("Curso", foreign_keys=curso)
    nombre = database.Column(database.String(100), nullable=False)
    descripcion = database.Column(database.String(250), nullable=False)
    indice = database.Column(database.Integer(), index=True)
    # 0: Borrador, 1: Publico
    estado = database.Column(database.Boolean())


class CursoRecurso(database.Model, BaseTabla):  # type: ignore[name-defined]
    """Una sección de un curso consta de una serie de recursos."""

    __table_args__ = (database.UniqueConstraint("doc", name="documento_unico"),)
    indice = database.Column(database.Integer(), index=True)
    seccion = database.Column(database.String(26), database.ForeignKey(LLAVE_FORANEA_SECCION), nullable=False, index=True)
    curso = database.Column(database.String(10), database.ForeignKey(LLAVE_FORANEA_CURSO), nullable=False, index=True)
    rel_curso = database.relationship("Curso", foreign_keys=curso)
    nombre = database.Column(database.String(150), nullable=False)
    descripcion = database.Column(database.String(1000), nullable=False)
    # Uno de: mp3, pdf, meet, img, text, html, link, slides, youtube
    tipo = database.Column(database.String(150), nullable=False)
    # 1: Requerido, 2: Optional, 3: Alternativo
    requerido = database.Column(database.Integer(), default=1)
    url = database.Column(database.String(250), unique=False)
    fecha = database.Column(database.Date())
    hora_inicio = database.Column(database.Time())
    hora_fin = database.Column(database.Time())
    publico = database.Column(database.Boolean())
    base_doc_url = database.Column(database.String(50), unique=False)
    doc = database.Column(database.String(50), unique=True)
    ext = database.Column(database.String(5), unique=True)
    text = database.Column(database.String(750))
    external_code = database.Column(database.String(500))
    notes = database.Column(database.String(20))


class CursoRecursoAvance(database.Model, BaseTabla):  # type: ignore[name-defined]
    """
    Un control del avance de cada usuario de tipo estudiante de los recursos de un curso,
    para que un curso de considere finalizado un alumno debe completar todos los recursos requeridos.
    """

    curso = database.Column(database.String(10), database.ForeignKey(LLAVE_FORANEA_CURSO), nullable=False, index=True)
    seccion = database.Column(database.String(32), database.ForeignKey(LLAVE_FORANEA_SECCION), nullable=False, index=True)
    recurso = database.Column(database.String(32), database.ForeignKey(LLAVE_FORANEA_RECURSO), nullable=False, index=True)
    usuario = database.Column(database.String(20), database.ForeignKey(LLAVE_FORANEA_USUARIO), nullable=False, index=True)
    # pendiente, iniciado, completado
    estado = database.Column(database.String(15))
    avance = database.Column(database.Float(asdecimal=True))


class CursoRecursoPregunta(database.Model, BaseTabla):  # type: ignore[name-defined]
    """Los recursos de tipo prueba estan conformados por una serie de preguntas que el usario debe contestar."""

    __table_args__ = (database.UniqueConstraint("codigo", name="curso_recurso_pregunta_unico"),)
    indice = database.Column(database.Integer())
    codigo = database.Column(database.String(32), unique=False)
    curso = database.Column(database.String(10), database.ForeignKey(LLAVE_FORANEA_CURSO), nullable=False, index=True)
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


class CursoRecursoPreguntaOpcion(database.Model, BaseTabla):  # type: ignore[name-defined]
    """Las preguntas tienen opciones."""

    curso = database.Column(database.String(10), database.ForeignKey(LLAVE_FORANEA_CURSO), nullable=False, index=True)
    recurso = database.Column(database.String(32), database.ForeignKey(LLAVE_FORANEA_RECURSO), nullable=False, index=True)
    pregunta = database.Column(database.String(32), database.ForeignKey(LLAVE_FORANEA_PREGUNTA), nullable=False, index=True)
    texto = database.Column(database.String(50))
    boleano = database.Column(database.Boolean())
    correcta = database.Column(database.Boolean())


class CursoRecursoPreguntaRespuesta(database.Model, BaseTabla):  # type: ignore[name-defined]
    """Respuestas de los usuarios a las preguntas del curso."""

    curso = database.Column(database.String(10), database.ForeignKey(LLAVE_FORANEA_CURSO), nullable=False, index=True)
    recurso = database.Column(database.String(32), database.ForeignKey(LLAVE_FORANEA_RECURSO), nullable=False, index=True)
    pregunta = database.Column(database.String(32), database.ForeignKey(LLAVE_FORANEA_PREGUNTA), nullable=False, index=True)
    usuario = database.Column(database.String(20), database.ForeignKey(LLAVE_FORANEA_USUARIO), nullable=False, index=True)
    texto = database.Column(database.String(500))
    boleano = database.Column(database.Boolean())
    correcta = database.Column(database.Boolean())
    nota = database.Column(database.Float(asdecimal=True))


class CursoRecursoConsulta(database.Model, BaseTabla):  # type: ignore[name-defined]
    """Un usuario debe poder hacer consultas a su tutor/moderador."""

    curso = database.Column(database.String(10), database.ForeignKey(LLAVE_FORANEA_CURSO), nullable=False)
    recurso = database.Column(database.String(32), database.ForeignKey(LLAVE_FORANEA_RECURSO), nullable=False)
    usuario = database.Column(database.String(20), database.ForeignKey(LLAVE_FORANEA_USUARIO), nullable=False)
    pregunta = database.Column(database.String(500))
    respuesta = database.Column(database.String(500))


class CursoRecursoSlideShow(database.Model, BaseTabla):  # type: ignore[name-defined]
    """Una presentación basada en reveal.js"""

    __table_args__ = (database.UniqueConstraint("codigo", name="codigo_slideshow_unico"),)
    titulo = database.Column(database.String(100), database.ForeignKey(LLAVE_FORANEA_CURSO), nullable=False)
    descripcion = database.Column(database.String(250), database.ForeignKey(LLAVE_FORANEA_CURSO), nullable=False)
    codigo = database.Column(database.String(32), unique=False)
    curso = database.Column(database.String(10), database.ForeignKey(LLAVE_FORANEA_CURSO), nullable=False, index=True)
    recurso = database.Column(database.String(32), database.ForeignKey(LLAVE_FORANEA_RECURSO), nullable=False, index=True)
    usuario = database.Column(database.String(20), database.ForeignKey(LLAVE_FORANEA_USUARIO), nullable=False)


class CursoRecursoSlides(database.Model, BaseTabla):  # type: ignore[name-defined]
    """Una presentación basada en reveal.js"""

    titulo = database.Column(database.String(100), database.ForeignKey(LLAVE_FORANEA_CURSO), nullable=False)
    texto = database.Column(database.String(250), database.ForeignKey(LLAVE_FORANEA_CURSO), nullable=False)
    indice = database.Column(database.Integer())
    curso = database.Column(database.String(10), database.ForeignKey(LLAVE_FORANEA_CURSO), nullable=False)
    recurso = database.Column(database.String(32), database.ForeignKey(LLAVE_FORANEA_RECURSO), nullable=False)
    slide_show = database.Column(database.String(32), database.ForeignKey("curso_recurso_slide_show.codigo"), nullable=False)


class Files(database.Model, BaseTabla):  # type: ignore[name-defined]
    """Listado de archivos que se han cargado a la aplicacion."""

    archivo = database.Column(database.String(100), nullable=False)
    tipo = database.Column(database.String(15), nullable=False)
    hashtag = database.Column(database.String(50), nullable=False)
    url = database.Column(database.String(100), nullable=False)


class DocenteCurso(database.Model, BaseTabla):  # type: ignore[name-defined]
    """Uno o mas usuario de tipo intructor pueden estar a cargo de un curso."""

    curso = database.Column(database.String(10), database.ForeignKey(LLAVE_FORANEA_CURSO), nullable=False, index=True)
    usuario = database.Column(database.String(20), database.ForeignKey(LLAVE_FORANEA_USUARIO), nullable=False, index=True)
    vigente = database.Column(database.Boolean())


class ModeradorCurso(database.Model, BaseTabla):  # type: ignore[name-defined]
    """Uno o mas usuario de tipo moderator pueden estar a cargo de un curso."""

    curso = database.Column(database.String(10), database.ForeignKey(LLAVE_FORANEA_CURSO), nullable=False, index=True)
    usuario = database.Column(database.String(20), database.ForeignKey(LLAVE_FORANEA_USUARIO), nullable=False, index=True)
    vigente = database.Column(database.Boolean())


class EstudianteCurso(database.Model, BaseTabla):  # type: ignore[name-defined]
    """Uno o mas usuario de tipo user pueden estar a cargo de un curso."""

    curso = database.Column(database.String(10), database.ForeignKey(LLAVE_FORANEA_CURSO), nullable=False, index=True)
    usuario = database.Column(database.String(20), database.ForeignKey(LLAVE_FORANEA_USUARIO), nullable=False, index=True)
    vigente = database.Column(database.Boolean())


class Configuracion(database.Model, BaseTabla):  # type: ignore[name-defined]
    """
    Repositorio Central para la configuración de la aplicacion.

    Realmente esta tabla solo va a contener un registro con una columna para cada opción, en las plantillas
    va a estar disponible como la variable global config.
    """

    titulo = database.Column(database.String(150), nullable=False)
    descripcion = database.Column(database.String(500), nullable=False)
    # Uno de mooc, school, training
    modo = database.Column(database.String(500), nullable=False, default="mooc")
    moneda = database.Column(database.String(5))
    # Formas de pago
    stripe = database.Column(database.Boolean())
    paypal = database.Column(database.Boolean())
    # Stripe settings
    stripe_secret = database.Column(database.String(100))
    stripe_public = database.Column(database.String(100))
    # Style settings
    style = database.Column(database.String(15))
    custom_logo = database.Column(database.Boolean())
    # Email settings
    email = database.Column(database.Boolean())
    mail_server = database.Column(database.String(50))
    mail_port = database.Column(database.String(50))
    mail_username = database.Column(database.String(50))
    mail_password = database.Column(database.String(50))
    mail_use_tls = database.Column(database.Boolean())
    mail_use_ssl = database.Column(database.Boolean())


class Categoria(database.Model, BaseTabla):  # type: ignore[name-defined]
    """Permite Clasificar los cursos por categoria."""

    nombre = database.Column(database.String(100), nullable=False)
    descripcion = database.Column(database.String(250), nullable=False)


class CategoriaCurso(database.Model, BaseTabla):  # type: ignore[name-defined]
    """Listado de Cursos Permite Clasificar los cursos por categoria."""

    curso = database.Column(database.String(10), database.ForeignKey("curso.codigo"), nullable=False, index=True)
    categoria = database.Column(database.String(26), database.ForeignKey("categoria.id"), nullable=False, index=True)
    relacion_curso = database.relationship("Curso", foreign_keys=curso)
    relacion_categoria = database.relationship("Categoria", foreign_keys=categoria)


class Etiqueta(database.Model, BaseTabla):  # type: ignore[name-defined]
    """Permite Clasificar los cursos por etiquetas."""

    nombre = database.Column(database.String(20), nullable=False)
    color = database.Column(database.String(10), nullable=False)


class EtiquetaCurso(database.Model, BaseTabla):  # type: ignore[name-defined]
    """Listado de Cursos Permite Clasificar los cursos por categoria."""

    curso = database.Column(database.String(10), database.ForeignKey("curso.codigo"), nullable=False, index=True)
    etiqueta = database.Column(database.String(26), database.ForeignKey("etiqueta.id"), nullable=False, index=True)
    relacion_curso = database.relationship("Curso", foreign_keys=curso)
    relacion_etiqueta = database.relationship("Etiqueta", foreign_keys=etiqueta)


class Programa(database.Model, BaseTabla):  # type: ignore[name-defined]
    """Un programa agrupa una serie de cursos."""

    __table_args__ = (database.UniqueConstraint("codigo", name="codigo_programa_unico"),)
    nombre = database.Column(database.String(20), nullable=False)
    codigo = database.Column(database.String(10), nullable=False, unique=True)
    descripcion = database.Column(database.String(200))
    texto = database.Column(database.String(1000))
    precio = database.Column(database.Float())
    publico = database.Column(database.Boolean())
    # draft, open, closed
    estado = database.Column(database.String(20))
    logo = database.Column(database.Boolean(), default=False)
    promocionado = database.Column(database.Boolean())
    fecha_promocionado = database.Column(database.DateTime, nullable=True)


class ProgramaCurso(database.Model, BaseTabla):  # type: ignore[name-defined]
    """Cursos en un programa."""

    curso = database.Column(database.String(10), database.ForeignKey(LLAVE_FORANEA_CURSO), nullable=False, index=True)
    programa = database.Column(database.String(10), database.ForeignKey("programa.codigo"), nullable=False, index=True)
    relacion_curso = database.relationship("Curso", foreign_keys=curso)
    relacion_programa = database.relationship("Programa", foreign_keys=programa)


class ProgramaEstudiante(database.Model, BaseTabla):  # type: ignore[name-defined]
    """Cursos en un programa."""

    usuario = database.Column(database.String(20), database.ForeignKey(LLAVE_FORANEA_USUARIO), nullable=False, index=True)
    programa = database.Column(database.String(26), database.ForeignKey("programa.id"), nullable=False, index=True)
    relacion_usuario = database.relationship("Usuario", foreign_keys=usuario)
    relacion_programa = database.relationship("Programa", foreign_keys=programa)


class Recurso(database.Model, BaseTabla):  # type: ignore[name-defined]
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


class Certificado(database.Model, BaseTabla):  # type: ignore[name-defined]
    """Plantilla para generar un certificado."""

    nombre = database.Column(database.String(50))
    curso = database.Column(database.String(10), database.ForeignKey(LLAVE_FORANEA_CURSO), nullable=False, index=True)
    plantilla = database.Column(database.String(3000))
    habilitado = database.Column(database.Boolean())
    fondo = database.Column(database.String(100))


class Mensaje(database.Model, BaseTabla):  # type: ignore[name-defined]
    """Mensajes de usuarios."""

    usuario = database.Column(database.String(20), database.ForeignKey(LLAVE_FORANEA_USUARIO), nullable=False, index=True)
    curso = database.Column(database.String(10), database.ForeignKey(LLAVE_FORANEA_CURSO), nullable=False, index=True)
    recurso = database.Column(database.String(10), database.ForeignKey(LLAVE_FORANEA_RECURSO), nullable=False, index=True)
    cerrado = database.Column(database.Boolean(), default=False)
    publico = database.Column(database.Boolean(), default=False)
    texto = database.Column(database.String(100))
    es_respuesta = database.Column(database.Boolean(), default=False)
    padre = database.Column(database.String(26))
