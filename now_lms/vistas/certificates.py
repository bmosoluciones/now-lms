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

"""
NOW Learning Management System.

Gestión de certificados.
"""


from __future__ import annotations

# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------
from io import BytesIO
from typing import Any

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------
from flask import Blueprint, abort, flash, make_response, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy.exc import OperationalError
from werkzeug.wrappers import Response

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms.auth import perfil_requerido
from now_lms.config import DIRECTORIO_PLANTILLAS
from now_lms.db import (
    MAXIMO_RESULTADOS_EN_CONSULTA_PAGINADA,
    Certificacion,
    CertificacionPrograma,
    Certificado,
    MasterClassEnrollment,
    Programa,
    Usuario,
    database,
)
from now_lms.forms import CertificateForm, EmitCertificateForm

# Template constants
TEMPLATE_EMITIR_CERTIFICADO = "learning/certificados/emitir_certificado.html"

# ---------------------------------------------------------------------------------------
# Gestión de certificados
# ---------------------------------------------------------------------------------------


certificate = Blueprint("certificate", __name__, template_folder=DIRECTORIO_PLANTILLAS)
VISTA_CERTIFICADOS = "certificate.certificados"


@certificate.route("/certificate/list")
@login_required
@perfil_requerido("instructor")
def certificados() -> str:
    """Lista de certificados."""
    certificados_list = database.paginate(
        database.select(Certificado),
        page=request.args.get("page", default=1, type=int),
        max_per_page=MAXIMO_RESULTADOS_EN_CONSULTA_PAGINADA,
        count=True,
    )
    return render_template("learning/certificados/lista_certificados.html", consulta=certificados_list)


@certificate.route("/certificate/<ulid>/remove")
@login_required
@perfil_requerido("admin")
def certificate_remove(ulid: str) -> Response:
    """Elimina certificado."""
    row = database.session.execute(database.select(Certificado).filter_by(id=ulid)).first()
    if row is None:
        return redirect(url_for(VISTA_CERTIFICADOS))
    consulta = row[0]
    consulta.habilitado = False
    database.session.commit()
    return redirect(url_for(VISTA_CERTIFICADOS))


@certificate.route("/certificate/<ulid>/add")
@login_required
@perfil_requerido("admin")
def certificate_add(ulid: str) -> Response:
    """Elimina certificado."""
    row = database.session.execute(database.select(Certificado).filter_by(id=ulid)).first()
    if row is None:
        return redirect(url_for(VISTA_CERTIFICADOS))
    consulta = row[0]
    consulta.habilitado = True
    database.session.commit()
    return redirect(url_for(VISTA_CERTIFICADOS))


@certificate.route("/certificate/<ulid>/publish")
@login_required
@perfil_requerido("admin")
def certificate_publish(ulid: str) -> Response:
    """Elimina certificado."""
    row = database.session.execute(database.select(Certificado).filter_by(id=ulid)).first()
    if row is None:
        return redirect(url_for(VISTA_CERTIFICADOS))
    consulta = row[0]
    consulta.publico = True
    database.session.commit()
    return redirect(url_for(VISTA_CERTIFICADOS))


@certificate.route("/certificate/<ulid>/unpublish")
@login_required
@perfil_requerido("admin")
def certificate_unpublish(ulid: str) -> Response:
    """Elimina certificado."""
    row = database.session.execute(database.select(Certificado).filter_by(id=ulid)).first()
    if row is None:
        return redirect(url_for(VISTA_CERTIFICADOS))
    consulta = row[0]
    consulta.publico = False
    database.session.commit()
    return redirect(url_for(VISTA_CERTIFICADOS))


