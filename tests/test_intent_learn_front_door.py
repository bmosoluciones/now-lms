# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 Intent Solutions

"""Contract tests for the fork-local Intent Solutions Learn front door."""

import importlib.util
import re
from pathlib import Path

import pytest
from jinja2 import Environment

TEMPLATE_PATH = Path("now_lms/templates/themes/intent_learn/overrides/home.j2")
CSS_PATH = Path("now_lms/static/themes/intent_learn/front-door.css")
HEADER_PATH = Path("now_lms/templates/themes/intent_learn/header.j2")
BASE_PATH = Path("now_lms/templates/themes/intent_learn/base.j2")
JS_PATH = Path("now_lms/templates/themes/intent_learn/js.j2")
REQUEST_ACCESS_PATH = Path("now_lms/templates/themes/intent_learn/pages/request_access.html")


def _template() -> str:
    return TEMPLATE_PATH.read_text(encoding="utf-8")


def _css() -> str:
    return CSS_PATH.read_text(encoding="utf-8")


def test_front_door_template_parses() -> None:
    """Catch malformed Jinja before the fork-local theme reaches production."""
    Environment().parse(_template())


@pytest.mark.skipif(importlib.util.find_spec("flask_alembic") is None, reason="full app dependencies are not installed")
def test_front_door_renders_through_the_flask_route(client, db_session) -> None:
    """Exercise the real theme resolver, URL endpoints, and Jinja globals."""
    from now_lms.cache import cache
    from now_lms.db import Style, database

    style = db_session.execute(database.select(Style)).scalar_one()
    style.theme = "intent_learn"
    db_session.commit()
    cache.clear()

    response = client.get("/")

    assert response.status_code == 200
    # The default configured locale is Spanish, so this asserts a well-formed lang attribute
    # from current_locale() rather than hardcoding "en" -- which never held on the real route.
    assert re.search(rb'<html lang="[a-z]{2}(-[A-Za-z]{2,8})?">', response.data)
    assert b'class="isl-hero-copy"' in response.data

    # The access CTA lands on the stored intake, not a raw mailto. The mailto lives
    # on /request-access as the secondary "prefer email?" path -- its RFC 6068
    # guards moved to test_request_access_page_keeps_the_rfc6068_mailto_split and
    # tests/test_request_access.py.
    body = response.data.decode("utf-8")
    assert 'href="/request-access"' in body, "the access-request CTA should land on the intake"


def test_request_access_page_keeps_the_rfc6068_mailto_split() -> None:
    """Keep the RFC 6068 split: literal @ in the address, percent-encoded subject after ?.

    Runs without the full app so the guard still fires wherever the render-path test skips.
    Applying ``| urlencode`` to the address turned it into ``hello%40intentsolutions.io``,
    which shipped to production; applying it to the subject is correct and must stay.
    The mailto assembly moved from home.j2 to the request-access page when the
    front-door CTA became the stored intake.
    """
    template = REQUEST_ACCESS_PATH.read_text(encoding="utf-8")
    setup = "\n".join(line for line in template.splitlines() if "{% set access_" in line)
    assert "access_email" in setup, "the mailto: assembly moved -- update this test"

    env = Environment()
    env.globals.update(config=lambda: type("C", (), {"contact_email": "hello@intentsolutions.io"})())
    rendered = env.from_string(
        "{% set site_config = config() %}" + setup + "{{ access_email }}",
    ).render(_=lambda s: s)

    address, _sep, query = rendered.strip().partition("?")
    assert address == "mailto:hello@intentsolutions.io"
    assert "%40" not in address
    # The subject must be encoded: an unescaped space or em dash in the query breaks the URI.
    assert query.startswith("subject=")
    assert " " not in query
    assert "%20" in query or "+" in query


