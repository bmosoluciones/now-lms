# Copyright 2021 BMO Soluciones, S.A.
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


"""NOW Learning Management System."""
# Libreria standar:
import sys
from functools import wraps
from os import environ, name, path, cpu_count
from pathlib import Path
from typing import Dict, Union

# Librerias de terceros:
from flask import Flask, abort, flash, redirect, request, render_template, url_for, current_app
from flask.cli import FlaskGroup
from flask_alembic import Alembic
from flask_login import LoginManager, UserMixin, current_user, login_required, login_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from flask_uploads import IMAGES, UploadSet, configure_uploads
from loguru import logger as log
from pg8000.dbapi import ProgrammingError as PGProgrammingError
from pg8000.exceptions import DatabaseError
from sqlalchemy.exc import OperationalError, ProgrammingError
from wtforms import BooleanField, DecimalField, DateField, IntegerField, PasswordField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired

# Recursos locales:
from now_lms.version import PRERELEASE, VERSION

# < --------------------------------------------------------------------------------------------- >
# Metadatos
__version__: str = VERSION
DESARROLLO: bool = (
    (PRERELEASE is not None) or ("FLASK_DEBUG" in environ) or (environ.get("FLASK_ENV") == "development") or ("CI" in environ)
)
APPNAME: str = "NOW LMS"

if DESARROLLO:
    log.warning("Opciones de desarrollo detectadas, favor revise su configuración.")

# < --------------------------------------------------------------------------------------------- >
# Datos predefinidos
TIPOS_DE_USUARIO: list = ["admin", "user", "instructor", "moderator"]

# < --------------------------------------------------------------------------------------------- >
# Directorios de la aplicacion
DIRECTORIO_APP: str = path.abspath(path.dirname(__file__))
DIRECTORIO_PRINCICIPAL: Path = Path(DIRECTORIO_APP).parent.absolute()
DIRECTORIO_PLANTILLAS: str = path.join(DIRECTORIO_APP, "templates")
DIRECTORIO_ARCHIVOS: str = path.join(DIRECTORIO_APP, "static")
DIRECTORIO_BASE_ARCHIVOS_DE_USUARIO: str = path.join(DIRECTORIO_APP, "static", "files")
DIRECTORIO_ARCHIVOS_PUBLICOS: str = path.join(DIRECTORIO_BASE_ARCHIVOS_DE_USUARIO, "public")
DIRECTORIO_ARCHIVOS_PRIVADOS: str = path.join(DIRECTORIO_BASE_ARCHIVOS_DE_USUARIO, "private")


# < --------------------------------------------------------------------------------------------- >
# Directorios utilizados para la carga de archivos.
DIRECTORIO_IMAGENES: str = path.join(DIRECTORIO_ARCHIVOS_PUBLICOS, "img")
CARGA_IMAGENES = UploadSet("photos", IMAGES)

# < --------------------------------------------------------------------------------------------- >
# Ubicación predeterminada de base de datos SQLITE
if name == "nt":
    SQLITE: str = "sqlite:///" + str(DIRECTORIO_PRINCICIPAL) + "\\now_lms.db"
else:
    SQLITE = "sqlite:///" + str(DIRECTORIO_PRINCICIPAL) + "/now_lms.db"


# < --------------------------------------------------------------------------------------------- >
# Configuración de la aplicación, siguiendo "Twelve Factors App" las opciones se leen del entorno
# o se utilizan valores predeterminados.
CONFIGURACION: Dict = {
    "ADMIN_USER": environ.get("LMS_USER") or "lms-admin",
    "ADMIN_PSWD": environ.get("LMS_PSWD") or "lms-admin",
    "SECRET_KEY": environ.get("LMS_KEY") or "dev",
    "SQLALCHEMY_DATABASE_URI": environ.get("LMS_DB") or SQLITE,
    "SQLALCHEMY_TRACK_MODIFICATIONS": "False",
    # Carga de archivos
    "UPLOADED_PHOTOS_DEST": DIRECTORIO_IMAGENES,
}


# < --------------------------------------------------------------------------------------------- >
# Inicialización de extensiones de terceros

alembic: Alembic = Alembic()
administrador_sesion: LoginManager = LoginManager()
database: SQLAlchemy = SQLAlchemy()


# < --------------------------------------------------------------------------------------------- >
# Base de datos relacional

