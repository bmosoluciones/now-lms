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
from os import environ, name, path, cpu_count
from pathlib import Path
from typing import Dict

# Librerias de terceros:
from flask import Flask, flash, redirect, request, render_template, url_for, current_app
from flask.cli import FlaskGroup
from flask_alembic import Alembic
from flask_login import LoginManager, UserMixin, current_user, login_required, login_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from loguru import logger as log
from sqlalchemy.exc import OperationalError
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired

# Recursos locales:
from now_lms.version import VERSION

# < --------------------------------------------------------------------------------------------- >
# Metadatos
STATUS: str = "development"
__all__: tuple = VERSION

# < --------------------------------------------------------------------------------------------- >
# Directorios de la aplicacion
DIRECTORIO_APP: str = path.abspath(path.dirname(__file__))
DIRECTORIO_PRINCICIPAL: Path = Path(DIRECTORIO_APP).parent.absolute()
DIRECTORIO_PLANTILLAS: str = path.join(DIRECTORIO_APP, "templates")
DIRECTORIO_ARCHIVOS: str = path.join(DIRECTORIO_APP, "static")


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
}


# < --------------------------------------------------------------------------------------------- >
# Inicialización de extensiones de terceros

alembic: Alembic = Alembic()
administrador_sesion: LoginManager = LoginManager()
database: SQLAlchemy = SQLAlchemy()


# < --------------------------------------------------------------------------------------------- >
# Base de datos relacional

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
    usuario = database.Column(database.String(150), nullable=False)
    acceso = database.Column(database.LargeBinary(), nullable=False)
    nombre = database.Column(database.String(100))
    apellido = database.Column(database.String(100))
    # Tipo puede ser: admin, user, instructor, moderator
    tipo = database.Column(database.String(20))
    activo = database.Column(database.Boolean())
    genero = database.Column(database.String(10))
    nacimiento = database.Column(database.Date())


class Curso(database.Model, BaseTabla):  # type: ignore[name-defined]
    """Un curso es la base del aprendizaje en NOW LMS."""

    nombre = database.Column(database.String(150), nullable=False)
    codigo = database.Column(database.String(20), nullable=False)


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
    inicio_sesion = SubmitField()


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
    lms_app.jinja_env.globals["current_user"] = current_user
    try:
        CURSOS = Curso.query.all()
    except OperationalError:
        CURSOS = None
    lms_app.jinja_env.globals["cursos"] = CURSOS


def init_app():
    """Funcion auxiliar para iniciar la aplicacion"""
    with current_app.app_context():
        if STATUS == "development":
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
            database.session.add(administrador)
            database.session.commit()

        else:
            log.warning("NOW LMS ya se encuentra configurado.")
            log.warning("Intente ejecutar 'python -m now_lms'")


@lms_app.cli.command()
def setup():  # pragma: no cover
    """Inicia al aplicacion"""
    with current_app.app_context():
        init_app()


@lms_app.cli.command()
def serve():  # pragma: no cover
    """Servidor WSGI predeterminado"""
    from waitress import serve as server

    PORT: str = environ.get("LMS_PORT") or "8080"
    if STATUS == "development":
        THREADS: int = 4
    else:
        THREADS = int(environ.get("LMS_THREADS")) or ((cpu_count() * 2) + 1)
    log.info("Iniciando servidor WSGI en puerto {puerto} con {threads} hilos.", puerto=PORT, threads=THREADS)
    server(app=lms_app, port=int(PORT), threads=THREADS)


@lms_app.errorhandler(404)
def error_404(error):
    """Pagina personalizada para recursos no encontrados."""
    assert error is not None
    return render_template("404.html"), 404


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
# Definición de rutas/vistas
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


@lms_app.route("/exit")
@lms_app.route("/logout")
@lms_app.route("/salir")
def cerrar_sesion():
    """Finaliza la sesion actual."""
    logout_user()
    return redirect("/home")


@lms_app.route("/")
@lms_app.route("/home")
@lms_app.route("/index")
def home():
    """Página principal de la aplicación."""
    return render_template("inicio/mooc.html")


@lms_app.route("/dashboard")
@lms_app.route("/panel")
@login_required
def panel():
    """Panel principal de la aplicacion."""
    return render_template("inicio/panel.html")


@lms_app.route("/program")
@lms_app.route("/programa")
def programa():
    """
    Página principal del programa.

    Un programa puede constar de uno o mas cursos individuales
    """


@lms_app.route("/course")
@lms_app.route("/curso")
def curso():
    """Pagina principal del curso."""


@lms_app.route("/user")
@lms_app.route("/usuario")
@login_required
def usuario():
    """Perfil de usuario."""
    return render_template("inicio/usuario.html")


@lms_app.route("/student")
@login_required
def pagina_estudiante():
    """Perfil de usuario."""
    return render_template("perfiles/estudiante.html")


@lms_app.route("/moderator")
@login_required
def pagina_moderador():
    """Perfil de usuario."""
    return render_template("perfiles/instructor.html")


@lms_app.route("/instructor")
@login_required
def pagina_instructor():
    """Perfil de usuario."""
    return render_template("perfiles/moderador.html")


@lms_app.route("/admin")
@login_required
def pagina_admin():
    """Perfil de usuario."""
    return render_template("perfiles/admin.html")
