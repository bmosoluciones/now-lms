# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.

# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------
import platform
from os import environ

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms import lms_app, init_app
from now_lms.logs import log
from now_lms.session_config import ensure_session_storage
from now_lms.worker_config import get_worker_config_from_env

PORT = environ.get("PORT") or 8080

# Get WSGI server from environment variable (defaults to waitress)
WSGI_SERVER = environ.get("WSGI_SERVER", "waitress").lower()

if WSGI_SERVER not in {"gunicorn", "waitress"}:
    raise SystemExit(f"Unsupported WSGI_SERVER={WSGI_SERVER!r}; expected 'gunicorn' or 'waitress'")

# ---------------------------------------------------------------------------------------
# Initialize the database schema.
#
# init_app() is the single owner of schema management and does the right thing per DB
# state: on a fresh database it runs initial_setup() (create_all() + alembic.stamp(head));
# on an already-populated database it runs alembic.upgrade() (when NOW_LMS_AUTO_MIGRATE is
# set). Calling alembic.upgrade() here unconditionally — before init_app() — broke fresh
# deployments: on an empty database the migration chain runs from base and fails (e.g. a
# migration creates course_library with a FK to the not-yet-created curso table), and after
# a create_all() it collides with unguarded CREATE TABLE migrations. Let init_app() decide.
# ---------------------------------------------------------------------------------------
if init_app():
    log.info("Iniciando NOW Learning Management System")

    # Ensure session storage is ready before starting the WSGI server
    ensure_session_storage(lms_app)

    # Get optimal worker and thread configuration
    workers, threads = get_worker_config_from_env()

    if WSGI_SERVER == "gunicorn":
        # Use Gunicorn (Linux/Unix only)
        if platform.system() == "Windows":
            log.error("Gunicorn is not supported on Windows. Falling back to Waitress.")
            WSGI_SERVER = "waitress"
        else:
            try:
                from gunicorn.app.base import BaseApplication

                class StandaloneApplication(BaseApplication):
                    """Gunicorn application class for NOW LMS."""

                    def __init__(self, app, options=None):
                        self.options = options or {}
                        self.application = app
                        super().__init__()

                    def load_config(self):
                        for key, value in self.options.items():
                            if key in self.cfg.settings and value is not None:
                                self.cfg.set(key.lower(), value)

                    def load(self):
                        return self.application

                from now_lms.session_config import reset_connections_after_fork

                options = {
                    "bind": f"0.0.0.0:{PORT}",
                    "workers": workers,
                    "threads": threads,
                    "worker_class": "gthread" if threads > 1 else "sync",
                    # Preload the application to ensure that the shared session
                    # storage and database connections/tables are fully established
                    # in the master process before worker processes and threads are created.
                    # This prevents session loss and initialization race conditions across threads.
                    "preload_app": True,
                    "post_fork": reset_connections_after_fork,
                    "timeout": 120,
                    "graceful_timeout": 30,
                    "keepalive": 5,
                    "accesslog": "-",
                    "errorlog": "-",
                    "loglevel": "info",
                }

                log.info(
                    f"Starting Gunicorn WSGI server on port {PORT} with {workers} workers and {threads} threads per worker."
                )

                StandaloneApplication(lms_app, options).run()
            except ImportError:
                log.error("Gunicorn is not installed. Falling back to Waitress.")
                WSGI_SERVER = "waitress"

    if WSGI_SERVER == "waitress":
        # Use Waitress (cross-platform)
        try:
            from waitress import serve

            log.info(f"Starting Waitress WSGI server on port {PORT} with {threads} threads")
            serve(
                lms_app,
                host="0.0.0.0",
                port=PORT,
                threads=threads,
                channel_timeout=120,
                cleanup_interval=30,
                _quiet=False,
            )
        except ImportError:
            log.error("Waitress no está instalado. Por favor instálalo con: pip install waitress")
            log.error("No se pudo iniciar NOW Learning Management System.")
            raise
else:
    log.error("No se pudo iniciar NOW Learning Management System.")
    raise SystemExit(1)
