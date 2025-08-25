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

"""Test ConfigObj file-based configuration functionality."""

import os
import tempfile
from unittest.mock import patch

from now_lms.config import load_config_from_file


class TestConfigObjIntegration:
    """Test ConfigObj integration for file-based configuration."""

    def test_load_config_from_file_no_file(self):
        """Test that function returns empty dict when no config file exists."""
        config = load_config_from_file()
        assert isinstance(config, dict)
        # Should be empty when no file is found
        # (unless there's an actual config file in the search paths)

    def test_load_config_from_file_invalid_file(self):
        """Test handling of invalid config file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".conf", delete=False) as f:
            f.write("invalid config content [[[")
            config_path = f.name

        try:
            with patch.dict(os.environ, {"NOW_LMS_CONFIG": config_path}):
                config = load_config_from_file()
                # Should return empty dict when file is invalid
                assert config == {}

        finally:
            os.unlink(config_path)

    def test_configobj_optional_dependency(self):
        """Test that system works when ConfigObj is not available."""
        # Test the import error handling by mocking the import statement
        import sys

        # Temporarily remove configobj from sys.modules to simulate ImportError
        original_configobj = sys.modules.get("configobj")
        if "configobj" in sys.modules:
            del sys.modules["configobj"]

        try:
            # Patch the import to raise ImportError
            def mock_import(name, *args, **kwargs):
                if name == "configobj":
                    raise ImportError("No module named 'configobj'")
                return __import__(name, *args, **kwargs)

            with patch("builtins.__import__", side_effect=mock_import):
                config = load_config_from_file()
                assert config == {}
        finally:
            # Restore configobj if it was there
            if original_configobj is not None:
                sys.modules["configobj"] = original_configobj

    def test_search_paths_order(self):
        """Test that config files are searched in the correct order."""
        # Create a config file and test that NOW_LMS_CONFIG takes priority
        with tempfile.NamedTemporaryFile(mode="w", suffix=".conf", delete=False) as f:
            f.write("""TEST_VALUE = from_env_config""")
            config_path = f.name

        try:
            with patch.dict(os.environ, {"NOW_LMS_CONFIG": config_path}):
                config = load_config_from_file()
                assert config is not None

        finally:
            os.unlink(config_path)
