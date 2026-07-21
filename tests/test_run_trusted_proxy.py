# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""
Regression test for NOW_LMS_TRUSTED_PROXY wiring into Waitress in run.py.

Behind a TLS-terminating reverse proxy, Waitress (clear_untrusted_proxy_headers
defaults to True) strips X-Forwarded-* headers unless the proxy is explicitly
trusted, so any FORCE_HTTPS-style check never sees X-Forwarded-Proto=https and
the app redirect-loops. run.py's fix reads NOW_LMS_TRUSTED_PROXY and, when
set, adds trusted_proxy / trusted_proxy_headers / clear_untrusted_proxy_headers
to the kwargs passed to waitress.serve(); when unset, behavior is unchanged.

run.py is a script, not an importable library module — it runs its startup
sequence (DB migration, then waitress.serve()) at import time. To observe the
kwargs actually handed to waitress.serve() without starting a real server or
touching a real database, each case runs in a subprocess that:
  1. monkeypatches now_lms.init_app and now_lms.alembic.upgrade to no-ops,
     so run.py's pre-init "with lms_app.app_context(): alembic.upgrade()"
     and "if init_app():" steps succeed without a real database (irrelevant
     to what this test covers — that path is exercised separately by the
     PostgreSQL/SQLite bootstrap regression tests);
  2. monkeypatches waitress.serve() to capture its kwargs and exit instead of
     actually serving;
  3. imports run, which runs the above and then calls the patched serve().
"""

import json
import os
import subprocess
import sys

_HARNESS = """
import json
import waitress
import now_lms

now_lms.init_app = lambda *a, **kw: True
now_lms.alembic.upgrade = lambda *a, **kw: None

captured = {}


def fake_serve(app, **kwargs):
    captured.update(kwargs)
    print("CAPTURED_KWARGS=" + json.dumps(
        {k: (sorted(v) if isinstance(v, set) else v) for k, v in kwargs.items()}
    ))
    raise SystemExit(0)


waitress.serve = fake_serve

import run  # noqa: F401  (module-level side effects are the point)
"""


def _captured_waitress_kwargs(trusted_proxy_value: str | None) -> dict:
    env = os.environ.copy()
    env.update(
        {
            "CI": "True",
            "SECRET_KEY": "test-secret-key",
            "DATABASE_URL": "sqlite:///:memory:",
            "LOG_LEVEL": "ERROR",
            "WSGI_SERVER": "waitress",
        }
    )
    if trusted_proxy_value is None:
        env.pop("NOW_LMS_TRUSTED_PROXY", None)
    else:
        env["NOW_LMS_TRUSTED_PROXY"] = trusted_proxy_value

    result = subprocess.run(
        [sys.executable, "-c", _HARNESS],
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"

    for line in result.stdout.splitlines():
        if line.startswith("CAPTURED_KWARGS="):
            return json.loads(line[len("CAPTURED_KWARGS=") :])
    raise AssertionError(f"waitress.serve() kwargs were never captured.\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}")


def test_waitress_trusts_the_proxy_when_env_opt_in_is_set():
    kwargs = _captured_waitress_kwargs("*")

    assert kwargs["trusted_proxy"] == "*"
    assert sorted(kwargs["trusted_proxy_headers"]) == [
        "x-forwarded-for",
        "x-forwarded-host",
        "x-forwarded-proto",
    ]
    assert kwargs["clear_untrusted_proxy_headers"] is True


def test_waitress_does_not_trust_any_proxy_when_env_opt_in_is_unset():
    kwargs = _captured_waitress_kwargs(None)

    assert "trusted_proxy" not in kwargs
    assert "trusted_proxy_headers" not in kwargs
    assert "clear_untrusted_proxy_headers" not in kwargs
