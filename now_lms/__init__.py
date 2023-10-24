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
from collections import OrderedDict
from datetime import datetime
from functools import wraps
from typing import Union
from os import environ, cpu_count, path

# ---------------------------------------------------------------------------------------
# Librerias de terceros
# ---------------------------------------------------------------------------------------
import click
from bleach import clean, linkify
from flask import Flask, abort, flash, redirect, request, render_template, url_for, send_from_directory, current_app
from flask.cli import FlaskGroup
from flask_alembic import Alembic
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from flask_mail import Mail
from flask_mde import Mde
from flask_uploads import AUDIO, DOCUMENTS, IMAGES, UploadSet, configure_uploads, UploadNotAllowed
from markdown import markdown
from pg8000.dbapi import ProgrammingError as PGProgrammingError
from pg8000.exceptions import DatabaseError
from sqlalchemy.exc import ArgumentError, OperationalError, ProgrammingError
from ulid import ULID

# ---------------------------------------------------------------------------------------
# Recursos locales
# ---------------------------------------------------------------------------------------
from now_lms.auth import validar_acceso, proteger_passwd
from now_lms.cache import cache
from now_lms.config import DIRECTORIO_PLANTILLAS, DIRECTORIO_ARCHIVOS, DESARROLLO, CONFIGURACION
from now_lms.db import (
    database,
    Configuracion,
    Curso,
    CursoRecurso,
    CursoRecursoDescargable,
    CursoRecursoAvance,
    CursoSeccion,
    CursoRecursoSlides,
    CursoRecursoSlideShow,
    DocenteCurso,
    EstudianteCurso,
    ModeradorCurso,
    Usuario,
    UsuarioGrupo,
    UsuarioGrupoMiembro,
    Etiqueta,
    Categoria,
    Programa,
    ProgramaCurso,
    Recurso,
    UsuarioGrupoTutor,
    MAXIMO_RESULTADOS_EN_CONSULTA_PAGINADA,
)

from now_lms.db.initial_data import (
    crear_etiquetas,
    crear_categorias,
    crear_curso_predeterminado,
    crear_curso_demo,
    crear_curso_demo1,
    crear_curso_demo2,
    crear_curso_demo3,
    crear_usuarios_predeterminados,
    asignar_cursos_a_etiquetas,
    asignar_cursos_a_categoria,
    crear_programa,
    crear_recurso_descargable,
)
from now_lms.logs import log
from now_lms.db.tools import (
    crear_configuracion_predeterminada,
    crear_indice_recurso,
    verifica_docente_asignado_a_curso,
    verifica_estudiante_asignado_a_curso,
    verifica_moderador_asignado_a_curso,
    verificar_avance_recurso,
    obtener_estilo_actual,
    logo_perzonalizado,
    elimina_logo_perzonalizado,
    elimina_logo_perzonalizado_curso,
    elimina_logo_perzonalizado_programa,
    elimina_imagen_usuario,
    cursos_por_etiqueta,
    cursos_por_categoria,
)
from now_lms.bi import (
    asignar_curso_a_instructor,
    modificar_indice_curso,
    modificar_indice_seccion,
    cambia_estado_curso_por_id,
    reorganiza_indice_curso,
    reorganiza_indice_seccion,
    cambia_tipo_de_usuario_por_id,
    cambia_curso_publico,
    cambia_seccion_publico,
)
from now_lms.forms import (
    ConfigForm,
    LoginForm,
    LogonForm,
    CurseForm,
    CursoRecursoVideoYoutube,
    CursoRecursoArchivoPDF,
    CursoSeccionForm,
    CursoRecursoArchivoAudio,
    CursoRecursoArchivoText,
    CursoRecursoArchivoImagen,
    CursoRecursoExternalCode,
    CursoRecursoExternalLink,
    CursoRecursoMeet,
    GrupoForm,
    ThemeForm,
    MailForm,
    EtiquetaForm,
    CategoriaForm,
    ProgramaForm,
    RecursoForm,
    UserForm,
)
from now_lms.misc import (
    HTML_TAGS,
    ICONOS_RECURSOS,
    TEMPLATES_BY_TYPE,
    ESTILO,
    ESTILO_ALERTAS,
    CURSO_NIVEL,
    GENEROS,
    TIPOS_RECURSOS,
    concatenar_parametros_a_url,
)
from now_lms.version import VERSION

# ---------------------------------------------------------------------------------------
# Metadatos
# ---------------------------------------------------------------------------------------
__version__: str = VERSION
APPNAME: str = "NOW LMS"


# ---------------------------------------------------------------------------------------
# Datos predefinidos y variables globales
# ---------------------------------------------------------------------------------------
TIPOS_DE_USUARIO: list = ["admin", "user", "instructor", "moderator"]
INICIO_SESION = redirect("/login")
PANEL_DE_USUARIO = redirect("/panel")


# ---------------------------------------------------------------------------------------
# Extensiones de terceros
# ---------------------------------------------------------------------------------------
alembic: Alembic = Alembic()
administrador_sesion: LoginManager = LoginManager()
mde: Mde = Mde()


def inicializa_extenciones_terceros(flask_app):
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
                from flask_profiler import Profiler
                from flask_debugtoolbar import DebugToolbarExtension

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


# ---------------------------------------------------------------------------------------
# Control de acceso a la aplicación.
# Estos metodos son requeridos por la extension flask-login
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
# Opciones de cache.
# ---------------------------------------------------------------------------------------
def no_guardar_en_cache_global():
    """Si el usuario es anomino preferimos usar el sistema de cache."""
    return current_user and current_user.is_authenticated


# ---------------------------------------------------------------------------------------
# Definición de la aplicación principal.
# ---------------------------------------------------------------------------------------
lms_app = Flask(
    "now_lms",
    template_folder=DIRECTORIO_PLANTILLAS,
    static_folder=DIRECTORIO_ARCHIVOS,
)
lms_app.config.from_mapping(CONFIGURACION)
inicializa_extenciones_terceros(lms_app)


@lms_app.errorhandler(404)
@cache.cached()
def error_404(error):  # pragma: no cover
    """Pagina personalizada para recursos no encontrados."""
    assert error is not None  # nosec B101
    return render_template("404.html"), 404


@lms_app.errorhandler(403)
@cache.cached()
def error_403(error):  # pragma: no cover
    """Pagina personalizada para recursos no autorizados."""
    assert error is not None  # nosec B101
    return render_template("403.html"), 403


# Normalmente los servidores WSGI utilizan "app" or "application" por defecto.
app = lms_app
application = lms_app

# ---------------------------------------------------------------------------------------
# Configuración de carga de archivos al sistema.
# Esta configuración es requerida por la extensión flask-reuploaded
# Referencia:
#  - https://flask-reuploaded.readthedocs.io/en/latest/configuration/
# ---------------------------------------------------------------------------------------
images = UploadSet("images", IMAGES)
files = UploadSet("files", DOCUMENTS)
audio = UploadSet("audio", AUDIO)
configure_uploads(lms_app, images)
configure_uploads(lms_app, files)
configure_uploads(lms_app, audio)


# ---------------------------------------------------------------------------------------
# Carga configuración del sitio web.
# - Cargar configuración del sitio web.
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
# Definición de variables globales de Jinja2.
# Estas variables estaran disponibles en todas las plantillas HTML.
# Referencias:
#  - https://jinja.palletsprojects.com/en/3.1.x/api/#the-global-namespace
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


# ---------------------------------------------------------------------------------------
# Funciones auxiliares para el inicio de la aplicación.
# - Configuración inicial.
# - Crear base de datos.
# ---------------------------------------------------------------------------------------
def initial_setup(with_examples=False):
    """Inicializa una nueva bases de datos"""
    lms_app.app_context().push()
    log.info("Creando esquema de base de datos.")
    database.create_all()
    log.debug("Esquema de base de datos creado correctamente.")
    log.info("Cargando datos de muestra.")
    crear_configuracion_predeterminada()
    crear_usuarios_predeterminados(with_examples)
    crear_curso_predeterminado()
    if DESARROLLO or environ.get("CI") or with_examples:
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


def init_app(with_examples=False):  # pragma: no cover
    """Funcion auxiliar para iniciar la aplicacion."""

    lms_app.app_context().push()
    log.debug("Verificando configuración de la aplicación.")
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

    if not DB_INICIALIZADA:
        log.warning("No se detecto una base de datos inicilizada.")
        log.info("Iniciando nueva base de datos de desarrollo.")
        initial_setup(with_examples)

    else:
        log.info("Configuración detectada correctamente.")
        with lms_app.app_context():
            config = Configuracion.query.first()
            if config.email:
                lms_app.config["MAIL_SERVER"] = config.mail_server
                lms_app.config["MAIL_PORT"] = config.mail_port
                lms_app.config["MAIL_USERNAME"] = config.mail_username
                lms_app.config["MAIL_PASSWORD"] = config.mail_password
                lms_app.config["MAIL_USE_TLS"] = config.mail_use_tls
                lms_app.config["MAIL_USE_SSL"] = config.mail_use_ssl
                if DESARROLLO:
                    lms_app.config["MAIL_SUPPRESS_SEND"] = True

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
def setup(with_examples):  # pragma: no cover
    """Inicia al aplicacion."""
    lms_app.app_context().push()
    initial_setup(with_examples)


@lms_app.cli.command()
def upgrade_db():  # pragma: no cover
    """Actualiza esquema de base de datos."""
    alembic.upgrade()


@lms_app.cli.command()
@click.option("--with-examples", is_flag=True, default=False, help="Load example data at setup.")
def resetdb(with_examples):  # pragma: no cover
    """Elimina la base de datos actual e inicia una nueva."""
    lms_app.app_context().push()
    cache.clear()
    database.drop_all()
    initial_setup(with_examples)


@lms_app.cli.command()
def serve():  # pragma: no cover
    """Servidor WSGI predeterminado."""
    from waitress import serve as server

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


