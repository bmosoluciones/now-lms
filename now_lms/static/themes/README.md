# Theme Static Assets

This directory contains static assets (images, videos, audio, CSS, JavaScript) that are specific to themes in the NOW LMS system.

## Directory Structure

Each theme can have its own subdirectory containing static assets:

```
static/themes/
├── theme_name/
│   ├── images/
│   │   ├── logo.png
│   │   ├── background.jpg
│   │   └── hero-banner.png
│   ├── css/
│   │   └── custom.css
│   ├── js/
│   │   └── custom.js
│   ├── fonts/
│   │   └── custom-font.woff2
│   └── videos/
│       └── intro.mp4
```

## Using Static Assets in Theme Templates

To reference static assets in your theme templates, use Flask's `url_for` function:

### Images
```html
<!-- Theme-specific logo -->
<img src="{{ url_for('static', filename='themes/your_theme/images/logo.png') }}" alt="Logo">

<!-- Background image -->
<div style="background-image: url('{{ url_for('static', filename='themes/your_theme/images/background.jpg') }}')">
```

### CSS Files
```html
<!-- Additional theme-specific CSS -->
<link rel="stylesheet" href="{{ url_for('static', filename='themes/your_theme/css/custom.css') }}">
```

### JavaScript Files
```html
<!-- Theme-specific JavaScript -->
<script src="{{ url_for('static', filename='themes/your_theme/js/custom.js') }}"></script>
```

### Videos and Audio
```html
<!-- Video background -->
<video autoplay muted loop>
    <source src="{{ url_for('static', filename='themes/your_theme/videos/intro.mp4') }}" type="video/mp4">
</video>

<!-- Audio element -->
<audio controls>
    <source src="{{ url_for('static', filename='themes/your_theme/audio/notification.mp3') }}" type="audio/mpeg">
</audio>
```

## Custom Fonts
```css
/* In your theme's CSS file */
@font-face {
    font-family: 'CustomFont';
    src: url('{{ url_for('static', filename='themes/your_theme/fonts/custom-font.woff2') }}') format('woff2');
}
```

## Best Practices

1. **Optimize Assets**: Compress images and minify CSS/JS files for better performance
2. **Responsive Images**: Provide multiple sizes for different screen resolutions
3. **Accessibility**: Include proper alt text for images and ensure media is accessible
4. **File Naming**: Use descriptive, lowercase names with hyphens (e.g., `hero-banner.jpg`)
5. **Organization**: Keep assets organized in appropriate subdirectories

## Asset Types Supported

- **Images**: JPG, PNG, SVG, WebP, GIF
- **Videos**: MP4, WebM, OGV
- **Audio**: MP3, OGG, WAV
- **Stylesheets**: CSS files
- **Scripts**: JavaScript files
- **Fonts**: WOFF, WOFF2, TTF, OTF
- **Documents**: PDF files for theme documentation

## Examples

### Hero Section with Background Image
```html
<section class="hero" style="background-image: linear-gradient(rgba(0,0,0,0.5), rgba(0,0,0,0.5)), url('{{ url_for('static', filename='themes/harvard/images/campus-background.jpg') }}');">
    <div class="hero-content">
        <h1>Welcome to Harvard LMS</h1>
        <p>Excellence in Education</p>
    </div>
</section>
```

### Theme Logo in Navbar
```html
<a class="navbar-brand" href="{{ url_for('home.pagina_de_inicio') }}">
    <img src="{{ url_for('static', filename='themes/cambridge/images/cambridge-logo.png') }}" 
         alt="Cambridge LMS" height="40">
</a>
```

### Custom JavaScript for Theme Interactivity
```html
<script src="{{ url_for('static', filename='themes/oxford/js/oxford-animations.js') }}"></script>
```

## Security Notes

- Only upload trusted assets from verified sources
- Avoid executable files (.exe, .sh, .bat)
- Keep file sizes reasonable to maintain performance
- Use HTTPS for any external asset references

For more information about theming, refer to the main theming documentation.