# Amber Theme A warm, autumn-inspired theme for NOW LMS featuring the golden tones of amber and the earthy colors of fall. This
theme provides a cozy, traditional atmosphere perfect for educational institutions seeking a welcoming and sophisticated look.
## 🍂 Color Palette The amber theme draws inspiration from autumn colors, featuring warm golds, rich browns, and soft cream
tones that create an inviting educational environment. - Primary: #c97c10 (Amber Dorado) - Secondary: #5c3d21 (Marrón Corteza)
- Accent: #f1c27d (Miel Clara) - Light: #fff8ef (Vainilla Suave) - Background: #fdf6e4 (Marfil Cálido) - Surface: #ffffff
(Blanco puro) - Border: #ddb892 (Beige Arena) - Text: #3e2c20 (Marrón Tierra) - Text Secondary: #82654d (Cobre Grisáceo) -
Blush: #f4e2d8 (Rosa Ámbar Suave) ## Feedback Colors - Success: #6c9a8b (Verde Salvia) - Warning: #e4a11b (Mostaza Ámbar) -
Danger: #a03e3e (Rojo Terracota) - Info: #7c8d99 (Azul Opaco) ## Features - **Warm Autumn Palette**: Inspired by amber, gold,
and earthy tones - **Academic Navbar**: Professional styling with warm amber colors - **Traditional Button Styles**: Warm color
schemes suitable for education - **Cozy Card Design**: Inviting styling with soft enhancements - **Educational Icons**:
Bootstrap icons with amber theming - **Responsive Design**: Optimized for all screen sizes - **Accessibility Focused**: High
contrast and clear typography - **Elegant Typography**: Warm, readable font choices ## Structure ``` amber/ ├── base.j2 ├──
header.j2 -> Custom js and css files to include in the head of all pages ├── local_style.j2 -> Link to amber theme CSS ├──
navbar.j2 -> Custom navbar with amber styling ├── notify.j2 -> Custom notification styling ├── pagination.j2 -> Custom
pagination styling ├── js.j2 -> Custom JS includes └── overrides/ -> Template overrides (if any) ├── course_list.j2 ├──
course_view.j2 ├── home.j2 ├── program_list.j2 └── program_view.j2 ``` ## Visual Enhancements - Warm, inviting autumn styling -
Gentle hover effects with amber transitions - Cozy modal dialogs - Traditional form styling with amber accents - Elegant card
layouts - Soft, warm shadow effects ## Requirements The NOW - LMS frontend requires Bootstrap 5, so include those resources in
your header: ```html
<head>
    <!-- Bootstrap core CSS -->
    <link rel="stylesheet" href="/static/node_modules/bootstrap/dist/css/bootstrap.css" />
    <script src="/static/node_modules/bootstrap/dist/js/bootstrap.bundle.js"></script>

    <!-- Bootstrap Font -->
    <link rel="stylesheet" href="/static/node_modules/bootstrap-icons/font/bootstrap-icons.css" />
</head>
``` This theme provides a warm, traditional educational experience that evokes the comfort and wisdom of classic academic
institutions while maintaining the functionality and structure of the default NOW LMS interface.
