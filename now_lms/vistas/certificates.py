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
from io import BytesIO

# ---------------------------------------------------------------------------------------
# Librerias de terceros
# ---------------------------------------------------------------------------------------
from flask import Blueprint, flash, make_response, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy.exc import OperationalError

# ---------------------------------------------------------------------------------------
# Recursos locales
# ---------------------------------------------------------------------------------------
from now_lms.auth import perfil_requerido
from now_lms.config import DIRECTORIO_PLANTILLAS
from now_lms.db import MAXIMO_RESULTADOS_EN_CONSULTA_PAGINADA, Certificacion, Certificado, Curso, Usuario, database
from now_lms.forms import CertificateForm, EmitCertificateForm

# ---------------------------------------------------------------------------------------
# Gestión de certificados
# ---------------------------------------------------------------------------------------


certificate = Blueprint("certificate", __name__, template_folder=DIRECTORIO_PLANTILLAS)
VISTA_CERTIFICADOS = "certificate.certificados"


@certificate.route("/certificate/list")
@login_required
@perfil_requerido("instructor")
def certificados():
    """Lista de certificados."""
    certificados = database.paginate(
        database.select(Certificado),
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
    return redirect(url_for(VISTA_CERTIFICADOS))


@certificate.route("/certificate/<ulid>/add")
@login_required
@perfil_requerido("admin")
def certificate_add(ulid: str):
    """Elimina certificado."""
    consulta = database.session.execute(database.select(Certificado).filter_by(id=ulid)).first()
    consulta = consulta[0]
    consulta.habilitado = True
    database.session.commit()
    return redirect(url_for(VISTA_CERTIFICADOS))


@certificate.route("/certificate/<ulid>/publish")
@login_required
@perfil_requerido("admin")
def certificate_publish(ulid: str):
    """Elimina certificado."""
    consulta = database.session.execute(database.select(Certificado).filter_by(id=ulid)).first()
    consulta = consulta[0]
    consulta.publico = True
    database.session.commit()
    return redirect(url_for(VISTA_CERTIFICADOS))


@certificate.route("/certificate/<ulid>/unpublish")
@login_required
@perfil_requerido("admin")
def certificate_unpublish(ulid: str):
    """Elimina certificado."""
    consulta = database.session.execute(database.select(Certificado).filter_by(id=ulid)).first()
    consulta = consulta[0]
    consulta.publico = False
    database.session.commit()
    return redirect(url_for(VISTA_CERTIFICADOS))


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
        return redirect(url_for(VISTA_CERTIFICADOS))

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
        return redirect(url_for(VISTA_CERTIFICADOS))

    return render_template("learning/certificados/editar_certificado.html", form=form)


def insert_style_in_html(template):

    html = template.html
    css = template.css

    css = "<style>" + css + "</style>"

    if css:
        return css + html
    else:
        return html


@certificate.route("/certificate/inspect/<ulid>/")
def certificate_inspect(ulid: str):

    consulta = database.session.execute(database.select(Certificado).filter_by(id=ulid)).first()
    consulta = consulta[0]

    return insert_style_in_html(consulta)


@certificate.route("/certificate/get_as_qr/<id>/")
def certificacion_qr(id: str):
    import qrcode

    base_url = request.url_root
    url = base_url + "/certificate/view/" + id
    qr = qrcode.make(url, box_size=4)

    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    buffer.seek(0)

    response = make_response(buffer.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=QR.png"
    response.mimetype = "image/png"
    return response


@certificate.route("/certificate/certificate/<ulid>/")
def certificacion(ulid: str):
    from jinja2 import BaseLoader, Environment

    certificacion = database.session.execute(database.select(Certificacion).filter_by(id=ulid)).first()
    certificacion = certificacion[0]

    certificado = database.session.execute(database.select(Certificado).filter_by(id=certificacion.certificado)).first()
    certificado = certificado[0]

    curso = database.session.execute(database.select(Curso).filter_by(codigo=certificacion.curso)).first()
    curso = curso[0]

    usuario = database.session.execute(database.select(Usuario).filter_by(usuario=certificacion.usuario)).first()
    usuario = usuario[0]

    template = Environment(loader=BaseLoader, autoescape=True).from_string(insert_style_in_html(certificado))  # type: ignore[arg-type]

    return template.render(curso=curso, usuario=usuario, certificacion=certificacion, certificado=certificado, url_for=url_for)


@certificate.route("/certificate/download/<ulid>/")
def certificate_serve_pdf(ulid: str):
    """Editar categoria."""
    from flask_weasyprint import HTML, render_pdf
    from jinja2 import BaseLoader, Environment
    from weasyprint import CSS

    certificacion = database.session.execute(database.select(Certificacion).filter_by(id=ulid)).first()
    certificacion = certificacion[0]

    certificado = database.session.execute(database.select(Certificado).filter_by(id=certificacion.certificado)).first()
    certificado = certificado[0]

    curso = database.session.execute(database.select(Curso).filter_by(codigo=certificacion.curso)).first()
    curso = curso[0]

    usuario = database.session.execute(database.select(Usuario).filter_by(usuario=certificacion.usuario)).first()
    usuario = usuario[0]

    rtemplate = Environment(loader=BaseLoader, autoescape=True).from_string(certificado.html)  # type: ignore[arg-type]

    return render_pdf(
        HTML(
            string=rtemplate.render(
                curso=curso,
                usuario=usuario,
                certificacion=certificacion,
                certificado=certificado,
                url_for=url_for,
            )
        ),
        stylesheets=[CSS(string=certificado.css)],
    )


@certificate.route("/certificate/issued/list")
@login_required
@perfil_requerido("instructor")
def certificaciones():
    """Lista de certificaciones emitidas."""
    certificados = database.paginate(
        database.select(Certificacion),  # noqa: E712
        page=request.args.get("page", default=1, type=int),
        max_per_page=MAXIMO_RESULTADOS_EN_CONSULTA_PAGINADA,
        count=True,
    )
    return render_template("learning/certificados/lista_certificaciones.html", consulta=certificados)


@certificate.route("/certificate/view/<ulid>")
def certificado(ulid):
    """Lista de certificaciones emitidas."""

    certificacion = database.session.execute(database.select(Certificacion).filter_by(id=ulid)).first()
    certificacion = certificacion[0]

    certificado = database.session.execute(database.select(Certificado).filter_by(id=certificacion.certificado)).first()
    certificado = certificado[0]

    curso = database.session.execute(database.select(Curso).filter_by(codigo=certificacion.curso)).first()
    curso = curso[0]

    usuario = database.session.execute(database.select(Usuario).filter_by(usuario=certificacion.usuario)).first()
    usuario = usuario[0]

    return render_template(
        "learning/certificados/certificado.html",
        curso=curso,
        usuario=usuario,
        certificacion=certificacion,
        certificado=certificado,
    )


@certificate.route("/certificate/issue/<course>/<user>/<template>/")
@login_required
@perfil_requerido("instructor")
def certificacion_crear(course, user, template):
    """Generar un nuevo certificado."""

    cert = Certificacion(usuario=user, curso=course, certificado=template)

    database.session.add(cert)
    database.session.commit()
    database.session.refresh(cert)

    return redirect(url_for("certificate.certificado", ulid=cert.id))


@certificate.route("/certificate/release/", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def certificacion_generar():
    """Generar un nuevo certificado."""
    from now_lms.db.tools import generate_cource_choices, generate_template_choices, generate_user_choices

    form = EmitCertificateForm()

    form.usuario.choices = generate_user_choices()
    form.curso.choices = generate_cource_choices()
    form.template.choices = generate_template_choices()

    if form.validate_on_submit() or request.method == "POST":
        cert = Certificacion(
            usuario=form.usuario.data, curso=form.curso.data, certificado=form.template.data, nota=form.nota.data
        )
        try:
            database.session.add(cert)
            database.session.commit()
            return redirect(url_for("certificate.certificaciones"))

        except OperationalError:  # pragma: no cover
            flash("Hubo en error al crear la plantilla.", "warning")
            return redirect("/instructor")
    else:  # pragma: no cover
        return render_template("learning/certificados/emitir_certificado.html", form=form)