MAXIMO_RESULTADOS_EN_CONSULTA_PAGINADA: int = 3
# Para hacer feliz a Sonar Cloud
# https://sonarcloud.io/project/overview?id=bmosoluciones_now-lms
LLAVE_FORONEA_CURSO: str = "curso.codigo"
LLAVE_FORONEA_USUARIO: str = "usuario.usuario"


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
    usuario = database.Column(database.String(150), nullable=False)
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
    # draft, public, active, closed
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

    curso = database.Column(database.String(10), database.ForeignKey(LLAVE_FORONEA_CURSO), nullable=False)
    nombre = database.Column(database.String(150), nullable=False)
    indice = database.Column(database.Integer())


class CursoRecurso(database.Model, BaseTabla):  # type: ignore[name-defined]
    """Un curso consta de una serie de recursos."""

    curso = database.Column(database.String(10), database.ForeignKey(LLAVE_FORONEA_CURSO), nullable=False)
    seccion = database.Column(database.Integer(), database.ForeignKey("curso_seccion.id"), nullable=False)
    nombre = database.Column(database.String(150), nullable=False)
    indice = database.Column(database.Integer())


class Files(database.Model, BaseTabla):  # type: ignore[name-defined]
    """Listado de archivos que se han cargado a la aplicacion."""

    archivo = database.Column(database.String(100), nullable=False)
    tipo = database.Column(database.String(15), nullable=False)
    hash = database.Column(database.String(50), nullable=False)
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


# < --------------------------------------------------------------------------------------------- >
# Control de acceso a la aplicación


@administrador_sesion.user_loader
def cargar_sesion(identidad):
    """Devuelve la entrada correspondiente al usuario que inicio sesión."""
    if identidad is not None:
        return Usuario.query.get(identidad)
    return None


@administrador_sesion.unauthorized_handler
def no_autorizado():
    """Redirecciona al inicio de sesión usuarios no autorizados."""
    flash("Favor iniciar sesión para acceder al sistema.")
    return INICIO_SESION


def proteger_passwd(clave):
    """Devuelve una contraseña salteada con bcrytp."""
    from bcrypt import hashpw, gensalt

    return hashpw(clave.encode(), gensalt())


def validar_acceso(usuario_id, acceso):
    """Verifica el inicio de sesión del usuario."""
    from bcrypt import checkpw

    registro = Usuario.query.filter_by(usuario=usuario_id).first()
    if registro is not None:
        clave_validada = checkpw(acceso.encode(), registro.acceso)
    else:
        clave_validada = False
    return clave_validada


# < --------------------------------------------------------------------------------------------- >
# Definición de formularios
class LoginForm(FlaskForm):
    """Formulario de inicio de sesión."""

    usuario = StringField(validators=[DataRequired()])
    acceso = PasswordField(validators=[DataRequired()])
    inicio_sesion = SubmitField()


class LogonForm(FlaskForm):
    """Formulario para crear un nuevo usuario."""

    usuario = StringField(validators=[DataRequired()])
    acceso = PasswordField(validators=[DataRequired()])
    nombre = StringField(validators=[DataRequired()])
    apellido = StringField(validators=[DataRequired()])
    correo_electronico = StringField(validators=[DataRequired()])


class CurseForm(FlaskForm):
    """Formulario para crear un nuevo curso."""

    nombre = StringField(validators=[DataRequired()])
    codigo = StringField(validators=[DataRequired()])
    descripcion = StringField(validators=[DataRequired()])
    publico = BooleanField(validators=[])
    auditable = BooleanField(validators=[])
    certificado = BooleanField(validators=[])
    precio = DecimalField(validators=[])
    capacidad = IntegerField(validators=[])
    fecha_inicio = DateField(validators=[])
    fecha_fin = DateField(validators=[])
    duracion = IntegerField(validators=[])
    nivel = SelectField("User", choices=[(0, "Introductorio"), (1, "Principiante"), (2, "Intermedio"), (2, "Avanzado")])


# < --------------------------------------------------------------------------------------------- >
# Definición de la aplicación
lms_app = Flask(
    "now_lms",
    template_folder=DIRECTORIO_PLANTILLAS,
    static_folder=DIRECTORIO_ARCHIVOS,
)
lms_app.config.from_mapping(CONFIGURACION)


