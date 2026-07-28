# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.

"""End-to-end and contract tests for the access-request intake (/request-access).

The intake stores to the native contact_messages table with the ``[ACCESS] ``
subject discriminator, pings Slack best-effort, and defends itself (CSRF,
honeypot, timed token, rate limit, length caps). The practice-tracks teaser
tests live here too: both surfaces exist so the public site never leaks course
or vendor names to anonymous visitors.
"""

import re
from pathlib import Path

import pytest
from jinja2 import Environment

import now_lms.vistas.request_access as ra_module
from now_lms.auth import proteger_passwd
from now_lms.db import ContactMessage, Curso, Style, Usuario, database

REDIRECT_STATUS_CODES = {301, 302, 303, 307, 308}
TEASER_PATH = Path("now_lms/templates/themes/intent_learn/overrides/course_list.j2")
RA_TEMPLATE_PATH = Path("now_lms/templates/themes/intent_learn/pages/request_access.html")

VALID_DATA = {
    "name": "Ada Lovelace",
    "email": "ada@example.com",
    "links": "https://github.com/ada\nhttps://ada.dev",
    "building": "An agentic ETL pipeline that keeps eating my error budget.",
    "role_context": "Founder",
    "source": "A post",
    "website": "",
}


@pytest.fixture(autouse=True)
def _reset_rate_buckets():
    """The limiter is module state; isolate it between tests."""
    ra_module._RATE_BUCKETS.clear()
    yield
    ra_module._RATE_BUCKETS.clear()


@pytest.fixture()
def fast_ok(monkeypatch):
    """Disable the minimum-submit-time gate so happy-path POSTs store."""
    monkeypatch.setattr(ra_module, "MIN_SUBMIT_SECONDS", 0)


def _get_ts_token(client) -> str:
    """Fetch the form and extract the signed issue-time token."""
    page = client.get("/request-access").data.decode("utf-8")
    match = re.search(r'name="ts"[^>]*value="([^"]+)"', page) or re.search(r'value="([^"]+)"[^>]*name="ts"', page)
    assert match, "the request-access form did not render its ts token"
    return match.group(1)


def _post(client, ts_token, **overrides):
    data = dict(VALID_DATA, ts=ts_token)
    data.update(overrides)
    return client.post("/request-access", data=data, follow_redirects=False)


def _stored_rows(db_session):
    return (
        db_session.execute(database.select(ContactMessage).filter(ContactMessage.subject.like("[ACCESS] %"))).scalars().all()
    )


def _use_intent_learn_theme(db_session):
    from now_lms.cache import cache

    style = db_session.execute(database.select(Style)).scalar_one()
    style.theme = "intent_learn"
    db_session.commit()
    cache.clear()


# ---------------------------------------------------------------------------------------
# The intake page
# ---------------------------------------------------------------------------------------


def test_request_access_renders_anonymously(client, db_session):
    resp = client.get("/request-access")
    assert resp.status_code == 200
    body = resp.data.decode("utf-8")
    assert "isl-ra-form" in body
    assert "Request" in body and "Access" in body
    # The locked copy: soft review promise + waiting-list line + privacy line.
    assert "A person reads every request" in body
    assert "waiting list" in body
    assert "We store what you submit and use it only to review your request." in body
    # Secondary mailto path keeps its literal @ (RFC 6068).
    hrefs = re.findall(r'href="(mailto:[^"]*)"', body)
    assert hrefs, "the secondary mailto path is missing"
    for href in hrefs:
        address = href[len("mailto:") :].split("?", 1)[0]
        assert "@" in address and "%40" not in address
    # No vendor or course names leak from the public door.
    for leaked in ("Claude", "Anthropic", "CCA-"):
        assert leaked not in body


