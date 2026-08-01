# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""Learner-reported prior credentials (recognition of prior learning).

A learner records the courses they completed *elsewhere* before, or alongside, the
courses hosted here: which credential, its ID, when it was issued, the issuer's
verification link, and optionally an image of the certificate.

Two deliberate design choices, both worth keeping if this is ever upstreamed:

* **The verification URL is required; the image is not.** A link back to the issuer
  can be checked by whoever reviews it. An uploaded image only shows what the
  learner chose to upload, so it is a convenience attachment, never the proof.
* **Uploads never touch an UploadSet.** ``UPLOADS_AUTOSERVE`` is on and
  flask-reuploaded publishes every UploadSet file at ``/_uploads/<set>/<filename>``
  with no authorization at all. A certificate image carries a real person's name
  and credential number, so the bytes land in the private files directory and are
  served only through :func:`credential_image`, which checks the requester.

``status`` is review bookkeeping for staff. Nothing in the application gates on it:
enrollment, course access and evaluations are all unaffected by what a learner does
or does not record here.

The credential catalog below is deployment-specific data living in shared source.
That is the one thing blocking an upstream contribution — upstream would need it
admin-configurable (a table, or config) rather than a module constant.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------
from os import makedirs, path, remove
from urllib.parse import urlparse

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------
from flask import Blueprint, abort, flash, redirect, render_template, request, send_from_directory, url_for
from flask_login import current_user, login_required
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from werkzeug.utils import secure_filename
from werkzeug.wrappers import Response
from wtforms import DateField, SelectField, StringField
from wtforms.validators import DataRequired, Length, Optional as OptionalValidator

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms.auth import perfil_requerido
from now_lms.config import DIRECTORIO_ARCHIVOS_PRIVADOS, DIRECTORIO_PLANTILLAS
from now_lms.db import PriorCredential, Usuario, database, utc_now
from now_lms.i18n import _, _l
from now_lms.logs import log

prior_credentials = Blueprint("prior_credentials", __name__, template_folder=DIRECTORIO_PLANTILLAS)

LEARNER_TEMPLATE = "themes/intent_learn/pages/my_credentials.html"
ADMIN_TEMPLATE = "themes/intent_learn/pages/admin_credentials.html"

# The credentials a learner can record, in the order they are usually taken.
# Keys are stable slugs stored on the row; names are denormalized at submission
# time so renaming or retiring an entry here cannot rewrite an existing record.
CREDENTIAL_CATALOG: tuple[tuple[str, str], ...] = (
    ("claude-platform-101", "Claude Platform 101"),
    ("claude-code-101", "Claude Code 101"),
    ("claude-code-in-action", "Claude Code in Action"),
    ("building-with-claude-api", "Building with the Claude API"),
    ("intro-mcp", "Introduction to MCP"),
    ("mcp-advanced-topics", "MCP Advanced Topics"),
    ("intro-agent-skills", "Introduction to Agent Skills"),
    ("intro-subagents", "Introduction to Subagents"),
)
CREDENTIAL_NAMES: dict[str, str] = dict(CREDENTIAL_CATALOG)
CREDENTIAL_TOTAL = len(CREDENTIAL_CATALOG)

# Where credential images live. Deliberately under the PRIVATE tree: the public
# upload directories are autoserved without authorization.
CREDENTIALS_DIR = path.join(DIRECTORIO_ARCHIVOS_PRIVADOS, "credenciales")

ALLOWED_EXTENSIONS = ("png", "jpg", "jpeg", "webp", "pdf")
# Flask sets no MAX_CONTENT_LENGTH in this deployment, so the cap is enforced here.
MAX_UPLOAD_BYTES = 5 * 1024 * 1024

CREDENTIAL_ID_MAX = 100
VERIFICATION_URL_MAX = 500
ADMIN_NOTES_MAX = 2000
VALID_STATUSES = ("submitted", "verified", "rejected")

MY_CREDENTIALS_ROUTE = "prior_credentials.my_credentials"


class PriorCredentialForm(FlaskForm):
    """One credential earned elsewhere."""

    credential_key = SelectField(
        _l("Which course?"),
        choices=list(CREDENTIAL_CATALOG),
        validators=[DataRequired()],
    )
    credential_id = StringField(_l("Certificate ID"), validators=[OptionalValidator(), Length(max=CREDENTIAL_ID_MAX)])
    verification_url = StringField(
        _l("Verification link"),
        validators=[DataRequired(), Length(max=VERIFICATION_URL_MAX)],
    )
    issued_on = DateField(_l("Date completed"), validators=[OptionalValidator()])
    image = FileField(
        _l("Certificate image or PDF (optional)"),
        validators=[FileAllowed(ALLOWED_EXTENSIONS, _l("Images and PDFs only."))],
    )


