# Ocean Blue Theme A modern, professional theme for NOW LMS featuring a beautiful blue/teal color palette with enhanced visual
design. ## Features - **Ocean-inspired Color Palette**: Professional blue and teal gradient combinations - **Modern Gradient
Navbar**: Stunning gradient background with smooth hover effects - **Custom Button Styles**: Rounded buttons with gradient
backgrounds and hover animations - **Enhanced Card Design**: Subtle shadows, rounded corners, and backdrop blur effects -
**Improved Icons**: Updated Bootstrap icons for better visual hierarchy - **Responsive Design**: Optimized for all screen sizes
- **Smooth Animations**: Subtle hover effects and transitions throughout - **Professional Typography**: Clean, modern font
choices ## Color Scheme - Primary: #0077be (Ocean Blue) - Secondary: #20b2aa (Light Sea Green) - Accent: #4682b4 (Steel Blue) -
Light: #e6f3ff (Light Blue) - Dark: #003d5c (Deep Blue) ## Visual Enhancements - Gradient backgrounds and button effects -
Smooth hover transitions - Enhanced modal dialogs - Improved form styling - Professional card layouts - Shadow effects and
depth ## Theme Structure ``` ocean_blue/ ├── base.j2 ├── header.j2 -> Custom js and css files to include in the head of all
pages ├── home.js -> [OPTIONAL] A custom home page for your site, if not exists the default home will be served ├──
local_style.j2 -> Local basic css style with Ocean Blue theme enhancements ├── navbar.j2 -> Ocean Blue themed navbar with
gradients and enhanced styling ├── notify.j2 -> Custom notify html markup ├── pagination.j2 -> Custom pagination code ``` ##
Requirements The NOW - LMS frontend requires Bootstrap 5, so include those resources in your header: ```html
<head>
    <!-- Bootstrap core CSS -->
    <link rel="stylesheet" href="/static/node_modules/bootstrap/dist/css/bootstrap.css" />
    <script src="/static/node_modules/bootstrap/dist/js/bootstrap.bundle.js"></script>

    <!-- Bootstrap Font -->
    <link rel="stylesheet" href="/static/node_modules/bootstrap-icons/font/bootstrap-icons.css" />
</head>
``` This theme provides a significant visual upgrade while maintaining the functionality and structure of the default NOW LMS
interface.
