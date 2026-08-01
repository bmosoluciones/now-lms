# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""Regression tests for sender resolution across the two mail config sources.

Mail configuration has two sources — the environment (preferred) and the
MailConfig database row — and `_config()` owns the precedence. Several send
paths did not use it: they read the database row directly to get a sender, and
returned early when the row was absent.

That is a DIFFERENT question than the one deciding whether mail works at all, so
the two could disagree. On 2026-07-31 they did, on learn.intentsolutions.io: the
environment was fully configured and `mail_configured` reported True while the
MailConfig row was entirely NULL. Password reset and confirmation mail returned
early and sent nothing — silently, with every indicator green.

A second defect fell out of the same split: `_load_mail_config_from_env()` never
returned MAIL_DEFAULT_SENDER_NAME, but every caller reads that attribute off
whatever `_config()` handed back. paypal.py resolves correctly via `_config()`
and would therefore raise AttributeError at send time on an env-configured
deployment. The loaders must return the same shape.
"""

import sys
from types import SimpleNamespace

import pytest

from now_lms.mail import _config, _load_mail_config_from_env, resolve_sender

# NOT `from now_lms import mail as mail_module`. now_lms/__init__.py binds
# `mail = Mail()` at module scope, which SHADOWS the now_lms.mail submodule — so
# that import yields the Flask-Mail instance and any monkeypatch against it lands
# on the wrong object and silently does nothing (the real database loader then
# runs and the test fails for an unrelated reason). Go through sys.modules, which
# the shadowing cannot reach.
mail_module = sys.modules["now_lms.mail"]

ENV_KEYS = (
    "MAIL_SERVER",
    "MAIL_PORT",
    "MAIL_USERNAME",
    "MAIL_PASSWORD",
    "MAIL_DEFAULT_SENDER",
    "MAIL_DEFAULT_SENDER_NAME",
    "MAIL_USE_TLS",
    "MAIL_USE_SSL",
)


@pytest.fixture
def babel_app_context():
    """A minimal application context, because both loaders log through gettext.

    now_lms.i18n._ is flask_babel's gettext, which raises outside an application
    context — the real runtime condition, since these functions only ever run
    inside a request or an app context.

    Deliberately NOT the session `app` fixture: sender resolution touches no
    table, and pulling in the full app would couple these tests to the database
    for no reason (locally that fixture also hits the known in-memory-SQLite
    pooling problem documented in .github/workflows/deploy-line-ci.yml).
    """
    from flask import Flask
    from flask_babel import Babel

    app = Flask(__name__)
    app.config["BABEL_DEFAULT_LOCALE"] = "en"
    Babel(app)
    with app.app_context():
        yield app


@pytest.fixture
def clean_env(babel_app_context, monkeypatch):
    """Start from no mail environment at all, so each test states its own."""
    for key in ENV_KEYS:
        monkeypatch.delenv(key, raising=False)
    return monkeypatch


def _configure_env(monkeypatch, **overrides):
    values = {
        "MAIL_SERVER": "smtp.example.invalid",
        "MAIL_PORT": "587",
        "MAIL_USERNAME": "postmaster@example.invalid",
        "MAIL_PASSWORD": "s3cret",
    }
    values.update(overrides)
    for key, value in values.items():
        monkeypatch.setenv(key, value)


def _db_unconfigured(monkeypatch):
    """Stand in for an empty MailConfig table, which is what the loader raises on."""
    monkeypatch.setattr(
        mail_module,
        "_load_mail_config_from_db",
        lambda: (_ for _ in ()).throw(ValueError("No mail configuration found in database")),
    )


# ---------------------------------------------------------------------------------------
# Both loaders must return the same attributes.
# ---------------------------------------------------------------------------------------
def test_env_loader_exposes_default_sender_name(clean_env):
    """paypal.py reads this off _config()'s result; omitting it was an AttributeError."""
    _configure_env(clean_env, MAIL_DEFAULT_SENDER_NAME="Intent Solutions Learn")
    config = _load_mail_config_from_env()
    assert config.MAIL_DEFAULT_SENDER_NAME == "Intent Solutions Learn"


def test_env_loader_exposes_default_sender_name_even_when_unset(clean_env):
    """The attribute must EXIST regardless of value — absence is the crash, not None."""
    _configure_env(clean_env)
    config = _load_mail_config_from_env()
    assert config.MAIL_DEFAULT_SENDER_NAME is None


def test_both_loaders_return_the_same_shape(clean_env, monkeypatch):
    """Pin the contract that the AttributeError violated, so it cannot drift back apart."""
    _configure_env(clean_env)
    env_attrs = set(vars(_load_mail_config_from_env()))
    db_attrs = {
        "mail_configured",
        "MAIL_SERVER",
        "MAIL_PORT",
        "MAIL_USERNAME",
        "MAIL_PASSWORD",
        "MAIL_USE_TLS",
        "MAIL_USE_SSL",
        "MAIL_DEFAULT_SENDER",
        "MAIL_DEFAULT_SENDER_NAME",
    }
    assert env_attrs == db_attrs


