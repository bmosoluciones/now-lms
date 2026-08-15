# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""
Regression tests for cache keys that did not identify the user.

`cache_key_with_auth_state()` used to fold every logged-in user into a single "auth"
bucket, so two authenticated users shared one cache entry: whichever request populated
the cache decided what the next user saw. The views using it all render per-user
content - enrolment state, instructor controls, admin listings.

Separately, a number of views used a bare `@cache.cached(timeout=N)`. With
Flask-Caching the default view key is `"view/%s" % request.path` and `query_string`
is False, so those views discriminated neither by user nor by query parameters -
`?page=2` collided with page 1.

These tests exercise the key functions directly. They do not need a real cache backend
(the default is NullCache without REDIS_URL), which is the point: the defect is in key
construction, and that is what is asserted.
"""

from now_lms.auth import proteger_passwd
from now_lms.cache import cache_key_with_auth_state, cache_key_with_query_string
from now_lms.db import Usuario


def _crear_usuario(db_session, usuario: str) -> Usuario:
    user = Usuario(
        usuario=usuario,
        acceso=proteger_passwd(usuario),
        nombre=usuario.title(),
        correo_electronico=f"{usuario}@example.com",
        tipo="student",
        activo=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


def _key_as(app, user=None, path="/course/list", query=""):
    """Build the cache key for `path` as `user` (or anonymously when user is None).

    `logout_user()` is called explicitly for the anonymous case: a `login_user()` from
    an earlier request context in the same test can otherwise still be resolved here,
    which would make an anonymous assertion pass for the wrong reason.
    """
    from flask_login import login_user, logout_user

    with app.test_request_context(path + query):
        if user is not None:
            login_user(user)
        else:
            logout_user()
        return cache_key_with_auth_state()


# --------------------------------------------------------------------------------------
# cache_key_with_auth_state must separate individual users
# --------------------------------------------------------------------------------------


def test_two_authenticated_users_do_not_share_a_cache_key(app, db_session):
    """The headline defect: both users used to key as "auth"."""
    ana = _crear_usuario(db_session, "ana")
    beto = _crear_usuario(db_session, "beto")

    key_ana = _key_as(app, ana)
    key_beto = _key_as(app, beto)

    assert key_ana != key_beto


def test_an_authenticated_user_does_not_share_the_anonymous_key(app, db_session):
    """The property the original function did get right must survive."""
    ana = _crear_usuario(db_session, "ana2")

    assert _key_as(app, ana) != _key_as(app, None)


def test_anonymous_visitors_still_share_one_key(app, db_session):
    """Anonymous requests must stay poolable or the cache stops being worthwhile."""
    assert _key_as(app, None) == _key_as(app, None)


def test_the_same_user_gets_a_stable_key_for_the_same_path(app, db_session):
    """Per-user keys must still hit, not just miss."""
    ana = _crear_usuario(db_session, "ana3")

    assert _key_as(app, ana) == _key_as(app, ana)


def test_paths_remain_distinct_for_one_user(app, db_session):
    ana = _crear_usuario(db_session, "ana4")

    assert _key_as(app, ana, path="/course/list") != _key_as(app, ana, path="/program/list")


def test_query_string_still_participates_in_the_key(app, db_session):
    ana = _crear_usuario(db_session, "ana5")

    assert _key_as(app, ana, query="?page=1") != _key_as(app, ana, query="?page=2")


# --------------------------------------------------------------------------------------
# cache_key_with_query_string: public pages that vary only by query parameters
# --------------------------------------------------------------------------------------


def test_query_string_key_separates_filtered_listings(app):
    """`?tag=x` must not collide with the unfiltered page.

    This is the blog-index defect: the default view key drops the query string.
    """
    with app.test_request_context("/blog?tag=python"):
        con_tag = cache_key_with_query_string()
    with app.test_request_context("/blog"):
        sin_tag = cache_key_with_query_string()

    assert con_tag != sin_tag


def test_query_string_key_is_stable_and_user_independent(app, db_session):
    """A public page must stay poolable across visitors."""
    from flask_login import login_user

    ana = _crear_usuario(db_session, "ana6")

    with app.test_request_context("/blog?tag=python"):
        anonima = cache_key_with_query_string()
    with app.test_request_context("/blog?tag=python"):
        login_user(ana)
        autenticada = cache_key_with_query_string()

    assert anonima == autenticada


# --------------------------------------------------------------------------------------
# The views that used a bare @cache.cached must now carry an identity-aware key
# --------------------------------------------------------------------------------------


def test_auth_gated_views_no_longer_use_the_default_view_key(app):
    """Guard against a bare `@cache.cached(timeout=N)` reappearing on these views.

    Each of these renders content that depends on who is asking; the default key is
    the request path alone. `blog_post` is the per-user case (a comment form is
    rendered for signed-in readers and its CSRF token is per-session); the other
    modules are auth-gated rosters.
    """
    import inspect

    from now_lms.vistas import blog, programs
    from now_lms.vistas.announcements import admin as ann_admin
    from now_lms.vistas.announcements import instructor as ann_instructor
    from now_lms.vistas.profiles import admin as profiles_admin
    from now_lms.vistas.profiles import instructor as profiles_instructor

    modulos = [blog, programs, ann_admin, ann_instructor, profiles_admin, profiles_instructor]
    for modulo in modulos:
        fuente = inspect.getsource(modulo)
        assert "@cache.cached(timeout=60)\n" not in fuente, f"{modulo.__name__} has an unkeyed cached view"
        assert "@cache.cached(timeout=90)\n" not in fuente, f"{modulo.__name__} has an unkeyed cached view"


def test_error_handlers_that_branch_on_the_user_are_not_cached(app):
    """A cached 403 was served to every later visitor and skipped its flash()."""
    import inspect

    import now_lms

    fuente = inspect.getsource(now_lms.inicializa_extenciones_terceros)
    assert "@cache.cached()\n    def error_403" not in fuente
    assert "@cache.cached()\n    def error_404" not in fuente
    assert "@cache.cached()\n    def error_405" not in fuente


# --------------------------------------------------------------------------------------
# blog_post: the comment form (and its CSRF) varies by viewer
# --------------------------------------------------------------------------------------


def _crear_post(db_session, slug: str):
    from now_lms.db import BlogPost, Usuario

    autor = Usuario(
        usuario=f"autor_{slug}",
        acceso=proteger_passwd("password123"),
        nombre="Autor",
        correo_electronico=f"autor_{slug}@example.com",
        tipo="instructor",
        activo=True,
    )
    db_session.add(autor)
    db_session.commit()

    post = BlogPost(
        title=f"Post {slug}",
        slug=slug,
        content="contenido",
        author_id=autor.usuario,
        status="published",
        allow_comments=True,
    )
    db_session.add(post)
    db_session.commit()
    return post


def test_blog_post_cache_key_differs_per_user(app, db_session):
    """`blog_post` used `@cache.cached(timeout=60)` with the default path-only key.
    The page renders a `BlogCommentForm` (with a per-session CSRF) for signed-in
    readers, so two users with different session cookies must never share a
    cache entry.
    """
    from flask_login import login_user, logout_user

    ana = _crear_usuario(db_session, "ana_blog")
    _crear_post(db_session, "post-llaves")

    with app.test_request_context("/blog/post-llaves"):
        login_user(ana)
        autenticada = cache_key_with_auth_state()

    with app.test_request_context("/blog/post-llaves"):
        logout_user()
        anonima = cache_key_with_auth_state()

    assert autenticada != anonima


def test_blog_post_does_not_use_a_bare_cached_decorator(app):
    """Regression guard: `blog_post` must declare a `key_prefix` so the cache
    cannot replay one viewer's comment form to another.
    """
    import inspect

    from now_lms.vistas import blog

    fuente = inspect.getsource(blog)
    assert "@cache.cached(timeout=60)\n" not in fuente
    assert "cache_key_with_auth_state" in fuente
