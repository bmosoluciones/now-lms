# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.

"""
Module to run NOW LMS.

Several services prefer to have a wsgi.py server file.
"""

# Auto-compile stale .mo catalogs BEFORE importing the app. .mo is
# .gitignored, so a fresh checkout / demo deploy may have a .mo older
# than the .po (the catalog source). Without this, Babel falls back to
# the Spanish msgid for every translation added after the .mo was last
# compiled - which is exactly the demo "Gender rendered in Spanish" bug.
from now_lms.i18n_autocompile import ensure_translations_compiled

ensure_translations_compiled()

from now_lms import init_app, lms_app as app  # noqa: E402
from now_lms.cli import serve  # noqa: E402
from now_lms.session_config import ensure_session_storage  # noqa: E402

app.app_context().push()

if __name__ == "__main__":
    init_app(with_examples=False)
    ensure_session_storage(app)
    serve()