class CredentialActionForm(FlaskForm):
    """Empty form whose only job is to carry a CSRF token on a destructive POST.

    This application does not install ``CSRFProtect``, so ``csrf_token()`` is not a
    template global and a hand-rolled POST form is unprotected. Every mutating route
    here therefore goes through a FlaskForm and ``validate_on_submit()``.
    """


class CredentialReviewForm(FlaskForm):
    """A staff review decision.

    ``status`` is submitted by the button the reviewer presses (each carries
    ``name="status"``), so the SelectField both receives and validates it.
    """

    status = SelectField(_l("Decision"), choices=[(value, value) for value in VALID_STATUSES], validators=[DataRequired()])
    admin_notes = StringField(_l("Notes"), validators=[OptionalValidator(), Length(max=ADMIN_NOTES_MAX)])


def _valid_verification_url(raw: str) -> bool:
    """True when the link is a plausible https URL with a hostname.

    Deliberately not an allow-list of issuer domains: a learner may hold a
    credential from somewhere nobody anticipated, and a reviewer opens the link
    anyway. The scheme check is what matters — it keeps ``javascript:`` and
    ``file:`` out of a field that is rendered as an anchor.
    """
    try:
        parsed = urlparse(raw)
    except ValueError:
        return False
    return parsed.scheme == "https" and bool(parsed.netloc)


def _upload_too_large(storage) -> bool:
    """True when the uploaded file exceeds the cap. Leaves the stream rewound."""
    storage.stream.seek(0, 2)
    size = storage.stream.tell()
    storage.stream.seek(0)
    return size > MAX_UPLOAD_BYTES


def _extension_of(filename: str) -> str | None:
    """Return the lowercase extension when it is one we accept, else None."""
    safe = secure_filename(filename or "")
    if "." not in safe:
        return None
    ext = safe.rsplit(".", 1)[1].lower()
    return ext if ext in ALLOWED_EXTENSIONS else None


def _store_image(storage, record_id: str) -> str | None:
    """Persist the upload under a name we control. Returns the stored file name.

    The name is derived from the record id, never from the client-supplied
    filename, so no user input reaches the filesystem path.
    """
    ext = _extension_of(storage.filename)
    if ext is None:
        return None
    makedirs(CREDENTIALS_DIR, exist_ok=True)
    stored_name = f"{record_id}.{ext}"
    storage.save(path.join(CREDENTIALS_DIR, stored_name))
    return stored_name


def _delete_image(file_name: str | None) -> None:
    """Remove a stored image, tolerating one that is already gone."""
    if not file_name:
        return
    try:
        remove(path.join(CREDENTIALS_DIR, file_name))
    except OSError as error:
        log.warning(f"Could not remove credential image {file_name}: {error}")


def _credentials_for(username: str) -> list[PriorCredential]:
    """Every credential a learner has recorded, catalog order."""
    rows = (
        database.session.execute(database.select(PriorCredential).filter_by(usuario=username)).scalars().all()
    )
    order = {key: index for index, (key, _name) in enumerate(CREDENTIAL_CATALOG)}
    return sorted(rows, key=lambda row: order.get(row.credential_key, CREDENTIAL_TOTAL))


def _render_learner_page(form: PriorCredentialForm) -> str:
    """Render the learner's page with its current state."""
    return render_template(
        LEARNER_TEMPLATE,
        form=form,
        delete_form=CredentialActionForm(),
        credentials=_credentials_for(current_user.usuario),
        catalog_total=CREDENTIAL_TOTAL,
    )


@prior_credentials.route("/my-credentials", methods=["GET", "POST"])
@login_required
def my_credentials() -> str | Response:
    """A learner's own record of prior learning."""
    form = PriorCredentialForm()

    if form.validate_on_submit():
        verification_url = (form.verification_url.data or "").strip()
        if not _valid_verification_url(verification_url):
            flash(_("The verification link must be an https address."), "warning")
            return _render_learner_page(form)

        key = form.credential_key.data
        if key not in CREDENTIAL_NAMES:
            abort(400)

        existing = database.session.execute(
            database.select(PriorCredential).filter_by(usuario=current_user.usuario, credential_key=key)
        ).scalar_one_or_none()
        if existing is not None:
            flash(_("You have already recorded that course. Remove the existing entry to replace it."), "warning")
            return redirect(url_for(MY_CREDENTIALS_ROUTE))

        upload = request.files.get("image")
        if upload and upload.filename:
            if _upload_too_large(upload):
                flash(_("That file is larger than 5 MB. Please upload a smaller image or PDF."), "warning")
                return _render_learner_page(form)
            if _extension_of(upload.filename) is None:
                flash(_("That file type is not accepted. Upload a PNG, JPG, WEBP or PDF."), "warning")
                return _render_learner_page(form)

        record = PriorCredential(
            usuario=current_user.usuario,
            credential_key=key,
            credential_name=CREDENTIAL_NAMES[key],
            credential_id=(form.credential_id.data or "").strip()[:CREDENTIAL_ID_MAX] or None,
            verification_url=verification_url[:VERIFICATION_URL_MAX],
            issued_on=form.issued_on.data,
            status="submitted",
        )
        database.session.add(record)
        # Flush so the generated id exists before it names the stored file.
        database.session.flush()
        if upload and upload.filename:
            record.image_file = _store_image(upload, record.id)
        database.session.commit()
        flash(_("Credential recorded."), "success")
        return redirect(url_for(MY_CREDENTIALS_ROUTE))

    return _render_learner_page(form)


