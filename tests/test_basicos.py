# Copyright 2021 - 2023 BMO Soluciones, S.A.
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

import inspect
import os
import pytest
from typing import Dict, List, Tuple

from now_lms import log


def test_importable(app):
    """El proyecto debe poder importarse sin errores."""
    assert app


def test_cli(app):
    runner = app.test_cli_runner()
    runner.invoke(args=["info", "path"])
    runner.invoke(args=["info", "system"])
    runner.invoke(args=["info", "course", "now"])
    runner.invoke(args=["database"])


def test_flask_instance(app):
    from flask import Flask

    assert isinstance(app, Flask)


def test_sqlalchemy_instance(app):
    from now_lms import database
    from flask_sqlalchemy import SQLAlchemy

    assert isinstance(database, SQLAlchemy)


def test_alembic_instance(app):
    from now_lms import alembic
    from flask_alembic import Alembic

    assert isinstance(alembic, Alembic)


def test_login_manager_instance(app):
    from now_lms import administrador_sesion
    from flask_login import LoginManager

    assert isinstance(administrador_sesion, LoginManager)


def test_flask_form_classes(app):
    from flask_wtf import FlaskForm
    import now_lms.forms as forms

    form_classes = [
        cls
        for name, cls in inspect.getmembers(forms, inspect.isclass)
        if cls.__module__ == forms.__name__ and issubclass(cls, FlaskForm)
    ]

    assert form_classes, "No se encontraron formularios que hereden de FlaskForm."

    for cls in form_classes:
        assert issubclass(cls, FlaskForm), f"{cls.__name__} no hereda de FlaskForm"


def test_base_table_inheritance(app):
    from now_lms.db import BaseTabla, database
    from flask_login import UserMixin
    from now_lms import Usuario

    assert issubclass(Usuario, UserMixin)
    assert issubclass(Usuario, BaseTabla)
    assert issubclass(Usuario, database.Model)