def test_post_stores_a_parseable_access_request(client, db_session, fast_ok):
    resp = _post(client, _get_ts_token(client))
    assert resp.status_code in REDIRECT_STATUS_CODES

    rows = _stored_rows(db_session)
    assert len(rows) == 1
    row = rows[0]
    assert row.subject == "[ACCESS] Ada Lovelace"
    assert row.name == "Ada Lovelace"
    assert row.email == "ada@example.com"
    assert row.status == "not_seen"
    # The labeled template stays parseable field by field.
    assert "Links to work:\nhttps://github.com/ada\nhttps://ada.dev" in row.message
    assert "What are you building / where do you want sharper judgment:" in row.message
    assert "Current role or company:\nFounder" in row.message
    assert "How they found us:\nA post" in row.message
    assert "-- Submitted via /request-access" in row.message


def test_post_confirmation_page_carries_the_locked_copy(client, db_session, fast_ok):
    resp = _post(client, _get_ts_token(client))
    confirm = client.get(resp.headers["Location"]).data.decode("utf-8")
    assert "Got it" in confirm and "on the list" in confirm
    assert "fit beats speed" in confirm


def test_honeypot_drops_the_submission_silently(client, db_session, fast_ok):
    resp = _post(client, _get_ts_token(client), website="https://spam.example")
    # A bot sees success; nothing stores.
    assert resp.status_code in REDIRECT_STATUS_CODES
    assert _stored_rows(db_session) == []


def test_faster_than_human_submission_is_dropped(client, db_session):
    # MIN_SUBMIT_SECONDS is live here: a token issued and posted immediately
    # is bot-shaped, so it is silently dropped.
    resp = _post(client, _get_ts_token(client))
    assert resp.status_code in REDIRECT_STATUS_CODES
    assert _stored_rows(db_session) == []


def test_garbage_ts_token_reprompts_without_storing(client, db_session, fast_ok):
    resp = _post(client, "not-a-signed-token")
    assert resp.status_code == 200
    assert "expired" in resp.data.decode("utf-8")
    assert _stored_rows(db_session) == []


def test_missing_required_fields_do_not_store(client, db_session, fast_ok):
    resp = _post(client, _get_ts_token(client), links="", building="")
    assert resp.status_code == 200
    assert _stored_rows(db_session) == []


def test_invalid_email_does_not_store(client, db_session, fast_ok):
    resp = _post(client, _get_ts_token(client), email="not-an-email")
    assert resp.status_code == 200
    assert _stored_rows(db_session) == []


def test_csrf_is_enforced_when_enabled(app, db_session, fast_ok, monkeypatch):
    # TESTING config disables CSRF, which would make a naive test vacuous.
    # monkeypatch.setitem (not a bare assignment) so the flag RESTORES after
    # this test: v2.0.0's conftest builds the function-scoped `app` on a
    # session-scoped shared app, and a leaked WTF_CSRF_ENABLED=True made every
    # later token-less POST in the process re-render as a 200 (found on the
    # sync branch's first PG run).
    monkeypatch.setitem(app.config, "WTF_CSRF_ENABLED", True)
    client = app.test_client()

    page = client.get("/request-access").data.decode("utf-8")
    assert 'name="csrf_token"' in page, "the form must emit the CSRF token"

    ts_match = re.search(r'name="ts"[^>]*value="([^"]+)"', page)
    resp = client.post(
        "/request-access",
        data=dict(VALID_DATA, ts=ts_match.group(1) if ts_match else ""),
        follow_redirects=False,
    )
    # Without the token the form must not validate, and nothing may store.
    assert resp.status_code == 200
    assert _stored_rows(db_session) == []

    # With the token from the page, the same submission goes through.
    csrf = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', page)
    assert csrf
    resp_ok = client.post(
        "/request-access",
        data=dict(VALID_DATA, ts=ts_match.group(1), csrf_token=csrf.group(1)),
        follow_redirects=False,
    )
    assert resp_ok.status_code in REDIRECT_STATUS_CODES
    assert len(_stored_rows(db_session)) == 1


