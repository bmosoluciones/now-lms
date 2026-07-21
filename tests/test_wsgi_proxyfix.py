# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""
Regression test for the ProxyFix NameError in create_app().

create_app() applied ProxyFix as ``ProxyFix(app.wsgi_app, ...)``, but the
only local name bound inside create_app() is ``flask_app`` — ``app`` is a
*module-level* alias (``app = lms_app``) assigned only after create_app()
returns. Any deployment with NOW_LMS_FORCE_HTTPS set therefore crashed at
import time with ``NameError: name 'app' is not defined``, because the
crash happened inside create_app() itself, before the module-level
``app = lms_app`` line was ever reached.

Because FORCE_HTTPS is read once, at import time, from an environment
variable (now_lms.config.FORCE_HTTPS), the only reliable way to exercise
both the "flag off" and "flag on" import paths in the same test session is
to import the package fresh in a subprocess with the environment variable
set before the interpreter starts — reusing the already-imported
``now_lms`` module (or monkeypatching its module-level constant) would not
re-execute the buggy line inside create_app().
"""

import os
import subprocess
import sys

_BASE_ENV = {
    "CI": "True",
    "SECRET_KEY": "test-secret-key",
    "DATABASE_URL": "sqlite:///:memory:",
    "LOG_LEVEL": "ERROR",
}


def _run(extra_env: dict, code: str) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env.update(_BASE_ENV)
    env.update(extra_env)
    return subprocess.run(
        [sys.executable, "-c", code],
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )


def test_import_succeeds_and_wraps_wsgi_app_with_proxyfix_under_force_https():
    """A fresh import with NOW_LMS_FORCE_HTTPS=1 must not raise NameError,
    and the resulting app's wsgi_app must actually be wrapped in ProxyFix."""
    code = (
        "import now_lms\n"
        "from werkzeug.middleware.proxy_fix import ProxyFix\n"
        "assert isinstance(now_lms.lms_app.wsgi_app, ProxyFix), "
        "f'expected ProxyFix wrapping, got {type(now_lms.lms_app.wsgi_app)!r}'\n"
        "print('OK')\n"
    )
    result = _run({"NOW_LMS_FORCE_HTTPS": "1"}, code)

    assert "NameError" not in result.stderr, f"stderr:\n{result.stderr}"
    assert result.returncode == 0, f"import crashed (rc={result.returncode}):\n{result.stderr}"
    assert "OK" in result.stdout, f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"


def test_wsgi_app_is_not_wrapped_when_force_https_is_unset():
    """Sanity control: without the flag, no ProxyFix wrapping happens —
    proves the previous test is actually exercising the FORCE_HTTPS branch,
    not passing for an unrelated reason."""
    code = (
        "import now_lms\n"
        "from werkzeug.middleware.proxy_fix import ProxyFix\n"
        "assert not isinstance(now_lms.lms_app.wsgi_app, ProxyFix), "
        "'wsgi_app should not be ProxyFix-wrapped when NOW_LMS_FORCE_HTTPS is unset'\n"
        "print('OK')\n"
    )
    result = _run({"NOW_LMS_FORCE_HTTPS": "0"}, code)

    assert result.returncode == 0, f"stderr:\n{result.stderr}"
    assert "OK" in result.stdout, f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
