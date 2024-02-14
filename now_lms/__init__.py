# Copyright 2022 -2023 BMO Soluciones, S.A.
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

# pylint: disable=E1101
# pylint: disable=singleton-comparison

"""
NOW Learning Management System.

Simple to {install, use, configure and maintain} learning management system.

python3 -m venv venv
source venv/bin/activate
lmsctl setup
lmsctl serve

Visit http://127.0.0.1:8080/ in your browser, default user and password are lms-admin

"""

# ---------------------------------------------------------------------------------------
# Libreria estandar
# ---------------------------------------------------------------------------------------
import sys
from os import cpu_count, environ
from platform import python_version

# ---------------------------------------------------------------------------------------
# Librerias de terceros
# ---------------------------------------------------------------------------------------
import click
from flask import Flask, flash, render_template
from flask.cli import FlaskGroup
from flask_alembic import Alembic
from flask_login import LoginManager, current_user
from flask_mail import Mail
from flask_mde import Mde
from flask_uploads import configure_uploads
from pg8000.dbapi import ProgrammingError as PGProgrammingError
from pg8000.exceptions import DatabaseError
from sqlalchemy.exc import OperationalError, ProgrammingError
from werkzeug.exceptions import HTTPException

# ---------------------------------------------------------------------------------------
# Recursos locales
# ---------------------------------------------------------------------------------------
from now_lms.cache import cache
from now_lms.config import (
    CONFIGURACION,
    DESARROLLO,
    DIRECTORIO_ARCHIVOS,
    DIRECTORIO_PLANTILLAS,
    audio,
    files,
    images,
    log_messages,
)
from now_lms.db import Configuracion, Usuario, database
from now_lms.db.info import app_info
from now_lms.db.initial_data import (
    asignar_cursos_a_categoria,
    asignar_cursos_a_etiquetas,
    crear_categorias,
    crear_curso_demo,
    crear_curso_demo1,
    crear_curso_demo2,
    crear_curso_demo3,
    crear_curso_predeterminado,
    crear_etiquetas,
    crear_programa,
    crear_recurso_descargable,
    crear_usuarios_predeterminados,
    system_info,
)
from now_lms.db.tools import (
    crear_configuracion_predeterminada,
    cuenta_cursos_por_programa,
    logo_perzonalizado,
    obtener_estilo_actual,
    verifica_docente_asignado_a_curso,
    verifica_estudiante_asignado_a_curso,
    verifica_moderador_asignado_a_curso,
    verificar_avance_recurso,
)
from now_lms.logs import log
from now_lms.misc import (
    ESTILO,
    ESTILO_ALERTAS,
    ICONOS_RECURSOS,
    INICIO_SESION,
    concatenar_parametros_a_url,
    markdown_to_clean_hmtl,
)
from now_lms.version import VERSION
from now_lms.vistas.categories import category
from now_lms.vistas.certificates import certificate
from now_lms.vistas.courses import course
from now_lms.vistas.groups import group
from now_lms.vistas.home import home
from now_lms.vistas.messages import msg
from now_lms.vistas.profiles.admin import admin_profile
from now_lms.vistas.profiles.instructor import instructor_profile
from now_lms.vistas.profiles.moderator import moderator_profile
from now_lms.vistas.profiles.user import user_profile
from now_lms.vistas.programs import program
from now_lms.vistas.resources import resource_d
from now_lms.vistas.settings import setting
from now_lms.vistas.tags import tag
from now_lms.vistas.users import user
from now_lms.vistas.web_error_codes import web_error

# ---------------------------------------------------------------------------------------
# Metadatos
# ---------------------------------------------------------------------------------------
__version__: str = VERSION
APPNAME: str = "NOW LMS"


# ---------------------------------------------------------------------------------------
# Extensiones de terceros
# ---------------------------------------------------------------------------------------
alembic: Alembic = Alembic()
administrador_sesion: LoginManager = LoginManager()
mde: Mde = Mde()


