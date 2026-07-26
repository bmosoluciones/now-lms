# Custom Pages

Custom pages are admin-managed content pages stored in the database. They allow administrators to create, edit, activate/deactivate, and delete pages like "About Us", "Privacy Policy", or any other content — all from the admin panel without touching code.

## Admin Management

Access custom pages from:
- **Admin Panel** → "Páginas Custom" button in Herramientas de Administración
- **Settings** → Static Content Management → "Gestionar Páginas Custom"

### Creating a Page

1. Go to **Admin Panel** → **Páginas Custom** → **Nueva Página**
2. Fill in:
   - **Título**: Display title (max 200 chars)
   - **Slug**: URL identifier (max 50 chars, must be unique). Example: `about-us`
   - **Contenido (HTML)**: Page content in HTML
   - **Activa**: Toggle public visibility
   - **Mostrar en el footer**: Show in site footer "Acerca de" section
3. Click **Guardar**

The page is accessible at `/page/<slug>` (e.g., `/page/about-us`).

### Editing a Page

Click the pencil icon on any page in the list. You can modify title, slug, content, and settings.

### Activating / Deactivating

Click the green/red toggle badge in the status column to activate or deactivate a page. Inactive pages are not publicly visible.

### Deleting a Page

Click the trash icon and confirm. This action cannot be undone.

## Public URL

Each custom page is accessible at:
```
/page/<slug>
```

## Footer Integration

Pages with "Mostrar en el footer" enabled appear in the site footer under "Acerca de". The footer is controlled by the `enable_footer` configuration setting.

## Architecture

- **Model**: `CustomPage` in `now_lms/db/__init__.py`
- **Blueprint**: `custom_pages` in `now_lms/vistas/custom_pages.py`
- **Template (public)**: `templates/page_info/custom_page.html`
- **Templates (admin)**: `templates/admin/custom_pages.html`, `templates/admin/edit_custom_page.html`
- **Form**: `CustomPageForm` in `now_lms/forms/__init__.py`

## Routes

| Route | Method | Auth | Description |
|-------|--------|------|-------------|
| `/page/<slug>` | GET | Public | View a custom page |
| `/admin/pages` | GET | Admin | List all custom pages |
| `/admin/pages/new` | GET/POST | Admin | Create a new custom page |
| `/admin/pages/<id>/edit` | GET/POST | Admin | Edit a custom page |
| `/admin/pages/<id>/delete` | POST | Admin | Delete a custom page |
| `/admin/pages/<id>/toggle` | POST | Admin | Toggle active status |
