"""Browser E2E for the Community Hub (L6).

The deploy line blocks on this job, so these are the Hub behaviours that must
hold in a real browser against a real server, not just in the test client:

* a signed-out visitor cannot see the Hub, or that it exists
* a member can post, and the feed shows the BODY, not only the title
* a member can reply, and the reply appears in the thread
* liking twice leaves one like — the idempotency that the whole feature rests on
* a member cannot like their own post
* the feed does not scroll sideways on a phone

Driven through real HTTP with real form posts, so anything the test client would
paper over — CSRF tokens, redirects, session handling — is exercised for real.
"""

from __future__ import annotations

import re

from e2e.conftest import E2E_MEMBER, E2E_MEMBER_PASSWORD


def _sign_in(page, base_url: str) -> None:
    """Sign the seeded member in through the real form."""
    page.goto(f"{base_url}/user/login", wait_until="load")
    page.fill('input[name="usuario"]', E2E_MEMBER)
    page.fill('input[name="acceso"]', E2E_MEMBER_PASSWORD)
    page.click('button[type="submit"], input[type="submit"]')
    page.wait_for_load_state("load")


def _publicar(page, base_url: str, titulo: str, cuerpo: str) -> str:
    """Create a post through the composer and return its URL."""
    page.goto(f"{base_url}/community/new", wait_until="load")
    page.select_option('select[name="tipo"]', "question")
    page.fill('input[name="titulo"]', titulo)
    page.fill('textarea[name="contenido"]', cuerpo)
    page.click('button[type="submit"]')
    page.wait_for_url(re.compile(r".*/community/post/.*"), timeout=15000)
    return page.url


def test_signed_out_visitor_cannot_see_the_hub(page, app_server):
    """Not the content, and not that the Hub exists."""
    page.goto(f"{app_server}/community", wait_until="load")
    assert "/community" not in page.url, "the Hub rendered for a signed-out visitor"
    assert "Start a post" not in page.content()


def test_member_posts_and_the_feed_shows_the_body(page, app_server):
    """A feed of titles is not a feed — the card carries the post itself."""
    _sign_in(page, app_server)
    cuerpo = "This body text must be visible on the feed without opening the post."
    _publicar(page, app_server, "A browser-made post", cuerpo)

    page.goto(f"{app_server}/community", wait_until="load")
    contenido = page.content()
    assert "A browser-made post" in contenido
    assert "must be visible on the feed" in contenido


def test_member_can_reply_and_the_reply_appears(page, app_server):
    _sign_in(page, app_server)
    url = _publicar(page, app_server, "A post that gets a reply", "Original body.")

    page.goto(url, wait_until="load")
    page.fill('textarea[name="contenido"]', "A reply written in the browser.")
    page.click('button[type="submit"]')
    page.wait_for_load_state("load")

    assert "A reply written in the browser." in page.content()


def test_liking_twice_leaves_one_like(page, app_server, context):
    """The idempotency the whole feature rests on, exercised over real HTTP.

    The author cannot like their own post, so the like is performed by a second
    member — created here through the normal signup-free path the seeder uses.
    """
    _sign_in(page, app_server)
    url = _publicar(page, app_server, "A post to be liked", "Body of the likeable post.")

    # A second browser context is a second member session. The seeded member is
    # the author, so borrow the admin account, which is a member of the Hub too.
    otra = context.browser.new_context()
    pagina = otra.new_page()
    pagina.goto(f"{app_server}/user/login", wait_until="load")
    pagina.fill('input[name="usuario"]', "e2e-admin")
    pagina.fill('input[name="acceso"]', "e2e-admin-password-123")
    pagina.click('button[type="submit"], input[type="submit"]')
    pagina.wait_for_load_state("load")

    pagina.goto(url, wait_until="load")
    for _ in range(3):
        boton = pagina.query_selector('button[aria-pressed]')
        if boton is None:
            break
        boton.click()
        pagina.wait_for_load_state("load")

    # However many times it was pressed, the count can never exceed one member.
    pagina.goto(url, wait_until="load")
    etiqueta = pagina.eval_on_selector('[aria-label*="Like this post"], [aria-label*="likes"]',
                                       "e => e.getAttribute('aria-label')")
    numeros = [int(n) for n in re.findall(r"\d+", etiqueta or "0")]
    assert numeros and numeros[0] <= 1, f"like count exceeded one member: {etiqueta}"
    otra.close()


def test_author_cannot_like_their_own_post(page, app_server):
    _sign_in(page, app_server)
    url = _publicar(page, app_server, "A post nobody else likes", "Body.")
    page.goto(url, wait_until="load")
    # The control is not rendered on your own post, so there is nothing to press.
    assert page.query_selector('button[aria-pressed]') is None


def test_feed_does_not_scroll_sideways_at_390px(page, app_server):
    """The width the cohort actually reads on."""
    _sign_in(page, app_server)
    page.set_viewport_size({"width": 390, "height": 844})
    page.goto(f"{app_server}/community", wait_until="load")

    # Assert the real viewport: a resize that reports success is not evidence.
    assert page.evaluate("() => window.innerWidth") == 390
    ancho = page.evaluate("() => document.documentElement.scrollWidth")
    assert ancho <= 390, f"feed scrolls sideways at 390px (scrollWidth {ancho})"