@certificate.route("/certificate/new", methods=["GET", "POST"])
@login_required
@perfil_requerido("admin")
def certificate_new() -> str | Response:
    """Nuevo certificado."""
    form = CertificateForm()
    if form.validate_on_submit() or request.method == "POST":
        certificado_obj = Certificado(
            titulo=form.titulo.data,
            descripcion=form.descripcion.data,
            habilitado=False,
            publico=False,
            usuario=current_user.id,
            html=form.html.data,
            css=form.css.data,
            tipo=form.tipo.data,
        )
        database.session.add(certificado_obj)
        try:
            database.session.commit()
            flash("Nuevo certificado creado correctamente.", "success")
        except OperationalError:
            database.session.rollback()
            flash("Hubo un error al crear el certificado.", "warning")
        return redirect(url_for(VISTA_CERTIFICADOS))

    return render_template("learning/certificados/nuevo_certificado.html", form=form)


@certificate.route("/certificate/<ulid>/edit", methods=["GET", "POST"])
@login_required
@perfil_requerido("admin")
def certificate_edit(ulid: str) -> str | Response:
    """Editar categoria."""
    certificado_result = database.session.execute(database.select(Certificado).filter_by(id=ulid)).first()
    if certificado_result is None:
        return redirect(url_for(VISTA_CERTIFICADOS))
    certificado_obj = certificado_result[0]
    form = CertificateForm(
        titulo=certificado_obj.titulo,
        descripcion=certificado_obj.descripcion,
        habilitado=certificado_obj.habilitado,
        publico=certificado_obj.publico,
        html=certificado_obj.html,
        css=certificado_obj.css,
        tipo=certificado_obj.tipo,
    )
    if form.validate_on_submit() or request.method == "POST":
        certificado_obj.titulo = form.titulo.data
        certificado_obj.descripcion = form.descripcion.data
        certificado_obj.publico = form.publico.data
        certificado_obj.habilitado = form.habilitado.data
        certificado_obj.html = form.html.data
        certificado_obj.css = form.css.data
        certificado_obj.tipo = form.tipo.data
        try:
            database.session.add(certificado_obj)
            database.session.commit()
            flash("Certificado editado correctamente.", "success")
        except OperationalError:
            flash("No se puedo editar el certificado.", "warning")
        return redirect(url_for(VISTA_CERTIFICADOS))

    return render_template("learning/certificados/editar_certificado.html", form=form)


def insert_style_in_html(template: str) -> str:
    """Insert CSS styles into HTML template."""
    html = template.html
    css = template.css

    if css:
        css = "<style>" + css + "</style>"
        return css + html
    return html


@certificate.route("/certificate/inspect/<ulid>/")
def certificate_inspect(ulid: str) -> str:
    """Inspect a certificate by its ULID."""
    row = database.session.execute(database.select(Certificado).filter_by(id=ulid)).first()
    if row is None:
        return "Certificate not found"
    consulta = row[0]

    return insert_style_in_html(consulta)


