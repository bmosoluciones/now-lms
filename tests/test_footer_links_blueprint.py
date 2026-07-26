# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.

"""Tests for the footer links blueprint (enlaces utiles)."""

import pytest


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


class TestFooterLinksAdmin:
    """Tests for admin footer links management."""

    def test_list_links_requires_admin(self, client):
        response = client.get("/admin/enlaces-utiles")
        assert response.status_code in [302, 403]

    def test_list_links_view(self, client_admin):
        response = client_admin.get("/admin/enlaces-utiles")
        assert response.status_code == 200

    def test_create_link_form(self, client_admin):
        response = client_admin.get("/admin/enlaces-utiles/new")
        assert response.status_code == 200

    def test_create_link(self, client_admin, app):
        from now_lms.db import EnlacesUtiles, database

        with app.app_context():
            response = client_admin.post(
                "/admin/enlaces-utiles/new",
                data={
                    "titulo": "New Unique Link",
                    "url": "https://newlink-unique.com",
                    "orden": "2",
                    "activo": "y",
                },
                follow_redirects=True,
            )
            assert response.status_code == 200

            link = database.session.execute(
                database.select(EnlacesUtiles).filter(EnlacesUtiles.titulo == "New Unique Link")
            ).scalar_one_or_none()
            assert link is not None
            assert link.url == "https://newlink-unique.com"

    def test_edit_link(self, client_admin, app):
        from now_lms.db import EnlacesUtiles, database

        with app.app_context():
            link = EnlacesUtiles(titulo="Edit Test Link", url="https://edit-test.com", orden=1, activo=True, creado_por="test")
            database.session.add(link)
            database.session.commit()
            link_id = link.id

            response = client_admin.post(
                f"/admin/enlaces-utiles/{link_id}/edit",
                data={
                    "titulo": "Updated Link",
                    "url": "https://updated-unique.com",
                    "orden": "5",
                    "activo": "y",
                },
                follow_redirects=True,
            )
            assert response.status_code == 200

            updated = database.session.get(EnlacesUtiles, link_id)
            assert updated.titulo == "Updated Link"
            assert updated.url == "https://updated-unique.com"

    def test_delete_link(self, client_admin, app):
        from now_lms.db import EnlacesUtiles, database

        with app.app_context():
            link = EnlacesUtiles(
                titulo="Delete Test Link", url="https://delete-test.com", orden=1, activo=True, creado_por="test"
            )
            database.session.add(link)
            database.session.commit()
            link_id = link.id

            response = client_admin.post(
                f"/admin/enlaces-utiles/{link_id}/delete",
                follow_redirects=True,
            )
            assert response.status_code == 200

            deleted = database.session.get(EnlacesUtiles, link_id)
            assert deleted is None

    def test_edit_nonexistent_link(self, client_admin):
        response = client_admin.get("/admin/enlaces-utiles/nonexistent-id/edit")
        assert response.status_code in [302, 200]

    def test_delete_nonexistent_link(self, client_admin):
        response = client_admin.post(
            "/admin/enlaces-utiles/nonexistent-id/delete",
            follow_redirects=True,
        )
        assert response.status_code == 200
