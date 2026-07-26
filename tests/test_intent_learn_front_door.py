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
    assert b"mailto:" in response.data

    # RFC 6068 §2: the addr-spec in a mailto: URI carries a literal "@". Percent-encoding it
    # produced "hello%40intentsolutions.io", which mail clients treat as a local-part-only
    # address and refuse to send to. The query string after "?" is a separate matter -- see
    # test_front_door_encodes_the_mailto_subject_but_not_the_address.
    body = response.data.decode("utf-8")
    hrefs = re.findall(r'href="(mailto:[^"]*)"', body)
    assert hrefs, "the access-request CTA should render at least one mailto: link"
    for href in hrefs:
        address = href[len("mailto:") :].split("?", 1)[0]
        assert "@" in address, f"mailto: address lost its literal @: {href}"
        assert "%40" not in address, f"mailto: address percent-encoded its @: {href}"


def test_front_door_encodes_the_mailto_subject_but_not_the_address() -> None:
    """Keep the RFC 6068 split: literal @ in the address, percent-encoded subject after ?.

    Runs without the full app so the guard still fires wherever the render-path test skips.
    Applying ``| urlencode`` to the address turned it into ``hello%40intentsolutions.io``,
    which shipped to production; applying it to the subject is correct and must stay.
    """
    template = _template()
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
    assert "site_config.contact_email" in template
    assert "_('Intent Solutions Practice — Access Request') | urlencode" in template
    # The subject is encoded; the address deliberately is not (RFC 6068 §2).
    assert "contact_email or 'hello@intentsolutions.io') | urlencode" not in template
    assert 'loading="lazy"' in template
    assert "isl-team-initials" in template


def test_front_door_uses_the_composition_reset_and_canonical_legal_footer() -> None:
    """Lock the calmer hierarchy and the GetTerms-backed company policy destinations."""
    template = _template()
    css = _css()

    assert "--paper: #f3f6f4" in css
    assert "fonts.googleapis.com" not in css
    for path in (HEADER_PATH, BASE_PATH):
        assert "fonts.googleapis.com" not in path.read_text(encoding="utf-8")
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
