# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.

"""``current_locale`` must be called, not referenced, in the theme base templates.

Fork finding B1 (audit 2026-08-07): ``now_lms/templates/themes/intent_learn/base.j2``
lines 2-3 used ``current_locale`` — a Jinja global bound to the ``get_locale``
function (``now_lms/__init__.py``) — without calling it. Live in production
this rendered:

    <!-- DEBUG: current_locale = <function get_locale at 0x789f2ba22e80> -->
    <html lang="<function get_locale at 0x789f2ba22e80>" class="h-100">

Three consequences from one missing pair of parentheses: the stray ``>``
inside the ``lang`` attribute closed the ``<html>`` tag early, so
``" class="h-100">`` rendered as literal visible text at the top of the page;
the ``lang`` attribute was invalid, so screen readers and search engines got
no language; and a Python heap address leaked into public HTML. The identical
defect sat in ``now_lms/templates/themes/now_lms/base.j2`` (upstream's own
base template).

Both custom-page routes that extend this base (``/page/about-us``,
``/page/privacy-policy`` — via ``page_info/custom_page.html`` and
``page_info/contact.html``) are exercised here as a signed-out request, which
is what the audit's live ``curl`` reproduced.
"""

import re

DEBUG_COMMENT = b"<!-- DEBUG: current_locale"
BROKEN_LANG_MARKER = b'lang="<function'


def test_intent_learn_custom_page_has_no_debug_comment_or_broken_lang(client, app):
    from now_lms.db import CustomPage, database

    with app.app_context():
        page = database.session.execute(
            database.select(CustomPage).filter_by(slug="privacy-policy")
        ).scalar_one_or_none()
        if page is None:
            page = CustomPage(
                title="Privacy policy",
                slug="lang-attr-test-page",
                content="<p>Policy content.</p>",
                is_active=True,
            )
            database.session.add(page)
            database.session.commit()
            slug = "lang-attr-test-page"
        else:
            slug = page.slug

    response = client.get(f"/page/{slug}")
    assert response.status_code == 200
    body = response.data

    assert DEBUG_COMMENT not in body, "the DEBUG comment leaked into a live custom page again"
    assert BROKEN_LANG_MARKER not in body, "lang= still carries an unresolved function repr"

    match = re.search(rb'<html[^>]*\blang="([^"]*)"', body)
    assert match is not None, "the <html> tag must carry a lang attribute at all"
    lang_value = match.group(1).decode()
    assert lang_value and not lang_value.startswith("<function"), (
        f"lang attribute is not a real locale code: {lang_value!r}"
    )


def test_contact_page_has_no_debug_comment_or_broken_lang(client, app):
    from now_lms.db import Configuracion, database

    with app.app_context():
        config = database.session.execute(database.select(Configuracion)).scalar_one()
        config.enable_contact = True
        database.session.commit()

    response = client.get("/contact")
    assert response.status_code == 200
    body = response.data
    assert DEBUG_COMMENT not in body
    assert BROKEN_LANG_MARKER not in body