def test_rate_limit_returns_429_after_the_window_fills(client, db_session, fast_ok):
    ts_token = _get_ts_token(client)
    for _ in range(ra_module._RATE_LIMIT_POSTS):
        resp = _post(client, ts_token)
        assert resp.status_code in REDIRECT_STATUS_CODES
    resp = _post(client, ts_token)
    assert resp.status_code == 429
    assert len(_stored_rows(db_session)) == ra_module._RATE_LIMIT_POSTS


def test_crlf_is_stripped_from_header_shaped_fields(app, db_session):
    with app.test_request_context("/request-access"):
        form = ra_module.RequestAccessForm(
            data=dict(VALID_DATA, name="Eve\r\nInjected", email="eve@example.com\r\nBcc: x"),
            meta={"csrf": False},
        )
        ra_module._store_request(form)
    row = _stored_rows(db_session)[0]
    assert "\r" not in row.name and "\n" not in row.name
    assert "\r" not in row.email and "\n" not in row.email


def test_subject_truncates_to_the_column_limit(app, db_session):
    with app.test_request_context("/request-access"):
        form = ra_module.RequestAccessForm(
            data=dict(VALID_DATA, name="N" * 400),
            meta={"csrf": False},
        )
        ra_module._store_request(form)
    row = _stored_rows(db_session)[0]
    assert len(row.subject) <= ra_module.SUBJECT_MAX
    assert len(row.name) <= ra_module.NAME_MAX
    assert row.subject.startswith("[ACCESS] ")


# ---------------------------------------------------------------------------------------
# Slack ping (best-effort by contract)
# ---------------------------------------------------------------------------------------


def test_slack_ping_sends_name_but_never_email(client, db_session, fast_ok, monkeypatch):
    sent = {}

    class _FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    def fake_urlopen(req, timeout=0):
        sent["url"] = req.full_url
        sent["body"] = req.data.decode("utf-8")
        return _FakeResponse()

    monkeypatch.setenv("SLACK_WEBHOOK_LEADS_CONTACT", "https://hooks.slack.example/T000/B000")
    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    resp = _post(client, _get_ts_token(client))
    assert resp.status_code in REDIRECT_STATUS_CODES
    assert sent["url"] == "https://hooks.slack.example/T000/B000"
    assert "Ada Lovelace" in sent["body"]
    assert "ada@example.com" not in sent["body"], "the ping must not carry the applicant's email"
    assert '"unfurl_links": false' in sent["body"]
    # The admin link is a path, never a host-derived external URL: a crafted
    # Host header on the public POST must not be able to poison the staff link.
    assert "/admin/contact-messages" in sent["body"]
    assert "localhost" not in sent["body"]


def test_slack_failure_never_breaks_the_submission(client, db_session, fast_ok, monkeypatch):
    def exploding_urlopen(*args, **kwargs):
        raise OSError("slack is down")

    monkeypatch.setenv("SLACK_WEBHOOK_LEADS_CONTACT", "https://hooks.slack.example/T000/B000")
    monkeypatch.setattr("urllib.request.urlopen", exploding_urlopen)

    resp = _post(client, _get_ts_token(client))
    assert resp.status_code in REDIRECT_STATUS_CODES
    assert len(_stored_rows(db_session)) == 1


def test_unset_webhook_env_still_stores(client, db_session, fast_ok, monkeypatch):
    monkeypatch.delenv("SLACK_WEBHOOK_LEADS_CONTACT", raising=False)
    resp = _post(client, _get_ts_token(client))
    assert resp.status_code in REDIRECT_STATUS_CODES
    assert len(_stored_rows(db_session)) == 1


# ---------------------------------------------------------------------------------------
# Admin surface
# ---------------------------------------------------------------------------------------


def _login_admin(app, db_session):
    admin = Usuario(
        usuario="admin",
        acceso=proteger_passwd("admin"),
        nombre="Admin",
        correo_electronico="admin@example.com",
        tipo="admin",
        activo=True,
    )
    db_session.add(admin)
    db_session.commit()
    client = app.test_client()
    client.post("/user/login", data={"usuario": "admin", "acceso": "admin"}, follow_redirects=False)
    return client


