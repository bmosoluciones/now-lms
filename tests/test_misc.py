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


"""Tests for misc utility functions."""

from collections import OrderedDict

from now_lms.misc import (
    concatenar_parametros_a_url,
    markdown_to_clean_html,
    sanitize_slide_content,
    TIPOS_DE_USUARIO,
    ICONOS_RECURSOS,
    HTML_TAGS,
)


class TestMiscUtilities:
    """Test class for miscellaneous utility functions."""

    def test_concatenar_parametros_a_url_with_existing_params(self):
        """Test URL parameter concatenation with existing parameters."""
        params = OrderedDict([("page", "1"), ("size", "10")])
        result = concatenar_parametros_a_url(params, "sort", "name", "?")

        assert "page=1" in result
        assert "size=10" in result
        assert "sort=name" in result
        assert result.startswith("?")

    def test_concatenar_parametros_a_url_no_existing_params(self):
        """Test URL parameter concatenation without existing parameters."""
        result = concatenar_parametros_a_url(None, "filter", "active", "?")

        assert result == "?filter=active"

    def test_concatenar_parametros_a_url_empty_params(self):
        """Test URL parameter concatenation with empty parameters."""
        result = concatenar_parametros_a_url(None, None, None, "")

        assert result == ""

    def test_markdown_to_clean_html_basic(self):
        """Test basic markdown to HTML conversion."""
        markdown_text = "**Bold text** and *italic text*"
        result = markdown_to_clean_html(markdown_text)

        assert "<strong>" in result
        assert "<em>" in result
        assert "Bold text" in result
        assert "italic text" in result

    def test_markdown_to_clean_html_with_links(self):
        """Test markdown to HTML conversion with links."""
        markdown_text = "[Example](https://example.com)"
        result = markdown_to_clean_html(markdown_text)

        assert '<a href="https://example.com"' in result
        assert "Example" in result

    def test_sanitize_slide_content_basic(self):
        """Test basic slide content sanitization."""
        html_content = "<p>Hello <b>world</b></p><script>alert('xss')</script>"
        result = sanitize_slide_content(html_content)

        assert "<p>Hello <b>world</b></p>" in result
        assert "<script>" not in result
        # The text content may remain, but the script tags are removed

    def test_sanitize_slide_content_allowed_tags(self):
        """Test slide content sanitization with allowed tags."""
        html_content = "<h1>Title</h1><p>Content with <a href='#'>link</a></p>"
        result = sanitize_slide_content(html_content)

        assert "<h1>Title</h1>" in result
        assert '<a href="#">link</a>' in result

    def test_constants_are_defined(self):
        """Test that important constants are properly defined."""
        assert isinstance(TIPOS_DE_USUARIO, list)
        assert "admin" in TIPOS_DE_USUARIO
        assert "user" in TIPOS_DE_USUARIO
        assert "instructor" in TIPOS_DE_USUARIO
        assert "moderator" in TIPOS_DE_USUARIO

        assert isinstance(ICONOS_RECURSOS, dict)
        assert "pdf" in ICONOS_RECURSOS
        assert "html" in ICONOS_RECURSOS

        assert isinstance(HTML_TAGS, list)
        assert "p" in HTML_TAGS
        assert "div" in HTML_TAGS
        assert "a" in HTML_TAGS
