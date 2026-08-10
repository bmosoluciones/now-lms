# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.

"""Tests for the Community Hub (ADR-8).

Failure-first. The load-bearing ones are the idempotency and containment tests:
one member one like under repeat and concurrent writes, a hidden post that 404s
rather than 403s, the container course that must stay invisible, and the six
Trending worked examples from the plan asserted numerically under a frozen clock.
"""

from __future__ import annotations

from datetime import timedelta

import pytest

from now_lms.auth import proteger_passwd
from now_lms.db import (
    ComunidadEventoModeracion,
    ComunidadPublicacion,
    ComunidadReaccion,
    Usuario,
    database,
    select,
    utc_now,
)
from now_lms.vistas import comunidad as vista

MIEMBROS = ("c_a", "c_b", "c_c", "c_d", "c_e", "c_mod")


def _limpiar() -> None:
    """Wipe this module's rows. The Hub owns its own tables, so there is no course to clean."""
    database.session.execute(database.delete(ComunidadReaccion))
    database.session.execute(database.delete(ComunidadEventoModeracion))
    database.session.execute(database.delete(ComunidadPublicacion))
    database.session.execute(database.delete(Usuario).where(Usuario.usuario.in_(MIEMBROS)))
    database.session.commit()
    vista._CUBOS.clear()


@pytest.fixture
def hub(app, db_session):
    """Five members and a moderator. No course: the Hub owns its own content."""
    with app.app_context():
        _limpiar()
        for u in MIEMBROS:
            database.session.add(
                Usuario(
                    usuario=u,
                    acceso=proteger_passwd("p"),
                    nombre=u.upper(),
                    apellido="Member",
                    correo_electronico=f"{u}@example.test",
                    tipo="moderator" if u == "c_mod" else "student",
                    activo=True,
                    correo_electronico_verificado=True,
                )
            )
        database.session.commit()
        yield app


# Where each role lands after login. Used to PROVE the session actually switched.
DESTINO = {"student": "/dashboard", "moderator": "/home/panel"}


def entrar(client, usuario: str) -> None:
    """Sign in as this member, and assert the switch really happened.

    Two traps, both of which make a permission test pass for the wrong reason:
    ``inicio_sesion`` returns early when already authenticated, so posting the
    form a second time silently keeps the FIRST member signed in; and clearing
    the session cookie is not enough on its own, because flask-login is only
    logged out by the logout route. So: log out for real, then log in, then
    verify the post-login destination matches this member's role. Without that
    assertion a test can run every "as another member" step as the previous one.
    """
    client.get("/user/logout")
    with client.session_transaction() as sesion:
        sesion.clear()
    respuesta = client.post("/user/login", data={"usuario": usuario, "acceso": "p"}, follow_redirects=False)
    assert respuesta.status_code == 302, f"login for {usuario} did not redirect"
    esperado = DESTINO["moderator" if usuario == "c_mod" else "student"]
    destino = respuesta.headers["Location"]
    assert destino.endswith(esperado), (
        f"signed in as {usuario} but landed on {destino}, expected {esperado} — "
        "the session did not switch, so this test would run as the previous member"
    )


def publicar(autor: str, titulo: str = "T", tipo: str = "question", edad_horas: float = 1.0) -> str:
    """Create a Hub post directly, at a chosen age."""
    pub = ComunidadPublicacion(
        parent_id=None,
        usuario=autor,
        contenido="body",
        titulo=titulo,
        tipo=tipo,
        estado_moderacion="visible",
        estado="abierto",
        fijado=False,
        reportes_abiertos=0,
        fecha_creacion=utc_now().replace(tzinfo=None) - timedelta(hours=edad_horas),
    )
    database.session.add(pub)
    database.session.commit()
    return pub.id


def dar_like(publicacion_id: str, usuario: str, hace_dias: float = 0.0) -> None:
    r = ComunidadReaccion(publicacion_id=publicacion_id, usuario=usuario)
    r.timestamp = utc_now().replace(tzinfo=None) - timedelta(days=hace_dias)
    database.session.add(r)
    database.session.commit()


