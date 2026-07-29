# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""Regression tests for session persistence across WSGI worker processes."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import textwrap
from types import SimpleNamespace
from unittest.mock import Mock


WORKER_SCRIPT = textwrap.dedent(
    """
    import sys
    from flask_login import UserMixin, current_user, login_user
    import now_lms

    app = now_lms.lms_app
    app.before_request_funcs.clear()

    class ProbeUser(UserMixin):
        id = 'multiworker-user'
        usuario = id

    # Isolate session persistence from the application's user schema while
    # exercising Flask-Login's real login/load behavior in both processes.
    now_lms.administrador_sesion._user_callback = lambda user_id: ProbeUser() if user_id == ProbeUser.id else None

    @app.get('/_session_probe')
    def session_probe():
        if sys.argv[1] == 'write':
            login_user(ProbeUser())
            return 'written'
        return current_user.get_id() if current_user.is_authenticated else 'missing'

    client = app.test_client()
    if sys.argv[1] == 'write':
        response = client.get('/_session_probe')
        cookie = response.headers['Set-Cookie'].split(';', 1)[0]
        print('RESULT:' + cookie)
    else:
        name, value = sys.argv[2].split('=', 1)
        client.set_cookie(name, value)
        response = client.get('/_session_probe')
        print('RESULT:' + response.get_data(as_text=True))
    """
)


def _run_worker(mode: str, database_url: str, cookie: str | None = None) -> str:
    env = os.environ.copy()
    # The child represents a production WSGI worker, even though its parent is
    # pytest. These variables otherwise disable Flask-Session at import time.
    for key in ("CI", "PYTEST_CURRENT_TEST", "PYTEST_VERSION"):
        env.pop(key, None)
    env.update(
        {
            "DATABASE_URL": database_url,
            "SECRET_KEY": "shared-test-secret-key-that-is-long-enough",
            "LOG_LEVEL": "ERROR",
        }
    )
    command = [sys.executable, "-c", WORKER_SCRIPT, mode]
    if cookie is not None:
        command.append(cookie)
    result = subprocess.run(command, env=env, check=False, capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr
    return result.stdout.rsplit("RESULT:", 1)[1].strip()


def test_database_session_survives_request_on_another_worker(tmp_path: Path):
    database_url = f"sqlite:///{tmp_path / 'shared-workers.db'}"

    cookie = _run_worker("write", database_url)
    value_seen_by_second_worker = _run_worker("read", database_url, cookie)

    assert value_seen_by_second_worker == "multiworker-user"


def test_gunicorn_postfork_discards_inherited_database_pool(monkeypatch):
    import now_lms
    from now_lms.db import database
    from now_lms.session_config import reset_connections_after_fork

    with now_lms.lms_app.app_context():
        dispose = Mock()
        monkeypatch.setattr(database.engine, "dispose", dispose)

    reset_connections_after_fork(None, SimpleNamespace(pid=1234))

    dispose.assert_called_once_with(close=False)


def test_init_session_sqlalchemy_success(monkeypatch):
    from flask import Flask
    from now_lms.session_config import init_session
    from unittest.mock import MagicMock
    from flask_session.base import ServerSideSessionInterface

    app = Flask("test_app")
    app.config["TESTING"] = False
    monkeypatch.delenv("SESSION_REDIS_URL", raising=False)
    monkeypatch.delenv("CACHE_REDIS_URL", raising=False)
    monkeypatch.delenv("REDIS_URL", raising=False)

    mock_db = MagicMock()

    import now_lms.session_config
    monkeypatch.setattr(now_lms.session_config, "get_session_config", lambda app: {
        "SESSION_TYPE": "sqlalchemy",
        "SESSION_SQLALCHEMY_TABLE": "flask_sessions",
    })

    monkeypatch.setattr("now_lms.db.database", mock_db)

    mock_session_cls = MagicMock()
    monkeypatch.setattr("flask_session.Session", mock_session_cls)
    app.session_interface = MagicMock(spec=ServerSideSessionInterface)

    init_session(app)

    # Should run successfully and set session configuration
    assert app.config.get("SESSION_TYPE") == "sqlalchemy"


def test_initial_setup_session_table_verification_success(monkeypatch):
    from flask import Flask
    from now_lms import initial_setup
    from unittest.mock import MagicMock

    app = Flask("test_app")
    app.config["TESTING"] = False
    app.config["SESSION_TYPE"] = "sqlalchemy"
    app.config["SESSION_SQLALCHEMY_TABLE"] = "flask_sessions"

    mock_db = MagicMock()
    monkeypatch.setattr("now_lms.database", mock_db)
    monkeypatch.setattr("now_lms.db.database", mock_db)

    mock_inspector = MagicMock()
    mock_inspector.get_table_names.return_value = ["flask_sessions"]
    monkeypatch.setattr("sqlalchemy.inspect", lambda engine: mock_inspector)

    monkeypatch.setattr("now_lms.system_info", MagicMock())
    monkeypatch.setattr("now_lms.crear_configuracion_predeterminada", MagicMock())
    monkeypatch.setattr("now_lms.crear_certificados", MagicMock())
    monkeypatch.setattr("now_lms.crear_curso_predeterminado", MagicMock())
    monkeypatch.setattr("now_lms.crear_curso_autoaprendizaje", MagicMock())
    monkeypatch.setattr("now_lms.crear_evaluacion_predeterminada", MagicMock())
    monkeypatch.setattr("now_lms.crear_usuarios_predeterminados", MagicMock())
    monkeypatch.setattr("now_lms.crear_certificacion", MagicMock())
    monkeypatch.setattr("now_lms.crear_blog_post_predeterminado", MagicMock())
    monkeypatch.setattr("now_lms.crear_paginas_estaticas_predeterminadas", MagicMock())
    monkeypatch.setattr("now_lms.populate_custmon_data_dir", MagicMock())
    monkeypatch.setattr("now_lms.populate_custom_theme_dir", MagicMock())
    # v2.0.0's initial_setup ends with alembic.stamp(); this bare Flask app was
    # never alembic.init_app'd, so the real extension KeyErrors on its weakref
    # registry. Mock it like every other collaborator above.
    monkeypatch.setattr("now_lms.alembic", MagicMock())

    initial_setup(flask_app=app)

    mock_db.create_all.assert_called_once()


def test_initial_setup_session_table_verification_failure(monkeypatch):
    from flask import Flask
    from now_lms import initial_setup
    from unittest.mock import MagicMock
    import pytest

    app = Flask("test_app")
    app.config["TESTING"] = False
    app.config["SESSION_TYPE"] = "sqlalchemy"
    app.config["SESSION_SQLALCHEMY_TABLE"] = "flask_sessions"

    mock_db = MagicMock()
    monkeypatch.setattr("now_lms.database", mock_db)
    monkeypatch.setattr("now_lms.db.database", mock_db)

    mock_inspector = MagicMock()
    mock_inspector.get_table_names.return_value = []
    monkeypatch.setattr("sqlalchemy.inspect", lambda engine: mock_inspector)

    with pytest.raises(RuntimeError, match="Required session table 'flask_sessions' is missing."):
        initial_setup(flask_app=app)
