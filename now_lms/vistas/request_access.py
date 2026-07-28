# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""Access-request intake (waiting list).

Fork-local blueprint: renders the themed request-access page and stores each
submission as a native :class:`ContactMessage` row so the stock admin surface at
``/admin/contact-messages`` (status workflow, notes, unseen badge) manages the
waiting list without a new table or migration. Requests are discriminated by an
ASCII subject prefix (``[ACCESS] ``) so they stay trivially queryable.

The optional Slack webhook notification papers over a genuine upstream gap (no
notification hook on new contact messages); it is best-effort by design — the
database row is the durability, the ping is only the alert. Once a generic
``CONTACT_WEBHOOK_URL`` feature lands upstream this module's ping code is
dropped in its favor.

This file deliberately imports nothing from ``static_pages.py`` (that module is
removed by the upstream v2.0.0 split) so the route survives the sync.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------
import json
import re
import threading
import urllib.request
from collections import deque
from os import environ
from time import time

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------
from flask import Blueprint, current_app, redirect, render_template, request, url_for
from flask_wtf import FlaskForm
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from werkzeug.wrappers import Response
from wtforms import HiddenField, StringField, TextAreaField
from wtforms.validators import DataRequired, Length, Regexp

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms.config import DIRECTORIO_PLANTILLAS
from now_lms.db import ContactMessage, database
from now_lms.i18n import _, _l
from now_lms.logs import log

request_access_bp = Blueprint("request_access", __name__, template_folder=DIRECTORIO_PLANTILLAS)

TEMPLATE = "themes/intent_learn/pages/request_access.html"

# ASCII discriminator for waiting-list rows in contact_messages. Never wrapped in
# gettext: the admin filter and the canonical query
# (WHERE subject LIKE '[ACCESS] %') depend on the literal bytes.
ACCESS_SUBJECT_PREFIX = "[ACCESS] "
SUBJECT_MAX = 200  # ContactMessage.subject is String(200)

# Server-side length caps (also enforced by the form validators; the hard
# truncation below is the defense in depth before the INSERT).
NAME_MAX = 150  # ContactMessage.name is String(150)
EMAIL_MAX = 150  # ContactMessage.email is String(150)
LINKS_MAX = 2000
BUILDING_MAX = 4000
ROLE_MAX = 200
SOURCE_MAX = 200

# Anti-abuse: a human cannot fill four required fields in under this many seconds.
MIN_SUBMIT_SECONDS = 3
# A form left open longer than this must be refreshed (also bounds token replay).
MAX_TOKEN_AGE_SECONDS = 4 * 60 * 60
_TS_SALT = "request-access-form"

# In-process sliding-window rate limit for POSTs. Deliberately not the repo's
# check_rate_limit helper: that is a silent no-op under NullCache (the production
# cache config). Correct under waitress single-process/multi-thread; Caddy's
# rate_limit is the outer wall.
_RATE_LIMIT_POSTS = 5
_RATE_LIMIT_WINDOW = 900  # seconds
_RATE_LOCK = threading.Lock()
_RATE_BUCKETS: dict[str, deque] = {}


