# Static Pages (Theme-defined)

Static pages are Jinja2 template files defined within a theme. They are served directly from the filesystem without database storage. This makes them ideal for theme designers to create pages like `/equipo`, `/mision_vision`, or `/servicios` that don't need to read data from the database.

## Creating a Static Page

1. Create a `.j2` template file in your theme's `static_pages/` directory:
   ```
   templates/themes/your_theme/static_pages/<page_name>.j2
   ```

2. Access the page at: `/static/<page_name>`

### Example Template

```jinja2
<!-- templates/themes/mytheme/static_pages/equipo.j2 -->
{% set current_theme = current_theme() %}
<!doctype html>
<html lang="es">
    <head>
        {{ current_theme.headertags() }}
        {{ current_theme.local_style() }}
        <title>Equipo - {{ config().titulo }}</title>
    </head>
    <body>
        {{ current_theme.navbar() }}

        <div class="container py-5">
            <h1>Nuestro Equipo</h1>
            <p>Conoce a los miembros de nuestro equipo.</p>
        </div>

        {{ current_theme.jslibs() }}
    </body>
</html>
```

3. The page is accessible at: `/static/equipo`

## Security

- Page names are validated to prevent path traversal (rejects `/`, `\`, `.`, `$`)
- If the template file does not exist, the user is redirected to `/`
- Pages are cached for 180 seconds for performance

## Differences from Custom Pages

| Feature | Static Pages | Custom Pages |
|---------|-------------|--------------|
| Storage | Filesystem (.j2 templates) | Database |
| Management | Theme developers (code) | Admins (UI) |
| Route | `/static/<page>` | `/page/<slug>` |
| Data access | Template context only | Database queries |
| Suitable for | Team pages, mission/vision | About Us, Privacy Policy |

## Architecture

- **Route**: `/static/<page>` in `now_lms/vistas/home.py`
- **Template location**: `templates/themes/<theme>/static_pages/<page>.j2`
- **No database model** — pure filesystem
