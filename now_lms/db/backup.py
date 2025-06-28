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
# Contributors:
# - William José Moreno Reyes

# ---------------------------------------------------------------------------------------
# Libreria estandar
# ---------------------------------------------------------------------------------------
import shutil
import subprocess
import os
from datetime import datetime
from path import Path

# ---------------------------------------------------------------------------------------
# Librerias de terceros
# ---------------------------------------------------------------------------------------
from flask import current_app
from sqlalchemy.engine import make_url

# ---------------------------------------------------------------------------------------
# Recursos locales
# ---------------------------------------------------------------------------------------
from now_lms.config import DIRECTORIO_ARCHIVOS_PRIVADOS

DIRECTORIO_PRINCICIPAL

BACKUP_DIR = os.path.join(DIRECTORIO_ARCHIVOS_PRIVADOS, "database", "backup")

with current_app.app_context():
    DBURI = str(current_app.config.get("SQLALCHEMY_DATABASE_URI"))
    DBURL = make_url(DBURI)
    DBNAME = DBURL.database
    DBUSER = DBURL.username
    DBPASS = DBURL.password
    DBHOST = DBURL.host
    DBPORT = DBURL.port
    DBENGINE = DBURL.drivername


def db_backup():
    """Genera un respaldo de la base de datos."""
    TIME_STAMP = datetime.now().strftime("%Y%m%d-%H%M%S")
    BACKUP_FILE = os.path.join(BACKUP_DIR, "temp", f"nowlmsbackup_{TIME_STAMP}.sql")
    BACKUP_FILE = Path(BACKUP_FILE)

    with current_app.app_context():
        if "sqlite" in DBURI:
            ARCHIVO_ORIGEN = Path(str(DIRECTORIO_PRINCICIPAL) + "/now_lms.db")
            shutil.copy2(ARCHIVO_ORIGEN, BACKUP_FILE)
        elif "postgresql" in DBURI:
            os.environ["PGPASSWORD"] = DBPASS
            subprocess.run(
                ["pg_dump", "-h", DBHOST, "-p", DBPORT, "-U", DBUSER, "-F", "c", "-b", "-v", "-f", BACKUP_FILE, DBNAME]
            )
        elif "mysql" in DBURI:
            output_file = BACKUP_FILE

            with open(output_file, "w") as f:
                subprocess.run(
                    ["mysqldump", "-h", DBHOST, "-P", DBPORT, "-u", DBUSER, f"--password={DBPASS}", DBNAME], stdout=f
                )
