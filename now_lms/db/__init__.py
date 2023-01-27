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

# pylint: disable=E1101

# Libreria standar:

# Librerias de terceros:
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy

# Recursos locales:


database: SQLAlchemy = SQLAlchemy()

# < --------------------------------------------------------------------------------------------- >
# Base de datos relacional

MAXIMO_RESULTADOS_EN_CONSULTA_PAGINADA: int = 10
LLAVE_FORANEA_CURSO: str = "curso.codigo"
LLAVE_FORANEA_USUARIO: str = "usuario.usuario"
LLAVE_FORANEA_SECCION: str = "curso_seccion.codigo"
LLAVE_FORANEA_RECURSO: str = "curso_recurso.codigo"
LLAVE_FORANEA_PREGUNTA: str = "curso_recurso_pregunta.codigo"


# pylint: disable=too-few-public-methods
# pylint: disable=no-member
class BaseTabla:
    """Columnas estandar para todas las tablas de la base de datos."""

    # Pistas de auditoria comunes a todas las tablas.
    id = database.Column(database.Integer(), primary_key=True, nullable=True)
    status = database.Column(database.String(50), nullable=True)
    creado = database.Column(database.DateTime, default=database.func.now(), nullable=False)
    creado_por = database.Column(database.String(15), nullable=True)
    modificado = database.Column(database.DateTime, default=database.func.now(), onupdate=database.func.now(), nullable=True)
    modificado_por = database.Column(database.String(15), nullable=True)


class Usuario(UserMixin, database.Model, BaseTabla):  # type: ignore[name-defined]
    """Una entidad con acceso al sistema."""

    # Información Básica
    __table_args__ = (database.UniqueConstraint("usuario", name="id_usuario_unico"),)
    __table_args__ = (database.UniqueConstraint("correo_electronico", name="correo_usuario_unico"),)
    usuario = database.Column(database.String(20), nullable=False, index=True, unique=True)
    acceso = database.Column(database.LargeBinary(), nullable=False)
    nombre = database.Column(database.String(100))
    apellido = database.Column(database.String(100))
    correo_electronico = database.Column(database.String(100))
    # Tipo puede ser: admin, user, instructor, moderator
    tipo = database.Column(database.String(20))
    activo = database.Column(database.Boolean())
    genero = database.Column(database.String(1))
    nacimiento = database.Column(database.Date())


class Curso(database.Model, BaseTabla):  # type: ignore[name-defined]
    """Un curso es la base del aprendizaje en NOW LMS."""

    __table_args__ = (database.UniqueConstraint("codigo", name="curso_codigo_unico"),)
    nombre = database.Column(database.String(150), nullable=False)
    codigo = database.Column(database.String(20), unique=True)
    descripcion = database.Column(database.String(500), nullable=False)
    # draft, open, closed
    estado = database.Column(database.String(10), nullable=False)
    # mooc
    publico = database.Column(database.Boolean())
    certificado = database.Column(database.Boolean())
    auditable = database.Column(database.Boolean())
    precio = database.Column(database.Numeric())
    capacidad = database.Column(database.Integer())
    fecha_inicio = database.Column(database.Date())
    fecha_fin = database.Column(database.Date())
    duracion = database.Column(database.Integer())
    portada = database.Column(database.String(250), nullable=True, default=None)
    nivel = database.Column(database.Integer())


class CursoSeccion(database.Model, BaseTabla):  # type: ignore[name-defined]
    """Los cursos tienen secciones para dividir el contenido en secciones logicas."""

    __table_args__ = (database.UniqueConstraint("codigo", name="curso_seccion_unico"),)
    codigo = database.Column(database.String(32), unique=False)
    curso = database.Column(database.String(10), database.ForeignKey(LLAVE_FORANEA_CURSO), nullable=False)
    rel_curso = database.relationship("Curso", foreign_keys=curso)
    nombre = database.Column(database.String(100), nullable=False)
    descripcion = database.Column(database.String(250), nullable=False)
    indice = database.Column(database.Integer())
    # 0: Borrador, 1: Publico
    estado = database.Column(database.Boolean())