with lms_app.app_context():
    alembic.init_app(lms_app)
    administrador_sesion.init_app(lms_app)
    database.init_app(lms_app)
    configure_uploads(app=lms_app, upload_sets=[CARGA_IMAGENES])
    try:
        CONFIG = Configuracion.query.first()
    except OperationalError:
        CONFIG = None
    except ProgrammingError:
        CONFIG = None
    except PGProgrammingError:
        CONFIG = None
    except DatabaseError:
        CONFIG = None
    if CONFIG:
        log.info("Configuración detectada.")
    else:
        log.warning("No se pudo cargar la configuración.")
    lms_app.jinja_env.globals["current_user"] = current_user
    lms_app.jinja_env.globals["config"] = CONFIG
    lms_app.jinja_env.globals["docente_asignado"] = verifica_docente_asignado_a_curso
    lms_app.jinja_env.globals["moderador_asignado"] = verifica_moderador_asignado_a_curso
    lms_app.jinja_env.globals["estudiante_asignado"] = verifica_estudiante_asignado_a_curso


def init_app():
    """Funcion auxiliar para iniciar la aplicacion."""
    with current_app.app_context():
        if DESARROLLO:
            log.warning("Modo desarrollo detectado.")
            log.warning("Iniciando una base de datos nueva.")
            database.drop_all()
        if not database.engine.has_table("usuario"):
            log.info("Iniciando Configuracion de la aplicacion.")
            log.info("Creando esquema de base de datos.")
            database.create_all()
            log.info("Creando usuario administrador.")
            administrador = Usuario(
                usuario=CONFIGURACION.get("ADMIN_USER"),
                acceso=proteger_passwd(CONFIGURACION.get("ADMIN_PSWD")),
                tipo="admin",
                activo=True,
            )
            config = Configuracion(
                titulo="NOW LMS",
                descripcion="Sistema de aprendizaje en linea.",
            )
            database.session.add(administrador)
            database.session.add(config)
            database.session.commit()

        else:
            log.warning("NOW LMS ya se encuentra configurado.")
            log.warning("Intente ejecutar 'python -m now_lms'")


@lms_app.cli.command()
def setup():  # pragma: no cover
    """Inicia al aplicacion."""
    with current_app.app_context():
        init_app()


@lms_app.cli.command()
def serve():  # pragma: no cover
    """Servidor WSGI predeterminado."""
    from waitress import serve as server

    if not CONFIG:
        init_app()

    if environ.get("LMS_PORT"):
        PORT: int = int(environ.get("LMS_PORT"))
    elif environ.get("PORT"):
        PORT = int(environ.get("PORT"))
    else:
        PORT = 8080
    if DESARROLLO:
        THREADS: int = 4
    else:
        if environ.get("LMS_THREADS"):
            THREADS = int(environ.get("LMS_THREADS"))
        else:
            THREADS = (cpu_count() * 2) + 1
    log.info("Iniciando servidor WSGI en puerto {puerto} con {threads} hilos.", puerto=PORT, threads=THREADS)
    server(app=lms_app, port=int(PORT), threads=THREADS)


@lms_app.errorhandler(404)
def error_404(error):
    """Pagina personalizada para recursos no encontrados."""
    assert error is not None
    return render_template("404.html"), 404


@lms_app.errorhandler(403)
def error_403(error):
    """Pagina personalizada para recursos no autorizados."""
    assert error is not None
    return render_template("403.html"), 403


# < --------------------------------------------------------------------------------------------- >
# Interfaz de linea de comandos
COMMAND_LINE_INTERFACE = FlaskGroup(
    help="""\
Interfaz de linea de comandos para la administración de NOW LMS.
"""
)


def command(as_module=False) -> None:
    """Linea de comandos para administración de la aplicacion."""
    COMMAND_LINE_INTERFACE.main(args=sys.argv[1:], prog_name="python -m flask" if as_module else None)


# < --------------------------------------------------------------------------------------------- >
# Funciones auxiliares
def asignar_curso_a_instructor(curso_codigo: Union[None, str] = None, usuario_id: Union[None, str] = None):
    """Asigna un usuario como instructor de un curso."""
    ASIGNACION = DocenteCurso(curso=curso_codigo, usuario=usuario_id, vigente=True, creado_por=current_user.usuario)
    database.session.add(ASIGNACION)
    database.session.commit()


def asignar_curso_a_moderador(curso_codigo: Union[None, str] = None, usuario_id: Union[None, str] = None):
    """Asigna un usuario como moderador de un curso."""
    ASIGNACION = ModeradorCurso(usuario=usuario_id, curso=curso_codigo, vigente=True, creado_por=current_user.usuario)
    database.session.add(ASIGNACION)
    database.session.commit()


