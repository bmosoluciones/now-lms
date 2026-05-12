# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.

import pytest
import os
from unittest.mock import patch, MagicMock
from now_lms.db import Usuario
from now_lms.db.tools import get_one_record, get_all_records
from tests.test_end_to_end_course_resources import _ultimo_recurso


def test_get_one_record(app, db_session):
    """Test get_one_record helper."""
    # Create a user
    user = Usuario(usuario="test_get_one", acceso=b"pass", nombre="Test", tipo="student", activo=True)
    db_session.add(user)
    db_session.commit()

    # Test with default (primary key)
    record = get_one_record("Usuario", user.id)
    assert record is not None
    assert record.usuario == "test_get_one"

    # Test with specific column
    record = get_one_record("Usuario", "Test", column_name="nombre")
    assert record is not None
    assert record.usuario == "test_get_one"

    # Test with non-existent table
    assert get_one_record("Inexistente", "val") is None

    # Test with non-existent column
    assert get_one_record("Usuario", "val", column_name="inexistente") is None

    # Test with no result
    assert get_one_record("Usuario", "no_existe") is None


def test_get_all_records(app, db_session):
    """Test get_all_records helper."""
    # Create users
    user1 = Usuario(usuario="u1", acceso=b"pass", nombre="N1", tipo="student", activo=True)
    user2 = Usuario(usuario="u2", acceso=b"pass", nombre="N1", tipo="instructor", activo=True)
    db_session.add_all([user1, user2])
    db_session.commit()

    # Test all
    records = get_all_records("Usuario")
    assert len(records) >= 2

    # Test with filter
    records = get_all_records("Usuario", filters={"nombre": "N1"})
    assert len(records) == 2

    records = get_all_records("Usuario", filters={"tipo": "student"})
    assert len(records) == 1
    assert records[0].usuario == "u1"

    # Test filter with non-existent column
    records = get_all_records("Usuario", filters={"inexistente": "val"})
    assert len(records) >= 2  # Should ignore invalid filter and return all

    # Test with non-existent table
    assert get_all_records("Inexistente") is None


def test_debug_redis_endpoint_unconfigured(app):
    """Test debug/redis when not configured."""
    os.environ["NOW_LMS_DEBUG_ENDPOINTS"] = "1"

    # Backup and clear environment variables
    env_backup = {k: os.environ.get(k) for k in ["REDIS_URL", "CACHE_REDIS_URL", "SESSION_REDIS_URL"]}
    for k in env_backup:
        if k in os.environ:
            del os.environ[k]

    try:
        with app.test_client() as client:
            response = client.get("/debug/redis")
            assert response.status_code == 200
            data = response.get_json()
            assert data["status"] == "not_configured"
    finally:
        # Restore environment
        for k, v in env_backup.items():
            if v is not None:
                os.environ[k] = v
        if "NOW_LMS_DEBUG_ENDPOINTS" in os.environ:
            del os.environ["NOW_LMS_DEBUG_ENDPOINTS"]


def test_debug_redis_endpoint_ok(app):
    """Test debug/redis when ok."""
    os.environ["NOW_LMS_DEBUG_ENDPOINTS"] = "1"
    os.environ["REDIS_URL"] = "redis://localhost"

    with patch("redis.from_url") as mock_from_url:
        mock_client = MagicMock()
        mock_from_url.return_value = mock_client
        mock_client.info.return_value = {"redis_version": "7.0", "uptime_in_seconds": 100, "connected_clients": 5}
        mock_client.keys.return_value = ["session:1", "session:2"]

        with app.test_client() as client:
            response = client.get("/debug/redis")
            assert response.status_code == 200
            data = response.get_json()
            assert data["status"] == "ok"
            assert data["session_keys_count"] == 2

    del os.environ["NOW_LMS_DEBUG_ENDPOINTS"]
    del os.environ["REDIS_URL"]


def test_debug_redis_endpoint_error(app):
    """Test debug/redis when error occurs."""
    os.environ["NOW_LMS_DEBUG_ENDPOINTS"] = "1"
    os.environ["REDIS_URL"] = "redis://localhost"

    with patch("redis.from_url") as mock_from_url:
        mock_client = MagicMock()
        mock_from_url.return_value = mock_client
        mock_client.ping.side_effect = Exception("Connection error")

        with app.test_client() as client:
            response = client.get("/debug/redis")
            assert response.status_code == 503
            data = response.get_json()
            assert data["status"] == "error"

    del os.environ["NOW_LMS_DEBUG_ENDPOINTS"]
    del os.environ["REDIS_URL"]


def test_ultimo_recurso_error(app):
    """Test helper _ultimo_recurso with non-existent resource."""
    with app.app_context():
        with pytest.raises(ValueError, match="No se encontró el recurso"):
            _ultimo_recurso("inexistente")
