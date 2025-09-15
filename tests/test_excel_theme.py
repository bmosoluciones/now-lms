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

"""Tests specifically for the Excel theme implementation."""

import os
import pytest
from pathlib import Path

from now_lms.themes import list_themes


def test_excel_theme_exists():
    """Test that the Excel theme is properly listed."""
    themes = list_themes()
    assert 'excel' in themes


def test_excel_theme_files_exist():
    """Test that all required Excel theme files exist."""
    # Get the directory path for the Excel theme
    excel_theme_path = Path(__file__).parent.parent / 'now_lms' / 'templates' / 'themes' / 'excel'
    
    # Check required template files
    required_files = [
        'README.md',
        'base.j2',
        'header.j2',
        'local_style.j2',
        'navbar.j2',
        'notify.j2',
        'pagination.j2',
        'js.j2'
    ]
    
    for file_name in required_files:
        file_path = excel_theme_path / file_name
        assert file_path.exists(), f"Required file {file_name} does not exist in Excel theme"


def test_excel_theme_static_files_exist():
    """Test that Excel theme static files exist."""
    excel_static_path = Path(__file__).parent.parent / 'now_lms' / 'static' / 'themes' / 'excel'
    
    # Check required static files
    required_static_files = [
        'theme.css',
        'theme.min.css'
    ]
    
    for file_name in required_static_files:
        file_path = excel_static_path / file_name
        assert file_path.exists(), f"Required static file {file_name} does not exist in Excel theme"


def test_excel_theme_home_override_exists():
    """Test that Excel theme has a home page override."""
    excel_overrides_path = Path(__file__).parent.parent / 'now_lms' / 'templates' / 'themes' / 'excel' / 'overrides'
    home_override_path = excel_overrides_path / 'home.j2'
    
    assert home_override_path.exists(), "Excel theme home override does not exist"


def test_excel_theme_templates_have_translations():
    """Test that Excel theme templates contain translation markers."""
    excel_theme_path = Path(__file__).parent.parent / 'now_lms' / 'templates' / 'themes' / 'excel'
    
    # Check that key templates contain translation markers
    templates_to_check = [
        'navbar.j2',
        'overrides/home.j2'
    ]
    
    for template_name in templates_to_check:
        template_path = excel_theme_path / template_name
        if template_path.exists():
            content = template_path.read_text(encoding='utf-8')
            # Check for Flask-Babel translation markers
            assert '_(' in content, f"Template {template_name} should contain translation markers _('text')"


def test_excel_theme_spanish_content():
    """Test that Excel theme contains Spanish content as specified."""
    excel_home_path = Path(__file__).parent.parent / 'now_lms' / 'templates' / 'themes' / 'excel' / 'overrides' / 'home.j2'
    
    if excel_home_path.exists():
        content = excel_home_path.read_text(encoding='utf-8')
        
        # Check for key Spanish phrases from the mockup
        expected_phrases = [
            'MAESTRO DE EXCEL EN LÍNEA',
            'CURSOS QUE TRANSFORMAN TUS DATOS',
            'EXPLORAR CURSOS',
            'CURSOS DESTACADOS'
        ]
        
        for phrase in expected_phrases:
            assert phrase in content, f"Expected Spanish phrase '{phrase}' not found in home template"


def test_excel_theme_responsive_classes():
    """Test that Excel theme contains responsive CSS classes."""
    excel_css_path = Path(__file__).parent.parent / 'now_lms' / 'static' / 'themes' / 'excel' / 'theme.css'
    excel_home_path = Path(__file__).parent.parent / 'now_lms' / 'templates' / 'themes' / 'excel' / 'overrides' / 'home.j2'
    
    if excel_css_path.exists():
        css_content = excel_css_path.read_text(encoding='utf-8')
        
        # Check for responsive CSS features
        responsive_css_indicators = [
            '@media',
            'max-width'
        ]
        
        for indicator in responsive_css_indicators:
            assert indicator in css_content, f"Responsive CSS indicator '{indicator}' not found in CSS"
    
    if excel_home_path.exists():
        html_content = excel_home_path.read_text(encoding='utf-8')
        
        # Check for Bootstrap responsive classes in templates
        responsive_html_indicators = [
            'col-12',
            'col-md-',
            'col-lg-'
        ]
        
        for indicator in responsive_html_indicators:
            assert indicator in html_content, f"Responsive HTML indicator '{indicator}' not found in template"


def test_excel_theme_green_color_scheme():
    """Test that Excel theme uses the appropriate green color scheme."""
    excel_css_path = Path(__file__).parent.parent / 'now_lms' / 'static' / 'themes' / 'excel' / 'theme.css'
    
    if excel_css_path.exists():
        content = excel_css_path.read_text(encoding='utf-8')
        
        # Check for Excel green color scheme
        expected_colors = [
            '#217346',  # Excel green
            '--excel-primary',
            '--excel-primary-light',
            '--excel-primary-dark'
        ]
        
        for color in expected_colors:
            assert color in content, f"Expected Excel color '{color}' not found in CSS"