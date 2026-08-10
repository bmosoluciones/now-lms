# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.

"""Community Hub — ADR-10 (000-docs/017-AT-ADEC), which supersedes ADR-8.

A private feed where cohort members publish Questions, Builds and Success
Stories, reply to each other, and like a post once.

The Hub owns its own content: ``ComunidadPublicacion`` holds the body, the
author and the reply relationship, so there is no dependency on the native
forum and no container course. ADR-8 stored bodies in ``ForoMensaje`` behind a
metadata sidecar; that needed a fake course row to satisfy a NOT NULL column,
and since ``ForoMensaje.curso_id`` cascades, deleting that one row would have
silently deleted every post in the Hub. The table count was identical either
way, so the container bought nothing.

Membership: every active, verified Intent Solutions member is in the Hub. There
is no per-member provisioning, and because there is exactly one Hub with
everyone in it, cross-cohort disclosure is prevented structurally rather than by
filtering. Moderation state is applied at the query level, never hidden in a
template.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------
import threading
from collections import deque
from datetime import timedelta
from time import time
from urllib.parse import urlparse

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------
from bleach import clean
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from flask_wtf import FlaskForm
from markdown import markdown
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from werkzeug.wrappers import Response
from wtforms import HiddenField, SelectField, StringField, TextAreaField
from wtforms.validators import DataRequired, Length
from wtforms.validators import Optional as OptionalValidator

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms.auth import email_verificado_requerido
from now_lms.calendar_utils import get_upcoming_events_for_user
from now_lms.config import DIRECTORIO_PLANTILLAS
from now_lms.db import (
    COMUNIDAD_TIPOS,
    Announcement,
    ComunidadEventoModeracion,
    ComunidadPublicacion,
    ComunidadReaccion,
    Usuario,
    database,
    select,
    utc_now,
)
from now_lms.i18n import _, _l

comunidad = Blueprint("comunidad", __name__, template_folder=DIRECTORIO_PLANTILLAS)

FEED_TEMPLATE = "themes/intent_learn/pages/comunidad_feed.html"
POST_TEMPLATE = "themes/intent_learn/pages/comunidad_post.html"
STAFF_TEMPLATE = "themes/intent_learn/pages/comunidad_staff.html"
NUEVO_TEMPLATE = "themes/intent_learn/pages/comunidad_nuevo.html"

TITULO_MAX = 160
CUERPO_MAX = 8000
MOTIVO_MAX = 500
POR_PAGINA = 20

TIPO_ETIQUETAS = {
    "question": _l("Question"),
    "build": _l("Build"),
    "success_story": _l("Success Story"),
}

ROLES_STAFF = ("admin", "instructor", "moderator")

# ---------------------------------------------------------------------------------------
# Trending contract (ADR-8 §9 of the plan). Constants live together so they are tunable
# in one place without a migration — the ranking is computed live, never stored.
# ---------------------------------------------------------------------------------------
VENTANA_ELEGIBILIDAD_DIAS = 30  # a post older than this cannot trend, however active
VENTANA_ENGAGEMENT_DIAS = 7  # only likes and replies inside this window count
PESO_RESPUESTA = 3  # a reply costs more than a like and is the durable artifact
PESO_LIKE = 2
MINIMO_MIEMBROS = 3  # fewer distinct engaged members and the post does not qualify
MINIMO_PARA_RANKEAR = 5  # fewer qualifying posts and Trending refuses to exist
GRAVEDAD = 1.5
DESPLAZAMIENTO_HORAS = 2

# ---------------------------------------------------------------------------------------
# Sanitiser. Deliberately NOT forum.py's: that allow-list permits <img src> with no scheme
# or host restriction, which makes any member post a tracking pixel that leaks every
# reader's IP, and it strips `rel`, so links cannot be hardened at render time.
# Media hosting is an explicit non-goal for V1, so images have no legitimate use here.
# ---------------------------------------------------------------------------------------
TAGS_PERMITIDOS = [
    "p", "br", "strong", "em", "u", "ol", "ul", "li",
    "h3", "h4", "h5", "h6", "blockquote", "code", "pre", "a",
]
ATRIBUTOS_PERMITIDOS = {"a": ["href", "title", "rel", "target"]}
PROTOCOLOS_PERMITIDOS = ["http", "https", "mailto"]


def _destino_local(respaldo: str) -> str:
    """Return the referrer only when it points back into this site, else ``respaldo``.

    These endpoints send the member back where they came from after a like, an
    unlike or a report. ``request.referrer`` is the ``Referer`` header, which the
    caller controls: a page on another origin can POST here and have this app issue
    the redirect off-site, which is an open redirect and lends this domain's
    credibility to whatever it points at. Flagged by CodeQL on PR #82.

    Accepted: a same-host absolute URL, or a root-relative path. Everything else
    falls back. Protocol-relative (``//evil.example``) and backslash (``/\\evil``)
    forms are rejected explicitly, because some browsers normalise the backslash to
    a slash and would treat the result as a host rather than a path.
    """
    referrer = request.referrer
    if not referrer:
        return respaldo

    partes = urlparse(referrer)
    if partes.netloc and partes.netloc != request.host:
        return respaldo
    if partes.scheme and partes.scheme not in ("http", "https"):
        return respaldo

    ruta = partes.path or "/"
    if not ruta.startswith("/") or ruta.startswith("//") or ruta.startswith("/\\"):
        return respaldo

    return f"{ruta}?{partes.query}" if partes.query else ruta


def markdown_seguro(texto: str) -> str:
    """Markdown to sanitised HTML, with every anchor hardened."""
    html = markdown(texto or "", extensions=["nl2br", "codehilite"])
    limpio = clean(html, tags=TAGS_PERMITIDOS, attributes=ATRIBUTOS_PERMITIDOS, protocols=PROTOCOLOS_PERMITIDOS)
    return limpio.replace("<a ", '<a rel="noopener noreferrer nofollow" target="_blank" ')


def enlace_valido(bruto: str | None) -> bool:
    """True when the build link is a plausible http(s) URL with a hostname."""
    if not bruto:
        return True
    try:
        partes = urlparse(bruto)
    except ValueError:
        return False
    return partes.scheme in ("http", "https") and bool(partes.netloc)


# How much of a post body the feed shows before "See more". Long enough that most
# short posts render whole, short enough that one post cannot own the screen.
EXTRACTO_MAX = 320


def texto_plano(markdown_bruto: str) -> str:
    """Body as plain text, for the feed excerpt.

    Renders and sanitises first, then strips every tag, so the excerpt cannot
    carry markup into the card and cannot be used to break the layout.
    """
    html = markdown_seguro(markdown_bruto or "")
    return " ".join(clean(html, tags=[], attributes={}, strip=True).split())


def extracto(markdown_bruto: str) -> tuple[str, bool]:
    """Return (excerpt, truncated). Cuts on a word boundary, never mid-word."""
    plano = texto_plano(markdown_bruto)
    if len(plano) <= EXTRACTO_MAX:
        return plano, False
    corte = plano[:EXTRACTO_MAX].rsplit(" ", 1)[0]
    return corte, True


def hace(momento) -> str:
    """Compact relative age: 3h, 2d, 5w. Falls back to a date past a year."""
    if not momento:
        return ""
    segundos = (utc_now().replace(tzinfo=None) - momento).total_seconds()
    if segundos < 60:
        return _("just now")
    for umbral, divisor, sufijo in ((3600, 60, "m"), (86400, 3600, "h"), (604800, 86400, "d"), (31536000, 604800, "w")):
        if segundos < umbral:
            return f"{int(segundos // divisor)}{sufijo}"
    return momento.strftime("%b %Y")


def iniciales(autor) -> str:
    """Two letters for the avatar circle, falling back to the username."""
    partes = [p for p in (autor.nombre, autor.apellido) if p]
    if partes:
        return "".join(p[0] for p in partes[:2]).upper()
    return (autor.usuario or "?")[:2].upper()


# ---------------------------------------------------------------------------------------
# Rate limiting. In-process sliding window keyed on the member, following
# vistas/request_access.py. The repo's `check_rate_limit` helper is deliberately NOT used:
# it is a silent no-op under NullCache, which is the production fallback.
# ---------------------------------------------------------------------------------------
_LIMITES = {"post": (10, 3600), "reply": (30, 3600), "report": (10, 3600), "like": (200, 3600)}
_LOCK = threading.Lock()
_CUBOS: dict[str, deque] = {}
_MAX_CUBOS = 10_000


def _limitado(accion: str, usuario: str) -> bool:
    """True when this member is over the limit for this action."""
    maximo, ventana = _LIMITES[accion]
    ahora = time()
    clave = f"{accion}:{usuario}"
    with _LOCK:
        cubo = _CUBOS.setdefault(clave, deque())
        while cubo and ahora - cubo[0] > ventana:
            cubo.popleft()
        if len(cubo) >= maximo:
            return True
        cubo.append(ahora)
        if len(_CUBOS) > _MAX_CUBOS:
            for clave_vieja in sorted(_CUBOS, key=lambda k: _CUBOS[k][-1] if _CUBOS[k] else 0)[:1000]:
                _CUBOS.pop(clave_vieja, None)
        return False


# ---------------------------------------------------------------------------------------
# Forms. Every mutating route goes through a FlaskForm and validate_on_submit(): this
# application does not install CSRFProtect, so csrf_token() is not a template global and a
# hand-rolled POST form would carry no CSRF protection at all.
# ---------------------------------------------------------------------------------------
class PublicacionForm(FlaskForm):
    """A new Hub post."""

    titulo = StringField(_l("Title"), validators=[DataRequired(), Length(max=TITULO_MAX)])
    tipo = SelectField(_l("Type"), choices=[(t, TIPO_ETIQUETAS[t]) for t in COMUNIDAD_TIPOS], validators=[DataRequired()])
    contenido = TextAreaField(_l("Your post"), validators=[DataRequired(), Length(max=CUERPO_MAX)])
    enlace_build = StringField(_l("Link (optional)"), validators=[OptionalValidator(), Length(max=500)])


class RespuestaForm(FlaskForm):
    """A reply to a Hub post."""

    contenido = TextAreaField(_l("Reply"), validators=[DataRequired(), Length(max=CUERPO_MAX)])


class AccionForm(FlaskForm):
    """Empty form whose only job is to carry a CSRF token on a state-changing POST."""


class ReporteForm(FlaskForm):
    """A member report. A reason is required or the report is not actionable."""

    motivo = StringField(_l("What is wrong with this post?"), validators=[DataRequired(), Length(max=MOTIVO_MAX)])


class ModeracionForm(FlaskForm):
    """A staff hide, which owes the author a reason."""

    motivo = StringField(_l("Reason"), validators=[DataRequired(), Length(max=MOTIVO_MAX)])
    destino = HiddenField()


# ---------------------------------------------------------------------------------------
# Authorization
# ---------------------------------------------------------------------------------------
def es_miembro() -> bool:
    """Every active member with a real role is in the Hub.

    Deliberately checks ``activo`` and the role itself rather than relying on the
    fact that self-registration is closed: that gate lives in host ingress config
    outside this repository, and regenerating it silently reopens signup.
    """
    return bool(
        current_user.is_authenticated
        and current_user.activo
        and current_user.tipo in (*ROLES_STAFF, "student")
    )


def es_staff() -> bool:
    """Moderators, instructors and admins."""
    return bool(current_user.is_authenticated and current_user.tipo in ROLES_STAFF)


def _exigir_miembro() -> None:
    if not es_miembro():
        abort(404)


def _exigir_staff() -> None:
    if not es_staff():
        abort(403)


# ---------------------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------------------
def _publicaciones_base():
    """Visible root posts with their author. Moderation is applied here, never in a template."""
    return (
        select(ComunidadPublicacion, Usuario)
        .join(Usuario, Usuario.usuario == ComunidadPublicacion.usuario)
        .filter(
            ComunidadPublicacion.parent_id.is_(None),
            ComunidadPublicacion.estado_moderacion == "visible",
        )
    )


def _agregados(ids: list[str], usuario: str) -> tuple[dict, dict, set]:
    """Like counts, reply counts and this member's likes — three queries, flat in post count."""
    if not ids:
        return {}, {}, set()

    likes = dict(
        database.session.execute(
            select(ComunidadReaccion.publicacion_id, func.count(ComunidadReaccion.id))
            .filter(ComunidadReaccion.publicacion_id.in_(ids))
            .group_by(ComunidadReaccion.publicacion_id)
        ).all()
    )
    respuestas = dict(
        database.session.execute(
            select(ComunidadPublicacion.parent_id, func.count(ComunidadPublicacion.id))
            .filter(ComunidadPublicacion.parent_id.in_(ids))
            .group_by(ComunidadPublicacion.parent_id)
        ).all()
    )
    mios = set(
        database.session.execute(
            select(ComunidadReaccion.publicacion_id).filter(
                ComunidadReaccion.publicacion_id.in_(ids), ComunidadReaccion.usuario == usuario
            )
        )
        .scalars()
        .all()
    )
    return likes, respuestas, mios


def _decorar(filas, usuario: str) -> list[dict]:
    """Attach counts to a page of posts without a query per row."""
    ids = [pub.id for pub, _ in filas]
    likes, respuestas, mios = _agregados(ids, usuario)
    decorados = []
    for pub, autor in filas:
        cuerpo, cortado = extracto(pub.contenido)
        decorados.append(
            {
                "pub": pub,
                "autor": autor,
                "likes": likes.get(pub.id, 0),
                "respuestas": respuestas.get(pub.id, 0),
                "me_gusta": pub.id in mios,
                "es_propio": pub.usuario == usuario,
                "etiqueta": TIPO_ETIQUETAS.get(pub.tipo, pub.tipo),
                "extracto": cuerpo,
                "cortado": cortado,
                "hace": hace(pub.fecha_creacion),
                "iniciales": iniciales(autor),
                "nombre": " ".join(p for p in (autor.nombre, autor.apellido) if p) or autor.usuario,
            }
        )
    return decorados


def calcular_trending(usuario: str) -> tuple[list[dict], bool]:
    """Rank visible root posts. Returns (posts, ranked).

    ``ranked`` is False when too few posts qualify, in which case the caller shows
    Latest with an honest banner rather than crowning a post with three likes.

    Each engaged member counts exactly once: a reply counts 3, a like counts 2,
    and doing both counts 3. That collapses double-dipping by construction and is
    what makes reply spam worth nothing — forty replies from one member is still
    one member.
    """
    ahora = utc_now().replace(tzinfo=None)
    corte_post = ahora - timedelta(days=VENTANA_ELEGIBILIDAD_DIAS)
    corte_engagement = ahora - timedelta(days=VENTANA_ENGAGEMENT_DIAS)

    filas = database.session.execute(
        _publicaciones_base().filter(
            ComunidadPublicacion.fijado.is_(False),
            ComunidadPublicacion.fecha_creacion >= corte_post,
            Usuario.activo.is_(True),
        )
    ).all()
    if not filas:
        return [], False

    ids = [pub.id for pub, _ in filas]
    autores = {pub.id: pub.usuario for pub, _ in filas}

    # Distinct likers in the window, excluding the author and inactive accounts.
    likers: dict[str, set] = {i: set() for i in ids}
    for publicacion_id, quien in database.session.execute(
        select(ComunidadReaccion.publicacion_id, ComunidadReaccion.usuario)
        .join(Usuario, Usuario.usuario == ComunidadReaccion.usuario)
        .filter(
            ComunidadReaccion.publicacion_id.in_(ids),
            ComunidadReaccion.timestamp >= corte_engagement,
            Usuario.activo.is_(True),
        )
    ).all():
        if quien != autores.get(publicacion_id):
            likers[publicacion_id].add(quien)

    # Distinct non-author repliers in the window.
    repliers: dict[str, set] = {i: set() for i in ids}
    respuesta = database.aliased(ComunidadPublicacion)
    for parent_id, quien in database.session.execute(
        select(respuesta.parent_id, respuesta.usuario)
        .join(Usuario, Usuario.usuario == respuesta.usuario)
        .filter(
            respuesta.parent_id.in_(ids),
            respuesta.fecha_creacion >= corte_engagement,
            Usuario.activo.is_(True),
        )
    ).all():
        if quien != autores.get(parent_id):
            repliers[parent_id].add(quien)

    puntuados = []
    for pub, _autor in filas:
        r, lk = repliers[pub.id], likers[pub.id]
        comprometidos = r | lk
        if len(comprometidos) < MINIMO_MIEMBROS:
            continue
        # Per-member weight, counted once. Replying outranks liking; doing both is not additive.
        bruto = sum(PESO_RESPUESTA if m in r else PESO_LIKE for m in comprometidos)
        horas = max(0.0, (ahora - pub.fecha_creacion).total_seconds() / 3600.0)
        puntaje = bruto / ((horas + DESPLAZAMIENTO_HORAS) ** GRAVEDAD)
        puntuados.append(((puntaje, len(comprometidos), pub.fecha_creacion, pub.id), (pub, _autor)))

    if len(puntuados) < MINIMO_PARA_RANKEAR:
        return [], False

    # Total order, so pagination is stable and nothing is ever random.
    puntuados.sort(key=lambda par: par[0], reverse=True)
    return _decorar([fila for _, fila in puntuados], usuario), True


def _anclados(usuario: str) -> list[dict]:
    filas = database.session.execute(
        _publicaciones_base().filter(ComunidadPublicacion.fijado.is_(True)).order_by(ComunidadPublicacion.fecha_creacion.desc())
    ).all()
    return _decorar(filas, usuario)


def anuncios_activos(limite: int = 3) -> list:
    """Active sticky global announcements, for the top of the feed.

    Read from the NATIVE ``Announcement`` model, not a Hub post type. Staff
    already have working admin CRUD there with stickiness and expiry, and a
    second announcement concept would be two channels for one message — which is
    the whole reason ``/dashboard/announcements`` redirects rather than rendering
    a second reader.

    Naive UTC, matching ``Announcement.is_active()`` and how ``expires_at`` is
    stored. The native view compared against ``datetime.now()``, which is local
    time, so on a non-UTC host it retired announcements early or late.
    """
    ahora = utc_now().replace(tzinfo=None)
    return list(
        database.session.execute(
            select(Announcement)
            .filter(
                Announcement.course_id.is_(None),
                database.or_(Announcement.expires_at.is_(None), Announcement.expires_at >= ahora),
            )
            .order_by(Announcement.is_sticky.desc(), Announcement.timestamp.desc())
            .limit(limite)
        )
        .scalars()
        .all()
    )


def posts_recientes(usuario: str, limite: int = 5) -> list[dict]:
    """The newest visible Hub posts, for the member dashboard.

    Lives here rather than in the dashboard so the Hub owns its own scoping and
    the dashboard never writes a query against Hub tables.
    """
    filas = database.session.execute(
        _publicaciones_base()
        .filter(ComunidadPublicacion.fijado.is_(False))
        .order_by(ComunidadPublicacion.fecha_creacion.desc())
        .limit(limite)
    ).all()
    return _decorar(filas, usuario)


# ---------------------------------------------------------------------------------------
# Read routes
# ---------------------------------------------------------------------------------------
@comunidad.route("/community", methods=["GET"])
@login_required
def feed() -> str:
    """The Hub feed: Latest or Trending, filtered by type, searchable."""
    _exigir_miembro()
    usuario = current_user.usuario

    vista = request.args.get("view", "latest")
    if vista not in ("latest", "trending"):
        vista = "latest"
    tipo = request.args.get("tipo")
    if tipo not in COMUNIDAD_TIPOS:
        tipo = None
    consulta = (request.args.get("q") or "").strip()

    degradado = False
    if vista == "trending" and not tipo and not consulta:
        publicaciones, rankeado = calcular_trending(usuario)
        if not rankeado:
            degradado = True
    else:
        publicaciones, rankeado = [], False

    if not rankeado:
        seleccion = _publicaciones_base().filter(ComunidadPublicacion.fijado.is_(False))
        if tipo:
            seleccion = seleccion.filter(ComunidadPublicacion.tipo == tipo)
        if consulta:
            patron = f"%{consulta}%"
            seleccion = seleccion.filter(
                database.or_(ComunidadPublicacion.titulo.ilike(patron), ComunidadPublicacion.contenido.ilike(patron))
            )
        filas = database.session.execute(
            seleccion.order_by(ComunidadPublicacion.fecha_creacion.desc()).limit(POR_PAGINA)
        ).all()
        publicaciones = _decorar(filas, usuario)

    # Sidebar. Trending is shown only when it genuinely ranks — a shortlist of
    # three posts labelled "Trending" on thin data is the fabrication the fallback
    # exists to prevent, so the card is omitted rather than filled with filler.
    destacados, hay_destacados = calcular_trending(usuario)
    return render_template(
        FEED_TEMPLATE,
        publicaciones=publicaciones,
        eventos=get_upcoming_events_for_user(usuario, limit=5),
        destacados=destacados[:4] if hay_destacados else [],
        anclados=_anclados(usuario) if not consulta and not tipo else [],
        anuncios=anuncios_activos() if not consulta and not tipo else [],
        vista=vista,
        degradado=degradado,
        tipo=tipo,
        consulta=consulta,
        tipos=[(t, TIPO_ETIQUETAS[t]) for t in COMUNIDAD_TIPOS],
        es_staff=es_staff(),
        accion_form=AccionForm(),
        mis_iniciales=iniciales(current_user),
    )


@comunidad.route("/community/post/<publicacion_id>", methods=["GET"])
@login_required
def ver_publicacion(publicacion_id: str) -> str:
    """One post and its replies."""
    _exigir_miembro()
    usuario = current_user.usuario

    fila = database.session.execute(
        select(ComunidadPublicacion, Usuario)
        .join(Usuario, Usuario.usuario == ComunidadPublicacion.usuario)
        .filter(ComunidadPublicacion.id == publicacion_id, ComunidadPublicacion.parent_id.is_(None))
    ).first()
    # 404 rather than 403 on a hidden post: a 403 confirms it exists.
    if not fila:
        abort(404)
    pub, _autor = fila
    if pub.estado_moderacion != "visible" and not (es_staff() or pub.usuario == usuario):
        abort(404)

    respuesta = database.aliased(ComunidadPublicacion)
    respuestas = database.session.execute(
        select(respuesta, Usuario)
        .join(Usuario, Usuario.usuario == respuesta.usuario)
        .filter(respuesta.parent_id == publicacion_id, respuesta.estado_moderacion == "visible")
        .order_by(respuesta.fecha_creacion)
    ).all()

    decorado = _decorar([fila], usuario)[0]
    return render_template(
        POST_TEMPLATE,
        item=decorado,
        cuerpo=markdown_seguro(pub.contenido),
        respuestas=[
            {
                "autor": a,
                "cuerpo": markdown_seguro(r.contenido),
                "es_staff": a.tipo in ROLES_STAFF,
            }
            for r, a in respuestas
        ],
        cerrado=pub.estado == "cerrado",
        oculto=pub.estado_moderacion != "visible",
        respuesta_form=RespuestaForm(),
        reporte_form=ReporteForm(),
        moderacion_form=ModeracionForm(),
        accion_form=AccionForm(),
        es_staff=es_staff(),
    )


# ---------------------------------------------------------------------------------------
# Write routes
# ---------------------------------------------------------------------------------------
@comunidad.route("/community/new", methods=["GET", "POST"])
@login_required
@email_verificado_requerido
def nueva_publicacion() -> str | Response:
    """Compose a post."""
    _exigir_miembro()
    form = PublicacionForm()
    if form.validate_on_submit():
        if _limitado("post", current_user.usuario):
            flash(_("You have posted a lot in a short time. Try again shortly."), "warning")
            return redirect(url_for("comunidad.feed"))
        if not enlace_valido(form.enlace_build.data):
            # Re-render the bound form rather than redirect: a redirect lands on a
            # blank GET compose form and silently discards the typed title and body.
            flash(_("That link does not look like a web address."), "warning")
            return render_template(NUEVO_TEMPLATE, form=form, tipos=[(t, TIPO_ETIQUETAS[t]) for t in COMUNIDAD_TIPOS])

        publicacion = ComunidadPublicacion(
            parent_id=None,
            usuario=current_user.usuario,
            contenido=form.contenido.data,
            titulo=form.titulo.data,
            tipo=form.tipo.data,
            enlace_build=(form.enlace_build.data or None),
            fijado=False,
            estado_moderacion="visible",
            estado="abierto",
            reportes_abiertos=0,
        )
        database.session.add(publicacion)
        database.session.commit()
        return redirect(url_for("comunidad.ver_publicacion", publicacion_id=publicacion.id))

    return render_template(NUEVO_TEMPLATE, form=form, tipos=[(t, TIPO_ETIQUETAS[t]) for t in COMUNIDAD_TIPOS])


@comunidad.route("/community/post/<publicacion_id>/reply", methods=["POST"])
@login_required
@email_verificado_requerido
def responder(publicacion_id: str) -> Response:
    """Reply to a post."""
    _exigir_miembro()
    raiz = _cargar(publicacion_id)
    if raiz.estado == "cerrado":
        flash(_("Replies are closed on this thread."), "warning")
        return redirect(url_for("comunidad.ver_publicacion", publicacion_id=publicacion_id))

    form = RespuestaForm()
    if form.validate_on_submit():
        if _limitado("reply", current_user.usuario):
            flash(_("You have replied a lot in a short time. Try again shortly."), "warning")
        else:
            database.session.add(
                ComunidadPublicacion(
                    parent_id=publicacion_id,
                    usuario=current_user.usuario,
                    contenido=form.contenido.data,
                    estado_moderacion="visible",
                    estado="abierto",
                    fijado=False,
                    reportes_abiertos=0,
                )
            )
            database.session.commit()
    return redirect(url_for("comunidad.ver_publicacion", publicacion_id=publicacion_id))


@comunidad.route("/community/post/<publicacion_id>/like", methods=["POST"])
@login_required
@email_verificado_requerido
def dar_like(publicacion_id: str) -> Response:
    """Idempotent like. Never a toggle.

    Two endpoints rather than one toggle because a toggle under a double-click
    flips twice and lands wherever the race left it, while two idempotent
    endpoints always converge on the state the member asked for. The database
    unique constraint is the arbiter — there is no read-then-write window.
    """
    _exigir_miembro()
    raiz = _cargar(publicacion_id)
    if raiz.usuario == current_user.usuario:
        abort(403)  # a member cannot like their own post
    if not AccionForm().validate_on_submit():
        abort(400)
    if _limitado("like", current_user.usuario):
        return redirect(_destino_local(url_for("comunidad.feed")))

    try:
        with database.session.begin_nested():
            database.session.add(ComunidadReaccion(publicacion_id=publicacion_id, usuario=current_user.usuario))
    except IntegrityError:
        # Already liked. The constraint absorbed a concurrent duplicate; this is success.
        pass
    database.session.commit()
    return redirect(_destino_local(url_for("comunidad.ver_publicacion", publicacion_id=publicacion_id)))


@comunidad.route("/community/post/<publicacion_id>/unlike", methods=["POST"])
@login_required
@email_verificado_requerido
def quitar_like(publicacion_id: str) -> Response:
    """Idempotent unlike. Deleting zero rows is success."""
    _exigir_miembro()
    if not AccionForm().validate_on_submit():
        abort(400)
    database.session.execute(
        database.delete(ComunidadReaccion).where(
            ComunidadReaccion.publicacion_id == publicacion_id, ComunidadReaccion.usuario == current_user.usuario
        )
    )
    database.session.commit()
    return redirect(_destino_local(url_for("comunidad.ver_publicacion", publicacion_id=publicacion_id)))


@comunidad.route("/community/post/<publicacion_id>/report", methods=["POST"])
@login_required
@email_verificado_requerido
def reportar(publicacion_id: str) -> Response:
    """Report a post. Reporting never hides anything — only a staff action does."""
    _exigir_miembro()
    pub = _cargar(publicacion_id)
    form = ReporteForm()
    if form.validate_on_submit() and not _limitado("report", current_user.usuario):
        database.session.add(
            ComunidadEventoModeracion(
                publicacion_id=publicacion_id, tipo="report", actor=current_user.usuario, motivo=form.motivo.data
            )
        )
        pub.reportes_abiertos = (pub.reportes_abiertos or 0) + 1
        database.session.commit()
        flash(_("Thank you. A moderator will look at this."), "info")
    return redirect(url_for("comunidad.ver_publicacion", publicacion_id=publicacion_id))


# ---------------------------------------------------------------------------------------
# Moderation
# ---------------------------------------------------------------------------------------
def _cargar(publicacion_id: str, *, permitir_oculta: bool = False) -> ComunidadPublicacion:
    """Load a root post, 404 when it is not one or when the caller may not see it.

    The moderation boundary lives here rather than at each call site, and it defaults
    to CLOSED. `ver_publicacion` already 404s a hidden post for anyone but staff and
    its author, but the mutation routes reloaded the row through this helper without
    that check, so a member who knew a hidden post's ID could still reply to it, like
    it or report it — and could distinguish "hidden" from "never existed" by whether
    the write succeeded. Found by Greptile on PR #82.

    Fail-closed is the point: a new caller gets the boundary without remembering to
    ask for it. Only the staff moderation actions pass ``permitir_oculta=True``, and
    every one of them calls ``_exigir_staff()`` before this.

    404 rather than 403, matching the read route: a 403 confirms the post exists.
    """
    fila = database.session.execute(
        select(ComunidadPublicacion).filter(
            ComunidadPublicacion.id == publicacion_id, ComunidadPublicacion.parent_id.is_(None)
        )
    ).scalars().first()
    if not fila:
        abort(404)
    if not permitir_oculta and fila.estado_moderacion != "visible":
        if not (es_staff() or fila.usuario == current_user.usuario):
            abort(404)
    return fila


def _registrar(publicacion_id: str, tipo: str, motivo: str | None = None) -> None:
    database.session.add(
        ComunidadEventoModeracion(
            publicacion_id=publicacion_id, tipo=tipo, actor=current_user.usuario, motivo=motivo
        )
    )


@comunidad.route("/community/post/<publicacion_id>/hide", methods=["POST"])
@login_required
def ocultar(publicacion_id: str) -> Response:
    """Hide a post. Reversible, reasoned, and recorded. Nothing is deleted."""
    _exigir_staff()
    pub = _cargar(publicacion_id, permitir_oculta=True)
    form = ModeracionForm()
    if form.validate_on_submit():
        pub.estado_moderacion = "oculto"
        _registrar(publicacion_id, "hide", form.motivo.data)
        database.session.commit()
        flash(_("Post hidden."), "info")
    else:
        flash(_("A reason is required to hide a post."), "warning")
    return redirect(url_for("comunidad.ver_publicacion", publicacion_id=publicacion_id))


@comunidad.route("/community/post/<publicacion_id>/restore", methods=["POST"])
@login_required
def restaurar(publicacion_id: str) -> Response:
    """Reverse a hide and clear the report queue counter."""
    _exigir_staff()
    pub = _cargar(publicacion_id, permitir_oculta=True)
    if AccionForm().validate_on_submit():
        pub.estado_moderacion = "visible"
        pub.reportes_abiertos = 0
        _registrar(publicacion_id, "restore")
        database.session.commit()
    return redirect(url_for("comunidad.ver_publicacion", publicacion_id=publicacion_id))


@comunidad.route("/community/post/<publicacion_id>/lock", methods=["POST"])
@login_required
def cerrar(publicacion_id: str) -> Response:
    """Close replies. Same `abierto`/`cerrado` vocabulary the native forum uses."""
    _exigir_staff()
    raiz = _cargar(publicacion_id, permitir_oculta=True)
    if AccionForm().validate_on_submit():
        raiz.estado = "cerrado"
        _registrar(publicacion_id, "lock")
        database.session.commit()
    return redirect(url_for("comunidad.ver_publicacion", publicacion_id=publicacion_id))


@comunidad.route("/community/post/<publicacion_id>/unlock", methods=["POST"])
@login_required
def abrir(publicacion_id: str) -> Response:
    """Reopen replies."""
    _exigir_staff()
    raiz = _cargar(publicacion_id, permitir_oculta=True)
    if AccionForm().validate_on_submit():
        raiz.estado = "abierto"
        _registrar(publicacion_id, "unlock")
        database.session.commit()
    return redirect(url_for("comunidad.ver_publicacion", publicacion_id=publicacion_id))


@comunidad.route("/community/post/<publicacion_id>/pin", methods=["POST"])
@login_required
def fijar(publicacion_id: str) -> Response:
    """Pin a post above the feed. Admins only."""
    if not (current_user.is_authenticated and current_user.tipo == "admin"):
        abort(403)
    pub = _cargar(publicacion_id, permitir_oculta=True)
    if AccionForm().validate_on_submit():
        pub.fijado = not pub.fijado
        _registrar(publicacion_id, "pin" if pub.fijado else "unpin")
        database.session.commit()
    return redirect(url_for("comunidad.ver_publicacion", publicacion_id=publicacion_id))


@comunidad.route("/community/staff", methods=["GET"])
@login_required
def staff() -> str:
    """The Hub as staff need it: what needs answering, what needs a decision.

    Deliberately NOT a mirror of the member feed. A member's question is "what is
    the cohort talking about"; a moderator's is "what is waiting on me". So this
    leads with unanswered questions — the Hub exists so a question gets answered
    once and stays findable, and a question with no reply is the only thing here
    that is actively failing that promise.

    Query budget is flat in the number of posts, like the feed: one query per
    panel plus the shared aggregates, never one per row.
    """
    _exigir_staff()
    usuario = current_user.usuario
    ahora = utc_now().replace(tzinfo=None)
    semana = ahora - timedelta(days=7)

    respuesta = database.aliased(ComunidadPublicacion)
    conteo_respuestas = (
        select(respuesta.parent_id, func.count(respuesta.id).label("n"))
        .filter(respuesta.parent_id.isnot(None))
        .group_by(respuesta.parent_id)
        .subquery()
    )

    # Unanswered questions, oldest first: the longest-waiting member is the most
    # overdue, so this is not sorted newest-first like everything else.
    sin_responder = database.session.execute(
        _publicaciones_base()
        .outerjoin(conteo_respuestas, conteo_respuestas.c.parent_id == ComunidadPublicacion.id)
        .filter(
            ComunidadPublicacion.tipo == "question",
            database.or_(conteo_respuestas.c.n.is_(None), conteo_respuestas.c.n == 0),
        )
        .order_by(ComunidadPublicacion.fecha_creacion)
    ).all()

    reportados = database.session.execute(
        select(ComunidadPublicacion, Usuario)
        .join(Usuario, Usuario.usuario == ComunidadPublicacion.usuario)
        .filter(ComunidadPublicacion.reportes_abiertos > 0)
        .order_by(ComunidadPublicacion.reportes_abiertos.desc())
    ).all()

    ocultos = database.session.execute(
        select(ComunidadPublicacion, Usuario)
        .join(Usuario, Usuario.usuario == ComunidadPublicacion.usuario)
        .filter(
            ComunidadPublicacion.estado_moderacion == "oculto",
            ComunidadPublicacion.parent_id.is_(None),
        )
        .order_by(ComunidadPublicacion.fecha_creacion.desc())
    ).all()

    eventos = (
        database.session.execute(
            select(ComunidadEventoModeracion, Usuario)
            .join(Usuario, Usuario.usuario == ComunidadEventoModeracion.actor)
            .order_by(ComunidadEventoModeracion.ocurrido_en.desc())
            .limit(25)
        )
        .all()
    )

    publicaciones_semana = database.session.execute(
        select(func.count(ComunidadPublicacion.id)).filter(
            ComunidadPublicacion.parent_id.is_(None),
            ComunidadPublicacion.fecha_creacion >= semana,
        )
    ).scalar()
    miembros_semana = database.session.execute(
        select(func.count(func.distinct(ComunidadPublicacion.usuario))).filter(
            ComunidadPublicacion.fecha_creacion >= semana
        )
    ).scalar()

    return render_template(
        STAFF_TEMPLATE,
        sin_responder=_decorar(sin_responder, usuario),
        reportados=_decorar(reportados, usuario),
        ocultos=_decorar(ocultos, usuario),
        eventos=[{"evento": e, "actor": a, "hace": hace(e.ocurrido_en)} for e, a in eventos],
        resumen={
            "sin_responder": len(sin_responder),
            "reportes": len(reportados),
            "ocultos": len(ocultos),
            "publicaciones_semana": publicaciones_semana or 0,
            "miembros_semana": miembros_semana or 0,
        },
        accion_form=AccionForm(),
        moderacion_form=ModeracionForm(),
    )