def test_front_door_expresses_the_selective_practice_doctrine() -> None:
    """Keep the public positioning aligned with the private operating model."""
    template = _template()

    required_language = (
        "Selective AI implementation practice",
        "model-agnostic room for serious practitioners",
        "Intent Solutions house method",
        "Credentials are optional. Production standards are not.",
        "A practice,",
        "not a course catalog.",
        "Invitation only",
        "No credential required",
    )
    for phrase in required_language:
        assert phrase in template

    forbidden_public_claims = (
        "outsourcing bench",
        "hire our certified",
        "get certified",
        "start your ai journey",
        "beginner academy",
    )
    lowered = template.lower()
    for phrase in forbidden_public_claims:
        assert phrase not in lowered


def test_front_door_carries_mobile_overflow_and_accessibility_guards() -> None:
    """Protect the narrow mobile layout that previously appeared stretched."""
    template = _template()
    css = _css()
    assert '<link rel="stylesheet" href="{{ S }}/front-door.css" />' in template
    assert "<style>" not in template
    assert "overflow-x: clip" in css
    assert ".isl-root *::before" in css
    assert "min-width: 0" in css
    assert "@media (max-width: 520px)" in css
    assert "min-height: 44px" in css
    assert ":focus-visible" in css
    assert "prefers-reduced-motion: reduce" in css
    assert ".isl-btn-sm { min-height: 44px" in css
    assert '<html lang="{{ current_locale() }}">' in template
    assert 'loading="lazy"' in template
    assert "isl-team-initials" in template

    # The mailto assembly lives on the request-access page now; same guards there.
    ra_template = REQUEST_ACCESS_PATH.read_text(encoding="utf-8")
    assert "site_config.contact_email" in ra_template
    assert "_('Intent Solutions Practice — Access Request') | urlencode" in ra_template
    # The subject is encoded; the address deliberately is not (RFC 6068 §2).
    assert "contact_email or 'hello@intentsolutions.io') | urlencode" not in ra_template


def test_front_door_uses_the_composition_reset_and_canonical_legal_footer() -> None:
    """Lock the calmer hierarchy and the GetTerms-backed company policy destinations."""
    template = _template()
    css = _css()

    assert "--paper: #f3f6f4" in css
    assert "fonts.googleapis.com" not in css
    for path in (HEADER_PATH, BASE_PATH, JS_PATH):
        chrome = path.read_text(encoding="utf-8")
        assert "fonts.googleapis.com" not in chrome
        # Same privacy/CSP boundary as the fonts: no third-party CDN loads, ever.
        # Both prior offenders were dead code -- ionicons in base.j2 (nothing renders
        # <ion-icon>; icons are self-hosted bootstrap-icons) and an unversioned AlpineJS
        # in js.j2 (no Alpine directive exists in any template, theme or core). Upstream's
        # v2.0.0 Content-Security-Policy blocks unpkg.com anyway. Vendor, don't hotlink.
        assert "unpkg.com" not in chrome
        assert "cdn.jsdelivr.net" not in chrome
    assert "font-size: clamp(3rem, 5.1vw, 4.65rem)" in css
    assert ".isl-standard-step .n { display: none; }" in css
    assert "border-radius: 0;" in css

    legal_links = {
        "Terms of Service": "https://intentsolutions.io/terms",
        "Privacy Policy": "https://intentsolutions.io/privacy",
        "Acceptable Use": "https://intentsolutions.io/acceptable-use",
    }
    for label, url in legal_links.items():
        assert label in template
        assert url in template

    # The Anthropic Claude Partner credential embeds as Credly's plain https iframe,
    # never their embed.js: that script loads from cdn.credly.com, which breaks the
    # theme's no-CDN-script rule and is refused by upstream v2.0.0's CSP script-src.
    # The iframe passes both (frame-src 'self' https:) and renders identically.
    assert "www.credly.com/embedded_badge/ddf22fb4-0aa6-46b3-a93b-0b45b509e471" in template
    assert "cdn.credly.com" not in template
    assert "embed.js" not in template
