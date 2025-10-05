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
from os import environ

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------
from loguru import logger

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms import lms_app, init_app
from now_lms.worker_config import get_worker_config_from_env

PORT = environ.get("PORT") or 8080

if init_app():
    logger.info("Iniciando NOW Learning Management System")
    try:
        from gunicorn.app.base import BaseApplication

        class StandaloneApplication(BaseApplication):
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

        # Get optimal worker and thread configuration
        workers, threads = get_worker_config_from_env()
        
        options = {
            "bind": f"0.0.0.0:{PORT}",
            "workers": workers,
            "threads": threads,
            "worker_class": "gthread" if threads > 1 else "sync",
            "timeout": 120,
            "accesslog": "-",
            "errorlog": "-",
        }

        logger.info(f"Starting with {workers} workers and {threads} threads per worker")
        StandaloneApplication(lms_app, options).run()
    except ImportError:
        logger.error("Gunicorn no está instalado. Por favor instálalo con: pip install gunicorn")
        logger.error("No se pudo iniciar NOW Learning Management System.")
else:
    logger.error("No se pudo iniciar NOW Learning Management System.")