def asignar_curso_a_estudiante(curso_codigo: Union[None, str] = None, usuario_id: Union[None, str] = None):
    """Asigna un usuario como moderador de un curso."""
    ASIGNACION = EstudianteCurso(
        creado_por=current_user.usuario,
        curso=curso_codigo,
        usuario=usuario_id,
        vigente=True,
    )
    database.session.add(ASIGNACION)
    database.session.commit()


def cambia_tipo_de_usuario_por_id(id_usuario: Union[None, str] = None, nuevo_tipo: Union[None, str] = None):
    """
    Cambia el estatus de un usuario del sistema.

    Los valores reconocidos por el sistema son: admin, user, instructor, moderator.
    """
    USUARIO = Usuario.query.filter_by(usuario=id_usuario).first()
    USUARIO.tipo = nuevo_tipo
    database.session.commit()


def cambia_estado_curso_por_id(id_curso: Union[None, str, int] = None, nuevo_estado: Union[None, str] = None):
    """
    Cambia el estatus de un curso.

    Los valores reconocidos por el sistema son: draft, public, open, closed.
    """
    CURSO = Curso.query.filter_by(codigo=id_curso).first()
    CURSO.estado = nuevo_estado
    database.session.commit()


def cambia_curso_publico(id_curso: Union[None, str, int] = None):
    """Cambia el estatus publico de un curso."""
    CURSO = Curso.query.filter_by(codigo=id_curso).first()
    if CURSO.publico:
        CURSO.publico = False
    else:
        CURSO.publico = True
    database.session.commit()


# < --------------------------------------------------------------------------------------------- >
# Definición de rutas/vistas


def perfil_requerido(perfil_id):
    """Comprueba si un usuario tiene acceso a un recurso determinado en base a su tipo."""

    def decorator_verifica_acceso(func):
        @wraps(func)
        def wrapper(*args, **kwargs):

            if (current_user.is_authenticated and current_user.tipo == perfil_id) or current_user.tipo == "admin":
                return func(*args, **kwargs)

            else:
                flash("No se encuentra autorizado a acceder al recurso solicitado.")
                return abort(403)

        return wrapper

    return decorator_verifica_acceso


# < --------------------------------------------------------------------------------------------- >
# Definición de rutas/vistas
# pylint: disable=singleton-comparison

# <-------- Autenticación de usuarios  -------->
INICIO_SESION = redirect("/login")


@lms_app.route("/login", methods=["GET", "POST"])
def inicio_sesion():
    """Inicio de sesión del usuario."""
    form = LoginForm()
    if form.validate_on_submit():
        if validar_acceso(form.usuario.data, form.acceso.data):
            identidad = Usuario.query.filter_by(usuario=form.usuario.data).first()
            if identidad.activo:
                login_user(identidad)
                return redirect(url_for("panel"))
            else:
                flash("Su cuenta esta inactiva.")
                return INICIO_SESION
        else:
            flash("Inicio de Sesion Incorrecto.")
            return INICIO_SESION
    return render_template("auth/login.html", form=form, titulo="Inicio de Sesion - NOW LMS")


@lms_app.route("/logon", methods=["GET", "POST"])
def crear_cuenta():
    """Crear cuenta de usuario."""
    form = LogonForm()
    if form.validate_on_submit() or request.method == "POST":
        usuario_ = Usuario(
            usuario=form.usuario.data,
            acceso=proteger_passwd(form.acceso.data),
            nombre=form.nombre.data,
            apellido=form.apellido.data,
            correo_electronico=form.correo_electronico.data,
            tipo="user",
            activo=False,
        )
        try:
            database.session.add(usuario_)
            database.session.commit()
            flash("Cuenta creada exitosamente.")
            return INICIO_SESION
        except OperationalError:
            flash("Error al crear la cuenta.")
            return redirect("/logon")
    else:
        return render_template("auth/logon.html", form=form, titulo="Crear cuenta - NOW LMS")


