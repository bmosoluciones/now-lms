---
draft: false
date: 2026-07-26
slug: page-refactoring-breaking-changes
authors:
  - admin
categories:
  - Breaking Changes
  - Migration Guide
---

# Page Refactoring: Breaking Changes and Migration Guide

The page management system has been refactored to fix an inverted nomenclature. This introduces breaking changes that require manual migration of themes and database.

<!-- more -->

## Background

Previously, the naming was inverted:
- **Database-driven admin pages** were called `static_pages`
- **Filesystem theme templates** were called `custom_pages`

This caused confusion. The refactoring corrects it:
- **Database-driven admin pages** → `custom_pages` (route: `/page/<slug>`)
- **Filesystem theme templates** → `static_pages` (route: `/static/<page>`)

## What breaks

### Database

- Table `static_pages` renamed to `custom_pages`
- Alembic migration `20260726_000000_rename_static_pages_to_custom_pages.py` renames the table only
- Does **not** update templates, URLs, or custom themes
- `StaticPage` model renamed to `CustomPage`

### Routes

- Admin-managed pages: `/static/<slug>` → `/page/<slug>`
- Theme-defined pages: new route `/static/<page>`
- Contact endpoint: `static_pages.contact` → `contact.contact_form`

### Python API

- `get_footer_pages()` → `get_custom_pages()`
- `StaticPageFooterForm` → `CustomPageFooterForm`
- Blueprint `static_pages` split into `custom_pages`, `contact`, `footer_links`

### Templates

- `admin/static_pages.html` → `admin/custom_pages.html`
- `admin/edit_static_page.html` → `admin/edit_custom_page.html`
- `page_info/static_page.html` → `page_info/custom_page.html`

### Theme directories

- `templates/themes/<theme>/custom_pages/` → `templates/themes/<theme>/static_pages/`

### Theme templates

Every theme footer and navbar must update:
- `get_footer_pages()` → `get_custom_pages()`
- `static_pages.view_page` → `custom_pages.view_page`
- `static_pages.contact` → `contact.contact_form`

Old themes using previous function names or endpoints will fail at runtime with Jinja `UndefinedError` or `BuildError`.

## Migration steps

1. Put the application in maintenance mode
2. Back up both databases and all theme directories
3. Update the source checkout to the latest commit
4. Run `flask db upgrade` (or `alembic upgrade head`)
5. Rename theme `custom_pages/` directories to `static_pages/`
6. Update theme footer/navbar templates for new endpoints and helpers
7. Clear application and Redis caches
8. Restart application services
9. Verify: home, navbar, footer, `/page/<slug>`, `/static/<page>`, `/contact`, blog, courses, admin custom-page CRUD
10. Check logs for `BuildError`, `UndefinedError`, migration errors, missing-template errors

## Verification checklist

- [ ] `alembic upgrade head` completes without errors
- [ ] Home page renders correctly
- [ ] Navbar and footer render without `BuildError` or `UndefinedError`
- [ ] `/page/<slug>` loads admin-managed pages
- [ ] `/static/<page>` loads theme-defined pages
- [ ] `/contact` form submits successfully
- [ ] Blog pages load correctly
- [ ] Course and resource pages render without errors
- [ ] Admin custom-page CRUD works (create, edit, activate/deactivate, delete)
- [ ] No `UndefinedError` or `BuildError` in application logs

## Affected themes

Any theme with a `custom_pages/` directory or templates referencing `get_footer_pages()`, `static_pages.view_page`, or `static_pages.contact` must be updated.

For BMO Soluciones and Sunshine English themes, backups already exist. The safe sequence is:

backup → migrate database → adapt themes → clear cache → restart → verify
