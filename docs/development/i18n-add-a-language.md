# Adding a new language (i18n)

NOW - LMS is fully internationalized with [Flask-Babel](https://python-babel.github.io/flask-babel/)
and [Babel](https://babel.pocoo.org/). All user-facing strings are wrapped in the translation
helpers from `now_lms/i18n.py` (`_`, `_n`, `_l`), extracted into a message catalog, and translated
per locale. This guide shows how to add a brand-new language as a clean, self-contained
contribution.

The shipped catalogs live under `now_lms/translations/<locale>/LC_MESSAGES/` (currently `es`, `en`,
`pt_BR`). Each locale has a human-edited `messages.po` and a compiled `messages.mo`.

## How the site language is selected (precedence)

`get_locale()` in `now_lms/i18n.py` resolves the active language in this order:

1. **Site configuration (`Configuracion.lang`)** — the value an administrator picks under
   **Settings → General** (`/setting/general`). This is the authoritative, site-wide default. It is
   read from `g.configuracion` first (request-scoped), then directly from the database as a
   fallback.
2. **Browser preference (`Accept-Language`)** — used only when no site configuration is available,
   matched against the supported set `["es", "en", "pt_BR"]`.
3. **Built-in default** — `en` in production, `es` under the test/CI harness.

An administrator changes the site language from the admin settings form
(`ConfigForm.lang`, a select of the supported locales in `now_lms/forms/__init__.py`). After adding a
new language below, add its locale code to that select's `choices` so admins can pick it, and to the
`Accept-Language` match list in `get_locale()` if you want browser auto-detection.

## Prerequisites

Babel ships with the project's dev dependencies. Verify the CLI is available:

```bash
pybabel --version
```

The extraction configuration is `babel.cfg` at the repository root (it points Babel at the Python
sources and the Jinja templates).

## Add a language in three steps

Replace `<locale>` with the target locale code — e.g. `fr` (French), `de` (German), `it` (Italian),
or a region-qualified code such as `fr_CA`.

### 1. Extract the up-to-date message template

Regenerate the `.pot` template so it reflects every current source string:

```bash
pybabel extract -F babel.cfg -o now_lms/translations/messages.pot .
```

### 2. Initialize the new locale catalog

```bash
pybabel init -i now_lms/translations/messages.pot -d now_lms/translations -l <locale>
```

This creates `now_lms/translations/<locale>/LC_MESSAGES/messages.po` with every `msgid` and an empty
`msgstr`. Edit that file and fill in each translation.

> **Placeholder safety.** Every `%(name)s`, `%s`, `%d`, `{variable}`, and HTML tag (`<b>`,
> `<a href="...">`, …) in a `msgid` **must** appear identically in your `msgstr`. A mismatch breaks
> string interpolation at runtime. Leave a `msgstr` empty rather than ship a broken placeholder —
> an empty `msgstr` safely falls back to the source string.

### 3. Compile the catalog

```bash
pybabel compile -d now_lms/translations -l <locale>
```

This produces the binary `messages.mo` that Flask-Babel loads at runtime. Commit **both** the
`.po` (source) and the `.mo` (compiled artifact).

## Wire the language into the UI

To let administrators select the new language:

1. Add the locale to the `lang` select in `now_lms/forms/__init__.py`
   (`ConfigForm.lang` → `choices`), e.g. `("fr", "Français")`.
2. (Optional) Add the locale to the `Accept-Language` match list in `get_locale()`
   (`now_lms/i18n.py`) to enable browser auto-detection.

## Updating an existing language

When source strings change, refresh every catalog from the template and recompile:

```bash
pybabel extract -F babel.cfg -o now_lms/translations/messages.pot .
pybabel update -i now_lms/translations/messages.pot -d now_lms/translations
# edit the changed .po files, then:
pybabel compile -d now_lms/translations
```

`pybabel update` marks changed entries `#, fuzzy`; review and clear those flags after correcting the
translation (`dev/remove_fuzzy_po.py <file.po>` clears fuzzy `msgstr`s in bulk).

## Verify

Run the app, sign in as an administrator, set **Settings → General → Language** to the new locale,
and confirm the UI renders in that language. A quick catalog sanity check:

```bash
pybabel compile -d now_lms/translations -l <locale>   # must compile with no errors
```

A convenience wrapper for the init/compile flow is provided at `dev/add-locale.sh`:

```bash
dev/add-locale.sh fr
```