# < ------------------------------------------------------------------------------------- >
# < ----------------------- Definición de las vistas del sistema. ----------------------- >
# < ------------------------------------------------------------------------------------- >


# ---------------------------------------------------------------------------------------
# Funciones auxiliares para las vistas del sistema.
# ---------------------------------------------------------------------------------------
def perfil_requerido(perfil_id):
    """Comprueba si un usuario tiene acceso a un recurso determinado en base a su tipo."""

    def decorator_verifica_acceso(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if (current_user.is_authenticated and current_user.tipo == perfil_id) or current_user.tipo == "admin":
                return func(*args, **kwargs)

            else:  # pragma: no cover
                flash("No se encuentra autorizado a acceder al recurso solicitado.", "error")
                return abort(403)

        return wrapper

    return decorator_verifica_acceso


# ---------------------------------------------------------------------------------------
# Administración de acceso a la aplicación.
# - Iniciar sesión
# - Cerrar sesión
# ---------------------------------------------------------------------------------------
@lms_app.route("/login", methods=["GET", "POST"])
def inicio_sesion():
    """Inicio de sesión del usuario."""
    if current_user.is_authenticated:
        flash("Su usuario ya tiene una sesión iniciada.", "info")
        return PANEL_DE_USUARIO
    form = LoginForm()
    if form.validate_on_submit():
        if validar_acceso(form.usuario.data, form.acceso.data):
            identidad = Usuario.query.filter_by(usuario=form.usuario.data).first()
            if identidad.activo:
                login_user(identidad)
                return PANEL_DE_USUARIO
            else:  # pragma: no cover
                flash("Su cuenta esta inactiva.", "info")
                return INICIO_SESION
        else:  # pragma: no cover
            flash("Inicio de Sesion Incorrecto.", "warning")
            return INICIO_SESION
    return render_template("auth/login.html", form=form, titulo="Inicio de Sesion - NOW LMS")


@lms_app.route("/exit")
@lms_app.route("/logout")
@lms_app.route("/salir")
def cerrar_sesion():  # pragma: no cover
    """Finaliza la sesion actual."""
    logout_user()
    return redirect("/home")


# ---------------------------------------------------------------------------------------
# Registro de Nuevos Usuarios.
# - Crear cuenta directamente por el usuario.
# - Crear nuevo usuario por acción del administrador del sistema.
# ---------------------------------------------------------------------------------------
@lms_app.route("/logon", methods=["GET", "POST"])
def crear_cuenta():
    """Crear cuenta de usuario desde el sistio web."""
    if current_user.is_authenticated:
        flash("Usted ya posee una cuenta en el sistema.", "warning")
        return PANEL_DE_USUARIO
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
            creado_por=form.usuario.data,
        )
        try:
            database.session.add(usuario_)
            database.session.commit()
            flash("Cuenta creada exitosamente.", "success")
            return INICIO_SESION
        except OperationalError:  # pragma: no cover
            flash("Error al crear la cuenta.", "warning")
            return redirect("/logon")
    else:
        return render_template("auth/logon.html", form=form, titulo="Crear cuenta - NOW LMS")


@lms_app.route("/new_user", methods=["GET", "POST"])
def crear_usuario():  # pragma: no cover
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
            creado_por=current_user.usuario,
        )
        try:
            database.session.add(usuario_)
            database.session.commit()
            flash("Usuario creado exitosamente.", "success")
            return redirect(url_for("usuario", id_usuario=form.usuario.data))
        except OperationalError:
            flash("Error al crear la cuenta.", "warning")
            return redirect("/new_user")
    else:
        return render_template(
            "learning/nuevo_usuario.html",
            form=form,
        )


# ---------------------------------------------------------------------------------------
# Página de inicio de la aplicación.
# ---------------------------------------------------------------------------------------
@lms_app.route("/")
@lms_app.route("/home")
@lms_app.route("/index")
@cache.cached(timeout=90, unless=no_guardar_en_cache_global)
def home():
    """Página principal de la aplicación."""

    if DESARROLLO:  # pragma: no cover
        MAX = 3
    else:
        MAX = MAXIMO_RESULTADOS_EN_CONSULTA_PAGINADA

    CURSOS = database.paginate(
        database.select(Curso).filter(Curso.publico == True, Curso.estado == "open"),  # noqa: E712
        page=request.args.get("page", default=1, type=int),
        max_per_page=MAX,
        count=True,
    )

    return render_template("inicio/mooc.html", cursos=CURSOS)


@lms_app.route("/dashboard")
@lms_app.route("/panel")
@login_required
def panel():
    """Panel principal de la aplicacion luego de inicar sesión."""
    if not current_user.is_authenticated:
        return redirect("/home")
    elif current_user.tipo == "admin":
        cursos_actuales = Curso.query.count()
        usuarios_registrados = Usuario.query.count()
        recursos_creados = CursoRecurso.query.count()
        cursos_por_fecha = Curso.query.order_by(Curso.creado).limit(5).all()
        return render_template(
            "inicio/panel.html",
            cursos_actuales=cursos_actuales,
            usuarios_registrados=usuarios_registrados,
            recursos_creados=recursos_creados,
            cursos_por_fecha=cursos_por_fecha,
        )
    else:
        return redirect("/home")


# ---------------------------------------------------------------------------------------
# Espacio del estudiante.
# - Perfil de usuario
# ---------------------------------------------------------------------------------------
@lms_app.route("/student")
@login_required
def pagina_estudiante():
    """Perfil de usuario."""
    return render_template("perfiles/estudiante.html")


@lms_app.route("/perfil")
@login_required
@perfil_requerido("student")
@cache.cached(timeout=90)
def perfil():
    """Perfil del usuario."""
    perfil_usuario = Usuario.query.filter_by(usuario=current_user.usuario).first()
    return render_template("inicio/perfil.html", perfil=perfil_usuario, genero=GENEROS)


@lms_app.route("/perfil/edit/<ulid>", methods=["GET", "POST"])
@login_required
def edit_perfil(ulid: str):
    """Actualizar información de usuario."""
    if current_user.id != ulid:
        abort(403)

    usuario_ = database.session.get(Usuario, ulid)
    form = UserForm(obj=usuario_)

    if request.method == "POST":
        #
        usuario_.nombre = form.nombre.data  # type: ignore[union-attr]
        usuario_.apellido = form.apellido.data  # type: ignore[union-attr]
        usuario_.correo_electronico = form.correo_electronico.data  # type: ignore[union-attr]
        usuario_.url = form.url.data  # type: ignore[union-attr]
        usuario_.linkedin = form.linkedin.data  # type: ignore[union-attr]
        usuario_.facebook = form.facebook.data  # type: ignore[union-attr]
        usuario_.twitter = form.twitter.data  # type: ignore[union-attr]
        usuario_.github = form.github.data  # type: ignore[union-attr]
        usuario_.youtube = form.youtube.data  # type: ignore[union-attr]
        usuario_.genero = form.genero.data  # type: ignore[union-attr]
        usuario_.titulo = form.titulo.data  # type: ignore[union-attr]
        usuario_.nacimiento = form.nacimiento.data  # type: ignore[union-attr]
        usuario_.bio = form.bio.data  # type: ignore[union-attr]

        if form.correo_electronico.data != usuario_.correo_electronico:  # type: ignore[union-attr]
            usuario_.correo_electronico_verificado = False  # type: ignore[union-attr]
            flash("Favor verifique su nuevo correo electronico.", "warning")

        try:  # pragma: no cover
            database.session.commit()
            cache.delete("view/" + url_for("perfil"))
            flash("Pefil actualizado.", "success")
            if "logo" in request.files:
                try:
                    picture_file = images.save(request.files["logo"], folder="usuarios", name=current_user.id + ".jpg")
                    if picture_file:
                        usuario_ = database.session.execute(
                            database.select(Usuario).filter(Usuario.id == current_user.id)
                        ).first()[0]
                        usuario_.portada = True  # type: ignore[union-attr]
                        database.session.commit()
                        flash("Imagen de perfil actualizada.", "success")
                except UploadNotAllowed:
                    log.warning("No se pudo actualizar la imagen de perfil.", "error")
        except OperationalError:  # pragma: no cover
            flash("Error al editar el perfil.", "error")

        return redirect("/perfil")

    else:  # pragma: no cover
        return render_template("inicio/perfil_editar.html", form=form, usuario=usuario_)


@lms_app.route("/perfil/<ulid>/delete_logo")
@login_required
def elimina_logo_usuario(ulid: str):
    """Elimina logo de usuario."""
    if current_user.id != ulid:
        abort(403)

    elimina_imagen_usuario(ulid=ulid)
    flash("Imagen de usuario eliminada correctamente.", "success")
    return redirect("/perfil")


# ---------------------------------------------------------------------------------------
# Espacio del moderador.
# ---------------------------------------------------------------------------------------
@lms_app.route("/moderator")
@login_required
def pagina_moderador():
    """Perfil de usuario moderador."""
    return render_template("perfiles/moderador.html")


# ---------------------------------------------------------------------------------------
# Espacio del instructor.
# - Lista de cursos.
# ---------------------------------------------------------------------------------------
@lms_app.route("/instructor")
@login_required
def pagina_instructor():
    """Perfil de usuario instructor."""
    return render_template("perfiles/instructor.html")


@lms_app.route("/courses")
@lms_app.route("/cursos")
@login_required
def cursos():
    """Lista de cursos disponibles en el sistema."""
    if current_user.tipo == "admin":
        consulta_cursos = database.paginate(
            database.select(Curso),
            page=request.args.get("page", default=1, type=int),
            max_per_page=MAXIMO_RESULTADOS_EN_CONSULTA_PAGINADA,
            count=True,
        )
    else:
        try:  # pragma: no cover
            consulta_cursos = database.paginate(
                database.select(Curso).join(DocenteCurso).filter(DocenteCurso.usuario == current_user.usuario),
                page=request.args.get("page", default=1, type=int),
                max_per_page=MAXIMO_RESULTADOS_EN_CONSULTA_PAGINADA,
                count=True,
            )

        except ArgumentError:  # pragma: no cover
            consulta_cursos = None
    return render_template("learning/curso_lista.html", consulta=consulta_cursos)