# ---------------------------------------------------------------------------------------
# Funciones auxiliares para inicializar la aplicación principal.
# ---------------------------------------------------------------------------------------
def inicializa_extenciones_terceros(flask_app: Flask):
    """Inicia extensiones de terceros."""

    log.trace("Iniciando extensiones de terceros")
    with flask_app.app_context():
        database.init_app(flask_app)
        alembic.init_app(flask_app)
        administrador_sesion.init_app(flask_app)
        cache.init_app(flask_app)
        mde.init_app(flask_app)
        if environ.get("PROFILER"):  # pragma: no cover
            log.warning("Profiler activo, no se recomienda el uso de esta opción en entornos reales.")
            try:
                from flask_debugtoolbar import DebugToolbarExtension
                from flask_profiler import Profiler

                app.debug = True

                app.config["flask_profiler"] = {
                    "enabled": app.config["DEBUG"],
                    "storage": {"engine": "sqlite"},
                    "basicAuth": {"enabled": True, "username": "admin", "password": "admin"},
                    "ignore": ["^/static/.*"],
                }

                app.config["DEBUG_TB_INTERCEPT_REDIRECTS"] = False
                toolbar = DebugToolbarExtension(app)
                profiler = Profiler(app)
                log.debug("Profiler activo")
            except ModuleNotFoundError:
                toolbar = None
                profiler = None
            except ImportError:
                toolbar = None
                profiler = None

            if toolbar:
                log.info("Flask development toolbar enabled.")
            if profiler:
                log.info("Flask profiler enabled.")
    log.trace("Extensiones de terceros iniciadas correctamente.")


def registrar_modulos_en_la_aplicacion_principal(flask_app: Flask):
    """Registro modulos en la aplicación principal."""

    log.trace("Registrando modulos en la aplicación principal.")

    with flask_app.app_context():
        flask_app.register_blueprint(category)
        flask_app.register_blueprint(certificate)
        flask_app.register_blueprint(course)
        flask_app.register_blueprint(group)
        flask_app.register_blueprint(home)
        flask_app.register_blueprint(msg)
        flask_app.register_blueprint(program)
        flask_app.register_blueprint(resource_d)
        flask_app.register_blueprint(setting)
        flask_app.register_blueprint(tag)
        flask_app.register_blueprint(user)
        # User profiles
        flask_app.register_blueprint(admin_profile)
        flask_app.register_blueprint(instructor_profile)
        flask_app.register_blueprint(moderator_profile)
        flask_app.register_blueprint(user_profile)
        flask_app.register_blueprint(web_error)


# ---------------------------------------------------------------------------------------
# Control de acceso a la aplicación con la extensión flask_login.
# ---------------------------------------------------------------------------------------
@administrador_sesion.user_loader
def cargar_sesion(identidad):  # pragma: no cover
    """Devuelve la entrada correspondiente al usuario que inicio sesión desde la base de datos."""
    if identidad is not None:
        return database.session.get(Usuario, identidad)
    return None


@administrador_sesion.unauthorized_handler
def no_autorizado():  # pragma: no cover
    """Redirecciona al inicio de sesión usuarios no autorizados."""
    flash("Favor iniciar sesión para acceder al sistema.", "warning")
    return INICIO_SESION


# ---------------------------------------------------------------------------------------
# Definición de la aplicación principal.
# ---------------------------------------------------------------------------------------
lms_app = Flask(
    "now_lms",
    template_folder=DIRECTORIO_PLANTILLAS,
    static_folder=DIRECTORIO_ARCHIVOS,
)

# Normalmente los servidores WSGI utilizan "app" or "application" por defecto.
app = lms_app
application = lms_app

# ---------------------------------------------------------------------------------------
# Iniciliazación y configuración de la aplicación principal.
# ---------------------------------------------------------------------------------------
log.trace("Configurando directorio de archivos estaticos: {dir}", dir=DIRECTORIO_ARCHIVOS)
log.trace("Configurando directorio de plantillas: {dir}", dir=DIRECTORIO_PLANTILLAS)
lms_app.config.from_mapping(CONFIGURACION)
log.trace("Configuración de la aplicación cargada correctamente.")
inicializa_extenciones_terceros(lms_app)
registrar_modulos_en_la_aplicacion_principal(lms_app)
log_messages(lms_app)
log.trace("Configurando directorio de carga de imagenes.")
configure_uploads(lms_app, images)
configure_uploads(lms_app, files)
configure_uploads(lms_app, audio)


# ---------------------------------------------------------------------------------------
# Páginas de error personalizadas.
# ---------------------------------------------------------------------------------------


# Reference: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/402
class PaymentRequired(HTTPException):
    """402 Payment Required"""

    code = 402
    description = """
The HTTP 402 Payment Required is a nonstandard response status code that is reserved
for future use. This status code was created to enable digital cash or (micro) payment
systems and would indicate that the requested content is not available until the client
makes a payment.
"""


# Errores standares
def handle_402(error):
    if error:
        return render_template("error_pages/403.html")


lms_app.register_error_handler(PaymentRequired, handle_402)


@lms_app.errorhandler(403)
@cache.cached()
def error_403(error):  # pragma: no cover
    """Pagina personalizada para recursos no autorizados."""
    assert error is not None  # nosec B101
    return render_template("error_pages/403.html"), 403


