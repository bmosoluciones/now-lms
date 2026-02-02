# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.

"""Health check endpoint."""


from __future__ import annotations

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------
from flask import Blueprint, Response, jsonify
from sqlalchemy import text

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms.db import database
from now_lms.version import CODE_NAME, VERSION

# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------


health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health() -> tuple[Response, int]:
    """Health check endpoint for application status monitoring."""
    # Default response
    status = {"status": "ok", "database": "ok", "version": VERSION, "code_name": CODE_NAME}

    try:
        # Simple DB check (lightweight)
        database.session.execute(text("SELECT 1"))
    except Exception as e:
        status["status"] = "error"
        status["database"] = f"error: {str(e)}"

    return jsonify(status), 200 if status["status"] == "ok" else 503
