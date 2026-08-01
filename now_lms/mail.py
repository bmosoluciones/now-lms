# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.

"""Email functionality for NOW LMS."""

from __future__ import annotations

# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------
import json
import re
import threading
import urllib.request
from os import environ
from time import monotonic
from types import SimpleNamespace

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------
from flask import Flask, current_app, flash
from flask_mail import Mail, Message

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms.auth import descifrar_secreto
from now_lms.config import DESARROLLO
from now_lms.db import MailConfig, database
from now_lms.i18n import _
from now_lms.logs import LOG_LEVEL
from now_lms.logs import log as logger

# ---------------------------------------------------------------------------------------
# Configuración de tipos.
# ---------------------------------------------------------------------------------------
MAIL_SERVER: str | bool | dict | None = None
MAIL_PORT: str | bool | dict | None = None
MAIL_USERNAME: str | bool | dict | None = None
MAIL_PASSWORD: str | bool | dict | None = None
MAIL_USE_TLS: str | bool | dict | None = None
MAIL_USE_SSL: str | bool | dict | None = None
MAIL_DEFAULT_SENDER: str | bool | dict | None = None
mail_configured: bool = False


# ---------------------------------------------------------------------------------------
# Load setting from environment variables
# ---------------------------------------------------------------------------------------
def _load_mail_config_from_env() -> SimpleNamespace:
    """Carga la configuración de correo electrónico desde las variables de entorno."""
    logger.trace("Obteniendo configuración de correo electronico desde variables de entorno.")
    # Server name and user credentials
    mail_server = environ.get("MAIL_SERVER", None)
    mail_port = environ.get("MAIL_PORT", None)
    mail_username = environ.get("MAIL_USERNAME", None)
    mail_password = environ.get("MAIL_PASSWORD", None)
    if mail_server and mail_port and mail_username and mail_password:
        logger.debug(_("Configuración de correo electrónico cargada desde variables de entorno."))
        is_mail_configured = True
    else:
        logger.trace(_("No se encontró configuración de correo electrónico en variables de entorno."))
        is_mail_configured = False
    # TLS/SSL settings
    mail_use_tls = environ.get("MAIL_USE_TLS", "False").capitalize()
    mail_use_ssl = environ.get("MAIL_USE_SSL", "False").capitalize()
    # Default sender. MAIL_DEFAULT_SENDER_NAME is read here as well as in the
    # database loader: every caller that builds a Message reads BOTH attributes
    # off whatever _config() returned, so omitting it from this branch made an
    # env-configured deployment raise AttributeError at send time (paypal.py's
    # receipt mail did exactly that). The two loaders must return the same shape.
    mail_default_sender = environ.get("MAIL_DEFAULT_SENDER")
    mail_default_sender_name = environ.get("MAIL_DEFAULT_SENDER_NAME")

    # String to boolean conversion using pattern matching.
    # str.capitalize() yields "True"/"False", so the arms must match that exact
    # casing — the previous all-caps arms ("TRUE"/"FALSE") never matched, the
    # values stayed non-empty strings, and both flags read as enabled
    # simultaneously (every non-empty string is truthy). The wildcard arm makes
    # any unrecognized value an explicit False instead of a truthy string.
    match mail_use_ssl:
        case "False":
            mail_use_ssl = False  # type: ignore[assignment]
        case "True":
            mail_use_ssl = True  # type: ignore[assignment]
        case _:
            mail_use_ssl = False  # type: ignore[assignment]

    match mail_use_tls:
        case "False":
            mail_use_tls = False  # type: ignore[assignment]
        case "True":
            mail_use_tls = True  # type: ignore[assignment]
        case _:
            mail_use_tls = False  # type: ignore[assignment]

    return SimpleNamespace(
        mail_configured=is_mail_configured,
        MAIL_SERVER=mail_server,
        MAIL_PORT=mail_port,
        MAIL_USERNAME=mail_username,
        MAIL_PASSWORD=mail_password,
        MAIL_USE_TLS=mail_use_tls,
        MAIL_USE_SSL=mail_use_ssl,
        MAIL_DEFAULT_SENDER=mail_default_sender,
        MAIL_DEFAULT_SENDER_NAME=mail_default_sender_name,
    )