@lms_app.route("/new_user", methods=["GET", "POST"])
def crear_usuario():
    """Crear manualmente una cuenta de usuario."""
    form = LogonForm()
    if form.validate_on_submit() or request.method == "POST":
        usuario_ = Usuario(
            usuario=form.usuario.data,
            acceso=proteger_passwd(form.acceso.data),
            nombre=form.nombre.data,
            apellido=form.apellido.data,
            correo_electronico=form.correo_electronico.data,
            tipo="user",
            activo=False,
        )
        try:
            database.session.add(usuario_)
            database.session.commit()
            flash("Usuario creado exitosamente.")
            return redirect(url_for("usuario", id_usuario=form.usuario.data))
        except OperationalError:
            flash("Error al crear la cuenta.")
            return redirect("/new_user")
    else:
        return render_template(
            "learning/nuevo_usuario.html",
            form=form,
        )


@lms_app.route("/exit")
@lms_app.route("/logout")
@lms_app.route("/salir")
def cerrar_sesion():
    """Finaliza la sesion actual."""
    logout_user()
    return redirect("/home")


# <-------- Estructura general de al aplicación  -------->
@lms_app.route("/")
@lms_app.route("/home")
@lms_app.route("/index")
def home():
    """Página principal de la aplicación."""
    CURSOS = Curso.query.filter(Curso.publico == True, Curso.estado == "public").paginate(  # noqa: E712
        request.args.get("page", default=1, type=int), 6, False
    )
    return render_template("inicio/mooc.html", cursos=CURSOS)


@lms_app.route("/dashboard")
@lms_app.route("/panel")
@login_required
def panel():
    """Panel principal de la aplicacion."""
    return render_template("inicio/panel.html")


@lms_app.route("/student")
@login_required
def pagina_estudiante():
    """Perfil de usuario."""
    return render_template("perfiles/estudiante.html")


@lms_app.route("/moderator")
@login_required
def pagina_moderador():
    """Perfil de usuario moderador."""
    return render_template("perfiles/moderador.html")


@lms_app.route("/instructor")
@login_required
def pagina_instructor():
    """Perfil de usuario instructor."""
    return render_template("perfiles/instructor.html")


@lms_app.route("/admin")
@login_required
def pagina_admin():
    """Perfil de usuario administrador."""
    return render_template("perfiles/admin.html", inactivos=Usuario.query.filter_by(activo=False).count() or 0)


# <-------- Aprendizaje -------->
@lms_app.route("/program")
@lms_app.route("/programa")
def programa():
    """
    Página principal del programa.

    Un programa puede constar de uno o mas cursos individuales
    """


