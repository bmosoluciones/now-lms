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

# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------
import platform
from os import environ

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms import lms_app, init_app, alembic
from now_lms.logs import log
from now_lms.worker_config import get_worker_config_from_env

PORT = environ.get("PORT") or 8080

# Get WSGI server from environment variable (defaults to waitress)
WSGI_SERVER = environ.get("WSGI_SERVER", "waitress").lower()

# ---------------------------------------------------------------------------------------
# Update the database schema
# ---------------------------------------------------------------------------------------
with lms_app.app_context():
    alembic.upgrade()

if init_app():
    log.info("Iniciando NOW Learning Management System")

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

                options = {
                    "bind": f"0.0.0.0:{PORT}",
                    "workers": workers,
                    "threads": threads,
                    "worker_class": "gthread" if threads > 1 else "sync",
                    "preload_app": True,
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
else:
    log.error("No se pudo iniciar NOW Learning Management System.")
