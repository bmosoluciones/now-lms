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
from os import path
from pathlib import Path
from typing import Union

# ---------------------------------------------------------------------------------------
# Librerias de terceros
# ---------------------------------------------------------------------------------------
from configobj import ConfigObj

# ---------------------------------------------------------------------------------------
# Recursos locales
# ---------------------------------------------------------------------------------------


# ---------------------------------------------------------------------------------------
# Configuration can be loaded from a init like life.
# ---------------------------------------------------------------------------------------
BASE_FILE: str = "nowlms.conf"
# Default configuration file is /etc/nowlms.conf
GLOBAL_CONFIG_FILE: Path = Path(path.join("/etc/", BASE_FILE))
# Configuration file can be placed in $home/.config/nowlms.conf
USER_CONFIG_FILE: Path = Path(path.join(Path.home(), ".config", BASE_FILE))


if Path.exists(GLOBAL_CONFIG_FILE):
    CONFIG_FILE: Union[str, Path, None] = GLOBAL_CONFIG_FILE
elif Path.exists(USER_CONFIG_FILE):
    CONFIG_FILE = USER_CONFIG_FILE
else:
    CONFIG_FILE = None

if CONFIG_FILE:
    CONFIG_FILE_PARSER: Union[ConfigObj, None] = ConfigObj(CONFIG_FILE)
else:
    CONFIG_FILE_PARSER = None


CONFIG_FROM_FILE: Union[ConfigObj, dict, None]

if CONFIG_FROM_FILE := CONFIG_FILE_PARSER:
    pass
else:
    CONFIG_FROM_FILE = None
