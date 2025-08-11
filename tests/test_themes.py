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

"""Tests for themes functionality."""

from unittest.mock import patch, MagicMock

from now_lms.themes import (
    get_theme_path,
    get_home_template,
    get_course_list_template,
    get_program_list_template,
    get_course_view_template,
    get_program_view_template,
    list_themes,
)


class TestThemeFunctions:
    """Test class for theme utility functions."""

    @patch("now_lms.themes.get_current_theme")
    def test_get_theme_path_with_theme(self, mock_get_theme):
        """Test get_theme_path when a theme is set."""
        mock_get_theme.return_value = "test_theme"

        result = get_theme_path()

        assert "test_theme" in result
        assert "themes" in result

    @patch("now_lms.themes.get_current_theme")
    def test_get_theme_path_no_theme(self, mock_get_theme):
        """Test get_theme_path when no theme is set."""
        mock_get_theme.return_value = None

        result = get_theme_path()

        assert "now_lms" in result
        assert "themes" in result

    @patch("now_lms.themes.get_current_theme")
    @patch("now_lms.themes.Path")
    def test_get_home_template_with_override(self, mock_path, mock_get_theme):
        """Test get_home_template when theme override exists."""
        mock_get_theme.return_value = "test_theme"

        # Mock the Path object to simulate file exists
        mock_home_path = MagicMock()
        mock_home_path.exists.return_value = True
        mock_path.return_value = mock_home_path

        result = get_home_template()

        assert "test_theme" in result
        assert "overrides/home.j2" in result

    @patch("now_lms.themes.get_current_theme")
    @patch("now_lms.themes.Path")
    def test_get_home_template_no_override(self, mock_path, mock_get_theme):
        """Test get_home_template when no theme override exists."""
        mock_get_theme.return_value = "test_theme"

        # Mock the Path object to simulate file doesn't exist
        mock_home_path = MagicMock()
        mock_home_path.exists.return_value = False
        mock_path.return_value = mock_home_path

        result = get_home_template()

        assert result == "inicio/home.html"

    @patch("now_lms.themes.get_current_theme")
    @patch("now_lms.themes.Path")
    def test_get_course_list_template_with_override(self, mock_path, mock_get_theme):
        """Test get_course_list_template when theme override exists."""
        mock_get_theme.return_value = "test_theme"

        mock_course_list_path = MagicMock()
        mock_course_list_path.exists.return_value = True
        mock_path.return_value = mock_course_list_path

        result = get_course_list_template()

        assert "test_theme" in result
        assert "overrides/course_list.j2" in result

    @patch("now_lms.themes.get_current_theme")
    @patch("now_lms.themes.Path")
    def test_get_course_list_template_no_override(self, mock_path, mock_get_theme):
        """Test get_course_list_template when no theme override exists."""
        mock_get_theme.return_value = "test_theme"

        mock_course_list_path = MagicMock()
        mock_course_list_path.exists.return_value = False
        mock_path.return_value = mock_course_list_path

        result = get_course_list_template()

        assert result == "inicio/cursos.html"

    @patch("now_lms.themes.get_current_theme")
    @patch("now_lms.themes.Path")
    def test_get_program_list_template_with_override(self, mock_path, mock_get_theme):
        """Test get_program_list_template when theme override exists."""
        mock_get_theme.return_value = "test_theme"

        mock_program_list_path = MagicMock()
        mock_program_list_path.exists.return_value = True
        mock_path.return_value = mock_program_list_path

        result = get_program_list_template()

        assert "test_theme" in result
        assert "overrides/program_list.j2" in result

    @patch("now_lms.themes.get_current_theme")
    @patch("now_lms.themes.Path")
    def test_get_program_list_template_no_override(self, mock_path, mock_get_theme):
        """Test get_program_list_template when no theme override exists."""
        mock_get_theme.return_value = "test_theme"

        mock_program_list_path = MagicMock()
        mock_program_list_path.exists.return_value = False
        mock_path.return_value = mock_program_list_path

        result = get_program_list_template()

        assert result == "inicio/programas.html"

    @patch("now_lms.themes.get_current_theme")
    @patch("now_lms.themes.Path")
    def test_get_course_view_template_with_override(self, mock_path, mock_get_theme):
        """Test get_course_view_template when theme override exists."""
        mock_get_theme.return_value = "test_theme"

        mock_course_view_path = MagicMock()
        mock_course_view_path.exists.return_value = True
        mock_path.return_value = mock_course_view_path

        result = get_course_view_template()

        assert "test_theme" in result
        assert "overrides/course_view.j2" in result

    @patch("now_lms.themes.get_current_theme")
    @patch("now_lms.themes.Path")
    def test_get_course_view_template_no_override(self, mock_path, mock_get_theme):
        """Test get_course_view_template when no theme override exists."""
        mock_get_theme.return_value = "test_theme"

        mock_course_view_path = MagicMock()
        mock_course_view_path.exists.return_value = False
        mock_path.return_value = mock_course_view_path

        result = get_course_view_template()

        assert result == "learning/curso/curso.html"

    @patch("now_lms.themes.get_current_theme")
    @patch("now_lms.themes.Path")
    def test_get_program_view_template_with_override(self, mock_path, mock_get_theme):
        """Test get_program_view_template when theme override exists."""
        mock_get_theme.return_value = "test_theme"

        mock_program_view_path = MagicMock()
        mock_program_view_path.exists.return_value = True
        mock_path.return_value = mock_program_view_path

        result = get_program_view_template()

        assert "test_theme" in result
        assert "overrides/program_view.j2" in result

    @patch("now_lms.themes.get_current_theme")
    @patch("now_lms.themes.Path")
    def test_get_program_view_template_no_override(self, mock_path, mock_get_theme):
        """Test get_program_view_template when no theme override exists."""
        mock_get_theme.return_value = "test_theme"

        mock_program_view_path = MagicMock()
        mock_program_view_path.exists.return_value = False
        mock_path.return_value = mock_program_view_path

        result = get_program_view_template()

        assert result == "learning/programa.html"

    @patch("os.listdir")
    def test_list_themes(self, mock_listdir):
        """Test list_themes function."""
        mock_listdir.return_value = ["theme_c", "theme_a", "theme_b"]

        result = list_themes()

        assert isinstance(result, list)
        assert result == ["theme_a", "theme_b", "theme_c"]  # Should be sorted
        mock_listdir.assert_called_once()

    @patch("os.listdir")
    def test_list_themes_empty(self, mock_listdir):
        """Test list_themes function with empty directory."""
        mock_listdir.return_value = []

        result = list_themes()

        assert isinstance(result, list)
        assert len(result) == 0
