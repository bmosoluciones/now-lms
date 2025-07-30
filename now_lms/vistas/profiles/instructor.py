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
    CursoSeccion,
    DocenteCurso,
    Evaluation,
    Usuario,
    UsuarioGrupo,
    UsuarioGrupoMiembro,
    database,
)
from now_lms.forms import EvaluationForm

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
    grupo_ = database.session.get(UsuarioGrupo, ulid)
    CONSULTA = database.paginate(
        database.select(Usuario).join(UsuarioGrupoMiembro).filter(UsuarioGrupoMiembro.grupo == id_),
        page=request.args.get("page", default=1, type=int),
        max_per_page=MAXIMO_RESULTADOS_EN_CONSULTA_PAGINADA,
        count=True,
    )
    estudiantes = database.session.query(Usuario).filter(Usuario.tipo == "student").all()
    tutores = database.session.query(Usuario).filter(Usuario.tipo == "instructor").all()
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

    database.session.query(UsuarioGrupoMiembro).filter(
        UsuarioGrupoMiembro.usuario == user, UsuarioGrupoMiembro.grupo == group
    ).delete()
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
    except OperationalError:  # pragma: no cover
        flash("No se pudo agregar al usuario.", "warning")
        return redirect(url_grupo)


# ---------------------------------------------------------------------------------------
# Evaluation Management Routes
# ---------------------------------------------------------------------------------------


@instructor_profile.route("/instructor/courses/<course_code>/evaluations")
@login_required
@perfil_requerido("instructor")
def course_evaluations(course_code):
    """List evaluations for a course."""

    # Check if instructor has access to this course
    if current_user.tipo != "admin":
        instructor_assignment = (
            database.session.query(DocenteCurso)
            .filter_by(curso=course_code, usuario=current_user.usuario, vigente=True)
            .first()
        )
        if not instructor_assignment:
            flash("No tiene permisos para acceder a este curso.", "danger")
            return redirect(url_for("instructor_profile.cursos"))

    curso = database.session.query(Curso).filter_by(codigo=course_code).first()
    if not curso:
        flash("Curso no encontrado.", "danger")
        return redirect(url_for("instructor_profile.cursos"))

    # Get course sections and their evaluations
    secciones = database.session.query(CursoSeccion).filter_by(curso=course_code).order_by(CursoSeccion.indice).all()
    evaluaciones = database.session.query(Evaluation).join(CursoSeccion).filter(CursoSeccion.curso == course_code).all()

    return render_template("instructor/course_evaluations.html", curso=curso, secciones=secciones, evaluaciones=evaluaciones)


@instructor_profile.route("/instructor/courses/<course_code>/sections/<section_id>/evaluations/new", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def new_evaluation(course_code, section_id):
    """Create a new evaluation for a course section."""

    # Check permissions
    if current_user.tipo != "admin":
        instructor_assignment = (
            database.session.query(DocenteCurso)
            .filter_by(curso=course_code, usuario=current_user.usuario, vigente=True)
            .first()
        )
        if not instructor_assignment:
            flash("No tiene permisos para acceder a este curso.", "danger")
            return redirect(url_for("instructor_profile.cursos"))

    seccion = database.session.get(CursoSeccion, section_id)
    if not seccion or seccion.curso != course_code:
        flash("Sección no encontrada.", "danger")
        return redirect(url_for("instructor_profile.course_evaluations", course_code=course_code))

    form = EvaluationForm()

    if form.validate_on_submit():
        evaluacion = Evaluation(
            section_id=section_id,
            title=form.title.data,
            description=form.description.data,
            is_exam=form.is_exam.data,
            passing_score=float(form.passing_score.data),
            max_attempts=form.max_attempts.data,
            creado_por=current_user.usuario,
        )

        try:
            database.session.add(evaluacion)
            database.session.commit()
            flash("Evaluación creada correctamente.", "success")
            return redirect(
                url_for("instructor_profile.edit_evaluation", course_code=course_code, evaluation_id=evaluacion.id)
            )
        except OperationalError:
            flash("Error al crear la evaluación.", "danger")
            return redirect(url_for("instructor_profile.course_evaluations", course_code=course_code))

    return render_template("instructor/new_evaluation.html", form=form, seccion=seccion)
