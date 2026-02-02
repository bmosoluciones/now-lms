# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.

"""
Module to run NOW LMS.

Several services prefer to have a wsgi.py server file.
"""

from now_lms import init_app, lms_app as app
from now_lms.cli import serve

app.app_context().push()

if __name__ == "__main__":
    init_app(with_examples=False)
    serve()
