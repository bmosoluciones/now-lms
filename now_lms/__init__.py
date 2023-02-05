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


"""NOW Learning Management System."""

# pylint: disable=E1101
# pylint: disable=singleton-comparison

# ---------------------------------------------------------------------------------------
# Libreria standar
# ---------------------------------------------------------------------------------------
import sys
from functools import wraps
from os import environ, cpu_count

# ---------------------------------------------------------------------------------------
# Librerias de terceros
# ---------------------------------------------------------------------------------------
from bleach import clean, linkify
from flask import Flask, abort, flash, redirect, request, render_template, url_for, send_from_directory, current_app
from flask.cli import FlaskGroup
from flask_alembic import Alembic
from flask_caching import Cache
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from flask_mde import Mde
from flask_uploads import AUDIO, DOCUMENTS, IMAGES, UploadSet, configure_uploads
from loguru import logger as log
from markdown import markdown
from pg8000.dbapi import ProgrammingError as PGProgrammingError
from pg8000.exceptions import DatabaseError
from sqlalchemy.exc import ArgumentError, OperationalError, ProgrammingError
from ulid import ULID

# ---------------------------------------------------------------------------------------
# Recursos locales
# ---------------------------------------------------------------------------------------
from now_lms.auth import validar_acceso, proteger_passwd
from now_lms.config import (
    DIRECTORIO_PLANTILLAS,
    DIRECTORIO_ARCHIVOS,
    DESARROLLO,
    CONFIGURACION,
    CACHE_CONFIG,
)
from now_lms.db import (
    database,
    Configuracion,
    Curso,
    CursoRecurso,
    CursoSeccion,
    CursoRecursoSlides,
    CursoRecursoSlideShow,
    DocenteCurso,
    EstudianteCurso,
    ModeradorCurso,
    Usuario,
    MAXIMO_RESULTADOS_EN_CONSULTA_PAGINADA,
)

from now_lms.db.init_courses import crear_curso_predeterminado, crear_curso_demo, crear_usuarios_predeterminados

from now_lms.db.tools import (
    crear_configuracion_predeterminada,
    verifica_docente_asignado_a_curso,
    verifica_estudiante_asignado_a_curso,
    verifica_moderador_asignado_a_curso,
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
)
from now_lms.misc import HTML_TAGS, ICONOS_RECURSOS, TEMPLATES_BY_TYPE
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


# ---------------------------------------------------------------------------------------
# Inicialización de extensiones de terceros
# ---------------------------------------------------------------------------------------
alembic: Alembic = Alembic()
administrador_sesion: LoginManager = LoginManager()
cache: Cache = Cache()
mde: Mde = Mde()


def inicializa_extenciones_terceros(flask_app):
    """Inicia extensiones de terceros."""
    with flask_app.app_context():
        alembic.init_app(flask_app)
        administrador_sesion.init_app(flask_app)
        database.init_app(flask_app)
        cache.init_app(flask_app, CACHE_CONFIG)
        mde.init_app(flask_app)


# ---------------------------------------------------------------------------------------
# Control de acceso a la aplicación.
# Estos metodos son requeridos por la extension flask-login
# ---------------------------------------------------------------------------------------
@administrador_sesion.user_loader
def cargar_sesion(identidad):  # pragma: no cover
    """Devuelve la entrada correspondiente al usuario que inicio sesión desde la base de datos."""
    if identidad is not None:
        return Usuario.query.get(identidad)
    return None


@administrador_sesion.unauthorized_handler
def no_autorizado():  # pragma: no cover
    """Redirecciona al inicio de sesión usuarios no autorizados."""
    flash("Favor iniciar sesión para acceder al sistema.")
    return INICIO_SESION


# ---------------------------------------------------------------------------------------
# Opciones de cache.
# ---------------------------------------------------------------------------------------
def no_guardar_en_cache_global():
    """Si el usuario es anomino preferimos usar el sistema de cache."""
    return current_user and current_user.is_authenticated


# ---------------------------------------------------------------------------------------
# Definición de variables globales de Jinja2.
# Estas variables estaran disponibles en todas plantillas HTML.
# ---------------------------------------------------------------------------------------
def carga_configuracion_del_sitio_web_desde_db(flask_app):
    """Obtiene configuración del sitio web desde la base de datos."""
    with flask_app.app_context():
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
        finally:
            log.warning("No se pudo cargar la configuración del sitio web desde la base de datos.")
    return CONFIG