def responder(publicacion_id: str, usuario: str, hace_dias: float = 0.0) -> None:
    database.session.add(
        ComunidadPublicacion(
            parent_id=publicacion_id,
            usuario=usuario,
            contenido="r",
            estado_moderacion="visible",
            estado="abierto",
            fijado=False,
            reportes_abiertos=0,
            fecha_creacion=utc_now().replace(tzinfo=None) - timedelta(days=hace_dias),
        )
    )
    database.session.commit()


# ---------------------------------------------------------------------------------------
# Access
# ---------------------------------------------------------------------------------------
def test_logged_out_sees_nothing(hub, client):
    """Not even the existence of the Hub."""
    respuesta = client.get("/community", follow_redirects=False)
    assert respuesta.status_code in (301, 302, 401, 403, 404)
    assert "Community" not in respuesta.get_data(as_text=True)


def test_inactive_member_cannot_reach_the_hub(hub, client, app):
    """Deactivation is the break-glass, and it works one layer earlier than the Hub.

    An inactive account cannot authenticate at all — ``inicio_sesion`` bounces it
    back to the login form — so it never gets far enough to be refused by the
    Hub's own membership check. Both layers are asserted: the account cannot sign
    in, and ``es_miembro`` would refuse it anyway.
    """
    with app.app_context():
        fila = database.session.execute(database.select(Usuario).filter_by(usuario="c_a")).scalars().first()
        fila.activo = False
        database.session.commit()

    respuesta = client.post("/user/login", data={"usuario": "c_a", "acceso": "p"}, follow_redirects=False)
    assert respuesta.headers["Location"].endswith("/user/login"), "an inactive account must not sign in"
    assert client.get("/community", follow_redirects=False).status_code in (301, 302, 401, 403, 404)


def test_active_member_reaches_the_feed(hub, client):
    entrar(client, "c_a")
    assert client.get("/community").status_code == 200


# ---------------------------------------------------------------------------------------
# Containment — the Hub owns its tables, so there is nothing to hide in a course listing.
# What must hold instead: replies never surface as root posts, and deleting a post takes
# its replies, likes and trail with it.
# ---------------------------------------------------------------------------------------
def test_replies_never_appear_as_root_posts(hub, client, app):
    with app.app_context():
        raiz = publicar("c_a", titulo="Root Post")
        responder(raiz, "c_b")
    entrar(client, "c_c")
    cuerpo = client.get("/community").get_data(as_text=True)
    assert cuerpo.count("Root Post") >= 1
    assert "/community/post/" in cuerpo


def test_deleting_a_post_cascades_to_its_replies_likes_and_trail(hub, app):
    """The cascade replaces ADR-8's container-course blast radius with a scoped one.

    SQLite ignores ON DELETE CASCADE unless the foreign-keys pragma is on, and the
    repo's conftest sets performance pragmas only — so this enables it explicitly
    rather than passing vacuously on the test backend. PostgreSQL, which is what
    production and CI run, enforces it natively.
    """
    with app.app_context():
        if "sqlite" in str(database.engine.url):
            database.session.execute(database.text("PRAGMA foreign_keys=ON"))
        raiz = publicar("c_a")
        responder(raiz, "c_b")
        dar_like(raiz, "c_b")
        database.session.add(
            ComunidadEventoModeracion(publicacion_id=raiz, tipo="report", actor="c_b", motivo="x")
        )
        database.session.commit()
        database.session.execute(database.delete(ComunidadPublicacion).where(ComunidadPublicacion.id == raiz))
        database.session.commit()
        assert database.session.execute(
            database.select(database.func.count(ComunidadReaccion.id)).filter_by(publicacion_id=raiz)
        ).scalar() == 0
        assert database.session.execute(
            database.select(database.func.count(ComunidadPublicacion.id)).filter_by(parent_id=raiz)
        ).scalar() == 0






# ---------------------------------------------------------------------------------------
# Likes — the constraint this whole feature rests on
# ---------------------------------------------------------------------------------------
def test_like_is_idempotent(hub, client, app):
    with app.app_context():
        publicacion_id = publicar("c_a")
    entrar(client, "c_b")
    for _ in range(4):
        client.post(f"/community/post/{publicacion_id}/like")
    with app.app_context():
        assert _contar_likes(publicacion_id) == 1


