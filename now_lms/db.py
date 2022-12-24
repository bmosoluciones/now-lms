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
from uuid import uuid4

# Librerias de terceros:
from flask import current_app
from flask_login import current_user, UserMixin
from flask_sqlalchemy import SQLAlchemy
from loguru import logger as log

# Recursos locales:
from now_lms.auth import proteger_passwd
from now_lms.config import CONFIGURACION


database: SQLAlchemy = SQLAlchemy()

# < --------------------------------------------------------------------------------------------- >
# Base de datos relacional

MAXIMO_RESULTADOS_EN_CONSULTA_PAGINADA: int = 10
LLAVE_FORONEA_CURSO: str = "curso.codigo"
LLAVE_FORONEA_USUARIO: str = "usuario.usuario"
LLAVE_FORANEA_SECCION: str = "curso_seccion.codigo"


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
    __table_args__ = (database.UniqueConstraint("usuario", name="usuario_unico"),)
    usuario = database.Column(database.String(150), nullable=False, index=True)
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
    curso = database.Column(database.String(10), database.ForeignKey(LLAVE_FORONEA_CURSO), nullable=False)
    rel_curso = database.relationship("Curso", foreign_keys=curso)
    nombre = database.Column(database.String(100), nullable=False)
    descripcion = database.Column(database.String(250), nullable=False)
    indice = database.Column(database.Integer())
    # 0: Borrador, 1: Publico
    estado = database.Column(database.Boolean())


class CursoRecurso(database.Model, BaseTabla):  # type: ignore[name-defined]
    """Una sección de un curso consta de una serie de recursos."""

    __table_args__ = (database.UniqueConstraint("codigo", name="curso_recurso_unico"),)
    indice = database.Column(database.Integer())
    codigo = database.Column(database.String(32), unique=False)
    seccion = database.Column(database.String(32), database.ForeignKey(LLAVE_FORANEA_SECCION), nullable=False)
    curso = database.Column(database.String(10), database.ForeignKey(LLAVE_FORONEA_CURSO), nullable=False)
    rel_curso = database.relationship("Curso", foreign_keys=curso)
    nombre = database.Column(database.String(150), nullable=False)
    descripcion = database.Column(database.String(250), nullable=False)
    # Implemented types: meet, pdf, youtube
    tipo = database.Column(database.String(150), nullable=False)
    # Youtube
    url = database.Column(database.String(250), unique=False)
    fecha = database.Column(database.Date())
    hora = database.Column(database.Time())


class Files(database.Model, BaseTabla):  # type: ignore[name-defined]
    """Listado de archivos que se han cargado a la aplicacion."""

    archivo = database.Column(database.String(100), nullable=False)
    tipo = database.Column(database.String(15), nullable=False)
    hashtag = database.Column(database.String(50), nullable=False)
    url = database.Column(database.String(100), nullable=False)


class DocenteCurso(database.Model, BaseTabla):  # type: ignore[name-defined]
    """Uno o mas usuario de tipo intructor pueden estar a cargo de un curso."""

    curso = database.Column(database.String(10), database.ForeignKey(LLAVE_FORONEA_CURSO), nullable=False)
    usuario = database.Column(database.String(10), database.ForeignKey(LLAVE_FORONEA_USUARIO), nullable=False)
    vigente = database.Column(database.Boolean())


class ModeradorCurso(database.Model, BaseTabla):  # type: ignore[name-defined]
    """Uno o mas usuario de tipo moderator pueden estar a cargo de un curso."""

    curso = database.Column(database.String(10), database.ForeignKey(LLAVE_FORONEA_CURSO), nullable=False)
    usuario = database.Column(database.String(10), database.ForeignKey(LLAVE_FORONEA_USUARIO), nullable=False)
    vigente = database.Column(database.Boolean())


class EstudianteCurso(database.Model, BaseTabla):  # type: ignore[name-defined]
    """Uno o mas usuario de tipo user pueden estar a cargo de un curso."""

    curso = database.Column(database.String(10), database.ForeignKey(LLAVE_FORONEA_CURSO), nullable=False)
    usuario = database.Column(database.String(10), database.ForeignKey(LLAVE_FORONEA_USUARIO), nullable=False)
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


