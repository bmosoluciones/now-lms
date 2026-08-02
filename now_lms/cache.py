# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.

"""Configuración de cache."""

from __future__ import annotations

# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------
from os import environ

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------
from flask_caching import Cache
from flask_login import current_user

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms.logs import log

# < --------------------------------------------------------------------------------------------- >
# Configuracion de Cache


# For backward compatibility, we need to maintain CTYPE and CACHE_CONFIG
# The actual cache initialization will be handled by cache_utils.py
def _determine_cache_type() -> str:
    """Helper to determine which cache type is configured via environment variables."""
    if (environ.get("CACHE_REDIS_URL")) or (environ.get("REDIS_URL")):
        return "redis"
    if environ.get("CACHE_MEMCACHED_SERVERS"):
        return "memcached"
    if environ.get("NOW_LMS_MEMORY_CACHE", "0") == "1":
        return "filesystem"
    return "null"


def _get_cache_type_for_compatibility() -> str:
    """Determine cache type for backward compatibility with existing code."""
    cache_type = _determine_cache_type()

    match cache_type:
        case "redis":
            return "RedisCache"
        case "memcached":
            return "MemcachedCache"
        case "filesystem":
            return "FileSystemCache"
        case _:
            return "NullCache"


def _get_cache_config_for_compatibility() -> dict[str, object]:
    """Get basic cache config for backward compatibility."""
    config: dict[str, object] = {"CACHE_KEY_PREFIX": "now_lms:", "CACHE_DEFAULT_TIMEOUT": 300}

    cache_type = _determine_cache_type()

    match cache_type:
        case "redis":
            config["CACHE_TYPE"] = "RedisCache"
            config["CACHE_REDIS_URL"] = environ.get("CACHE_REDIS_URL") or environ.get("REDIS_URL")
        case "memcached":
            config["CACHE_TYPE"] = "MemcachedCache"
            config["CACHE_MEMCACHED_SERVERS"] = environ.get("CACHE_MEMCACHED_SERVERS")
        case "filesystem":
            config["CACHE_TYPE"] = "FileSystemCache"
            # Note: CACHE_DIR will be determined dynamically by cache_utils
        case _:
            config["CACHE_TYPE"] = "NullCache"

    return config


# Maintain backward compatibility
CTYPE = _get_cache_type_for_compatibility()
CACHE_CONFIG = _get_cache_config_for_compatibility()

if CTYPE != "NullCache":
    log.trace(f"Using {CTYPE} service for storage")
else:
    log.debug("No cache service configured.")

# Create cache instance (will be properly initialized via cache_utils.init_cache)
cache: Cache = Cache()


# ---------------------------------------------------------------------------------------
# Opciones de cache.
# ---------------------------------------------------------------------------------------
def no_guardar_en_cache_global() -> bool:
    """Si el usuario es anomino preferimos usar el sistema de cache."""
    # Return True (don't cache) when user is authenticated
    # Return False (do cache) when user is anonymous
    # IMPORTANT: This only controls whether to WRITE to cache, not whether to READ from it
    # If an anonymous user's cached page exists, authenticated users will still see it
    # unless we use a different cache key per authentication state
    return current_user and current_user.is_authenticated


def cache_key_with_auth_state() -> str:
    """Generate cache key that includes authentication state.

    This ensures authenticated and anonymous users get different cached versions
    of the same page, preventing authenticated users from seeing cached anonymous
    pages (and vice versa).
    """
    from flask import request

    # Include the user IDENTITY, not just the auth-or-anon flag. Pages cached
    # under these keys (course take/moderate, etc.) render per-user data —
    # evaluation attempts, certificates, enrollment state — so keying on a
    # shared "auth" bucket serves one member's cached page to every other
    # member the moment a real cache backend (Redis) is configured.
    # (Fork finding U10, offered upstream.)
    if current_user and current_user.is_authenticated:
        auth_state = f"user:{current_user.usuario}"
    else:
        auth_state = "anon"

    # Build key from request path and auth state
    key = f"view/{request.path}/{auth_state}"

    # Include query parameters if present
    if request.query_string:
        key += f"?{request.query_string.decode('utf-8')}"

    return key


def cache_key_with_query_string() -> str:
    """Cache key for public pages whose output varies by query string only.

    Flask-Caching's default view key is ``"view/%s" % request.path`` with
    ``query_string=False``, so ``?tag=x`` collapses onto the unfiltered page and
    one filtered listing is served for another. Use this where the page is the
    same for every visitor but differs by its query parameters; use
    `cache_key_with_auth_state` when the output also depends on who is asking.
    """
    from flask import request

    key = f"view/{request.path}"
    if request.query_string:
        key += f"?{request.query_string.decode('utf-8')}"
    return key


