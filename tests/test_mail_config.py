# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""Regression tests for MAIL_USE_TLS / MAIL_USE_SSL boolean coercion.

The env loader capitalizes the raw value (str.capitalize() -> "True"/"False")
and then pattern-matches it to a real boolean. The original match arms compared
against all-caps "TRUE"/"FALSE", which str.capitalize() can never produce, so
the values stayed non-empty strings — and every non-empty string is truthy,
meaning MAIL_USE_TLS=False and MAIL_USE_SSL=False both read as *enabled* and
Flask-Mail picked SSL on a STARTTLS port. These tests pin the fixed behavior
for every spelling a .env file plausibly contains.
"""

import pytest

from now_lms.mail import _load_mail_config_from_env


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("True", True),
        ("true", True),
        ("TRUE", True),
        ("False", False),
        ("false", False),
        ("FALSE", False),
        ("", False),  # empty string must not read as enabled
        ("yes", False),  # unrecognized values are an explicit False, never a truthy string
        ("1", False),
    ],
)
def test_mail_use_tls_coerces_to_real_boolean(monkeypatch, raw, expected):
    monkeypatch.setenv("MAIL_USE_TLS", raw)
    monkeypatch.delenv("MAIL_USE_SSL", raising=False)
    config = _load_mail_config_from_env()
    assert config.MAIL_USE_TLS is expected
    assert config.MAIL_USE_SSL is False


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("True", True),
        ("TRUE", True),
        ("False", False),
        ("FALSE", False),
    ],
)
def test_mail_use_ssl_coerces_to_real_boolean(monkeypatch, raw, expected):
    monkeypatch.setenv("MAIL_USE_SSL", raw)
    monkeypatch.delenv("MAIL_USE_TLS", raising=False)
    config = _load_mail_config_from_env()
    assert config.MAIL_USE_SSL is expected


def test_tls_and_ssl_are_never_both_truthy_by_default(monkeypatch):
    """The original bug: with neither var set, BOTH flags read as enabled."""
    monkeypatch.delenv("MAIL_USE_TLS", raising=False)
    monkeypatch.delenv("MAIL_USE_SSL", raising=False)
    config = _load_mail_config_from_env()
    assert config.MAIL_USE_TLS is False
    assert config.MAIL_USE_SSL is False
