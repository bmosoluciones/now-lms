"""L6 browser E2E: the anonymous gating boundary.

Mirrors features/gating_boundary.feature at the browser level: an anonymous
visitor holding a course link lands on the request-access intake (the
conversion path), never on raw content. The /user/logon → /request-access 302
lives at the INGRESS layer (host config, not the app) and is deliberately NOT
asserted here — scripts/deploy-smoke.sh owns that surface in production.
"""

from __future__ import annotations

import re

from playwright.sync_api import Page, expect

from e2e.conftest import E2E_COURSE


def test_anonymous_course_link_lands_on_intake(app_server: str, page: Page) -> None:
    page.goto(f"{app_server}/course/{E2E_COURSE}/view")
    page.wait_for_url(re.compile(r"/request-access"), timeout=15000)
    expect(page.locator("form")).to_be_visible()


def test_anonymous_take_requires_login(app_server: str, page: Page) -> None:
    page.goto(f"{app_server}/course/{E2E_COURSE}/take")
    assert re.search(r"/(user/login|request-access)", page.url)


def test_request_access_page_serves_form(app_server: str, page: Page) -> None:
    page.goto(f"{app_server}/request-access")
    expect(page.locator('form input[name="email"], form input[type="email"]').first).to_be_visible()