def cargar_variables_globales_de_plantillas_html(flask_app):
    """Asignamos variables globales para ser utilizadas dentro de las plantillas del sistema."""
    log.debug("Estableciendo valores blogales de Jinja2.")
    lms_app.jinja_env.globals["current_user"] = current_user
    lms_app.jinja_env.globals["config"] = carga_configuracion_del_sitio_web_desde_db(flask_app)
    lms_app.jinja_env.globals["docente_asignado"] = verifica_docente_asignado_a_curso
    lms_app.jinja_env.globals["moderador_asignado"] = verifica_moderador_asignado_a_curso
    lms_app.jinja_env.globals["estudiante_asignado"] = verifica_estudiante_asignado_a_curso
    lms_app.jinja_env.globals["iconos_recursos"] = ICONOS_RECURSOS


# ---------------------------------------------------------------------------------------
# Definición de la aplicación principal.
# ---------------------------------------------------------------------------------------
lms_app = Flask(
    "now_lms",
    template_folder=DIRECTORIO_PLANTILLAS,
    static_folder=DIRECTORIO_ARCHIVOS,
)
app = lms_app
lms_app.config.from_mapping(CONFIGURACION)
inicializa_extenciones_terceros(lms_app)
cargar_variables_globales_de_plantillas_html(lms_app)


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


# ---------------------------------------------------------------------------------------
# Configuración de carga de archivos al sistema.
# Esta configuración es requerida por la extensión flask-reuploaded
# ---------------------------------------------------------------------------------------
images = UploadSet("images", IMAGES)
files = UploadSet("files", DOCUMENTS)
audio = UploadSet("audio", AUDIO)
configure_uploads(lms_app, images)
configure_uploads(lms_app, files)
configure_uploads(lms_app, audio)


# ---------------------------------------------------------------------------------------
# Funciones auxiliares para el inicio de la aplicación.
# - Crear base de datos.
# - Iniciar servidor WSGI.
# ---------------------------------------------------------------------------------------
def initial_setup():
    """Inicializa una nueva bases de datos"""
    lms_app.app_context().push()
    log.info("Creando esquema de base de datos.")
    database.create_all()
    log.debug("Esquema de base de datos creado correctamente.")
    log.info("Cargando datos de muestra.")
    crear_configuracion_predeterminada()
    crear_usuarios_predeterminados()
    crear_curso_predeterminado()
    crear_curso_demo()
    log.debug("Datos de muestra cargados correctamente.")


def init_app():  # pragma: no cover
    """Funcion auxiliar para iniciar la aplicacion."""

    lms_app.app_context().push()
    try:
        VERIFICA_EXISTE_CONFIGURACION_DB = carga_configuracion_del_sitio_web_desde_db(lms_app)
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
        initial_setup()

    else:
        log.info("Iniciando NOW LMS")


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
def setup():  # pragma: no cover
    """Inicia al aplicacion."""
    lms_app.app_context().push()
    initial_setup()


@lms_app.cli.command()
def resetdb():  # pragma: no cover
    """Elimina la base de datos actual e inicia una nueva."""
    lms_app.app_context().push()
    cache.clear()
    database.drop_all()
    initial_setup()


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


# < ----------------------- Definición de las vistas del sistema. ----------------------- >

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
                flash("No se encuentra autorizado a acceder al recurso solicitado.")
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
    form = LoginForm()
    if form.validate_on_submit():
        if validar_acceso(form.usuario.data, form.acceso.data):
            identidad = Usuario.query.filter_by(usuario=form.usuario.data).first()
            if identidad.activo:
                login_user(identidad)
                return redirect(url_for("panel"))
            else:  # pragma: no cover
                flash("Su cuenta esta inactiva.")
                return INICIO_SESION
        else:  # pragma: no cover
            flash("Inicio de Sesion Incorrecto.")
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
        except OperationalError:  # pragma: no cover
            flash("Error al crear la cuenta.")
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


# ---------------------------------------------------------------------------------------
# Página de inicio de la aplicación.
# ---------------------------------------------------------------------------------------
@lms_app.route("/")
@lms_app.route("/home")
@lms_app.route("/index")
@cache.cached(unless=no_guardar_en_cache_global)
def home():
    """Página principal de la aplicación."""

    CURSOS = database.paginate(
        database.select(Curso).filter(Curso.publico == True, Curso.estado == "open"),  # noqa: E712
        page=request.args.get("page", default=1, type=int),
        max_per_page=MAXIMO_RESULTADOS_EN_CONSULTA_PAGINADA,
        count=True,
    )

    return render_template("inicio/mooc.html", cursos=CURSOS)


