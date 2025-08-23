# Theming System

NOW LMS includes a flexible theming system that allows you to customize the appearance of your learning management system. This guide explains how to create, customize, and extend themes.

## Overview

The theming system is built using Jinja2 templates and provides a modular approach to styling different aspects of the application. Each theme consists of several components that control different parts of the user interface and can override specific page templates.

## Theme Structure

Each theme is located in the `now_lms/templates/themes/` directory and follows this structure:

```
now_lms/templates/themes/your_theme_name/
├── base.j2              # Base template structure
├── header.j2            # HTML head tags and metadata
├── js.j2                # JavaScript libraries and scripts
├── local_style.j2       # Theme-specific CSS styles (uses url_for)
├── navbar.j2            # Navigation bar component
├── notify.j2            # Notification/alert components
├── pagination.j2        # Pagination controls
├── overrides/           # Template overrides directory (optional)
│   └── home.j2          # Custom home page (most common override)
└── README.md            # Theme documentation
```

### Static Assets

Each theme can include static assets in the `static/themes/` directory:

```
now_lms/static/themes/your_theme_name/
├── theme.css            # Main theme stylesheet
├── theme.min.css        # Minified version for performance
├── images/              # Theme-specific images
├── fonts/               # Custom fonts
├── js/                  # Theme-specific JavaScript
└── videos/              # Theme-specific videos
```