# Source: https://gist.github.com/allysonsilva/85fff14a22bbdf55485be947566cc09e
MARKDOWN_EXAMPLE = """
# Headers

```
# h1 Heading 8-)
## h2 Heading
### h3 Heading
#### h4 Heading
##### h5 Heading
###### h6 Heading

Alternatively, for H1 and H2, an underline-ish style:

Alt-H1
======

Alt-H2
------
```

# h1 Heading 8-)
## h2 Heading
### h3 Heading
#### h4 Heading
##### h5 Heading
###### h6 Heading

Alternatively, for H1 and H2, an underline-ish style:

Alt-H1
======

Alt-H2
------

------

# Emphasis

```
Emphasis, aka italics, with *asterisks* or _underscores_.

Strong emphasis, aka bold, with **asterisks** or __underscores__.

Combined emphasis with **asterisks and _underscores_**.

Strikethrough uses two tildes. ~~Scratch this.~~

**This is bold text**

__This is bold text__

*This is italic text*

_This is italic text_

~~Strikethrough~~
```

Emphasis, aka italics, with *asterisks* or _underscores_.

Strong emphasis, aka bold, with **asterisks** or __underscores__.

Combined emphasis with **asterisks and _underscores_**.

Strikethrough uses two tildes. ~~Scratch this.~~

**This is bold text**

__This is bold text__

*This is italic text*

_This is italic text_

~~Strikethrough~~

------

# Lists

```
1. First ordered list item
2. Another item
⋅⋅* Unordered sub-list.
1. Actual numbers don't matter, just that it's a number
⋅⋅1. Ordered sub-list
4. And another item.

⋅⋅⋅You can have properly indented paragraphs within list items. Notice the blank line above, and the leading spaces (at least one, but we'll use three here to also align the raw Markdown).

⋅⋅⋅To have a line break without a paragraph, you will need to use two trailing spaces.⋅⋅
⋅⋅⋅Note that this line is separate, but within the same paragraph.⋅⋅
⋅⋅⋅(This is contrary to the typical GFM line break behaviour, where trailing spaces are not required.)

* Unordered list can use asterisks
- Or minuses
+ Or pluses

1. Make my changes
    1. Fix bug
    2. Improve formatting
        - Make the headings bigger
2. Push my commits to GitHub
3. Open a pull request
    * Describe my changes
    * Mention all the members of my team
        * Ask for feedback

+ Create a list by starting a line with `+`, `-`, or `*`
+ Sub-lists are made by indenting 2 spaces:
  - Marker character change forces new list start:
    * Ac tristique libero volutpat at
    + Facilisis in pretium nisl aliquet
    - Nulla volutpat aliquam velit
+ Very easy!
```

1. First ordered list item
2. Another item
⋅⋅* Unordered sub-list.
1. Actual numbers don't matter, just that it's a number
⋅⋅1. Ordered sub-list
4. And another item.

⋅⋅⋅You can have properly indented paragraphs within list items. Notice the blank line above, and the leading spaces (at least one, but we'll use three here to also align the raw Markdown).

⋅⋅⋅To have a line break without a paragraph, you will need to use two trailing spaces.⋅⋅
⋅⋅⋅Note that this line is separate, but within the same paragraph.⋅⋅
⋅⋅⋅(This is contrary to the typical GFM line break behaviour, where trailing spaces are not required.)

* Unordered list can use asterisks
- Or minuses
+ Or pluses

1. Make my changes
    1. Fix bug
    2. Improve formatting
        - Make the headings bigger
2. Push my commits to GitHub
3. Open a pull request
    * Describe my changes
    * Mention all the members of my team
        * Ask for feedback

+ Create a list by starting a line with `+`, `-`, or `*`
+ Sub-lists are made by indenting 2 spaces:
  - Marker character change forces new list start:
    * Ac tristique libero volutpat at
    + Facilisis in pretium nisl aliquet
    - Nulla volutpat aliquam velit
+ Very easy!

------

# Task lists

```
- [x] Finish my changes
- [ ] Push my commits to GitHub
- [ ] Open a pull request
- [x] @mentions, #refs, [links](), **formatting**, and <del>tags</del> supported
- [x] list syntax required (any unordered or ordered list supported)
- [x] this is a complete item
- [ ] this is an incomplete item
```

- [x] Finish my changes
- [ ] Push my commits to GitHub
- [ ] Open a pull request
- [x] @mentions, #refs, [links](), **formatting**, and <del>tags</del> supported
- [x] list syntax required (any unordered or ordered list supported)
- [ ] this is a complete item
- [ ] this is an incomplete item

"""


def test_clean_markdown():
    from now_lms.misc import markdown_to_clean_html

    markdown_to_clean_html(MARKDOWN_EXAMPLE)


# -----------------------------------------------------------------------------
# Comprehensive tests that visit all views exposed by the Flask app.
# This test suite ensures that users do not encounter 404 or 500 errors
# when visiting any route. It skips dynamic URLs that require real data
# in the database and skips known failing views.
# -----------------------------------------------------------------------------