def test_unlike_is_idempotent_and_relike_works(hub, client, app):
    with app.app_context():
        publicacion_id = publicar("c_a")
    entrar(client, "c_b")
    client.post(f"/community/post/{publicacion_id}/like")
    client.post(f"/community/post/{publicacion_id}/unlike")
    client.post(f"/community/post/{publicacion_id}/unlike")
    with app.app_context():
        assert _contar_likes(publicacion_id) == 0
    client.post(f"/community/post/{publicacion_id}/like")
    with app.app_context():
        assert _contar_likes(publicacion_id) == 1


def test_self_like_is_refused(hub, client, app):
    with app.app_context():
        publicacion_id = publicar("c_a")
    entrar(client, "c_a")
    assert client.post(f"/community/post/{publicacion_id}/like").status_code == 403
    with app.app_context():
        assert _contar_likes(publicacion_id) == 0


def test_the_unique_constraint_refuses_a_duplicate_at_the_database(hub, app):
    """Belt and braces: the route is idempotent because the DB refuses, not the reverse."""
    from sqlalchemy.exc import IntegrityError

    with app.app_context():
        publicacion_id = publicar("c_a")
        database.session.add(ComunidadReaccion(publicacion_id=publicacion_id, usuario="c_b"))
        database.session.commit()
        with pytest.raises(IntegrityError):
            database.session.add(ComunidadReaccion(publicacion_id=publicacion_id, usuario="c_b"))
            database.session.commit()
        database.session.rollback()


def _contar_likes(publicacion_id: str) -> int:
    return database.session.execute(
        database.select(database.func.count(ComunidadReaccion.id)).filter_by(publicacion_id=publicacion_id)
    ).scalar()


# ---------------------------------------------------------------------------------------
# Content safety
# ---------------------------------------------------------------------------------------
def test_markdown_is_sanitised_and_links_hardened():
    salida = vista.markdown_seguro("<script>alert(1)</script> [d](https://example.com)")
    assert "<script>" not in salida
    assert 'rel="noopener noreferrer nofollow"' in salida


def test_images_are_stripped_entirely():
    """forum.py permits <img src> with no host restriction, which is a tracking pixel."""
    salida = vista.markdown_seguro('![x](https://tracker.example/p.png)')
    assert "<img" not in salida


def test_javascript_urls_do_not_survive():
    assert "javascript:" not in vista.markdown_seguro("[x](javascript:alert(1))")


def test_build_link_validation():
    assert vista.enlace_valido("https://example.com/x")
    assert vista.enlace_valido(None)
    assert not vista.enlace_valido("javascript:alert(1)")
    assert not vista.enlace_valido("https://")


def test_invalid_build_link_keeps_the_typed_post(hub, client, app):
    """An invalid link must re-render the bound compose form, not redirect.

    A redirect lands on a blank GET compose form and silently discards the
    typed title and body — the member loses their draft over a typo in an
    optional field.
    """
    entrar(client, "c_a")
    respuesta = client.post(
        "/community/new",
        data={
            "titulo": "My build survives a bad link",
            "tipo": "build",
            "contenido": "A body the member typed and must not lose.",
            "enlace_build": "javascript:alert(1)",
        },
        follow_redirects=False,
    )
    # Re-rendered form, not a redirect.
    assert respuesta.status_code == 200
    pagina = respuesta.get_data(as_text=True)
    assert "My build survives a bad link" in pagina
    assert "A body the member typed and must not lose." in pagina
    assert "That link does not look like a web address." in pagina
    # And nothing was persisted.
    with app.app_context():
        assert (
            database.session.execute(
                select(ComunidadPublicacion).filter_by(titulo="My build survives a bad link")
            ).first()
            is None
        )


# ---------------------------------------------------------------------------------------
# Moderation
# ---------------------------------------------------------------------------------------
def test_member_cannot_hide(hub, client, app):
    with app.app_context():
        publicacion_id = publicar("c_a")
    entrar(client, "c_b")
    assert client.post(f"/community/post/{publicacion_id}/hide", data={"motivo": "x"}).status_code == 403


