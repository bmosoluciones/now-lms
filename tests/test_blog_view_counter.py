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

"""Test blog view counter functionality."""

import json
from now_lms.db import BlogPost, database


class TestBlogViewCounter:
    """Test the blog view counter feature."""

    def test_blog_post_has_view_count_field(self, session_full_db_setup_with_examples):
        """Test that blog posts have a view_count field."""
        with session_full_db_setup_with_examples.app_context():
            blog_post = (
                database.session.execute(database.select(BlogPost).filter(BlogPost.status == "published")).scalars().first()
            )

            assert blog_post is not None, "There should be at least one published blog post"
            assert hasattr(blog_post, "view_count"), "BlogPost should have view_count attribute"
            assert blog_post.view_count is not None, "view_count should not be None"
            assert isinstance(blog_post.view_count, int), "view_count should be an integer"

    def test_new_blog_post_has_zero_views(self, session_full_db_setup_with_examples):
        """Test that new blog posts start with zero views."""
        with session_full_db_setup_with_examples.app_context():
            # Create a new blog post
            blog_post = BlogPost(
                title="Test Post for Views",
                slug="test-post-for-views",
                content="This is a test post",
                author_id="lms-admin",
                status="published",
            )
            database.session.add(blog_post)
            database.session.commit()

            # Check that view count starts at 0
            assert blog_post.view_count == 0, "New blog posts should have 0 views"

    def test_count_view_endpoint_exists(self, session_full_db_setup_with_examples):
        """Test that the count_view endpoint exists and works."""
        client = session_full_db_setup_with_examples.test_client()

        with session_full_db_setup_with_examples.app_context():
            # Get a published blog post
            blog_post = (
                database.session.execute(database.select(BlogPost).filter(BlogPost.status == "published")).scalars().first()
            )

            assert blog_post is not None, "There should be at least one published blog post"

            initial_views = blog_post.view_count or 0

            # Call the count_view endpoint
            response = client.post(f"/blog/count_view/{blog_post.id}")

            assert response.status_code == 200, "count_view endpoint should return 200"

            data = json.loads(response.data)
            assert data["status"] == "ok", "Response should indicate success"
            assert "view_count" in data, "Response should include view_count"
            assert data["view_count"] == initial_views + 1, "View count should be incremented by 1"

            # Verify the database was updated
            database.session.refresh(blog_post)
            assert blog_post.view_count == initial_views + 1, "Database should be updated with new view count"

    def test_count_view_endpoint_multiple_calls(self, session_full_db_setup_with_examples):
        """Test that the count_view endpoint can be called multiple times."""
        client = session_full_db_setup_with_examples.test_client()

        with session_full_db_setup_with_examples.app_context():
            # Get a published blog post
            blog_post = (
                database.session.execute(database.select(BlogPost).filter(BlogPost.status == "published")).scalars().first()
            )

            assert blog_post is not None, "There should be at least one published blog post"

            initial_views = blog_post.view_count or 0

            # Call the endpoint multiple times
            for i in range(3):
                response = client.post(f"/blog/count_view/{blog_post.id}")
                assert response.status_code == 200, f"Request {i+1} should return 200"

                data = json.loads(response.data)
                expected_views = initial_views + i + 1
                assert data["view_count"] == expected_views, f"View count should be {expected_views} after {i+1} calls"

            # Verify final database state
            database.session.refresh(blog_post)
            assert blog_post.view_count == initial_views + 3, "Database should reflect all view increments"

    def test_count_view_endpoint_invalid_post_id(self, session_full_db_setup_with_examples):
        """Test that the count_view endpoint handles invalid post IDs."""
        client = session_full_db_setup_with_examples.test_client()

        # Test with non-existent post ID
        response = client.post("/blog/count_view/99999")
        assert response.status_code == 404, "Should return 404 for non-existent post"

        data = json.loads(response.data)
        assert data["status"] == "error", "Response should indicate error"
        assert "message" in data, "Response should include error message"

    def test_count_view_endpoint_draft_post(self, session_full_db_setup_with_examples):
        """Test that the count_view endpoint doesn't count views for draft posts."""
        client = session_full_db_setup_with_examples.test_client()

        with session_full_db_setup_with_examples.app_context():
            # Create a draft blog post
            draft_post = BlogPost(
                title="Draft Post", slug="draft-post", content="This is a draft post", author_id="lms-admin", status="draft"
            )
            database.session.add(draft_post)
            database.session.commit()

            # Try to count views for draft post
            response = client.post(f"/blog/count_view/{draft_post.id}")
            assert response.status_code == 404, "Should return 404 for draft posts"

            data = json.loads(response.data)
            assert data["status"] == "error", "Response should indicate error"

    def test_blog_post_page_displays_view_count(self, session_full_db_setup_with_examples):
        """Test that the blog post page displays the view count."""
        client = session_full_db_setup_with_examples.test_client()

        with session_full_db_setup_with_examples.app_context():
            # Get a published blog post and set some views
            blog_post = (
                database.session.execute(database.select(BlogPost).filter(BlogPost.status == "published")).scalars().first()
            )

            assert blog_post is not None, "There should be at least one published blog post"

            # Set a specific view count
            blog_post.view_count = 42
            database.session.commit()

            # Test the blog post page
            response = client.get(f"/blog/{blog_post.slug}")
            assert response.status_code == 200, "Blog post page should be accessible"

            # Check that view count is displayed
            page_content = response.data.decode("utf-8")
            # Check for the view count in the span element
            assert '<span id="view-count">42</span> vistas' in page_content, "View count should be displayed on the page"

    def test_blog_index_displays_view_count(self, session_full_db_setup_with_examples):
        """Test that the blog index page displays view counts."""
        client = session_full_db_setup_with_examples.test_client()

        with session_full_db_setup_with_examples.app_context():
            # Get a published blog post and set some views
            blog_post = (
                database.session.execute(database.select(BlogPost).filter(BlogPost.status == "published")).scalars().first()
            )

            assert blog_post is not None, "There should be at least one published blog post"

            # Set a specific view count
            blog_post.view_count = 15
            database.session.commit()

            # Test the blog index page
            response = client.get("/blog")
            assert response.status_code == 200, "Blog index page should be accessible"

            # Check that view count is displayed (may be plural or singular)
            page_content = response.data.decode("utf-8")
            # The blog index shows "- 15 vistas" in the metadata line
            assert "- 15 vistas" in page_content, "View count should be displayed on the blog index page"

    def test_view_count_displays_correctly_singular_plural(self, session_full_db_setup_with_examples):
        """Test that view count displays correctly for singular and plural."""
        client = session_full_db_setup_with_examples.test_client()

        with session_full_db_setup_with_examples.app_context():
            # Get a published blog post
            blog_post = (
                database.session.execute(database.select(BlogPost).filter(BlogPost.status == "published")).scalars().first()
            )

            assert blog_post is not None, "There should be at least one published blog post"

            # Test singular (1 view)
            blog_post.view_count = 1
            database.session.commit()

            response = client.get(f"/blog/{blog_post.slug}")
            assert response.status_code == 200
            page_content = response.data.decode("utf-8")
            assert '<span id="view-count">1</span> vista' in page_content, "Should display singular form for 1 view"

            # Test plural (2 views)
            blog_post.view_count = 2
            database.session.commit()

            response = client.get(f"/blog/{blog_post.slug}")
            assert response.status_code == 200
            page_content = response.data.decode("utf-8")
            assert '<span id="view-count">2</span> vistas' in page_content, "Should display plural form for multiple views"
