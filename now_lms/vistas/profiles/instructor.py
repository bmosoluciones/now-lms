# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------
from datetime import datetime

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy.exc import ArgumentError, OperationalError
from sqlalchemy import delete

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms.auth import perfil_requerido
from now_lms.cache import cache
from now_lms.calendar_utils import update_evaluation_events
from now_lms.config import DIRECTORIO_PLANTILLAS
from now_lms.db import (
    MAXIMO_RESULTADOS_EN_CONSULTA_PAGINADA,
    Curso,
    CursoSeccion,
    DocenteCurso,
    Evaluation,
    Question,
    Usuario,
    UsuarioGrupo,
    UsuarioGrupoMiembro,
    database,
    select,
)
from now_lms.forms import EvaluationForm

# Route constants
ROUTE_INSTRUCTOR_PROFILE_CURSOS = "instructor_profile.cursos"
ROUTE_INSTRUCTOR_PROFILE_EVALUACIONES_LISTA = "instructor_profile.evaluaciones_lista"

instructor_profile = Blueprint("instructor_profile", __name__, template_folder=DIRECTORIO_PLANTILLAS)


@instructor_profile.route("/instructor")
@login_required
@perfil_requerido("instructor")
def pagina_instructor():
    """Perfil de usuario instructor."""
    return render_template("perfiles/instructor.html")


@instructor_profile.route("/instructor/courses_list")
@login_required
@perfil_requerido("instructor")
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
    estudiantes = database.session.execute(select(Usuario).filter(Usuario.tipo == "student")).scalars().all()
    tutores = database.session.execute(select(Usuario).filter(Usuario.tipo == "instructor")).scalars().all()
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

    database.session.execute(
        delete(UsuarioGrupoMiembro).where((UsuarioGrupoMiembro.usuario == user) & (UsuarioGrupoMiembro.grupo == group))
    )
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
            database.session.execute(
                select(DocenteCurso).filter_by(curso=course_code, usuario=current_user.usuario, vigente=True)
            )
            .scalars()
            .first()
        )
        if not instructor_assignment:
            flash("No tiene permisos para acceder a este curso.", "danger")
            return redirect(url_for(ROUTE_INSTRUCTOR_PROFILE_CURSOS))

    curso = database.session.execute(select(Curso).filter_by(codigo=course_code)).scalars().first()
    if not curso:
        flash("Curso no encontrado.", "danger")
        return redirect(url_for(ROUTE_INSTRUCTOR_PROFILE_CURSOS))

    # Get course sections and their evaluations
    secciones = (
        database.session.execute(select(CursoSeccion).filter_by(curso=course_code).order_by(CursoSeccion.indice))
        .scalars()
        .all()
    )
    evaluaciones = (
        database.session.execute(select(Evaluation).join(CursoSeccion).filter(CursoSeccion.curso == course_code))
        .scalars()
        .all()
    )

    return render_template("instructor/course_evaluations.html", curso=curso, secciones=secciones, evaluaciones=evaluaciones)