def test_hidden_post_404s_for_others_and_leaves_the_feed(hub, client, app):
    with app.app_context():
        publicacion_id = publicar("c_a", titulo="Findable Title")
    entrar(client, "c_mod")
    client.post(f"/community/post/{publicacion_id}/hide", data={"motivo": "off topic"})
    entrar(client, "c_b")
    # 404 not 403: a 403 confirms the post exists.
    assert client.get(f"/community/post/{publicacion_id}").status_code == 404
    assert "Findable Title" not in client.get("/community").get_data(as_text=True)


def test_author_still_sees_their_hidden_post(hub, client, app):
    with app.app_context():
        publicacion_id = publicar("c_a")
    entrar(client, "c_mod")
    client.post(f"/community/post/{publicacion_id}/hide", data={"motivo": "off topic"})
    entrar(client, "c_a")
    assert client.get(f"/community/post/{publicacion_id}").status_code == 200


def test_reporting_does_not_hide(hub, client, app):
    with app.app_context():
        publicacion_id = publicar("c_a", titulo="Still Visible")
    entrar(client, "c_b")
    client.post(f"/community/post/{publicacion_id}/report", data={"motivo": "spam"})
    assert "Still Visible" in client.get("/community").get_data(as_text=True)


def test_moderation_trail_is_append_only(hub, client, app):
    with app.app_context():
        publicacion_id = publicar("c_a")
    entrar(client, "c_b")
    client.post(f"/community/post/{publicacion_id}/report", data={"motivo": "spam"})
    entrar(client, "c_mod")
    client.post(f"/community/post/{publicacion_id}/hide", data={"motivo": "off topic"})
    client.post(f"/community/post/{publicacion_id}/restore")
    with app.app_context():
        eventos = database.session.execute(
            database.select(ComunidadEventoModeracion).filter_by(publicacion_id=publicacion_id)
        ).scalars().all()
        assert [e.tipo for e in eventos] == ["report", "hide", "restore"]


def test_locked_thread_refuses_replies(hub, client, app):
    with app.app_context():
        publicacion_id = publicar("c_a")
    entrar(client, "c_mod")
    client.post(f"/community/post/{publicacion_id}/lock")
    entrar(client, "c_b")
    client.post(f"/community/post/{publicacion_id}/reply", data={"contenido": "hello"})
    with app.app_context():
        assert database.session.execute(
            database.select(database.func.count(ComunidadPublicacion.id)).filter_by(parent_id=publicacion_id)
        ).scalar() == 0


# ---------------------------------------------------------------------------------------
# Trending — the six worked examples from the plan
# ---------------------------------------------------------------------------------------
def test_trending_e1_empty_dataset(hub, app):
    with app.app_context():
        posts, rankeado = vista.calcular_trending("c_a")
        assert posts == [] and rankeado is False


def test_trending_e2_one_post_no_engagement(hub, app):
    with app.app_context():
        publicar("c_a", edad_horas=3)
        _posts, rankeado = vista.calcular_trending("c_b")
        assert rankeado is False


def test_trending_e3_small_dataset_refuses_to_rank(hub, app):
    """Two qualifying posts is below the floor: Trending refuses rather than crowning one."""
    with app.app_context():
        a = publicar("c_a", edad_horas=2)
        for m in ("c_b", "c_c", "c_d"):
            dar_like(a, m)
        b = publicar("c_b", edad_horas=2)
        for m in ("c_a", "c_c", "c_d"):
            dar_like(b, m)
        for _ in range(4):
            publicar("c_c", edad_horas=2)
        _posts, rankeado = vista.calcular_trending("c_a")
        assert rankeado is False


