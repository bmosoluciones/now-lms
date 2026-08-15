# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.

"""The exam page is themable, and the fallback still works when a theme does not override it.

`take_evaluation` was the one learner-facing page with no override slot, so an
Intent-branded exam surface would have meant editing the shared platform template —
exactly what `FORK.md` forbids. These tests pin both halves of the slot: a theme that
ships `overrides/take_evaluation.j2` gets it, and a theme that does not falls back to
the platform template rather than 500ing.
"""

import re
from pathlib import Path

import pytest

from now_lms import lms_app
from now_lms.themes import get_take_evaluation_template

PLATFORM_TEMPLATE = "evaluations/take_evaluation.html"


@pytest.fixture
def app_context():
    """Application context; the theme lookup reads the active theme from the database."""
    with lms_app.app_context():
        yield


def _override_path(theme: str) -> Path:
    from now_lms.config import DIRECTORIO_PLANTILLAS

    return Path(DIRECTORIO_PLANTILLAS) / "themes" / theme / "overrides" / "take_evaluation.j2"


def test_falls_back_to_the_platform_template_when_the_theme_has_no_override(app_context, monkeypatch):
    """A theme with no override must not break the exam page."""
    monkeypatch.setattr("now_lms.themes.get_current_theme", lambda: "now_lms")
    assert not _override_path("now_lms").exists(), "the default theme is not supposed to override this page"
    assert get_take_evaluation_template() == PLATFORM_TEMPLATE


def test_the_intent_theme_serves_its_own_exam_surface(app_context, monkeypatch):
    """The whole point of the slot: intent_learn ships an override and it is selected."""
    monkeypatch.setattr("now_lms.themes.get_current_theme", lambda: "intent_learn")
    assert _override_path("intent_learn").exists(), "intent_learn is expected to ship the exam override"
    assert get_take_evaluation_template() == "themes/intent_learn/overrides/take_evaluation.j2"


def test_the_override_keeps_the_form_contract_the_platform_template_defines(app_context):
    """The override is a re-skin, not a re-implementation.

    The simulator only changes which item is visible; the POST payload has to stay
    byte-compatible with what `_save_question_answers` reads, or every answer is lost.
    Asserting on the source rather than a render keeps this cheap and independent of
    having a seeded evaluation to hand.
    """
    source = _override_path("intent_learn").read_text(encoding="utf-8")
    assert 'name="question_{{ question.id }}"' in source, "field name must stay question_<id>"
    assert 'value="{{ option.id }}"' in source, "multiple-choice values must stay option ids"
    assert 'value="Verdadero"' in source and 'value="Falso"' in source, "boolean values are read by text"
    assert 'method="POST"' in source

    # `required` on a hidden input makes the browser refuse to submit and then fail to
    # focus the offending control, which would strand a member on the last item. The
    # server already scores a missing answer as wrong.
    #
    # Look inside the input tags rather than grepping the file: the word "required"
    # appears in this template's own explanatory comment and in question prose, and a
    # bare substring check fails on both.
    inputs = re.findall(r"<input\b[^>]*>", source, flags=re.S)
    assert inputs, "the template is expected to render inputs"
    with_required = [tag for tag in inputs if re.search(r"\brequired\b", tag)]
    assert not with_required, f"paged form must not mark inputs required: {with_required}"
