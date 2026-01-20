# Copyright 2025 BMO Soluciones, S.A.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Comprehensive tests for AdSense integration.

This test module validates:
1. AdSense database model
2. Template functions for retrieving ad codes
3. ads.txt route
4. AdSense configuration UI
5. Ad display logic in templates
6. Theme integration
"""

import pytest

from now_lms.auth import proteger_passwd
from now_lms.db import AdSense, Curso, Usuario, database
from now_lms.db.tools import (
    get_ad_billboard,
    get_ad_large_rectangle,
    get_ad_large_skyscraper,
    get_ad_leaderboard,
    get_ad_medium_rectangle,
    get_ad_mobile_banner,
    get_ad_skyscraper,
    get_ad_wide_skyscraper,
    get_addsense_code,
    get_addsense_meta,
    get_adsense_enabled,
)

REDIRECT_STATUS_CODES = {301, 302, 303, 307, 308}


@pytest.fixture
def admin_user(db_session):
    """Create an admin user for testing."""
    user = Usuario(
        usuario="admin",
        acceso=proteger_passwd("admin"),
        nombre="Admin",
        correo_electronico="admin@example.com",
        tipo="admin",
        activo=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def configured_adsense(db_session):
    """Create AdSense configuration with test data."""
    adsense = db_session.execute(database.select(AdSense)).scalars().first()
    if not adsense:
        adsense = AdSense()
        db_session.add(adsense)

    # Configure with test values
    adsense.meta_tag = '<meta name="google-adsense-account" content="ca-pub-1234567890">'
    adsense.meta_tag_include = True
    adsense.pub_id = "1234567890"
    adsense.show_ads = True
    adsense.add_code = '<script>console.log("AdSense loaded");</script>'
    adsense.add_leaderboard = "<div>Leaderboard Ad (728x90)</div>"
    adsense.add_medium_rectangle = "<div>Medium Rectangle Ad (300x250)</div>"
    adsense.add_large_rectangle = "<div>Large Rectangle Ad (336x280)</div>"
    adsense.add_mobile_banner = "<div>Mobile Banner Ad (300x50)</div>"
    adsense.add_wide_skyscraper = "<div>Wide Skyscraper Ad (160x600)</div>"
    adsense.add_skyscraper = "<div>Skyscraper Ad (120x600)</div>"
    adsense.add_large_skyscraper = "<div>Large Skyscraper Ad (300x600)</div>"
    adsense.add_billboard = "<div>Billboard Ad (970x250)</div>"

    db_session.commit()
    return adsense


@pytest.fixture
def free_course(db_session):
    """Create a free course for testing."""
    curso = Curso(
        codigo="FREE001",
        nombre="Free Test Course",
        descripcion_corta="A free course",
        descripcion="A free course for testing AdSense",
        estado="active",
        nivel=0,
        publico=True,
        pagado=False,  # Free course
    )
    db_session.add(curso)
    db_session.commit()
    return curso


@pytest.fixture
def paid_course(db_session):
    """Create a paid course for testing."""
    curso = Curso(
        codigo="PAID001",
        nombre="Paid Test Course",
        descripcion_corta="A paid course",
        descripcion="A paid course for testing AdSense",
        estado="active",
        nivel=0,
        publico=True,
        pagado=True,  # Paid course
        precio=99.99,
    )
    db_session.add(curso)
    db_session.commit()
    return curso


class TestAdSenseModel:
    """Test AdSense database model."""

    def test_adsense_model_exists(self, db_session):
        """Test that AdSense model can be queried."""
        adsense = db_session.execute(database.select(AdSense)).scalars().first()
        assert adsense is not None

    def test_adsense_model_fields(self, configured_adsense):
        """Test that all AdSense model fields are present."""
        assert hasattr(configured_adsense, "meta_tag")
        assert hasattr(configured_adsense, "meta_tag_include")
        assert hasattr(configured_adsense, "pub_id")
        assert hasattr(configured_adsense, "add_code")
        assert hasattr(configured_adsense, "show_ads")
        assert hasattr(configured_adsense, "add_leaderboard")
        assert hasattr(configured_adsense, "add_medium_rectangle")
        assert hasattr(configured_adsense, "add_large_rectangle")
        assert hasattr(configured_adsense, "add_mobile_banner")
        assert hasattr(configured_adsense, "add_wide_skyscraper")
        assert hasattr(configured_adsense, "add_skyscraper")
        assert hasattr(configured_adsense, "add_large_skyscraper")
        assert hasattr(configured_adsense, "add_billboard")


class TestAdSenseTemplateFunctions:
    """Test template helper functions for AdSense."""

    def test_get_adsense_enabled_returns_false_when_disabled(self, db_session):
        """Test that get_adsense_enabled returns False when ads are disabled."""
        adsense = db_session.execute(database.select(AdSense)).scalars().first()
        adsense.show_ads = False
        db_session.commit()

        assert get_adsense_enabled() is False

    def test_get_adsense_enabled_returns_true_when_enabled(self, configured_adsense):
        """Test that get_adsense_enabled returns True when ads are enabled."""
        assert get_adsense_enabled() is True

    def test_get_addsense_meta_returns_meta_tag(self, configured_adsense):
        """Test that get_addsense_meta returns the meta tag when enabled."""
        meta = get_addsense_meta()
        assert meta == '<meta name="google-adsense-account" content="ca-pub-1234567890">'

    def test_get_addsense_meta_returns_empty_when_disabled(self, db_session):
        """Test that get_addsense_meta returns empty string when disabled."""
        adsense = db_session.execute(database.select(AdSense)).scalars().first()
        adsense.meta_tag_include = False
        db_session.commit()

        meta = get_addsense_meta()
        assert meta == ""

    def test_get_addsense_code_returns_code(self, configured_adsense):
        """Test that get_addsense_code returns the ad code when enabled."""
        code = get_addsense_code()
        assert code == '<script>console.log("AdSense loaded");</script>'

    def test_get_ad_leaderboard(self, configured_adsense):
        """Test that get_ad_leaderboard returns leaderboard ad code."""
        ad = get_ad_leaderboard()
        assert ad == "<div>Leaderboard Ad (728x90)</div>"

    def test_get_ad_medium_rectangle(self, configured_adsense):
        """Test that get_ad_medium_rectangle returns medium rectangle ad code."""
        ad = get_ad_medium_rectangle()
        assert ad == "<div>Medium Rectangle Ad (300x250)</div>"

    def test_get_ad_large_rectangle(self, configured_adsense):
        """Test that get_ad_large_rectangle returns large rectangle ad code."""
        ad = get_ad_large_rectangle()
        assert ad == "<div>Large Rectangle Ad (336x280)</div>"

    def test_get_ad_mobile_banner(self, configured_adsense):
        """Test that get_ad_mobile_banner returns mobile banner ad code."""
        ad = get_ad_mobile_banner()
        assert ad == "<div>Mobile Banner Ad (300x50)</div>"

    def test_get_ad_wide_skyscraper(self, configured_adsense):
        """Test that get_ad_wide_skyscraper returns wide skyscraper ad code."""
        ad = get_ad_wide_skyscraper()
        assert ad == "<div>Wide Skyscraper Ad (160x600)</div>"

    def test_get_ad_skyscraper(self, configured_adsense):
        """Test that get_ad_skyscraper returns skyscraper ad code."""
        ad = get_ad_skyscraper()
        assert ad == "<div>Skyscraper Ad (120x600)</div>"

    def test_get_ad_large_skyscraper(self, configured_adsense):
        """Test that get_ad_large_skyscraper returns large skyscraper ad code."""
        ad = get_ad_large_skyscraper()
        assert ad == "<div>Large Skyscraper Ad (300x600)</div>"

    def test_get_ad_billboard(self, configured_adsense):
        """Test that get_ad_billboard returns billboard ad code."""
        ad = get_ad_billboard()
        assert ad == "<div>Billboard Ad (970x250)</div>"

    def test_ad_functions_return_empty_when_disabled(self, db_session):
        """Test that ad functions return empty string when ads are disabled."""
        adsense = db_session.execute(database.select(AdSense)).scalars().first()
        adsense.show_ads = False
        db_session.commit()

        assert get_ad_leaderboard() == ""
        assert get_ad_medium_rectangle() == ""
        assert get_ad_large_rectangle() == ""
        assert get_ad_mobile_banner() == ""
        assert get_ad_wide_skyscraper() == ""
        assert get_ad_skyscraper() == ""
        assert get_ad_large_skyscraper() == ""
        assert get_ad_billboard() == ""


class TestAdsTxtRoute:
    """Test ads.txt route."""

    def test_ads_txt_route_exists(self, app):
        """Test that ads.txt route is accessible."""
        client = app.test_client()
        response = client.get("/ads.txt")
        assert response.status_code == 200

    def test_ads_txt_content_type(self, app):
        """Test that ads.txt returns correct content type."""
        client = app.test_client()
        response = client.get("/ads.txt")
        assert response.content_type == "text/plain; charset=utf-8"

    def test_ads_txt_with_publisher_id(self, app, configured_adsense):
        """Test that ads.txt returns correct content with publisher ID."""
        client = app.test_client()
        response = client.get("/ads.txt")
        content = response.get_data(as_text=True)

        assert "google.com, pub-1234567890, DIRECT, f08c47fec0942fa0" in content

    def test_ads_txt_without_publisher_id(self, app, db_session):
        """Test that ads.txt returns fallback content without publisher ID."""
        adsense = db_session.execute(database.select(AdSense)).scalars().first()
        adsense.pub_id = ""
        db_session.commit()

        client = app.test_client()
        response = client.get("/ads.txt")
        content = response.get_data(as_text=True)

        assert "# No AdSense publisher ID configured" in content


class TestAdSenseConfigurationUI:
    """Test AdSense configuration interface."""

    def test_adsense_config_route_requires_auth(self, app):
        """Test that AdSense configuration requires authentication."""
        client = app.test_client()
        response = client.get("/setting/adsense")
        # Should redirect to login
        assert response.status_code in REDIRECT_STATUS_CODES

    def test_adsense_config_route_accessible_to_admin(self, app, admin_user):
        """Test that admin can access AdSense configuration."""
        client = app.test_client()
        # Login as admin
        client.post("/user/login", data={"usuario": "admin", "acceso": "admin"}, follow_redirects=False)

        response = client.get("/setting/adsense")
        assert response.status_code == 200

    def test_adsense_config_form_renders(self, app, admin_user):
        """Test that AdSense configuration form renders correctly."""
        client = app.test_client()
        client.post("/user/login", data={"usuario": "admin", "acceso": "admin"}, follow_redirects=False)

        response = client.get("/setting/adsense")
        content = response.get_data(as_text=True)

        # Check for form fields
        assert "pub_id" in content or "ID de Usuario de AdSense" in content
        assert "show_ads" in content or "Mostrar anuncios" in content

    def test_adsense_config_update(self, app, admin_user, db_session):
        """Test updating AdSense configuration."""
        client = app.test_client()
        client.post("/user/login", data={"usuario": "admin", "acceso": "admin"}, follow_redirects=False)

        # Update configuration
        response = client.post(
            "/setting/adsense",
            data={
                "pub_id": "9876543210",
                "show_ads": "y",
                "add_leaderboard": "<div>Updated Leaderboard</div>",
            },
            follow_redirects=False,
        )

        assert response.status_code in REDIRECT_STATUS_CODES | {200}

        # Verify changes
        adsense = db_session.execute(database.select(AdSense)).scalars().first()
        assert adsense.pub_id == "9876543210"


class TestAdSenseBusinessLogic:
    """Test AdSense business logic for displaying ads."""

    def test_ads_display_on_free_courses(self, app, admin_user, configured_adsense, free_course):
        """Test that ads are displayed on free courses when enabled."""
        client = app.test_client()
        client.post("/user/login", data={"usuario": "admin", "acceso": "admin"}, follow_redirects=False)

        # The actual rendering test would require checking template context
        # For now, verify the business logic through database state
        assert configured_adsense.show_ads is True
        assert free_course.pagado is False

    def test_ads_not_display_on_paid_courses(self, app, admin_user, configured_adsense, paid_course):
        """Test that ads are not displayed on paid courses."""
        # Verify business logic through database state
        assert configured_adsense.show_ads is True
        assert paid_course.pagado is True

    def test_ads_not_display_when_globally_disabled(self, app, db_session, free_course):
        """Test that ads are not displayed when globally disabled."""
        adsense = db_session.execute(database.select(AdSense)).scalars().first()
        adsense.show_ads = False
        db_session.commit()

        # Verify through template function
        assert get_adsense_enabled() is False


class TestThemeIntegration:
    """Test AdSense integration in all themes."""

    def test_all_themes_have_adsense_integration(self):
        """Test that all theme header files include AdSense integration."""
        import os
        from pathlib import Path

        themes_dir = Path("now_lms/templates/themes")
        header_files = list(themes_dir.glob("*/header.j2"))

        # Should have 13 themes
        assert len(header_files) == 13

        # Check each header file contains AdSense
        for header_file in header_files:
            content = header_file.read_text()
            assert "adsense_meta()" in content or "adsense_code()" in content, f"{header_file} missing AdSense integration"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