class RequestAccessForm(FlaskForm):
    """Vetting-grade access request: the work sample is the application."""

    name = StringField(_l("Your name"), validators=[DataRequired(), Length(max=NAME_MAX)])
    email = StringField(
        _l("Email"),
        validators=[
            DataRequired(),
            Length(max=EMAIL_MAX),
            Regexp(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", message=_l("Enter a valid email address.")),
        ],
    )
    links = TextAreaField(_l("Links to your work"), validators=[DataRequired(), Length(max=LINKS_MAX)])
    building = TextAreaField(
        _l("What are you building? Where do you want sharper production judgment?"),
        validators=[DataRequired(), Length(max=BUILDING_MAX)],
    )
    role_context = StringField(_l("Current role or company"), validators=[Length(max=ROLE_MAX)])
    source = StringField(_l("How did you find us?"), validators=[Length(max=SOURCE_MAX)])
    # Honeypot: hidden from humans by CSS; any value means a bot filled it.
    website = StringField()
    # Signed issue-time token: too-young means a bot, too-old means a stale tab.
    ts = HiddenField()


def _ts_serializer() -> URLSafeTimedSerializer:
    """Signer for the form issue-time token."""
    return URLSafeTimedSerializer(current_app.secret_key or "", salt=_TS_SALT)


def _issue_ts_token() -> str:
    """Return a fresh signed issue-time token."""
    return _ts_serializer().dumps("ra")


def _token_age_seconds(token: str) -> float | None:
    """Return the token's age in seconds, or None when invalid/expired."""
    try:
        _payload, issued_at = _ts_serializer().loads(token, max_age=MAX_TOKEN_AGE_SECONDS, return_timestamp=True)
    except (BadSignature, SignatureExpired):
        return None
    return time() - issued_at.timestamp()


def _rate_limited(ip: str) -> bool:
    """Sliding-window POST limit per client IP; True when over the limit."""
    now = time()
    with _RATE_LOCK:
        bucket = _RATE_BUCKETS.setdefault(ip, deque())
        while bucket and now - bucket[0] > _RATE_LIMIT_WINDOW:
            bucket.popleft()
        if len(bucket) >= _RATE_LIMIT_POSTS:
            return True
        bucket.append(now)
        # Bounded memory: expire other IPs' stale entries, then drop drained
        # buckets. Without the expiry pass, one-shot IPs that never return
        # would hold their timestamps (and their bucket) forever.
        if len(_RATE_BUCKETS) > 1000:
            for key, other in list(_RATE_BUCKETS.items()):
                if key == ip:
                    continue
                while other and now - other[0] > _RATE_LIMIT_WINDOW:
                    other.popleft()
                if not other:
                    del _RATE_BUCKETS[key]
        return False


def _strip_crlf(value: str) -> str:
    """Remove CR/LF so header-shaped fields cannot forge log or message lines."""
    return re.sub(r"[\r\n]+", " ", value).strip()


def _compose_message(form: RequestAccessForm) -> str:
    """Compose the labeled, parseable message body stored in ContactMessage."""
    return (
        "Links to work:\n"
        f"{form.links.data.strip()[:LINKS_MAX]}\n\n"
        "What are you building / where do you want sharper judgment:\n"
        f"{form.building.data.strip()[:BUILDING_MAX]}\n\n"
        "Current role or company:\n"
        f"{_strip_crlf(form.role_context.data or '-')[:ROLE_MAX] or '-'}\n\n"
        "How they found us:\n"
        f"{_strip_crlf(form.source.data or '-')[:SOURCE_MAX] or '-'}\n\n"
        "-- Submitted via /request-access"
    )


def _notify_slack(name: str, building_snippet: str) -> None:
    """Best-effort Slack ping to the leads channel. Never raises.

    Temporary fork-local mechanism pending an upstream CONTACT_WEBHOOK_URL
    feature. Sends only the applicant's name and a snippet of what they are
    building plus the admin deep-link — never the email address or employer.
    """
    webhook = environ.get("SLACK_WEBHOOK_LEADS_CONTACT")
    if not webhook:
        log.warning("SLACK_WEBHOOK_LEADS_CONTACT is not set; access request stored without a Slack ping.")
        return
    try:
        # Path only, never _external=True: an external URL would be derived from
        # the request Host header, letting a crafted POST poison the staff-facing
        # link (Greptile P1 on PR #25). Staff open it against the admin origin.
        admin_path = url_for("static_pages.list_contact_messages") + "?q=%5BACCESS%5D"
        payload = {
            "text": f"New access request: {name}",
            "unfurl_links": False,
            "unfurl_media": False,
            "blocks": [
                {
                    "type": "header",
                    "text": {"type": "plain_text", "text": "New access request", "emoji": False},
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "plain_text", "text": name[:150], "emoji": False},
                        {"type": "plain_text", "text": building_snippet[:250] or "-", "emoji": False},
                    ],
                },
                {
                    "type": "section",
                    "text": {"type": "plain_text", "text": f"Review in the admin panel: {admin_path}", "emoji": False},
                },
            ],
        }
        req = urllib.request.Request(
            webhook,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5):  # nosec B310 - env-provided https webhook
            pass
    except Exception as error:  # pylint: disable=broad-exception-caught
        # The DB row is the durability; a notification failure must never
        # surface to the visitor or roll back the stored request.
        log.warning(f"Slack ping for access request failed: {error}")


def _store_request(form: RequestAccessForm) -> None:
    """Persist the access request as a native contact message row."""
    name = _strip_crlf(form.name.data)[:NAME_MAX]
    contact_msg = ContactMessage(
        name=name,
        email=_strip_crlf(form.email.data)[:EMAIL_MAX],
        subject=(ACCESS_SUBJECT_PREFIX + name)[:SUBJECT_MAX],
        message=_compose_message(form),
        status="not_seen",
    )
    database.session.add(contact_msg)
    database.session.commit()
    _notify_slack(name, form.building.data.strip().splitlines()[0] if form.building.data.strip() else "")


@request_access_bp.route("/request-access", methods=["GET", "POST"])
def request_access() -> str | Response | tuple[str, int]:
    """Public access-request page: the front door's conversion event."""
    sent_url = url_for("request_access.request_access", sent="1")

    if request.method == "POST":
        if _rate_limited(request.remote_addr or "unknown"):
            form = RequestAccessForm()
            form.ts.data = _issue_ts_token()
            return (
                render_template(
                    TEMPLATE,
                    form=form,
                    sent=False,
                    form_error=_("Too many requests from this address. Please try again later."),
                ),
                429,
            )

        form = RequestAccessForm()
        if form.validate_on_submit():
            # Bots: pretend success so the honeypot stays useful. Nothing stores.
            if form.website.data:
                log.warning("Access request dropped: honeypot field was filled.")
                return redirect(sent_url)
            age = _token_age_seconds(form.ts.data or "")
            if age is None:
                form.ts.data = _issue_ts_token()
                return render_template(
                    TEMPLATE,
                    form=form,
                    sent=False,
                    form_error=_("The form expired. Please submit it again."),
                )
            if age < MIN_SUBMIT_SECONDS:
                log.warning("Access request dropped: submitted faster than a human can type.")
                return redirect(sent_url)

            _store_request(form)
            return redirect(sent_url)

        form.ts.data = _issue_ts_token()
        return render_template(TEMPLATE, form=form, sent=False, form_error=None)

    form = RequestAccessForm()
    form.ts.data = _issue_ts_token()
    return render_template(TEMPLATE, form=form, sent=request.args.get("sent") == "1", form_error=None)