class CursoRecurso(database.Model, BaseTabla):  # type: ignore[name-defined]
    """Una sección de un curso consta de una serie de recursos."""

    __table_args__ = (
        database.UniqueConstraint("codigo", name="curso_recurso_unico"),
        database.UniqueConstraint("doc", name="documento_unico"),
    )
    indice = database.Column(database.Integer())
    codigo = database.Column(database.String(32), unique=False)
    seccion = database.Column(database.String(32), database.ForeignKey(LLAVE_FORANEA_SECCION), nullable=False)
    curso = database.Column(database.String(10), database.ForeignKey(LLAVE_FORANEA_CURSO), nullable=False)
    rel_curso = database.relationship("Curso", foreign_keys=curso)
    nombre = database.Column(database.String(150), nullable=False)
    descripcion = database.Column(database.String(250), nullable=False)
    tipo = database.Column(database.String(150), nullable=False)
    requerido = database.Column(database.String(15))
    url = database.Column(database.String(250), unique=False)
    fecha = database.Column(database.Date())
    hora = database.Column(database.Time())
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

    curso = database.Column(database.String(10), database.ForeignKey(LLAVE_FORANEA_CURSO), nullable=False)
    seccion = database.Column(database.String(32), database.ForeignKey(LLAVE_FORANEA_SECCION), nullable=False)
    recurso = database.Column(database.String(32), database.ForeignKey(LLAVE_FORANEA_RECURSO), nullable=False)
    usuario = database.Column(database.String(20), database.ForeignKey(LLAVE_FORANEA_USUARIO), nullable=False)
    # pendiente, iniciado, completado
    estado = database.Column(database.String(15))
    avance = database.Column(database.Float(asdecimal=True))


class CursoRecursoPregunta(database.Model, BaseTabla):  # type: ignore[name-defined]
    """Los recursos de tipo prueba estan conformados por una serie de preguntas que el usario debe contestar."""

    __table_args__ = (database.UniqueConstraint("codigo", name="curso_recurso_pregunta_unico"),)
    indice = database.Column(database.Integer())
    codigo = database.Column(database.String(32), unique=False)
    curso = database.Column(database.String(10), database.ForeignKey(LLAVE_FORANEA_CURSO), nullable=False)
    seccion = database.Column(database.String(32), database.ForeignKey(LLAVE_FORANEA_SECCION), nullable=False)
    recurso = database.Column(database.String(32), database.ForeignKey(LLAVE_FORANEA_RECURSO), nullable=False)
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

    curso = database.Column(database.String(10), database.ForeignKey(LLAVE_FORANEA_CURSO), nullable=False)
    recurso = database.Column(database.String(32), database.ForeignKey(LLAVE_FORANEA_RECURSO), nullable=False)
    pregunta = database.Column(database.String(32), database.ForeignKey(LLAVE_FORANEA_PREGUNTA), nullable=False)
    texto = database.Column(database.String(50))
    boleano = database.Column(database.Boolean())
    correcta = database.Column(database.Boolean())


class CursoRecursoPreguntaRespuesta(database.Model, BaseTabla):  # type: ignore[name-defined]
    """Respuestas de los usuarios a las preguntas del curso."""

    curso = database.Column(database.String(10), database.ForeignKey(LLAVE_FORANEA_CURSO), nullable=False)
    recurso = database.Column(database.String(32), database.ForeignKey(LLAVE_FORANEA_RECURSO), nullable=False)
    pregunta = database.Column(database.String(32), database.ForeignKey(LLAVE_FORANEA_PREGUNTA), nullable=False)
    usuario = database.Column(database.String(20), database.ForeignKey(LLAVE_FORANEA_USUARIO), nullable=False)
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
    curso = database.Column(database.String(10), database.ForeignKey(LLAVE_FORANEA_CURSO), nullable=False)
    recurso = database.Column(database.String(32), database.ForeignKey(LLAVE_FORANEA_RECURSO), nullable=False)
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

    curso = database.Column(database.String(10), database.ForeignKey(LLAVE_FORANEA_CURSO), nullable=False)
    usuario = database.Column(database.String(20), database.ForeignKey(LLAVE_FORANEA_USUARIO), nullable=False)
    vigente = database.Column(database.Boolean())


class ModeradorCurso(database.Model, BaseTabla):  # type: ignore[name-defined]
    """Uno o mas usuario de tipo moderator pueden estar a cargo de un curso."""

    curso = database.Column(database.String(10), database.ForeignKey(LLAVE_FORANEA_CURSO), nullable=False)
    usuario = database.Column(database.String(20), database.ForeignKey(LLAVE_FORANEA_USUARIO), nullable=False)
    vigente = database.Column(database.Boolean())


class EstudianteCurso(database.Model, BaseTabla):  # type: ignore[name-defined]
    """Uno o mas usuario de tipo user pueden estar a cargo de un curso."""

    curso = database.Column(database.String(10), database.ForeignKey(LLAVE_FORANEA_CURSO), nullable=False)
    usuario = database.Column(database.String(20), database.ForeignKey(LLAVE_FORANEA_USUARIO), nullable=False)
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
    # Pagos en linea
    paypal_key = database.Column(database.String(150), nullable=True)
    stripe_key = database.Column(database.String(150), nullable=True)
    # Micelaneos
    dev_docs = database.Column(database.Boolean(), default=False)
    # Permitir al usuario cargar archivos
    file_uploads = database.Column(database.Boolean(), default=False)