@instructor_profile.route("/instructor/courses/<course_code>/sections/<section_id>/evaluations/new", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def new_evaluation(course_code, section_id):
    """Create a new evaluation for a course section."""

    # Check permissions
    if current_user.tipo != "admin":
        instructor_assignment = (
            database.session.execute(
                select(DocenteCurso).filter_by(curso=course_code, usuario=current_user.usuario, vigente=True)
            )
            .scalars()
            .first()
        )
        if not instructor_assignment:
            flash("No tiene permisos para acceder a este curso.", "danger")
            return redirect(url_for(ROUTE_INSTRUCTOR_PROFILE_CURSOS))

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


@instructor_profile.route("/instructor/evaluaciones")
@login_required
@perfil_requerido("instructor")
def evaluaciones_lista():
    """Lista todas las evaluaciones creadas por el instructor."""

    if current_user.tipo == "admin":
        # Admin can see all evaluations
        evaluaciones = database.session.execute(select(Evaluation)).scalars().all()
    else:
        # Filter evaluations created by current instructor
        evaluaciones = database.session.execute(select(Evaluation).filter_by(creado_por=current_user.usuario)).scalars().all()

    # Get course information for each evaluation
    evaluaciones_con_curso = []
    for eval in evaluaciones:
        seccion = database.session.get(CursoSeccion, eval.section_id)
        curso = database.session.execute(select(Curso).filter_by(codigo=seccion.curso)).scalars().first() if seccion else None
        evaluaciones_con_curso.append({"evaluacion": eval, "seccion": seccion, "curso": curso})

    return render_template("instructor/evaluaciones_lista.html", evaluaciones=evaluaciones_con_curso)


@instructor_profile.route("/instructor/nueva-evaluacion")
@login_required
@perfil_requerido("instructor")
def nueva_evaluacion_global():
    """Página para seleccionar curso y sección antes de crear una evaluación."""

    if current_user.tipo == "admin":
        cursos = database.session.execute(select(Curso)).scalars().all()
    else:
        # Get courses assigned to this instructor
        cursos = (
            database.session.execute(
                select(Curso).join(DocenteCurso).filter(DocenteCurso.usuario == current_user.usuario, DocenteCurso.vigente)
            )  # noqa: E712
            .scalars()
            .all()
        )

    return render_template("instructor/nueva_evaluacion_global.html", cursos=cursos)


@instructor_profile.route("/instructor/evaluations/<evaluation_id>/edit", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def edit_evaluation(evaluation_id):
    """Editar una evaluación existente."""

    evaluacion = database.session.get(Evaluation, evaluation_id)
    if not evaluacion:
        flash("Evaluación no encontrada.", "danger")
        return redirect(url_for(ROUTE_INSTRUCTOR_PROFILE_EVALUACIONES_LISTA))

    # Check permissions
    if current_user.tipo != "admin" and evaluacion.creado_por != current_user.usuario:
        flash("No tiene permisos para editar esta evaluación.", "danger")
        return redirect(url_for(ROUTE_INSTRUCTOR_PROFILE_EVALUACIONES_LISTA))

    seccion = database.session.get(CursoSeccion, evaluacion.section_id)
    curso = database.session.execute(select(Curso).filter_by(codigo=seccion.curso)).scalars().first() if seccion else None

    form = EvaluationForm(obj=evaluacion)

    if form.validate_on_submit():
        evaluacion.title = form.title.data
        evaluacion.description = form.description.data
        evaluacion.is_exam = form.is_exam.data
        evaluacion.passing_score = float(form.passing_score.data)
        evaluacion.max_attempts = form.max_attempts.data

        try:
            database.session.commit()
            flash("Evaluación actualizada correctamente.", "success")
        except OperationalError:
            flash("Error al actualizar la evaluación.", "danger")

    # Get questions for this evaluation
    preguntas = (
        database.session.execute(select(Question).filter_by(evaluation_id=evaluation_id).order_by(Question.order))
        .scalars()
        .all()
    )

    course_code = curso.codigo if curso else ""

    return render_template(
        "instructor/edit_evaluation.html",
        form=form,
        evaluacion=evaluacion,
        preguntas=preguntas,
        course_code=course_code,
    )


@instructor_profile.route("/instructor/evaluations/<evaluation_id>/toggle", methods=["POST"])
@login_required
@perfil_requerido("instructor")
def toggle_evaluation_status(evaluation_id):
    """Habilitar o deshabilitar una evaluación."""

    evaluacion = database.session.get(Evaluation, evaluation_id)
    if not evaluacion:
        flash("Evaluación no encontrada.", "danger")
        return redirect(url_for(ROUTE_INSTRUCTOR_PROFILE_EVALUACIONES_LISTA))

    # Check permissions
    if current_user.tipo != "admin" and evaluacion.creado_por != current_user.usuario:
        flash("No tiene permisos para modificar esta evaluación.", "danger")
        return redirect(url_for(ROUTE_INSTRUCTOR_PROFILE_EVALUACIONES_LISTA))

    # Toggle enabled status (assuming we need to add this field to the model)
    # For now, we'll add a basic implementation
    try:
        # We'll use available_until field to enable/disable
        if evaluacion.available_until is None:
            # Disable by setting past date
            from datetime import datetime, timedelta

            evaluacion.available_until = datetime.now() - timedelta(days=1)
            flash("Evaluación deshabilitada.", "info")
        else:
            # Enable by removing the restriction
            evaluacion.available_until = None
            flash("Evaluación habilitada.", "success")

        database.session.commit()
        # Update calendar events for this evaluation
        update_evaluation_events(evaluation_id)
    except OperationalError:
        flash("Error al cambiar el estado de la evaluación.", "danger")

    return redirect(url_for(ROUTE_INSTRUCTOR_PROFILE_EVALUACIONES_LISTA))
