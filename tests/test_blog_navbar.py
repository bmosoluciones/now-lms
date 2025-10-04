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

"""Test blog navbar functionality."""

import pytest
from now_lms.db import Configuracion, database


class TestBlogNavbar:
    """Test blog navbar functionality."""

    def test_blog_enabled_navbar_appears(self, session_full_db_setup):
        """Test that blog link appears in navbar when blog is enabled."""
        client = session_full_db_setup.test_client()

        with session_full_db_setup.app_context():
            # Enable blog
            config = database.session.execute(database.select(Configuracion)).scalar_one()
            config.enable_blog = True
            database.session.commit()

            # Test navbar rendering with blog enabled
            response = client.get("/")
            assert response.status_code == 200

            # Check that blog link is present in the navbar
            response_text = response.get_data(as_text=True)
            assert 'href="/blog"' in response_text or "url_for('blog.blog_index')" in response_text
            # Blog text might appear as "Blog" or localized text

    def test_blog_disabled_navbar_hidden(self, session_full_db_setup):
        """Test that blog link is hidden in navbar when blog is disabled."""
        client = session_full_db_setup.test_client()

        with session_full_db_setup.app_context():
            # Disable blog
            config = database.session.execute(database.select(Configuracion)).scalar_one()
            config.enable_blog = False
            database.session.commit()

            # Test navbar rendering with blog disabled
            response = client.get("/")
            assert response.status_code == 200

            # The response should not contain blog link when disabled
            response_text = response.get_data(as_text=True)
            # We should NOT find a link to /blog in the navbar section
            # But the word "blog" might appear elsewhere so we need to be specific
            lines = response_text.split("\n")
            navbar_lines = []
            in_navbar = False
            for line in lines:
                if "<nav" in line and "navbar" in line:
                    in_navbar = True
                if in_navbar:
                    navbar_lines.append(line)
                if "</nav>" in line and in_navbar:
                    break

            navbar_content = "\n".join(navbar_lines)
            # Check that there's no blog link in the navbar when disabled
            assert 'href="/blog"' not in navbar_content

    def test_is_blog_enabled_function_available_in_templates(self, session_full_db_setup):
        """Test that is_blog_enabled function is available in Jinja templates."""
        with session_full_db_setup.app_context():
            # Test that the function is registered as a global in Jinja
            assert "is_blog_enabled" in session_full_db_setup.jinja_env.globals

            # Test the function can be called from template context
            from now_lms.db.tools import is_blog_enabled

            assert callable(is_blog_enabled)
            result = is_blog_enabled()
            assert isinstance(result, bool)

    def test_is_blog_enabled_with_isolated_session(self, isolated_db_session):
        """Test is_blog_enabled function with isolated session."""
        from now_lms.db.tools import is_blog_enabled

        # Test when blog is enabled
        config = isolated_db_session.execute(database.select(Configuracion)).scalars().first()
        if config:
            config.enable_blog = True
            isolated_db_session.commit()
            assert is_blog_enabled() is True

            config.enable_blog = False
            isolated_db_session.commit()
            assert is_blog_enabled() is False
        else:
            # No config exists, should return False
            assert is_blog_enabled() is False

    @pytest.mark.parametrize(
        "theme",
        [
            "now_lms",
            "amber",
            "cambridge",
            "classic",
            "corporative",
            "golden",
            "harvard",
            "ocean",
            "oxford",
            "sakura",
            "excel",
        ],
    )
    def test_navbar_template_exists_for_all_themes(self, theme):
        """Test that navbar.j2 template exists for all themes."""
        import os

        navbar_path = f"now_lms/templates/themes/{theme}/navbar.j2"
        assert os.path.exists(navbar_path), f"navbar.j2 should exist for theme {theme}"
