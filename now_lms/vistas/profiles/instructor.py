# ---------------------------------------------------------------------------------------
# Libreria estandar
# ---------------------------------------------------------------------------------------
from datetime import datetime

# ---------------------------------------------------------------------------------------
# Librerias de terceros
# ---------------------------------------------------------------------------------------
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy.exc import ArgumentError, OperationalError

# ---------------------------------------------------------------------------------------
# Recursos locales
# ---------------------------------------------------------------------------------------
from now_lms.auth import perfil_requerido
from now_lms.cache import cache
from now_lms.config import DIRECTORIO_PLANTILLAS
from now_lms.db import (
    MAXIMO_RESULTADOS_EN_CONSULTA_PAGINADA,
    Curso,
    DocenteCurso,
    Usuario,
    UsuarioGrupo,
    UsuarioGrupoMiembro,
    database,
)

instructor_profile = Blueprint("instructor_profile", __name__, template_folder=DIRECTORIO_PLANTILLAS)


@instructor_profile.route("/instructor")
@login_required
def pagina_instructor():
    """Perfil de usuario instructor."""
    return render_template("perfiles/instructor.html")


@instructor_profile.route("/instructor/courses_list")
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


@instructor_profile.route("/instructor/group/list")
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


@instructor_profile.route("/group/<ulid>")
@login_required
@perfil_requerido("instructor")
def grupo(ulid: str):
    """Grupo de usuarios"""
    id_ = request.args.get("id", type=str)
    grupo_ = UsuarioGrupo.query.get(ulid)
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


@instructor_profile.route(
    "/group/remove/<group>/<user>",
)
@login_required
@perfil_requerido("instructor")
def elimina_usuario__grupo(group: str, user: str):
    """Elimina usuario de grupo."""

    UsuarioGrupoMiembro.query.filter(UsuarioGrupoMiembro.usuario == user, UsuarioGrupoMiembro.grupo == group).delete()
    database.session.commit()
    return redirect(url_for("grupo", id=group))


@instructor_profile.route(
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
