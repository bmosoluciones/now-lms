# Sakura Theme

A delicate, spring-inspired theme for NOW LMS featuring the beautiful Sakura (cherry blossom) color palette with elegant and soft visual design.

## Features

- **Sakura-inspired Color Palette**: Soft pinks and earth tones inspired by Japanese cherry blossoms
- **Elegant Typography**: Recommended serif fonts for headers with clean sans-serif for body text
- **Subtle Animations**: Gentle hover effects and smooth transitions throughout
- **Enhanced Visual Design**: Modern gradients, rounded corners, and sophisticated styling
- **Responsive Design**: Optimized for all screen sizes
- **Professional Appeal**: Perfect for educational, cultural, or artistic projects

## Color Scheme

| Variable CSS | Color | Description |
|---|---|---|
| `--sakura-primary` | `#e89cae` | Rosa Sakura — Base principal |
| `--sakura-secondary` | `#5c3c47` | Ciruela Profundo — Contraste |
| `--sakura-accent` | `#f4c2c2` | Rosa Pastel — Acentos suaves |
| `--sakura-light` | `#fef6f8` | Niebla Rosa — Fondo claro |
| `--sakura-background` | `#fffafb` | Blanco Cerezo — Fondo base |
| `--sakura-surface` | `#ffffff` | Blanco puro — Superficies |
| `--sakura-border` | `#d8a1b0` | Rosa Palo — Bordes |
| `--sakura-text` | `#5c3c47` | Ciruela Profundo — Texto base |
| `--sakura-text-secondary` | `#b58a99` | Malva Empolvado — Texto leve |
| `--sakura-sage` | `#e7d9dc` | Gris Rosado Claro — Fondo suave |
| `--sakura-blue` | `#8aa1b1` | Azul Lluvia — Contraste fresco |

## Feedback Colors (Alerts)

| Usage | Variable CSS | Color | Description |
|---|---|---|---|
| Success | `--sakura-success` | `#a3c9a8` | Verde Matcha — Confirmaciones |
| Warning | `--sakura-warning` | `#f2b5a0` | Melocotón — Alertas suaves |
| Danger/Error | `--sakura-danger` | `#c97c7c` | Rojo Rosado — Errores |
| Information | `--sakura-info` | `#8aa1b1` | Azul Lluvia — Notificaciones |

## Typography Suggestions

- **Headers**: "Cormorant Garamond", "Noto Serif JP", "EB Garamond", or "Georgia", serif
- **Body Text**: "Open Sans", "Noto Sans JP", "Segoe UI", "Roboto", sans-serif

## Visual Enhancements

- Gradient backgrounds with soft sakura tones
- Smooth hover transitions and animations
- Enhanced modal dialogs with backdrop blur effects
- Professional card layouts with subtle shadows
- Modern button styling with gradient effects
- Elegant form controls with rounded borders

## Theme Structure

```
sakura/
├── base.j2
├── header.j2          # Custom headers with sakura theme colors
├── local_style.j2     # References the sakura CSS theme
├── navbar.j2          # Sakura-themed navbar with gradients
├── notify.j2          # Notification templates
├── pagination.j2      # Pagination templates
├── js.j2              # JavaScript includes
├── footer.j2          # Footer component
├── theme.yml          # Theme metadata (required for validation)
├── overrides/         # Template overrides directory (optional)
│   ├── home.j2        # Custom home page
│   ├── course_view.j2 # Custom course view page
│   ├── course_take.j2 # Custom course taking page (enrolled student)
│   ├── resource_list.j2   # Custom resource listing page
│   └── resource_view.j2   # Custom resource detail page
└── README.md
```

## Design Philosophy

- **Light & Delicate**: Inspired by the ephemeral beauty of cherry blossoms
- **Harmonious**: Balanced color relationships creating visual harmony
- **Professional**: Suitable for educational, cultural, and artistic projects
- **Accessible**: Maintains good contrast ratios for readability
- **Elegant**: Sophisticated typography and spacing choices

## Requirements

The NOW LMS frontend requires Bootstrap 5, so include those resources in your header:

```html
<head>
    <!-- Bootstrap core CSS -->
    <link rel="stylesheet" href="/static/node_modules/bootstrap/dist/css/bootstrap.css" />
    <script src="/static/node_modules/bootstrap/dist/js/bootstrap.bundle.js"></script>

    <!-- Bootstrap Font -->
    <link rel="stylesheet" href="/static/node_modules/bootstrap-icons/font/bootstrap-icons.css" />
</head>
```

This theme provides a refined, aesthetic upgrade while maintaining the full functionality and structure of the default NOW LMS interface.

## Aesthetic Appeal

Perfect for:
- Educational institutions with a focus on arts and humanities
- Cultural organizations and museums
- Literary and creative writing platforms
- Wellness and mindfulness learning environments
- Any platform seeking a warm, inviting, and sophisticated appearance