def test_admin_list_filters_by_subject_and_shows_the_request(app, client, db_session, fast_ok):
    resp = _post(client, _get_ts_token(client))
    assert resp.status_code in REDIRECT_STATUS_CODES
    db_session.add(ContactMessage(name="Otro", email="o@example.com", subject="Unrelated", message="x", status="not_seen"))
    db_session.commit()

    admin_client = _login_admin(app, db_session)
    listing = admin_client.get("/admin/contact-messages?q=[ACCESS]")
    assert listing.status_code == 200
    assert b"Ada Lovelace" in listing.data
    assert b"Unrelated" not in listing.data

    row = _stored_rows(db_session)[0]
    detail = admin_client.get(f"/admin/contact-messages/{row.id}/view")
    assert detail.status_code == 200
    assert b"Links to work:" in detail.data


# ---------------------------------------------------------------------------------------
# The practice-tracks teaser (/course/explore) and gated courses
# ---------------------------------------------------------------------------------------


def test_explore_serves_the_teaser_to_anonymous_visitors(client, db_session):
    _use_intent_learn_theme(db_session)
    resp = client.get("/course/explore")
    assert resp.status_code == 200
    body = resp.data.decode("utf-8")
    assert "isl-tracks-list" in body
    assert "/request-access" in body
    # Doctrine copy, including the founder-approved honesty sentence.
    assert "One practice." in body
    assert "That invitation is earned, not sold." in body
    # Zero course cards, zero vendor names — even with public courses in the DB.
    assert "isl-course-grid" not in body
    for leaked in ("Claude", "Anthropic", "CCA-"):
        assert leaked not in body


def test_explore_shows_members_the_panel_pointer(app, db_session):
    _use_intent_learn_theme(db_session)
    student = Usuario(
        usuario="student",
        acceso=proteger_passwd("student"),
        nombre="Student",
        correo_electronico="s@example.com",
        tipo="student",
        activo=True,
    )
    db_session.add(student)
    db_session.commit()
    client = app.test_client()
    client.post("/user/login", data={"usuario": "student", "acceso": "student"}, follow_redirects=False)

    body = client.get("/course/explore").data.decode("utf-8")
    assert "isl-tracks-list" in body
    assert "go to your dashboard" in body


def test_gated_course_redirects_anonymous_to_the_intake(client, db_session):
    curso = Curso(
        codigo="GATED01",
        nombre="Hidden Course",
        descripcion_corta="hidden",
        descripcion="hidden",
        estado="open",
        publico=False,
    )
    db_session.add(curso)
    db_session.commit()

    resp = client.get("/course/GATED01/view", follow_redirects=False)
    assert resp.status_code in REDIRECT_STATUS_CODES
    assert "/request-access" in resp.headers["Location"]


# ---------------------------------------------------------------------------------------
# File-level contract tests (run even without the full app installed)
# ---------------------------------------------------------------------------------------


def test_teaser_template_parses_and_carries_the_locked_copy():
    template = TEASER_PATH.read_text(encoding="utf-8")
    Environment().parse(template)
    assert "One practice." in template
    assert "Several ways to prove it." in template
    assert "house core" in template
    assert "Some members are invited onto client work that comes through Intent Solutions." in template
    assert "That invitation is earned, not sold." in template
    assert "request_access.request_access" in template
    # The teaser must not iterate the course queryset.
    assert "cursos.items" not in template
    assert "curso.nombre" not in template


def test_request_access_template_is_autoescaped_html_with_defenses():
    template = RA_TEMPLATE_PATH.read_text(encoding="utf-8")
    Environment().parse(template)
    # .html extension => Flask autoescaping. The .j2 overrides are NOT autoescaped,
    # so this page (which re-renders visitor input on validation errors) must stay .html.
    assert RA_TEMPLATE_PATH.suffix == ".html"
    assert "form.csrf_token" in template
    assert "isl-ra-hp" in template  # honeypot wrapper
    assert "{{ form.ts }}" in template  # signed issue-time token
    assert "intentsolutions.io/privacy" in template
