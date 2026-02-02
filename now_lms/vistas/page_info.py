# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.

"""Page info view - development information page."""


from __future__ import annotations

import os

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------
from flask import Blueprint, current_app, redirect, render_template
from werkzeug.wrappers import Response

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms.config import DIRECTORIO_PLANTILLAS
from now_lms.db.info import app_info, config_info, lms_info
from now_lms.version import CODE_NAME, VERSION

page_info = Blueprint("page_info", __name__, template_folder=DIRECTORIO_PLANTILLAS)


@page_info.route("/page_info")
def page_info_view() -> str | Response:
    """Display development information page - only available when CI environment variable is set."""
    # Check if CI environment variable is set using the same logic as config
    ci_value = os.environ.get("CI", "").strip().lower()
    valores_true = {"1", "true", "yes", "on", "development", "dev"}

    if ci_value not in valores_true:
        return redirect("/")

    # Gather system information
    config_data = config_info()
    app_data = app_info(current_app)
    lms_data = lms_info()

    # Get routes information
    routes = []
    for rule in current_app.url_map.iter_rules():
        if rule.endpoint != "static":  # Skip static file handling
            routes.append(
                {
                    "endpoint": rule.endpoint,
                    "rule": str(rule),
                    "methods": sorted((rule.methods or set()) - {"HEAD", "OPTIONS"}),
                }
            )
    routes.sort(key=lambda x: x["rule"])

    # Get filtered environment variables (exclude sensitive ones)
    sensitive_vars = {"SECRET_KEY", "DATABASE_URL", "PASSWORD", "KEY", "TOKEN", "API_KEY"}
    env_vars = {}
    for key, value in os.environ.items():
        if not any(sensitive in key.upper() for sensitive in sensitive_vars):
            env_vars[key] = value

    return render_template(
        "page_info/page_info.html",
        version=VERSION,
        code_name=CODE_NAME,
        config_data=config_data,
        app_data=app_data,
        lms_data=lms_data,
        routes=routes,
        env_vars=env_vars,
    )
