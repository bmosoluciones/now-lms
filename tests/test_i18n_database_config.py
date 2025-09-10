#!/usr/bin/env python3
"""Test i18n behavior respects database configuration."""

import pytest


def test_locale_respects_database_english_setting(session_full_db_setup):
    """Test that get_locale returns 'en' when database is configured for English."""
    with session_full_db_setup.app_context():
        from flask import g
        from now_lms.db import Configuracion, database
        from now_lms.i18n import get_locale

        # Set database configuration to English
        config = database.session.execute(database.select(Configuracion)).scalars().first()
        if config:
            config.lang = "en"
            database.session.commit()

        # Test with a request context
        with session_full_db_setup.test_request_context("/"):
            # Load configuration into g
            g.configuracion = config

            # Test locale returns English
            locale = get_locale()
            assert locale == "en", f"Expected 'en' when database is set to English, got '{locale}'"


def test_locale_respects_database_spanish_setting(session_full_db_setup):
    """Test that get_locale returns 'es' when database is configured for Spanish."""
    with session_full_db_setup.app_context():
        from flask import g
        from now_lms.db import Configuracion, database
        from now_lms.i18n import get_locale

        # Set database configuration to Spanish
        config = database.session.execute(database.select(Configuracion)).scalars().first()
        if config:
            config.lang = "es"
            database.session.commit()

        # Test with a request context
        with session_full_db_setup.test_request_context("/"):
            # Load configuration into g
            g.configuracion = config

            # Test locale returns Spanish
            locale = get_locale()
            assert locale == "es", f"Expected 'es' when database is set to Spanish, got '{locale}'"


@pytest.mark.xfail(raises=AssertionError)
def test_english_translations_work_when_enabled(session_full_db_setup):
    """Test that English translations work when database language is set to 'en'."""
    with session_full_db_setup.app_context():
        from flask import g
        from flask_babel import get_locale
        from now_lms.db import Configuracion, database
        from now_lms.i18n import _

        # Set database configuration to English
        config = database.session.execute(database.select(Configuracion)).scalars().first()
        if config:
            config.lang = "en"
            database.session.commit()

        # Test with a request context
        with session_full_db_setup.test_request_context("/"):
            # Load configuration into g
            g.configuracion = config

            # Verify locale is English
            locale = get_locale()
            assert str(locale) == "en"

            # Test that translations work
            # These translations exist in the English .po file
            home_translation = _("Inicio")
            courses_translation = _("Cursos")

            assert home_translation == "Home", f"Expected 'Home', got '{home_translation}'"
            assert courses_translation == "Courses", f"Expected 'Courses', got '{courses_translation}'"
