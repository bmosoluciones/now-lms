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

"""User groups management for NOW LMS."""

from __future__ import annotations

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------
from flask import Blueprint, flash, redirect, render_template, request
from flask_login import login_required
from sqlalchemy.exc import OperationalError
from werkzeug.wrappers import Response

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms.auth import perfil_requerido
from now_lms.config import DIRECTORIO_PLANTILLAS
from now_lms.db import UsuarioGrupo, database
from now_lms.forms import GrupoForm

# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------


group = Blueprint("group", __name__, template_folder=DIRECTORIO_PLANTILLAS)


@group.route("/group/new", methods=["GET", "POST"])
@login_required
@perfil_requerido("admin")
def nuevo_grupo() -> str | Response:
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
        except OperationalError:
            database.session.rollback()
            flash("Error al crear el nuevo grupo.", "warning")
            return redirect("/new_group")
    else:
        return render_template("admin/grupos/nuevo.html", form=form)