# ---------------------------------------------------------------------------------------
# The live bug: env configured, database row empty.
# ---------------------------------------------------------------------------------------
def test_sender_resolves_from_env_when_the_database_row_is_absent(clean_env, monkeypatch):
    """THE 2026-07-31 PRODUCTION STATE. Must resolve, not return None."""
    _configure_env(clean_env, MAIL_DEFAULT_SENDER="learn@example.invalid", MAIL_DEFAULT_SENDER_NAME="Learn")
    _db_unconfigured(monkeypatch)
    assert resolve_sender() == ("Learn", "learn@example.invalid")


def test_sender_falls_back_to_the_smtp_username_when_no_default_sender_is_set(clean_env, monkeypatch):
    """MAIL_DEFAULT_SENDER is optional in both sources; the SMTP account is a real sender."""
    _configure_env(clean_env)
    _db_unconfigured(monkeypatch)
    assert resolve_sender() == ("NOW LMS", "postmaster@example.invalid")


def test_sender_name_defaults_when_unset(clean_env, monkeypatch):
    _configure_env(clean_env, MAIL_DEFAULT_SENDER="learn@example.invalid")
    _db_unconfigured(monkeypatch)
    name, _address = resolve_sender()
    assert name == "NOW LMS"


def test_resolve_sender_is_not_a_gate(clean_env, monkeypatch):
    """It answers "who is the sender", never "should we send".

    Every caller passes no_config=True to send_mail, i.e. "send regardless of
    whether the config has been verified". A mail_configured check in here would
    silently overrule them -- which is exactly the regression the first version of
    this change shipped, caught by test_auth_helpers and test_public_api against
    real PostgreSQL.

    A pair always comes back, and the address may be None — unchanged from the
    code this replaced. Returning None instead was tried and reverted: the
    "NOW LMS <None>" string flask_mail builds is truthy, and that truthiness is
    what satisfies its "no sender configured" assertion today, so returning None
    turns "mail with a broken sender" into "no mail at all". See resolve_sender's
    docstring and the bead for the real fix.
    """
    _db_unconfigured(monkeypatch)
    name, address = resolve_sender()
    assert name == "NOW LMS"
    assert address is None


def test_unverified_config_still_yields_a_sender(clean_env, monkeypatch):
    """email_verificado False must not silently suppress a no_config=True send."""
    monkeypatch.setattr(
        mail_module,
        "_load_mail_config_from_db",
        lambda: SimpleNamespace(
            mail_configured=False,
            MAIL_SERVER="smtp.db.invalid",
            MAIL_PORT="465",
            MAIL_USERNAME="db-user@example.invalid",
            MAIL_PASSWORD="db-secret",
            MAIL_USE_TLS=False,
            MAIL_USE_SSL=True,
            MAIL_DEFAULT_SENDER="from-db@example.invalid",
            MAIL_DEFAULT_SENDER_NAME="From DB",
        ),
    )
    assert resolve_sender() == ("From DB", "from-db@example.invalid")


def test_config_returns_unconfigured_instead_of_raising_when_nothing_is_set(clean_env, monkeypatch):
    """_config() used to propagate ValueError; callers branch on mail_configured."""
    _db_unconfigured(monkeypatch)
    config = _config()
    assert config.mail_configured is False


# ---------------------------------------------------------------------------------------
# The database source still wins when the environment is not configured.
# ---------------------------------------------------------------------------------------
def test_database_row_is_used_when_the_environment_is_not_configured(clean_env, monkeypatch):
    monkeypatch.setattr(
        mail_module,
        "_load_mail_config_from_db",
        lambda: SimpleNamespace(
            mail_configured=True,
            MAIL_SERVER="smtp.db.invalid",
            MAIL_PORT="465",
            MAIL_USERNAME="db-user@example.invalid",
            MAIL_PASSWORD="db-secret",
            MAIL_USE_TLS=False,
            MAIL_USE_SSL=True,
            MAIL_DEFAULT_SENDER="from-db@example.invalid",
            MAIL_DEFAULT_SENDER_NAME="From DB",
        ),
    )
    assert resolve_sender() == ("From DB", "from-db@example.invalid")





# ---------------------------------------------------------------------------------------
# The send paths that carried the bug now go through the resolver.
# ---------------------------------------------------------------------------------------
def test_no_send_path_reads_the_mailconfig_row_directly():
    """Guard the fix itself.

    auth.py and public_api.py send mail; the admin settings views EDIT the row and
    are supposed to read it. If a future change reintroduces a direct row read in a
    sending module, this fails and points at the resolver.
    """
    import inspect

    from now_lms import auth
    from now_lms.vistas import public_api

    for module in (auth, public_api):
        source = inspect.getsource(module)
        assert "select(MailConfig)" not in source, (
            f"{module.__name__} reads the MailConfig row directly. Sending code must use "
            "now_lms.mail.resolve_sender() so it honours the same env-then-database "
            "precedence as send_mail; see the 2026-07-31 silent-no-send incident."
        )
