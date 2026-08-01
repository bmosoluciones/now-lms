# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.

"""Tests for the prior-credentials blueprint (recognition of prior learning).

The authorization tests carry the weight here. Certificate images hold a real
person's name and credential number, and the upload directories this application
autoserves have no authorization at all, so "another learner cannot open my
certificate" is the property most worth protecting against regression.
"""

from io import BytesIO
from itertools import count
from os import path

import pytest

from now_lms.db import PriorCredential, Usuario, database
from now_lms.vistas.prior_credentials import CREDENTIALS_DIR, MAX_UPLOAD_BYTES

VALID_URL = "https://anthropic.skilljar.com/verify/abc123"


_IDENTITY_COUNTER = count(1)


def _make_user(app, label: str, tipo: str = "user") -> tuple[str, str]:
    """Create a user and return (id, username).

    The username carries a per-call suffix so the suite does not depend on the
    harness clearing tables between tests: it passes under in-memory SQLite (fresh
    database per test), file-backed SQLite (no cleanup at all) and PostgreSQL
    (TRUNCATE between tests) alike.
    """
    from now_lms.auth import proteger_passwd

    username = f"{label}{next(_IDENTITY_COUNTER)}"
    with app.app_context():
        user = Usuario(
            usuario=username,
            acceso=proteger_passwd("testpass"),
            nombre=username.title(),
            apellido="Tester",
            correo_electronico=f"{username}@example.com",
            tipo=tipo,
            activo=True,
            correo_electronico_verificado=True,
        )
        database.session.add(user)
        database.session.commit()
        return user.id, username


def _login(client, app, user_id: str):
    """Attach a session for the given user id."""
    with app.test_request_context():
        with client.session_transaction() as sess:
            sess["_user_id"] = user_id
            sess["_fresh"] = True
    return client


def _submit(client, **overrides):
    """POST a credential, with sane defaults."""
    data = {
        "credential_key": "claude-code-101",
        "verification_url": VALID_URL,
        "credential_id": "CC101-0001",
    }
    data.update(overrides)
    return client.post("/my-credentials", data=data, follow_redirects=True)


class TestLearnerSubmission:
    """The learner's own record."""

    def test_page_requires_login(self, client):
        response = client.get("/my-credentials")
        assert response.status_code in (302, 401)

    def test_page_loads_for_learner(self, client, app):
        user_id, learner1_name = _make_user(app, "learner1")
        _login(client, app, user_id)
        assert client.get("/my-credentials").status_code == 200

    def test_valid_submission_is_stored(self, client, app):
        user_id, learner2_name = _make_user(app, "learner2")
        _login(client, app, user_id)

        assert _submit(client).status_code == 200

        with app.app_context():
            row = database.session.execute(
                database.select(PriorCredential).filter_by(usuario=learner2_name)
            ).scalar_one_or_none()
            assert row is not None
            assert row.credential_key == "claude-code-101"
            # The display name is denormalized at submission time.
            assert row.credential_name == "Claude Code 101"
            assert row.verification_url == VALID_URL
            assert row.status == "submitted"
            assert row.image_file is None

    def test_non_https_url_is_rejected(self, client, app):
        user_id, learner3_name = _make_user(app, "learner3")
        _login(client, app, user_id)

        _submit(client, verification_url="http://example.com/cert")

        with app.app_context():
            rows = database.session.execute(database.select(PriorCredential).filter_by(usuario=learner3_name)).scalars().all()
            assert rows == []

    def test_javascript_url_is_rejected(self, client, app):
        """The field renders as an anchor, so a script scheme must never store."""
        user_id, learner4_name = _make_user(app, "learner4")
        _login(client, app, user_id)

        _submit(client, verification_url="javascript:alert(1)")

        with app.app_context():
            rows = database.session.execute(database.select(PriorCredential).filter_by(usuario=learner4_name)).scalars().all()
            assert rows == []

    def test_missing_url_is_rejected(self, client, app):
        user_id, learner5_name = _make_user(app, "learner5")
        _login(client, app, user_id)

        _submit(client, verification_url="")

        with app.app_context():
            rows = database.session.execute(database.select(PriorCredential).filter_by(usuario=learner5_name)).scalars().all()
            assert rows == []

    def test_unknown_credential_key_is_rejected(self, client, app):
        user_id, learner6_name = _make_user(app, "learner6")
        _login(client, app, user_id)

        _submit(client, credential_key="not-a-real-course")

        with app.app_context():
            rows = database.session.execute(database.select(PriorCredential).filter_by(usuario=learner6_name)).scalars().all()
            assert rows == []

    def test_duplicate_course_is_rejected(self, client, app):
        user_id, learner7_name = _make_user(app, "learner7")
        _login(client, app, user_id)

        _submit(client)
        _submit(client, credential_id="CC101-SECOND")

        with app.app_context():
            rows = database.session.execute(database.select(PriorCredential).filter_by(usuario=learner7_name)).scalars().all()
            assert len(rows) == 1
            assert rows[0].credential_id == "CC101-0001"


