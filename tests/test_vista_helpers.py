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

"""Tests for vista helper functions."""

from unittest.mock import patch, MagicMock

from now_lms.vistas._helpers import get_current_course_logo, get_site_logo, get_site_favicon


class TestVistaHelpers:
    """Test class for vista helper functions."""

    @patch("now_lms.vistas._helpers.Path")
    def test_get_current_course_logo_found(self, mock_path):
        """Test get_current_course_logo when logo file exists."""
        # Mock a directory with a logo file
        mock_logo_file = MagicMock()
        mock_logo_file.is_file.return_value = True
        mock_logo_file.stem = "logo"
        mock_logo_file.name = "logo.png"

        mock_course_dir = MagicMock()
        mock_course_dir.iterdir.return_value = [mock_logo_file]

        mock_path.return_value = mock_course_dir

        result = get_current_course_logo("test-course")

        assert result == "logo.png"
        mock_path.assert_called_once()

    @patch("now_lms.vistas._helpers.Path")
    def test_get_current_course_logo_not_found(self, mock_path):
        """Test get_current_course_logo when no logo file exists."""
        # Mock a directory with no logo files
        mock_other_file = MagicMock()
        mock_other_file.is_file.return_value = True
        mock_other_file.stem = "other"

        mock_course_dir = MagicMock()
        mock_course_dir.iterdir.return_value = [mock_other_file]

        mock_path.return_value = mock_course_dir

        result = get_current_course_logo("test-course")

        assert result is None

    @patch("now_lms.vistas._helpers.Path")
    def test_get_current_course_logo_file_not_found_exception(self, mock_path):
        """Test get_current_course_logo when accessing logo file raises FileNotFoundError."""
        # Mock a logo file that raises FileNotFoundError when accessing .name
        mock_logo_file = MagicMock()
        mock_logo_file.is_file.return_value = True
        mock_logo_file.stem = "logo"

        # Configure the .name property to raise FileNotFoundError when accessed
        type(mock_logo_file).name = property(lambda self: (_ for _ in ()).throw(FileNotFoundError("File not found")))

        mock_course_dir = MagicMock()
        mock_course_dir.iterdir.return_value = [mock_logo_file]

        mock_path.return_value = mock_course_dir

        result = get_current_course_logo("test-course")

        assert result is None

    @patch("now_lms.vistas._helpers.Path")
    def test_get_current_course_logo_index_error(self, mock_path):
        """Test get_current_course_logo when no logo files match."""
        mock_course_dir = MagicMock()
        mock_course_dir.iterdir.return_value = []  # Empty directory

        mock_path.return_value = mock_course_dir

        result = get_current_course_logo("test-course")

        assert result is None

    @patch("now_lms.vistas._helpers.Path")
    def test_get_site_logo_found(self, mock_path):
        """Test get_site_logo when logotipo file exists."""
        # Mock a directory with a logotipo file
        mock_logo_file = MagicMock()
        mock_logo_file.is_file.return_value = True
        mock_logo_file.stem = "logotipo"
        mock_logo_file.name = "logotipo.png"

        mock_site_dir = MagicMock()
        mock_site_dir.iterdir.return_value = [mock_logo_file]

        mock_path.return_value = mock_site_dir

        result = get_site_logo()

        assert result == "logotipo.png"

    @patch("now_lms.vistas._helpers.Path")
    def test_get_site_logo_not_found(self, mock_path):
        """Test get_site_logo when no logotipo file exists."""
        # Mock a directory with no logotipo files
        mock_other_file = MagicMock()
        mock_other_file.is_file.return_value = True
        mock_other_file.stem = "other"

        mock_site_dir = MagicMock()
        mock_site_dir.iterdir.return_value = [mock_other_file]

        mock_path.return_value = mock_site_dir

        result = get_site_logo()

        assert result is None

    @patch("now_lms.vistas._helpers.Path")
    def test_get_site_logo_index_error(self, mock_path):
        """Test get_site_logo when no files match."""
        mock_site_dir = MagicMock()
        mock_site_dir.iterdir.return_value = []  # Empty directory

        mock_path.return_value = mock_site_dir

        result = get_site_logo()

        assert result is None

    @patch("now_lms.vistas._helpers.Path")
    def test_get_current_course_logo_multiple_logo_files(self, mock_path):
        """Test get_current_course_logo when multiple logo files exist."""
        # Mock a directory with multiple logo files (should return first one)
        mock_logo_file1 = MagicMock()
        mock_logo_file1.is_file.return_value = True
        mock_logo_file1.stem = "logo"
        mock_logo_file1.name = "logo.png"

        mock_logo_file2 = MagicMock()
        mock_logo_file2.is_file.return_value = True
        mock_logo_file2.stem = "logo"
        mock_logo_file2.name = "logo.jpg"

        mock_course_dir = MagicMock()
        mock_course_dir.iterdir.return_value = [mock_logo_file1, mock_logo_file2]

        mock_path.return_value = mock_course_dir

        result = get_current_course_logo("test-course")

        assert result == "logo.png"

    @patch("now_lms.vistas._helpers.Path")
    def test_get_site_logo_multiple_logotipo_files(self, mock_path):
        """Test get_site_logo when multiple logotipo files exist."""
        # Mock a directory with multiple logotipo files (should return first one)
        mock_logo_file1 = MagicMock()
        mock_logo_file1.is_file.return_value = True
        mock_logo_file1.stem = "logotipo"
        mock_logo_file1.name = "logotipo.svg"

        mock_logo_file2 = MagicMock()
        mock_logo_file2.is_file.return_value = True
        mock_logo_file2.stem = "logotipo"
        mock_logo_file2.name = "logotipo.png"

        mock_site_dir = MagicMock()
        mock_site_dir.iterdir.return_value = [mock_logo_file1, mock_logo_file2]

        mock_path.return_value = mock_site_dir

        result = get_site_logo()

        assert result == "logotipo.svg"

    @patch("now_lms.vistas._helpers.Path")
    def test_get_site_favicon_found(self, mock_path):
        """Test get_site_favicon when favicon file exists."""
        # Mock a directory with a favicon file
        mock_favicon_file = MagicMock()
        mock_favicon_file.is_file.return_value = True
        mock_favicon_file.stem = "favicon"
        mock_favicon_file.name = "favicon.ico"

        mock_site_dir = MagicMock()
        mock_site_dir.iterdir.return_value = [mock_favicon_file]

        mock_path.return_value = mock_site_dir

        result = get_site_favicon()

        assert result == "favicon.ico"
        mock_path.assert_called_once()

    @patch("now_lms.vistas._helpers.Path")
    def test_get_site_favicon_not_found(self, mock_path):
        """Test get_site_favicon when no favicon file exists."""
        # Mock a directory with no favicon files
        mock_other_file = MagicMock()
        mock_other_file.is_file.return_value = True
        mock_other_file.stem = "other"
        mock_other_file.name = "other.png"

        mock_site_dir = MagicMock()
        mock_site_dir.iterdir.return_value = [mock_other_file]

        mock_path.return_value = mock_site_dir

        result = get_site_favicon()

        assert result is None

    @patch("now_lms.vistas._helpers.Path")
    def test_get_site_favicon_multiple_files(self, mock_path):
        """Test get_site_favicon when multiple favicon files exist."""
        # Mock a directory with multiple favicon files (should return first one)
        mock_favicon_file1 = MagicMock()
        mock_favicon_file1.is_file.return_value = True
        mock_favicon_file1.stem = "favicon"
        mock_favicon_file1.name = "favicon.ico"

        mock_favicon_file2 = MagicMock()
        mock_favicon_file2.is_file.return_value = True
        mock_favicon_file2.stem = "favicon"
        mock_favicon_file2.name = "favicon.png"

        mock_site_dir = MagicMock()
        mock_site_dir.iterdir.return_value = [mock_favicon_file1, mock_favicon_file2]

        mock_path.return_value = mock_site_dir

        result = get_site_favicon()

        assert result == "favicon.ico"