def _load_mail_config_from_db() -> SimpleNamespace:
    """Carga la configuración de correo electrónico desde la base de datos."""
    logger.trace(_("Obteniendo configuración de correo electronico desde base de datos."))
    with current_app.app_context():
        row = database.session.execute(database.select(MailConfig)).first()
        if row is None:
            raise ValueError("No mail configuration found in database")
        mail_config = row[0]

        # If available, use the configuration from the database
        mail_server = mail_config.MAIL_SERVER
        mail_port = mail_config.MAIL_PORT
        mail_use_tls = mail_config.MAIL_USE_TLS
        mail_use_ssl = mail_config.MAIL_USE_SSL
        mail_username = mail_config.MAIL_USERNAME
        mail_password = descifrar_secreto(mail_config.MAIL_PASSWORD)
        mail_default_sender = mail_config.MAIL_DEFAULT_SENDER
        mail_default_sender_name = mail_config.MAIL_DEFAULT_SENDER_NAME
        is_mail_configured = mail_config.email_verificado

        return SimpleNamespace(
            mail_configured=is_mail_configured,
            MAIL_SERVER=mail_server,
            MAIL_PORT=mail_port,
            MAIL_USERNAME=mail_username,
            MAIL_PASSWORD=mail_password,
            MAIL_USE_TLS=mail_use_tls,
            MAIL_USE_SSL=mail_use_ssl,
            MAIL_DEFAULT_SENDER=mail_default_sender,
            MAIL_DEFAULT_SENDER_NAME=mail_default_sender_name,
        )


def _config() -> SimpleNamespace:
    """Resolve the effective mail configuration: environment first, database second."""
    config_from_env = _load_mail_config_from_env()

    if config_from_env.mail_configured:
        return config_from_env
    try:
        return _load_mail_config_from_db()
    except ValueError:
        # Neither source is configured. Return the (unconfigured) env shape rather
        # than propagating, so callers branch on `mail_configured` like every other
        # not-set-up path instead of having to catch an exception that only one of
        # the two loaders can raise.
        logger.trace("No mail configuration in environment or database.")
        return config_from_env


def resolve_sender() -> tuple[str, str | None]:
    """Return the (name, address) sender pair for an outgoing Message.

    WHY THIS EXISTS
    Mail configuration has two sources — environment (preferred) and the MailConfig
    database row — and `_config()` is the only place that knows the precedence.
    Callers that read the database row directly to obtain a sender therefore ask a
    DIFFERENT question than the one that decides whether mail works at all.

    On 2026-07-31 that divergence was live on learn.intentsolutions.io: the
    environment was fully configured and `mail_configured` reported True, while the
    MailConfig row was entirely NULL. Password-reset and confirmation mail returned
    early at the row check and sent nothing — silently, with every indicator green.

    Use this instead of `select(MailConfig)` in any code path whose job is to SEND.
    Reading the row directly is still correct in the admin settings views, which
    exist to edit that row.

    DELIBERATELY NOT A GATE. This answers "who is the sender", never "should we
    send" — `send_mail` owns that, via `config.mail_configured or no_config`.
    Every current caller passes `no_config=True`, meaning "send regardless of
    whether the config has been verified", so a `mail_configured` check in here
    would silently overrule them.

    ALWAYS RETURNS A PAIR, and the address may be None on a completely
    unconfigured deployment. That is deliberately UNCHANGED from the code this
    replaced, which built the same shape straight off the MailConfig row.

    Kilo flagged on PR #60 that flask_mail formats any tuple as
    `f"{sender[0]} <{sender[1]}>"` before validating it, so a None address
    becomes the literal envelope sender "NOW LMS <None>". That is true, and it is
    a real pre-existing wart — but returning None instead is a BEHAVIOUR CHANGE,
    not a cleanup: the resulting string is truthy, which is what currently
    satisfies flask_mail's "no sender configured" assertion. Returning None makes
    that assertion fire and turns "mail with a broken sender" into "no mail at
    all", which fails tests/test_auth_helpers.py and tests/test_public_api.py
    against real PostgreSQL. Verified by trying it.

    Fixing it properly means giving an unconfigured deployment a real fallback
    sender, which is its own change with its own tests. Tracked separately; out
    of scope for a PR about which SOURCE the sender comes from.
    """
    config = _config()
    # An SMTP account is a usable envelope sender, and MAIL_DEFAULT_SENDER is
    # optional in both sources — falling back gives a working configuration a real
    # address instead of leaning on the flask_mail fallback.
    address = config.MAIL_DEFAULT_SENDER or config.MAIL_USERNAME
    return (config.MAIL_DEFAULT_SENDER_NAME or "NOW LMS", address)