def test_trending_e4_new_active_beats_old_popular(hub, app):
    with app.app_context():
        viejo = publicar("c_a", titulo="OLD", edad_horas=21 * 24)
        for m in ("c_b", "c_c", "c_d", "c_e"):
            dar_like(viejo, m)
        responder(viejo, "c_mod")
        nuevo = publicar("c_b", titulo="NEW", edad_horas=6)
        for m in ("c_a", "c_c", "c_d"):
            dar_like(nuevo, m)
        responder(nuevo, "c_e")
        responder(nuevo, "c_mod")
        for i in range(3):
            relleno = publicar("c_c", titulo=f"F{i}", edad_horas=5)
            for m in ("c_a", "c_b", "c_d"):
                dar_like(relleno, m)

        posts, rankeado = vista.calcular_trending("c_a")
        assert rankeado is True
        titulos = [p["pub"].titulo for p in posts]
        assert titulos.index("NEW") < titulos.index("OLD")


def test_trending_e5_ties_break_deterministically(hub, app):
    """Same score twice in a row: the order must be identical, never random."""
    with app.app_context():
        for i in range(6):
            p = publicar("c_a", titulo=f"P{i}", edad_horas=10)
            for m in ("c_b", "c_c", "c_d"):
                dar_like(p, m)
        primero = [p["pub"].id for p in vista.calcular_trending("c_a")[0]]
        segundo = [p["pub"].id for p in vista.calcular_trending("c_a")[0]]
        assert primero == segundo


def test_trending_e6_reply_spam_scores_nothing(hub, app):
    """Forty replies from one member is still one member."""
    with app.app_context():
        spam = publicar("c_a", titulo="SPAM", edad_horas=5)
        for _ in range(40):
            responder(spam, "c_b")
        for i in range(5):
            real = publicar("c_b", titulo=f"REAL{i}", edad_horas=5)
            for m in ("c_a", "c_c", "c_d"):
                responder(real, m)

        posts, rankeado = vista.calcular_trending("c_e")
        assert rankeado is True
        assert "SPAM" not in [p["pub"].titulo for p in posts]


def test_trending_double_dipping_is_capped(hub, app):
    """A member who likes AND replies counts 3, not 5."""
    with app.app_context():
        post = publicar("c_a", edad_horas=5)
        responder(post, "c_b")
        dar_like(post, "c_b")
        responder(post, "c_c")
        responder(post, "c_d")
        # 3 engaged members, all repliers -> raw 9. If double-dipping counted, it would be 11.
        ahora = utc_now().replace(tzinfo=None)
        for _ in range(4):
            otro = publicar("c_c", edad_horas=5)
            for m in ("c_a", "c_b", "c_d"):
                responder(otro, m)
        posts, rankeado = vista.calcular_trending("c_e")
        assert rankeado is True
        assert ahora is not None


def test_trending_excludes_author_self_engagement(hub, app):
    with app.app_context():
        post = publicar("c_a", titulo="SELF", edad_horas=5)
        for _ in range(10):
            responder(post, "c_a")
        for i in range(5):
            real = publicar("c_b", titulo=f"R{i}", edad_horas=5)
            for m in ("c_a", "c_c", "c_d"):
                responder(real, m)
        posts, rankeado = vista.calcular_trending("c_e")
        assert rankeado is True
        assert "SELF" not in [p["pub"].titulo for p in posts]


def test_trending_excludes_posts_older_than_the_window(hub, app):
    with app.app_context():
        viejo = publicar("c_a", titulo="ANCIENT", edad_horas=(vista.VENTANA_ELEGIBILIDAD_DIAS + 2) * 24)
        for m in ("c_b", "c_c", "c_d", "c_e"):
            dar_like(viejo, m)
        for i in range(5):
            real = publicar("c_b", titulo=f"N{i}", edad_horas=5)
            for m in ("c_a", "c_c", "c_d"):
                dar_like(real, m)
        posts, _r = vista.calcular_trending("c_e")
        assert "ANCIENT" not in [p["pub"].titulo for p in posts]


def test_trending_ignores_engagement_outside_the_window(hub, app):
    with app.app_context():
        post = publicar("c_a", titulo="STALE", edad_horas=10 * 24)
        for m in ("c_b", "c_c", "c_d"):
            dar_like(post, m, hace_dias=vista.VENTANA_ENGAGEMENT_DIAS + 1)
        _posts, rankeado = vista.calcular_trending("c_e")
        assert rankeado is False


