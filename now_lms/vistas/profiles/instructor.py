"""Instructor profile views for NOW LMS."""

# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------
from datetime import datetime

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import delete
from sqlalchemy.exc import ArgumentError, OperationalError

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
    EvaluationAttempt,
    Question,
    QuestionOption,
    Usuario,
    UsuarioGrupo,
    UsuarioGrupoMiembro,
    database,
    select,
)
from now_lms.forms import EvaluationForm, QuestionForm

# Route constants
ROUTE_INSTRUCTOR_PROFILE_CURSOS = "instructor_profile.cursos"
ROUTE_INSTRUCTOR_PROFILE_EVALUACIONES_LISTA = "instructor_profile.evaluaciones_lista"
ROUTE_INSTRUCTOR_EDIT_EVALUATION = "instructor_profile.edit_evaluation"

# Message constants
MESSAGE_EVALUACION_NO_ENCONTRADA = "Evaluación no encontrada."
MESSAGE_PREGUNTA_NO_ENCONTRADA = "Pregunta no encontrada."

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
    """Grupo de usuarios."""
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
    return redirect(url_for("instructor_profile.grupo", ulid=group))


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
    url_grupo = url_for("instructor_profile.grupo", ulid=id_)
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
            return redirect(url_for(ROUTE_INSTRUCTOR_EDIT_EVALUATION, course_code=course_code, evaluation_id=evaluacion.id))
        except OperationalError:
            flash("Error al crear la evaluación.", "danger")
            return redirect(url_for("instructor_profile.course_evaluations", course_code=course_code))

    return render_template("instructor/new_evaluation.html", form=form, seccion=seccion)


@instructor_profile.route("/instructor/evaluations")
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


@instructor_profile.route("/instructor/new-evaluation")
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
        flash(MESSAGE_EVALUACION_NO_ENCONTRADA, "danger")
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
            return redirect(url_for(ROUTE_INSTRUCTOR_EDIT_EVALUATION, evaluation_id=evaluation_id))
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
        flash(MESSAGE_EVALUACION_NO_ENCONTRADA, "danger")
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