@prior_credentials.route("/my-credentials/<record_id>/delete", methods=["POST"])
@login_required
def delete_credential(record_id: str) -> Response:
    """Remove one of the current learner's own records."""
    if not CredentialActionForm().validate_on_submit():
        abort(400)

    record = database.session.get(PriorCredential, record_id)
    # 404 rather than 403 on someone else's row: a different status code would
    # confirm the record exists.
    if record is None or record.usuario != current_user.usuario:
        abort(404)

    _delete_image(record.image_file)
    database.session.delete(record)
    database.session.commit()
    flash(_("Credential removed."), "success")
    return redirect(url_for(MY_CREDENTIALS_ROUTE))


@prior_credentials.route("/my-credentials/<record_id>/image", methods=["GET"])
@login_required
def credential_image(record_id: str) -> Response:
    """Serve a credential image to its owner or to staff, and to nobody else.

    This route exists because the upload directories flask-reuploaded autoserves
    have no authorization. Certificate images carry a person's name and credential
    number, so they are private files served under a check.
    """
    record = database.session.get(PriorCredential, record_id)
    if record is None or not record.image_file:
        abort(404)

    is_owner = record.usuario == current_user.usuario
    is_staff = current_user.tipo in ("admin", "instructor")
    if not (is_owner or is_staff):
        abort(403)

    return send_from_directory(CREDENTIALS_DIR, record.image_file)


@prior_credentials.route("/admin/prior-credentials", methods=["GET"])
@login_required
@perfil_requerido(("admin", "instructor"))
def admin_list() -> str:
    """Every recorded credential, grouped by learner, with a completeness count."""
    status_filter = request.args.get("status", "")
    query = database.select(PriorCredential)
    if status_filter in VALID_STATUSES:
        query = query.filter_by(status=status_filter)

    rows = database.session.execute(query).scalars().all()

    learners: dict[str, dict] = {}
    for row in rows:
        entry = learners.setdefault(row.usuario, {"username": row.usuario, "rows": [], "display": row.usuario})
        entry["rows"].append(row)

    # One query for the display names rather than one per learner.
    if learners:
        users = (
            database.session.execute(database.select(Usuario).filter(Usuario.usuario.in_(list(learners.keys()))))
            .scalars()
            .all()
        )
        for user in users:
            full_name = " ".join(part for part in (user.nombre, user.apellido) if part).strip()
            if full_name:
                learners[user.usuario]["display"] = full_name

    order = {key: index for index, (key, _name) in enumerate(CREDENTIAL_CATALOG)}
    for entry in learners.values():
        entry["rows"].sort(key=lambda row: order.get(row.credential_key, CREDENTIAL_TOTAL))
        entry["verified_count"] = sum(1 for row in entry["rows"] if row.status == "verified")

    return render_template(
        ADMIN_TEMPLATE,
        learners=sorted(learners.values(), key=lambda entry: entry["display"].lower()),
        review_form=CredentialReviewForm(),
        catalog_total=CREDENTIAL_TOTAL,
        status_filter=status_filter,
        statuses=VALID_STATUSES,
    )


@prior_credentials.route("/admin/prior-credentials/<record_id>/review", methods=["POST"])
@login_required
@perfil_requerido(("admin", "instructor"))
def review_credential(record_id: str) -> Response:
    """Record a staff review decision. Bookkeeping only — nothing gates on it."""
    form = CredentialReviewForm()
    if not form.validate_on_submit():
        abort(400)

    record = database.session.get(PriorCredential, record_id)
    if record is None:
        abort(404)

    record.status = form.status.data
    record.admin_notes = (form.admin_notes.data or "").strip()[:ADMIN_NOTES_MAX] or None
    record.reviewed_by = current_user.usuario
    record.reviewed_at = utc_now()
    database.session.commit()
    flash(_("Review saved."), "success")
    return redirect(url_for("prior_credentials.admin_list", status=request.args.get("status", "")))