@lms_app.errorhandler(404)
@cache.cached()
def error_404(error):  # pragma: no cover
    """Pagina personalizada para recursos no encontrados."""
    assert error is not None  # nosec B101
    return render_template("error_pages/404.html"), 404


@lms_app.errorhandler(405)
@cache.cached()
def error_405(error):  # pragma: no cover
    """Pagina personalizada para metodos no permitidos."""
    assert error is not None  # nosec B101
    return render_template("error_pages/405.html"), 405


@lms_app.errorhandler(500)
@cache.cached()
def error_500(error):  # pragma: no cover
    """Pagina personalizada para recursos no autorizados."""
    assert error is not None  # nosec B101
    return render_template("error_pages/500.html"), 500


# ---------------------------------------------------------------------------------------
# Carga configuración del sitio web desde la base de datos.
# ---------------------------------------------------------------------------------------
@cache.cached(timeout=60, key_prefix="site_config")
def carga_configuracion_del_sitio_web_desde_db():  # pragma: no cover
    """Obtiene configuración del sitio web desde la base de datos."""

    with lms_app.app_context():
        try:
            CONFIG = Configuracion.query.first()
        # Si no existe una entrada en la tabla de configuración uno de los siguientes errores puede ocurrir
        # en dependencia del motor de base de datos utilizado.
        except OperationalError:
            CONFIG = None
        except ProgrammingError:
            CONFIG = None
        except PGProgrammingError:
            CONFIG = None
        except DatabaseError:
            CONFIG = None
    return CONFIG


# ---------------------------------------------------------------------------------------
# Definición de variables globales de Jinja2 para su disponibilidad en plantillas HTML
# ---------------------------------------------------------------------------------------
lms_app.jinja_env.globals["current_user"] = current_user
lms_app.jinja_env.globals["docente_asignado"] = verifica_docente_asignado_a_curso
lms_app.jinja_env.globals["moderador_asignado"] = verifica_moderador_asignado_a_curso
lms_app.jinja_env.globals["estudiante_asignado"] = verifica_estudiante_asignado_a_curso
lms_app.jinja_env.globals["verificar_avance_recurso"] = verificar_avance_recurso
lms_app.jinja_env.globals["iconos_recursos"] = ICONOS_RECURSOS
lms_app.jinja_env.globals["estilo"] = ESTILO
lms_app.jinja_env.globals["estilo_alerta"] = ESTILO_ALERTAS
lms_app.jinja_env.globals["obtener_estilo_actual"] = obtener_estilo_actual
lms_app.jinja_env.globals["logo_perzonalizado"] = logo_perzonalizado
lms_app.jinja_env.globals["parametros_url"] = concatenar_parametros_a_url
lms_app.jinja_env.globals["config"] = carga_configuracion_del_sitio_web_desde_db
lms_app.jinja_env.globals["version"] = VERSION
lms_app.jinja_env.globals["info"] = app_info(lms_app)
lms_app.jinja_env.globals["pyversion"] = python_version()
lms_app.jinja_env.globals["mkdonw2thml"] = markdown_to_clean_hmtl
lms_app.jinja_env.globals["cuenta_cursos"] = cuenta_cursos_por_programa


# ---------------------------------------------------------------------------------------
# Funciones auxiliares para la administracion y configuración inicial de la aplicacion
# ---------------------------------------------------------------------------------------
def initial_setup(with_examples=False, with_tests=False):
    """Inicializa una nueva bases de datos"""
    with lms_app.app_context():
        log.info("Creando esquema de base de datos.")
        database.create_all()
        system_info(lms_app)
        log.debug("Esquema de base de datos creado correctamente.")
        log.info("Cargando datos de muestra.")
        crear_configuracion_predeterminada()
        crear_curso_predeterminado()
        crear_usuarios_predeterminados()
        if with_examples:
            crear_categorias()
            crear_etiquetas()
            log.debug("Cargando datos de prueba.")
            crear_curso_demo()
            crear_curso_demo1()
            crear_curso_demo2()
            crear_curso_demo3()
            asignar_cursos_a_etiquetas()
            asignar_cursos_a_categoria()
            crear_programa()
            crear_recurso_descargable()
            log.debug("Datos de muestra cargados correctamente.")
        if with_tests:
            from now_lms.db.data_test import crear_data_para_pruebas

            crear_data_para_pruebas()

    log.info("NOW - LMS iniciado correctamente.")


