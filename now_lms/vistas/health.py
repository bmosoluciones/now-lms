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

"""Health check endpoint."""

# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------
from flask import Blueprint, jsonify
from sqlalchemy import text

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms.db import database
from now_lms.version import CODE_NAME, VERSION

health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health():
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
