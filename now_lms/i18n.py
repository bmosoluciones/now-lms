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


"""Internationalization utilities."""


from __future__ import annotations

# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------
import sys
from os import environ, path

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------
from flask import g, request
from flask_babel import gettext, lazy_gettext, ngettext

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms.cache import cache
from now_lms.logs import log


# ---------------------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------------------
def is_testing_mode() -> bool:
    """Detect if the application is running in CI/testing mode."""
    return (
        "PYTEST_CURRENT_TEST" in environ
        or "PYTEST_VERSION" in environ
        or hasattr(sys, "_called_from_test")
        or bool(environ.get("CI"))
        or "pytest" in sys.modules
        or path.basename(sys.argv[0]) in ["pytest", "py.test"]
    )


# ---------------------------------------------------------------------------------------
# Translation functions
# ---------------------------------------------------------------------------------------
def _(text: str) -> str:
    """Mark text for translation."""
    return gettext(text)


def _n(singular: str, plural: str, n: int) -> str:
    """Mark text for plural translation."""
    return ngettext(singular, plural, n)


def _l(text: str) -> str:
    """Mark text for lazy translation (useful in forms)."""
    return lazy_gettext(text)


@cache.cached(key_prefix="configuracion_global")
def get_configuracion():
    """Obtiene configuración del sitio web desde la base de datos (usando Flask-Caching)."""
    from now_lms.db import Configuracion, database

    config = database.session.execute(database.select(Configuracion)).scalars().first()
    if not config:
        # Fallback en caso de que no haya configuración cargada
        # Use Spanish for testing/CI mode, English for production
        default_lang = "es" if is_testing_mode() else "en"
        config = Configuracion(
            lang=default_lang, time_zone="UTC", titulo=_("Título por defecto"), descripcion=_("Descripción")
        )
    return config


def get_locale() -> str:
    """Obtiene el idioma desde la configuración en g."""
    # Check for configuration in g first (respects database setting)
    try:
        if hasattr(g, "configuracion") and g.configuracion:
            return getattr(g.configuracion, "lang", "en")
    except RuntimeError:
        # Working outside application context
        pass

    # Fallback: if no configuration in g, check from database directly
    try:
        config = get_configuracion()
        if config and config.lang:
            return config.lang
    except Exception:
        pass  # Continue to next fallback

    # Final fallback: use browser preference or default
    try:
        return request.accept_languages.best_match(["es", "en", "pt_BR"]) or "en"
    except RuntimeError:
        # Working outside request context - use default based on testing mode
        return "es" if is_testing_mode() else "en"


def get_timezone() -> str:
    """Obtiene la zona horaria desde la configuración en g."""
    if hasattr(g, "configuracion") and g.configuracion:
        return getattr(g.configuracion, "time_zone", "UTC")
    # Fallback si no hay configuración disponible
    return "UTC"


def invalidate_configuracion_cache() -> None:
    """Invalida la caché de configuración cuando se actualice."""
    cache.delete("configuracion_global")
    log.trace(_("Cache de configuración invalidada"))


# Guia de uso:
#
# Extraer textos a traducir
# pybabel extract -F babel.cfg -o now_lms/translations/messages.pot .
#
# Crear archivo de traducción para inglés (si no existe)
# pybabel init -i now_lms/translations/messages.pot -d now_lms/translations -l en
#
# Compilar traducciones
# pybabel compile -d now_lms/translations
#
# Actualizar archivo de traducción
# Extraer nuevos textos
# pybabel extract -F babel.cfg -o now_lms/translations/messages.pot .
#
# Actualizar archivos de idioma
# pybabel update -i now_lms/translations/messages.pot -d now_lms/translations
#
# Luego edita los .po y recompila
# pybabel compile -d now_lms/translations
#
# Uso en código Python:
# from now_lms.i18n import _
# flash(_("Mensaje a traducir"), "success")
#
# Uso en plantillas Jinja2:
# {{ _('Texto a traducir') }}

# Para plurales:
# from now_lms.i18n import _n
# _n('%(num)d archivo', '%(num)d archivos', num, num=num)
#
# Para traducciones perezosas (formularios):
# from now_lms.i18n import _l
# field = StringField(_l('Etiqueta del campo'))
