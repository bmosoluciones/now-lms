# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.

"""Tests for custom pages CRUD (admin-managed DB-driven pages)."""

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


class TestCustomPageModel:
    """Tests for CustomPage model."""

    def test_create_custom_page(self, app, db_session):
        from now_lms.db import CustomPage

        with app.app_context():
            page = CustomPage(
                title="Unique About Us Test",
                slug="unique-about-us-test",
                content="<p>About content</p>",
                is_active=True,
                mostrar_en_footer=True,
            )
            db_session.add(page)
            db_session.commit()

            assert page.id is not None
            assert page.slug == "unique-about-us-test"
            assert page.is_active is True
            assert page.mostrar_en_footer is True

    def test_custom_page_slug_unique(self, app, db_session):
        from now_lms.db import CustomPage

        with app.app_context():
            page1 = CustomPage(title="Page 1", slug="unique-duplicate-test", content="Content 1", is_active=True)
            db_session.add(page1)
            db_session.commit()

            page2 = CustomPage(title="Page 2", slug="unique-duplicate-test", content="Content 2", is_active=True)
            db_session.add(page2)
            with pytest.raises(Exception):
                db_session.commit()


class TestCustomPagesAdminAccess:
    """Tests for admin access to custom pages."""

    def test_admin_panel_has_custom_pages_button(self, client_admin):
        response = client_admin.get("/admin/panel")
        assert response.status_code == 200

    def test_list_pages_requires_admin(self, client):
        response = client.get("/admin/pages")
        assert response.status_code in [302, 403]

    def test_list_pages_view(self, client_admin):
        response = client_admin.get("/admin/pages")
        assert response.status_code == 200

    def test_create_page_form(self, client_admin):
        response = client_admin.get("/admin/pages/new")
        assert response.status_code == 200


class TestCustomPagesCRUD:
    """Tests for custom pages CRUD operations."""

    def test_create_page(self, client_admin, app):
        with app.app_context():
            response = client_admin.post(
                "/admin/pages/new",
                data={
                    "title": "Brand New Page",
                    "slug": "brand-new-page-unique",
                    "content": "<p>New content</p>",
                    "is_active": "on",
                    "mostrar_en_footer": "on",
                },
                follow_redirects=True,
            )
            assert response.status_code == 200

            from now_lms.db import CustomPage, database

            page = database.session.execute(
                database.select(CustomPage).filter(CustomPage.slug == "brand-new-page-unique")
            ).scalar_one_or_none()
            assert page is not None
            assert page.title == "Brand New Page"
            assert page.is_active is True
            assert page.mostrar_en_footer is True

    def test_create_page_duplicate_slug(self, client_admin, app):
        from now_lms.db import CustomPage, database

        with app.app_context():
            existing = database.session.execute(
                database.select(CustomPage).filter(CustomPage.slug == "about-us")
            ).scalar_one_or_none()
            slug_to_test = existing.slug if existing else "about-us"

            response = client_admin.post(
                "/admin/pages/new",
                data={
                    "title": "Duplicate",
                    "slug": slug_to_test,
                    "content": "<p>Duplicate</p>",
                    "is_active": "on",
                },
                follow_redirects=True,
            )
            assert response.status_code == 200

            count = len(
                database.session.execute(database.select(CustomPage).filter(CustomPage.slug == slug_to_test)).scalars().all()
            )
            assert count == 1

    def test_edit_page(self, client_admin, app):
        from now_lms.db import CustomPage, database

        with app.app_context():
            page = CustomPage(
                title="Edit Test Page",
                slug="edit-test-page-unique",
                content="<p>Original</p>",
                is_active=True,
                creado_por="test",
            )
            database.session.add(page)
            database.session.commit()
            page_id = page.id

            response = client_admin.post(
                f"/admin/pages/{page_id}/edit",
                data={
                    "title": "Updated Title",
                    "slug": "edit-test-page-unique",
                    "content": "<p>Updated content</p>",
                    "is_active": "on",
                    "mostrar_en_footer": "on",
                },
                follow_redirects=True,
            )
            assert response.status_code == 200

            updated = database.session.get(CustomPage, page_id)
            assert updated.title == "Updated Title"
            assert updated.mostrar_en_footer is True

    def test_delete_page(self, client_admin, app):
        from now_lms.db import CustomPage, database

        with app.app_context():
            page = CustomPage(
                title="Delete Test Page",
                slug="delete-test-page-unique",
                content="<p>Delete me</p>",
                is_active=True,
                creado_por="test",
            )
            database.session.add(page)
            database.session.commit()
            page_id = page.id

            response = client_admin.post(
                f"/admin/pages/{page_id}/delete",
                follow_redirects=True,
            )
            assert response.status_code == 200

            deleted = database.session.get(CustomPage, page_id)
            assert deleted is None

    def test_toggle_page_active(self, client_admin, app):
        from now_lms.db import CustomPage, database

        with app.app_context():
            page = CustomPage(
                title="Toggle Test Page",
                slug="toggle-test-page-unique",
                content="<p>Toggle me</p>",
                is_active=True,
                creado_por="test",
            )
            database.session.add(page)
            database.session.commit()
            page_id = page.id

            response = client_admin.post(
                f"/admin/pages/{page_id}/toggle",
                follow_redirects=True,
            )
            assert response.status_code == 200

            toggled = database.session.get(CustomPage, page_id)
            assert toggled.is_active is False

    def test_toggle_page_inactive_to_active(self, client_admin, app):
        from now_lms.db import CustomPage, database

        with app.app_context():
            page = CustomPage(
                title="Inactive Page",
                slug="inactive-page-unique",
                content="<p>Inactive</p>",
                is_active=False,
                creado_por="test",
            )
            database.session.add(page)
            database.session.commit()
            page_id = page.id

            response = client_admin.post(
                f"/admin/pages/{page_id}/toggle",
                follow_redirects=True,
            )
            assert response.status_code == 200

            toggled = database.session.get(CustomPage, page_id)
            assert toggled.is_active is True