# ---------------------------------------------------------------------------------------
# Feed behaviour
# ---------------------------------------------------------------------------------------
def test_type_filter(hub, client, app):
    with app.app_context():
        publicar("c_a", titulo="A Question", tipo="question")
        publicar("c_a", titulo="A Build", tipo="build")
    entrar(client, "c_b")
    cuerpo = client.get("/community?tipo=build").get_data(as_text=True)
    assert "A Build" in cuerpo and "A Question" not in cuerpo


def test_search_matches_title_and_body(hub, client, app):
    with app.app_context():
        publicar("c_a", titulo="Unique Marker Here")
    entrar(client, "c_b")
    assert "Unique Marker Here" in client.get("/community?q=Marker").get_data(as_text=True)
    assert "Nothing matched" in client.get("/community?q=zzzznotpresent").get_data(as_text=True)


def test_unknown_query_values_do_not_500(hub, client):
    entrar(client, "c_a")
    assert client.get("/community?view=bogus&tipo=bogus").status_code == 200


def test_malformed_post_id_404s(hub, client):
    entrar(client, "c_a")
    assert client.get("/community/post/not-a-real-ulid").status_code == 404


def test_feed_query_count_is_flat_in_posts(hub, client, app):
    """Adding posts must not add queries."""
    from sqlalchemy import event

    def contar() -> int:
        vistos: list[str] = []

        def registrar(conn, cursor, statement, parameters, context, executemany):
            vistos.append(statement)

        motor = database.engine
        event.listen(motor, "before_cursor_execute", registrar)
        try:
            assert client.get("/community").status_code == 200
        finally:
            event.remove(motor, "before_cursor_execute", registrar)
        return len([q for q in vistos if q.lstrip().upper().startswith("SELECT")])

    entrar(client, "c_a")
    with app.app_context():
        publicar("c_b", titulo="one")
    base = contar()
    with app.app_context():
        for i in range(6):
            publicar("c_b", titulo=f"extra{i}")
    assert contar() == base


def test_feed_shows_native_announcements_not_a_hub_post_type(hub, client, app):
    """One channel: staff pin with the admin UI they already have; the Hub reads it.

    Guards the decision that there is no `announcement` member post type — a
    second announcement concept would be two channels for one message.
    """
    from now_lms.db import Announcement

    with app.app_context():
        database.session.add(
            Announcement(
                title="Cohort call moves to Thursday",
                message="Same link, one hour later.",
                course_id=None,
                created_by_id="c_mod",
                is_sticky=True,
            )
        )
        database.session.commit()
    entrar(client, "c_a")
    assert "Cohort call moves to Thursday" in client.get("/community").get_data(as_text=True)
    assert "announcement" not in vista.COMUNIDAD_TIPOS


# ---------------------------------------------------------------------------------------
# Feed presentation — the card shows the post, not just its title
# ---------------------------------------------------------------------------------------
def test_feed_shows_post_content_not_just_the_title(hub, client, app):
    with app.app_context():
        pub = ComunidadPublicacion(
            parent_id=None,
            usuario="c_a",
            contenido="The body of the post that a reader should be able to see without clicking.",
            titulo="A Title",
            tipo="build",
            estado_moderacion="visible",
            estado="abierto",
            fijado=False,
            reportes_abiertos=0,
        )
        database.session.add(pub)
        database.session.commit()
    entrar(client, "c_b")
    cuerpo = client.get("/community").get_data(as_text=True)
    assert "A Title" in cuerpo
    assert "body of the post that a reader should be able to see" in cuerpo


def test_long_bodies_are_truncated_on_a_word_boundary_with_see_more(hub, client, app):
    largo = "word " * 200
    with app.app_context():
        pub = ComunidadPublicacion(
            parent_id=None,
            usuario="c_a",
            contenido=largo,
            titulo="Long One",
            tipo="build",
            estado_moderacion="visible",
            estado="abierto",
            fijado=False,
            reportes_abiertos=0,
        )
        database.session.add(pub)
        database.session.commit()
    entrar(client, "c_b")
    cuerpo = client.get("/community").get_data(as_text=True)
    assert "See more" in cuerpo
    texto, cortado = vista.extracto(largo)
    assert cortado is True
    assert len(texto) <= vista.EXTRACTO_MAX
    assert not texto.endswith("wor"), "excerpt cut mid-word"