# ---------------------------------------------------------------------------------------
# Failure notification
# ---------------------------------------------------------------------------------------
# WHY THIS EXISTS
# send_mail(background=True) runs in a thread and turns every failure into a log
# line. Mail was switched on for the first time in this deployment's life on
# 2026-07-31; without this, the first signal that SMTP auth expired or the
# provider started rate-limiting would be a member saying "I never got the
# email" -- a detector that only fires for the people who bother to complain.
#
# Deliberately reuses SLACK_WEBHOOK_LEADS_CONTACT (already set on the box) rather
# than introducing a second secret: a channel that already carries "someone wants
# in" is the right place for "and we could not email them".
_ALERT_THROTTLE_SECONDS = 300
_alert_last_sent: dict[str, float] = {}
_alert_lock = threading.Lock()


_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+\.[A-Za-z]{2,})")


def _redact_addresses(text: str, known=()) -> str:
    """Strip email addresses out of free text, keeping their domains.

    The recipient list is redacted before it reaches the payload, but the
    EXCEPTION TEXT is free-form and routinely carries the address anyway --
    smtplib raises SMTPRecipientsRefused with a dict keyed by the rejected
    recipient, and providers echo the address back in the 5xx string. Sending
    that through unredacted would defeat the redaction (Greptile P1, PR #60).

    TWO PASSES, because a regex alone is not enough. Greptile's follow-up was
    right that no ASCII dotted-domain pattern covers every address form --
    quoted local parts, IP-literal domains, internationalised domains. But we do
    not have to guess: the recipients are already in hand, so they are removed by
    exact match first, whatever shape they take. The pattern is the backstop for
    addresses that were never in the recipient list (a Bcc, a relay's own
    postmaster address) and is deliberately allowed to be imperfect.
    """
    for address in known:
        address = str(address)
        if "@" in address:
            text = text.replace(address, f"<redacted>@{address.rpartition('@')[2]}")
    return _EMAIL_RE.sub(r"<redacted>@\1", text)


def _redact_recipients(recipients) -> str:
    """Domains only. An alert says which mail is failing, not who the members are.

    Matches the disclosure posture of the /request-access Slack ping, which
    deliberately never sends an applicant's address off-platform. The domain is
    what distinguishes "our relay is broken" from "one member's provider is
    bouncing us", which is the question an alert has to answer.
    """
    domains = sorted({str(r).rpartition("@")[2].lower() for r in (recipients or []) if "@" in str(r)})
    if not domains:
        return f"{len(recipients or [])} recipient(s)"
    return ", ".join(domains[:3]) + (" (+more)" if len(domains) > 3 else "")


def _should_alert(key: str) -> bool:
    """Throttle per failure kind, so an SMTP outage cannot flood the channel.

    Without this, a provider rate-limit turns every queued send into a Slack POST
    and the alert channel becomes the second outage.

    PER PROCESS, deliberately. Under gunicorn with N workers an outage yields up
    to N alerts per window rather than one. That is accepted: N is small, the
    failure is worth over-reporting rather than under-reporting, and a shared
    backend would make the alert path depend on Redis being up -- precisely the
    kind of infrastructure whose absence it needs to survive.
    """
    now = monotonic()
    with _alert_lock:
        last = _alert_last_sent.get(key)
        if last is not None and (now - last) < _ALERT_THROTTLE_SECONDS:
            return False
        _alert_last_sent[key] = now
        return True