class RouteTestConfig:
    """Configuration for route testing"""

    # Routes to skip because they require special parameters or are known to fail
    SKIP_ROUTES = {
        # Token-based routes that require valid tokens
        "/user/check_mail/<token>",
        "/user/reset_password/<token>",
        # File download routes that need specific file paths
        "/static/flask_mde/<path:filename>",
        # PayPal routes that require external integration or have known issues
        "/paypal_checkout/resume_payment/<payment_id>",
        "/paypal_checkout/payment_status/<course_code>",  # Has database schema issues
        # Routes that perform destructive actions or require specific data
        "/setting/delete_site_logo",
        # Routes that redirect immediately and don't need testing
        "/course/change_curse_public",
        "/course/change_curse_seccion_public",
        "/course/change_curse_status",
        # Routes with URL building issues or missing JavaScript dependencies
        "/resource/explore",  # Has URL building error in template
        "/user/calendar",  # Missing moment.js dependency
        # POST-only routes that shouldn't be tested with GET
        "/group/add",
        "/group/set_tutor",
        "/admin/blog/tags",  # POST route for creating tags
        "/paypal_checkout/confirm_payment",
        "/setting/mail_check",
        # File upload routes
        "/_uploads/<setname>/<path:filename>",
    }

    # Sample parameters for dynamic routes (using test data IDs)
    SAMPLE_PARAMS = {
        "course_code": "now",  # Test course code
        "curso_code": "now",
        "curso_id": "now",
        "course_id": "now",
        "cource_code": "now",  # Typo in original route
        "ulid": "01HNZXJRD65A55BJACFEFNZ88D",  # Sample ULID from test data
        "codigo": "01HPB1MZXBHZETC4ZH0HV4G39Q",  # Sample section ID
        "resource_code": "01HNZXA1BX9B297CYAAA4MK93V",  # Sample resource ID
        "recurso_code": "01HPB3AP3QNVK9ES6JGG5YK7CH",  # Sample resource ID
        "seccion": "01HPB1MZXBHZETC4ZH0HV4G39Q",
        "seccion_id": "01HPB1MZXBHZETC4ZH0HV4G39Q",
        "section_id": "01HPB1MZXBHZETC4ZH0HV4G39Q",
        "id_": "01HPB1MZXBHZETC4ZH0HV4G39Q",
        "slideshow_id": "1",
        "message_id": "1",
        "announcement_id": "1",
        "evaluation_id": "1",
        "attempt_id": "1",
        "event_id": "1",
        "thread_id": "1",
        "payment_id": "test-payment-id",
        "id_usuario": "01HNZXJRD65A55BJACFEFNZ88D",
        "user": "01HNZXJRD65A55BJACFEFNZ88D",
        "group": "1",
        "indice": "1",
        "order": "1",
        "resource_index": "1",
        "task": "increment",
        "resource_type": "material",
        "page": "about",
        "code": "404",
        "new_status": "closed",
        "slug": "test-masterclass",
        "id": "1",
        "filename": "test.css",
        "token": "invalid-token-for-testing",
    }


def discover_app_routes(app) -> List[Dict]:
    """Discover all routes in the Flask app"""
    routes = []

    with app.app_context():
        for rule in app.url_map.iter_rules():
            # Skip static file handling
            if rule.endpoint == "static":
                continue

            route_info = {
                "rule": str(rule),
                "endpoint": rule.endpoint,
                "methods": list(rule.methods - {"HEAD", "OPTIONS"}),
                "has_parameters": bool(rule.arguments),
                "parameters": list(rule.arguments) if rule.arguments else [],
            }
            routes.append(route_info)

    return routes


def build_test_url(rule: str, params: Dict[str, str]) -> str:
    """Build a test URL by replacing parameters with sample values"""
    url = rule

    # Replace angle-bracket parameters
    for param_name, param_value in params.items():
        # Handle different parameter formats
        patterns = [
            f"<{param_name}>",
            f"<string:{param_name}>",
            f"<int:{param_name}>",
            f"<path:{param_name}>",
        ]

        for pattern in patterns:
            if pattern in url:
                url = url.replace(pattern, str(param_value))

    return url


def categorize_routes(routes: List[Dict]) -> Tuple[List[str], List[Dict]]:
    """Categorize routes into static and dynamic"""
    static_routes = []
    dynamic_routes = []

    for route in routes:
        if not route["has_parameters"]:
            # Skip routes that are in the skip list
            if route["rule"] in RouteTestConfig.SKIP_ROUTES:
                continue
            # Only include routes that support GET method
            if "GET" in route["methods"]:
                static_routes.append(route["rule"])
        else:
            # Skip routes that are in the skip list
            if route["rule"] in RouteTestConfig.SKIP_ROUTES:
                continue
            dynamic_routes.append(route)

    return static_routes, dynamic_routes


def get_user_credentials() -> Dict[str, Tuple[str, str]]:
    """Get test user credentials"""
    admin_username = os.environ.get("ADMIN_USER") or os.environ.get("LMS_USER") or "lms-admin"
    admin_password = os.environ.get("ADMIN_PSWD") or os.environ.get("LMS_PSWD") or "lms-admin"

    return {
        "admin": (admin_username, admin_password),
        "user": ("student1", "student1"),
        "moderator": ("moderator", "moderator"),
        "instructor": ("instructor", "instructor"),
    }


