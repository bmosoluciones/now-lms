# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.

"""Tests for the contact blueprint (contact form and messages)."""

import pytest
from flask import url_for


@pytest.fixture
def admin_user(app):
    """Create and return an admin user for testing."""
    from now_lms.db import database, Usuario

    with app.app_context():
        admin = database.session.execute(database.select(Usuario).filter(Usuario.tipo == "admin")).scalar_one_or_none()
        if not admin:
            pytest.skip("No admin user found in database")
        return admin


@pytest.fixture
def client_admin(client, admin_user, app):
    """Authenticated client as admin."""
    with app.test_request_context():
        with client.session_transaction() as sess:
            sess["_user_id"] = admin_user.id
            sess["_fresh"] = True
    return client


class TestContactForm:
    """Tests for the public contact form."""

    @pytest.fixture(autouse=True)
    def enable_contact(self, app):
        from now_lms.db import Configuracion, database

        with app.app_context():
            config = database.session.execute(database.select(Configuracion)).scalar_one_or_none()
            if config:
                config.enable_contact = True
                database.session.commit()

    def test_contact_page_loads(self, client):
        response = client.get("/contact")
        assert response.status_code == 200

    def test_contact_disabled_redirects(self, client, app):
        from now_lms.db import Configuracion, database

        with app.app_context():
            config = database.session.execute(database.select(Configuracion)).scalar_one_or_none()
            if config:
                config.enable_contact = False
                database.session.commit()

        response = client.get("/contact", follow_redirects=False)
        assert response.status_code == 302
        # Redirects to home page
        assert response.headers["Location"] in {
            "/",
            "http://localhost/",
            "http://localhost.localdomain/",
            "/home",
            "http://localhost/home",
            "http://localhost.localdomain/home",
        }

    def test_contact_form_submission(self, client, app):
        with app.app_context():
            response = client.post(
                "/contact",
                data={
                    "name": "John Doe",
                    "email": "john@example.com",
                    "subject": "Test Subject",
                    "message": "Test message",
                },
                follow_redirects=True,
            )
            assert response.status_code == 200

            from now_lms.db import ContactMessage, database

            msg = database.session.execute(
                database.select(ContactMessage).filter(ContactMessage.email == "john@example.com")
            ).scalar_one_or_none()
            assert msg is not None
            assert msg.name == "John Doe"
            assert msg.status == "not_seen"

    def test_contact_form_validation_empty_fields(self, client):
        response = client.post(
            "/contact",
            data={"name": "", "email": "", "subject": "", "message": ""},
            follow_redirects=True,
        )
        assert response.status_code == 200

    def test_contact_form_max_length(self, client):
        response = client.post(
            "/contact",
            data={
                "name": "x" * 151,
                "email": "test@test.com",
                "subject": "Test",
                "message": "Test",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200


class TestContactMessagesAdmin:
    """Tests for admin contact messages management."""

    def test_list_messages_requires_admin(self, client):
        response = client.get("/admin/contact-messages")
        assert response.status_code in [302, 403]

    def test_list_messages_view(self, client_admin):
        response = client_admin.get("/admin/contact-messages")
        assert response.status_code == 200

    def test_list_messages_filter(self, client_admin, app):
        from now_lms.db import ContactMessage, database

        with app.app_context():
            msg = ContactMessage(
                name="Filter Test", email="filter@test.com", subject="Filter", message="Filter msg", status="not_seen"
            )
            database.session.add(msg)
            database.session.commit()

            response = client_admin.get("/admin/contact-messages?status=not_seen")
            assert response.status_code == 200

    def test_view_message(self, client_admin, app):
        from now_lms.db import ContactMessage, database

        with app.app_context():
            msg = ContactMessage(
                name="View Test", email="view@test.com", subject="View", message="View msg", status="not_seen"
            )
            database.session.add(msg)
            database.session.commit()
            msg_id = msg.id

            response = client_admin.get(f"/admin/contact-messages/{msg_id}/view")
            assert response.status_code == 200

            updated = database.session.get(ContactMessage, msg_id)
            assert updated.status == "seen"

    def test_update_message_status(self, client_admin, app):
        from now_lms.db import ContactMessage, database

        with app.app_context():
            msg = ContactMessage(
                name="Update Test", email="update@test.com", subject="Update", message="Update msg", status="not_seen"
            )
            database.session.add(msg)
            database.session.commit()
            msg_id = msg.id

            response = client_admin.post(
                f"/admin/contact-messages/{msg_id}/view",
                data={"status": "answered", "admin_notes": "Test notes"},
                follow_redirects=True,
            )
            assert response.status_code == 200

            updated = database.session.get(ContactMessage, msg_id)
            assert updated.status == "answered"
            assert updated.admin_notes == "Test notes"
            assert updated.answered_at is not None

    def test_view_nonexistent_message(self, client_admin):
        response = client_admin.get("/admin/contact-messages/nonexistent-id/view")
        assert response.status_code in [302, 200]

    def test_message_url_generation(self, app):
        from now_lms.db import ContactMessage, database

        with app.test_request_context():
            msg = ContactMessage(
                name="URL Test", email="url@test.com", subject="URL Test", message="URL test content", status="not_seen"
            )
            database.session.add(msg)
            database.session.commit()

            view_url = url_for("contact.view_contact_message", message_id=msg.id)
            assert f"/admin/contact-messages/{msg.id}/view" in view_url
