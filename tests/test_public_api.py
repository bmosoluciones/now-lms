# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
import hashlib
import uuid
import pytest
from now_lms.db import ExternalApiKey, RemoteEnrollmentRequest, Curso, database, ContactMessage


@pytest.fixture
def api_key(app, db_session):
    key_plain = "test-api-key-123"
    key_hash = hashlib.sha256(key_plain.encode()).hexdigest()
    new_key = ExternalApiKey(name="Test Harbor", key_hash=key_hash, active=True)
    database.session.add(new_key)
    database.session.commit()
    return key_plain


@pytest.fixture
def active_course(app, db_session):
    course = Curso(
        codigo="HARBOR_TEST",
        nombre="Test Course for Harbor",
        descripcion_corta="Short Description",
        descripcion="Test Description",
        estado="open",
        publico=True,
        duracion=10,
        certificado=True,
        recertification_required=True,
        recertification_period_years=2,
    )
    database.session.add(course)
    database.session.commit()
    return course


def test_ping_unauthenticated(client):
    response = client.get("/api/v1/public/ping")
    assert response.status_code == 401


def test_ping_authenticated(client, api_key):
    response = client.get("/api/v1/public/ping", headers={"Authorization": f"Bearer {api_key}"})
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "ok"
    assert data["service"] == "NOW LMS"


def test_get_course_not_found(client, api_key):
    response = client.get("/api/v1/public/courses/NON_EXISTENT", headers={"X-API-Key": api_key})
    assert response.status_code == 404
    data = response.get_json()
    assert data["error"] == "course_not_found"


def test_get_course_success(client, api_key, active_course):
    response = client.get(f"/api/v1/public/courses/{active_course.codigo}", headers={"X-API-Key": api_key})
    assert response.status_code == 200
    data = response.get_json()
    assert data["code"] == active_course.codigo
    assert data["title"] == active_course.nombre
    assert data["recertification_required"] is True


def test_enrollment_invalid_payload(client, api_key):
    response = client.post(
        "/api/v1/public/enrollments", headers={"Authorization": f"Bearer {api_key}"}, json={"email": "test@example.com"}
    )
    assert response.status_code == 400


def test_enrollment_payment_not_confirmed(client, api_key, active_course):
    payload = {
        "request_id": str(uuid.uuid4()),
        "course_code": active_course.codigo,
        "email": "newuser@example.com",
        "payment_confirmed": False,
    }
    response = client.post("/api/v1/public/enrollments", headers={"Authorization": f"Bearer {api_key}"}, json=payload)
    assert response.status_code == 400


def test_enrollment_new_user(client, api_key, active_course):
    from now_lms import mail
    from now_lms.db import MailConfig

    # Mock mail config as verified
    mail_config = database.session.execute(database.select(MailConfig)).scalar_one_or_none()
    if not mail_config:
        mail_config = MailConfig(MAIL_DEFAULT_SENDER="noreply@example.com")
        database.session.add(mail_config)
    mail_config.email_verificado = True
    database.session.commit()

    with mail.record_messages() as outbox:
        request_id = str(uuid.uuid4())
        email = "newuser@example.com"
        payload = {
            "request_id": request_id,
            "course_code": active_course.codigo,
            "email": email,
            "payment_confirmed": True,
            "_sync_email": True,
        }
        response = client.post("/api/v1/public/enrollments", headers={"Authorization": f"Bearer {api_key}"}, json=payload)
        assert response.status_code == 201
        data = response.get_json()
        assert data["status"] == "enrolled"
        assert data["user_status"] == "pending_verification"

        # Check if audit record exists
        audit = database.session.query(RemoteEnrollmentRequest).filter_by(request_id=request_id).first()
        assert audit is not None
        assert audit.status == "processed"

        # Check email sent
        assert len(outbox) > 0
        assert email in outbox[0].recipients


