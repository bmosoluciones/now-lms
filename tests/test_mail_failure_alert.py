# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""Regression tests for the mail-delivery failure alert.

send_mail(background=True) sends in a thread and turns every failure into a log
line. Mail was switched on for the first time in this deployment's life on
2026-07-31; without an alert the first signal that SMTP auth expired or the
provider began rate-limiting would be a member saying "I never got the email".

Three properties matter and each is pinned here:

1. It never raises. It runs in the except arm of a background thread, so an
   exception there would replace a delivery failure with a thread crash and lose
   the log line that is currently the only record.
2. It does not put member email addresses in Slack. Domains only — matching the
   /request-access ping, which deliberately never sends an applicant's address
   off-platform.
3. It throttles. An SMTP outage fails every queued send; one POST per failure
   would make the alert channel the second outage.
"""

import sys
from types import SimpleNamespace

import pytest

from now_lms.mail import _redact_addresses, _redact_recipients, _should_alert, notify_mail_failure

# Reach the module object through sys.modules, NOT `from now_lms import mail`:
# now_lms/__init__.py binds `mail = Mail()` and shadows the submodule, so that
# import yields the Flask-Mail instance and monkeypatching it does nothing.
# The import above is what puts the key in sys.modules, so it has to come first.
mail_module = sys.modules["now_lms.mail"]


@pytest.fixture(autouse=True)
def reset_throttle():
    """Each test starts with an empty throttle window."""
    mail_module._alert_last_sent.clear()
    yield
    mail_module._alert_last_sent.clear()


@pytest.fixture
def captured_posts(monkeypatch):
    """Capture what would have been POSTed, instead of hitting the network."""
    posts = []

    class _Response:
        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

    def fake_urlopen(request, timeout=None):
        posts.append({"url": request.full_url, "body": request.data.decode("utf-8")})
        return _Response()

    monkeypatch.setattr(mail_module.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setenv("SLACK_WEBHOOK_LEADS_CONTACT", "https://hooks.slack.invalid/services/T/B/x")
    return posts


def _msg(recipients=("member@example.invalid",), subject="Password reset"):
    return SimpleNamespace(subject=subject, recipients=list(recipients))


# ---------------------------------------------------------------------------------------
# 1. Never raises.
# ---------------------------------------------------------------------------------------
def test_alert_never_raises_when_the_webhook_is_unset(monkeypatch):
    monkeypatch.delenv("SLACK_WEBHOOK_LEADS_CONTACT", raising=False)
    notify_mail_failure(_msg(), RuntimeError("smtp down"))  # must not raise


def test_alert_never_raises_when_the_post_itself_fails(monkeypatch):
    monkeypatch.setenv("SLACK_WEBHOOK_LEADS_CONTACT", "https://hooks.slack.invalid/x")

    def boom(*_args, **_kwargs):
        raise OSError("network unreachable")

    monkeypatch.setattr(mail_module.urllib.request, "urlopen", boom)
    notify_mail_failure(_msg(), RuntimeError("smtp down"))  # must not raise


def test_alert_never_raises_on_a_malformed_message(captured_posts):
    notify_mail_failure(SimpleNamespace(subject=None, recipients=None), RuntimeError("smtp down"))


# ---------------------------------------------------------------------------------------
# 2. No member addresses leave the platform.
# ---------------------------------------------------------------------------------------
def test_alert_body_carries_the_domain_and_not_the_address(captured_posts):
    notify_mail_failure(_msg(["member@example.invalid"]), RuntimeError("smtp down"))
    assert len(captured_posts) == 1
    body = captured_posts[0]["body"]
    assert "example.invalid" in body
    assert "member@example.invalid" not in body
    assert "member" not in body


def test_redaction_deduplicates_and_caps_domains():
    recipients = [f"a{i}@example.invalid" for i in range(5)] + ["b@other.invalid"]
    redacted = _redact_recipients(recipients)
    assert "@" not in redacted
    assert redacted == "example.invalid, other.invalid"


def test_redaction_survives_a_recipient_without_an_at_sign():
    assert _redact_recipients(["not-an-address"]) == "1 recipient(s)"


def test_the_exception_text_is_redacted_too(captured_posts):
    """Greptile P1 on PR #60: redacting the recipient list is not enough.

    smtplib raises SMTPRecipientsRefused with a dict KEYED BY the rejected
    address, and providers echo the address back in the 5xx string. Sending the
    exception through unredacted would defeat the recipient redaction entirely.
    """
    error = RuntimeError("SMTPRecipientsRefused: {'member@example.invalid': (550, b'User unknown')}")
    notify_mail_failure(_msg(), error)
    body = captured_posts[0]["body"]
    assert "member@example.invalid" not in body
    assert "example.invalid" in body          # the domain still survives, for diagnosis
    assert "550" in body                      # and so does the actual failure reason


def test_known_recipients_are_redacted_whatever_shape_they_take(captured_posts):
    """Greptile's follow-up: no ASCII pattern covers every address form.

    Quoted local parts, IP-literal domains and internationalised domains all slip
    past the regex. We do not have to guess though -- the recipients are already
    in hand, so they are removed by exact match before the pattern runs.
    """
    exotic = '"john doe"@example.invalid'
    error = RuntimeError(f"SMTPRecipientsRefused: {{{exotic!r}: (550, b'nope')}}")
    notify_mail_failure(_msg([exotic]), error)
    body = captured_posts[0]["body"]
    assert "john doe" not in body
    assert "example.invalid" in body


def test_redact_addresses_keeps_the_domain_and_drops_the_local_part():
    out = _redact_addresses("rejected a@b.invalid and c.d+tag@e.f.invalid")
    assert "a@b.invalid" not in out
    assert "c.d+tag@e.f.invalid" not in out
    assert "b.invalid" in out
    assert "e.f.invalid" in out


def test_redact_addresses_leaves_ordinary_text_alone():
    assert _redact_addresses("connection timed out after 30s") == "connection timed out after 30s"


def test_alert_reports_the_error_and_subject(captured_posts):
    notify_mail_failure(_msg(subject="Password reset"), ValueError("bad credentials"))
    body = captured_posts[0]["body"]
    assert "ValueError" in body
    assert "bad credentials" in body
    assert "Password reset" in body


# ---------------------------------------------------------------------------------------
# 3. Throttling: an outage must not become a Slack flood.
# ---------------------------------------------------------------------------------------
def test_repeated_failures_of_the_same_kind_post_once(captured_posts):
    for _ in range(25):
        notify_mail_failure(_msg(), RuntimeError("smtp down"))
    assert len(captured_posts) == 1, "an SMTP outage must not turn every queued send into a Slack POST"


def test_a_different_failure_kind_still_gets_through(captured_posts):
    notify_mail_failure(_msg(), RuntimeError("smtp down"))
    notify_mail_failure(_msg(), ValueError("bad credentials"))
    assert len(captured_posts) == 2


def test_throttle_window_reopens(captured_posts, monkeypatch):
    notify_mail_failure(_msg(), RuntimeError("smtp down"))
    # Age the recorded timestamp past the window rather than sleeping through it.
    for key in mail_module._alert_last_sent:
        mail_module._alert_last_sent[key] -= mail_module._ALERT_THROTTLE_SECONDS + 1
    notify_mail_failure(_msg(), RuntimeError("smtp down"))
    assert len(captured_posts) == 2


def test_should_alert_is_true_once_then_false():
    assert _should_alert("SomeError") is True
    assert _should_alert("SomeError") is False


# ---------------------------------------------------------------------------------------
# Wiring: the background sender actually calls it.
# ---------------------------------------------------------------------------------------
def test_background_sender_alerts_on_failure(monkeypatch):
    """Guard the call site, not just the function.

    An alert nobody invokes is the same as no alert, and the except arm in
    send_threaded_email is exactly the line that used to end at a log call.
    """
    from flask import Flask

    from flask_babel import Babel

    app = Flask(__name__)
    app.config["BABEL_DEFAULT_LOCALE"] = "en"
    Babel(app)

    alerts = []
    monkeypatch.setattr(mail_module, "notify_mail_failure", lambda msg, err: alerts.append((msg, err)))

    class _ExplodingMail:
        def send(self, _msg):
            raise RuntimeError("smtp down")

    mail_module.send_threaded_email(app, _ExplodingMail(), _msg())
    assert len(alerts) == 1
    assert isinstance(alerts[0][1], RuntimeError)
