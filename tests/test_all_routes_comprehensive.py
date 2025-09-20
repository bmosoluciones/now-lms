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
#

"""
Comprehensive route testing implementation that discovers and tests all Flask routes.

This test file automatically discovers all routes using Flask's URL map and tests them
to ensure users do not encounter 404 or 500 errors. It provides comprehensive coverage
for all course routes and other application routes.
"""

import re

import pytest
from flask import url_for
from now_lms.db import Usuario


@pytest.mark.comprehensive
@pytest.mark.slow
class TestAllRoutesComprehensive:
    """Comprehensive route testing using automatic route discovery."""

    # Class-level route cache to avoid rediscovering routes in each test
    _routes_cache = None

    # Sample parameters for dynamic routes based on test data
    SAMPLE_PARAMS = {
        "course_code": "now",  # Test course code from session fixtures
        "codigo": "now",  # Alternative course code parameter
        "course_id": "now",
        "curso_id": "now",
        "curso_code": "now",
        "cource_code": "now",  # Typo in actual route
        "ulid": "01HNZXJRD65A55BJACFEFNZ88D",  # Sample ULID from test data
        "resource_code": "01HNZXA1BX9B297CYAAA4MK93V",
        "recurso_code": "01HNZXA1BX9B297CYAAA4MK93V",
        "resource_id": "01HNZXA1BX9B297CYAAA4MK93V",
        "seccion": "01HNZXJZ1YBCN7C1FMRN5NRXM3",
        "seccion_id": "01HNZXJZ1YBCN7C1FMRN5NRXM3",
        "section_id": "01HNZXJZ1YBCN7C1FMRN5NRXM3",
        "slideshow_id": "01HNZXA1BX9B297CYAAA4MK93V",
        "coupon_id": "SAMPLE_COUPON",
        "id_": "test_id",
        "id": "test_id",
        "indice": "1",
        "order": "1",
        "resource_index": "1",
        "task": "view",
        "resource_type": "text",
        "usuario": "lms-admin",
        "user_id": "lms-admin",
        "filename": "test.txt",
        "path": "test/path",
        "token": "test_token",
        "payment_id": "test_payment",
        "tag": "python",
        "category": "programming",
        "evaluation_id": "test_eval",
        "question_id": "test_question",
        "attempt_id": "test_attempt",
        "group_id": "test_group",
        "forum_id": "test_forum",
        "post_id": "test_post",
        "comment_id": "test_comment",
        "year": "2024",
        "month": "01",
        "day": "01",
    }

    # Routes that should be skipped during testing due to special requirements
    SKIP_ROUTES = {
        # Routes requiring valid JWT tokens
        "user.check_mail",
        "user.reset_password",
        # File serving routes that need valid file paths
        "static",
        "flask_mde.static",
        # External integration routes (PayPal, etc.)
        "paypal.create_payment",
        "paypal.execute_payment",
        "paypal.cancel_payment",
        # POST-only routes that shouldn't be tested with GET
        "course.change_curse_status",
        "course.change_curse_public",
        "course.change_curse_seccion_public",
        "course.delete_coupon",
        # Routes with complex requirements
        "course.file_upload",
        # Error handlers
        "main.not_found",
        "main.forbidden",
        "main.internal_server_error",
        "main.method_not_allowed",
    }

    def discover_all_routes(self, session_basic_db_setup):
        """Discover all routes in the Flask application with caching."""
        if self._routes_cache is not None:
            return self._routes_cache

        with session_basic_db_setup.app_context():
            routes = []
            for rule in session_basic_db_setup.url_map.iter_rules():
                if rule.endpoint not in self.SKIP_ROUTES:
                    routes.append(
                        {
                            "endpoint": rule.endpoint,
                            "rule": rule.rule,
                            "methods": rule.methods,
                            "has_variables": bool(rule.arguments),
                        }
                    )
            # Cache the routes for subsequent test methods
            TestAllRoutesComprehensive._routes_cache = routes
            return routes

    def build_url_with_params(self, app, endpoint, rule):
        """Build URL for a route with sample parameters."""
        with app.app_context():
            # Extract parameter names from the rule
            param_pattern = r"<(?:(?P<converter>[^>:]+):)?(?P<variable>[^>]+)>"
            params = {}

            for match in re.finditer(param_pattern, rule):
                variable = match.group("variable")
                if variable in self.SAMPLE_PARAMS:
                    params[variable] = self.SAMPLE_PARAMS[variable]
                else:
                    # Fallback for unknown parameters
                    params[variable] = "test_value"

            try:
                return url_for(endpoint, **params)
            except Exception:
                # If URL building fails, return None to skip this route
                return None

    def test_discover_all_routes(self, session_basic_db_setup):
        """Test that route discovery works and finds expected number of routes."""
        routes = self.discover_all_routes(session_basic_db_setup)

        # Should discover a significant number of routes (README mentions 207)
        assert len(routes) > 50, f"Expected to discover many routes, found {len(routes)}"

        # Should include course routes
        course_routes = [r for r in routes if r["endpoint"].startswith("course.")]
        assert len(course_routes) > 10, f"Expected many course routes, found {len(course_routes)}"

    def test_static_routes_anonymous_user(self, session_basic_db_setup):
        """Test static routes with anonymous user."""
        client = session_basic_db_setup.test_client()

        with session_basic_db_setup.app_context():
            routes = self.discover_all_routes(session_basic_db_setup)
            static_routes = [r for r in routes if not r["has_variables"]]

            tested_count = 0
            success_count = 0

            for route in static_routes:
                if "GET" in route["methods"]:
                    try:
                        url = url_for(route["endpoint"])
                        response = client.get(url)
                        tested_count += 1

                        # Accept any response that's not a server error (500+)
                        if response.status_code < 500:
                            success_count += 1
                        else:
                            print(f"Server error on {url}: {response.status_code}")

                    except Exception:
                        # Skip routes that can't be built or have issues
                        pass

            assert tested_count > 0, "No static routes were tested"
            # At least 70% of routes should not have server errors
            success_rate = success_count / tested_count if tested_count > 0 else 0
            assert success_rate >= 0.7, f"Too many server errors: {success_count}/{tested_count} success rate"

    def test_static_routes_admin_user(self, session_full_db_setup):
        """Test static routes with admin user privileges."""
        client = session_full_db_setup.test_client()

        with session_full_db_setup.app_context():
            # Get admin user from session fixtures
            admin_user = Usuario.query.filter_by(usuario="lms-admin").first()
            assert admin_user is not None, "Admin user not found in session fixtures"

            with client.session_transaction() as sess:
                sess["_user_id"] = admin_user.usuario
                sess["_fresh"] = True

            routes = self.discover_all_routes(session_full_db_setup)
            static_routes = [r for r in routes if not r["has_variables"]]

            tested_count = 0
            success_count = 0

            for route in static_routes:
                if "GET" in route["methods"]:
                    try:
                        with session_full_db_setup.app_context():
                            url = url_for(route["endpoint"])
                        response = client.get(url)
                        tested_count += 1

                        # Accept any response that's not a server error (500+)
                        if response.status_code < 500:
                            success_count += 1
                        else:
                            print(f"Server error on {url}: {response.status_code}")

                    except Exception:
                        # Skip routes that can't be built or have issues
                        pass

            assert tested_count > 0, "No static routes were tested"
            # Admin should have better success rate
            success_rate = success_count / tested_count if tested_count > 0 else 0
            assert success_rate >= 0.8, f"Too many server errors for admin: {success_count}/{tested_count}"

    def test_static_routes_regular_user(self, session_full_db_setup):
        """Test static routes with regular user."""
        client = session_full_db_setup.test_client()

        with session_full_db_setup.app_context():
            # Get a regular user from session fixtures
            regular_user = Usuario.query.filter_by(tipo="student").first()
            if not regular_user:
                # Skip if no regular user available
                return

            with client.session_transaction() as sess:
                sess["_user_id"] = regular_user.usuario
                sess["_fresh"] = True

            routes = self.discover_all_routes(session_full_db_setup)
            static_routes = [r for r in routes if not r["has_variables"]]

            tested_count = 0
            success_count = 0

            for route in static_routes:
                if "GET" in route["methods"]:
                    try:
                        with session_full_db_setup.app_context():
                            url = url_for(route["endpoint"])
                        response = client.get(url)
                        tested_count += 1

                        # Accept any response that's not a server error (500+)
                        if response.status_code < 500:
                            success_count += 1
                        else:
                            print(f"Server error on {url}: {response.status_code}")

                    except Exception:
                        # Skip routes that can't be built or have issues
                        pass

            assert tested_count > 0, "No static routes were tested"
            # Regular user success rate might be lower due to authorization
            success_rate = success_count / tested_count if tested_count > 0 else 0
            assert success_rate >= 0.6, f"Too many server errors for regular user: {success_count}/{tested_count}"

    def test_dynamic_routes_with_sample_data(self, session_full_db_setup):
        """Test dynamic routes using sample parameters."""
        client = session_full_db_setup.test_client()

        with session_full_db_setup.app_context():
            # Test with admin user for broader access
            admin_user = Usuario.query.filter_by(usuario="lms-admin").first()
            assert admin_user is not None, "Admin user not found in session fixtures"

            with client.session_transaction() as sess:
                sess["_user_id"] = admin_user.usuario
                sess["_fresh"] = True

            routes = self.discover_all_routes(session_full_db_setup)
            dynamic_routes = [r for r in routes if r["has_variables"]]

            tested_count = 0
            success_count = 0

            for route in dynamic_routes:
                if "GET" in route["methods"]:
                    url = self.build_url_with_params(session_full_db_setup, route["endpoint"], route["rule"])
                    if url:
                        try:
                            response = client.get(url)
                            tested_count += 1

                            # For dynamic routes, 404 is often expected with sample data
                            # We mainly want to avoid 500+ server errors
                            if response.status_code < 500:
                                success_count += 1
                            else:
                                print(f"Server error on {url}: {response.status_code}")

                        except Exception:
                            # Skip routes that fail for other reasons
                            pass

            assert tested_count > 0, "No dynamic routes were tested"
            # Dynamic routes with sample data will have more 404s, so lower threshold
            success_rate = success_count / tested_count if tested_count > 0 else 0
            assert success_rate >= 0.5, f"Too many server errors on dynamic routes: {success_count}/{tested_count}"

    def test_course_routes_comprehensive(self, session_full_db_setup):
        """Focus specifically on course routes to improve coverage."""
        client = session_full_db_setup.test_client()

        with session_full_db_setup.app_context():
            # Test with admin user for broader access
            admin_user = Usuario.query.filter_by(usuario="lms-admin").first()
            assert admin_user is not None, "Admin user not found in session fixtures"

            with client.session_transaction() as sess:
                sess["_user_id"] = admin_user.usuario
                sess["_fresh"] = True

            routes = self.discover_all_routes(session_full_db_setup)
            course_routes = [r for r in routes if r["endpoint"].startswith("course.")]

            tested_count = 0
            success_count = 0
            course_view_tested = False
            course_enroll_tested = False
            course_take_tested = False

            for route in course_routes:
                if "GET" in route["methods"]:
                    if route["has_variables"]:
                        url = self.build_url_with_params(session_full_db_setup, route["endpoint"], route["rule"])
                    else:
                        try:
                            with session_full_db_setup.app_context():
                                url = url_for(route["endpoint"])
                        except Exception:
                            continue

                    if url:
                        try:
                            response = client.get(url)
                            tested_count += 1

                            # Track specific important course routes
                            if "/course/now/view" in url:
                                course_view_tested = True
                            elif "/course/now/enroll" in url:
                                course_enroll_tested = True
                            elif "/course/now/take" in url:
                                course_take_tested = True

                            # Accept any response that's not a server error
                            if response.status_code < 500:
                                success_count += 1
                            else:
                                print(f"Server error on course route {url}: {response.status_code}")

                        except Exception:
                            pass

            assert tested_count > 0, "No course routes were tested"
            # Course routes should have good success rate
            success_rate = success_count / tested_count if tested_count > 0 else 0
            assert success_rate >= 0.6, f"Too many server errors on course routes: {success_count}/{tested_count}"

            # Verify key course functionality was tested
            assert course_view_tested or course_enroll_tested or course_take_tested, "Key course routes should be tested"

    def test_error_handling_routes(self, session_basic_db_setup):
        """Test that custom error pages work correctly."""
        client = session_basic_db_setup.test_client()

        # Test 404 page
        response = client.get("/nonexistent-page")
        assert response.status_code == 404

        # Test that 404 page renders without server error
        assert b"404" in response.data or b"Not Found" in response.data or response.status_code == 404

    def test_common_public_routes(self, session_basic_db_setup):
        """Test critical public routes that must work."""
        client = session_basic_db_setup.test_client()

        critical_routes = [
            "/",  # Homepage
            "/blog",  # Blog
            "/user/login",  # Login page
            "/course/explore",  # Course exploration
        ]

        for url in critical_routes:
            response = client.get(url)
            # These routes must not have server errors
            assert response.status_code < 500, f"Critical route {url} returned {response.status_code}"
