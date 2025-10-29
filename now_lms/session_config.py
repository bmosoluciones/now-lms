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
"""Session configuration for multi-worker/multi-threaded environments.

This module configures Flask sessions to work properly with production WSGI
servers (Gunicorn, Waitress) that use multiple workers or threads. It supports:
- Redis (preferred): Shared session storage across workers/threads
- SQLAlchemy: Database-backed session storage as fallback when Redis is unavailable
- NullSession: For testing environments

When running with production WSGI servers (multiple workers or threads), the
default Flask session (cookie-based) can cause erratic behavior because each
worker/thread may have its own memory space. This module ensures sessions are
properly shared.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------
import os

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------
from flask import Flask

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms.config import TESTING
from now_lms.logs import log

# Global variable to track if we've created the session model
_session_model_created = False


def get_session_config() -> dict[str, object] | None:
    """
    Determine the best session storage backend available.

    Priority order:
    1. Redis (if REDIS_URL or SESSION_REDIS_URL is set)
    2. SQLAlchemy (database-backed session storage)
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
        log.info("Configuring Redis-based session storage for multi-worker/multi-threaded WSGI servers")

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

    # Fallback to SQLAlchemy-backed session storage
    # This uses the database to store sessions, which works across WSGI workers/threads
    log.info("Configuring SQLAlchemy-based session storage for multi-worker/multi-threaded WSGI servers")

    return {
        "SESSION_TYPE": "sqlalchemy",
        "SESSION_SQLALCHEMY": None,  # Will be set in init_session with the app's db instance
        "SESSION_SQLALCHEMY_TABLE": "flask_sessions",
        "SESSION_PERMANENT": False,
        "SESSION_USE_SIGNER": True,  # Ensures sessions cannot be modified
        "PERMANENT_SESSION_LIFETIME": 86400,  # 24 hours
        "SESSION_COOKIE_HTTPONLY": True,
        "SESSION_COOKIE_SECURE": os.environ.get("FLASK_ENV") == "production",
        "SESSION_COOKIE_SAMESITE": "Lax",
        "SESSION_CLEANUP_N_REQUESTS": 100,  # Cleanup expired sessions every 100 requests on average
    }


def init_session(app: Flask) -> None:
    """
    Initialize Flask-Session with the appropriate backend.

    This function must be called after the Flask app is configured
    but before request handling begins.

    Args:
        app: Flask application instance

    Note:
        This ensures sessions work correctly with production WSGI servers
        (Gunicorn, Waitress) using multi-worker/multi-threaded architectures
        by using shared storage (Redis or database) instead of in-memory sessions.
    """
    global _session_model_created

    # Check if session is already initialized for this app
    if hasattr(app, "_session_initialized"):
        log.debug("Session already initialized for this app, skipping")
        return

    try:
        # Validate SECRET_KEY configuration
        secret_key = app.config.get("SECRET_KEY")
        if not secret_key or secret_key in {"dev", "development", "test"}:
            log.warning(
                "SECRET_KEY is not set or using default value! "
                "Set a unique SECRET_KEY for production: export SECRET_KEY=$(openssl rand -hex 32)"
            )
        elif len(str(secret_key)) < 32:
            log.warning(
                f"SECRET_KEY is too short ({len(str(secret_key))} chars). " "Use at least 32 characters for better security."
            )

        # Get the session configuration
        session_config = get_session_config()

        # If None (testing mode), skip Flask-Session initialization
        if session_config is None:
            log.debug("Skipping Flask-Session initialization for testing mode")
            app._session_initialized = True
            return

        from flask_session import Session

        # For SQLAlchemy backend, inject the app's database instance
        if session_config.get("SESSION_TYPE") == "sqlalchemy":
            from now_lms.db import database

            session_config["SESSION_SQLALCHEMY"] = database

            # If the model has already been created (e.g., by another app instance),
            # we need to skip re-creating it to avoid metadata conflicts
            if _session_model_created:
                log.debug("Session model already created, reusing existing model")
                # We still need to initialize flask-session for this app instance
                # but we need to handle the fact that the model already exists

        # Update Flask config with session settings
        app.config.update(session_config)

        # Initialize Flask-Session
        # This may fail if called multiple times with SQLAlchemy backend
        try:
            Session(app)
            if session_config.get("SESSION_TYPE") == "sqlalchemy":
                _session_model_created = True
        except Exception as e:
            # If initialization fails due to table already exists, that's ok for subsequent apps
            if "already defined" in str(e):
                log.debug(f"Session model already defined, continuing: {e}")
            else:
                raise

        # Mark as initialized
        app._session_initialized = True

        session_type = session_config.get("SESSION_TYPE", "unknown")
        log.info(f"Session storage initialized: {session_type}")

        # Log warnings and recommendations based on session type
        workers_env = os.environ.get("NOW_LMS_WORKERS") or os.environ.get("WORKERS")
        num_workers = int(workers_env) if workers_env else 1

        match session_type:
            case "redis":
                log.info("Using Redis for session storage - optimal for multi-worker WSGI servers")
                # Validate Redis connection
                redis_client = session_config.get("SESSION_REDIS")
                if redis_client:
                    try:
                        redis_client.ping()
                        log.info("Redis connection verified successfully")
                    except Exception as e:
                        log.error(f"Redis connection failed: {e}")
                        log.error("Sessions will not work correctly without Redis!")

            case "sqlalchemy":
                log.info("Using SQLAlchemy database for session storage - works with multi-worker/multi-threaded WSGI servers")
                table_name = session_config.get("SESSION_SQLALCHEMY_TABLE", "flask_sessions")
                log.info(f"Session table: {table_name}")

                if num_workers > 1:
                    log.warning(
                        f"Running with {num_workers} workers using database backend."
                        "Redis is recommended for better performance and reliability. "
                        "Set SESSION_REDIS_URL environment variable to use Redis."
                    )
            case _:
                log.warning(f"Unknown session type: {session_type}")

                if num_workers > 1:
                    log.warning(
                        f"Running with {num_workers} workers without shared session storage! "
                        "Sessions may not persist correctly. "
                        "Set SESSION_REDIS_URL for Redis or ensure Flask-Session is configured."
                    )

    except ImportError:
        log.error(
            "Flask-Session is not installed. Sessions may not work correctly "
            "with multi-worker/multi-threaded WSGI servers. Install with: pip install flask-session"
        )
        raise
    except Exception as e:
        log.error(f"Failed to initialize session storage: {e}")
        raise
