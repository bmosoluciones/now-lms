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
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy.exc import OperationalError

# ---------------------------------------------------------------------------------------
# Recursos locales
# ---------------------------------------------------------------------------------------
from now_lms.auth import perfil_requerido
from now_lms.config import DIRECTORIO_PLANTILLAS
from now_lms.db import MAXIMO_RESULTADOS_EN_CONSULTA_PAGINADA, Certificado, database
from now_lms.forms import CertificateForm

# ---------------------------------------------------------------------------------------
# Gestión de certificados
# ---------------------------------------------------------------------------------------


certificate = Blueprint("certificate", __name__, template_folder=DIRECTORIO_PLANTILLAS)


@certificate.route("/certificate/list")
@login_required
@perfil_requerido("instructor")
def certificados():
    """Lista de certificados."""
    certificados = database.paginate(
        database.select(Certificado),  # noqa: E712
        page=request.args.get("page", default=1, type=int),
        max_per_page=MAXIMO_RESULTADOS_EN_CONSULTA_PAGINADA,
        count=True,
    )
    return render_template("learning/certificados/lista_certificados.html", consulta=certificados)


@certificate.route("/certificate/<ulid>/remove")
@login_required
@perfil_requerido("admin")
def certificate_remove(ulid: str):
    """Elimina certificado."""
    consulta = database.session.execute(database.select(Certificado).filter_by(id=ulid)).first()
    consulta = consulta[0]
    consulta.habilitado = False
    database.session.commit()
    return redirect(url_for("certificate.certificados"))


@certificate.route("/certificate/<ulid>/add")
@login_required
@perfil_requerido("admin")
def certificate_add(ulid: str):
    """Elimina certificado."""
    consulta = database.session.execute(database.select(Certificado).filter_by(id=ulid)).first()
    consulta = consulta[0]
    consulta.habilitado = True
    database.session.commit()
    return redirect(url_for("certificate.certificados"))


@certificate.route("/certificate/<ulid>/publish")
@login_required
@perfil_requerido("admin")
def certificate_publish(ulid: str):
    """Elimina certificado."""
    consulta = database.session.execute(database.select(Certificado).filter_by(id=ulid)).first()
    consulta = consulta[0]
    consulta.publico = True
    database.session.commit()
    return redirect(url_for("certificate.certificados"))


@certificate.route("/certificate/<ulid>/unpublish")
@login_required
@perfil_requerido("admin")
def certificate_unpublish(ulid: str):
    """Elimina certificado."""
    consulta = database.session.execute(database.select(Certificado).filter_by(id=ulid)).first()
    consulta = consulta[0]
    consulta.publico = False
    database.session.commit()
    return redirect(url_for("certificate.certificados"))


@certificate.route("/certificate/new", methods=["GET", "POST"])
@login_required
@perfil_requerido("admin")
def certificate_new():
    """Nuevo certificado."""
    form = CertificateForm()
    if form.validate_on_submit() or request.method == "POST":
        certificado = Certificado(
            titulo=form.titulo.data,
            descripcion=form.descripcion.data,
            habilitado=False,
            publico=False,
            usuario=current_user.id,
            html=form.html.data,
            css=form.css.data,
        )
        database.session.add(certificado)
        try:
            database.session.commit()
            flash("Nuevo certificado creado correctamente.", "success")
        except OperationalError:  # pragma: no cover
            flash("Hubo un error al crear el certificado.", "warning")
        return redirect(url_for("certificate.certificados"))

    return render_template("learning/certificados/nuevo_certificado.html", form=form)


@certificate.route("/certificate/<ulid>/edit", methods=["GET", "POST"])
@login_required
@perfil_requerido("admin")
def certificate_edit(ulid: str):
    """Editar categoria."""
    certificado = database.session.execute(database.select(Certificado).filter_by(id=ulid)).first()
    certificado = certificado[0]
    form = CertificateForm(
        titulo=certificado.titulo,
        descripcion=certificado.descripcion,
        habilitado=certificado.habilitado,
        publico=certificado.publico,
        html=certificado.html,
        css=certificado.css,
    )
    if form.validate_on_submit() or request.method == "POST":
        certificado.titulo = form.titulo.data
        certificado.descripcion = form.descripcion.data
        certificado.publico = form.publico.data
        certificado.habilitado = form.habilitado.data
        certificado.html = form.html.data
        certificado.css = form.css.data
        try:
            database.session.add(certificado)
            database.session.commit()
            flash("Certificado editado correctamente.", "success")
        except OperationalError:  # pragma: no cover
            flash("No se puedo editar el certificado.", "warning")
        return redirect(url_for("certificate.certificados"))

    return render_template("learning/certificados/editar_certificado.html", form=form)


@certificate.route("/certificate/view/<ulid>/")
@login_required
@perfil_requerido("admin")
def certificate_view(ulid: str):
    """Editar categoria."""
    certificado = Certificado.query.filter(Certificado.id == ulid).first()
    form = CertificateForm(titulo=certificado.titulo, descripcion=certificado.descripcion, habilitado=certificado.habilitado)
    if form.validate_on_submit() or request.method == "POST":
        certificado.titulo = form.titulo.data
        certificado.descripcion = form.descripcion.data
        try:
            database.session.add(certificado)
            database.session.commit()
            flash("Certificado editado correctamente.", "success")
        except OperationalError:  # pragma: no cover
            flash("No se puedo editar el certificado.", "warning")
        return redirect(url_for("certificate.certificados"))

    return render_template("learning/certificados/editar_certificado.html", form=form)
