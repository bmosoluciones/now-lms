# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 Intent Solutions

"""Contract tests for the fork-local Intent Solutions Learn front door."""

import importlib.util
from pathlib import Path

import pytest
from jinja2 import Environment


TEMPLATE_PATH = Path("now_lms/templates/themes/intent_learn/overrides/home.j2")


def _template() -> str:
    return TEMPLATE_PATH.read_text(encoding="utf-8")


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
    assert b'<html lang="en">' in response.data
    assert b'class="isl-hero-copy"' in response.data
    assert b"mailto:" in response.data


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

    assert "overflow-x: clip" in template
    assert ".isl-root *, .isl-root *::before, .isl-root *::after { box-sizing: border-box; min-width: 0; }" in template
    assert "@media (max-width: 520px)" in template
    assert "min-height: 44px" in template
    assert ":focus-visible" in template
    assert "prefers-reduced-motion: reduce" in template
    assert '<html lang="{{ current_locale() }}">' in template
    assert "site_config.contact_email" in template
    assert "_('Intent Solutions Practice — Access Request') | urlencode" in template
    assert "| urlencode" in template
    assert 'loading="lazy"' in template
    assert "isl-team-initials" in template
