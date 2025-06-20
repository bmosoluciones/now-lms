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
# Contributors:
# - William José Moreno Reyes


"""
NOW Learning Management System.

Simple to {install, use, configure and maintain} learning management system.

python3 -m venv venv
source venv/bin/activate
python3 -m pip install -e .
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
    crear_certificacion,
    crear_certificados,
    crear_curso_demo,
    crear_curso_demo1,
    crear_curso_demo2,
    crear_curso_demo3,
    crear_curso_predeterminado,
    crear_etiquetas,
    crear_programa,
    crear_recurso_descargable,
    crear_usuarios_predeterminados,
    populate_custmon_data_dir,
    populate_custom_theme_dir,
    system_info,
)
from now_lms.db.tools import (
    crear_configuracion_predeterminada,
    cuenta_cursos_por_programa,
    get_addsense_code,
    get_addsense_meta,
    logo_perzonalizado,
    verifica_docente_asignado_a_curso,
    verifica_estudiante_asignado_a_curso,
    verifica_moderador_asignado_a_curso,
    verificar_avance_recurso,
    get_paypal_id,
)
from now_lms.logs import log
from now_lms.misc import (
    ESTILO_ALERTAS,
    ICONOS_RECURSOS,
    INICIO_SESION,
    concatenar_parametros_a_url,
    markdown_to_clean_hmtl,
)
from now_lms.themes import current_theme
from now_lms.version import VERSION
from now_lms.vistas._helpers import get_current_course_logo, get_site_logo
from now_lms.vistas.categories import category
from now_lms.vistas.certificates import certificate
from now_lms.vistas.courses import course
from now_lms.vistas.groups import group
from now_lms.vistas.home import home
from now_lms.vistas.messages import msg
from now_lms.vistas.paypal import check_paypal_enabled, paypal
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
        flask_app.register_blueprint(paypal)
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
def cargar_sesion(identidad):
    """Devuelve la entrada correspondiente al usuario que inicio sesión desde la base de datos."""
    if identidad is not None:
        return database.session.get(Usuario, identidad)
    return None


@administrador_sesion.unauthorized_handler
def no_autorizado():
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


# Errores personalizados
def handle_402(error):
    """Pagina personalizada para recursos que requieren pago."""

    return render_template("error_pages/403.html", error=error)


lms_app.register_error_handler(PaymentRequired, handle_402)


# Errores standares
@lms_app.errorhandler(403)
@cache.cached()
def error_403(error):
    """Pagina personalizada para recursos no autorizados."""

    return render_template("error_pages/403.html", error=error), 403


@lms_app.errorhandler(404)
@cache.cached()
def error_404(error):
    """Pagina personalizada para recursos no encontrados."""

    return render_template("error_pages/404.html", error=error), 404


@lms_app.errorhandler(405)
@cache.cached()
def error_405(error):
    """Pagina personalizada para metodos no permitidos."""
    return render_template("error_pages/405.html", error=error), 405


@lms_app.errorhandler(500)
@cache.cached()
def error_500(error):
    """Pagina personalizada para recursos no autorizados."""
    return render_template("error_pages/500.html", error=error), 500


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
lms_app.jinja_env.globals["estilo_alerta"] = ESTILO_ALERTAS
lms_app.jinja_env.globals["logo_perzonalizado"] = logo_perzonalizado
lms_app.jinja_env.globals["parametros_url"] = concatenar_parametros_a_url
lms_app.jinja_env.globals["config"] = carga_configuracion_del_sitio_web_desde_db
lms_app.jinja_env.globals["version"] = VERSION
lms_app.jinja_env.globals["info"] = app_info(lms_app)
lms_app.jinja_env.globals["pyversion"] = python_version()
lms_app.jinja_env.globals["mkdonw2thml"] = markdown_to_clean_hmtl
lms_app.jinja_env.globals["cuenta_cursos"] = cuenta_cursos_por_programa
lms_app.jinja_env.globals["adsense_meta"] = get_addsense_meta
lms_app.jinja_env.globals["adsense_code"] = get_addsense_code
lms_app.jinja_env.globals["paypal_enabled"] = check_paypal_enabled
lms_app.jinja_env.globals["paypal_id"] = get_paypal_id
lms_app.jinja_env.globals["current_theme"] = current_theme
lms_app.jinja_env.globals["course_logo"] = get_current_course_logo
lms_app.jinja_env.globals["site_logo"] = get_site_logo


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
        log.debug("Cargando datos de muestra.")
        crear_configuracion_predeterminada()
        crear_curso_predeterminado()
        crear_usuarios_predeterminados()
        crear_certificados()
        crear_certificacion()
        populate_custmon_data_dir()
        populate_custom_theme_dir()
        log.debug("Datos de muestra cargado correctamente.")
        if with_examples:
            log.debug("Cargando datos de prueba.")
            crear_categorias()
            crear_etiquetas()
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


def init_app(with_examples=False):
    """Funcion auxiliar para iniciar la aplicacion."""

    from now_lms.db.tools import check_db_access, database_is_populated

    DB_ACCESS = check_db_access(lms_app)
    DB_INICIALIZADA = database_is_populated(lms_app)

    if DB_ACCESS:
        log.trace("Acceso a base de datos verificado.")
        if DB_INICIALIZADA:
            log.trace("Base de datos inicializada.")
            return True
        else:
            log.info("Iniciando nueva base de datos.")
            initial_setup(with_examples=with_examples)
            return True
    else:
        log.trace("No se pudo acceder a la base de datos.")
        return False


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
@click.option("--with-testdata", is_flag=True, default=False, help="Load data for testing.")
def db_init(with_examples=False, with_testdata=False):  # pragma: no cover
    """Init a new database."""
    with lms_app.app_context():
        from now_lms.db.tools import database_is_populated

        if not database_is_populated(lms_app):

            initial_setup(with_examples)
            if with_testdata:
                from now_lms.db.data_test import crear_data_para_pruebas

                crear_data_para_pruebas()
        else:
            log.info("Database already initialised.")


@lms_app.cli.command()
def db_seed():
    """Setup a new develoment database."""

    from now_lms.db.data_test import crear_data_para_pruebas

    with lms_app.app_context():
        initial_setup(with_examples=True)
        crear_data_para_pruebas()


@lms_app.cli.command()
def db_backup():  # pragma: no cover
    """Make a backup of system data."""
    pass


@lms_app.cli.command()
def db_backup_restore():  # pragma: no cover
    """Restore the system from a backup."""
    pass


@lms_app.cli.command()
def db_migrate():  # pragma: no cover
    """Update dabatase schema."""
    alembic.upgrade()


@lms_app.cli.command()
def db_drop():  # pragma: no cover
    """Delete database schema and all the data in it."""
    with lms_app.app_context():
        if click.confirm("This will delete the database and all the data on it. Do you want to continue?", abort=True):
            database.drop_all()


@lms_app.cli.command()
@click.option("--with-examples", is_flag=True, default=False, help="Load example data at setup.")
@click.option("--with-tests", is_flag=True, default=False, help="Load data for testing.")
def db_reset(with_examples=False, with_tests=False) -> None:  # pragma: no cover
    """Drop the system database and populate with init a new one."""
    with lms_app.app_context():
        if click.confirm("This will delete the current database and all the data on it. Do you want to continue?", abort=True):
            cache.clear()
            database.drop_all()
            initial_setup(with_examples, with_tests)


@lms_app.cli.command()
def version():  # pragma: no cover
    """Return the current versión of the software."""
    click.echo(VERSION)


@lms_app.cli.command()
def serve():  # pragma: no cover
    """Serve NOW LMS with the default WSGi server."""
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

    with lms_app.app_context():
        server(app=lms_app, port=int(PORT), threads=THREADS)


# ---------------------------------------------------------------------------------------
# Las vistas de la aplicación se definen su modulos respectivos.
# ---------------------------------------------------------------------------------------
