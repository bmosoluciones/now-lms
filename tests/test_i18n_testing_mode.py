#!/usr/bin/env python3
"""Test i18n behavior in testing vs production mode."""


def test_testing_mode_detection():
    """Test that testing mode is correctly detected during test runs."""
    from now_lms.i18n import is_testing_mode

    # Since we're running this as a test, it should detect testing mode
    result = is_testing_mode()
    assert result is True, "Should detect testing mode when running tests"


def test_locale_returns_spanish_in_testing_mode():
    """Test that get_locale returns Spanish in testing mode."""
    from now_lms.i18n import get_locale

    locale = get_locale()
    assert locale == "es", f"Expected 'es' in testing mode, got '{locale}'"


def test_configuration_fallback_spanish_in_testing_mode(session_basic_db_setup):
    """Test that configuration fallback uses Spanish in testing mode."""
    with session_basic_db_setup.app_context():
        from now_lms.cache import cache
        from now_lms.i18n import get_configuracion

        # Clear cache to force fallback behavior
        cache.clear()

        # This should use the fallback logic since it's testing mode
        config = get_configuracion()
        assert config.lang == "es", f"Expected 'es' in testing mode fallback, got '{config.lang}'"


def test_default_configuration_language_in_testing(session_basic_db_setup):
    """Test that crear_configuracion_predeterminada sets Spanish in testing mode."""
    with session_basic_db_setup.app_context():
        from now_lms.db import Configuracion, database
        from now_lms.db.tools import crear_configuracion_predeterminada

        # Clear any existing configuration
        database.session.execute(database.delete(Configuracion))
        database.session.commit()

        # Create default configuration - should use Spanish in testing mode
        crear_configuracion_predeterminada()

        # Verify the created configuration uses Spanish
        config = database.session.execute(database.select(Configuracion)).scalars().first()
        assert config is not None, "Configuration should be created"
        assert config.lang == "es", f"Expected 'es' in testing mode, got '{config.lang}'"
        assert config.time_zone == "UTC", f"Expected 'UTC' timezone, got '{config.time_zone}'"
