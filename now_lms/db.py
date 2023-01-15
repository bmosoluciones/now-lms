# Copyright 2022 BMO Soluciones, S.A.
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
from datetime import datetime, time, timedelta
from typing import Union

# Librerias de terceros:
from flask_login import current_user, UserMixin
from flask_sqlalchemy import SQLAlchemy
from loguru import logger as log
from ulid import ULID

# Recursos locales:
from now_lms.auth import proteger_passwd
from now_lms.config import CONFIGURACION


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
    # Tipos implementados:
    #   - prueba: Una evaluación para valor el aprendizaje del estudiante.
    #   - meet: Un link a un reunión en linea en la plataforma de elección del docente:
    # Zoom, Microsoft Teams, Google Meet, etc.
    #   - pdf: Un link a un pdf descargable
    #   - youtube: Un link a un vídeo alojado en YouTube.
    # Es importante mencionar advertir al docente que si bien navegadores basados en Chromium como MS Edge o Google Chrome
    # no permiten descargar videos directamente desde ese navegador exiten N cantidad de sitios y herramientas que permiten
    # bajar al ordenador vídeos alojados en YouTube por que lo el contenido es facilmente plageable.
    tipo = database.Column(database.String(150), nullable=False)
    # Parte de la logica de la aplicación es que el docente puede definir si en recurso debe ser
    # completado para considerar el curso finalizado, si el recurso es opcional o si el alumno puede
    # decidir completar uno de N recurso recursos para considerar el curso finalizado.
    # Se definen 3 tipos de recurso: requerido, opcional y alternativo.
    requerido = database.Column(database.String(15))
    url = database.Column(database.String(250), unique=False)
    fecha = database.Column(database.Date())
    hora = database.Column(database.Time())
    # Un instructor puede decidir brindar acceso publico a un recurso.
    publico = database.Column(database.Boolean())
    base_doc_url = database.Column(database.String(50), unique=False)
    doc = database.Column(database.String(50), unique=True)


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


# < --------------------------------------------------------------------------------------------- >
# Funciones auxiliares relacionadas a contultas de la base de datos.


def verifica_docente_asignado_a_curso(id_curso: Union[None, str] = None):
    """Si el usuario no esta asignado como docente al curso devuelve None."""
    if current_user.is_authenticated:
        return DocenteCurso.query.filter(DocenteCurso.usuario == current_user.usuario, DocenteCurso.curso == id_curso)
    else:
        return False


def verifica_moderador_asignado_a_curso(id_curso: Union[None, str] = None):
    """Si el usuario no esta asignado como moderador al curso devuelve None."""
    if current_user.is_authenticated:
        return ModeradorCurso.query.filter(ModeradorCurso.usuario == current_user.usuario, ModeradorCurso.curso == id_curso)
    else:
        return False


def verifica_estudiante_asignado_a_curso(id_curso: Union[None, str] = None):
    """Si el usuario no esta asignado como estudiante al curso devuelve None."""
    if current_user.is_authenticated:
        return EstudianteCurso.query.filter(EstudianteCurso.usuario == current_user.usuario, EstudianteCurso.curso == id_curso)
    else:
        return False


def crear_configuracion_predeterminada():
    """Crea configuración predeterminada de la aplicación."""
    config = Configuracion(
        titulo="NOW LMS",
        descripcion="Sistema de aprendizaje en linea.",
    )
    database.session.add(config)
    database.session.commit()


def copy_sample_pdf():
    """Crea un archivo PDF de ejemplo."""
    from os import path, makedirs
    from shutil import copyfile
    from now_lms.config import DIRECTORIO_ARCHIVOS

    origen = path.join(DIRECTORIO_ARCHIVOS, "examples", "NOW_Learning_Management_System.pdf")
    directorio_destino = path.join(DIRECTORIO_ARCHIVOS, "files", "public", "files", "resources")
    try:  # pragma: no cover
        makedirs(directorio_destino)
    except FileExistsError:
        pass
    except FileNotFoundError:
        pass
    destino = path.join(directorio_destino, "NOW_Learning_Management_System.pdf")
    try:  # pragma: no cover
        copyfile(origen, destino)
    except FileExistsError:
        pass
    except FileNotFoundError:
        pass


def copy_sample_audio():
    """Crea un archivo audio de ejemplo."""
    from os import path, makedirs
    from shutil import copyfile
    from now_lms.config import DIRECTORIO_ARCHIVOS

    origen = path.join(DIRECTORIO_ARCHIVOS, "examples", "En-us-hello.ogg")
    directorio_destino = path.join(DIRECTORIO_ARCHIVOS, "files", "public", "audio", "resources")
    try:
        makedirs(directorio_destino)
    except FileExistsError:
        pass
    except FileNotFoundError:
        pass
    destino = path.join(directorio_destino, "En-us-hello.ogg")
    try:
        copyfile(origen, destino)
    except FileExistsError:
        pass
    except FileNotFoundError:
        pass


