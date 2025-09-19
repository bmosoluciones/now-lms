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
#


from __future__ import annotations

# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------
from pathlib import Path

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms.config import DIRECTORIO_ARCHIVOS_PUBLICOS

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------


def get_current_course_logo(course_code: str) -> str | None:
    """Return the name of the logo file for the current course."""
    course_dir = Path(str(str(DIRECTORIO_ARCHIVOS_PUBLICOS) + "/images/" + course_code))
    logo_files = [f for f in course_dir.iterdir() if f.is_file() and f.stem == "logo"]

    try:
        logo_file = logo_files[0]
        return logo_file.name
    except (FileNotFoundError, IndexError):
        return None


def get_site_logo() -> str | None:
    """Return the name of the logo file of the site."""
    course_dir = Path(str(str(DIRECTORIO_ARCHIVOS_PUBLICOS) + "/images/"))
    logo_files = [f for f in course_dir.iterdir() if f.is_file() and f.stem == "logotipo"]
    try:
        logo_file = logo_files[0]
        return logo_file.name
    except IndexError:
        return None


def get_site_favicon() -> str | None:
    """Return the name of the logo file of the site."""
    course_dir = Path(str(str(DIRECTORIO_ARCHIVOS_PUBLICOS) + "/images/"))
    logo_files = [f for f in course_dir.iterdir() if f.is_file() and f.stem == "favicon"]
    try:
        logo_file = logo_files[0]
        return logo_file.name
    except IndexError:
        return None


def logo_personalizado() -> bool:
    """Check if custom logo is enabled."""
    from now_lms.db import Style, database

    try:
        style = database.session.execute(database.select(Style)).first()
        if style:
            return style[0].custom_logo
        return False
    except Exception:
        return False


def favicon_personalizado() -> bool:
    """Check if custom favicon is enabled."""
    from now_lms.db import Style, database

    try:
        style = database.session.execute(database.select(Style)).first()
        if style:
            return style[0].custom_favicon
        return False
    except Exception:
        return False