# ---------------------------------------------------------------------------------------
# Espacio del administrador.
# - Configuracion.
# - Listado de usuarios.
# - Inactivar usuario.
# - Perfil del usuario.
# - Cambiar tipo de usuario.
# - Establecer usuario como activo.
# - Establecer usuario como inactivo.
# - Eliminar usuairo con activo.
# ---------------------------------------------------------------------------------------
@lms_app.route("/admin")
@login_required
@perfil_requerido("admin")
@cache.cached(timeout=90)
def pagina_admin():
    """Perfil de usuario administrador."""
    return render_template("perfiles/admin.html", inactivos=Usuario.query.filter_by(activo=False).count() or 0)


@lms_app.route("/settings", methods=["GET", "POST"])
@login_required
@perfil_requerido("admin")
def configuracion():
    """Configuración del sistema."""

    config = Configuracion.query.first()
    form = ConfigForm(modo=config.modo, moneda=config.moneda)
    if form.validate_on_submit() or request.method == "POST":
        config.titulo = form.titulo.data
        config.descripcion = form.descripcion.data
        config.modo = form.descripcion.data
        config.stripe = form.stripe.data
        config.paypal = form.paypal.data
        config.stripe_secret = form.stripe_secret.data
        config.stripe_public = form.stripe_secret.data
        config.moneda = form.moneda.data
        try:
            database.session.commit()
            cache.delete("site_config")
            flash("Sitio web actualizado exitosamente.", "success")
            return redirect("/admin")
        except OperationalError:  # pragma: no cover
            flash("No se pudo actualizar la configuración del sitio web.", "warning")
            return redirect("/admin")

    else:
        return render_template("admin/config.html", form=form, config=config)


@lms_app.route("/theming", methods=["GET", "POST"])
@login_required
@perfil_requerido("admin")
def personalizacion():
    """Personalizar el sistema."""

    config = Configuracion.query.first()
    form = ThemeForm(style=config.style)

    if form.validate_on_submit() or request.method == "POST":  # pragma: no cover
        config.style = form.style.data

        if "logo" in request.files:
            try:
                picture_file = images.save(request.files["logo"], name="logotipo.jpg")
                if picture_file:
                    config.custom_logo = True
                    cache.delete("cached_logo")
                    cache.delete("cached_style")
            except UploadNotAllowed:
                log.warning("Ocurrio un error al actualizar el logotipo del sitio web.")

        try:
            database.session.commit()
            flash("Tema del sitio web actualizado exitosamente.", "success")
            return redirect(url_for("personalizacion"))
        except OperationalError:
            flash("No se pudo actualizar el tema del sitio web.", "warning")
            return redirect(url_for("personalizacion"))

    else:  # pragma: no cover
        return render_template("admin/theme.html", form=form, config=config)


@lms_app.route("/delete_logo")
@login_required
@perfil_requerido("admin")
def elimina_logo():
    """Elimina logo"""
    elimina_logo_perzonalizado()
    return redirect(url_for("personalizacion"))


@lms_app.route("/<course_code>/delete_logo")
@login_required
@perfil_requerido("instructor")
def elimina_logo_curso(course_code: str):
    """Elimina logo"""
    elimina_logo_perzonalizado_curso(course_code)
    return redirect(url_for("editar_curso", course_code=course_code))


@lms_app.route("/program/<codigo>/delete_logo")
@login_required
@perfil_requerido("instructor")
def elimina_logo_programa(codigo: str):
    """Elimina logo programa."""
    elimina_logo_perzonalizado_programa(codigo)
    return redirect(url_for("edit_program", tag=codigo))


@lms_app.route("/mail", methods=["GET", "POST"])
@login_required
@perfil_requerido("admin")
def mail():
    """Configuración de Correo Electronico."""
    config = Configuracion.query.first()
    form = MailForm()
    if form.validate_on_submit() or request.method == "POST":  # pragma: no cover
        config.email = form.email.data
        config.mail_server = form.mail_server.data
        config.mail_port = form.mail_port.data
        config.mail_use_tls = form.mail_use_tls.data
        config.mail_use_ssl = form.mail_use_ssl.data
        config.mail_username = form.mail_username.data
        config.mail_password = form.mail_password.data
        try:  # pragma: no cover
            database.session.commit()
            flash("Configuración de correo electronico actualizada exitosamente.", "success")
            return redirect(url_for("mail"))
        except OperationalError:
            flash("No se pudo actualizar la configuración de correo electronico.", "warning")
            return redirect(url_for("mail"))
    else:  # pragma: no cover
        return render_template("admin/mail.html", form=form, config=configuracion)


@lms_app.route("/users")
@login_required
@perfil_requerido("admin")
@cache.cached(timeout=60)
def usuarios():
    """Lista de usuarios con acceso a al aplicación."""
    CONSULTA = database.paginate(
        database.select(Usuario),
        page=request.args.get("page", default=1, type=int),
        max_per_page=MAXIMO_RESULTADOS_EN_CONSULTA_PAGINADA,
        count=True,
    )

    return render_template(
        "admin/users.html",
        consulta=CONSULTA,
    )


@lms_app.route("/set_user_as_active/<user_id>")
@login_required
@perfil_requerido("admin")
def activar_usuario(user_id):
    """Estable el usuario como activo y redirecciona a la vista dada."""
    perfil_usuario = Usuario.query.filter_by(usuario=user_id).first()
    perfil_usuario.activo = True
    database.session.add(perfil_usuario)
    database.session.commit()
    cache.delete("view/" + url_for("usuarios"))
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
    cache.delete("view/" + url_for("usuarios"))
    return redirect(url_for("usuario", id_usuario=user_id))


@lms_app.route("/delete_user/<user_id>")
@login_required
@perfil_requerido("admin")
def eliminar_usuario(user_id):
    """Elimina un usuario por su id y redirecciona a la vista dada."""
    Usuario.query.filter(Usuario.usuario == user_id).delete()
    database.session.commit()
    cache.delete("view/" + url_for("usuarios"))
    return redirect(url_for(request.args.get("ruta", default="home", type=str)))


@lms_app.route("/inactive_users")
@login_required
@perfil_requerido("admin")
@cache.cached(timeout=60)
def usuarios_inactivos():
    """Lista de usuarios con acceso a al aplicación."""
    CONSULTA = database.paginate(
        database.select(Usuario).filter_by(activo=False),
        page=request.args.get("page", default=1, type=int),
        max_per_page=MAXIMO_RESULTADOS_EN_CONSULTA_PAGINADA,
        count=True,
    )

    return render_template(
        "admin/inactive_users.html",
        consulta=CONSULTA,
    )


@lms_app.route("/user/<id_usuario>")
@login_required
def usuario(id_usuario):
    """Acceso administrativo al perfil de un usuario."""
    perfil_usuario = Usuario.query.filter_by(usuario=id_usuario).first()
    # La misma plantilla del perfil de usuario con permisos elevados como
    # activar desactivar el perfil o cambiar el perfil del usuario.
    if current_user.usuario == id_usuario or current_user.tipo != "student" or perfil_usuario.visible is True:
        return render_template("inicio/perfil.html", perfil=perfil_usuario, genero=GENEROS)
    else:
        return render_template("inicio/private.html")


@lms_app.route("/change_user_type")
@login_required
@perfil_requerido("admin")
def cambiar_tipo_usario():
    """Actualiza el tipo de usuario."""
    cambia_tipo_de_usuario_por_id(
        id_usuario=request.args.get("user"),
        nuevo_tipo=request.args.get("type"),
        usuario=current_user.usuario,
    )
    return redirect(url_for("usuario", id_usuario=request.args.get("user")))


@lms_app.route("/new_group", methods=["GET", "POST"])
@login_required
@perfil_requerido("admin")
def nuevo_grupo():
    """Formulario para crear un nuevo grupo."""
    form = GrupoForm()
    if form.validate_on_submit() or request.method == "POST":
        grupo_ = UsuarioGrupo(
            nombre=form.nombre.data,
            descripcion=form.descripcion.data,
        )

        try:
            database.session.add(grupo_)
            database.session.commit()
            cache.delete("view/" + url_for("lista_grupos"))
            flash("Grupo creado correctamente", "success")
            return redirect("/groups")
        except OperationalError:
            flash("Error al crear el nuevo grupo.", "warning")
            return redirect("/new_group")
    else:
        return render_template("admin/grupos/nuevo.html", form=form)


@lms_app.route("/groups")
@login_required
@perfil_requerido("instructor")
@cache.cached(timeout=60)
def lista_grupos():
    """Formulario para crear un nuevo grupo."""

    grupos = database.paginate(
        database.select(UsuarioGrupo),
        page=request.args.get("page", default=1, type=int),
        max_per_page=MAXIMO_RESULTADOS_EN_CONSULTA_PAGINADA,
        count=True,
    )

    _usuarios = database.session.execute(database.select(UsuarioGrupo))

    return render_template("admin/grupos/lista.html", grupos=grupos, usuarios=_usuarios)


@lms_app.route("/group")
@login_required
@perfil_requerido("instructor")
def grupo():
    """Grupo de usuarios"""
    id_ = request.args.get("id", type=str)
    grupo_ = UsuarioGrupo.query.get(id_)
    CONSULTA = database.paginate(
        database.select(Usuario).join(UsuarioGrupoMiembro).filter(UsuarioGrupoMiembro.grupo == id_),
        page=request.args.get("page", default=1, type=int),
        max_per_page=MAXIMO_RESULTADOS_EN_CONSULTA_PAGINADA,
        count=True,
    )
    estudiantes = Usuario.query.filter(Usuario.tipo == "student").all()
    tutores = Usuario.query.filter(Usuario.tipo == "instructor").all()
    return render_template(
        "admin/grupos/grupo.html", consulta=CONSULTA, grupo=grupo_, tutores=tutores, estudiantes=estudiantes
    )