@certificate.route("/certificate/get_as_qr/<cert_id>/")
def certificacion_qr(cert_id: str) -> Response:
    """Generate QR code for certificate verification."""
    import qrcode

    base_url = request.url_root
    url = base_url + "/certificate/view/" + cert_id
    qr = qrcode.make(url, box_size=4)

    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    buffer.seek(0)

    response = make_response(buffer.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=QR.png"
    response.mimetype = "image/png"
    return response


@certificate.route("/certificate/certificate/<ulid>/")
def certificacion(ulid: str) -> str | Response:
    """Render a certificate based on certification ULID."""
    from jinja2 import BaseLoader, Environment

    row = database.session.execute(database.select(Certificacion).filter_by(id=ulid)).first()
    if row is None:
        return redirect(url_for("home.pagina_de_inicio"))
    certificacion_obj = row[0]

    row = database.session.execute(database.select(Certificado).filter_by(code=certificacion_obj.certificado)).first()
    if row is None:
        return redirect(url_for("home.pagina_de_inicio"))
    certificado_obj = row[0]

    # Get course or master class information
    content = certificacion_obj.get_content_info()
    content_type = certificacion_obj.get_content_type()

    row = database.session.execute(database.select(Usuario).filter_by(usuario=certificacion_obj.usuario)).first()
    if row is None:
        return redirect(url_for("home.pagina_de_inicio"))
    usuario = row[0]

    template = Environment(loader=BaseLoader, autoescape=True).from_string(insert_style_in_html(certificado_obj))  # type: ignore[arg-type]

    # Create context with both curso and master_class for template compatibility
    context = {
        "usuario": usuario,
        "certificacion": certificacion_obj,
        "certificado": certificado_obj,
        "url_for": url_for,
        "content_type": content_type,
    }

    if content_type == "course":
        context["curso"] = content
        context["master_class"] = None
    else:
        context["curso"] = content  # For backward compatibility with templates that expect 'curso'
        context["master_class"] = content

    return template.render(**context)


@certificate.route("/certificate/download/<ulid>/")
def certificate_serve_pdf(ulid: str) -> Response:
    """Editar categoria."""
    from flask_weasyprint import HTML, render_pdf
    from jinja2 import BaseLoader, Environment
    from weasyprint import CSS

    row = database.session.execute(database.select(Certificacion).filter_by(id=ulid)).first()
    if row is None:
        return redirect(url_for("home.pagina_de_inicio"))
    certificacion_obj = row[0]

    row = database.session.execute(database.select(Certificado).filter_by(code=certificacion_obj.certificado)).first()
    if row is None:
        return redirect(url_for("home.pagina_de_inicio"))
    certificado_obj = row[0]

    # Get course or master class information
    content = certificacion_obj.get_content_info()
    content_type = certificacion_obj.get_content_type()

    row = database.session.execute(database.select(Usuario).filter_by(usuario=certificacion_obj.usuario)).first()
    if row is None:
        return redirect(url_for("home.pagina_de_inicio"))
    usuario = row[0]

    rtemplate = Environment(loader=BaseLoader, autoescape=True).from_string(certificado_obj.html)  # type: ignore[arg-type]

    # Create context with both curso and master_class for template compatibility
    context = {
        "usuario": usuario,
        "certificacion": certificacion_obj,
        "certificado": certificado_obj,
        "url_for": url_for,
        "content_type": content_type,
    }

    if content_type == "course":
        context["curso"] = content
        context["master_class"] = None
    else:
        context["curso"] = content  # For backward compatibility with templates that expect 'curso'
        context["master_class"] = content

    return render_pdf(
        HTML(string=rtemplate.render(**context)),
        stylesheets=[CSS(string=certificado_obj.css)],
    )


@certificate.route("/certificate/issued/list")
@login_required
def certificaciones() -> str:
    """Lista de certificaciones emitidas."""
    # Build query based on user role
    query = database.select(Certificacion)

    # Python 3.10+ - Use match statement instead of if-elif-else for role-based filtering
    match current_user.tipo:
        case "admin":
            # Admins can see all certificates
            pass  # No additional filtering needed
        case "instructor":
            # Instructors can see certificates for courses they own
            from now_lms.db import DocenteCurso

            # Modern SQLAlchemy 2.x query pattern following project query guide
            instructor_courses = (
                database.session.execute(
                    database.select(DocenteCurso.curso).filter(
                        DocenteCurso.usuario == current_user.usuario, DocenteCurso.vigente.is_(True)
                    )
                )
                .scalars()
                .all()
            )

            if instructor_courses:
                # Filter certificates for instructor's courses
                query = query.filter(Certificacion.curso.in_(instructor_courses))
            else:
                # Instructor has no courses, show empty list
                query = query.filter(Certificacion.id.is_(None))
        case "student":
            # Students can only see their own certificates
            query = query.filter(Certificacion.usuario == current_user.usuario)
        case _:
            # Other user types (like moderator) can only see their own certificates
            query = query.filter(Certificacion.usuario == current_user.usuario)

    certificados_list = database.paginate(
        query,
        page=request.args.get("page", default=1, type=int),
        max_per_page=MAXIMO_RESULTADOS_EN_CONSULTA_PAGINADA,
        count=True,
    )
    return render_template("learning/certificados/lista_certificaciones.html", consulta=certificados_list)


@certificate.route("/certificate/view/<ulid>")
def certificado(ulid: str) -> str:
    """Lista de certificaciones emitidas."""
    row = database.session.execute(database.select(Certificacion).filter_by(id=ulid)).first()
    if row is None:
        return "Certificate not found"
    certificacion_obj = row[0]

    row = database.session.execute(database.select(Certificado).filter_by(code=certificacion_obj.certificado)).first()
    if row is None:
        return "Certificate template not found"
    certificado_obj = row[0]

    # Get course or master class information
    content = certificacion_obj.get_content_info()
    content_type = certificacion_obj.get_content_type()

    row = database.session.execute(database.select(Usuario).filter_by(usuario=certificacion_obj.usuario)).first()
    if row is None:
        return "User not found"
    usuario = row[0]

    # Create context with both curso and master_class for template compatibility
    context = {
        "usuario": usuario,
        "certificacion": certificacion_obj,
        "certificado": certificado_obj,
        "content_type": content_type,
    }

    if content_type == "course":
        context["curso"] = content
        context["master_class"] = None
    else:
        context["curso"] = content  # For backward compatibility with templates that expect 'curso'
        context["master_class"] = content

    return render_template("learning/certificados/certificado.html", **context)


@certificate.route("/certificate/issue/<course>/<user>/<template>/")
@login_required
@perfil_requerido("instructor")
def certificacion_crear(course: str, user: str, template: str) -> Response:
    """Generar un nuevo certificado."""
    # Check if user meets all requirements including evaluations
    from now_lms.vistas.evaluation_helpers import can_user_receive_certificate

    can_receive, reason = can_user_receive_certificate(course, user)
    if not can_receive:
        flash(f"No se puede emitir el certificado: {reason}", "warning")
        return redirect(url_for("certificate.certificaciones"))

    cert = Certificacion(usuario=user, curso=course, certificado=template)

    database.session.add(cert)
    database.session.commit()
    database.session.refresh(cert)

    return redirect(url_for("certificate.certificado", ulid=cert.id))


@certificate.route("/certificate/release/", methods=["GET", "POST"])
@login_required
@perfil_requerido("instructor")
def certificacion_generar() -> str | Response:
    """Generar un nuevo certificado."""
    from now_lms.db.tools import (
        generate_cource_choices,
        generate_masterclass_choices,
        generate_template_choices,
        generate_user_choices,
    )

    form = EmitCertificateForm()

    form.usuario.choices = generate_user_choices()
    form.curso.choices = generate_cource_choices()
    form.master_class.choices = generate_masterclass_choices()
    form.template.choices = generate_template_choices()

    if form.validate_on_submit() or request.method == "POST":
        content_type = form.content_type.data

        # Validate that either curso or master_class is selected based on content_type
        if content_type == "course" and not form.curso.data:
            flash("Por favor selecciona un curso.", "warning")
            return render_template(TEMPLATE_EMITIR_CERTIFICADO, form=form)
        if content_type == "masterclass" and not form.master_class.data:
            flash("Por favor selecciona una clase magistral.", "warning")
            return render_template(TEMPLATE_EMITIR_CERTIFICADO, form=form)

        # Check if user meets requirements for courses
        if content_type == "course":
            from now_lms.vistas.evaluation_helpers import can_user_receive_certificate

            can_receive, reason = can_user_receive_certificate(form.curso.data, form.usuario.data)
            if not can_receive:
                flash(f"No se puede emitir el certificado: {reason}", "warning")
                return render_template(TEMPLATE_EMITIR_CERTIFICADO, form=form)

            cert = Certificacion(
                usuario=form.usuario.data,
                curso=form.curso.data,
                master_class_id=None,
                certificado=form.template.data,
                nota=form.nota.data,
            )
        else:  # masterclass
            # For master classes, check if user is enrolled and confirmed
            enrollment = database.session.execute(
                database.select(MasterClassEnrollment).filter_by(
                    master_class_id=form.master_class.data, user_id=form.usuario.data
                )
            ).first()

            if not enrollment or not enrollment[0].is_confirmed:
                flash("El usuario debe estar inscrito y confirmado en la clase magistral.", "warning")
                return render_template(TEMPLATE_EMITIR_CERTIFICADO, form=form)

            cert = Certificacion(
                usuario=form.usuario.data,
                curso=None,
                master_class_id=form.master_class.data,
                certificado=form.template.data,
                nota=form.nota.data,
            )

        try:
            database.session.add(cert)
            database.session.commit()
            flash("Certificado generado correctamente.", "success")
            return redirect(url_for("certificate.certificaciones"))

        except OperationalError:
            flash("Hubo en error al crear la plantilla.", "warning")
            return redirect("/instructor")
    else:
        return render_template(TEMPLATE_EMITIR_CERTIFICADO, form=form)


# ---------------------------------------------------------------------------------------
# Program Certificate Routes
# ---------------------------------------------------------------------------------------


@certificate.route("/certificate/program/get_as_qr/<certificate_id>/")
def certificacion_programa_qr(certificate_id: str) -> Response:
    """Generate QR code for program certificate verification."""
    import qrcode

    base_url = request.url_root
    url = base_url + "/certificate/program/view/" + certificate_id
    qr = qrcode.make(url, box_size=4)

    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    buffer.seek(0)

    response = make_response(buffer.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=QR_programa.png"
    response.mimetype = "image/png"
    return response


@certificate.route("/certificate/program/view/<ulid>/")
def certificacion_programa(ulid: str) -> str:
    """View program certificate."""
    from jinja2 import BaseLoader, Environment

    certificacion_programa_obj = database.session.execute(
        database.select(CertificacionPrograma).filter_by(id=ulid)
    ).scalar_one_or_none()

    if not certificacion_programa_obj:
        abort(404)

    certificado_obj = database.session.execute(
        database.select(Certificado).filter_by(code=certificacion_programa_obj.certificado)
    ).scalar_one_or_none()

    if not certificado_obj:
        abort(404)

    programa = database.session.execute(
        database.select(Programa).filter_by(id=certificacion_programa_obj.programa)
    ).scalar_one_or_none()

    if not programa:
        abort(404)

    usuario = database.session.execute(
        database.select(Usuario).filter_by(usuario=certificacion_programa_obj.usuario)
    ).scalar_one_or_none()

    if not usuario:
        abort(404)

    template = Environment(loader=BaseLoader, autoescape=True).from_string(insert_style_in_html(certificado_obj))  # type: ignore

    context = {
        "usuario": usuario,
        "certificacion_programa": certificacion_programa_obj,
        "certificado": certificado_obj,
        "programa": programa,
        "id": ulid,  # Keep backward compatibility for templates using id
        "url_for": url_for,
        "database": database,  # For accessing Curso model in template
    }

    return template.render(**context)


@certificate.route("/certificate/program/download/<ulid>/")
def certificate_programa_serve_pdf(ulid: str) -> Any:
    """Download program certificate as PDF."""
    from flask_weasyprint import HTML, render_pdf
    from jinja2 import BaseLoader, Environment
    from weasyprint import CSS

    certificacion_programa_obj = database.session.execute(
        database.select(CertificacionPrograma).filter_by(id=ulid)
    ).scalar_one_or_none()

    if not certificacion_programa_obj:
        abort(404)

    certificado_obj = database.session.execute(
        database.select(Certificado).filter_by(code=certificacion_programa_obj.certificado)
    ).scalar_one_or_none()

    if not certificado_obj:
        abort(404)

    programa = database.session.execute(
        database.select(Programa).filter_by(id=certificacion_programa_obj.programa)
    ).scalar_one_or_none()

    if not programa:
        abort(404)

    usuario = database.session.execute(
        database.select(Usuario).filter_by(usuario=certificacion_programa_obj.usuario)
    ).scalar_one_or_none()

    if not usuario:
        abort(404)

    template = Environment(loader=BaseLoader, autoescape=True).from_string(certificado_obj.html)  # type: ignore

    context = {
        "usuario": usuario,
        "certificacion_programa": certificacion_programa_obj,
        "certificado": certificado_obj,
        "programa": programa,
        "url_for": url_for,
        "database": database,  # For accessing Curso model in template
    }

    return render_pdf(
        HTML(string=template.render(**context)),
        stylesheets=[CSS(string=certificado_obj.css)],
    )