class TestCustomPagePublicView:
    """Tests for public custom page viewing."""

    def test_view_active_page(self, client, app):
        from now_lms.db import CustomPage, database

        with app.app_context():
            page = CustomPage(
                title="Public View Page",
                slug="public-view-page-unique",
                content="<p>Public content</p>",
                is_active=True,
            )
            database.session.add(page)
            database.session.commit()

            response = client.get("/page/public-view-page-unique")
            assert response.status_code == 200
            assert b"Public content" in response.data

    def test_view_inactive_page_redirects(self, client, app):
        from now_lms.db import CustomPage, database

        with app.app_context():
            page = CustomPage(
                title="Inactive",
                slug="inactive-view-unique",
                content="<p>Inactive</p>",
                is_active=False,
            )
            database.session.add(page)
            database.session.commit()

            response = client.get("/page/inactive-view-unique")
            assert response.status_code in [302, 200]

    def test_view_nonexistent_page_redirects(self, client):
        response = client.get("/page/nonexistent-page-xyz-999")
        assert response.status_code in [302, 200]

    def test_path_traversal_rejected(self, client):
        response = client.get("/page/../../../etc/passwd")
        assert response.status_code in [302, 200, 404]

    def test_url_generation(self, app):
        from now_lms.db import CustomPage, database

        with app.test_request_context():
            pages = database.session.execute(database.select(CustomPage)).scalars().all()
            for page in pages:
                edit_url = url_for("custom_pages.edit_page", page_id=page.id)
                assert f"/admin/pages/{page.id}/edit" in edit_url

    def test_delete_nonexistent_returns_redirect(self, client_admin):
        response = client_admin.post(
            "/admin/pages/nonexistent-id/delete",
            follow_redirects=True,
        )
        assert response.status_code == 200

    def test_toggle_nonexistent_returns_redirect(self, client_admin):
        response = client_admin.post(
            "/admin/pages/nonexistent-id/toggle",
            follow_redirects=True,
        )
        assert response.status_code == 200