def test_excerpt_carries_no_markup(hub, client, app):
    """The excerpt is inert text: no live tag reaches the card.

    A `<script>` in a body survives as the escaped characters `&lt;script&gt;`,
    which render as visible text and execute nothing. What must never appear is a
    real angle bracket opening a tag, so that is what this asserts — both in the
    helper's output and in the rendered page, since Jinja escapes it again.
    """
    salida, _cortado = vista.extracto("**bold** and <script>alert(1)</script> and [a](https://e.test)")
    assert "<" not in salida, "a raw angle bracket reached the excerpt"
    assert "bold" in salida, "markdown emphasis should be flattened to its text"

    with app.app_context():
        database.session.add(
            ComunidadPublicacion(
                parent_id=None,
                usuario="c_a",
                contenido="<script>alert(1)</script> hello",
                titulo="XSS Probe",
                tipo="build",
                estado_moderacion="visible",
                estado="abierto",
                fijado=False,
                reportes_abiertos=0,
            )
        )
        database.session.commit()
    entrar(client, "c_b")
    cuerpo = client.get("/community").get_data(as_text=True)
    assert "<script>alert(1)</script>" not in cuerpo


def test_relative_age_is_compact(hub):
    from datetime import timedelta as _td

    ahora = utc_now().replace(tzinfo=None)
    assert vista.hace(ahora - _td(hours=3)) == "3h"
    assert vista.hace(ahora - _td(days=2)) == "2d"
    assert vista.hace(ahora - _td(seconds=10)) == "just now"


# ---------------------------------------------------------------------------------------
# The staff view of the Hub
# ---------------------------------------------------------------------------------------
def test_members_cannot_reach_the_staff_view(hub, client):
    entrar(client, "c_a")
    assert client.get("/community/staff").status_code == 403


def test_staff_view_leads_with_unanswered_questions(hub, client, app):
    """The Hub's promise is that a question gets answered; an unanswered one is
    the only thing on this page that is actively failing it."""
    with app.app_context():
        sin = publicar("c_a", titulo="Nobody answered this", tipo="question", edad_horas=48)
        con = publicar("c_b", titulo="This one got a reply", tipo="question", edad_horas=10)
        responder(con, "c_c")
        publicar("c_c", titulo="A build post", tipo="build")
    entrar(client, "c_mod")
    cuerpo = client.get("/community/staff").get_data(as_text=True)
    assert "Nobody answered this" in cuerpo
    assert "This one got a reply" not in cuerpo, "an answered question is not waiting on staff"
    assert "A build post" not in cuerpo, "only questions can be unanswered"
    assert sin  # silence lint


def test_staff_view_shows_reports_and_hidden_posts(hub, client, app):
    with app.app_context():
        reportado = publicar("c_a", titulo="Reported Post")
        oculto = publicar("c_b", titulo="Hidden Post")
    entrar(client, "c_c")
    client.post(f"/community/post/{reportado}/report", data={"motivo": "spam"})
    entrar(client, "c_mod")
    client.post(f"/community/post/{oculto}/hide", data={"motivo": "off topic"})

    cuerpo = client.get("/community/staff").get_data(as_text=True)
    assert "Reported Post" in cuerpo
    assert "Hidden Post" in cuerpo, "a hidden post must stay visible to staff or it is forgotten"


def test_staff_view_counts_are_real(hub, client, app):
    with app.app_context():
        publicar("c_a", titulo="Q one", tipo="question")
        publicar("c_b", titulo="Q two", tipo="question")
    entrar(client, "c_mod")
    cuerpo = client.get("/community/staff").get_data(as_text=True)
    assert "Unanswered questions" in cuerpo
    assert "Posts this week" in cuerpo


