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

"""Test default blog post creation."""

from now_lms.db import BlogPost, database


class TestDefaultBlogPost:
    """Test the default blog post functionality."""

    def test_default_blog_post_created(self, full_db_setup_with_examples):
        """Test that the default blog post is created during initialization."""
        # The default blog post should exist after initialization
        with full_db_setup_with_examples.app_context():
            blog_post = database.session.execute(
                database.select(BlogPost).filter(BlogPost.title == "The Importance of Online Learning in Today's World")
            ).scalar_one_or_none()

            assert blog_post is not None, "Default blog post should exist"
            assert blog_post.status == "published", "Default blog post should be published"
            assert blog_post.allow_comments is True, "Default blog post should allow comments"
            assert "COVID-19 pandemic" in blog_post.content, "Blog post should contain expected content"
            assert "Learning Management System" in blog_post.content, "Blog post should mention LMS"
            assert blog_post.slug == "the-importance-of-online-learning-in-todays-world", "Slug should be correct"

    def test_default_blog_post_has_tags(self, full_db_setup_with_examples):
        """Test that the default blog post has appropriate tags."""
        with full_db_setup_with_examples.app_context():
            blog_post = database.session.execute(
                database.select(BlogPost).filter(BlogPost.title == "The Importance of Online Learning in Today's World")
            ).scalar_one_or_none()

            assert blog_post is not None, "Default blog post should exist"

            tag_names = [tag.name for tag in blog_post.tags]
            expected_tags = ["Online Learning", "Education", "LMS", "Pedagogy", "Andragogy"]

            for expected_tag in expected_tags:
                assert expected_tag in tag_names, f"Tag '{expected_tag}' should be associated with the blog post"

    def test_default_blog_post_accessible_via_web(self, full_db_setup_with_examples):
        """Test that the default blog post is accessible via the web interface."""
        client = full_db_setup_with_examples.test_client()

        # Test the blog index page
        response = client.get("/blog")
        assert response.status_code == 200
        assert b"The Importance of Online Learning" in response.data

        # Test the specific blog post page
        response = client.get("/blog/the-importance-of-online-learning-in-todays-world")
        assert response.status_code == 200
        assert b"COVID-19 pandemic" in response.data
        assert b"Learning Management System" in response.data

    def test_default_blog_post_not_duplicated(self, full_db_setup_with_examples):
        """Test that initializing twice doesn't create duplicate blog posts."""
        with full_db_setup_with_examples.app_context():
            # Count initial blog posts
            initial_count = database.session.execute(database.select(database.func.count(BlogPost.id))).scalar()

            # Try to create the default blog post again
            from now_lms.db.initial_data import crear_blog_post_predeterminado

            crear_blog_post_predeterminado()

            # Count should remain the same
            final_count = database.session.execute(database.select(database.func.count(BlogPost.id))).scalar()

            assert initial_count == final_count, "Should not create duplicate blog posts"
