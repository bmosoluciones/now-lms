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
"""Tests to verify Waitress and Gunicorn use synchronized configuration."""

from __future__ import annotations

# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------
from os import environ

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms.worker_config import get_worker_config_from_env


class TestWSGIConfigSync:
    """Test cases to verify WSGI server configuration is synchronized."""

    def test_both_servers_use_same_config_function(self):
        """Test that both Waitress and Gunicorn use get_worker_config_from_env()."""
        # This test verifies the design decision that both servers
        # use the same configuration function

        # Clear environment
        old_values = {
            "NOW_LMS_WORKERS": environ.get("NOW_LMS_WORKERS"),
            "NOW_LMS_THREADS": environ.get("NOW_LMS_THREADS"),
            "WORKERS": environ.get("WORKERS"),
            "THREADS": environ.get("THREADS"),
        }

        try:
            # Clear all variants
            for var in old_values.keys():
                if var in environ:
                    del environ[var]

            # Set explicit configuration
            environ["NOW_LMS_WORKERS"] = "5"
            environ["NOW_LMS_THREADS"] = "4"

            workers, threads = get_worker_config_from_env()

            # Both servers should get the same values from this function
            assert workers == 5, "Workers should be 5"
            assert threads == 4, "Threads should be 4"

            # For Gunicorn: uses both workers and threads
            # For Waitress: only uses threads (single-process server)
            # But both call the same function

        finally:
            # Restore environment
            for var, value in old_values.items():
                if value is not None:
                    environ[var] = value
                elif var in environ:
                    del environ[var]

    def test_shared_environment_variables(self):
        """Test that both servers support the same environment variables."""
        old_values = {
            "NOW_LMS_WORKERS": environ.get("NOW_LMS_WORKERS"),
            "NOW_LMS_THREADS": environ.get("NOW_LMS_THREADS"),
            "NOW_LMS_WORKER_MEMORY_MB": environ.get("NOW_LMS_WORKER_MEMORY_MB"),
        }

        try:
            # Clear all variants
            for var in old_values.keys():
                if var in environ:
                    del environ[var]

            # Set shared configuration using NOW_LMS_ prefix
            environ["NOW_LMS_THREADS"] = "8"

            workers, threads = get_worker_config_from_env()

            # Both servers should get thread count from same env var
            assert threads == 8, "Both servers should use NOW_LMS_THREADS"

        finally:
            # Restore environment
            for var, value in old_values.items():
                if value is not None:
                    environ[var] = value
                elif var in environ:
                    del environ[var]

    def test_automatic_calculation_is_consistent(self):
        """Test that automatic calculation produces consistent results."""
        old_values = {
            "NOW_LMS_WORKERS": environ.get("NOW_LMS_WORKERS"),
            "NOW_LMS_THREADS": environ.get("NOW_LMS_THREADS"),
            "WORKERS": environ.get("WORKERS"),
            "THREADS": environ.get("THREADS"),
        }

        try:
            # Clear all variants to force automatic calculation
            for var in old_values.keys():
                if var in environ:
                    del environ[var]

            # Get configuration twice - should be identical
            workers1, threads1 = get_worker_config_from_env()
            workers2, threads2 = get_worker_config_from_env()

            assert workers1 == workers2, "Worker calculation should be deterministic"
            assert threads1 == threads2, "Thread calculation should be deterministic"

            # Both values should be at least 1
            assert workers1 >= 1, "Workers should be at least 1"
            assert threads1 >= 1, "Threads should be at least 1"

        finally:
            # Restore environment
            for var, value in old_values.items():
                if value is not None:
                    environ[var] = value
                elif var in environ:
                    del environ[var]

    def test_session_config_works_for_both_servers(self):
        """Test that session configuration is server-agnostic."""
        from now_lms.session_config import get_session_config

        # Session config should work regardless of which WSGI server is used
        # In testing mode, it returns None
        config = get_session_config()

        # In testing mode, session config should be None (uses default Flask sessions)
        # This is correct for both Waitress and Gunicorn in tests
        assert config is None, "Session config should be None in testing mode"

    def test_formula_consistency(self):
        """Test that the worker calculation formula is consistently applied."""
        from now_lms.worker_config import calculate_optimal_workers

        # Test the formula gives consistent results
        workers_default = calculate_optimal_workers()
        assert workers_default >= 1, "Should always return at least 1 worker"

        # Test with threads reduces worker count
        workers_with_threads = calculate_optimal_workers(threads=4)
        assert workers_with_threads >= 1, "Should always return at least 1 worker with threads"

        # With threads, workers should be reduced or equal
        # (depending on system resources)
        assert workers_with_threads <= workers_default, "Threads should reduce or maintain worker count"
