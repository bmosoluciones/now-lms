# Copyright 2022 - 2024 BMO Soluciones, S.A.
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

"""Configuración de logs."""

# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------
import logging
from os import environ
from sys import stdout

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------


# Definir nivel TRACE
TRACE_LEVEL_NUM = 5
logging.addLevelName(TRACE_LEVEL_NUM, "TRACE")


# Método adicional para usar logger.trace(...)
def trace(self, message, *args, **kwargs):
    """Log a message with TRACE level."""
    if self.isEnabledFor(TRACE_LEVEL_NUM):
        self._log(TRACE_LEVEL_NUM, message, args, **kwargs)


logging.Logger.trace = trace


# Configurar nivel desde variable de entorno (default: INFO)
log_level_str = environ.get("LOG_LEVEL", "INFO").upper()

# Soporte de niveles personalizados
custom_levels = {
    "TRACE": TRACE_LEVEL_NUM,
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

# Nivel numérico, default INFO si no coincide
numeric_level = custom_levels.get(log_level_str, logging.INFO)

# Configurar logger raíz
root_logger = logging.getLogger("now_lms")
root_logger.setLevel(numeric_level)

# Handler solo para stdout
console_handler = logging.StreamHandler(stdout)
console_handler.setLevel(numeric_level)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s: %(message)s")
console_handler.setFormatter(formatter)
root_logger.addHandler(console_handler)

# Configurar logger de Flask y Werkzeug al mismo nivel
logging.getLogger("flask").setLevel(numeric_level)
logging.getLogger("werkzeug").setLevel(numeric_level)

# Configurar logger de SQLAlchemy al nivel WARNING
logging.getLogger("sqlalchemy").setLevel(logging.WARNING)

LOG_LEVEL = root_logger.getEffectiveLevel()

log = root_logger
logger = root_logger
