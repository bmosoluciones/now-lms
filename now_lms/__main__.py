# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.

"""Modulo para ejecutar NOW LMS."""


from __future__ import annotations

# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------
from os import environ

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms import init_app
from now_lms.cli import serve
from now_lms.config import DESARROLLO
from now_lms.logs import log

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------


if __name__ == "__main__":
    environ["FLASK_APP"] = "now_lms"
    log.info("Starting NOW Learning Management System.")
    if DESARROLLO:
        log.trace("Running NOW-LMS with development options.")
        init_app(with_examples=True)
        serve()
    log.trace("Starting NOW-LMS as importable module.")
    init_app(with_examples=False)
    serve()