@lms_app.route("/new_curse", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def nuevo_curso():
    """Formulario para crear un nuevo usuario."""
    form = CurseForm()
    if form.validate_on_submit() or request.method == "POST":
        nuevo_curso_ = Curso(
            nombre=form.nombre.data,
            codigo=form.codigo.data,
            descripcion=form.descripcion.data,
            estado="draft",
            publico=form.publico.data,
            auditable=form.auditable.data,
            certificado=form.certificado.data,
            precio=form.precio.data,
            capacidad=form.capacidad.data,
            fecha_inicio=form.fecha_inicio.data,
            fecha_fin=form.fecha_fin.data,
            duracion=form.duracion.data,
            creado_por=current_user.usuario,
            nivel=form.nivel.data,
        )
        try:
            database.session.add(nuevo_curso_)
            database.session.commit()
            asignar_curso_a_instructor(curso_codigo=form.codigo.data, usuario_id=current_user.usuario)
            flash("Curso creado exitosamente.")
            return redirect(url_for("curso", course_code=form.codigo.data))
        except OperationalError:
            flash("Hubo en error al crear su curso.")
            return redirect("/instructor")
    else:
        return render_template("learning/nuevo_curso.html", form=form)


@lms_app.route("/courses")
@lms_app.route("/cursos")
@login_required
def cursos():
    """Pagina principal del curso."""
    if current_user.tipo == "admin":
        lista_cursos = Curso.query.paginate(
            request.args.get("page", default=1, type=int), MAXIMO_RESULTADOS_EN_CONSULTA_PAGINADA, False
        )
    else:
        lista_cursos = (
            Curso.query.join(Curso.creado_por)
            .filter(Usuario.id == current_user.id)
            .paginate(request.args.get("page", default=1, type=int), MAXIMO_RESULTADOS_EN_CONSULTA_PAGINADA, False)
        )
    return render_template("learning/curso_lista.html", consulta=lista_cursos)


@lms_app.route("/course/<course_code>")
@lms_app.route("/curso")
def curso(course_code):
    """Pagina principal del curso."""
    return render_template(
        "learning/curso.html",
        curso=Curso.query.filter_by(codigo=course_code).first(),
        secciones=CursoSeccion.query.filter_by(curso=course_code).all(),
        recursos=CursoRecurso.query.filter_by(curso=course_code).all(),
    )


# <-------- Administración -------->
@lms_app.route("/users")
@login_required
@perfil_requerido("admin")
def usuarios():
    """Lista de usuarios con acceso a al aplicación."""
    CONSULTA = Usuario.query.paginate(
        request.args.get("page", default=1, type=int), MAXIMO_RESULTADOS_EN_CONSULTA_PAGINADA, False
    )

    return render_template(
        "admin/users.html",
        consulta=CONSULTA,
    )


@lms_app.route("/inactive_users")
@login_required
@perfil_requerido("admin")
def usuarios_inactivos():
    """Lista de usuarios con acceso a al aplicación."""
    CONSULTA = Usuario.query.filter_by(activo=False).paginate(
        request.args.get("page", default=1, type=int), MAXIMO_RESULTADOS_EN_CONSULTA_PAGINADA, False
    )

    return render_template(
        "admin/inactive_users.html",
        consulta=CONSULTA,
    )


@lms_app.route("/user/<id_usuario>")
@login_required
@perfil_requerido("admin")
def usuario(id_usuario):
    """Acceso administrativo al perfil de un usuario."""
    perfil_usuario = Usuario.query.filter_by(usuario=id_usuario).first()
    # La misma plantilla del perfil de usuario con permisos elevados como
    # activar desactivar el perfil o cambiar el perfil del usuario.
    return render_template("inicio/perfil.html", perfil=perfil_usuario)


# <-------- Espacio del usuario -------->
@lms_app.route("/perfil")
@login_required
def perfil():
    """Perfil del usuario."""
    perfil_usuario = Usuario.query.filter_by(usuario=current_user.usuario).first()
    return render_template("inicio/perfil.html", perfil=perfil_usuario)


# <-------- Funciones Auxiliares -------->
@lms_app.route("/set_user_as_active/<user_id>")
@login_required
@perfil_requerido("admin")
def activar_usuario(user_id):
    """Estable el usuario como activo y redirecciona a la vista dada."""
    perfil_usuario = Usuario.query.filter_by(usuario=user_id).first()
    perfil_usuario.activo = True
    database.session.add(perfil_usuario)
    database.session.commit()
    return redirect(url_for("usuario", id_usuario=user_id))


@lms_app.route("/set_user_as_inactive/<user_id>")
@login_required
@perfil_requerido("admin")
def inactivar_usuario(user_id):
    """Estable el usuario como activo y redirecciona a la vista dada."""
    perfil_usuario = Usuario.query.filter_by(usuario=user_id).first()
    perfil_usuario.activo = False
    database.session.add(perfil_usuario)
    database.session.commit()
    return redirect(url_for("usuario", id_usuario=user_id))


@lms_app.route("/delete_user/<user_id>")
@login_required
@perfil_requerido("admin")
def eliminar_usuario(user_id):
    """Elimina un usuario por su id y redirecciona a la vista dada."""
    perfil_usuario = Usuario.query.filter(Usuario.usuario == user_id)
    perfil_usuario.delete()
    database.session.commit()
    return redirect(url_for(request.args.get("ruta", default="home", type=str)))


@lms_app.route("/change_user_tipo")
@login_required
@perfil_requerido("admin")
def cambiar_tipo_usario():
    """Actualiza el tipo de usuario."""
    cambia_tipo_de_usuario_por_id(
        id_usuario=request.args.get("user"),
        nuevo_tipo=request.args.get("type"),
    )
    return redirect(url_for("usuario", id_usuario=request.args.get("user")))


@lms_app.route("/change_curse_status")
@login_required
@perfil_requerido("admin")
def cambiar_estatus_curso():
    """Actualiza el estatus de un curso."""
    cambia_estado_curso_por_id(
        id_curso=request.args.get("curse"),
        nuevo_estado=request.args.get("status"),
    )
    return redirect(url_for("curso", course_code=request.args.get("curse")))


@lms_app.route("/change_curse_public")
@login_required
@perfil_requerido("admin")
def cambiar_curso_publico():
    """Actualiza el estado publico de un curso."""
    cambia_curso_publico(
        id_curso=request.args.get("curse"),
    )
    return redirect(url_for("curso", course_code=request.args.get("curse")))


# Los servidores WSGI buscan por defecto una app
app = lms_app