def crear_cursos_predeterminados():
    # pylint: disable=too-many-locals
    """Crea en la base de datos un curso de demostración."""
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
    with current_app.app_context():
        database.session.add(demo)
        database.session.commit()

    ramdon = uuid4()
    seccion_id = str(ramdon.hex)
    nueva_seccion1 = CursoSeccion(
        codigo=seccion_id,
        curso="now",
        nombre="Introduction to online teaching.",
        descripcion="This is introductory material to online teaching.",
        estado=False,
        indice=1,
    )

    with current_app.app_context():
        database.session.add(nueva_seccion1)
        database.session.commit()

    ramdon1 = uuid4()
    recurso_id1 = str(ramdon1.hex)
    nuevo_recurso1 = CursoRecurso(
        codigo=recurso_id1,
        curso="now",
        seccion=seccion_id,
        tipo="youtube",
        nombre="Introduction to Online Teaching",
        descripcion="UofSC Center for Teaching Excellence - Introduction to Online Teaching.",
        url="https://www.youtube.com/watch?v=CvPj4V_j7u8",
        indice=1,
    )

    ramdon2 = uuid4()
    recurso_id2 = str(ramdon2.hex)
    nuevo_recurso2 = CursoRecurso(
        codigo=recurso_id2,
        curso="now",
        seccion=seccion_id,
        tipo="youtube",
        nombre="How to Teach OnLine.",
        descripcion="Kristina Garcia - Top Tips for New Online Teachers!",
        url="https://www.youtube.com/watch?v=CvPj4V_j7u8",
        indice=2,
    )

    ramdon2 = uuid4()
    seccion_id2 = str(ramdon2.hex)
    nueva_seccion2 = CursoSeccion(
        codigo=seccion_id2,
        curso="now",
        nombre="How to sell a online course.",
        descripcion="This is introductory material to how to sell your online course.",
        estado=False,
        indice=2,
    )

    with current_app.app_context():
        database.session.add(nueva_seccion2)
        database.session.commit()

    ramdon3 = uuid4()
    recurso_id3 = str(ramdon3.hex)
    nuevo_recurso3 = CursoRecurso(
        codigo=recurso_id3,
        curso="now",
        seccion=seccion_id2,
        tipo="youtube",
        nombre="4 Steps to Sell your Online Course with 0 audience.",
        descripcion="Sunny Lenarduzzi - No audience? No problem! YOU DON’T NEED AN AUDIENCE TO START A BUSINESS.",
        url="https://www.youtube.com/watch?v=TWQFHRt3dNg",
        indice=1,
    )

    ramdon4 = uuid4()
    recurso_id4 = str(ramdon4.hex)
    nuevo_recurso4 = CursoRecurso(
        codigo=recurso_id4,
        curso="now",
        seccion=seccion_id2,
        tipo="meet",
        nombre="A live meet about course sales.",
        descripcion="Live meets will improve your course.",
        url="https://meet.jit.si/",
        indice=2,
        fecha=datetime.today() + timedelta(days=9),
        hora=time(hour=14, minute=30),
    )

    ramdon5 = uuid4()
    recurso_id5 = str(ramdon5.hex)
    nuevo_recurso5 = CursoRecurso(
        codigo=recurso_id5,
        curso="now",
        seccion=seccion_id2,
        tipo="pdf",
        nombre="FACULTY DEVELOPMENT FOR ONLINE TEACHING AS A CATALYST FOR CHANGE.",
        descripcion="A PDF file to share with yours learners.",
        url="https://files.eric.ed.gov/fulltext/EJ971044.pdf",
        indice=3,
    )

    with current_app.app_context():
        database.session.add(nuevo_recurso1)
        database.session.add(nuevo_recurso2)
        database.session.add(nuevo_recurso3)
        database.session.add(nuevo_recurso4)
        database.session.add(nuevo_recurso5)
        database.session.commit()


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
    )
    # Crea un usuario de cada perfil (admin, user, instructor, moderator)
    # por defecto desactivados.
    demo_user1 = Usuario(
        usuario="student",
        acceso=proteger_passwd("studen"),
        tipo="user",
        nombre="User",
        apellido="Student",
        correo_electronico="usuario1@mail.com",
        activo=False,
    )
    demo_user2 = Usuario(
        usuario="instructor",
        acceso=proteger_passwd("instructor"),
        tipo="instructor",
        nombre="User",
        apellido="Instructor",
        correo_electronico="usuario2@mail.com",
        activo=False,
    )
    demo_user3 = Usuario(
        usuario="moderator",
        acceso=proteger_passwd("moderator"),
        tipo="moderator",
        nombre="User",
        apellido="Moderator",
        correo_electronico="usuario3@mail.com",
        activo=False,
    )
    database.session.add(administrador)
    database.session.add(demo_user1)
    database.session.add(demo_user2)
    database.session.add(demo_user3)
    database.session.commit()