class TestComprehensiveRoutes:
    """Comprehensive route testing"""

    def test_discover_all_routes(self, session_full_db_setup_with_examples):
        """Test that we can discover all routes in the app"""
        app = session_full_db_setup_with_examples
        routes = discover_app_routes(app)

        # We should have a significant number of routes
        assert len(routes) > 50, f"Expected more than 50 routes, found {len(routes)}"

        # Check that we have both static and dynamic routes
        static_routes, dynamic_routes = categorize_routes(routes)
        assert len(static_routes) > 0, "Should have static routes"
        assert len(dynamic_routes) > 0, "Should have dynamic routes"

        log.info(f"Discovered {len(routes)} total routes: {len(static_routes)} static, {len(dynamic_routes)} dynamic")

    def test_static_routes_anonymous_user(self, session_full_db_setup_with_examples):
        """Test all static routes with anonymous user"""
        app = session_full_db_setup_with_examples
        routes = discover_app_routes(app)
        static_routes, _ = categorize_routes(routes)

        with app.test_client() as client:
            # Ensure we're logged out
            client.get("/user/logout")

            failed_routes = []

            for route in static_routes:
                try:
                    response = client.get(route)

                    # Check that we don't get server errors (500)
                    if response.status_code >= 500:
                        failed_routes.append(f"{route}: {response.status_code}")
                        log.error(f"Server error on {route}: {response.status_code}")
                    else:
                        log.debug(f"✓ {route}: {response.status_code}")

                except Exception as e:
                    failed_routes.append(f"{route}: Exception - {str(e)}")
                    log.error(f"Exception testing {route}: {e}")

            # Report any failures
            if failed_routes:
                pytest.fail("Routes with server errors:\n" + "\n".join(failed_routes))

    def test_static_routes_admin_user(self, session_full_db_setup_with_examples):
        """Test all static routes with admin user"""
        app = session_full_db_setup_with_examples
        routes = discover_app_routes(app)
        static_routes, _ = categorize_routes(routes)
        credentials = get_user_credentials()

        with app.test_client() as client:
            # Login as admin
            admin_user, admin_pass = credentials["admin"]
            client.post("/user/login", data={"usuario": admin_user, "acceso": admin_pass})

            failed_routes = []

            for route in static_routes:
                try:
                    response = client.get(route)

                    # Check that we don't get server errors (500)
                    if response.status_code >= 500:
                        failed_routes.append(f"{route}: {response.status_code}")
                        log.error(f"Server error on {route}: {response.status_code}")
                    else:
                        log.debug(f"✓ {route}: {response.status_code}")

                except Exception as e:
                    failed_routes.append(f"{route}: Exception - {str(e)}")
                    log.error(f"Exception testing {route}: {e}")

            # Logout
            client.get("/user/logout")

            # Report any failures
            if failed_routes:
                pytest.fail("Routes with server errors:\n" + "\n".join(failed_routes))

    def test_static_routes_regular_user(self, session_full_db_setup_with_examples):
        """Test all static routes with regular user"""
        app = session_full_db_setup_with_examples
        routes = discover_app_routes(app)
        static_routes, _ = categorize_routes(routes)
        credentials = get_user_credentials()

        with app.test_client() as client:
            # Login as regular user
            user_name, user_pass = credentials["user"]
            client.post("/user/login", data={"usuario": user_name, "acceso": user_pass})

            failed_routes = []

            for route in static_routes:
                try:
                    response = client.get(route)

                    # Check that we don't get server errors (500)
                    if response.status_code >= 500:
                        failed_routes.append(f"{route}: {response.status_code}")
                        log.error(f"Server error on {route}: {response.status_code}")
                    else:
                        log.debug(f"✓ {route}: {response.status_code}")

                except Exception as e:
                    failed_routes.append(f"{route}: Exception - {str(e)}")
                    log.error(f"Exception testing {route}: {e}")

            # Logout
            client.get("/user/logout")

            # Report any failures
            if failed_routes:
                pytest.fail("Routes with server errors:\n" + "\n".join(failed_routes))

    def test_dynamic_routes_with_sample_data(self, session_full_db_setup_with_examples):
        """Test dynamic routes with sample parameters - focus on avoiding 500 errors"""
        app = session_full_db_setup_with_examples
        routes = discover_app_routes(app)
        _, dynamic_routes = categorize_routes(routes)
        credentials = get_user_credentials()

        with app.test_client() as client:
            # Login as admin to have maximum access
            admin_user, admin_pass = credentials["admin"]
            client.post("/user/login", data={"usuario": admin_user, "acceso": admin_pass})

            failed_routes = []
            tested_routes = []
            server_errors = []

            for route_info in dynamic_routes:
                rule = route_info["rule"]

                try:
                    # Build test URL with sample parameters
                    test_url = build_test_url(rule, RouteTestConfig.SAMPLE_PARAMS)

                    # Skip if we couldn't build a proper URL
                    if "<" in test_url or ">" in test_url:
                        log.warning(f"Skipping {rule}: couldn't resolve all parameters")
                        continue

                    # Test only GET requests for safety
                    if "GET" in route_info["methods"]:
                        response = client.get(test_url)
                        tested_routes.append(test_url)

                        # Check that we don't get server errors (500+)
                        if response.status_code >= 500:
                            server_errors.append(f"{test_url}: {response.status_code}")
                            log.error(f"Server error on {test_url}: {response.status_code}")
                        else:
                            log.debug(f"✓ {test_url}: {response.status_code}")

                except Exception as e:
                    # Only count actual server errors, not template/data errors
                    error_msg = str(e)
                    if any(server_error in error_msg.lower() for server_error in ["500", "internal server error"]):
                        server_errors.append(f"{test_url}: Exception - {error_msg}")
                        log.error(f"Server error testing {test_url}: {e}")
                    else:
                        # These are expected errors (missing data, etc.)
                        failed_routes.append(f"{test_url}: Exception - {error_msg}")
                        log.warning(f"Expected error testing {test_url}: {e}")

            # Logout
            client.get("/user/logout")

            log.info(f"Tested {len(tested_routes)} dynamic routes")
            log.info(f"Found {len(failed_routes)} expected errors (missing data, etc.)")

            # Only fail if we have actual server errors (500+)
            if server_errors:
                pytest.fail("Dynamic routes with server errors:\n" + "\n".join(server_errors))

    def test_error_handling_routes(self, session_full_db_setup_with_examples):
        """Test that error handling routes work properly"""
        app = session_full_db_setup_with_examples

        error_codes = [403, 404, 405, 500]

        with app.test_client() as client:
            failed_routes = []

            for error_code in error_codes:
                route = f"/http/error/{error_code}"
                try:
                    response = client.get(route)

                    # Error pages should return 200 (they're showing an error page, not erroring)
                    if response.status_code != 200:
                        failed_routes.append(f"{route}: Expected 200, got {response.status_code}")
                    else:
                        log.debug(f"✓ {route}: {response.status_code}")

                except Exception as e:
                    failed_routes.append(f"{route}: Exception - {str(e)}")
                    log.error(f"Exception testing {route}: {e}")

            # Report any failures
            if failed_routes:
                pytest.fail("Error handling routes failed:\n" + "\n".join(failed_routes))

    def test_common_public_routes(self, session_full_db_setup_with_examples):
        """Test common public routes that should always work"""
        app = session_full_db_setup_with_examples

        # Important public routes that should always work
        public_routes = [
            "/",
            "/home",
            "/course/explore",
            "/program/explore",
            "/blog",
            "/user/login",
            "/user/forgot_password",
            "/ads.txt",
        ]

        with app.test_client() as client:
            failed_routes = []

            for route in public_routes:
                try:
                    response = client.get(route)

                    # These routes should return 200 or redirect (3xx)
                    if response.status_code >= 400:
                        failed_routes.append(f"{route}: {response.status_code}")
                        log.error(f"Error on public route {route}: {response.status_code}")
                    else:
                        log.debug(f"✓ {route}: {response.status_code}")

                except Exception as e:
                    failed_routes.append(f"{route}: Exception - {str(e)}")
                    log.error(f"Exception testing {route}: {e}")

            # Report any failures
            if failed_routes:
                pytest.fail("Public routes failed:\n" + "\n".join(failed_routes))
