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
"""Tests for worker configuration utilities."""

from __future__ import annotations

# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------
from os import cpu_count as os_cpu_count
from os import environ
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms.worker_config import calculate_optimal_workers, get_worker_config_from_env


class TestCalculateOptimalWorkers:
    """Test cases for calculate_optimal_workers function."""

    def test_minimum_workers(self):
        """Test that minimum workers constraint is respected."""
        workers = calculate_optimal_workers(min_workers=3)
        assert workers >= 3

    def test_cpu_based_calculation(self):
        """Test CPU-based worker calculation."""
        cpu_count = os_cpu_count() or 1
        expected = (cpu_count * 2) + 1

        # With very high RAM, should use CPU-based calculation
        with patch("now_lms.worker_config.PSUTIL_AVAILABLE", False):
            workers = calculate_optimal_workers()
            assert workers == expected

    def test_thread_adjustment(self):
        """Test that threads reduce worker count proportionally."""
        with patch("now_lms.worker_config.PSUTIL_AVAILABLE", False):
            workers_no_threads = calculate_optimal_workers(threads=1)
            workers_with_threads = calculate_optimal_workers(threads=2)

            # With threads, workers should be reduced
            # Expected: workers_no_threads / 2 (but minimum 1)
            expected = max(1, workers_no_threads // 2)
            assert workers_with_threads == expected

    def test_max_workers_constraint(self):
        """Test that maximum workers constraint is respected."""
        workers = calculate_optimal_workers(max_workers=2)
        assert workers <= 2

    def test_ram_based_calculation(self):
        """Test RAM-based worker calculation when psutil is available."""
        # Mock psutil to simulate low RAM scenario
        mock_memory = MagicMock()
        mock_memory.available = 1024 * 1024 * 1024  # 1 GB in bytes

        with patch("now_lms.worker_config.PSUTIL_AVAILABLE", True):
            with patch("now_lms.worker_config.psutil.virtual_memory", return_value=mock_memory):
                # With 1 GB RAM and 200 MB per worker, should get ~5 workers
                # But CPU calculation might be lower/higher
                workers = calculate_optimal_workers(worker_memory_mb=200)

                # Should use minimum of RAM-based (5) and CPU-based
                cpu_count = os_cpu_count() or 1
                cpu_based = (cpu_count * 2) + 1
                ram_based = 1024 // 200  # ~5 workers
                expected = min(cpu_based, ram_based)

                assert workers == expected

    def test_very_low_ram(self):
        """Test that system handles very low RAM correctly."""
        # Mock psutil to simulate very low RAM
        mock_memory = MagicMock()
        mock_memory.available = 100 * 1024 * 1024  # 100 MB in bytes

        with patch("now_lms.worker_config.PSUTIL_AVAILABLE", True):
            with patch("now_lms.worker_config.psutil.virtual_memory", return_value=mock_memory):
                # With 100 MB RAM and 200 MB per worker, calculation would give 0
                # But minimum should be 1
                workers = calculate_optimal_workers(worker_memory_mb=200, min_workers=1)
                assert workers == 1

    def test_threads_with_low_ram(self):
        """Test that threads help when RAM is limited."""
        # Mock psutil to simulate low RAM
        mock_memory = MagicMock()
        mock_memory.available = 400 * 1024 * 1024  # 400 MB in bytes

        with patch("now_lms.worker_config.PSUTIL_AVAILABLE", True):
            with patch("now_lms.worker_config.psutil.virtual_memory", return_value=mock_memory):
                # With 400 MB RAM and 200 MB per worker: 2 workers
                # With threads=4, should get 2 / 4 = 0, but minimum 1
                workers = calculate_optimal_workers(worker_memory_mb=200, threads=4, min_workers=1)
                assert workers >= 1


class TestGetWorkerConfigFromEnv:
    """Test cases for get_worker_config_from_env function."""

    def test_default_configuration(self):
        """Test default configuration when no env vars are set."""
        # Clear relevant environment variables (both old and new naming)
        env_vars = [
            "LMS_WORKERS",
            "LMS_THREADS",
            "LMS_WORKER_MEMORY_MB",
            "NOW_LMS_WORKERS",
            "NOW_LMS_THREADS",
            "NOW_LMS_WORKER_MEMORY_MB",
            "WORKERS",
            "THREADS",
            "WORKER_MEMORY_MB",
        ]
        old_values = {}
        for var in env_vars:
            old_values[var] = environ.get(var)
            if var in environ:
                del environ[var]

        try:
            workers, threads = get_worker_config_from_env()

            # Should get calculated workers and default threads
            assert workers >= 1
            assert threads == 1
        finally:
            # Restore environment
            for var, value in old_values.items():
                if value is not None:
                    environ[var] = value

    def test_explicit_workers(self):
        """Test explicit worker count from environment using NOW_LMS_ prefix."""
        old_values = {
            "NOW_LMS_WORKERS": environ.get("NOW_LMS_WORKERS"),
            "WORKERS": environ.get("WORKERS"),
        }
        try:
            # Clear all variants
            for var in old_values.keys():
                if var in environ:
                    del environ[var]

            environ["NOW_LMS_WORKERS"] = "5"
            workers, threads = get_worker_config_from_env()

            assert workers == 5
            assert threads == 1
        finally:
            for var, value in old_values.items():
                if value is not None:
                    environ[var] = value
                elif var in environ:
                    del environ[var]

    def test_explicit_threads(self):
        """Test explicit thread count from environment using NOW_LMS_ prefix."""
        old_values = {
            "NOW_LMS_THREADS": environ.get("NOW_LMS_THREADS"),
            "THREADS": environ.get("THREADS"),
        }
        try:
            # Clear all variants
            for var in old_values.keys():
                if var in environ:
                    del environ[var]

            environ["NOW_LMS_THREADS"] = "4"
            workers, threads = get_worker_config_from_env()

            assert threads == 4
            # Workers should be adjusted for threads
            assert workers >= 1
        finally:
            for var, value in old_values.items():
                if value is not None:
                    environ[var] = value
                elif var in environ:
                    del environ[var]

    def test_custom_worker_memory(self):
        """Test custom worker memory configuration."""
        old_values = {
            "NOW_LMS_WORKER_MEMORY_MB": environ.get("NOW_LMS_WORKER_MEMORY_MB"),
            "WORKER_MEMORY_MB": environ.get("WORKER_MEMORY_MB"),
            "NOW_LMS_WORKERS": environ.get("NOW_LMS_WORKERS"),
            "WORKERS": environ.get("WORKERS"),
        }

        try:
            # Clear all variants to force calculation
            for var in old_values.keys():
                if var in environ:
                    del environ[var]

            environ["NOW_LMS_WORKER_MEMORY_MB"] = "500"

            # Mock psutil with fixed RAM
            mock_memory = MagicMock()
            mock_memory.available = 2048 * 1024 * 1024  # 2 GB

            with patch("now_lms.worker_config.PSUTIL_AVAILABLE", True):
                with patch("now_lms.worker_config.psutil.virtual_memory", return_value=mock_memory):
                    workers, threads = get_worker_config_from_env()

                    # With 2 GB RAM and 500 MB per worker, should get max 4 workers
                    # But also limited by CPU calculation
                    cpu_count = os_cpu_count() or 1
                    cpu_based = (cpu_count * 2) + 1
                    ram_based = 2048 // 500  # 4 workers
                    expected = min(cpu_based, ram_based)

                    assert workers == expected
        finally:
            for var, value in old_values.items():
                if value is not None:
                    environ[var] = value
                elif var in environ:
                    del environ[var]

    def test_invalid_env_values(self):
        """Test handling of invalid environment variable values."""
        old_values = {
            "NOW_LMS_WORKERS": environ.get("NOW_LMS_WORKERS"),
            "NOW_LMS_THREADS": environ.get("NOW_LMS_THREADS"),
            "WORKERS": environ.get("WORKERS"),
            "THREADS": environ.get("THREADS"),
        }

        try:
            # Clear all variants first
            for var in old_values.keys():
                if var in environ:
                    del environ[var]

            environ["NOW_LMS_WORKERS"] = "invalid"
            environ["NOW_LMS_THREADS"] = "also_invalid"

            # Should fallback to calculated/default values
            workers, threads = get_worker_config_from_env()

            assert workers >= 1
            assert threads == 1
        finally:
            for var, value in old_values.items():
                if value is not None:
                    environ[var] = value
                elif var in environ:
                    del environ[var]

    def test_zero_threads(self):
        """Test that zero threads is adjusted to minimum 1."""
        old_values = {
            "NOW_LMS_THREADS": environ.get("NOW_LMS_THREADS"),
            "THREADS": environ.get("THREADS"),
        }
        try:
            # Clear all variants first
            for var in old_values.keys():
                if var in environ:
                    del environ[var]

            environ["NOW_LMS_THREADS"] = "0"
            workers, threads = get_worker_config_from_env()

            # Should be adjusted to minimum 1
            assert threads == 1
        finally:
            for var, value in old_values.items():
                if value is not None:
                    environ[var] = value
                elif var in environ:
                    del environ[var]

    def test_now_lms_prefix_workers(self):
        """Test NOW_LMS_WORKERS prefix (preferred naming)."""
        old_values = {
            "NOW_LMS_WORKERS": environ.get("NOW_LMS_WORKERS"),
            "WORKERS": environ.get("WORKERS"),
            "LMS_WORKERS": environ.get("LMS_WORKERS"),
        }
        try:
            # Clear all variants
            for var in old_values.keys():
                if var in environ:
                    del environ[var]

            environ["NOW_LMS_WORKERS"] = "5"
            workers, threads = get_worker_config_from_env()

            assert workers == 5
            assert threads == 1
        finally:
            for var, value in old_values.items():
                if value is not None:
                    environ[var] = value
                elif var in environ:
                    del environ[var]

    def test_now_lms_prefix_threads(self):
        """Test NOW_LMS_THREADS prefix (preferred naming)."""
        old_values = {
            "NOW_LMS_THREADS": environ.get("NOW_LMS_THREADS"),
            "THREADS": environ.get("THREADS"),
            "LMS_THREADS": environ.get("LMS_THREADS"),
        }
        try:
            # Clear all variants
            for var in old_values.keys():
                if var in environ:
                    del environ[var]

            environ["NOW_LMS_THREADS"] = "4"
            workers, threads = get_worker_config_from_env()

            assert threads == 4
        finally:
            for var, value in old_values.items():
                if value is not None:
                    environ[var] = value
                elif var in environ:
                    del environ[var]

    def test_unprefixed_names(self):
        """Test unprefixed variable names (WORKERS, THREADS)."""
        old_values = {
            "NOW_LMS_WORKERS": environ.get("NOW_LMS_WORKERS"),
            "WORKERS": environ.get("WORKERS"),
            "NOW_LMS_THREADS": environ.get("NOW_LMS_THREADS"),
            "THREADS": environ.get("THREADS"),
        }
        try:
            # Clear all variants
            for var in old_values.keys():
                if var in environ:
                    del environ[var]

            # Set unprefixed versions
            environ["WORKERS"] = "3"
            environ["THREADS"] = "2"
            workers, threads = get_worker_config_from_env()

            assert workers == 3
            assert threads == 2
        finally:
            for var, value in old_values.items():
                if value is not None:
                    environ[var] = value
                elif var in environ:
                    del environ[var]

    def test_priority_now_lms_over_unprefixed(self):
        """Test that NOW_LMS_* takes priority over unprefixed."""
        old_values = {
            "NOW_LMS_WORKERS": environ.get("NOW_LMS_WORKERS"),
            "WORKERS": environ.get("WORKERS"),
            "NOW_LMS_THREADS": environ.get("NOW_LMS_THREADS"),
            "THREADS": environ.get("THREADS"),
        }
        try:
            # Clear all variants
            for var in old_values.keys():
                if var in environ:
                    del environ[var]

            # Set both - NOW_LMS_ should take priority
            environ["NOW_LMS_WORKERS"] = "5"
            environ["WORKERS"] = "3"
            environ["NOW_LMS_THREADS"] = "4"
            environ["THREADS"] = "2"

            workers, threads = get_worker_config_from_env()

            # Should use NOW_LMS_ values
            assert workers == 5
            assert threads == 4
        finally:
            for var, value in old_values.items():
                if value is not None:
                    environ[var] = value
                elif var in environ:
                    del environ[var]
