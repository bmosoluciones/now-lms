# ---------------------------------------------------------------------------------------
# Libreria estandar
# ---------------------------------------------------------------------------------------

# ---------------------------------------------------------------------------------------
# Librerias de terceros
# ---------------------------------------------------------------------------------------
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from flask_uploads import UploadNotAllowed
from sqlalchemy.exc import OperationalError

# ---------------------------------------------------------------------------------------
# Recursos locales
# ---------------------------------------------------------------------------------------
from now_lms.cache import cache
from now_lms.config import DIRECTORIO_PLANTILLAS, images
from now_lms.db import Usuario, database
from now_lms.db.tools import elimina_imagen_usuario
from now_lms.forms import UserForm
from now_lms.logs import log
from now_lms.misc import GENEROS

user_profile = Blueprint("user_profile", __name__, template_folder=DIRECTORIO_PLANTILLAS)


# ---------------------------------------------------------------------------------------
# Espacio del usuario, por defecto un usuario se considera un estudiante.
# ---------------------------------------------------------------------------------------
@user_profile.route("/student")
@login_required
def pagina_estudiante():
    """Perfil de usuario."""
    return render_template("perfiles/estudiante.html")


@user_profile.route("/perfil")
@login_required
def perfil():
    """Perfil del usuario."""
    registro_usuario = database.session.execute(database.select(Usuario).filter(Usuario.id == current_user.id)).first()[0]

    return render_template("inicio/perfil.html", perfil=registro_usuario, genero=GENEROS)


@user_profile.route("/user/<id_usuario>")
@login_required
def usuario(id_usuario):
    """Acceso administrativo al perfil de un usuario."""
    perfil_usuario = Usuario.query.filter_by(usuario=id_usuario).first()
    # La misma plantilla del perfil de usuario con permisos elevados como
    # activar desactivar el perfil o cambiar el perfil del usuario.
    if current_user.usuario == id_usuario or current_user.tipo != "student" or perfil_usuario.visible is True:
        return render_template("inicio/perfil.html", perfil=perfil_usuario, genero=GENEROS)
    else:
        return render_template("inicio/private.html")


@user_profile.route("/perfil/edit/<ulid>", methods=["GET", "POST"])
@login_required
def edit_perfil(ulid: str):
    """Actualizar información de usuario."""
    if current_user.id != ulid:
        abort(403)

    usuario_ = database.session.get(Usuario, ulid)
    form = UserForm(obj=usuario_)

    if request.method == "POST":
        #
        usuario_.nombre = form.nombre.data
        usuario_.apellido = form.apellido.data
        usuario_.correo_electronico = form.correo_electronico.data
        usuario_.url = form.url.data
        usuario_.linkedin = form.linkedin.data
        usuario_.facebook = form.facebook.data
        usuario_.twitter = form.twitter.data
        usuario_.github = form.github.data
        usuario_.youtube = form.youtube.data
        usuario_.genero = form.genero.data
        usuario_.titulo = form.titulo.data
        usuario_.nacimiento = form.nacimiento.data
        usuario_.bio = form.bio.data

        if form.correo_electronico.data != usuario_.correo_electronico:
            usuario_.correo_electronico_verificado = False
            flash("Favor verifique su nuevo correo electronico.", "warning")

        try:  # pragma: no cover
            database.session.commit()
            cache.delete("view/" + url_for("perfil"))
            flash("Pefil actualizado.", "success")
            if "logo" in request.files:
                try:
                    picture_file = images.save(request.files["logo"], folder="usuarios", name=current_user.id + ".jpg")
                    if picture_file:
                        usuario_ = database.session.execute(
                            database.select(Usuario).filter(Usuario.id == current_user.id)
                        ).first()[0]
                        usuario_.portada = True
                        database.session.commit()
                        flash("Imagen de perfil actualizada.", "success")
                except UploadNotAllowed:
                    log.warning("No se pudo actualizar la imagen de perfil.", "error")
        except OperationalError:  # pragma: no cover
            flash("Error al editar el perfil.", "error")

        return redirect("/perfil")

    else:  # pragma: no cover
        return render_template("inicio/perfil_editar.html", form=form, usuario=usuario_)


@user_profile.route("/perfil/<ulid>/delete_logo")
@login_required
def elimina_logo_usuario(ulid: str):
    """Elimina logo de usuario."""
    if current_user.id != ulid:
        abort(403)

    elimina_imagen_usuario(ulid=ulid)
    return redirect("/perfil")
