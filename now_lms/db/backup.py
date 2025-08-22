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

"""Database backup functionality for NOW LMS."""

import os

# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------
from flask import current_app
from sqlalchemy.engine import make_url

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms.config import DIRECTORIO_ARCHIVOS_PRIVADOS, DIRECTORIO_PRINCICIPAL

BACKUP_DIR = os.path.join(DIRECTORIO_ARCHIVOS_PRIVADOS, "database", "backup")

with current_app.app_context():
    DBURI = str(current_app.config.get("SQLALCHEMY_DATABASE_URI"))
    DBURL = make_url(DBURI)
    DBNAME = DBURL.database
    DBUSER = DBURL.username
    DBPASS = DBURL.password
    DBHOST = DBURL.host
    DBPORT = str(DBURL.port)
    DBENGINE = DBURL.drivername


def db_backup():
    """Genera un respaldo de la base de datos."""
    TIME_STAMP = datetime.now().strftime("%Y%m%d-%H%M%S")
    BACKUP_FILE = os.path.join(BACKUP_DIR, f"nowlmsbackup_{TIME_STAMP}.sql")
    BACKUP_FILE = Path(BACKUP_FILE)

    os.makedirs(BACKUP_DIR, exist_ok=True)

    if not BACKUP_FILE.exists():
        BACKUP_FILE.touch()

    with current_app.app_context():
        if "sqlite" in DBURI:
            ARCHIVO_ORIGEN = Path(str(DIRECTORIO_PRINCICIPAL) + "/now_lms.db")
            shutil.copy2(ARCHIVO_ORIGEN, BACKUP_FILE)
        elif "postgresql" in DBURI:
            os.environ["PGPASSWORD"] = DBPASS
            subprocess.run(
                ["pg_dump", "-h", DBHOST, "-p", DBPORT, "-U", DBUSER, "-F", "c", "-b", "-v", "-f", BACKUP_FILE, DBNAME]
            )
            os.environ["PGPASSWORD"] = ""
        elif "mysql" in DBURI:
            with BACKUP_FILE.open("w", encoding="utf-8") as f:
                subprocess.run(
                    ["mysqldump", "-h", DBHOST, "-P", DBPORT, "-u", DBUSER, f"--password={DBPASS}", DBNAME],
                    stdout=f,
                )


def _restaurar_postgresql(backup_sql_file):
    comando = [
        "psql",
        f"--host={DBHOST}",
        f"--port={DBPORT or 5432}",
        f"--username={DBUSER}",
        f"--dbname={DBNAME}",
        "-f",
        backup_sql_file,
    ]

    os.environ["PGPASSWORD"] = DBPASS

    print(f"Ejecutando: {' '.join(comando)}")

    resultado = subprocess.run(
        comando,
    )

    os.environ["PGPASSWORD"] = ""

    if resultado.returncode != 0:
        raise RuntimeError("Error al restaurar la base de datos PostgreSQL con psql")


def _restaurar_mysql(backup_sql_file):
    comando = [
        "mysql",
        f"-h{DBHOST}",
        f"-P{DBPORT or 3306}",
        f"-u{DBUSER}",
        f"-p{DBPASS}",
        DBNAME,
    ]

    print(f"Ejecutando: {' '.join(comando[:-1])} [password oculto] {comando[-1]}")

    with open(backup_sql_file, "rb") as sql_file:
        resultado = subprocess.run(comando, stdin=sql_file)

    if resultado.returncode != 0:
        raise RuntimeError("Error al restaurar la base de datos MySQL con mysql")


def _restaurar_sqlite(backup_sql_file):

    ARCHIVO_DESTINO = Path(str(DIRECTORIO_PRINCICIPAL) + "/now_lms.db")
    shutil.copy2(backup_sql_file, ARCHIVO_DESTINO)


def db_backup_restore(backup_sql_file):
    """Restaura la base de datos desde un respaldo."""
    with current_app.app_context():
        if "postgresql" in DBURI:
            _restaurar_postgresql(backup_sql_file)
        elif "mysql" in DBURI:
            _restaurar_mysql(backup_sql_file)
        elif "sqlite" in DBURI:
            _restaurar_sqlite(backup_sql_file)