@lms_app.route("/dashboard")
@lms_app.route("/panel")
@login_required
def panel():
    """Panel principal de la aplicacion luego de inicar sesión."""
    return render_template("inicio/panel.html")


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
def perfil():
    """Perfil del usuario."""
    perfil_usuario = Usuario.query.filter_by(usuario=current_user.usuario).first()
    return render_template("inicio/perfil.html", perfil=perfil_usuario)


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
        lista_cursos = database.paginate(
            database.select(Curso),
            page=request.args.get("page", default=1, type=int),
            max_per_page=MAXIMO_RESULTADOS_EN_CONSULTA_PAGINADA,
            count=True,
        )
    else:
        try:  # pragma: no cover
            lista_cursos = database.paginate(
                database.select(Curso).join(DocenteCurso).filter(DocenteCurso.usuario == current_user.usuario),
                page=request.args.get("page", default=1, type=int),
                max_per_page=MAXIMO_RESULTADOS_EN_CONSULTA_PAGINADA,
                count=True,
            )

        except ArgumentError:  # pragma: no cover
            lista_cursos = None
    return render_template("learning/curso_lista.html", consulta=lista_cursos)


# ---------------------------------------------------------------------------------------
# Espacio del administrador.
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
def pagina_admin():
    """Perfil de usuario administrador."""
    return render_template("perfiles/admin.html", inactivos=Usuario.query.filter_by(activo=False).count() or 0)


@lms_app.route("/users")
@login_required
@perfil_requerido("admin")
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
    Usuario.query.filter(Usuario.usuario == user_id).delete()
    database.session.commit()
    return redirect(url_for(request.args.get("ruta", default="home", type=str)))


@lms_app.route("/inactive_users")
@login_required
@perfil_requerido("admin")
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
@perfil_requerido("admin")
def usuario(id_usuario):
    """Acceso administrativo al perfil de un usuario."""
    perfil_usuario = Usuario.query.filter_by(usuario=id_usuario).first()
    # La misma plantilla del perfil de usuario con permisos elevados como
    # activar desactivar el perfil o cambiar el perfil del usuario.
    return render_template("inicio/perfil.html", perfil=perfil_usuario)


@lms_app.route("/change_user_type")
@login_required
@perfil_requerido("admin")
def cambiar_tipo_usario():
    """Actualiza el tipo de usuario."""
    cambia_tipo_de_usuario_por_id(
        id_usuario=request.args.get("user"),
        nuevo_tipo=request.args.get("type"),
    )
    return redirect(url_for("usuario", id_usuario=request.args.get("user")))


# ---------------------------------------------------------------------------------------
# Administración de programas.
# Un programa consta de varios cursos.
# ---------------------------------------------------------------------------------------
@lms_app.route("/program")
@lms_app.route("/programa")
def programa():
    """
    Página principal del programa.

    Un programa puede constar de uno o mas cursos individuales
    """


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


# ---------------------------------------------------------------------------------------
# Administración de un curso.
# - Página del curso.
# - Nuevo Curso
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
@lms_app.route("/course/<course_code>")
@cache.cached(unless=no_guardar_en_cache_global)
def curso(course_code):
    """Pagina principal del curso."""

    return render_template(
        "learning/curso.html",
        curso=Curso.query.filter_by(codigo=course_code).first(),
        secciones=CursoSeccion.query.filter_by(curso=course_code).order_by(CursoSeccion.indice).all(),
        recursos=CursoRecurso.query.filter_by(curso=course_code).order_by(CursoRecurso.indice).all(),
    )


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
        except OperationalError:  # pragma: no cover
            flash("Hubo en error al crear su curso.")
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
        )
        try:
            database.session.add(nueva_seccion)
            database.session.commit()
            flash("Sección agregada correctamente al curso.")
            return redirect(url_for("curso", course_code=course_code))
        except OperationalError:  # pragma: no cover
            flash("Hubo en error al crear la seccion.")
            return redirect(url_for("curso", course_code=course_code))
    else:  # pragma: no cover
        return render_template("learning/nuevo_seccion.html", form=form)


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
        flash("Curso Eliminado Correctamente.")
    except PGProgrammingError:  # pragma: no cover
        flash("No se pudo elimiar el curso solicitado.")
    except ProgrammingError:  # pragma: no cover
        flash("No se pudo elimiar el curso solicitado.")
    return redirect(url_for("cursos"))


