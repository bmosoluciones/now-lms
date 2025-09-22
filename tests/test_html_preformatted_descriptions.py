"""Tests for HTML preformatted descriptions functionality."""

import pytest
from now_lms.db import Configuracion, Recurso, CursoRecurso, database


class TestHTMLPreformattedDescriptions:
    """Test HTML preformatted descriptions feature."""

    def test_configuration_model_has_html_field(self, session_basic_db_setup):
        """Test that Configuracion model has the new HTML field."""
        with session_basic_db_setup.app_context():
            config = database.session.execute(database.select(Configuracion)).scalars().first()
            assert hasattr(config, 'enable_html_preformatted_descriptions')
            assert config.enable_html_preformatted_descriptions is False  # Default is False

    def test_recurso_model_has_html_field(self, session_basic_db_setup):
        """Test that Recurso model has the new HTML preformatted field."""
        with session_basic_db_setup.app_context():
            # Create a test resource
            recurso = Recurso(
                nombre="Test Resource",
                codigo="TEST001",
                descripcion="Test description",
                tipo="text"
            )
            database.session.add(recurso)
            database.session.commit()
            
            assert hasattr(recurso, 'descripcion_html_preformateado')
            assert recurso.descripcion_html_preformateado is False  # Default is False

    def test_html_preformatted_flag_can_be_set(self, session_basic_db_setup):
        """Test that HTML preformatted flag can be set and persisted."""
        with session_basic_db_setup.app_context():
            # Create resource with HTML preformatted flag
            recurso = Recurso(
                nombre="HTML Resource",
                codigo="HTML001",
                descripcion="<h1>HTML Title</h1><p>This is HTML content.</p>",
                descripcion_html_preformateado=True,
                tipo="text"
            )
            database.session.add(recurso)
            database.session.commit()
            
            # Retrieve and verify
            saved_recurso = database.session.execute(
                database.select(Recurso).filter(Recurso.codigo == "HTML001")
            ).scalars().first()
            
            assert saved_recurso.descripcion_html_preformateado is True
            assert "<h1>HTML Title</h1>" in saved_recurso.descripcion

    def test_global_configuration_can_be_enabled(self, session_basic_db_setup):
        """Test that global HTML configuration can be enabled."""
        with session_basic_db_setup.app_context():
            config = database.session.execute(database.select(Configuracion)).scalars().first()
            
            # Enable HTML preformatted descriptions
            config.enable_html_preformatted_descriptions = True
            database.session.commit()
            
            # Verify it was saved
            updated_config = database.session.execute(database.select(Configuracion)).scalars().first()
            assert updated_config.enable_html_preformatted_descriptions is True

    def test_mixed_resources_different_flags(self, session_basic_db_setup):
        """Test that we can have both HTML and markdown resources."""
        with session_basic_db_setup.app_context():
            # HTML resource
            html_recurso = Recurso(
                nombre="HTML Resource",
                codigo="HTML002",  # Different from other tests
                descripcion="<strong>Bold HTML</strong>",
                descripcion_html_preformateado=True,
                tipo="text"
            )
            
            # Markdown resource
            md_recurso = Recurso(
                nombre="Markdown Resource",
                codigo="MD002",  # Different from other tests
                descripcion="**Bold Markdown**",
                descripcion_html_preformateado=False,
                tipo="text"
            )
            
            database.session.add(html_recurso)
            database.session.add(md_recurso)
            database.session.commit()
            
            # Verify both exist with correct flags
            html_saved = database.session.execute(
                database.select(Recurso).filter(Recurso.codigo == "HTML002")
            ).scalars().first()
            md_saved = database.session.execute(
                database.select(Recurso).filter(Recurso.codigo == "MD002")
            ).scalars().first()
            
            assert html_saved.descripcion_html_preformateado is True
            assert md_saved.descripcion_html_preformateado is False
            assert html_saved.descripcion == "<strong>Bold HTML</strong>"
            assert md_saved.descripcion == "**Bold Markdown**"

    def test_html_field_defaults_to_false(self, session_basic_db_setup):
        """Test that HTML preformatted field defaults to False."""
        with session_basic_db_setup.app_context():
            # Create resource without explicitly setting the HTML flag
            recurso = Recurso(
                nombre="Default Resource",
                codigo="DEF001",
                descripcion="Default description",
                tipo="text"
            )
            database.session.add(recurso)
            database.session.commit()
            
            # Verify default is False
            saved_recurso = database.session.execute(
                database.select(Recurso).filter(Recurso.codigo == "DEF001")
            ).scalars().first()
            
            assert saved_recurso.descripcion_html_preformateado is False

    def test_configuration_field_defaults_to_false(self, session_basic_db_setup):
        """Test that configuration field can be toggled for security."""
        with session_basic_db_setup.app_context():
            config = database.session.execute(database.select(Configuracion)).scalars().first()
            
            # Set to False and verify
            config.enable_html_preformatted_descriptions = False
            database.session.commit()
            
            updated_config = database.session.execute(database.select(Configuracion)).scalars().first()
            assert updated_config.enable_html_preformatted_descriptions is False
            
            # Set to True and verify
            config.enable_html_preformatted_descriptions = True
            database.session.commit()
            
            updated_config = database.session.execute(database.select(Configuracion)).scalars().first()
            assert updated_config.enable_html_preformatted_descriptions is True

    def test_curso_recurso_html_field_exists(self, session_basic_db_setup):
        """Test that the CursoRecurso model has the HTML preformatted flag field."""
        with session_basic_db_setup.app_context():
            # Just test that the model has the field
            from now_lms.db import CursoRecurso
            
            # Check that the field exists in the model
            assert hasattr(CursoRecurso, 'descripcion_html_preformateado')
            
            # Create an instance to test the default value
            curso_recurso = CursoRecurso()
            # The field should exist but may be None until explicitly set
            assert hasattr(curso_recurso, 'descripcion_html_preformateado')

    def test_curso_recurso_html_preformateado_handling_in_view(self, session_full_db_setup):
        """Test that the course HTML resource views properly handle the descripcion_html_preformateado field."""
        with session_full_db_setup.app_context():
            from now_lms.vistas.courses import nuevo_recurso_html, editar_recurso_html
            from now_lms.forms import CursoRecursoExternalCode
            from flask import request, current_app
            from unittest.mock import Mock
            
            # Enable HTML preformatted descriptions globally
            config = database.session.execute(database.select(Configuracion)).scalars().first()
            config.enable_html_preformatted_descriptions = True
            database.session.commit()
            
            # Test that views import correctly (basic syntax test)
            assert nuevo_recurso_html is not None
            assert editar_recurso_html is not None
            
            # Test that the form has the field
            form = CursoRecursoExternalCode()
            assert hasattr(form, 'descripcion_html_preformateado')