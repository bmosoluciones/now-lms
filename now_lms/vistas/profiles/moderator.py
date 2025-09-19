"""Moderator profile views and functionality."""

from __future__ import annotations

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------
from flask import Blueprint, render_template
from flask_login import login_required

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms.config import DIRECTORIO_PLANTILLAS

# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------


moderator_profile = Blueprint("moderator_profile", __name__, template_folder=DIRECTORIO_PLANTILLAS)


# ---------------------------------------------------------------------------------------
# Espacio del moderador.
# ---------------------------------------------------------------------------------------
@moderator_profile.route("/moderator")
@login_required
def pagina_moderador() -> str:
    """Perfil de usuario moderador."""
    return render_template("perfiles/moderador.html")
