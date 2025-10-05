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
"""Worker configuration utilities for optimizing RAM usage."""

from __future__ import annotations

# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------
from os import cpu_count as os_cpu_count
from os import environ

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------
try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


def calculate_optimal_workers(
    worker_memory_mb: int = 200,
    min_workers: int = 1,
    max_workers: int | None = None,
    threads: int = 1,
) -> int:
    """
    Calculate optimal number of Gunicorn workers based on available RAM and CPU.

    Formula follows the guidelines from the issue:
    - CPU-based: (cpu_count * 2) + 1
    - RAM-based: available_ram_mb / worker_memory_mb
    - With threads: workers / threads (rounded down)
    - Minimum: 1 worker with threads

    Args:
        worker_memory_mb: Estimated memory usage per worker in MB (default: 200)
        min_workers: Minimum number of workers (default: 1)
        max_workers: Maximum number of workers (optional)
        threads: Number of threads per worker (default: 1)

    Returns:
        Optimal number of workers
    """
    cpu_count = os_cpu_count() or 1

    # Calculate CPU-based workers: (cpu_count * 2) + 1
    cpu_based_workers = (cpu_count * 2) + 1

    # Calculate RAM-based workers if psutil is available
    ram_based_workers = cpu_based_workers  # Default to CPU-based

    if PSUTIL_AVAILABLE:
        try:
            memory = psutil.virtual_memory()
            available_ram_mb = memory.available / (1024 * 1024)
            ram_based_workers = int(available_ram_mb / worker_memory_mb)
        except Exception:
            # If psutil fails, fallback to CPU-based calculation
            pass

    # Use the minimum of CPU-based and RAM-based calculations
    optimal_workers = min(cpu_based_workers, ram_based_workers)

    # Adjust for threads: if using threads, reduce workers proportionally
    if threads > 1:
        optimal_workers = max(min_workers, optimal_workers // threads)

    # Apply minimum constraint
    optimal_workers = max(min_workers, optimal_workers)

    # Apply maximum constraint if specified
    if max_workers is not None:
        optimal_workers = min(optimal_workers, max_workers)

    return optimal_workers


def get_worker_config_from_env() -> tuple[int, int]:
    """
    Get worker and thread configuration from environment variables.

    Supports both NOW_LMS_* (preferred) and unprefixed versions for backward compatibility.
    Priority: NOW_LMS_* > unprefixed

    Returns:
        Tuple of (workers, threads)
    """
    # Get threads from environment (default: 1)
    threads = 1
    threads_str = environ.get("NOW_LMS_THREADS") or environ.get("THREADS")
    if threads_str:
        try:
            threads = int(threads_str)
            threads = max(1, threads)  # Ensure at least 1 thread
        except (ValueError, TypeError):
            threads = 1

    # Get workers from environment or calculate optimal
    workers = None
    workers_str = environ.get("NOW_LMS_WORKERS") or environ.get("WORKERS")
    if workers_str:
        try:
            workers = int(workers_str)
        except (ValueError, TypeError):
            pass

    # If workers not explicitly set, calculate optimal based on system resources
    if workers is None:
        # Get worker memory estimate from environment (default: 200 MB)
        worker_memory_mb = 200
        worker_memory_str = environ.get("NOW_LMS_WORKER_MEMORY_MB") or environ.get("WORKER_MEMORY_MB")
        if worker_memory_str:
            try:
                worker_memory_mb = int(worker_memory_str)
            except (ValueError, TypeError):
                pass

        workers = calculate_optimal_workers(
            worker_memory_mb=worker_memory_mb,
            threads=threads,
        )

    return workers, threads
