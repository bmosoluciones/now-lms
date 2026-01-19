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


def get_blog_post_cover_image(post_id: str) -> str | None:
    """Return the name of the cover image file for a blog post."""
    blog_dir = Path(str(str(DIRECTORIO_ARCHIVOS_PUBLICOS) + "/images/blog/" + post_id))
    try:
        if not blog_dir.exists():
            return None
        cover_files = [f for f in blog_dir.iterdir() if f.is_file() and f.stem == "cover"]
        if cover_files:
            return cover_files[0].name
        return None
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


def get_footer_pages():
    """Get static pages to be shown in the footer."""
    from now_lms.cache import cache
    from now_lms.db import StaticPage, database

    @cache.memoize(timeout=300)
    def _get_footer_pages():
        try:
            pages = (
                database.session.execute(
                    database.select(StaticPage)
                    .filter(StaticPage.is_active.is_(True), StaticPage.mostrar_en_footer.is_(True))
                    .order_by(StaticPage.title)
                )
                .scalars()
                .all()
            )
            return pages
        except Exception:
            return []

    return _get_footer_pages()


def get_footer_enlaces():
    """Get useful links to be shown in the footer."""
    from now_lms.cache import cache
    from now_lms.db import EnlacesUtiles, database

    @cache.memoize(timeout=300)
    def _get_footer_enlaces():
        try:
            enlaces = (
                database.session.execute(
                    database.select(EnlacesUtiles).filter(EnlacesUtiles.activo.is_(True)).order_by(EnlacesUtiles.orden)
                )
                .scalars()
                .all()
            )
            return enlaces
        except Exception:
            return []

    return _get_footer_enlaces()
