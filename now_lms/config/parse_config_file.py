# Copyright 2022 - 2023 BMO Soluciones, S.A.
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
# Contributors:
# - William José Moreno Reyes

"""Configuration file parser."""
# ---------------------------------------------------------------------------------------
# Libreria estandar
# ---------------------------------------------------------------------------------------
from os import getcwd, path
from pathlib import Path
from typing import Union

# ---------------------------------------------------------------------------------------
# Librerias de terceros
# ---------------------------------------------------------------------------------------
from configobj import ConfigObj

# ---------------------------------------------------------------------------------------
# Recursos locales
# ---------------------------------------------------------------------------------------
from now_lms.logs import log


# ---------------------------------------------------------------------------------------
# Configuration can be loaded from a init like life.
# ---------------------------------------------------------------------------------------
BASE_FILE: str = "nowlms.conf"
# Default configuration file is /etc/nowlms.conf
GLOBAL_CONFIG_FILE: Path = Path(path.join("/etc/", BASE_FILE))
# Configuration file can be placed in $home/.config/nowlms.conf
USER_CONFIG_FILE: Path = Path(path.join(Path.home(), ".config", BASE_FILE))
# Current dir config=
CURRENT_DIR_CONFIG = Path(path.join(getcwd(), BASE_FILE))


# ---------------------------------------------------------------------------------------
# Configuration can be placed in diferent directories.
# ---------------------------------------------------------------------------------------
if Path.exists(GLOBAL_CONFIG_FILE):
    CONFIG_FILE: Union[str, Path, None] = GLOBAL_CONFIG_FILE
elif Path.exists(USER_CONFIG_FILE):
    CONFIG_FILE = USER_CONFIG_FILE
elif Path.exists(CURRENT_DIR_CONFIG):
    CONFIG_FILE = CURRENT_DIR_CONFIG
else:
    CONFIG_FILE = None


# ---------------------------------------------------------------------------------------
# Verify configuration file.
# ---------------------------------------------------------------------------------------
def verify_config_file(config_file: ConfigObj) -> bool:
    """Verifica si el archivo de configuración es correcto."""
    if isinstance(config_file, ConfigObj):
        if config_file.get("SECRET_KEY") and config_file.get("DATABASE_URL"):
            return True
        else:
            log.warning("Archivo de configuración incorrecto.")
            return False
    else:
        return False


# ---------------------------------------------------------------------------------------
# Load and verify configuration from file.
# ---------------------------------------------------------------------------------------
if CONFIG_FILE:
    log.trace("Archivo de configuración detectado.")
    CONFIG_FILE_PARSER: Union[ConfigObj, None] = ConfigObj(CONFIG_FILE)
    log.trace("Archivo de configuración leido correctamente.")

else:
    CONFIG_FILE_PARSER = None

CONFIG_FROM_FILE: Union[ConfigObj, bool]

if verify_config_file(CONFIG_FILE_PARSER):
    log.trace("Archivo de configuración validado.")
    CONFIG_FROM_FILE = CONFIG_FILE_PARSER
else:
    CONFIG_FROM_FILE = False