class TestUploads:
    """The optional certificate attachment."""

    def test_image_is_stored_privately(self, client, app):
        user_id, uploader1_name = _make_user(app, "uploader1")
        _login(client, app, user_id)

        _submit(client, image=(BytesIO(b"fake-png-bytes"), "certificate.png"))

        with app.app_context():
            row = database.session.execute(
                database.select(PriorCredential).filter_by(usuario=uploader1_name)
            ).scalar_one()
            assert row.image_file is not None
            # The stored name comes from the record id, never the client filename.
            assert row.image_file == f"{row.id}.png"
            assert "certificate" not in row.image_file
            assert path.exists(path.join(CREDENTIALS_DIR, row.image_file))

    def test_disallowed_extension_is_rejected(self, client, app):
        user_id, uploader2_name = _make_user(app, "uploader2")
        _login(client, app, user_id)

        _submit(client, image=(BytesIO(b"MZ-not-an-image"), "payload.exe"))

        with app.app_context():
            rows = (
                database.session.execute(database.select(PriorCredential).filter_by(usuario=uploader2_name)).scalars().all()
            )
            assert rows == []

    def test_oversized_upload_is_rejected(self, client, app):
        user_id, uploader3_name = _make_user(app, "uploader3")
        _login(client, app, user_id)

        too_big = BytesIO(b"x" * (MAX_UPLOAD_BYTES + 1))
        _submit(client, image=(too_big, "huge.png"))

        with app.app_context():
            rows = (
                database.session.execute(database.select(PriorCredential).filter_by(usuario=uploader3_name)).scalars().all()
            )
            assert rows == []


class TestImageAuthorization:
    """Who may open a stored certificate. The core security property."""

    @pytest.fixture
    def stored(self, client, app):
        """A learner with one credential and an uploaded image."""
        owner_id, owner_name = _make_user(app, "owner")
        _login(client, app, owner_id)
        _submit(client, image=(BytesIO(b"fake-png-bytes"), "certificate.png"))
        with app.app_context():
            row = database.session.execute(database.select(PriorCredential).filter_by(usuario=owner_name)).scalar_one()
            return {"record_id": row.id, "owner_id": owner_id}

    def test_owner_can_open_it(self, client, app, stored):
        _login(client, app, stored["owner_id"])
        response = client.get(f"/my-credentials/{stored['record_id']}/image")
        assert response.status_code == 200

    def test_another_learner_cannot_open_it(self, client, app, stored):
        intruder_id, intruder_name = _make_user(app, "intruder")
        _login(client, app, intruder_id)
        response = client.get(f"/my-credentials/{stored['record_id']}/image")
        assert response.status_code == 403

    def test_anonymous_cannot_open_it(self, client, app, stored):
        with client.session_transaction() as sess:
            sess.clear()
        response = client.get(f"/my-credentials/{stored['record_id']}/image")
        assert response.status_code in (302, 401)

    def test_staff_can_open_it(self, client, app, stored):
        admin_id, reviewer_name = _make_user(app, "reviewer", tipo="admin")
        _login(client, app, admin_id)
        response = client.get(f"/my-credentials/{stored['record_id']}/image")
        assert response.status_code == 200