@lms_app.route(
    "/group/add",
    methods=[
        "POST",
    ],
)
@login_required
@perfil_requerido("instructor")
def agrega_usuario_a_grupo():
    """Agrega un usuario a un grupo y redirecciona a la pagina del grupo."""

    id_ = request.args.get("id", type=str)
    registro = UsuarioGrupoMiembro(
        grupo=id_, usuario=request.form["usuario"], creado_por=current_user.usuario, creado=datetime.now()
    )
    database.session.add(registro)
    url_grupo = url_for("grupo", id=id_)
    try:
        database.session.commit()
        flash("Usuario Agregado Correctamente.", "success")
        return redirect(url_grupo)
    except OperationalError:
        flash("No se pudo agregar al usuario.", "warning")
        return redirect(url_grupo)


@lms_app.route(
    "/group/set_tutor",
    methods=[
        "POST",
    ],
)
@login_required
@perfil_requerido("admin")
def agrega_tutor_a_grupo():
    """Asigna como tutor de grupo a un usuario."""

    id_ = request.args.get("id", type=str)
    registro = UsuarioGrupoTutor(
        grupo=id_, usuario=request.form["usuario"], creado_por=current_user.usuario, creado=datetime.now()
    )
    database.session.add(registro)
    url_grupo = url_for("grupo", id=id_)
    try:
        database.session.commit()
        flash("Usuario Agregado Correctamente.", "success")
        return redirect(url_grupo)
    except OperationalError:
        flash("No se pudo agregar al usuario.", "warning")
        return redirect(url_grupo)


@lms_app.route(
    "/group/remove/<group>/<user>",
)
@login_required
@perfil_requerido("instructor")
def elimina_usuario__grupo(group: str, user: str):
    """Elimina usuario de grupo."""

    UsuarioGrupoMiembro.query.filter(UsuarioGrupoMiembro.usuario == user, UsuarioGrupoMiembro.grupo == group).delete()
    database.session.commit()
    return redirect(url_for("grupo", id=group))


# ---------------------------------------------------------------------------------------
# Vistas auxiliares para servir el contenido de los cursos por tipo de recurso.
# - Enviar archivo.
# - Presentar un recurso HTML externo como iframe
# - Devolver una presentación de reveal.js como iframe
# - Devolver texto en markdown como HTML para usarlo en un iframe
# ---------------------------------------------------------------------------------------
@lms_app.route("/course/<course_code>/files/<recurso_code>")
def recurso_file(course_code, recurso_code):
    """Devuelve un archivo desde el sistema de archivos."""
    doc = CursoRecurso.query.filter(CursoRecurso.id == recurso_code, CursoRecurso.curso == course_code).first()
    config = current_app.upload_set_config.get(doc.base_doc_url)

    return send_from_directory(config.destination, doc.doc)


@lms_app.route("/course/<course_code>/external_code/<recurso_code>")
def external_code(course_code, recurso_code):
    """Devuelve un archivo desde el sistema de archivos."""
    recurso = CursoRecurso.query.filter(CursoRecurso.id == recurso_code, CursoRecurso.curso == course_code).first()

    return recurso.external_code


@lms_app.route("/slide_show/<recurso_code>")
def slide_show(recurso_code):
    """Devuelve un archivo desde el sistema de archivos."""

    slide = CursoRecursoSlideShow.query.filter(CursoRecursoSlideShow.recurso == recurso_code).first()
    slides = CursoRecursoSlides.query.filter(CursoRecursoSlides.recurso == recurso_code).all()

    return render_template("/learning/resources/slide_show.html", resource=slide, slides=slides)


@lms_app.route("/course/<course_code>/md_to_html/<recurso_code>")
def markdown_a_html(course_code, recurso_code):
    """Devuelve un texto en markdown como HTML."""
    recurso = CursoRecurso.query.filter(CursoRecurso.id == recurso_code, CursoRecurso.curso == course_code).first()
    allowed_tags = HTML_TAGS
    allowed_attrs = {"*": ["class"], "a": ["href", "rel"], "img": ["src", "alt"]}

    html = markdown(recurso.text)
    html_limpio = clean(linkify(html), tags=allowed_tags, attributes=allowed_attrs)

    return html_limpio


@lms_app.route("/course/<course_code>/description")
def curso_descripcion_a_html(course_code):
    """Devuelve la descripción de un curso como HTML."""
    course = Curso.query.filter(Curso.codigo == course_code).first()
    allowed_tags = HTML_TAGS
    allowed_attrs = {"*": ["class"], "a": ["href", "rel"], "img": ["src", "alt"]}

    html = markdown(course.descripcion)
    html_limpio = clean(linkify(html), tags=allowed_tags, attributes=allowed_attrs)

    return html_limpio


@lms_app.route("/course/<course_code>/description/<resource>")
def recurso_descripcion_a_html(course_code, resource):
    """Devuelve la descripción de un curso como HTML."""
    recurso = CursoRecurso.query.filter(CursoRecurso.id == resource, CursoRecurso.curso == course_code).first()
    allowed_tags = HTML_TAGS
    allowed_attrs = {"*": ["class"], "a": ["href", "rel"], "img": ["src", "alt"]}

    html = markdown(recurso.descripcion)
    html_limpio = clean(linkify(html), tags=allowed_tags, attributes=allowed_attrs)

    return html_limpio


# ---------------------------------------------------------------------------------------
# Administración de un curso.
# - Página del curso.
# - Nuevo Curso
# - Editar Curso
# - Nueva sección
# - Reorganizar secciones dentro del curso:
#   - Subir sección
#   - Bajar sección
# - Gestión de recursos:
#   - Reorganizar orden de recursos dentro de una nueva sección.
#   - Eliminar recurso del curso.
# - Eliminar Curso
# - Cambiar estatus curso.
# - Establecer curso publico
# - Establecer sección publica
# ---------------------------------------------------------------------------------------
@lms_app.route("/explore")
@cache.cached(unless=no_guardar_en_cache_global)
def lista_cursos():
    """Lista de cursos."""

    if DESARROLLO:
        MAX_COUNT = 3
    else:
        MAX_COUNT = 30

    etiquetas = Etiqueta.query.all()
    categorias = Categoria.query.all()
    consulta_cursos = database.paginate(
        database.select(Curso).filter(Curso.publico == True, Curso.estado == "open"),  # noqa: E712
        page=request.args.get("page", default=1, type=int),
        max_per_page=MAX_COUNT,
        count=True,
    )
    # /explore?page=2&nivel=2&tag=python&category=programing
    if request.args.get("nivel") or request.args.get("tag") or request.args.get("category"):
        PARAMETROS: Union[OrderedDict, None] = OrderedDict()
        for arg in request.url[request.url.find("?") + 1 :].split("&"):  # noqa: E203
            PARAMETROS[arg[: arg.find("=")]] = arg[arg.find("=") + 1 :]  # noqa: E203

            # El numero de pagina debe ser generado por el macro de paginación.
            try:
                del PARAMETROS["page"]
            except KeyError:
                pass
    else:
        PARAMETROS = None

    return render_template(
        "inicio/cursos.html", cursos=consulta_cursos, etiquetas=etiquetas, categorias=categorias, parametros=PARAMETROS
    )


@lms_app.route("/programs")
@cache.cached(unless=no_guardar_en_cache_global)
def lista_programas():
    """Lista de programas."""

    if DESARROLLO:
        MAX_COUNT = 3
    else:
        MAX_COUNT = 30

    etiquetas = Etiqueta.query.all()
    categorias = Categoria.query.all()
    consulta_cursos = database.paginate(
        database.select(Programa).filter(Programa.publico == True, Programa.estado == "open"),  # noqa: E712
        page=request.args.get("page", default=1, type=int),
        max_per_page=MAX_COUNT,
        count=True,
    )
    # /explore?page=2&nivel=2&tag=python&category=programing
    if request.args.get("nivel") or request.args.get("tag") or request.args.get("category"):
        PARAMETROS: Union[OrderedDict, None] = OrderedDict()
        for arg in request.url[request.url.find("?") + 1 :].split("&"):  # noqa: E203
            PARAMETROS[arg[: arg.find("=")]] = arg[arg.find("=") + 1 :]  # noqa: E203

            # El numero de pagina debe ser generado por el macro de paginación.
            try:
                del PARAMETROS["page"]
            except KeyError:
                pass
    else:
        PARAMETROS = None

    return render_template(
        "inicio/programas.html", cursos=consulta_cursos, etiquetas=etiquetas, categorias=categorias, parametros=PARAMETROS
    )


@lms_app.route("/resources")
@cache.cached(unless=no_guardar_en_cache_global)
def lista_recursos():
    """Lista de programas."""

    if DESARROLLO:
        MAX_COUNT = 3
    else:
        MAX_COUNT = 30

    etiquetas = Etiqueta.query.all()
    categorias = Categoria.query.all()
    consulta_cursos = database.paginate(
        database.select(Recurso).filter(Recurso.publico == True),  # noqa: E712
        page=request.args.get("page", default=1, type=int),
        max_per_page=MAX_COUNT,
        count=True,
    )
    # /explore?page=2&nivel=2&tag=python&category=programing
    if request.args.get("nivel") or request.args.get("tag") or request.args.get("category"):
        PARAMETROS: Union[OrderedDict, None] = OrderedDict()
        for arg in request.url[request.url.find("?") + 1 :].split("&"):  # noqa: E203
            PARAMETROS[arg[: arg.find("=")]] = arg[arg.find("=") + 1 :]  # noqa: E203

            # El numero de pagina debe ser generado por el macro de paginación.
            try:
                del PARAMETROS["page"]
            except KeyError:
                pass
    else:
        PARAMETROS = None

    return render_template(
        "inicio/recursos.html",
        cursos=consulta_cursos,
        etiquetas=etiquetas,
        categorias=categorias,
        parametros=PARAMETROS,
        tipo=TIPOS_RECURSOS,
    )


