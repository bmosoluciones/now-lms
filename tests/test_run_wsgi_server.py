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
"""Tests for run.py WSGI server selection via environment variable."""

from __future__ import annotations

# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------
import subprocess
import sys
from os import environ
from pathlib import Path


class TestRunPyWSGIServerSelection:
    """Test cases for run.py WSGI server selection via WSGI_SERVER environment variable."""

    def test_default_uses_waitress(self):
        """Test that run.py defaults to Waitress when WSGI_SERVER is not set."""
        # Clear WSGI_SERVER if it exists
        old_value = environ.get("WSGI_SERVER")
        if "WSGI_SERVER" in environ:
            del environ["WSGI_SERVER"]

        try:
            # Run run.py and capture output
            subprocess.run(
                [sys.executable, "run.py"],
                cwd=Path(__file__).parent.parent,
                capture_output=True,
                text=True,
                timeout=3,
            )
        except subprocess.TimeoutExpired as e:
            # Server starts and runs, so timeout is expected
            output = e.stdout.decode() if e.stdout else ""
            assert "Starting Waitress WSGI server" in output, "Should default to Waitress"
        finally:
            # Restore original value
            if old_value is not None:
                environ["WSGI_SERVER"] = old_value

    def test_wsgi_server_gunicorn(self):
        """Test that run.py uses Gunicorn when WSGI_SERVER=gunicorn."""
        old_value = environ.get("WSGI_SERVER")
        environ["WSGI_SERVER"] = "gunicorn"

        try:
            # Run run.py and capture output
            subprocess.run(
                [sys.executable, "run.py"],
                cwd=Path(__file__).parent.parent,
                capture_output=True,
                text=True,
                timeout=3,
                env={**environ, "WSGI_SERVER": "gunicorn"},
            )
        except subprocess.TimeoutExpired as e:
            # Server starts and runs, so timeout is expected
            output = e.stdout.decode() if e.stdout else ""
            assert "Starting Gunicorn WSGI server" in output, "Should use Gunicorn when WSGI_SERVER=gunicorn"
        finally:
            # Restore original value
            if old_value is not None:
                environ["WSGI_SERVER"] = old_value
            elif "WSGI_SERVER" in environ:
                del environ["WSGI_SERVER"]

    def test_wsgi_server_case_insensitive(self):
        """Test that WSGI_SERVER environment variable is case-insensitive."""
        old_value = environ.get("WSGI_SERVER")

        try:
            # Test with uppercase
            subprocess.run(
                [sys.executable, "run.py"],
                cwd=Path(__file__).parent.parent,
                capture_output=True,
                text=True,
                timeout=3,
                env={**environ, "WSGI_SERVER": "WAITRESS"},
            )
        except subprocess.TimeoutExpired as e:
            # Server starts and runs, so timeout is expected
            output = e.stdout.decode() if e.stdout else ""
            assert "Starting Waitress WSGI server" in output, "Should handle WAITRESS (uppercase)"
        finally:
            # Restore original value
            if old_value is not None:
                environ["WSGI_SERVER"] = old_value
            elif "WSGI_SERVER" in environ:
                del environ["WSGI_SERVER"]
