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

"""Debug endpoints for troubleshooting multi-worker WSGI server issues.

These endpoints are only available when NOW_LMS_DEBUG_ENDPOINTS=1 is set.
DO NOT enable in production as they expose sensitive information.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------
import os
from typing import Any

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------
from flask import Blueprint, Response, current_app, jsonify, session
from flask_login import current_user

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms.logs import log

debug_bp = Blueprint("debug", __name__, url_prefix="/debug")


def is_debug_enabled() -> bool:
    """Check if debug endpoints are enabled via environment variable."""
    return os.environ.get("NOW_LMS_DEBUG_ENDPOINTS", "0").strip().lower() in {"1", "true", "yes", "on"}


@debug_bp.route("/session", methods=["GET"])
def debug_session() -> tuple[Response, int]:
    """Debug endpoint to verify session persistence across workers.

    This endpoint shows:
    - Current process ID (PID) - helps verify load balancing across workers
    - Session data - confirms session storage is working
    - Current user info - verifies Flask-Login integration
    - Session backend type - confirms Redis/CacheLib is active

    Usage:
        1. Login to the application
        2. Call this endpoint multiple times: curl -b cookies.txt http://localhost:8080/debug/session
        3. Observe that PID may change (different workers) but session data remains consistent

    Security:
        Only available when NOW_LMS_DEBUG_ENDPOINTS=1 environment variable is set.
        DO NOT enable in production.

    Returns:
        JSON with process info, session data, and user info
    """
    if not is_debug_enabled():
        log.warning("Debug endpoint accessed but NOW_LMS_DEBUG_ENDPOINTS is not enabled")
        return jsonify({"error": "Debug endpoints are not enabled", "help": "Set NOW_LMS_DEBUG_ENDPOINTS=1"}), 403

    # Get current process ID
    pid = os.getpid()

    # Get session data (sanitize sensitive info)
    session_data: dict[str, Any] = {}
    for key in session.keys():
        # Don't expose CSRF tokens or other sensitive session data
        if key.startswith("_"):
            session_data[key] = "[hidden]"
        else:
            session_data[key] = session.get(key)

    # Get current user info
    user_info = None
    if current_user.is_authenticated:
        user_info = {
            "id": current_user.id,
            "usuario": current_user.usuario,
            "tipo": current_user.tipo,
            "activo": current_user.activo,
        }

    # Get session backend type
    session_type = current_app.config.get("SESSION_TYPE", "default")

    # Get worker info
    worker_info = {
        "pid": pid,
        "workers_env": os.environ.get("NOW_LMS_WORKERS") or os.environ.get("WORKERS"),
        "threads_env": os.environ.get("NOW_LMS_THREADS") or os.environ.get("THREADS"),
    }

    response_data = {
        "worker": worker_info,
        "session_backend": session_type,
        "session_data": session_data,
        "current_user": user_info,
        "authenticated": current_user.is_authenticated,
    }

    log.debug(f"Debug session endpoint called from PID {pid}")
    return jsonify(response_data), 200


@debug_bp.route("/config", methods=["GET"])
def debug_config() -> tuple[Response, int]:
    """Debug endpoint to verify configuration for multi-worker setup.

    This endpoint shows critical configuration that affects session handling:
    - SECRET_KEY (masked)
    - SESSION_TYPE
    - Redis/Cache URLs (masked)
    - Cookie settings

    Security:
        Only available when NOW_LMS_DEBUG_ENDPOINTS=1 environment variable is set.
        DO NOT enable in production.

    Returns:
        JSON with configuration info (sensitive values masked)
    """
    if not is_debug_enabled():
        log.warning("Debug config endpoint accessed but NOW_LMS_DEBUG_ENDPOINTS is not enabled")
        return jsonify({"error": "Debug endpoints are not enabled", "help": "Set NOW_LMS_DEBUG_ENDPOINTS=1"}), 403

    def mask_value(value: str | None) -> str:
        """Mask sensitive configuration values."""
        if not value:
            return "[not set]"
        if len(value) <= 8:
            return "****"
        return f"{value[:4]}...{value[-4:]}"

    # Get relevant configuration
    config_info = {
        "secret_key": mask_value(current_app.config.get("SECRET_KEY")),
        "secret_key_is_default": current_app.config.get("SECRET_KEY") in {"dev", "test-secret-key-for-testing"},
        "session_type": current_app.config.get("SESSION_TYPE", "default"),
        "session_permanent": current_app.config.get("SESSION_PERMANENT"),
        "session_use_signer": current_app.config.get("SESSION_USE_SIGNER"),
        "session_cookie_httponly": current_app.config.get("SESSION_COOKIE_HTTPONLY"),
        "session_cookie_secure": current_app.config.get("SESSION_COOKIE_SECURE"),
        "session_cookie_samesite": current_app.config.get("SESSION_COOKIE_SAMESITE"),
        "permanent_session_lifetime": str(current_app.config.get("PERMANENT_SESSION_LIFETIME")),
        "redis_url": mask_value(
            os.environ.get("SESSION_REDIS_URL") or os.environ.get("CACHE_REDIS_URL") or os.environ.get("REDIS_URL")
        ),
        "testing": current_app.config.get("TESTING"),
    }

    # Environment checks
    env_checks = {
        "NOW_LMS_WORKERS": os.environ.get("NOW_LMS_WORKERS") or os.environ.get("WORKERS"),
        "NOW_LMS_THREADS": os.environ.get("NOW_LMS_THREADS") or os.environ.get("THREADS"),
        "FLASK_ENV": os.environ.get("FLASK_ENV"),
        "has_redis_url": bool(
            os.environ.get("SESSION_REDIS_URL") or os.environ.get("CACHE_REDIS_URL") or os.environ.get("REDIS_URL")
        ),
    }

    # Warnings for common misconfigurations
    warnings = []
    if config_info["secret_key_is_default"]:
        warnings.append("SECRET_KEY is using default value - set a unique value for production")

    if config_info["session_type"] == "default" and (
        env_checks["NOW_LMS_WORKERS"] and int(env_checks["NOW_LMS_WORKERS"] or "1") > 1
    ):
        warnings.append("Using default session with multiple workers - sessions may not persist. Use Redis or CacheLib.")

    if config_info["session_type"] == "cachelib" and (
        env_checks["NOW_LMS_WORKERS"] and int(env_checks["NOW_LMS_WORKERS"] or "1") > 1
    ):
        warnings.append(
            "Using CacheLib with multiple workers - ensure shared filesystem. Redis is recommended for multi-worker."
        )

    response_data = {
        "config": config_info,
        "environment": env_checks,
        "warnings": warnings,
        "recommendations": [
            "Use Redis for session storage with multiple workers: export REDIS_URL=redis://localhost:6379/0",
            "Set unique SECRET_KEY: export SECRET_KEY=$(openssl rand -hex 32)",
            "Ensure identical SECRET_KEY across all workers",
            "For HTTPS, set SESSION_COOKIE_SECURE=True",
        ],
    }

    log.debug("Debug config endpoint called")
    return jsonify(response_data), 200


@debug_bp.route("/redis", methods=["GET"])
def debug_redis() -> tuple[Response, int]:
    """Debug endpoint to test Redis connection.

    Security:
        Only available when NOW_LMS_DEBUG_ENDPOINTS=1 environment variable is set.
        DO NOT enable in production.

    Returns:
        JSON with Redis connection status
    """
    if not is_debug_enabled():
        log.warning("Debug redis endpoint accessed but NOW_LMS_DEBUG_ENDPOINTS is not enabled")
        return jsonify({"error": "Debug endpoints are not enabled", "help": "Set NOW_LMS_DEBUG_ENDPOINTS=1"}), 403

    redis_url = os.environ.get("SESSION_REDIS_URL") or os.environ.get("CACHE_REDIS_URL") or os.environ.get("REDIS_URL")

    if not redis_url:
        return (
            jsonify(
                {
                    "status": "not_configured",
                    "message": "Redis URL not configured",
                    "help": "Set REDIS_URL, CACHE_REDIS_URL, or SESSION_REDIS_URL environment variable",
                }
            ),
            200,
        )

    try:
        import redis

        client = redis.from_url(redis_url)
        # Test connection
        client.ping()

        # Get some stats
        info = client.info("server")
        stats = {
            "redis_version": info.get("redis_version"),
            "uptime_in_seconds": info.get("uptime_in_seconds"),
            "connected_clients": info.get("connected_clients"),
        }

        # Try to list session keys (limited)
        session_keys = client.keys("session:*")
        key_count = len(session_keys)

        return (
            jsonify(
                {
                    "status": "ok",
                    "message": "Redis connection successful",
                    "stats": stats,
                    "session_keys_count": key_count,
                }
            ),
            200,
        )

    except ImportError:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Redis library not installed",
                    "help": "Install with: pip install redis",
                }
            ),
            503,
        )
    except Exception as e:
        log.error(f"Redis connection failed: {e}")
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"Redis connection failed: {str(e)}",
                    "help": "Check Redis URL and ensure Redis server is running",
                }
            ),
            503,
        )