@lms_app.route("/course/view/<course_code>")
@cache.cached(unless=no_guardar_en_cache_global)
def curso(course_code):
    """Pagina principal del curso."""

    _curso = Curso.query.filter_by(codigo=course_code).first()

    if current_user.is_authenticated and request.args.get("inspect"):
        if current_user.tipo == "admin":
            acceso = True
            editable = True
        else:
            _consulta = database.select(DocenteCurso).filter(
                DocenteCurso.curso == course_code, DocenteCurso.usuario == current_user.id
            )
            acceso = database.session.execute(_consulta).first()
            if acceso:
                editable = True
    elif _curso.publico:
        acceso = _curso.estado == "open" and _curso.publico is True
        editable = False
    else:
        acceso = False

    if acceso:
        return render_template(
            "learning/curso/curso.html",
            curso=_curso,
            secciones=CursoSeccion.query.filter_by(curso=course_code).order_by(CursoSeccion.indice).all(),
            recursos=CursoRecurso.query.filter_by(curso=course_code).order_by(CursoRecurso.indice).all(),
            descargas=database.session.execute(
                database.select(Recurso).join(CursoRecursoDescargable).filter(CursoRecursoDescargable.curso == course_code)
            ).all(),  # El join devuelve una tuple.
            nivel=CURSO_NIVEL,
            tipo=TIPOS_RECURSOS,
            editable=editable,
        )

    else:
        abort(403)


@lms_app.route("/course/enroll/<course_code>")
@login_required
@perfil_requerido("student")
def course_enroll(course_code):
    """Pagina para inscribirse a un curso."""

    _curso = Curso.query.filter_by(codigo=course_code).first()

    return render_template("learning/curso/enroll.html", curso=_curso)


@lms_app.route("/course/take/<course_code>")
@login_required
@perfil_requerido("student")
@cache.cached(unless=no_guardar_en_cache_global)
def tomar_curso(course_code):
    """Pagina principal del curso."""

    return render_template(
        "learning/curso.html",
        curso=Curso.query.filter_by(codigo=course_code).first(),
        secciones=CursoSeccion.query.filter_by(curso=course_code).order_by(CursoSeccion.indice).all(),
        recursos=CursoRecurso.query.filter_by(curso=course_code).order_by(CursoRecurso.indice).all(),
        descargas=database.session.execute(
            database.select(Recurso).join(CursoRecursoDescargable).filter(CursoRecursoDescargable.curso == course_code)
        ).all(),  # El join devuelve una tuple.
        nivel=CURSO_NIVEL,
        tipo=TIPOS_RECURSOS,
    )


@lms_app.route("/course/moderate/<course_code>")
@login_required
@perfil_requerido("moderator")
@cache.cached(unless=no_guardar_en_cache_global)
def moderar_curso(course_code):
    """Pagina principal del curso."""

    return render_template(
        "learning/curso.html",
        curso=Curso.query.filter_by(codigo=course_code).first(),
        secciones=CursoSeccion.query.filter_by(curso=course_code).order_by(CursoSeccion.indice).all(),
        recursos=CursoRecurso.query.filter_by(curso=course_code).order_by(CursoRecurso.indice).all(),
        descargas=database.session.execute(
            database.select(Recurso).join(CursoRecursoDescargable).filter(CursoRecursoDescargable.curso == course_code)
        ).all(),  # El join devuelve una tuple.
        nivel=CURSO_NIVEL,
        tipo=TIPOS_RECURSOS,
    )


@lms_app.route("/course/admin/<course_code>")
@login_required
@perfil_requerido("instructor")
@cache.cached(unless=no_guardar_en_cache_global)
def administrar_curso(course_code):
    """Pagina principal del curso."""

    return render_template(
        "learning/curso/admin.html",
        curso=Curso.query.filter_by(codigo=course_code).first(),
        secciones=CursoSeccion.query.filter_by(curso=course_code).order_by(CursoSeccion.indice).all(),
        recursos=CursoRecurso.query.filter_by(curso=course_code).order_by(CursoRecurso.indice).all(),
        descargas=database.session.execute(
            database.select(Recurso).join(CursoRecursoDescargable).filter(CursoRecursoDescargable.curso == course_code)
        ).all(),  # El join devuelve una tuple.
        nivel=CURSO_NIVEL,
        tipo=TIPOS_RECURSOS,
    )


@lms_app.route("/program/<codigo>")
@cache.cached(timeout=60, unless=no_guardar_en_cache_global)
def pagina_programa(codigo):
    """Pagina principal del curso."""

    program = Programa.query.filter(Programa.codigo == codigo).first()
    cuenta_cursos = ProgramaCurso.query.filter(ProgramaCurso.programa == program.codigo).count()

    return render_template("learning/programa.html", programa=program, cuenta_cursos=cuenta_cursos)