class TestDeletion:
    """A learner may remove their own record and nobody else's."""

    def test_owner_can_delete(self, client, app):
        user_id, deleter_name = _make_user(app, "deleter")
        _login(client, app, user_id)
        _submit(client)

        with app.app_context():
            row_id = database.session.execute(
                database.select(PriorCredential).filter_by(usuario=deleter_name)
            ).scalar_one().id

        client.post(f"/my-credentials/{row_id}/delete", follow_redirects=True)

        with app.app_context():
            rows = database.session.execute(database.select(PriorCredential).filter_by(usuario=deleter_name)).scalars().all()
            assert rows == []

    def test_other_learner_cannot_delete(self, client, app):
        owner_id, victim_name = _make_user(app, "victim")
        _login(client, app, owner_id)
        _submit(client)

        with app.app_context():
            row_id = database.session.execute(
                database.select(PriorCredential).filter_by(usuario=victim_name)
            ).scalar_one().id

        attacker_id, attacker_name = _make_user(app, "attacker")
        _login(client, app, attacker_id)
        response = client.post(f"/my-credentials/{row_id}/delete")
        assert response.status_code == 404

        with app.app_context():
            rows = database.session.execute(database.select(PriorCredential).filter_by(usuario=victim_name)).scalars().all()
            assert len(rows) == 1


class TestAdminReview:
    """The staff surface."""

    def test_learner_cannot_reach_admin_list(self, client, app):
        user_id, nosy_name = _make_user(app, "nosy")
        _login(client, app, user_id)
        response = client.get("/admin/prior-credentials")
        assert response.status_code == 403

    def test_admin_sees_the_list(self, client, app):
        learner_id, listed_name = _make_user(app, "listed")
        _login(client, app, learner_id)
        _submit(client)

        admin_id, boss_name = _make_user(app, "boss", tipo="admin")
        _login(client, app, admin_id)
        response = client.get("/admin/prior-credentials")
        assert response.status_code == 200
        assert b"Claude Code 101" in response.data

    def test_review_updates_status(self, client, app):
        learner_id, reviewed_name = _make_user(app, "reviewed")
        _login(client, app, learner_id)
        _submit(client)

        with app.app_context():
            row_id = database.session.execute(
                database.select(PriorCredential).filter_by(usuario=reviewed_name)
            ).scalar_one().id

        admin_id, chief_name = _make_user(app, "chief", tipo="admin")
        _login(client, app, admin_id)
        client.post(
            f"/admin/prior-credentials/{row_id}/review",
            data={"status": "verified", "admin_notes": "Checked the link."},
            follow_redirects=True,
        )

        with app.app_context():
            row = database.session.get(PriorCredential, row_id)
            assert row.status == "verified"
            assert row.admin_notes == "Checked the link."
            assert row.reviewed_by == chief_name
            assert row.reviewed_at is not None

    def test_invalid_status_is_rejected(self, client, app):
        learner_id, unchanged_name = _make_user(app, "unchanged")
        _login(client, app, learner_id)
        _submit(client)

        with app.app_context():
            row_id = database.session.execute(
                database.select(PriorCredential).filter_by(usuario=unchanged_name)
            ).scalar_one().id

        admin_id, director_name = _make_user(app, "director", tipo="admin")
        _login(client, app, admin_id)
        response = client.post(
            f"/admin/prior-credentials/{row_id}/review",
            data={"status": "approved-by-me"},
        )
        assert response.status_code == 400

        with app.app_context():
            assert database.session.get(PriorCredential, row_id).status == "submitted"
