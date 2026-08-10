"""L6 browser E2E: a member records a credential they earned elsewhere.

Covers what the unit tests cannot see — that the pages render, that the form
submits through a real browser, and that neither page pushes the document
sideways on a phone.

**Deliberately no assertions on rendered size or spacing.** This job installs
Python dependencies only; it never runs `npm ci` in `now_lms/static`, so
`static/node_modules` is absent and Bootstrap 404s. Every page in the suite
therefore renders unstyled, and any assertion about a tap target or a computed
height would be measuring the absence of a stylesheet rather than the layout.
Those checks belong in an environment that carries the asset bundle. The
structural checks below hold with or without CSS.
"""

from __future__ import annotations

import re

from playwright.sync_api import Page, expect

from e2e.conftest import _ENV, E2E_MEMBER, E2E_MEMBER_PASSWORD

PHONE = {"width": 390, "height": 844}
DESKTOP = {"width": 1440, "height": 900}

VERIFICATION_URL = "https://anthropic.skilljar.com/verify/e2e-credential"


def _login(page: Page, base: str, user: str, password: str) -> None:
    # Log out first: /user/login redirects straight to the panel when a session
    # already exists, so a second login in the same test would find no form.
    page.goto(f"{base}/user/logout")
    page.goto(f"{base}/user/login")
    page.fill('input[name="usuario"]', user)
    page.fill('input[name="acceso"]', password)
    page.click('button[type="submit"], input[type="submit"]')
    page.wait_for_url(re.compile(r"/(dashboard|home/panel|panel)"), timeout=15000)


def _login_member(page: Page, base: str) -> None:
    _login(page, base, E2E_MEMBER, E2E_MEMBER_PASSWORD)


def _login_admin(page: Page, base: str) -> None:
    _login(page, base, _ENV["ADMIN_USER"], _ENV["ADMIN_PSWD"])


def _add_credential(page: Page, base: str, key: str, credential_id: str) -> None:
    page.goto(f"{base}/my-credentials")
    page.select_option('select[name="credential_key"]', key)
    page.fill('input[name="verification_url"]', VERIFICATION_URL)
    page.fill('input[name="credential_id"]', credential_id)
    page.get_by_role("button", name="Add credential").click()
    page.wait_for_url(re.compile(r"/my-credentials"), timeout=15000)


def _assert_viewport(page: Page, expected_width: int) -> None:
    """Fail loudly when the viewport is not the width we asked for.

    A resize that silently did not take produces a desktop measurement wearing a
    mobile label, which is worse than not checking at all.
    """
    measured = page.evaluate("() => window.innerWidth")
    assert measured == expected_width, f"viewport is {measured}px, expected {expected_width}px"


def _assert_no_horizontal_overflow(page: Page) -> None:
    overflow = page.evaluate(
        "() => document.documentElement.scrollWidth - document.documentElement.clientWidth"
    )
    assert overflow <= 0, f"page scrolls horizontally by {overflow}px"


def test_member_records_a_credential(app_server: str, page: Page) -> None:
    """The whole loop: open the page, submit the form, see the result."""
    _login_member(page, app_server)
    page.goto(f"{app_server}/my-credentials")
    expect(page.get_by_role("heading", name="My credentials")).to_be_visible()

    _add_credential(page, app_server, "claude-code-101", "E2E-CC101")

    expect(page.locator("body")).to_contain_text("Claude Code 101")
    expect(page.locator(f'a[href="{VERIFICATION_URL}"]').first).to_be_visible()


def test_duplicate_submission_is_refused_in_the_browser(app_server: str, page: Page) -> None:
    """A second entry for the same course must not create a second row."""
    _login_member(page, app_server)

    _add_credential(page, app_server, "intro-mcp", "E2E-DUP-1")
    _add_credential(page, app_server, "intro-mcp", "E2E-DUP-2")

    expect(page.locator("body")).to_contain_text("Introduction to MCP")
    # Scoped to the recorded list: the <option> in the add form carries the same
    # text, so an unscoped text count is always one too many.
    recorded = page.locator("li.list-group-item", has_text="Introduction to MCP")
    assert recorded.count() == 1
    # The first submission is the one kept.
    expect(page.locator("body")).to_contain_text("E2E-DUP-1")
    expect(page.locator("body")).not_to_contain_text("E2E-DUP-2")


def test_learner_page_does_not_scroll_sideways_at_390px(app_server: str, page: Page) -> None:
    """The width a member on a phone actually opens it at."""
    page.set_viewport_size(PHONE)
    _login_member(page, app_server)
    _add_credential(page, app_server, "claude-platform-101", "E2E-PHONE")

    _assert_viewport(page, PHONE["width"])
    _assert_no_horizontal_overflow(page)
    expect(page.get_by_role("button", name="Add credential")).to_be_visible()


def test_learner_page_renders_on_desktop(app_server: str, page: Page) -> None:
    page.set_viewport_size(DESKTOP)
    _login_member(page, app_server)
    page.goto(f"{app_server}/my-credentials")

    _assert_viewport(page, DESKTOP["width"])
    _assert_no_horizontal_overflow(page)
    expect(page.locator('select[name="credential_key"]')).to_be_visible()


def test_admin_review_page_renders_at_both_widths(app_server: str, page: Page) -> None:
    """Staff can reach the review surface on a phone and on a desktop."""
    _login_member(page, app_server)
    _add_credential(page, app_server, "intro-subagents", "E2E-ADMIN-VIEW")

    _login_admin(page, app_server)
    for viewport in (PHONE, DESKTOP):
        page.set_viewport_size(viewport)
        page.goto(f"{app_server}/admin/prior-credentials")

        _assert_viewport(page, viewport["width"])
        expect(page.get_by_role("heading", name="Prior credentials")).to_be_visible()
        expect(page.locator("body")).to_contain_text("Introduction to Subagents")


def test_learner_cannot_reach_the_admin_surface(app_server: str, page: Page) -> None:
    """The authorization boundary, exercised through a real browser."""
    _login_member(page, app_server)
    response = page.goto(f"{app_server}/admin/prior-credentials")
    assert response is not None and response.status == 403