def notify_mail_failure(msg: Message, error: BaseException) -> None:
    """Best-effort alert that a message could not be delivered. Never raises.

    Called from the background sender's except arm, which runs OUTSIDE the Flask
    application context -- so this must not touch current_app, url_for, or the
    database.
    """
    error_kind = type(error).__name__
    try:
        webhook = environ.get("SLACK_WEBHOOK_LEADS_CONTACT")
        if not webhook:
            logger.warning("Mail delivery failed and SLACK_WEBHOOK_LEADS_CONTACT is unset; alert not sent.")
            return
        # Scheme allow-list before urlopen, mirroring request_access._notify_slack:
        # the nosec below suppresses exactly the check that would otherwise catch a
        # misconfigured file:// or ftp:// value.
        if not webhook.lower().startswith("https://"):
            logger.warning("SLACK_WEBHOOK_LEADS_CONTACT is not an https URL; mail-failure alert not sent.")
            return
        if not _should_alert(error_kind):
            logger.debug(f"Mail-failure alert for {error_kind} throttled.")
            return

        payload = {
            "text": f"Mail delivery failed: {error_kind}",
            "unfurl_links": False,
            "unfurl_media": False,
            "blocks": [
                {"type": "header", "text": {"type": "plain_text", "text": "Mail delivery failed", "emoji": False}},
                {
                    "type": "section",
                    "fields": [
                        {"type": "plain_text", "text": f"Subject: {str(msg.subject)[:150]}", "emoji": False},
                        {"type": "plain_text", "text": f"To: {_redact_recipients(msg.recipients)}", "emoji": False},
                    ],
                },
                {
                    "type": "section",
                    "text": {
                        "type": "plain_text",
                        "text": f"{error_kind}: {_redact_addresses(str(error), msg.recipients or [])[:400]}",
                        "emoji": False,
                    },
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "plain_text",
                            "text": f"Further {error_kind} alerts muted for {_ALERT_THROTTLE_SECONDS}s.",
                            "emoji": False,
                        }
                    ],
                },
            ],
        }
        request = urllib.request.Request(
            webhook,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=5):  # nosec B310 - env-provided https webhook
            pass
    except Exception as alert_error:  # pylint: disable=broad-exception-caught
        # An alert that raises would replace a delivery failure with a thread
        # crash, losing the log line that is currently the only record.
        logger.warning(f"Could not send the mail-failure alert for {error_kind}: {alert_error}")


def send_threaded_email(app: Flask, mail: Mail, msg: Message, _log: str = "", _flush: str = ""):
    """
    Función interna que se ejecuta en un hilo para enviar el email.

    :param app: Instancia de Flask.
    :param mail: Instancia de Flask-Mail.
    :param msg: Instancia de flask_mail.Message.
    """
    logger.trace(f"Enviando correo a {msg.recipients} en segundo plano.")
    try:
        with app.app_context():
            logger.trace(_("Intentando enviar correo electrónico en segundo plano."))
            mail.send(msg)
            logger.trace(_("Correo enviado a {recipients}.").format(recipients=msg.recipients))
            if _log != "":
                logger.info(_log)
            if _flush != "":
                flash(_flush)
    except Exception as e:
        logger.error(
            _("Error al enviar correo a %(recipients)s: %(error)s")
            % {
                "recipients": msg.recipients,
                "error": e,
            }
        )
        # A log line inside a background thread is not a signal anyone receives.
        notify_mail_failure(msg, e)


def send_mail(msg: Message, background: bool = True, no_config: bool = False, _log: str = "", _flush: str = ""):
    """
    Envía un mensaje de correo electrónico de forma asincrónica usando hilos.

    :param mail: Instancia de Flask.
    :param msg: Instancia de flask_mail.Message.
    :param background: Si es True, envía el correo en segundo plano.
    """
    _app = current_app
    config = _config()

    for key, value in vars(config).items():
        if key.startswith("MAIL_"):
            _app.config[key] = value

    if LOG_LEVEL < 20:
        _app.config["MAIL_DEBUG"] = True

    if DESARROLLO:
        _app.config["MAIL_SUPPRESS_SEND"] = True

    logger.trace(_("Configuración de correo electrónico cargada en la aplicación Flask."))

    logger.trace(_("Creando instancia de Flask-Mail."))
    _mail = Mail(_app)

    if config.mail_configured or no_config:
        logger.trace(_("Configuración de correo electrónico verificada."))
        if background:
            logger.trace(_("Enviando correo en segundo plano."))
            try:
                hilo = threading.Thread(target=send_threaded_email, args=(_app, _mail, msg, _log, _flush))
                hilo.start()
                logger.trace(_("Hilo iniciado para enviar email a: {recipients}").format(recipients=msg.recipients))
            except Exception as e:
                logger.error(_("No se pudo iniciar el hilo de envío de correo: {error}").format(error=e))
        else:
            logger.trace(_("Enviando correo de forma síncrona."))
            with _app.app_context():
                _mail.send(msg)
                logger.trace(_("Correo enviado a {recipients}.").format(recipients=msg.recipients))
