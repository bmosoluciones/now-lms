# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------
from datetime import datetime

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy.exc import OperationalError

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms.auth import perfil_requerido
from now_lms.config import DIRECTORIO_PLANTILLAS
from now_lms.db import UsuarioGrupo, UsuarioGrupoTutor, database
from now_lms.forms import GrupoForm

group = Blueprint("group", __name__, template_folder=DIRECTORIO_PLANTILLAS)


@group.route("/group/new", methods=["GET", "POST"])
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
            # cache.delete("view/" + url_for("lista_grupos"))
            flash("Grupo creado correctamente", "success")
            return redirect("/admin/panel")
        except OperationalError:  # pragma: no cover
            database.session.rollback()
            flash("Error al crear el nuevo grupo.", "warning")
            return redirect("/new_group")
    else:
        return render_template("admin/grupos/nuevo.html", form=form)


@group.route(
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
    except OperationalError:  # pragma: no cover
        database.session.rollback()
        flash("No se pudo agregar al usuario.", "warning")
        return redirect(url_grupo)
