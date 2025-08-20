"""Moderator profile views and functionality."""

# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------
from flask import Blueprint, redirect, url_for
from flask_login import login_required

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms.config import DIRECTORIO_PLANTILLAS

moderator_profile = Blueprint("moderator_profile", __name__, template_folder=DIRECTORIO_PLANTILLAS)


# ---------------------------------------------------------------------------------------
# Espacio del moderador.
# ---------------------------------------------------------------------------------------
@moderator_profile.route("/moderator")
@login_required
def pagina_moderador():
    """Perfil de usuario moderador - Redirige a mensajes."""
    return redirect(url_for("msg.user_messages"))