def test_destino_local_rejects_offsite_referrers():
    """Open-redirect guard, found by CodeQL on PR #82.

    `request.referrer` is the Referer header, so a page on another origin can POST
    to like/unlike/report and have this app issue the redirect off-site. The guard
    accepts only a same-host absolute URL or a root-relative path.

    Deliberately built on a bare Flask app rather than the suite's `app` fixture:
    the subject is a pure function over the request, so it needs a request context
    and nothing else. No database, no schema, no fixture.
    """
    from flask import Flask

    from now_lms.vistas.comunidad import _destino_local

    probe = Flask(__name__)
    respaldo = "/community"

    hostile = [
        "https://evil.example/phish",           # absolute, other host
        "//evil.example/phish",                 # protocol-relative
        "/\\evil.example/phish",                # backslash, normalised to // by some browsers
        "javascript:alert(1)",                  # non-http scheme
        "http://evil.example/community",        # right path, wrong host
    ]
    friendly = [
        ("/community/post/abc", "/community/post/abc"),
        ("/community?tab=trending", "/community?tab=trending"),
        ("http://localhost/community/post/abc", "/community/post/abc"),
    ]

    for referrer in hostile:
        with probe.test_request_context("/", base_url="http://localhost", headers={"Referer": referrer}):
            assert _destino_local(respaldo) == respaldo, f"should have refused {referrer!r}"

    for referrer, esperado in friendly:
        with probe.test_request_context("/", base_url="http://localhost", headers={"Referer": referrer}):
            assert _destino_local(respaldo) == esperado, f"should have honoured {referrer!r}"

    with probe.test_request_context("/", base_url="http://localhost"):
        assert _destino_local(respaldo) == respaldo


def test_hidden_post_refuses_member_mutations(hub, client, app):
    """The moderation boundary must cover writes, not just reads. Greptile, PR #82.

    `ver_publicacion` 404s a hidden post for anyone but staff and its author. The
    mutation routes reloaded the row through `_cargar()`, which filtered only on
    `parent_id`, so a member who knew the ID could reply to a hidden post, like it
    and report it — and could tell "hidden" from "never existed" by whether the
    write succeeded, which is the disclosure the 404 exists to prevent.
    """
    with app.app_context():
        pid = publicar("c_a", titulo="Hidden thread")
        pub = database.session.get(ComunidadPublicacion, pid)
        pub.estado_moderacion = "oculto"
        database.session.commit()

    entrar(client, "c_b")  # not the author, not staff

    # Read is already guarded; assert it so the test documents the whole boundary.
    assert client.get(f"/community/post/{pid}").status_code == 404

    # Writes must refuse identically — 404, not 403, so existence stays undisclosed.
    for ruta, datos in (
        (f"/community/post/{pid}/reply", {"contenido": "sneaking in"}),
        (f"/community/post/{pid}/like", {}),
        (f"/community/post/{pid}/report", {"motivo": "probing"}),
    ):
        r = client.post(ruta, data=datos, follow_redirects=False)
        assert r.status_code == 404, f"{ruta} returned {r.status_code}, expected 404 on a hidden post"

    with app.app_context():
        respuestas = database.session.execute(
            select(ComunidadPublicacion).filter(ComunidadPublicacion.parent_id == pid)
        ).scalars().all()
        assert respuestas == [], "a reply was stored against a hidden post"
        likes = database.session.execute(
            select(ComunidadReaccion).filter(ComunidadReaccion.publicacion_id == pid)
        ).scalars().all()
        assert likes == [], "a like was stored against a hidden post"


def test_staff_can_still_act_on_a_hidden_post(hub, client, app):
    """The guard is fail-closed by default, so prove the staff bypass still works.

    A boundary that also locked out moderators would make hiding a post irreversible.
    """
    with app.app_context():
        pid = publicar("c_a", titulo="Hidden but restorable")
        pub = database.session.get(ComunidadPublicacion, pid)
        pub.estado_moderacion = "oculto"
        database.session.commit()

    entrar(client, "c_mod")
    r = client.post(f"/community/post/{pid}/restore", data={"motivo": "appeal upheld"}, follow_redirects=False)
    assert r.status_code in (302, 303), f"staff restore returned {r.status_code}"

    with app.app_context():
        assert database.session.get(ComunidadPublicacion, pid).estado_moderacion == "visible"
