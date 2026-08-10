# SPDX-License-Identifier: Apache-2.0
"""The cache key must be invalidatable. Greptile, PR #78.

`cache.delete()` takes one exact key and no supported backend offers portable
pattern deletion, so any key family the invalidator cannot enumerate is a family
it can never clear. Two separate defects came out of that:

  * `/course/<code>/view` reads no query args, yet its key carried the query
    string, so `.../view/user:someone?tab=details` survived every course edit.
    It is also a cache-busting vector: any visitor can mint unlimited entries.
  * `/course/explore`, `/program/explore` and `/` genuinely do vary by query, so
    their keys cannot be enumerated at all. They carry a generation instead.

These tests exercise the real key builder, not a copy of its rules.
"""

from __future__ import annotations

from flask import Flask
from flask_login import LoginManager

import pytest

from now_lms.cache import bump_generacion, cache, cache_key_with_auth_state


@pytest.fixture()
def probe():
    """A bare Flask app with a real in-process cache.

    Deliberately not the suite's `app` fixture: the subject is the key builder and
    the generation counter, which need a request context and a working cache and
    nothing else. No database, no schema.
    """
    aplicacion = Flask(__name__)
    aplicacion.config["CACHE_TYPE"] = "SimpleCache"
    aplicacion.config["SECRET_KEY"] = "probe"
    # The key builder reads current_user, so flask-login has to be attached.
    # Nobody signs in here: every request is anonymous, which is the branch
    # these tests exercise.
    gestor = LoginManager()
    gestor.user_loader(lambda _id: None)  # nobody is signed in; anonymous is the branch under test
    gestor.init_app(aplicacion)
    cache.init_app(aplicacion)
    with aplicacion.app_context():
        cache.clear()
        yield aplicacion


def _clave(aplicacion, path: str, query: str = "") -> str:
    with aplicacion.test_request_context(path + (f"?{query}" if query else "")):
        return cache_key_with_auth_state()


def test_bumping_a_course_scope_retires_its_query_variants(probe):
    """The reported case: `.../view/user:someone?tab=details` must become reachable.

    The query string stays in the key — collapsing it would serve one page's output
    for another, and eleven cached routes genuinely read args. What changes is that
    the key carries a generation, so one bump retires every variant of that course.
    """
    antes = _clave(probe, "/course/CCA-F/view", "tab=details")

    with probe.app_context():
        bump_generacion("curso:CCA-F")

    assert _clave(probe, "/course/CCA-F/view", "tab=details") != antes, (
        "bumping the course scope did not retire the ?tab=details variant"
    )


def test_a_course_bump_does_not_dump_another_course(probe):
    """Scopes are per course, so editing one must not evict every other course."""
    otro = _clave(probe, "/course/CCA-B/view")
    with probe.app_context():
        bump_generacion("curso:CCA-F")
    assert _clave(probe, "/course/CCA-B/view") == otro, "a bump leaked across course scopes"


def test_catalogue_key_still_varies_by_query(probe):
    """The catalogue reads page/nivel/tag/category, so its key must keep them.

    Collapsing these would be a worse bug than the one being fixed: filtered and
    unfiltered pages would serve each other's cached output.
    """
    a = _clave(probe, "/course/explore", "nivel=1")
    b = _clave(probe, "/course/explore", "nivel=3")
    assert a != b, "catalogue filters must remain distinct cache entries"

    # And the general contract the existing suite relies on: any two query strings
    # are two keys, on any path. Breaking this served one page's cache for another.
    p1 = _clave(probe, "/course/list", "page=1")
    p2 = _clave(probe, "/course/list", "page=2")
    assert p1 != p2, "pagination must remain distinct on every path, not just the catalogue"


def test_bumping_the_generation_retires_every_catalogue_variant(probe):
    """One write must make all prior variants unreachable, whatever query made them."""
    antes_a = _clave(probe, "/course/explore", "nivel=1")
    antes_b = _clave(probe, "/course/explore", "page=2")

    with probe.app_context():
        bump_generacion("global")

    despues_a = _clave(probe, "/course/explore", "nivel=1")
    despues_b = _clave(probe, "/course/explore", "page=2")

    assert despues_a != antes_a, "bumping the generation did not retire the nivel=1 variant"
    assert despues_b != antes_b, "bumping the generation did not retire the page=2 variant"
    assert despues_a != despues_b, "the generation must not collapse distinct queries"