def cache_incr(key: str, timeout: int = 60) -> int:
    """Incrementa un contador en cache de forma atómica.

    Para Redis usa INCR nativo; para otros backends (o si Redis no está
    disponible) realiza get + set manual.
    """
    backend = cache.cache
    client = getattr(backend, "_write_client", None)
    if client is not None:
        try:
            prefix = getattr(backend, "_get_prefix", lambda: "")()
            return client.incr(name=f"{prefix}{key}", amount=1)
        except Exception:
            pass
    current = cache.get(key)
    if current is None:
        current = 1
    else:
        current = int(current) + 1
    cache.set(key, current, timeout=timeout)
    return current


def invalidate_all_cache() -> bool:
    """Invalida toda la cache del sistema cuando cambia el tema."""
    try:
        if CTYPE != "NullCache":
            cache.clear()
            log.trace("Cache invalidated due to theme change")
        return True
    except Exception as e:
        log.error(f"Error invalidating cache: {e}")
        return False


def _obtiene_llaves_generales_cache() -> list[str]:
    """Retorna las llaves comunes de catálogo y página de inicio para invalidación."""
    return [
        # Con doble diagonal
        "view//course/explore/anon",
        "view//course/explore/auth",
        "view//program/explore/anon",
        "view//program/explore/auth",
        "view///anon",
        "view///auth",
        # Con diagonal simple
        "view/course/explore/anon",
        "view/course/explore/auth",
        "view/program/explore/anon",
        "view/program/explore/auth",
        "view//anon",
        "view//auth",
    ]


def invalidar_cache_curso(course_code: str) -> None:
    """Invalidar cache para un curso específico y las vistas relacionadas."""
    if CTYPE == "NullCache":
        return
    try:
        keys_to_delete = [
            f"view//course/{course_code}/view/anon",
            f"view//course/{course_code}/view/auth",
            f"view//course/{course_code}/admin/anon",
            f"view//course/{course_code}/admin/auth",
            f"view//course/{course_code}/take/anon",
            f"view//course/{course_code}/take/auth",
            f"view//course/{course_code}/moderate/anon",
            f"view//course/{course_code}/moderate/auth",
            f"view/course/{course_code}/view/anon",
            f"view/course/{course_code}/view/auth",
            f"view/course/{course_code}/admin/anon",
            f"view/course/{course_code}/admin/auth",
            f"view/course/{course_code}/take/anon",
            f"view/course/{course_code}/take/auth",
            f"view/course/{course_code}/moderate/anon",
            f"view/course/{course_code}/moderate/auth",
        ]
        keys_to_delete.extend(_obtiene_llaves_generales_cache())
        for key in keys_to_delete:
            cache.delete(key)
        log.trace(f"Cache invalidated for course: {course_code}")
    except Exception as e:
        log.error(f"Error invalidating cache for course {course_code}: {e}")


def invalidar_cache_programa(program_code: str) -> None:
    """Invalidar cache para un programa específico y las vistas relacionadas."""
    if CTYPE == "NullCache":
        return
    try:
        keys_to_delete = [
            f"view//program/{program_code}/anon",
            f"view//program/{program_code}/auth",
            f"view/program/{program_code}/anon",
            f"view/program/{program_code}/auth",
        ]
        keys_to_delete.extend(_obtiene_llaves_generales_cache())
        for key in keys_to_delete:
            cache.delete(key)
        log.trace(f"Cache invalidated for program: {program_code}")
    except Exception as e:
        log.error(f"Error invalidating cache for program {program_code}: {e}")


def invalidate_user_course_view_cache(usuario: str, course_code: str) -> None:
    """Drop a member's cached renders of a course's take and view pages.

    Both routes cache per user under ``cache_key_with_auth_state``
    (``view/<path>/user:<usuario>``), and nothing cleared those entries when
    enrollment state changed — so the ordinary sequence "look at a course,
    then enroll" redirected the member straight into their own stale
    pre-enrollment render: a phantom Enroll button, suppressed lesson links,
    and a second enrollment attempt (fork issue #50). Call this after ANY
    commit that changes a member's enrollment state: self-enrollment, payment
    confirmation, admin enrollment, unenrollment, program fan-out, API and
    bulk enrollment.

    Deleting a key that does not exist is a no-op, so callers do not need to
    know whether the member ever warmed the cache.
    """
    for path in (f"/course/{course_code}/take", f"/course/{course_code}/view"):
        cache.delete(f"view/{path}/user:{usuario}")
