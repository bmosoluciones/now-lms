# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.

"""Unit tests for cache utilities (now_lms/cache_utils.py)."""

import os
import tempfile
from unittest import mock

from flask import Flask

from now_lms.cache_utils import get_memory_cache_config, init_cache


def test_get_memory_cache_config_disabled():
    """Test get_memory_cache_config when memory cache is disabled."""
    with mock.patch.dict(os.environ, {"NOW_LMS_MEMORY_CACHE": "0"}):
        config = get_memory_cache_config()
        assert config == {"CACHE_TYPE": "NullCache"}


def test_get_memory_cache_config_enabled_shm_success():
    """Test get_memory_cache_config when /dev/shm is writeable."""
    with mock.patch.dict(os.environ, {"NOW_LMS_MEMORY_CACHE": "1"}):
        with (
            mock.patch("os.path.exists", return_value=True),
            mock.patch("builtins.open", mock.mock_open()),
            mock.patch("os.remove") as mock_remove,
        ):
            config = get_memory_cache_config()
            assert config["CACHE_TYPE"] == "FileSystemCache"
            assert config["CACHE_DIR"] == "/dev/shm/now_lms_cache"
            mock_remove.assert_called_once()


def test_get_memory_cache_config_shm_fails_temp_success():
    """Test fallback to system temp dir when /dev/shm is not writeable."""
    with mock.patch.dict(os.environ, {"NOW_LMS_MEMORY_CACHE": "1"}):
        # Raise OSError when writing to /dev/shm, but succeed on temp directory
        def side_effect(filename, mode="r", encoding=None):
            if "/dev/shm" in filename:
                raise OSError("No permission")
            return mock.mock_open()()

        with (
            mock.patch("os.path.exists", return_value=False),
            mock.patch("os.makedirs"),
            mock.patch("builtins.open", side_effect=side_effect),
            mock.patch("os.remove"),
        ):
            config = get_memory_cache_config()
            assert config["CACHE_TYPE"] == "FileSystemCache"
            assert config["CACHE_DIR"] == os.path.join(tempfile.gettempdir(), "now_lms_cache")


def test_get_memory_cache_config_all_fail():
    """Test fallback to NullCache when both shm and temp dir fail."""
    with mock.patch.dict(os.environ, {"NOW_LMS_MEMORY_CACHE": "1"}):
        with (
            mock.patch("os.path.exists", return_value=False),
            mock.patch("os.makedirs", side_effect=OSError("Drive full")),
            mock.patch("builtins.open", side_effect=OSError("No write access")),
        ):
            config = get_memory_cache_config()
            assert config == {"CACHE_TYPE": "NullCache"}


def test_init_cache_redis():
    """Test init_cache when Redis environment variables are configured."""
    app = Flask("test_app")
    with mock.patch.dict(os.environ, {"CACHE_REDIS_URL": "redis://localhost:6379/0"}):
        from now_lms.cache import cache

        with mock.patch.object(cache, "init_app") as mock_init_app:
            init_cache(app)
            # The config passed should use RedisCache
            called_config = mock_init_app.call_args[1]["config"]
            assert called_config["CACHE_TYPE"] == "RedisCache"
            assert called_config["CACHE_REDIS_URL"] == "redis://localhost:6379/0"


def test_init_cache_redis_fallback():
    """Test init_cache with REDIS_URL fallback."""
    app = Flask("test_app")
    with mock.patch.dict(os.environ, {"REDIS_URL": "redis://localhost:6379/1"}):
        from now_lms.cache import cache

        with mock.patch.object(cache, "init_app") as mock_init_app:
            init_cache(app)
            called_config = mock_init_app.call_args[1]["config"]
            assert called_config["CACHE_TYPE"] == "RedisCache"
            assert called_config["CACHE_REDIS_URL"] == "redis://localhost:6379/1"


def test_init_cache_memcached():
    """Test init_cache when Memcached servers are configured."""
    app = Flask("test_app")
    with mock.patch.dict(os.environ, {"CACHE_MEMCACHED_SERVERS": "localhost:11211"}):
        from now_lms.cache import cache

        with mock.patch.object(cache, "init_app") as mock_init_app:
            init_cache(app)
            called_config = mock_init_app.call_args[1]["config"]
            assert called_config["CACHE_TYPE"] == "MemcachedCache"
            assert called_config["CACHE_MEMCACHED_SERVERS"] == "localhost:11211"


def test_init_cache_app_overrides():
    """Test init_cache respects explicitly set app config overrides."""
    app = Flask("test_app")
    app.config["CACHE_TYPE"] = "SimpleCache"
    app.config["CACHE_THRESHOLD"] = 1000

    from now_lms.cache import cache

    with mock.patch.object(cache, "init_app") as mock_init_app:
        init_cache(app)
        called_config = mock_init_app.call_args[1]["config"]
        assert called_config["CACHE_TYPE"] == "SimpleCache"
        assert called_config["CACHE_THRESHOLD"] == 1000


def test_init_cache_exception_fallback():
    """Test that cache initialization exception falls back to NullCache."""
    app = Flask("test_app")
    from now_lms.cache import cache

    with mock.patch.object(cache, "init_app", side_effect=[Exception("Initialization failed"), None]) as mock_init_app:
        init_cache(app)
        # Should be called twice (the first fail, then fallback)
        assert mock_init_app.call_count == 2
        # The second call must be with NullCache
        last_called_config = mock_init_app.call_args_list[-1][1]["config"]
        assert last_called_config == {"CACHE_TYPE": "NullCache"}