@lms_app.route("/course/<course_code>/edit", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def editar_curso(course_code):
    """Editar pagina del curso."""

    curso_a_editar = Curso.query.filter_by(codigo=course_code).first()
    form = CurseForm(
        nivel=curso_a_editar.nivel, descripcion=curso_a_editar.descripcion, promocionado=curso_a_editar.promocionado
    )
    curso_url = url_for("curso", course_code=course_code, inspect=True)
    if form.validate_on_submit() or request.method == "POST":
        if curso_a_editar.promocionado is False and form.promocionado.data is True:
            curso_a_editar.promocionado = datetime.today()
        curso_a_editar.nombre = form.nombre.data
        curso_a_editar.descripcion = form.descripcion.data
        curso_a_editar.publico = form.publico.data
        curso_a_editar.auditable = form.auditable.data
        curso_a_editar.certificado = form.certificado.data
        curso_a_editar.precio = form.precio.data
        curso_a_editar.capacidad = form.capacidad.data
        curso_a_editar.fecha_inicio = form.fecha_inicio.data
        curso_a_editar.fecha_fin = form.fecha_fin.data
        curso_a_editar.duracion = form.duracion.data
        curso_a_editar.modificado_por = current_user.usuario
        curso_a_editar.nivel = form.nivel.data
        curso_a_editar.promocionado = form.promocionado.data

        try:
            database.session.commit()
            if "logo" in request.files:
                try:
                    picture_file = images.save(request.files["logo"], folder=curso_a_editar.codigo, name="logo.jpg")
                    if picture_file:
                        curso_a_editar.portada = True
                        database.session.commit()
                except UploadNotAllowed:
                    log.warning("No se pudo actualizar la portada del curso.")
            flash("Curso actualizado exitosamente.", "success")
            return redirect(curso_url)

        except OperationalError:  # pragma: no cover
            flash("Hubo en error al actualizar el curso.", "warning")
            return redirect(curso_url)

    return render_template("learning/edit_curso.html", form=form, curso=curso_a_editar)


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
            if "logo" in request.files:
                try:
                    picture_file = images.save(request.files["logo"], folder=nuevo_curso.codigo, name="logo.jpg")
                    if picture_file:
                        nuevo_curso.portada = True
                except UploadNotAllowed:
                    log.warning("No se pudo actualizar la foto de perfil.")
                except AttributeError:
                    log.warning("No se pudo actualizar la foto de perfil.")

            flash("Curso creado exitosamente.", "success")
            cache.delete("view/" + url_for("home"))
            return redirect(url_for("curso", course_code=form.codigo.data))
        except OperationalError:  # pragma: no cover
            flash("Hubo en error al crear su curso.", "warning")
            return redirect("/instructor")
    else:  # pragma: no cover
        return render_template("learning/nuevo_curso.html", form=form)


@lms_app.route("/course/<course_code>/new_seccion", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def nuevo_seccion(course_code):
    """Formulario para crear una nueva sección en el curso."""
    # Las seccion son contenedores de recursos.
    form = CursoSeccionForm()
    if form.validate_on_submit() or request.method == "POST":
        secciones = CursoSeccion.query.filter_by(curso=course_code).count()
        nuevo_indice = int(secciones + 1)
        nueva_seccion = CursoSeccion(
            curso=course_code,
            nombre=form.nombre.data,
            descripcion=form.descripcion.data,
            estado=False,
            indice=nuevo_indice,
            creado_por=current_user.usuario,
        )
        try:
            database.session.add(nueva_seccion)
            database.session.commit()
            flash("Sección agregada correctamente al curso.", "success")
            return redirect(url_for("curso", course_code=course_code, inspect=True))
        except OperationalError:  # pragma: no cover
            flash("Hubo en error al crear la seccion.", "warning")
            return redirect(url_for("curso", course_code=course_code, inspect=True))
    else:  # pragma: no cover
        return render_template("learning/nuevo_seccion.html", form=form)


@lms_app.route("/course/<course_code>/<seccion>/edit", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def editar_seccion(course_code, seccion):
    """Formulario para editar una sección en el curso."""

    seccion_a_editar = CursoSeccion.query.get_or_404(seccion)
    form = CursoSeccionForm(nombre=seccion_a_editar.nombre, descripcion=seccion_a_editar.descripcion)
    if form.validate_on_submit() or request.method == "POST":
        seccion_a_editar.nombre = form.nombre.data
        seccion_a_editar.descripcion = form.descripcion.data
        seccion_a_editar.modificado_por = current_user.usuario
        seccion_a_editar.curso = course_code
        try:
            database.session.commit()
            flash("Sección modificada correctamente.", "success")
            return redirect(url_for("curso", course_code=course_code))
        except OperationalError:  # pragma: no cover
            flash("Hubo en error al actualizar la seccion.", "warning")
            return redirect(url_for("curso", course_code=course_code))
    else:  # pragma: no cover
        return render_template("learning/editar_seccion.html", form=form, seccion=seccion_a_editar)


@lms_app.route("/course/<course_code>/seccion/increment/<indice>")
@login_required
@perfil_requerido("instructor")
def incrementar_indice_seccion(course_code, indice):
    """Actualiza indice de secciones."""
    modificar_indice_curso(
        codigo_curso=course_code,
        indice=int(indice),
        task="decrement",
    )
    return redirect(url_for("curso", course_code=course_code))


@lms_app.route("/course/<course_code>/seccion/decrement/<indice>")
@login_required
@perfil_requerido("instructor")
def reducir_indice_seccion(course_code, indice):
    """Actualiza indice de secciones."""
    modificar_indice_curso(
        codigo_curso=course_code,
        indice=int(indice),
        task="increment",
    )
    return redirect(url_for("curso", course_code=course_code))


@lms_app.route("/course/resource/<cource_code>/<seccion_id>/<task>/<resource_index>")
@login_required
@perfil_requerido("instructor")
def modificar_orden_recurso(cource_code, seccion_id, resource_index, task):
    """Actualiza indice de recursos."""
    modificar_indice_seccion(
        seccion_id=seccion_id,
        indice=int(resource_index),
        task=task,
    )
    return redirect(url_for("curso", course_code=cource_code))


@lms_app.route("/delete_recurso/<curso_id>/<seccion>/<id_>")
@login_required
@perfil_requerido("instructor")
def eliminar_recurso(curso_id, seccion, id_):
    """Elimina una seccion del curso."""
    CursoRecurso.query.filter(CursoRecurso.id == id_).delete()
    database.session.commit()
    reorganiza_indice_seccion(seccion=seccion)
    return redirect(url_for("curso", course_code=curso_id))


@lms_app.route("/delete_seccion/<curso_id>/<id_>")
@login_required
@perfil_requerido("instructor")
def eliminar_seccion(curso_id, id_):
    """Elimina una seccion del curso."""
    CursoSeccion.query.filter(CursoSeccion.id == id_).delete()
    database.session.commit()
    reorganiza_indice_curso(codigo_curso=curso_id)
    return redirect(url_for("curso", course_code=curso_id))


@lms_app.route("/delete_curse/<course_id>")
@login_required
@perfil_requerido("instructor")
def eliminar_curso(course_id):
    """Elimina un curso por su id y redirecciona a la vista dada."""

    try:
        # Eliminanos los recursos relacionados al curso seleccionado.
        CursoSeccion.query.filter(CursoSeccion.curso == course_id).delete()
        CursoRecurso.query.filter(CursoRecurso.curso == course_id).delete()
        # Eliminanos los acceso definidos para el curso detallado.
        DocenteCurso.query.filter(DocenteCurso.curso == course_id).delete()
        ModeradorCurso.query.filter(ModeradorCurso.curso == course_id).delete()
        EstudianteCurso.query.filter(EstudianteCurso.curso == course_id).delete()
        # Elimanos curso seleccionado.
        Curso.query.filter(Curso.codigo == course_id).delete()
        database.session.commit()
        flash("Curso Eliminado Correctamente.", "success")
    except PGProgrammingError:  # pragma: no cover
        flash("No se pudo eliminar el curso solicitado.", "warning")
    except ProgrammingError:  # pragma: no cover
        flash("No se pudo eliminar el curso solicitado.", "warning")
    return redirect(url_for("cursos"))


@lms_app.route("/change_curse_status")
@login_required
@perfil_requerido("instructor")
def cambiar_estatus_curso():
    """Actualiza el estatus de un curso."""
    cambia_estado_curso_por_id(
        id_curso=request.args.get("curse"), nuevo_estado=request.args.get("status"), usuario=current_user.usuario
    )
    return redirect(url_for("curso", course_code=request.args.get("curse")))


@lms_app.route("/change_curse_public")
@login_required
@perfil_requerido("instructor")
def cambiar_curso_publico():
    """Actualiza el estado publico de un curso."""
    cambia_curso_publico(
        id_curso=request.args.get("curse"),
    )
    return redirect(url_for("curso", course_code=request.args.get("curse")))


@lms_app.route("/change_curse_seccion_public")
@login_required
@perfil_requerido("instructor")
def cambiar_seccion_publico():
    """Actualiza el estado publico de un curso."""
    cambia_seccion_publico(
        codigo=request.args.get("codigo"),
    )
    return redirect(url_for("curso", course_code=request.args.get("course_code")))


# ---------------------------------------------------------------------------------------
# Administración de recursos de un curso por tipo.
# - Pagina del recurso
# - Pagina para seleccionar tipo de recurso.
# ---------------------------------------------------------------------------------------

RECURSO_AGREGADO = "Recurso agregado correctamente al curso."
ERROR_AL_AGREGAR_CURSO = "Hubo en error al crear el recurso."


@lms_app.route("/cource/<curso_id>/resource/<resource_type>/<codigo>")
def pagina_recurso(curso_id, resource_type, codigo):
    """Pagina de un recurso."""

    CURSO = database.session.query(Curso).filter(Curso.codigo == curso_id).first()
    RECURSO = database.session.query(CursoRecurso).filter(CursoRecurso.id == codigo).first()
    RECURSOS = database.session.query(CursoRecurso).filter(CursoRecurso.curso == curso_id).order_by(CursoRecurso.indice)
    SECCION = database.session.query(CursoSeccion).filter(CursoSeccion.id == RECURSO.seccion).first()
    SECCIONES = database.session.query(CursoSeccion).filter(CursoSeccion.curso == curso_id).order_by(CursoSeccion.indice)
    TEMPLATE = "learning/resources/" + TEMPLATES_BY_TYPE[resource_type]
    INDICE = crear_indice_recurso(codigo)

    if current_user.is_authenticated or RECURSO.publico is True:
        return render_template(
            TEMPLATE, curso=CURSO, recurso=RECURSO, recursos=RECURSOS, seccion=SECCION, secciones=SECCIONES, indice=INDICE
        )
    else:
        flash("No se encuentra autorizado a acceder al recurso solicitado.", "warning")
        return abort(403)


@lms_app.route("/cource/<curso_id>/resource/<resource_type>/<codigo>/complete")
@login_required
@perfil_requerido("student")
def marcar_recurso_completado(curso_id, resource_type, codigo):
    """Registra avance de un 100% en un recurso."""
    RECURSO = database.session.query(CursoRecurso).filter(CursoRecurso.id == codigo).first()

    avance = CursoRecursoAvance(
        curso=curso_id,
        seccion=RECURSO.seccion,
        recurso=RECURSO.id,
        usuario=current_user.id,
        avance=100,
    )
    database.session.add(avance)
    database.session.commit()

    return redirect(url_for("pagina_recurso", curso_id=curso_id, resource_type=resource_type, codigo=RECURSO.id))


@lms_app.route("/cource/<curso_id>/alternative/<codigo>/<order>")
@login_required
@perfil_requerido("student")
def pagina_recurso_alternativo(curso_id, codigo, order):
    """Pagina para seleccionar un curso alternativo."""

    CURSO = database.session.query(Curso).filter(Curso.codigo == curso_id).first()
    RECURSO = database.session.query(CursoRecurso).filter(CursoRecurso.id == codigo).first()
    SECCION = database.session.query(CursoSeccion).filter(CursoSeccion.id == RECURSO.seccion).first()
    INDICE = crear_indice_recurso(codigo)

    if order == "asc":
        consulta_recursos = (
            CursoRecurso.query.filter(
                CursoRecurso.seccion == RECURSO.seccion,
                CursoRecurso.indice >= RECURSO.indice,  # type     : ignore[union-attr]
            )
            .order_by(CursoRecurso.indice)
            .all()
        )

    else:  # Equivale a order == "desc".
        consulta_recursos = (
            CursoRecurso.query.filter(
                CursoRecurso.seccion == RECURSO.seccion, CursoRecurso.indice >= RECURSO.indice  # type: ignore[union-attr]
            )
            .order_by(CursoRecurso.indice.desc())
            .all()
        )

    return render_template(
        "learning/resources/type_alternativo.html",
        recursos=consulta_recursos,
        curso=CURSO,
        recurso=RECURSO,
        seccion=SECCION,
        indice=INDICE,
    )


@lms_app.route("/course/<course_code>/<seccion>/new_resource")
@login_required
@perfil_requerido("instructor")
def nuevo_recurso(course_code, seccion):
    """Página para seleccionar tipo de recurso."""
    return render_template("learning/nuevo_recurso.html", id_curso=course_code, id_seccion=seccion)


@lms_app.route("/course/<course_code>/<seccion>/youtube/new", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def nuevo_recurso_youtube_video(course_code, seccion):
    """Formulario para crear un nuevo recurso tipo vídeo en Youtube."""
    form = CursoRecursoVideoYoutube()
    consulta_recursos = CursoRecurso.query.filter_by(seccion=seccion).count()
    nuevo_indice = int(consulta_recursos + 1)
    if form.validate_on_submit() or request.method == "POST":
        nuevo_recurso_ = CursoRecurso(
            curso=course_code,
            seccion=seccion,
            tipo="youtube",
            nombre=form.nombre.data,
            descripcion=form.descripcion.data,
            url=form.youtube_url.data,
            indice=nuevo_indice,
            creado_por=current_user.usuario,
        )
        try:
            database.session.add(nuevo_recurso_)
            database.session.commit()
            flash(RECURSO_AGREGADO, "success")
            return redirect(url_for("curso", course_code=course_code))
        except OperationalError:  # pragma: no cover
            flash(ERROR_AL_AGREGAR_CURSO, "warning")
            return redirect(url_for("curso", course_code=course_code))
    else:
        return render_template(
            "learning/resources_new/nuevo_recurso_youtube.html", id_curso=course_code, id_seccion=seccion, form=form
        )


@lms_app.route("/course/<course_code>/<seccion>/text/new", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def nuevo_recurso_text(course_code, seccion):
    """Formulario para crear un nuevo documento de texto."""
    form = CursoRecursoArchivoText()
    consulta_recursos = CursoRecurso.query.filter_by(seccion=seccion).count()
    nuevo_indice = int(consulta_recursos + 1)
    if form.validate_on_submit() or request.method == "POST":
        nuevo_recurso_ = CursoRecurso(
            curso=course_code,
            seccion=seccion,
            tipo="text",
            nombre=form.nombre.data,
            descripcion=form.descripcion.data,
            indice=nuevo_indice,
            text=form.editor.data,
            creado_por=current_user.usuario,
        )
        try:
            database.session.add(nuevo_recurso_)
            database.session.commit()
            flash(RECURSO_AGREGADO, "success")
            return redirect(url_for("curso", course_code=course_code))
        except OperationalError:  # pragma: no cover
            flash(ERROR_AL_AGREGAR_CURSO, "warning")
            return redirect(url_for("curso", course_code=course_code))
    else:
        return render_template(
            "learning/resources_new/nuevo_recurso_text.html", id_curso=course_code, id_seccion=seccion, form=form
        )


@lms_app.route("/course/<course_code>/<seccion>/link/new", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def nuevo_recurso_link(course_code, seccion):
    """Formulario para crear un nuevo documento de texto."""
    form = CursoRecursoExternalLink()
    recursos = CursoRecurso.query.filter_by(seccion=seccion).count()
    nuevo_indice = int(recursos + 1)
    if form.validate_on_submit() or request.method == "POST":
        nuevo_recurso_ = CursoRecurso(
            curso=course_code,
            seccion=seccion,
            tipo="link",
            nombre=form.nombre.data,
            descripcion=form.descripcion.data,
            indice=nuevo_indice,
            url=form.url.data,
            creado_por=current_user.usuario,
        )
        try:
            database.session.add(nuevo_recurso_)
            database.session.commit()
            flash(RECURSO_AGREGADO, "success")
            return redirect(url_for("curso", course_code=course_code))
        except OperationalError:  # pragma: no cover
            flash(ERROR_AL_AGREGAR_CURSO, "warning")
            return redirect(url_for("curso", course_code=course_code))
    else:
        return render_template(
            "learning/resources_new/nuevo_recurso_link.html", id_curso=course_code, id_seccion=seccion, form=form
        )


@lms_app.route("/course/<course_code>/<seccion>/pdf/new", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def nuevo_recurso_pdf(course_code, seccion):
    """Formulario para crear un nuevo recurso tipo archivo en PDF."""
    form = CursoRecursoArchivoPDF()
    recursos = CursoRecurso.query.filter_by(seccion=seccion).count()
    nuevo_indice = int(recursos + 1)
    if (form.validate_on_submit() or request.method == "POST") and "pdf" in request.files:
        file_name = str(ULID()) + ".pdf"
        pdf_file = files.save(request.files["pdf"], folder=course_code, name=file_name)
        nuevo_recurso_ = CursoRecurso(
            curso=course_code,
            seccion=seccion,
            tipo="pdf",
            nombre=form.nombre.data,
            descripcion=form.descripcion.data,
            indice=nuevo_indice,
            base_doc_url=files.name,
            doc=pdf_file,
            creado_por=current_user.usuario,
        )
        try:
            database.session.add(nuevo_recurso_)
            database.session.commit()
            flash("RECURSO_AGREGADO", "success")
            return redirect(url_for("curso", course_code=course_code))
        except OperationalError:  # pragma: no cover
            flash(ERROR_AL_AGREGAR_CURSO, "warning")
            return redirect(url_for("curso", course_code=course_code))
    else:
        return render_template(
            "learning/resources_new/nuevo_recurso_pdf.html", id_curso=course_code, id_seccion=seccion, form=form
        )


@lms_app.route("/course/<course_code>/<seccion>/meet/new", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def nuevo_recurso_meet(course_code, seccion):
    """Formulario para crear un nuevo recurso tipo archivo en PDF."""
    form = CursoRecursoMeet()
    recursos = CursoRecurso.query.filter_by(seccion=seccion).count()
    nuevo_indice = int(recursos + 1)
    if form.validate_on_submit() or request.method == "POST":
        nuevo_recurso_ = CursoRecurso(
            curso=course_code,
            seccion=seccion,
            tipo="meet",
            nombre=form.nombre.data,
            descripcion=form.descripcion.data,
            indice=nuevo_indice,
            creado_por=current_user.usuario,
            url=form.url.data,
            fecha=form.fecha.data,
            hora_inicio=form.hora_inicio.data,
            hora_fin=form.hora_fin.data,
            notes=form.notes.data,
        )
        try:
            database.session.add(nuevo_recurso_)
            database.session.commit()
            flash("RECURSO_AGREGADO", "success")
            return redirect(url_for("curso", course_code=course_code))
        except OperationalError:  # pragma: no cover
            flash(ERROR_AL_AGREGAR_CURSO, "warning")
            return redirect(url_for("curso", course_code=course_code))
    else:
        return render_template(
            "learning/resources_new/nuevo_recurso_meet.html", id_curso=course_code, id_seccion=seccion, form=form
        )


@lms_app.route("/course/<course_code>/<seccion>/img/new", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def nuevo_recurso_img(course_code, seccion):
    """Formulario para crear un nuevo recurso tipo imagen."""
    form = CursoRecursoArchivoImagen()
    recursos = CursoRecurso.query.filter_by(seccion=seccion).count()
    nuevo_indice = int(recursos + 1)
    if (form.validate_on_submit() or request.method == "POST") and "img" in request.files:
        file_name = str(ULID()) + ".jpg"
        picture_file = images.save(request.files["img"], folder=course_code, name=file_name)

        nuevo_recurso_ = CursoRecurso(
            curso=course_code,
            seccion=seccion,
            tipo="img",
            nombre=form.nombre.data,
            descripcion=form.descripcion.data,
            indice=nuevo_indice,
            base_doc_url=images.name,
            doc=picture_file,
            creado_por=current_user.usuario,
        )
        try:
            database.session.add(nuevo_recurso_)
            database.session.commit()
            flash("RECURSO_AGREGADO", "success")
            return redirect(url_for("curso", course_code=course_code))
        except OperationalError:  # pragma: no cover
            flash(ERROR_AL_AGREGAR_CURSO, "warning")
            return redirect(url_for("curso", course_code=course_code))
    else:
        return render_template(
            "learning/resources_new/nuevo_recurso_img.html", id_curso=course_code, id_seccion=seccion, form=form
        )


@lms_app.route("/course/<course_code>/<seccion>/audio/new", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def nuevo_recurso_audio(course_code, seccion):
    """Formulario para crear un nuevo recurso de audio"""
    form = CursoRecursoArchivoAudio()
    recursos = CursoRecurso.query.filter_by(seccion=seccion).count()
    nuevo_indice = int(recursos + 1)
    if (form.validate_on_submit() or request.method == "POST") and "audio" in request.files:
        audio_name = str(ULID()) + ".ogg"
        audio_file = audio.save(request.files["audio"], folder=course_code, name=audio_name)

        nuevo_recurso_ = CursoRecurso(
            curso=course_code,
            seccion=seccion,
            tipo="mp3",
            nombre=form.nombre.data,
            descripcion=form.descripcion.data,
            indice=nuevo_indice,
            base_doc_url=audio.name,
            doc=audio_file,
            creado_por=current_user.usuario,
        )
        try:
            database.session.add(nuevo_recurso_)
            database.session.commit()
            flash("RECURSO_AGREGADO", "success")
            return redirect(url_for("curso", course_code=course_code))
        except OperationalError:  # pragma: no cover
            flash(ERROR_AL_AGREGAR_CURSO, "warning")
            return redirect(url_for("curso", course_code=course_code))
    else:
        return render_template(
            "learning/resources_new/nuevo_recurso_mp3.html", id_curso=course_code, id_seccion=seccion, form=form
        )


@lms_app.route("/course/<course_code>/<seccion>/html/new", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def nuevo_recurso_html(course_code, seccion):
    """Formulario para crear un nuevo recurso tipo HTML externo."""
    form = CursoRecursoExternalCode()
    recursos = CursoRecurso.query.filter_by(seccion=seccion).count()
    nuevo_indice = int(recursos + 1)
    if form.validate_on_submit() or request.method == "POST":
        nuevo_recurso_ = CursoRecurso(
            curso=course_code,
            seccion=seccion,
            tipo="html",
            nombre=form.nombre.data,
            descripcion=form.descripcion.data,
            external_code=form.html_externo.data,
            indice=nuevo_indice,
            creado_por=current_user.usuario,
        )
        try:
            database.session.add(nuevo_recurso_)
            database.session.commit()
            flash("RECURSO_AGREGADO", "success")
            return redirect(url_for("curso", course_code=course_code))
        except OperationalError:  # pragma: no cover
            flash(ERROR_AL_AGREGAR_CURSO, "warning")
            return redirect(url_for("curso", course_code=course_code))
    else:
        return render_template(
            "learning/resources_new/nuevo_recurso_html.html", id_curso=course_code, id_seccion=seccion, form=form
        )


# ---------------------------------------------------------------------------------------
# Administración de Etiquetas.
# ---------------------------------------------------------------------------------------
@lms_app.route("/new_tag", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def new_tag():
    """Formulario para crear una etiqueta."""
    form = EtiquetaForm()
    if form.validate_on_submit() or request.method == "POST":
        etiqueta = Etiqueta(
            nombre=form.nombre.data,
            color=form.color.data,
        )
        database.session.add(etiqueta)
        try:
            database.session.commit()
            flash("Nueva etiqueta creada.", "successs")
        except OperationalError:
            flash("Hubo un error al crear la etiqueta.", "warning")
        return redirect("/tags")

    return render_template("learning/etiquetas/nueva_etiqueta.html", form=form)


@lms_app.route("/tags")
@login_required
@perfil_requerido("instructor")
def tags():
    """Lista de etiquetas."""
    etiquetas = database.paginate(
        database.select(Etiqueta),  # noqa: E712
        page=request.args.get("page", default=1, type=int),
        max_per_page=MAXIMO_RESULTADOS_EN_CONSULTA_PAGINADA,
        count=True,
    )
    return render_template(
        "learning/etiquetas/lista_etiquetas.html", consulta=etiquetas, cursos_por_etiqueta=cursos_por_etiqueta
    )


@lms_app.route("/delete_tag/<tag>")
@login_required
@perfil_requerido("instructor")
def delete_tag(tag: str):
    """Elimina una etiqueta."""
    Etiqueta.query.filter(Etiqueta.id == tag).delete()
    database.session.commit()
    return redirect("/tags")


@lms_app.route("/edit_tag/<tag>", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def edit_tag(tag: str):
    """Edita una etiqueta."""
    etiqueta = Etiqueta.query.filter(Etiqueta.id == tag).first()
    form = EtiquetaForm(color=etiqueta.color, nombre=etiqueta.nombre)
    if form.validate_on_submit() or request.method == "POST":
        etiqueta.nombre = form.nombre.data
        etiqueta.color = form.color.data
        try:
            database.session.add(etiqueta)
            database.session.commit()
            flash("Etiqueta editada correctamente.", "success")
        except OperationalError:
            flash("No se puedo editar la etiqueta.", "warning")
        return redirect("/tags")

    return render_template("learning/etiquetas/editar_etiqueta.html", form=form)


# ---------------------------------------------------------------------------------------
# Administración de Categorias.
# ---------------------------------------------------------------------------------------
@lms_app.route("/new_category", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def new_category():
    """Nueva Categoria."""
    form = CategoriaForm()
    if form.validate_on_submit() or request.method == "POST":
        categoria = Categoria(
            nombre=form.nombre.data,
            descripcion=form.descripcion.data,
        )
        database.session.add(categoria)
        try:
            database.session.commit()
            flash("Nueva categoria creada.", "success")
        except OperationalError:
            flash("Hubo un error al crear la categoria.", "warning")
        return redirect("/categories")

    return render_template("learning/categorias/nueva_categoria.html", form=form)


@lms_app.route("/categories")
@login_required
@perfil_requerido("instructor")
def categories():
    """Lista de categorias."""
    categorias = database.paginate(
        database.select(Categoria),  # noqa: E712
        page=request.args.get("page", default=1, type=int),
        max_per_page=MAXIMO_RESULTADOS_EN_CONSULTA_PAGINADA,
        count=True,
    )
    return render_template(
        "learning/categorias/lista_categorias.html", consulta=categorias, cursos_por_categoria=cursos_por_categoria
    )


@lms_app.route("/delete_category/<tag>")
@login_required
@perfil_requerido("instructor")
def delete_category(tag: str):
    """Elimina categoria."""
    Categoria.query.filter(Categoria.id == tag).delete()
    database.session.commit()
    return redirect("/categories")


@lms_app.route("/edit_category/<tag>", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def edit_category(tag: str):
    """Editar categoria."""
    categoria = Categoria.query.filter(Categoria.id == tag).first()
    form = CategoriaForm(nombre=categoria.nombre, descripcion=categoria.descripcion)
    if form.validate_on_submit() or request.method == "POST":
        categoria.nombre = form.nombre.data
        categoria.descripcion = form.descripcion.data
        try:
            database.session.add(categoria)
            database.session.commit()
            flash("Categoria editada correctamente.", "success")
        except OperationalError:
            flash("No se puedo editar la categoria.", "warning")
        return redirect("/categories")

    return render_template("learning/categorias/editar_categoria.html", form=form)


# ---------------------------------------------------------------------------------------
# Administración de Programas.
# ---------------------------------------------------------------------------------------
@lms_app.route("/new_program", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def new_program():
    """Nueva programa."""
    form = ProgramaForm()
    if form.validate_on_submit() or request.method == "POST":
        programa = Programa(
            nombre=form.nombre.data,
            descripcion=form.descripcion.data,
            codigo=form.codigo.data,
            precio=form.precio.data,
            publico=False,
            estado="draft",
            logo=False,
        )
        database.session.add(programa)
        try:
            database.session.commit()
            cache.delete("view/" + url_for("programs"))
            flash("Nueva Programa creado.", "success")
        except OperationalError:
            flash("Hubo un error al crear el programa.", "warning")
        return redirect(url_for("programs"))

    return render_template("learning/programas/nuevo_programa.html", form=form)


@lms_app.route("/programs_list")
@login_required
@perfil_requerido("instructor")
@cache.cached(timeout=60)
def programs():
    """Lista de programas"""
    consulta = database.paginate(
        database.select(Programa),  # noqa: E712
        page=request.args.get("page", default=1, type=int),
        max_per_page=MAXIMO_RESULTADOS_EN_CONSULTA_PAGINADA,
        count=True,
    )
    return render_template("learning/programas/lista_programas.html", consulta=consulta)


@lms_app.route("/delete_program/<tag>")
@login_required
@perfil_requerido("instructor")
def delete_program(tag: str):
    """Elimina programa."""
    Programa.query.filter(Programa.id == tag).delete()
    database.session.commit()
    cache.delete("view/" + url_for("programs"))
    return redirect("/programs_list")


@lms_app.route("/edit_program/<tag>", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def edit_program(tag: str):
    """Editar programa."""
    programa = Programa.query.filter(Programa.id == tag).first()
    form = ProgramaForm(
        nombre=programa.nombre,
        descripcion=programa.descripcion,
        codigo=programa.codigo,
        precio=programa.precio,
        estado=programa.estado,
        promocionado=programa.promocionado,
    )
    if form.validate_on_submit() or request.method == "POST":
        if programa.promocionado is False and form.promocionado.data is True:
            programa.fecha_promocionado = datetime.today()

        programa.nombre = form.nombre.data
        programa.descripcion = form.descripcion.data
        programa.precio = form.precio.data
        programa.publico = form.publico.data
        programa.estado = form.estado.data
        programa.promocionado = form.promocionado.data

        try:
            database.session.add(programa)
            database.session.commit()
            if "logo" in request.files:
                try:
                    picture_file = images.save(request.files["logo"], folder="program" + programa.codigo, name="logo.jpg")
                    if picture_file:
                        programa.logo = True
                        flash("Portada del curso actualizada correctamente", "success")
                        database.session.commit()
                except UploadNotAllowed:
                    flash("No se pudo actualizar la portada del curso.", "warning")

            flash("Programa editado correctamente.")
        except OperationalError:
            flash("No se puedo editar el programa.")
        return redirect("/programs_list")

    return render_template("learning/programas/editar_programa.html", form=form, programa=programa)


# ---------------------------------------------------------------------------------------
# Administración de Recursos.
# ---------------------------------------------------------------------------------------
@lms_app.route("/new_resource", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def new_resource():
    """Nueva recursos."""
    form = RecursoForm()
    if form.validate_on_submit() or request.method == "POST":
        if "img" in request.files:
            file_name = form.codigo.data + ".jpg"
            picture_file = images.save(request.files["img"], folder="resources_files", name=file_name)
        else:
            picture_file = None

        if "recurso" in request.files:
            recurso = request.files["recurso"]
            file_name = form.codigo.data + "." + recurso.filename.split(".")[1]
            resource_file = files.save(request.files["recurso"], folder="resources_files", name=file_name)
        else:
            resource_file = False

        recurso = Recurso(
            nombre=form.nombre.data,
            descripcion=form.descripcion.data,
            codigo=form.codigo.data,
            precio=form.precio.data,
            publico=False,
            file_name=file_name,
            tipo=form.tipo.data,
        )
        if resource_file and picture_file:
            recurso.logo = True
        database.session.add(recurso)
        try:
            database.session.commit()
            flash("Nueva Recurso creado.", "success")
        except OperationalError:
            flash("Hubo un error al crear el recurso.", "warning")
        return redirect("/resources_list")

    return render_template("learning/recursos/nuevo_recurso.html", form=form)


@lms_app.route("/resources_list")
@login_required
@perfil_requerido("instructor")
def lista_de_recursos():
    """Lista de programas"""
    consulta = database.paginate(
        database.select(Recurso),  # noqa: E712
        page=request.args.get("page", default=1, type=int),
        max_per_page=MAXIMO_RESULTADOS_EN_CONSULTA_PAGINADA,
        count=True,
    )
    return render_template("learning/recursos/lista_recursos.html", consulta=consulta)


@lms_app.route("/resource/<resource_code>/donwload")
@login_required
def descargar_recurso(resource_code):
    """Genera link para descargar recurso."""
    recurso = Recurso.query.filter(Recurso.id == resource_code).first()
    config = current_app.upload_set_config.get("files")
    directorio = path.join(config.destination, "resources_files")

    if current_user.is_authenticated:
        return send_from_directory(directorio, recurso.file_name)
    else:
        return redirect("/login")


@lms_app.route("/delete_resource/<ulid>")
@login_required
@perfil_requerido("instructor")
def delete_resource(ulid: str):
    """Elimina recurso."""
    Recurso.query.filter(Recurso.id == ulid).delete()
    database.session.commit()
    return redirect("/resources_list")


@lms_app.route("/update_resource/<ulid>", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def edit_resource(ulid: str):
    """Actualiza recurso."""

    recurso = Recurso.query.filter(Recurso.id == ulid).first()
    form = RecursoForm(nombre=recurso.nombre, descripcion=recurso.descripcion, tipo=recurso.tipo)

    if form.validate_on_submit() or request.method == "POST":
        if recurso.promocionado is False and form.promocionado.data is True:
            recurso.fecha_promocionado = datetime.today()
        recurso.nombre = form.nombre.data
        recurso.descripcion = form.descripcion.data
        recurso.precio = form.precio.data
        recurso.publico = form.publico.data
        recurso.tipo = form.tipo.data

        try:  # pragma: no cover
            database.session.commit()
            flash("Recurso recurso correctamente.", "success")
        except OperationalError:
            flash("Error al editar el recurso.", "warning")
        return redirect(url_for("vista_recurso", resource_code=recurso.codigo))

    return render_template("learning/recursos/editar_recurso.html", form=form, recurso=recurso)


@lms_app.route("/resource/<resource_code>")
@cache.cached(unless=no_guardar_en_cache_global)
def vista_recurso(resource_code):
    """Pagina de un recurso."""

    return render_template(
        "learning/recursos/recurso.html",
        curso=Recurso.query.filter_by(codigo=resource_code).first(),
        tipo=TIPOS_RECURSOS,
    )