def init_app(with_examples=False):  # pragma: no cover
    """Funcion auxiliar para iniciar la aplicacion."""

    with lms_app.app_context():
        log.trace("Verificando acceso a base de datos.")
        try:
            from now_lms.db.initial_data import SystemInfo

            consulta = database.session.execute(database.select(SystemInfo)).all()
            if consulta:
                DB_ACCESS = True

        except OperationalError:
            DB_ACCESS = False
        except ProgrammingError:
            DB_ACCESS = False
        except PGProgrammingError:
            DB_ACCESS = False
        except DatabaseError:
            DB_ACCESS = False

        if DB_ACCESS:
            log.trace("Acceso a base de datos verificado.")

            try:
                VERIFICA_EXISTE_CONFIGURACION_DB = carga_configuracion_del_sitio_web_desde_db()
                VERIFICA_EXISTE_USUARIO_DB = Usuario.query.first()
                DB_INICIALIZADA = (VERIFICA_EXISTE_CONFIGURACION_DB is not None) and (VERIFICA_EXISTE_USUARIO_DB is not None)
            except OperationalError:
                DB_INICIALIZADA = False
            except ProgrammingError:
                DB_INICIALIZADA = False
            except PGProgrammingError:
                DB_INICIALIZADA = False
            except DatabaseError:
                DB_INICIALIZADA = False
        else:
            log.warning("Error al acceder a la base de datos.")
            DB_INICIALIZADA = False

        if DB_ACCESS and not DB_INICIALIZADA:
            log.info("Iniciando nueva base de datos.")
            initial_setup(with_examples=with_examples)
        else:
            log.trace("Acceso a base de datos verificado.")
            config = Configuracion.query.first()

        if config.email:
            lms_app.config.update(
                {
                    "MAIL_SERVER": config.mail_server,
                    "MAIL_PORT": config.mail_port,
                    "MAIL_USERNAME": config.mail_username,
                    "MAIL_PASSWORD": config.mail_password,
                    "MAIL_USE_TLS": config.mail_use_tls,
                    "MAIL_USE_SSL": config.mail_use_ssl,
                }
            )
            if DESARROLLO:
                lms_app.config.update({"MAIL_SUPPRESS_SEND": True})
            e_mail = Mail()
            e_mail.init_app(lms_app)


# ---------------------------------------------------------------------------------------
# Interfaz de linea de comandos.
# ---------------------------------------------------------------------------------------
COMMAND_LINE_INTERFACE = FlaskGroup(
    help="""\
Interfaz de linea de comandos para la administración de NOW LMS.
"""
)


def command(as_module=False) -> None:  # pragma: no cover
    """Linea de comandos para administración de la aplicacion."""
    COMMAND_LINE_INTERFACE.main(args=sys.argv[1:], prog_name="python -m flask" if as_module else None)


@lms_app.cli.command()
@click.option("--with-examples", is_flag=True, default=False, help="Load example data at setup.")
@click.option("--with-tests", is_flag=True, default=False, help="Load data for testing.")
def setup(with_examples=False, with_tests=False):  # pragma: no cover
    """Inicia al aplicacion."""
    lms_app.app_context().push()
    initial_setup(with_examples)
    if with_tests:
        from now_lms.db.data_test import crear_data_para_pruebas

        crear_data_para_pruebas()


@lms_app.cli.command()
def release():  # pragma: no cover
    """Devuelve la versión actual del programa."""
    print(VERSION)


@lms_app.cli.command()
def upgrade_db():  # pragma: no cover
    """Actualiza esquema de base de datos."""
    alembic.upgrade()


@lms_app.cli.command()
@click.option("--with-examples", is_flag=True, default=False, help="Load example data at setup.")
@click.option("--with-tests", is_flag=True, default=False, help="Load data for testing.")
def resetdb(with_examples=False, with_tests=False) -> None:  # pragma: no cover
    """Elimina la base de datos actual e inicia una nueva."""
    lms_app.app_context().push()
    cache.clear()
    database.drop_all()
    initial_setup(with_examples, with_tests)


@lms_app.cli.command()
def serve():  # pragma: no cover
    """Servidor WSGI predeterminado."""
    from waitress import serve as server

    if environ.get("LMS_PORT"):
        PORT = environ.get("LMS_PORT")
    elif environ.get("PORT"):
        PORT = environ.get("PORT")
    else:
        PORT = 8080
    if DESARROLLO:
        THREADS = 4
    else:
        if environ.get("LMS_THREADS"):
            THREADS = environ.get("LMS_THREADS")
        else:
            THREADS = (cpu_count() * 2) + 1
    log.info("Iniciando servidor WSGI en puerto {puerto} con {threads} hilos.", puerto=PORT, threads=THREADS)
    server(app=lms_app, port=int(PORT), threads=THREADS)


# ---------------------------------------------------------------------------------------
# Las vistas de la aplicación se definen su modulos respectivos.
# ---------------------------------------------------------------------------------------
