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


"""NOW Learning Management System."""

# pylint: disable=E1101

# Libreria standar:
import sys
from functools import wraps
from os import environ, cpu_count
from uuid import uuid4

# Librerias de terceros:
from flask import Flask, abort, flash, redirect, request, render_template, url_for, current_app
from flask.cli import FlaskGroup
from flask_alembic import Alembic
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from flask_uploads import configure_uploads
from loguru import logger as log
from pg8000.dbapi import ProgrammingError as PGProgrammingError
from pg8000.exceptions import DatabaseError
from sqlalchemy.exc import ArgumentError, OperationalError, ProgrammingError


# Recursos locales:
from now_lms.auth import validar_acceso, proteger_passwd
from now_lms.config import DIRECTORIO_PLANTILLAS, DIRECTORIO_ARCHIVOS, DESARROLLO, CONFIGURACION, CARGA_IMAGENES
from now_lms.db import (
    database,
    Configuracion,
    Curso,
    CursoRecurso,
    CursoSeccion,
    DocenteCurso,
    EstudianteCurso,
    ModeradorCurso,
    Usuario,
    crear_cursos_predeterminados,
    crear_usuarios_predeterminados,
    verifica_docente_asignado_a_curso,
    verifica_estudiante_asignado_a_curso,
    verifica_moderador_asignado_a_curso,
    MAXIMO_RESULTADOS_EN_CONSULTA_PAGINADA,
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
from now_lms.forms import LoginForm, LogonForm, CurseForm, CursoRecursoVideoYoutube, CursoSeccionForm
from now_lms.version import VERSION

# < --------------------------------------------------------------------------------------------- >
# Metadatos
__version__: str = VERSION
APPNAME: str = "NOW LMS"

if DESARROLLO:
    log.warning("Se detecto que tiene configuradas las opciones de desarrollo.")
    log.warning("Con las opciones de desarrollo habilitadas puede experimentar perdida de datos.")
    log.warning("Revise su configuración si desea que sus cambios sean permanentes.")

# < --------------------------------------------------------------------------------------------- >
# Datos predefinidos
TIPOS_DE_USUARIO: list = ["admin", "user", "instructor", "moderator"]

# < --------------------------------------------------------------------------------------------- >
# Inicialización de extensiones de terceros

alembic: Alembic = Alembic()
administrador_sesion: LoginManager = LoginManager()


# < --------------------------------------------------------------------------------------------- >
# Control de acceso a la aplicación


@administrador_sesion.user_loader
def cargar_sesion(identidad):
    """Devuelve la entrada correspondiente al usuario que inicio sesión."""
    if identidad is not None:
        return Usuario.query.get(identidad)
    return None


@administrador_sesion.unauthorized_handler
def no_autorizado():  # pragma: no cover
    """Redirecciona al inicio de sesión usuarios no autorizados."""
    flash("Favor iniciar sesión para acceder al sistema.")
    return INICIO_SESION


# < --------------------------------------------------------------------------------------------- >
# Definición de la aplicación
lms_app = Flask(
    "now_lms",
    template_folder=DIRECTORIO_PLANTILLAS,
    static_folder=DIRECTORIO_ARCHIVOS,
)
lms_app.config.from_mapping(CONFIGURACION)


# Inicializamos extenciones y cargamos algunas variables para que esten disponibles de forma
# global en las plantillas de Jinja2.
with lms_app.app_context():  # pragma: no cover
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
        log.info("Configuración cargada correctamente.")
    else:
        log.warning("No se detecto configuración de usuario.")
        log.warning("Utilizando configuración predeterminada.")
    # Asignamos variables globales para ser utilizadas dentro de las plantillas del sistema.
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
            config = Configuracion(
                titulo="NOW LMS",
                descripcion="Sistema de aprendizaje en linea.",
            )
            database.session.add(config)
            database.session.commit()
            crear_usuarios_predeterminados()
            crear_cursos_predeterminados()
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
def error_404(error):  # pragma: no cover
    """Pagina personalizada para recursos no encontrados."""
    assert error is not None  # nosec B101
    return render_template("404.html"), 404


@lms_app.errorhandler(403)
def error_403(error):  # pragma: no cover
    """Pagina personalizada para recursos no autorizados."""
    assert error is not None  # nosec B101
    return render_template("403.html"), 403


# < --------------------------------------------------------------------------------------------- >
# Interfaz de linea de comandos
COMMAND_LINE_INTERFACE = FlaskGroup(
    help="""\
Interfaz de linea de comandos para la administración de NOW LMS.
"""
)


def command(as_module=False) -> None:  # pragma: no cover
    """Linea de comandos para administración de la aplicacion."""
    COMMAND_LINE_INTERFACE.main(args=sys.argv[1:], prog_name="python -m flask" if as_module else None)


# < --------------------------------------------------------------------------------------------- >
# Definición de rutas/vistas
# pylint: disable=singleton-comparison


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

    CURSOS = database.paginate(
        database.select(Curso).filter(Curso.publico == True, Curso.estado == "public"),  # noqa: E712
        page=request.args.get("page", default=1, type=int),
        max_per_page=MAXIMO_RESULTADOS_EN_CONSULTA_PAGINADA,
        count=True,
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


@lms_app.route("/course/<course_code>/new_seccion", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def nuevo_seccion(course_code):
    """Formulario para crear un nuevo recurso."""
    form = CursoSeccionForm()
    if form.validate_on_submit() or request.method == "POST":
        ramdon = uuid4()
        id_unico = str(ramdon.hex)
        secciones = CursoSeccion.query.filter_by(curso=course_code).count()
        nuevo_indice = int(secciones + 1)
        nueva_seccion = CursoSeccion(
            codigo=id_unico,
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
            if secciones > 4:
                reorganiza_indice_curso(codigo_curso=course_code)
            return redirect(url_for("curso", course_code=course_code))
        except OperationalError:
            flash("Hubo en error al crear la seccion.")
            return redirect(url_for("curso", course_code=course_code))
    else:
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
        ramdon = uuid4()
        id_unico = str(ramdon.hex)
        nuevo_recurso_ = CursoRecurso(
            codigo=id_unico,
            curso=course_code,
            seccion=seccion,
            tipo="youtube",
            nombre=form.nombre.data,
            descripcion=form.descripcion.data,
            youtube_url=form.youtube_url.data,
            indice=nuevo_indice,
        )
        try:
            database.session.add(nuevo_recurso_)
            database.session.commit()
            flash("Recurso agregado correctamente al curso.")
            return redirect(url_for("curso", course_code=course_code))
        except OperationalError:
            flash("Hubo en error al crear el recurso.")
            return redirect(url_for("curso", course_code=course_code))
    else:
        return render_template("learning/nuevo_recurso_youtube.html", id_curso=course_code, id_seccion=seccion, form=form)


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
    CursoRecurso.query.filter(CursoRecurso.codigo == id_).delete()
    database.session.commit()
    reorganiza_indice_seccion(seccion=seccion)
    return redirect(url_for("curso", course_code=curso_id))


@lms_app.route("/courses")
@lms_app.route("/cursos")
@login_required
def cursos():
    """Pagina principal del curso."""
    if current_user.tipo == "admin":
        lista_cursos = database.paginate(
            database.select(Curso),
            page=request.args.get("page", default=1, type=int),
            max_per_page=MAXIMO_RESULTADOS_EN_CONSULTA_PAGINADA,
            count=True,
        )
    else:
        try:
            lista_cursos = database.paginate(
                database.select(Curso).join(DocenteCurso).filter(DocenteCurso.usuario == current_user.usuario),
                page=request.args.get("page", default=1, type=int),
                max_per_page=MAXIMO_RESULTADOS_EN_CONSULTA_PAGINADA,
                count=True,
            )

        except ArgumentError:
            lista_cursos = None
    return render_template("learning/curso_lista.html", consulta=lista_cursos)


@lms_app.route("/course/<course_code>")
def curso(course_code):
    """Pagina principal del curso."""
    return render_template(
        "learning/curso.html",
        curso=Curso.query.filter_by(codigo=course_code).first(),
        secciones=CursoSeccion.query.filter_by(curso=course_code).order_by(CursoSeccion.indice).all(),
        recursos=CursoRecurso.query.filter_by(curso=course_code).all(),
    )


# <-------- Administración -------->
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
    Usuario.query.filter(Usuario.usuario == user_id).delete()
    database.session.commit()
    return redirect(url_for(request.args.get("ruta", default="home", type=str)))


@lms_app.route("/delete_seccion/<curso_id>/<id_>")
@login_required
@perfil_requerido("instructor")
def eliminar_seccion(curso_id, id_):
    """Elimina una seccion del curso."""
    CursoSeccion.query.filter(CursoSeccion.codigo == id_).delete()
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
    except PGProgrammingError:
        flash("No se pudo elimiar el curso solicitado.")
    except ProgrammingError:
        flash("No se pudo elimiar el curso solicitado.")
    return redirect(url_for("cursos"))


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


# <-------- Servidores WSGI buscan una "app" por defecto  -------->
app = lms_app
