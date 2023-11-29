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

# ---------------------------------------------------------------------------------------
# Libreria estandar
# ---------------------------------------------------------------------------------------
from typing import TYPE_CHECKING, Union

# ---------------------------------------------------------------------------------------
# Librerias de terceros
# ---------------------------------------------------------------------------------------


# ---------------------------------------------------------------------------------------
# Recursos locales
# ---------------------------------------------------------------------------------------

if TYPE_CHECKING:
    from flask import Flask


def app_info(flask_app: "Flask") -> dict:
    from now_lms.cache import CTYPE

    DBURL: str
    DBENGINE: Union[str, None]

    if flask_app.config.get("SQLALCHEMY_DATABASE_URI"):
        DBURL = str(flask_app.config.get("SQLALCHEMY_DATABASE_URI"))
        if "postgresql" in DBURL:
            DBENGINE = "PostgreSQL"
        elif "mysql" in DBURL:
            DBENGINE = "MySQL"
        elif "mariadb" in DBURL:
            DBENGINE = "MariaDB"
        elif "sqlite" in DBURL:
            DBENGINE = "SQLite"
        else:
            DBENGINE = "Otra"
    else:
        DBENGINE = None

    return {"DBENGINE": DBENGINE, "CACHE": CTYPE}