def test_invalidar_cache_curso():
    """Test that invalidar_cache_curso calls cache.delete with the expected keys."""
    from now_lms.cache import invalidar_cache_curso, cache

    with mock.patch.object(cache, "delete") as mock_delete:
        invalidar_cache_curso("test-course-code")

        # Verify that expected keys are deleted
        expected_keys = [
            "view//course/test-course-code/view/auth",
            "view//course/test-course-code/view/anon",
            "view//course/test-course-code/admin/auth",
            "view//course/test-course-code/admin/anon",
            "view//course/test-course-code/take/auth",
            "view//course/test-course-code/take/anon",
            "view//course/test-course-code/moderate/auth",
            "view//course/test-course-code/moderate/anon",
            "view//course/explore/auth",
            "view//course/explore/anon",
            "view//course/explore",
            "view///auth",
            "view///anon",
            "view//home/auth",
            "view//home/anon",
            "view//home",
        ]

        # Check that cache.delete was called for each expected key
        called_keys = [args[0] for args, _ in mock_delete.call_args_list]
        for key in expected_keys:
            assert key in called_keys


def test_no_guardar_en_cache_global_authenticated():
    """Test that no_guardar_en_cache_global returns True if user is authenticated."""
    from now_lms.cache import no_guardar_en_cache_global
    # Mock current_user as authenticated
    mock_user = mock.MagicMock()
    mock_user.is_authenticated = True
    with mock.patch("now_lms.cache.current_user", mock_user):
        assert no_guardar_en_cache_global() is True


def test_no_guardar_en_cache_global_anonymous():
    """Test that no_guardar_en_cache_global returns False if user is anonymous or not authenticated."""
    from now_lms.cache import no_guardar_en_cache_global
    # Mock current_user as anonymous
    mock_user = mock.MagicMock()
    mock_user.is_authenticated = False
    with mock.patch("now_lms.cache.current_user", mock_user):
        assert no_guardar_en_cache_global() is False

    with mock.patch("now_lms.cache.current_user", None):
        assert no_guardar_en_cache_global() is False


def test_detect_cache_invalidations_curso():
    """Test that detect_cache_invalidations correctly detects modified courses and registers them."""
    from now_lms.db import detect_cache_invalidations

    # Mock some model instances
    mock_curso = mock.MagicMock()
    mock_curso.__class__.__name__ = "Curso"
    mock_curso.codigo = "test-course"

    mock_seccion = mock.MagicMock()
    mock_seccion.__class__.__name__ = "CursoSeccion"
    mock_seccion.curso = "test-course-sec"

    mock_recurso = mock.MagicMock()
    mock_recurso.__class__.__name__ = "CursoRecurso"
    mock_recurso.curso = "test-course-rec"

    mock_programa = mock.MagicMock()
    mock_programa.__class__.__name__ = "Programa"
    mock_programa.codigo = "test-program"

    # Mock session
    mock_session = mock.MagicMock()
    mock_session.new = [mock_curso]
    mock_session.dirty = [mock_seccion, mock_recurso]
    mock_session.deleted = [mock_programa]
    mock_session.info = {}

    detect_cache_invalidations(mock_session)

    assert mock_session.info["courses_to_invalidate"] == {"test-course", "test-course-sec", "test-course-rec"}
    assert mock_session.info["programs_to_invalidate"] == {"test-program"}


def test_trigger_cache_invalidations():
    """Test that trigger_cache_invalidations calls invalidar_cache_curso and invalidar_cache_programa."""
    from now_lms.db import trigger_cache_invalidations

    mock_session = mock.MagicMock()
    mock_session.info = {
        "courses_to_invalidate": {"test-course"},
        "programs_to_invalidate": {"test-program"}
    }

    with mock.patch("now_lms.cache.invalidar_cache_curso") as mock_invalidar_curso, \
         mock.patch("now_lms.cache.invalidar_cache_programa") as mock_invalidar_programa:
        trigger_cache_invalidations(mock_session)
        mock_invalidar_curso.assert_called_once_with("test-course")
        mock_invalidar_programa.assert_called_once_with("test-program")

    assert "courses_to_invalidate" not in mock_session.info
    assert "programs_to_invalidate" not in mock_session.info


def test_invalidar_cache_programa():
    """Test that invalidar_cache_programa calls cache.delete with the expected keys."""
    from now_lms.cache import invalidar_cache_programa, cache

    with mock.patch.object(cache, "delete") as mock_delete:
        invalidar_cache_programa("test-program-code")

        # Verify that expected keys are deleted
        expected_keys = [
            "view//program/test-program-code/auth",
            "view//program/test-program-code/anon",
            "view//program/explore/auth",
            "view//program/explore/anon",
            "view//program/explore",
            "view//program/list",
            "view///auth",
            "view///anon",
            "view//home/auth",
            "view//home/anon",
            "view//home",
        ]

        # Check that cache.delete was called for each expected key
        called_keys = [args[0] for args, _ in mock_delete.call_args_list]
        for key in expected_keys:
            assert key in called_keys