def crear_curso_demo():
    # pylint: disable=too-many-locals
    """Crea en la base de datos un curso de demostración."""
    log.info("Creando curso de demo de recursos.")
    demo = Curso(
        nombre="Demo Course",
        codigo="resources",
        descripcion="This course will let you learn resource types.",
        estado="draft",
        certificado=False,
        publico=False,
        duracion=7,
        nivel=1,
        auditable=False,
        portada="https://img.freepik.com/vector-gratis/concepto-tutoriales-linea_52683-37480.jpg",
        # https://www.freepik.es/vector-gratis/concepto-tutoriales-linea_7915189.htm
        # Imagen de pikisuperstar en Freepik
        fecha_inicio=datetime.today() + timedelta(days=7),
        fecha_fin=datetime.today() + timedelta(days=14),
    )
    database.session.add(demo)
    database.session.commit()

    ramdon1 = ULID()
    seccion_id = str(ramdon1)
    nueva_seccion = CursoSeccion(
        codigo=seccion_id,
        curso="resources",
        nombre="Demo of type of resources.",
        descripcion="Demo of type of resources.",
        estado=False,
        indice=1,
    )

    database.session.add(nueva_seccion)
    database.session.commit()

    copy_sample_audio()
    ramdon2 = ULID()
    recurso1 = str(ramdon2)
    nuevo_recurso6 = CursoRecurso(
        codigo=recurso1,
        curso="resources",
        seccion=seccion_id,
        tipo="mp3",
        nombre="A demo audio resource.",
        descripcion="Audio is easy to produce that videos.",
        base_doc_url="audio",
        doc="demo/En-us-hello.ogg",
        indice=1,
        publico=True,
        requerido=True,
    )
    database.session.add(nuevo_recurso6)
    database.session.commit()

    copy_sample_pdf()
    ramdon3 = ULID()
    recurso2 = str(ramdon3)
    nuevo_recurso5 = CursoRecurso(
        codigo=recurso2,
        curso="resources",
        seccion=seccion_id,
        tipo="pdf",
        nombre="Demo pdf resource.",
        descripcion="A exampel of a PDF file to share with yours learners.",
        base_doc_url="files",
        doc="demo/NOW_Learning_Management_System.pdf",
        indice=2,
        publico=True,
        requerido=True,
    )
    database.session.add(nuevo_recurso5)
    database.session.commit()

    ramdon4 = ULID()
    recurso4 = str(ramdon4)
    nuevo_recurso4 = CursoRecurso(
        codigo=recurso4,
        curso="resources",
        seccion=seccion_id,
        tipo="meet",
        nombre="A live meet about course sales.",
        descripcion="Live meets will improve your course.",
        url="https://en.wikipedia.org/wiki/Web_conferencing",
        indice=3,
        fecha=datetime.today() + timedelta(days=9),
        hora=time(hour=14, minute=30),
        publico=False,
        requerido=True,
    )
    database.session.add(nuevo_recurso4)
    database.session.commit()

    log.debug("Curso de demo de recursos creado correctamente.")


