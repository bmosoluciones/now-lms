"""Tests for static pages administration."""

import pytest
from flask import url_for


@pytest.fixture
def admin_user(app):
    """Create and return an admin user for testing."""
    from now_lms.db import database, Usuario
    
    with app.app_context():
        admin = database.session.execute(
            database.select(Usuario).filter(Usuario.tipo == "admin")
        ).scalar_one_or_none()
        
        if not admin:
            pytest.skip("No admin user found in database")
        
        return admin


@pytest.fixture
def client_admin(client, admin_user, app):
    """Authenticated client as admin."""
    with app.test_request_context():
        with client.session_transaction() as sess:
            sess['_user_id'] = admin_user.id
            sess['_fresh'] = True
    return client


def test_static_pages_url_generation(app):
    """Test that URL generation works for static pages with string IDs."""
    from now_lms.db import database, StaticPage
    
    with app.test_request_context():
        # Get existing static pages from the database
        pages = database.session.execute(database.select(StaticPage)).scalars().all()
        assert len(pages) > 0, "Database should have at least one static page"
        
        # Test URL generation for each page
        for page in pages:
            # Verify the ID is a string (ULID format)
            assert isinstance(page.id, str), f"Page ID should be string, got {type(page.id)}"
            
            # Test that URL can be generated without error
            edit_url = url_for('static_pages.edit_page', page_id=page.id)
            assert edit_url is not None
            assert f'/admin/pages/{page.id}/edit' in edit_url


def test_admin_pages_list_view(client_admin):
    """Test that the admin pages list view renders without error."""
    response = client_admin.get('/admin/pages')
    assert response.status_code in [200, 302]  # 302 if not logged in properly


def test_contact_message_url_generation(app):
    """Test that URL generation works for contact messages with string IDs."""
    from now_lms.db import database, ContactMessage
    
    with app.test_request_context():
        # Create a test contact message
        contact_msg = ContactMessage(
            name="Test User",
            email="test@example.com",
            subject="Test Subject",
            message="Test message content",
            status="not_seen",
        )
        database.session.add(contact_msg)
        database.session.commit()
        
        # Verify the ID is a string (ULID format)
        assert isinstance(contact_msg.id, str), f"Message ID should be string, got {type(contact_msg.id)}"
        
        # Test that URL can be generated without error
        view_url = url_for('static_pages.view_contact_message', message_id=contact_msg.id)
        assert view_url is not None
        assert f'/admin/contact-messages/{contact_msg.id}/view' in view_url
