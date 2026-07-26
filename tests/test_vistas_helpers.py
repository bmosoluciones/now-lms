# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.

"""Unit tests for vistas helpers (now_lms/vistas/_helpers.py)."""

from unittest import mock

import pytest

from now_lms.db import CustomPage, EnlacesUtiles, Style, database
from now_lms.vistas._helpers import (
    favicon_personalizado,
    get_blog_post_cover_image,
    get_current_course_logo,
    get_custom_pages,
    get_footer_enlaces,
    get_site_favicon,
    get_site_logo,
    logo_personalizado,
)


@pytest.fixture
def mock_public_dir(tmp_path, monkeypatch):
    """Mocks the public files directory with a temporary directory."""
    import now_lms.vistas._helpers as helpers_mod

    monkeypatch.setattr(helpers_mod, "DIRECTORIO_ARCHIVOS_PUBLICOS", str(tmp_path))
    return tmp_path


def test_get_current_course_logo(mock_public_dir):
    """Test getting course-specific logo."""
    course_code = "HELP101"
    course_dir = mock_public_dir / "images" / course_code
    course_dir.mkdir(parents=True, exist_ok=True)

    # When no logo exists
    assert get_current_course_logo(course_code) is None

    # When logo exists
    logo_file = course_dir / "logo.png"
    logo_file.touch()

    assert get_current_course_logo(course_code) == "logo.png"


def test_get_blog_post_cover_image(mock_public_dir):
    """Test getting blog post cover image."""
    post_id = "post123"
    blog_dir = mock_public_dir / "images" / "blog" / post_id

    # When blog dir doesn't exist
    assert get_blog_post_cover_image(post_id) is None

    # Create blog dir
    blog_dir.mkdir(parents=True, exist_ok=True)
    assert get_blog_post_cover_image(post_id) is None

    # Create cover image
    cover_file = blog_dir / "cover.jpg"
    cover_file.touch()

    assert get_blog_post_cover_image(post_id) == "cover.jpg"


def test_get_site_logo_and_favicon(mock_public_dir):
    """Test getting global site logo and favicon."""
    images_dir = mock_public_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    # When they don't exist
    assert get_site_logo() is None
    assert get_site_favicon() is None

    # Create logo and favicon files
    logo_file = images_dir / "logotipo.svg"
    logo_file.touch()
    favicon_file = images_dir / "favicon.ico"
    favicon_file.touch()

    assert get_site_logo() == "logotipo.svg"
    assert get_site_favicon() == "favicon.ico"


def test_logo_and_favicon_personalizado(app, db_session):
    """Test checking if custom logo/favicon is enabled."""
    # First, make sure Style table has a record
    style = db_session.execute(database.select(Style)).scalar_one_or_none()
    if not style:
        style = Style()
        db_session.add(style)

    # Scenario 1: custom_logo/favicon are False
    style.custom_logo = False
    style.custom_favicon = False
    db_session.commit()

    assert logo_personalizado() is False
    assert favicon_personalizado() is False

    # Scenario 2: custom_logo/favicon are True
    style.custom_logo = True
    style.custom_favicon = True
    db_session.commit()

    assert logo_personalizado() is True
    assert favicon_personalizado() is True

    # Scenario 3: Exception during database query
    with mock.patch("now_lms.db.database.session.execute", side_effect=Exception("DB Error")):
        assert logo_personalizado() is False
        assert favicon_personalizado() is False


def test_get_custom_pages_and_enlaces(app, db_session):
    """Test retrieving active footer pages and links."""
    # Create custom pages
    page1 = CustomPage(
        title="Terms of Service Unique Title",
        slug="terms",
        content="Our terms...",
        is_active=True,
        mostrar_en_footer=True,
        creado_por="helper_tester",
    )
    page2 = CustomPage(
        title="Privacy Policy Unique Title",
        slug="privacy",
        content="Our privacy policy...",
        is_active=True,
        mostrar_en_footer=False,  # Not in footer
        creado_por="helper_tester",
    )
    page3 = CustomPage(
        title="About Us Unique Title",
        slug="about",
        content="About our site...",
        is_active=False,  # Inactive
        mostrar_en_footer=True,
        creado_por="helper_tester",
    )
    db_session.add_all([page1, page2, page3])

    # Create useful links
    link1 = EnlacesUtiles(
        titulo="BMO Soluciones Unique Link",
        url="https://bmosoluciones.com",
        activo=True,
        orden=1,
        creado_por="helper_tester",
    )
    link2 = EnlacesUtiles(
        titulo="Disabled Link Unique Link",
        url="https://disabled.com",
        activo=False,  # Inactive
        orden=2,
        creado_por="helper_tester",
    )
    db_session.add_all([link1, link2])
    db_session.commit()

    # Retrieve and check custom pages in footer
    pages = get_custom_pages()
    titles = [p.title for p in pages]
    assert "Terms of Service Unique Title" in titles
    assert "Privacy Policy Unique Title" not in titles
    assert "About Us Unique Title" not in titles

    # Retrieve and check footer links
    links = get_footer_enlaces()
    link_titles = [lnk.titulo for lnk in links]
    assert "BMO Soluciones Unique Link" in link_titles
    assert "Disabled Link Unique Link" not in link_titles


def test_get_custom_pages_and_enlaces_exceptions(app, db_session):
    """Test exceptions handling in footer loaders."""
    with mock.patch("now_lms.db.database.session.execute", side_effect=Exception("DB Error")):
        assert get_custom_pages() == []
        assert get_footer_enlaces() == []
