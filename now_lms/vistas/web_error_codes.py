# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.

"""
NOW Learning Management System.

Gestión de certificados.
"""


from __future__ import annotations

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------
from flask import Blueprint, render_template

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms.config import DIRECTORIO_PLANTILLAS

# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------


# ---------------------------------------------------------------------------------------
# Administración de Etiquetas.
# ---------------------------------------------------------------------------------------

web_error = Blueprint("error", __name__, template_folder=DIRECTORIO_PLANTILLAS)


@web_error.route("/http/error/<code>")
def error_page(code: str) -> str:
    """HTTP error code pages."""
    url = "error_pages/" + code + ".html"

    return render_template(url)
