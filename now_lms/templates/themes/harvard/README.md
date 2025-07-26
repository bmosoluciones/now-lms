# Harvard Academic Theme Inspired by the elegance and traditional academic atmosphere of Harvard University. This theme
embodies institutional sophistication with a classic burgundy color scheme. ## Features - Classic academic design inspired by
Harvard - Professional burgundy and neutral color palette - Traditional typography with modern readability - Clean navbar
without icons for focused learning - Elegant forms and components - Fully responsive layout ## Color Palette - **Rojo
Harvard**: #A41034 - Main navbar and primary elements - **Gris Humo Claro**: #F5F3F2 - Main background - **Gris Piedra**:
#C9C1BD - Borders and subtle elements - **Gris Oxford**: #474340 - Primary text - **Beige Académico**: #E8DCC8 - Soft accents
and secondary backgrounds - **Marrón Corteza**: #7A5E49 - Links and interactive elements - **Dorado Pergamino**: #D8B866 -
Special highlights and badges ## Typography - **Titles**: "Merriweather" or "Playfair Display" - Classic with character -
**Body Text**: "Source Sans Pro" - Clean and modern with excellent readability ## Components - Clean navigation bar with no
icons - Academic-styled cards and forms - Traditional color schemes for buttons and alerts - Professional table styling -
Elegant modal designs - Classic pagination controls ## Design Philosophy This theme emphasizes: - Academic tradition and
elegance - Readable typography suitable for long-form content - Professional appearance for educational institutions - Timeless
design that conveys authority and trust ## Theme Structure ``` harvard/ ├── base.j2 # Base template structure ├── header.j2 #
HTML head tags and metadata ├── home.j2 # [OPTIONAL] Custom home page ├── js.j2 # JavaScript libraries and scripts ├──
local_style.j2 # Theme-specific CSS styles ├── navbar.j2 # Navigation bar component ├── notify.j2 # Notification/alert
components ├── pagination.j2 # Pagination controls └── README.md # Theme documentation ``` Note that NOW LMS frontend requires
Bootstrap 5, so include those resources in your header: ```html
<head>
    <!-- Bootstrap core CSS -->
    <link rel="stylesheet" href="/static/node_modules/bootstrap/dist/css/bootstrap.css" />
    <script src="/static/node_modules/bootstrap/dist/js/bootstrap.bundle.js"></script>

    <!-- Bootstrap Font -->
    <link rel="stylesheet" href="/static/node_modules/bootstrap-icons/font/bootstrap-icons.css" />
</head>
```