For more details on managing static assets, see the [Static Assets README](https://github.com/bmosoluciones/now-lms/tree/main/now_lms/static/themes).

## Available Themes

NOW LMS comes with 13 built-in themes:

### Base Theme

- **now_lms**: Default theme made with vanilla Bootstrap 5

### Professional Themes

- **corporative**: Professional blue theme for corporate environments
- **finance**: Federal green theme inspired by financial institutions
- **classic**: Minimalist white/gray design with clean typography

### Color Variations

- **amber**: A warm, autumn-inspired theme
- **golden**: A gold-based color theme
- **lime**: A green-based theme
- **nebula**: A purple-based theme
- **ocean**: A blue-based theme
- **sakura**: A cherry blossom-inspired theme

### Academic Themes

Three prestigious academic themes inspired by world-renowned universities:

- **harvard**: Burgundy theme (#A41034) inspired by Harvard University
    - Classic academic design with traditional typography
    - Merriweather/Playfair Display fonts for titles
    - Source Sans Pro for body text
    - Clean navbar without icons
    - Academic highlights and "Veritas" branding

- **cambridge**: Green patina theme (#4A7B6D) inspired by Cambridge University
    - Historic architecture and scholarly heritage design
    - Cormorant Garamond/EB Garamond fonts for titles
    - Open Sans for body text
    - Manuscript-inspired design elements
    - Clean navbar without icons

- **oxford**: Blue-gray theme (#5A5F68) inspired by Oxford University
    - Aristocratic elegance and formal tradition
    - Libre Baskerville fonts for titles
    - Lato/Nunito for body text
    - Sophisticated and refined components
    - Clean navbar without icons

## Creating a Custom Theme

### Step 1: Create Theme Directory

Create a new directory in `now_lms/templates/themes/` with your theme name:

```bash
mkdir now_lms/templates/themes/my_custom_theme
```

### Step 2: Copy Base Files

Start by copying files from an existing theme as a template:

```bash
cp -r now_lms/templates/themes/now_lms/* now_lms/templates/themes/my_custom_theme/
```

### Step 3: Customize Theme Components

#### Header Component (`header.j2`)

Define HTML head tags, meta information, and external resources:

```jinja2
{% macro headertags() -%}
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="description" content="{{ site_config.descripcion }}" />
    <meta name="author" content="NOW LMS" />

    <!-- Bootstrap CSS -->
    <link href="{{ url_for('static', filename='node_modules/bootstrap/dist/css/bootstrap.min.css') }}" rel="stylesheet" />

    <!-- Custom Fonts -->
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet" />

    <!-- Icons -->
    <link rel="stylesheet" href="{{ url_for('static', filename='node_modules/bootstrap-icons/font/bootstrap-icons.css') }}" />
{%- endmacro %}
```

#### Local Styles (`local_style.j2`)

**Note:** For optimal performance, create external CSS files instead of inline styles.

Create your theme CSS file in `static/themes/your_theme_name/theme.css`:

```css
/* Custom Theme Variables */
:root {
    --primary-color: #yourcolor;
    --secondary-color: #yourcolor;
    --accent-color: #yourcolor;
    --background-color: #yourcolor;
    --text-color: #yourcolor;
    --success-color: #yourcolor;
    --warning-color: #yourcolor;
    --danger-color: #yourcolor;
}

/* Your custom CSS styles */
body {
    font-family: "Inter", sans-serif;
    background-color: var(--background-color);
    color: var(--text-color);
}

.navbar-custom {
    background: var(--primary-color) !important;
}

/* Add more custom styles... */
```

Then create a minified version and update your `local_style.j2`:

```jinja2
{% macro local_style() -%}
    <link rel="stylesheet" href="{{ url_for('static', filename='themes/your_theme_name/theme.min.css') }}" />
{% endmacro %}
```

## Template Overrides

The theming system now supports complete page template overrides. You can customize specific pages by creating templates in the `overrides/` directory.

### Supported Override Templates

- **`home.j2`**: Custom home page template
- **`course_list.j2`**: Custom course listing page
- **`course_view.j2`**: Custom individual course page
- **`program_list.j2`**: Custom program listing page
- **`program_view.j2`**: Custom individual program page

### Using the `get_home_template()` Function

The system automatically uses the `get_home_template()` function to determine which template to use:

```python
def get_home_template() -> str:
    """Returns the path to the home page template."""
    THEME = get_current_theme()
    HOME = Path(path.join(get_theme_path(), "overrides", "home.j2"))

    if HOME.exists():
        return THEMES_DIRECTORY + str(THEME) + "/overrides/home.j2"
    else:
        return "inicio/home.html"  # Default template
```

### Template Override Functions

The system includes several template override functions:

- `get_home_template()` - Home page override
- `get_course_list_template()` - Course listing override
- `get_program_list_template()` - Program listing override
- `get_course_view_template()` - Course view override
- `get_program_view_template()` - Program view override

## Custom Pages

Create static custom pages for your theme in the `custom_pages/` directory. These pages can be accessed via `/custom/<page_name>`.

### Creating Custom Pages

1. Create a template in `templates/themes/your_theme/custom_pages/`:

```jinja2
<!-- templates/themes/mytheme/custom_pages/contacto.j2 -->
{% set current_theme = current_theme() %}
<!doctype html>
<html lang="es">
    <head>
        {{ current_theme.headertags() }}
        {{ current_theme.local_style() }}
        <title>Contacto - {{ site_config.nombre }}</title>
    </head>
    <body>
        {{ current_theme.navbar() }}

        <div class="container py-5">
            <h1>Contacto</h1>
            <p>Esta es una página personalizada del tema.</p>
            <!-- Add your custom content here -->
        </div>

        {{ current_theme.jslibs() }}
    </body>
</html>
```

2. Access the page at: `/custom/contacto`

### Custom Page Security

- Page names are validated to contain only alphanumeric characters, underscores, and hyphens
- Only authenticated themes can serve custom pages
- Pages are cached for 180 seconds for performance

## Static Assets Management

### Using `url_for` for Theme Assets

Reference theme-specific static assets using Flask's `url_for`:

```jinja2
<!-- Images -->
<img src="{{ url_for('static', filename='themes/mytheme/images/logo.png') }}" alt="Logo" />

<!-- CSS (additional stylesheets) -->
<link rel="stylesheet" href="{{ url_for('static', filename='themes/mytheme/css/custom.css') }}" />

<!-- JavaScript -->
<script src="{{ url_for('static', filename='themes/mytheme/js/theme.js') }}"></script>

<!-- Fonts -->
<link
    href="{{ url_for('static', filename='themes/mytheme/fonts/custom-font.woff2') }}"
    rel="preload"
    as="font"
    type="font/woff2"
    crossorigin
/>

<!-- Videos -->
<video src="{{ url_for('static', filename='themes/mytheme/videos/intro.mp4') }}" controls></video>
```

For complete examples and best practices, see the [Static Assets README](https://github.com/bmosoluciones/now-lms/tree/main/now_lms/static/themes).
color: var(--text-color);
}

    /* Navigation styles */
    .navbar-custom {
        background-color: var(--primary-color);
    }

    /* Button styles */
    .btn-custom-primary {
        background-color: var(--primary-color);
        border-color: var(--primary-color);
        color: white;
    }

</style>
{%- endmacro %}
```

#### Navigation Bar (`navbar.j2`)

Customize the navigation structure and styling:

```jinja2
{% macro navbar() -%}
    <nav class="navbar navbar-expand-md navbar-custom" aria-label="Custom navbar">
        <div class="container-fluid">
            <!-- Logo and brand -->
            <a href="{{ url_for('home.pagina_de_inicio') }}" class="navbar-brand">
                {% if logo_perzonalizado() %}
                    <img height="30" src="{{ url_for('static', filename='/files/public/images/logotipo.jpg') }}" alt="LMS" />
                {% else %}
                    <img
                        height="30"
                        src="{{ url_for('static', filename='/icons/logo/logo_white_large.png') }}"
                        alt="NOW LMS"
                    />
                {% endif %}
            </a>

            <!-- Navigation links -->
            <div class="collapse navbar-collapse">
                <ul class="navbar-nav me-auto">
                    <li class="nav-item">
                        <a href="{{ url_for('home.pagina_de_inicio') }}" class="nav-link">Home</a>
                    </li>
                    <!-- Add more navigation items -->
                </ul>
            </div>
        </div>
    </nav>
{%- endmacro %}
```

### Step 4: JavaScript Libraries (`js.j2`)

Include JavaScript dependencies and custom scripts:

```jinja2
{% macro jslibs() -%}
    <script src="{{ url_for('static', filename='node_modules/bootstrap/dist/js/bootstrap.bundle.min.js') }}"></script>

    <!-- Custom JavaScript for your theme -->
    <script>
        // Your custom JavaScript code
        document.addEventListener("DOMContentLoaded", function () {
            // Theme-specific initialization
        })
    </script>
{%- endmacro %}
```

### Step 5: Other Components

- **`notify.j2`**: Customize notification and alert styling
- **`pagination.j2`**: Define pagination controls appearance
- **`base.j2`**: Set up the overall page structure

## Theme Integration

### Using Theme Functions in Templates

All HTML templates should include the theme style call in the `<head>` section:

```html
<!doctype html>
<html lang="es">
    {% set current_theme = current_theme() %}
    <head>
        {{ current_theme.headertags() }} {{ current_theme.local_style() }}
        <title>Page Title</title>
    </head>
    <body>
        {{ current_theme.navbar() }}
        <!-- Page content -->
        {{ current_theme.jslibs() }}
    </body>
</html>
```

### Custom Home Pages

The theming system supports theme-specific home pages through the `get_home_template()` function. This allows you to completely override the default home page with a custom design for your theme.

#### How it works:

```python
def get_home_template() -> str:
    """Returns the path to the home page template."""
    THEME = get_current_theme()

    HOME = Path(path.join(get_theme_path(), "overrides", "home.j2"))

    if HOME.exists():
        return THEMES_DIRECTORY + str(THEME) + "/overrides/home.j2"
    else:
        return "inicio/home.html"
```

If your theme directory contains a `home.j2` file, it will be used instead of the default home page. This gives you complete control over the home page design, layout, and content.

#### Creating a Custom Home Page:

1. Create a `home.j2` file in your theme directory
2. Design your custom home page using your theme's styling
3. Include all necessary theme functions and Bootstrap components
4. The system will automatically use your custom home page when the theme is active

#### Example Custom Home Page Structure:

```html
<!doctype html>
<html lang="es">
    {% set current_theme = current_theme() %}
    <head>
        {{ current_theme.headertags() }} {{ current_theme.local_style() }}
        <title>{{ site_config.nombre }} - Custom Home</title>
    </head>
    <body>
        {{ current_theme.navbar() }}

        <!-- Your custom home page content -->
        <section class="hero-section">
            <!-- Custom hero content -->
        </section>

        <section class="features-section">
            <!-- Custom features content -->
        </section>

        {{ current_theme.jslibs() }}
    </body>
</html>
```

### Static Content and Assets

#### Static Assets Directory

Theme-specific static assets should be placed in the `static/themes/` directory. This allows you to include custom images, CSS files, JavaScript, fonts, and other media specific to your theme.

##### Directory Structure:

```
static/themes/
├── your_theme_name/
│   ├── images/
│   │   ├── logo.png
│   │   ├── background.jpg
│   │   └── hero-banner.png
│   ├── css/
│   │   └── additional.css
│   ├── js/
│   │   └── theme-animations.js
│   ├── fonts/
│   │   └── custom-font.woff2
│   └── videos/
│       └── intro.mp4
```

#### Using `url_for` for Static Assets

Flask's `url_for` function is used to generate URLs for static assets. This ensures proper URL generation regardless of the application's configuration.

##### Examples:

**Images:**

```html
<!-- Theme logo -->
<img src="{{ url_for('static', filename='themes/harvard/images/logo.png') }}" alt="Harvard Logo" />

<!-- Background image -->
<div style="background-image: url('{{ url_for('static', filename='themes/harvard/images/campus-bg.jpg') }}');">
    <!-- Content -->
</div>

<!-- Hero banner -->
<img
    src="{{ url_for('static', filename='themes/cambridge/images/hero-banner.png') }}"
    class="img-fluid"
    alt="Cambridge Banner"
/>
```

**CSS Files:**

```html
<!-- Additional theme-specific CSS -->
<link rel="stylesheet" href="{{ url_for('static', filename='themes/oxford/css/animations.css') }}" />

<!-- Font file -->
<link rel="stylesheet" href="{{ url_for('static', filename='themes/oxford/css/fonts.css') }}" />
```

**JavaScript Files:**

```html
<!-- Theme-specific JavaScript -->
<script src="{{ url_for('static', filename='themes/harvard/js/interactive.js') }}"></script>

<!-- Theme initialization -->
<script src="{{ url_for('static', filename='themes/cambridge/js/cambridge-init.js') }}"></script>
```

**Fonts:**

```css
/* In your theme's CSS */
@font-face {
    font-family: "CustomFont";
    src: url("{{ url_for("static", filename="themes/oxford/fonts/oxford-font.woff2") }}") format("woff2");
}
```

**Videos and Audio:**

```html
<!-- Video background -->
<video autoplay muted loop class="bg-video">
    <source src="{{ url_for('static', filename='themes/harvard/videos/campus-tour.mp4') }}" type="video/mp4" />
</video>

<!-- Audio element -->
<audio controls>
    <source src="{{ url_for('static', filename='themes/cambridge/audio/bell-chime.mp3') }}" type="audio/mpeg" />
</audio>
```

#### Best Practices for Static Assets:

1. **Organization**: Keep assets organized in logical subdirectories
2. **Optimization**: Compress images and minify CSS/JS files
3. **Responsive Images**: Provide multiple sizes for different screens
4. **Accessibility**: Include proper alt text and ARIA labels
5. **Performance**: Use appropriate image formats (WebP, SVG when possible)
6. **Caching**: Static assets are automatically cached by Flask

#### Asset Loading Examples:

**Conditional Asset Loading:**

```html
{% if current_theme_name == 'harvard' %}
<link rel="stylesheet" href="{{ url_for('static', filename='themes/harvard/css/harvard-extras.css') }}" />
{% elif current_theme_name == 'cambridge' %}
<script src="{{ url_for('static', filename='themes/cambridge/js/manuscript-effects.js') }}"></script>
{% endif %}
```

**Dynamic Asset References:**

```html
<!-- Dynamic theme assets -->
<img
    src="{{ url_for('static', filename='themes/' + current_theme_name + '/images/logo.png') }}"
    alt="{{ current_theme_name|title }} Logo"
/>
```

### Available Theme Functions

- `current_theme.headertags()`: HTML head tags and metadata
- `current_theme.local_style()`: Theme CSS styles
- `current_theme.navbar()`: Navigation bar
- `current_theme.notify()`: Notification components
- `current_theme.jslibs()`: JavaScript libraries
- `current_theme.rendizar_paginacion()`: Pagination controls

## Color Scheme Guidelines

### CSS Variables

Use CSS custom properties (variables) for consistent theming:

```css
:root {
    /* Primary colors */
    --primary: #your-primary-color;
    --secondary: #your-secondary-color;
    --accent: #your-accent-color;

    /* Neutral colors */
    --background: #your-background-color;
    --surface: #your-surface-color;
    --text: #your-text-color;
    --text-secondary: #your-secondary-text-color;

    /* State colors */
    --success: #your-success-color;
    --warning: #your-warning-color;
    --danger: #your-danger-color;
    --info: #your-info-color;
}
```

### Bootstrap Integration

NOW LMS uses Bootstrap 5. You can override Bootstrap variables or use custom CSS classes:

```css
/* Override Bootstrap variables */
.btn-primary {
    background-color: var(--primary);
    border-color: var(--primary);
}

/* Custom button class */
.btn-theme-custom {
    background-color: var(--accent);
    color: white;
    border: none;
}
```

## Cache Management

The theming system includes automatic cache invalidation. When you change the active theme:

1. The system detects the theme change
2. Automatically clears the cache if configured
3. Ensures immediate theme updates for all users

## Best Practices

### 1. Consistent Design Language

- Use a consistent color palette throughout your theme
- Maintain proper contrast ratios for accessibility
- Follow responsive design principles

### 2. Performance Optimization

- Minimize CSS and JavaScript file sizes
- Use efficient selectors
- Optimize images and assets

### 3. Accessibility

- Ensure sufficient color contrast (WCAG 2.1 AA standards)
- Include proper ARIA labels
- Test with screen readers

### 4. Testing

- Test your theme across different browsers
- Verify responsive behavior on various screen sizes
- Check all interactive elements

## Troubleshooting

### Theme Not Loading

1. Verify theme directory structure
2. Check file permissions
3. Clear browser cache
4. Restart the application if needed

### Styling Issues

1. Use browser developer tools to debug CSS
2. Check for CSS conflicts with Bootstrap
3. Verify CSS variable definitions

### Cache Issues

- Clear application cache: The system automatically handles this
- Clear browser cache for development
- Check cache configuration in `now_lms/cache.py`

## Advanced Customization

### Custom Components

You can extend themes by adding custom components and including them in your templates.

### Theme Inheritance

Consider creating base themes and extending them for variations, though this requires more advanced template techniques.

### Integration with Frontend Frameworks

For advanced theming, you can integrate with modern frontend build tools and frameworks while maintaining compatibility with the Jinja2 template system.

## Support

For additional help with theming:

1. Check the existing themes for examples
2. Review the application documentation
3. Contact the development team for complex customizations

---

_This documentation covers the essential aspects of the NOW LMS theming system. For specific implementation details, refer to the existing theme files and application code._
