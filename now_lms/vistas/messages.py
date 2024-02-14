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

"""
NOW Learning Management System.

Gestión de certificados.
"""

# ---------------------------------------------------------------------------------------
# Libreria estandar
# ---------------------------------------------------------------------------------------


# ---------------------------------------------------------------------------------------
# Librerias de terceros
# ---------------------------------------------------------------------------------------
from flask import Blueprint, abort, redirect, render_template, url_for
from flask_login import current_user, login_required

# ---------------------------------------------------------------------------------------
# Recursos locales
# ---------------------------------------------------------------------------------------
from now_lms.config import DIRECTORIO_PLANTILLAS
from now_lms.db import Mensaje, Usuario, database
from now_lms.forms import MsgForm
from now_lms.misc import INICIO_SESION

# ---------------------------------------------------------------------------------------
# Interfaz de mensajes
# ---------------------------------------------------------------------------------------

msg = Blueprint("msg", __name__, template_folder=DIRECTORIO_PLANTILLAS)


@msg.route("/message/<ulid>")
@login_required
def mensaje(ulid: str):
    """Mensaje."""

    mensaje = database.session.execute(database.select(Mensaje).filter(Mensaje.id == ulid)).first()[0]
    usuario = database.session.execute(database.select(Usuario).filter(Usuario.id == mensaje.usuario)).first()[0]
    respuestas = database.session.execute(database.select(Mensaje, Usuario).filter(Mensaje.parent == ulid)).all()
    form = MsgForm(es_respuesta=True, parent=mensaje.id)

    if current_user.is_authenticated:
        if mensaje.usuario == current_user.id:
            return render_template(
                "learning/mensajes/ver_msg.html", mensaje=mensaje, usuario=usuario, form=form, respuestas=respuestas
            )
        else:
            return abort(403)
    else:
        return redirect(INICIO_SESION)


@msg.route("/message/new", methods=["GET", "POST"])
@login_required
def nuevo_mensaje():
    """Nuevo Mensaje."""

    form = MsgForm()
    mensaje = Mensaje()
    if form.validate_on_submit():
        mensaje.usuario = current_user.id
        mensaje.titulo = form.titulo.data
        mensaje.texto = form.editor.data
        mensaje.parent = form.parent.data
        database.session.add(mensaje)
        database.session.commit()
        database.session.refresh(mensaje)
        return redirect(url_for("msg.mensaje", ulid=mensaje.id))

    return render_template("learning/mensajes/nuevo_msg.html", form=form)