@lms_app.route("/change_curse_status")
@login_required
@perfil_requerido("instructor")
def cambiar_estatus_curso():
    """Actualiza el estatus de un curso."""
    cambia_estado_curso_por_id(
        id_curso=request.args.get("curse"),
        nuevo_estado=request.args.get("status"),
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
@lms_app.route("/cource/<curso_id>/resource/<resource_type>/<codigo>")
def pagina_recurso(curso_id, resource_type, codigo):
    """Pagina de un recurso."""

    CURSO = database.session.query(Curso).filter(Curso.codigo == curso_id).first()
    RECURSO = database.session.query(CursoRecurso).filter(CursoRecurso.id == codigo).first()
    RECURSOS = database.session.query(CursoRecurso).filter(CursoRecurso.curso == curso_id).order_by(CursoRecurso.indice)
    SECCION = database.session.query(CursoSeccion).filter(CursoSeccion.id == RECURSO.seccion).first()
    SECCIONES = database.session.query(CursoSeccion).filter(CursoSeccion.curso == curso_id).order_by(CursoSeccion.indice)
    TEMPLATE = "learning/resources/" + TEMPLATES_BY_TYPE[resource_type]

    if current_user.is_authenticated or RECURSO.publico is True:
        return render_template(TEMPLATE, curso=CURSO, recurso=RECURSO, recursos=RECURSOS, seccion=SECCION, secciones=SECCIONES)
    else:
        flash("No se encuentra autorizado a acceder al recurso solicitado.")
        return abort(403)


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
    recursos = CursoRecurso.query.filter_by(seccion=seccion).count()
    nuevo_indice = int(recursos + 1)
    if form.validate_on_submit() or request.method == "POST":
        nuevo_recurso_ = CursoRecurso(
            curso=course_code,
            seccion=seccion,
            tipo="youtube",
            nombre=form.nombre.data,
            descripcion=form.descripcion.data,
            url=form.youtube_url.data,
            indice=nuevo_indice,
            requerido=False,
        )
        try:
            database.session.add(nuevo_recurso_)
            database.session.commit()
            flash("Recurso agregado correctamente al curso.")
            return redirect(url_for("curso", course_code=course_code))
        except OperationalError:  # pragma: no cover
            flash("Hubo en error al crear el recurso.")
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
    recursos = CursoRecurso.query.filter_by(seccion=seccion).count()
    nuevo_indice = int(recursos + 1)
    if form.validate_on_submit() or request.method == "POST":
        nuevo_recurso_ = CursoRecurso(
            curso=course_code,
            seccion=seccion,
            tipo="text",
            nombre=form.nombre.data,
            descripcion=form.descripcion.data,
            indice=nuevo_indice,
            text=form.editor.data,
            requerido=False,
        )
        try:
            database.session.add(nuevo_recurso_)
            database.session.commit()
            flash("Recurso agregado correctamente al curso.")
            return redirect(url_for("curso", course_code=course_code))
        except OperationalError:  # pragma: no cover
            flash("Hubo en error al crear el recurso.")
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
            requerido=False,
        )
        try:
            database.session.add(nuevo_recurso_)
            database.session.commit()
            flash("Recurso agregado correctamente al curso.")
            return redirect(url_for("curso", course_code=course_code))
        except OperationalError:  # pragma: no cover
            flash("Hubo en error al crear el recurso.")
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
            requerido=False,
        )
        try:
            database.session.add(nuevo_recurso_)
            database.session.commit()
            flash("Recurso agregado correctamente al curso.")
            return redirect(url_for("curso", course_code=course_code))
        except OperationalError:  # pragma: no cover
            flash("Hubo en error al crear el recurso.")
            return redirect(url_for("curso", course_code=course_code))
    else:
        return render_template(
            "learning/resources_new/nuevo_recurso_pdf.html", id_curso=course_code, id_seccion=seccion, form=form
        )


@lms_app.route("/course/<course_code>/<seccion>/slides/new", methods=["GET", "POST"])
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
            tipo="slides",
            nombre=form.nombre.data,
            descripcion=form.descripcion.data,
            indice=nuevo_indice,
            base_doc_url=files.name,
            requerido=False,
        )
        try:
            database.session.add(nuevo_recurso_)
            database.session.commit()
            flash("Recurso agregado correctamente al curso.")
            return redirect(url_for("curso", course_code=course_code))
        except OperationalError:  # pragma: no cover
            flash("Hubo en error al crear el recurso.")
            return redirect(url_for("curso", course_code=course_code))
    else:
        return render_template(
            "learning/resources_new/nuevo_recurso_slides.html", id_curso=course_code, id_seccion=seccion, form=form
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
            requerido=False,
        )
        try:
            database.session.add(nuevo_recurso_)
            database.session.commit()
            flash("Recurso agregado correctamente al curso.")
            return redirect(url_for("curso", course_code=course_code))
        except OperationalError:  # pragma: no cover
            flash("Hubo en error al crear el recurso.")
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
            requerido=False,
        )
        try:
            database.session.add(nuevo_recurso_)
            database.session.commit()
            flash("Recurso agregado correctamente al curso.")
            return redirect(url_for("curso", course_code=course_code))
        except OperationalError:  # pragma: no cover
            flash("Hubo en error al crear el recurso.")
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
            requerido=False,
        )
        try:
            database.session.add(nuevo_recurso_)
            database.session.commit()
            flash("Recurso agregado correctamente al curso.")
            return redirect(url_for("curso", course_code=course_code))
        except OperationalError:  # pragma: no cover
            flash("Hubo en error al crear el recurso.")
            return redirect(url_for("curso", course_code=course_code))
    else:
        return render_template(
            "learning/resources_new/nuevo_recurso_html.html", id_curso=course_code, id_seccion=seccion, form=form
        )