@instructor_profile.route("/instructor/evaluations/<evaluation_id>/questions/new", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def new_question(evaluation_id):
    """Crear una nueva pregunta para una evaluación."""
    evaluacion = database.session.get(Evaluation, evaluation_id)
    if not evaluacion:
        flash(MESSAGE_EVALUACION_NO_ENCONTRADA, "danger")
        return redirect(url_for(ROUTE_INSTRUCTOR_PROFILE_EVALUACIONES_LISTA))

    # Check permissions
    if current_user.tipo != "admin" and evaluacion.creado_por != current_user.usuario:
        flash("No tiene permisos para editar esta evaluación.", "danger")
        return redirect(url_for(ROUTE_INSTRUCTOR_PROFILE_EVALUACIONES_LISTA))

    form = QuestionForm()

    if form.validate_on_submit():
        # Get the next order number for this evaluation
        max_order = database.session.execute(
            select(database.func.max(Question.order)).filter_by(evaluation_id=evaluation_id)
        ).scalar()
        next_order = (max_order or 0) + 1

        question = Question(
            evaluation_id=evaluation_id,
            type=form.type.data,
            text=form.text.data,
            explanation=form.explanation.data,
            order=next_order,
            creado_por=current_user.usuario,
        )

        try:
            database.session.add(question)
            database.session.flush()  # Get the question ID

            # Create default options based on question type
            if form.type.data == "boolean":
                # Create True/False options for boolean questions
                true_option = QuestionOption(
                    question_id=question.id,
                    text="Verdadero",
                    is_correct=False,  # Default to false, user needs to set correct answer
                    creado_por=current_user.usuario,
                )
                false_option = QuestionOption(
                    question_id=question.id,
                    text="Falso",
                    is_correct=False,
                    creado_por=current_user.usuario,
                )
                database.session.add(true_option)
                database.session.add(false_option)
            else:
                # Create default options for multiple choice questions
                for i in range(4):  # Create 4 default options
                    option = QuestionOption(
                        question_id=question.id,
                        text=f"Opción {i + 1}",
                        is_correct=False,
                        creado_por=current_user.usuario,
                    )
                    database.session.add(option)

            database.session.commit()
            flash("Pregunta creada correctamente.", "success")
            return redirect(url_for(ROUTE_INSTRUCTOR_EDIT_EVALUATION, evaluation_id=evaluation_id))
        except OperationalError:
            flash("Error al crear la pregunta.", "danger")

    return render_template("instructor/new_question.html", form=form, evaluacion=evaluacion)


@instructor_profile.route("/instructor/questions/<question_id>/edit", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def edit_question(question_id):
    """Edit an existing question."""
    question = database.session.get(Question, question_id)
    if not question:
        flash(MESSAGE_PREGUNTA_NO_ENCONTRADA, "danger")
        return redirect(url_for(ROUTE_INSTRUCTOR_PROFILE_EVALUACIONES_LISTA))

    # Get the evaluation to check permissions
    evaluacion = database.session.get(Evaluation, question.evaluation_id)
    if not evaluacion:
        flash(MESSAGE_EVALUACION_NO_ENCONTRADA, "danger")
        return redirect(url_for(ROUTE_INSTRUCTOR_PROFILE_EVALUACIONES_LISTA))

    # Check permissions
    if current_user.tipo != "admin" and evaluacion.creado_por != current_user.usuario:
        flash("No tiene permisos para editar esta pregunta.", "danger")
        return redirect(url_for(ROUTE_INSTRUCTOR_PROFILE_EVALUACIONES_LISTA))

    form = QuestionForm(obj=question)

    if form.validate_on_submit():
        try:
            question.text = form.text.data
            question.type = form.type.data
            question.explanation = form.explanation.data

            database.session.commit()
            flash("Pregunta actualizada correctamente.", "success")
            return redirect(url_for(ROUTE_INSTRUCTOR_EDIT_EVALUATION, evaluation_id=question.evaluation_id))
        except OperationalError:
            flash("Error al actualizar la pregunta.", "danger")

    return render_template("instructor/edit_question.html", form=form, question=question, evaluacion=evaluacion)


@instructor_profile.route("/instructor/evaluations/<evaluation_id>/results")
@login_required
@perfil_requerido("instructor")
def evaluation_results(evaluation_id):
    """View results and statistics for an evaluation."""
    evaluacion = database.session.get(Evaluation, evaluation_id)
    if not evaluacion:
        flash(MESSAGE_EVALUACION_NO_ENCONTRADA, "danger")
        return redirect(url_for(ROUTE_INSTRUCTOR_PROFILE_EVALUACIONES_LISTA))

    # Check permissions
    if current_user.tipo != "admin" and evaluacion.creado_por != current_user.usuario:
        flash("No tiene permisos para ver los resultados de esta evaluación.", "danger")
        return redirect(url_for(ROUTE_INSTRUCTOR_PROFILE_EVALUACIONES_LISTA))

    # Get evaluation attempts
    attempts = database.session.execute(select(EvaluationAttempt).filter_by(evaluation_id=evaluation_id)).scalars().all()

    # Calculate basic statistics
    total_attempts = len(attempts)
    completed_attempts = [attempt for attempt in attempts if attempt.submitted_at is not None]
    passed_attempts = [attempt for attempt in attempts if attempt.passed is True]

    # Get course information
    seccion = database.session.get(CursoSeccion, evaluacion.section_id)
    curso = database.session.execute(select(Curso).filter_by(codigo=seccion.curso)).scalars().first() if seccion else None

    statistics = {
        "total_attempts": total_attempts,
        "completed_attempts": len(completed_attempts),
        "passed_attempts": len(passed_attempts),
        "pass_rate": (len(passed_attempts) / len(completed_attempts) * 100) if completed_attempts else 0,
        "average_score": (
            sum(attempt.score for attempt in completed_attempts if attempt.score) / len(completed_attempts)
            if completed_attempts
            else 0
        ),
    }

    return render_template(
        "instructor/evaluation_results.html",
        evaluacion=evaluacion,
        curso=curso,
        seccion=seccion,
        attempts=completed_attempts,
        statistics=statistics,
    )


@instructor_profile.route("/instructor/questions/<question_id>/options/new", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def new_question_option(question_id):
    """Add a new option to a question."""
    question = database.session.get(Question, question_id)
    if not question:
        flash(MESSAGE_PREGUNTA_NO_ENCONTRADA, "danger")
        return redirect(url_for(ROUTE_INSTRUCTOR_PROFILE_EVALUACIONES_LISTA))

    # Get the evaluation to check permissions
    evaluacion = database.session.get(Evaluation, question.evaluation_id)
    if not evaluacion:
        flash(MESSAGE_EVALUACION_NO_ENCONTRADA, "danger")
        return redirect(url_for(ROUTE_INSTRUCTOR_PROFILE_EVALUACIONES_LISTA))

    # Check permissions
    if current_user.tipo != "admin" and evaluacion.creado_por != current_user.usuario:
        flash("No tiene permisos para editar esta pregunta.", "danger")
        return redirect(url_for(ROUTE_INSTRUCTOR_PROFILE_EVALUACIONES_LISTA))

    # For boolean questions, limit to 2 options
    if question.type == "boolean":
        existing_options = database.session.execute(select(QuestionOption).filter_by(question_id=question_id)).scalars().all()
        if len(existing_options) >= 2:
            flash("Las preguntas de verdadero/falso solo pueden tener 2 opciones.", "warning")
            return redirect(url_for(ROUTE_INSTRUCTOR_EDIT_EVALUATION, evaluation_id=question.evaluation_id))

    from now_lms.forms import QuestionOptionForm

    form = QuestionOptionForm()

    if form.validate_on_submit():
        option = QuestionOption(
            question_id=question_id,
            text=form.text.data,
            is_correct=form.is_correct.data,
            creado_por=current_user.usuario,
        )

        try:
            database.session.add(option)
            database.session.commit()
            flash("Opción agregada correctamente.", "success")
            return redirect(url_for(ROUTE_INSTRUCTOR_EDIT_EVALUATION, evaluation_id=question.evaluation_id))
        except OperationalError:
            flash("Error al agregar la opción.", "danger")

    return render_template("instructor/new_question_option.html", form=form, question=question, evaluacion=evaluacion)


@instructor_profile.route("/instructor/options/<option_id>/edit", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def edit_question_option(option_id):
    """Edit an existing question option."""
    option = database.session.get(QuestionOption, option_id)
    if not option:
        flash("Opción no encontrada.", "danger")
        return redirect(url_for(ROUTE_INSTRUCTOR_PROFILE_EVALUACIONES_LISTA))

    question = database.session.get(Question, option.question_id)
    if not question:
        flash(MESSAGE_PREGUNTA_NO_ENCONTRADA, "danger")
        return redirect(url_for(ROUTE_INSTRUCTOR_PROFILE_EVALUACIONES_LISTA))

    # Get the evaluation to check permissions
    evaluacion = database.session.get(Evaluation, question.evaluation_id)
    if not evaluacion:
        flash(MESSAGE_EVALUACION_NO_ENCONTRADA, "danger")
        return redirect(url_for(ROUTE_INSTRUCTOR_PROFILE_EVALUACIONES_LISTA))

    # Check permissions
    if current_user.tipo != "admin" and evaluacion.creado_por != current_user.usuario:
        flash("No tiene permisos para editar esta opción.", "danger")
        return redirect(url_for(ROUTE_INSTRUCTOR_PROFILE_EVALUACIONES_LISTA))

    from now_lms.forms import QuestionOptionForm

    form = QuestionOptionForm(obj=option)

    if form.validate_on_submit():
        try:
            option.text = form.text.data
            option.is_correct = form.is_correct.data
            option.modificado_por = current_user.usuario

            database.session.commit()
            flash("Opción actualizada correctamente.", "success")
            return redirect(url_for(ROUTE_INSTRUCTOR_EDIT_EVALUATION, evaluation_id=question.evaluation_id))
        except OperationalError:
            flash("Error al actualizar la opción.", "danger")

    return render_template(
        "instructor/edit_question_option.html", form=form, option=option, question=question, evaluacion=evaluacion
    )


@instructor_profile.route("/instructor/options/<option_id>/delete", methods=["POST"])
@login_required
@perfil_requerido("instructor")
def delete_question_option(option_id):
    """Delete a question option."""
    option = database.session.get(QuestionOption, option_id)
    if not option:
        flash("Opción no encontrada.", "danger")
        return redirect(url_for(ROUTE_INSTRUCTOR_PROFILE_EVALUACIONES_LISTA))

    question = database.session.get(Question, option.question_id)
    if not question:
        flash(MESSAGE_PREGUNTA_NO_ENCONTRADA, "danger")
        return redirect(url_for(ROUTE_INSTRUCTOR_PROFILE_EVALUACIONES_LISTA))

    # Get the evaluation to check permissions
    evaluacion = database.session.get(Evaluation, question.evaluation_id)
    if not evaluacion:
        flash(MESSAGE_EVALUACION_NO_ENCONTRADA, "danger")
        return redirect(url_for(ROUTE_INSTRUCTOR_PROFILE_EVALUACIONES_LISTA))

    # Check permissions
    if current_user.tipo != "admin" and evaluacion.creado_por != current_user.usuario:
        flash("No tiene permisos para eliminar esta opción.", "danger")
        return redirect(url_for(ROUTE_INSTRUCTOR_PROFILE_EVALUACIONES_LISTA))

    # Check if this would leave the question with too few options
    remaining_options = database.session.execute(
        select(database.func.count(QuestionOption.id)).filter_by(question_id=question.id)
    ).scalar()

    if remaining_options <= 2:
        flash("No se puede eliminar esta opción. Las preguntas necesitan al menos 2 opciones.", "warning")
        return redirect(url_for(ROUTE_INSTRUCTOR_EDIT_EVALUATION, evaluation_id=question.evaluation_id))

    try:
        database.session.delete(option)
        database.session.commit()
        flash("Opción eliminada correctamente.", "success")
    except OperationalError:
        flash("Error al eliminar la opción.", "danger")

    return redirect(url_for(ROUTE_INSTRUCTOR_EDIT_EVALUATION, evaluation_id=question.evaluation_id))


@instructor_profile.route("/instructor/questions/<question_id>/delete", methods=["POST"])
@login_required
@perfil_requerido("instructor")
def delete_question(question_id):
    """Delete a question and all its options."""
    question = database.session.get(Question, question_id)
    if not question:
        flash(MESSAGE_PREGUNTA_NO_ENCONTRADA, "danger")
        return redirect(url_for(ROUTE_INSTRUCTOR_PROFILE_EVALUACIONES_LISTA))

    # Get the evaluation to check permissions
    evaluacion = database.session.get(Evaluation, question.evaluation_id)
    if not evaluacion:
        flash(MESSAGE_EVALUACION_NO_ENCONTRADA, "danger")
        return redirect(url_for(ROUTE_INSTRUCTOR_PROFILE_EVALUACIONES_LISTA))

    # Check permissions
    if current_user.tipo != "admin" and evaluacion.creado_por != current_user.usuario:
        flash("No tiene permisos para eliminar esta pregunta.", "danger")
        return redirect(url_for(ROUTE_INSTRUCTOR_PROFILE_EVALUACIONES_LISTA))

    try:
        # Delete the question (options will be deleted automatically due to cascade)
        database.session.delete(question)
        database.session.commit()
        flash("Pregunta eliminada correctamente.", "success")
    except OperationalError:
        flash("Error al eliminar la pregunta.", "danger")

    return redirect(url_for(ROUTE_INSTRUCTOR_EDIT_EVALUATION, evaluation_id=question.evaluation_id))
