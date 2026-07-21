# Intent Solutions Learn theme

The live front door for `learn.intentsolutions.io`. This theme overrides only the
**home page** (`overrides/home.j2`) with a fully custom, self-contained landing page —
hero, proof strip, six curriculum-track cards, a "who teaches" band, and a final CTA.
Every other page (login, course catalog, admin, etc.) still renders through the
standard Bootstrap 5 chrome (`base.j2` / `navbar.j2` / `footer.j2` copied verbatim from
the built-in `now_lms` theme) so the rest of the app keeps working unmodified.

## Design language

Transferred from Max's hub theme (`learn-intent-solutions-hub/public/theme.css`):
a warm near-black ground (`#18171b`), orange accent (`#f97316`), elevated-darker
cards, and a three-font system — Syne (display), Inter (body), JetBrains Mono
(labels/eyebrows). Fonts load from Google Fonts (see `header.j2`) so the real Syne
renders in production, not a system-font fallback.

## Theme structure

```
intent_learn/
├── base.j2          -> Base template (copied from now_lms, unmodified)
├── footer.j2         -> Default site footer (copied from now_lms, unmodified)
├── header.j2         -> headertags() — Intent Solutions favicon, Google Fonts, theme-color
├── js.j2              -> JS includes (copied from now_lms, unmodified)
├── local_style.j2    -> Links static/themes/intent_learn/theme.{css,min.css}
├── navbar.j2          -> Standard Bootstrap navbar (copied from now_lms, unmodified)
├── notify.j2          -> Flash-message markup (copied from now_lms, unmodified)
├── pagination.j2      -> Pagination markup (copied from now_lms, unmodified)
└── overrides/
    └── home.j2         -> The branded landing page (this is the actual front door)
```

Static assets: `static/themes/intent_learn/{theme.css,theme.min.css,favicon.svg}`.
`favicon.svg` is the real Intent Solutions mark and auto-flips black/white via
`prefers-color-scheme`.

## CTA wiring

The landing page's calls to action point at real routes, not placeholders:

| CTA | Anonymous visitor | Signed-in user |
| --- | --- | --- |
| Header "Sign in" / "Start learning" | `user.inicio_sesion` / `course.lista_cursos` | `home.panel` (dashboard) |
| Hero row | `user.inicio_sesion` | `home.panel` |
| Final section | `course.lista_cursos` | `home.panel` |

In-page anchors (`#curriculum`, `#teaching`, `#why`) are intentional scroll targets
within the same page, not dead links.

## Activating this theme

Set the `theme` column of the single row in the `style` table to `intent_learn`
(admin UI: **Settings → Appearance**, or directly via the app's `Style` model).
`now_lms.themes.list_themes()` discovers this directory automatically — no other
registration is required.
