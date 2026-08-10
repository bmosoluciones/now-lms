"""L6 browser E2E: the one journey the platform exists for.

Member logs in → opens the course → sees LESSONS (not an enroll button) →
opens a lesson. This is the journey that was silently broken for all 49
founding members on 2026-07-28 (U12): every layer below this one stayed green
while the take page rendered a link-less outline plus an Enroll button.
"""

from __future__ import annotations

import re

from playwright.sync_api import Page, expect

from e2e.conftest import E2E_COURSE, E2E_MEMBER, E2E_MEMBER_PASSWORD


def _login(page: Page, base: str) -> None:
    page.goto(f"{base}/user/login")
    page.fill('input[name="usuario"]', E2E_MEMBER)
    page.fill('input[name="acceso"]', E2E_MEMBER_PASSWORD)
    page.click('button[type="submit"], input[type="submit"]')
    page.wait_for_url(re.compile(r"/(dashboard|home/panel|panel)"), timeout=15000)


def test_member_login_reaches_panel(app_server: str, page: Page) -> None:
    _login(page, app_server)
    # A student now lands on the fork-local member dashboard rather than upstream's
    # /home/panel (see now_lms.misc.panel_de_usuario). Instructors, moderators and
    # admins are unchanged, so both destinations remain valid depending on role.
    assert "/dashboard" in page.url or "/panel" in page.url


def test_enrolled_member_sees_lessons_not_enroll_button(app_server: str, page: Page) -> None:
    """U12 regression pin: enrollment with pago=None on a FREE course must
    render lesson links on the take page — and must NOT render the enroll CTA
    that stacked duplicate enrollments for real members."""
    _login(page, app_server)
    page.goto(f"{app_server}/course/{E2E_COURSE}/take")

    lesson_links = page.locator(f'a[href*="/course/{E2E_COURSE}/resource/"]')
    expect(lesson_links.first).to_be_visible(timeout=15000)

    enroll_cta = page.locator(f'a[href$="/course/{E2E_COURSE}/enroll"]')
    expect(enroll_cta).to_have_count(0)


def test_member_can_open_a_lesson(app_server: str, page: Page) -> None:
    _login(page, app_server)
    page.goto(f"{app_server}/course/{E2E_COURSE}/take")
    page.locator(f'a[href*="/course/{E2E_COURSE}/resource/"]').first.click()
    page.wait_for_url(re.compile(rf"/course/{E2E_COURSE}/resource/"), timeout=15000)
    expect(page.locator("body")).to_contain_text("Lesson one")
