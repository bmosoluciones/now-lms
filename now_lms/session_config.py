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

"""Session configuration for multi-worker environments (Gunicorn).

This module configures Flask sessions to work properly with Gunicorn's
multi-worker architecture. It supports:
- Redis (preferred): Shared session storage across workers
- CacheLib FileSystemCache: Fallback when Redis is unavailable
- NullSession: For testing environments

When running with Gunicorn (multiple worker processes), the default Flask
session (cookie-based) can cause erratic behavior because each worker has
its own memory space. This module ensures sessions are properly shared.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------
import os
import tempfile
from pathlib import Path

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------
from flask import Flask

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms.config import TESTING
from now_lms.logs import log


def get_session_config() -> dict[str, object] | None:
    """
    Determine the best session storage backend available.

    Priority order:
    1. Redis (if REDIS_URL or SESSION_REDIS_URL is set)
    2. CacheLib FileSystemCache (if not in testing mode)
    3. None (for testing - use default Flask sessions)

    Returns:
        dict: Configuration dictionary for Flask-Session, or None to skip
    """
    if TESTING:
        # In testing mode, don't use Flask-Session at all
        # Flask's default signed cookie sessions work fine for tests
        return None

    # Use the Redis URL check pattern from now_lms/cache.py line 45
    redis_url = os.environ.get("SESSION_REDIS_URL") or os.environ.get("CACHE_REDIS_URL") or os.environ.get("REDIS_URL")

    if redis_url:
        log.info("Configuring Redis-based session storage for Gunicorn workers")

        # Import Redis client
        try:
            import redis

            redis_client = redis.from_url(redis_url)
        except ImportError:
            log.error("Redis library not installed. Install with: pip install redis")
            raise

        return {
            "SESSION_TYPE": "redis",
            "SESSION_REDIS": redis_client,  # Must be Redis client object, not URL string
            "SESSION_PERMANENT": False,
            "SESSION_USE_SIGNER": True,  # Ensures sessions cannot be modified
            "SESSION_KEY_PREFIX": "session:",
            "PERMANENT_SESSION_LIFETIME": 86400,  # 24 hours
            "SESSION_COOKIE_HTTPONLY": True,
            "SESSION_COOKIE_SECURE": os.environ.get("FLASK_ENV") == "production",
            "SESSION_COOKIE_SAMESITE": "Lax",
        }

    # Fallback to CacheLib FileSystemCache
    # Using CacheLib instead of deprecated filesystem backend
    # This works across Gunicorn workers as long as they share the same filesystem
    log.info("Configuring CacheLib FileSystemCache-based session storage for Gunicorn workers")

    # Prefer /dev/shm for better performance (shared memory)
    # Fall back to temp directory if /dev/shm is not available
    shm_path = Path("/dev/shm")
    if shm_path.exists() and shm_path.is_dir():
        cache_dir = shm_path / "now_lms_sessions"
    else:
        cache_dir = Path(tempfile.gettempdir()) / "now_lms_sessions"

    cache_dir.mkdir(parents=True, exist_ok=True)

    # Import and create FileSystemCache from cachelib
    from cachelib import FileSystemCache

    return {
        "SESSION_TYPE": "cachelib",
        "SESSION_CACHELIB": FileSystemCache(cache_dir=str(cache_dir), threshold=1000),
        "SESSION_PERMANENT": False,
        "SESSION_USE_SIGNER": True,  # Ensures sessions cannot be modified
        "SESSION_FILE_THRESHOLD": 1000,  # Maximum number of sessions before cleanup
        "PERMANENT_SESSION_LIFETIME": 86400,  # 24 hours
        "SESSION_COOKIE_HTTPONLY": True,
        "SESSION_COOKIE_SECURE": os.environ.get("FLASK_ENV") == "production",
        "SESSION_COOKIE_SAMESITE": "Lax",
    }


def init_session(app: Flask) -> None:
    """
    Initialize Flask-Session with the appropriate backend.

    This function must be called after the Flask app is configured
    but before request handling begins.

    Args:
        app: Flask application instance

    Note:
        This ensures sessions work correctly with Gunicorn's multi-worker
        architecture by using shared storage (Redis or filesystem) instead
        of in-memory sessions.
    """
    try:
        # Get the session configuration
        session_config = get_session_config()

        # If None (testing mode), skip Flask-Session initialization
        if session_config is None:
            log.debug("Skipping Flask-Session initialization for testing mode")
            return

        from flask_session import Session

        # Update Flask config with session settings
        app.config.update(session_config)

        # Initialize Flask-Session
        Session(app)

        session_type = session_config.get("SESSION_TYPE", "unknown")
        log.info(f"Session storage initialized: {session_type}")

        match session_type:
            case "redis":
                log.info("Using Redis for session storage - optimal for Gunicorn")
            case "cachelib":
                log.info("Using CacheLib FileSystemCache for session storage - works with Gunicorn")
                cache_backend = session_config.get("SESSION_CACHELIB")
                if hasattr(cache_backend, "_path"):
                    log.info(f"Session cache directory: {cache_backend._path}")
            case _:
                log.warning(f"Unknown session type: {session_type}")

    except ImportError:
        log.error(
            "Flask-Session is not installed. Sessions may not work correctly "
            "with Gunicorn multi-worker setup. Install with: pip install flask-session"
        )
        raise
    except Exception as e:
        log.error(f"Failed to initialize session storage: {e}")
        raise
