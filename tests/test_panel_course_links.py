# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""
The role panels must not send a signed-in user to the public course catalog.

/course/explore is filtered to `publico` and `estado == "open"` courses for every
visitor, staff included, so a "See All" beside a list of the user's own courses
lands them somewhere that cannot contain those courses.
"""

from html.parser import HTMLParser

import pytest

from now_lms.auth import proteger_passwd
from now_lms.db import Usuario


@pytest.fixture
def instructor_user(app, db_session):
    """An instructor account, the role that renders inicio/panel_instructor.html."""
    instructor = Usuario(
        usuario="panel_links_instructor",
        acceso=proteger_passwd("pass"),
        nombre="Panel",
        apellido="Links",
        correo_electronico="panel_links_instructor@example.com",
        tipo="instructor",
        activo=True,
        correo_electronico_verificado=True,
    )
    db_session.add(instructor)
    db_session.commit()
    return instructor


def login(client, username):
    client.get("/user/logout")
    return client.post("/user/login", data={"usuario": username, "acceso": "pass"})


class _ArrowLinkFinder(HTMLParser):
    """Collect the href of every anchor containing a bi-arrow-right icon.

    Parsed rather than matched with a regex so the assertion survives attribute
    order, added attributes and whitespace changes in the template.
    """

    def __init__(self) -> None:
        super().__init__()
        self.hrefs: list[str] = []
        self._open_anchor: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "a":
            self._open_anchor = attributes.get("href")
        elif tag == "i" and self._open_anchor is not None:
            if "bi-arrow-right" in (attributes.get("class") or "").split():
                self.hrefs.append(self._open_anchor)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a":
            self._open_anchor = None


def _see_all_href(html: str) -> str:
    """Return the href of the panel's single arrow-right ("Ver Todos") anchor."""
    finder = _ArrowLinkFinder()
    finder.feed(html)
    assert finder.hrefs, "the recent-courses card no longer carries an arrow-right link"
    assert len(finder.hrefs) == 1, f"expected one arrow-right link on the panel, found {finder.hrefs}"
    return finder.hrefs[0]


def test_instructor_panel_see_all_reaches_the_instructor_course_list(client, db_session, instructor_user):
    """The card's See All must reach the instructor's own courses, not the public catalog."""
    login(client, "panel_links_instructor")

    response = client.get("/home/panel")
    assert response.status_code == 200

    href = _see_all_href(response.get_data(as_text=True))
    assert href == "/instructor/courses_list", f"See All points at {href}, not the instructor course list"


def test_instructor_can_open_the_course_list_that_see_all_points_at(client, db_session, instructor_user):
    """The destination is reachable by an instructor, not only by an admin."""
    login(client, "panel_links_instructor")

    response = client.get("/instructor/courses_list")
    assert response.status_code == 200