def test_enrollment_idempotency(client, api_key, active_course):
    request_id = str(uuid.uuid4())
    payload = {
        "request_id": request_id,
        "course_code": active_course.codigo,
        "email": "idempotent@example.com",
        "payment_confirmed": True,
    }
    # First call
    client.post("/api/v1/public/enrollments", headers={"X-API-Key": api_key}, json=payload)

    # Second call
    response = client.post("/api/v1/public/enrollments", headers={"X-API-Key": api_key}, json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "already_processed"


def test_revoke_api_key_hotspot_fix(client, db_session):
    # Setup: Login as admin
    from now_lms.db.data_test import crear_data_para_pruebas, USUARIO_ADMINISTRADOR

    crear_data_para_pruebas()

    # Get admin credentials
    import os

    admin_password = os.environ.get("ADMIN_PSWD") or "lms-admin"
    client.post("/user/login", data={"usuario": USUARIO_ADMINISTRADOR, "acceso": admin_password})

    # Create a key to revoke
    key = ExternalApiKey(name="Revoke Me", key_hash="some-hash", active=True)
    database.session.add(key)
    database.session.commit()
    key_id = key.id

    # Try revoking via GET (should be 405 Method Not Allowed)
    response = client.get(f"/setting/api_keys/{key_id}/revoke")
    assert response.status_code == 405

    # Revoke via POST
    response = client.post(f"/setting/api_keys/{key_id}/revoke", follow_redirects=True)
    assert response.status_code == 200

    # Verify revoked
    database.session.expire_all()
    key = database.session.get(ExternalApiKey, key_id)
    assert key.active is False
    assert key.revoked_at is not None


def test_contact_messages_require_auth(client):
    # GET list unread should require API Key
    response = client.get("/api/v1/public/contact-messages")
    assert response.status_code == 401

    # POST read should require API Key
    response = client.post("/api/v1/public/contact-messages/some-id/read")
    assert response.status_code == 401


def test_list_unread_contact_messages_success(client, api_key, app):
    with app.app_context():
        # Create unread contact message
        msg1 = ContactMessage(
            name="Alice",
            email="alice@example.com",
            subject="Question",
            message="How to register?",
            status="not_seen",
        )
        # Create seen contact message (should not be returned)
        msg2 = ContactMessage(
            name="Bob",
            email="bob@example.com",
            subject="Offer",
            message="Commercial proposal",
            status="seen",
        )
        database.session.add_all([msg1, msg2])
        database.session.commit()
        msg1_id = msg1.id

    response = client.get("/api/v1/public/contact-messages", headers={"Authorization": f"Bearer {api_key}"})
    assert response.status_code == 200
    data = response.get_json()

    assert len(data) >= 1
    # Check that msg1 is in the response but msg2 is not
    names = [item["name"] for item in data]
    assert "Alice" in names
    assert "Bob" not in names

    # Verify response structure
    alice_msg = next(item for item in data if item["id"] == msg1_id)
    assert alice_msg["email"] == "alice@example.com"
    assert alice_msg["subject"] == "Question"
    assert alice_msg["message"] == "How to register?"
    assert alice_msg["status"] == "not_seen"
    assert alice_msg["created_at"] is not None


def test_mark_contact_message_read_success(client, api_key, app):
    with app.app_context():
        msg = ContactMessage(
            name="Charlie",
            email="charlie@example.com",
            subject="Feedback",
            message="Great course!",
            status="not_seen",
        )
        database.session.add(msg)
        database.session.commit()
        msg_id = msg.id

    # Mark as read via API
    response = client.post(f"/api/v1/public/contact-messages/{msg_id}/read", headers={"X-API-Key": api_key})
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "success"
    assert data["new_status"] == "seen"

    # Verify status in database
    with app.app_context():
        db_msg = database.session.get(ContactMessage, msg_id)
        assert db_msg.status == "seen"


def test_mark_contact_message_read_not_found(client, api_key):
    response = client.post("/api/v1/public/contact-messages/invalid-id/read", headers={"X-API-Key": api_key})
    assert response.status_code == 404
    data = response.get_json()
    assert data["error"] == "message_not_found"