def crear_curso_predeterminado():
    # pylint: disable=too-many-locals
    """Crea un recurso publico."""
    log.info("Creando curso de demostración.")
    demo = Curso(
        nombre="First Course",
        codigo="now",
        descripcion="Welcome! This is your first course.",
        estado="open",
        certificado=True,
        publico=True,
        fecha_inicio=datetime.today() + timedelta(days=7),
        fecha_fin=datetime.today() + timedelta(days=14),
        duracion=7,
        nivel=1,
        precio=10,
        capacidad=50,
        auditable=True,
        portada="https://img.freepik.com/vector-gratis/concepto-tutoriales-linea_52683-37480.jpg",
        # https://www.freepik.es/vector-gratis/concepto-tutoriales-linea_7915189.htm
        # Imagen de pikisuperstar en Freepik
    )
    database.session.add(demo)
    database.session.commit()

    ramdon1 = ULID()
    seccion1_id = str(ramdon1)
    nueva_seccion1 = CursoSeccion(
        codigo=seccion1_id,
        curso="now",
        nombre="Introduction to online teaching.",
        descripcion="This is introductory material to online teaching.",
        estado=False,
        indice=1,
    )

    database.session.add(nueva_seccion1)
    database.session.commit()

    ramdon2 = ULID()
    seccion2_id = str(ramdon2)
    nueva_seccion2 = CursoSeccion(
        codigo=seccion2_id,
        curso="now",
        nombre="How to sell a online course.",
        descripcion="This is introductory material to how to sell your online course.",
        estado=False,
        indice=2,
    )

    database.session.add(nueva_seccion2)
    database.session.commit()

    ramdon1 = ULID()
    recurso_id1 = str(ramdon1)
    nuevo_recurso1 = CursoRecurso(
        codigo=recurso_id1,
        curso="now",
        seccion=seccion1_id,
        tipo="youtube",
        nombre="Introduction to Online Teaching",
        descripcion="UofSC Center for Teaching Excellence - Introduction to Online Teaching.",
        url="https://www.youtube.com/watch?v=CvPj4V_j7u8",
        indice=1,
        publico=True,
        requerido=True,
    )
    database.session.add(nuevo_recurso1)
    database.session.commit()

    ramdon2 = ULID()
    recurso_id2 = str(ramdon2)
    nuevo_recurso2 = CursoRecurso(
        codigo=recurso_id2,
        curso="now",
        seccion=seccion1_id,
        tipo="youtube",
        nombre="How to Teach OnLine.",
        descripcion="Kristina Garcia - Top Tips for New Online Teachers!",
        url="https://www.youtube.com/watch?v=CvPj4V_j7u8",
        indice=2,
        publico=False,
        requerido=False,
    )
    database.session.add(nuevo_recurso2)
    database.session.commit()

    ramdon6 = ULID()
    recurso_id6 = str(ramdon6)
    nuevo_recurso2 = CursoRecurso(
        codigo=recurso_id6,
        curso="now",
        seccion=seccion1_id,
        tipo="youtube",
        nombre="What You Should Know BEFORE Becoming an Online English Teacher.",
        descripcion="Danie Jay - What You Should Know BEFORE Becoming an Online English Teacher | 10 Things I WISH I Knew",
        url="https://www.youtube.com/watch?v=9JBDSzSARHA",
        indice=2,
        publico=False,
        requerido=False,
    )
    database.session.add(nuevo_recurso2)
    database.session.commit()

    ramdon3 = ULID()
    recurso_id3 = str(ramdon3)
    nuevo_recurso3 = CursoRecurso(
        codigo=recurso_id3,
        curso="now",
        seccion=seccion2_id,
        tipo="youtube",
        nombre="4 Steps to Sell your Online Course with 0 audience.",
        descripcion="Sunny Lenarduzzi - No audience? No problem! YOU DON’T NEED AN AUDIENCE TO START A BUSINESS.",
        url="https://www.youtube.com/watch?v=TWQFHRt3dNg",
        indice=1,
        publico=False,
        requerido=True,
    )
    database.session.add(nuevo_recurso3)
    database.session.commit()

    log.debug("Curso de demostración creado correctamente.")


def crear_usuarios_predeterminados():
    """Crea en la base de datos los usuarios iniciales."""
    log.info("Creando usuario administrador.")
    administrador = Usuario(
        usuario=CONFIGURACION.get("ADMIN_USER"),
        acceso=proteger_passwd(CONFIGURACION.get("ADMIN_PSWD")),
        tipo="admin",
        nombre="System",
        apellido="Admin",
        activo=True,
        correo_electronico="admininistrator@mail.com",
    )
    database.session.add(administrador)
    database.session.commit()
    log.debug("Usuario administrador creado correctamente.")

    # Crea un usuario de cada perfil (admin, user, instructor, moderator)
    # por defecto desactivados.
    log.info("Creando usuarios de demostración.")
    student = Usuario(
        usuario="student",
        acceso=proteger_passwd("student"),
        tipo="user",
        nombre="User",
        apellido="Student",
        correo_electronico="student@mail.com",
        activo=False,
    )
    database.session.add(student)
    database.session.commit()
    instructor = Usuario(
        usuario="instructor",
        acceso=proteger_passwd("instructor"),
        tipo="instructor",
        nombre="User",
        apellido="Instructor",
        correo_electronico="instructor@mail.com",
        activo=False,
    )
    database.session.add(instructor)
    database.session.commit()
    moderator = Usuario(
        usuario="moderator",
        acceso=proteger_passwd("moderator"),
        tipo="moderator",
        nombre="User",
        apellido="Moderator",
        correo_electronico="moderator@mail.com",
        activo=False,
    )
    database.session.add(moderator)
    database.session.commit()
    log.debug("Usuarios creados correctamente.")
