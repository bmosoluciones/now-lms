# ---------------------------------------------------------------------------------------
# Libreria estandar
# ---------------------------------------------------------------------------------------

# ---------------------------------------------------------------------------------------
# Librerias de terceros
# ---------------------------------------------------------------------------------------
from flask import Blueprint, render_template
from flask_login import login_required

# ---------------------------------------------------------------------------------------
# Recursos locales
# ---------------------------------------------------------------------------------------
from now_lms.config import DIRECTORIO_PLANTILLAS

moderator_profile = Blueprint("moderator_profile", __name__, template_folder=DIRECTORIO_PLANTILLAS)


# ---------------------------------------------------------------------------------------
# Espacio del moderador.
# ---------------------------------------------------------------------------------------
@moderator_profile.route("/moderator")
@login_required
def pagina_moderador():
    """Perfil de usuario moderador."""
    return render_template("perfiles/moderador.html")
