# Corporate Theme A professional, clean theme designed for corporate and business environments. ## Features - **Professional
Color Palette**: Conservative blue and gray combinations for business use - **Clean Navigation**: Professional navbar with
subtle hover effects - **Standard Button Styles**: Business-appropriate button designs with clean aesthetics - **Professional
Card Design**: Clean shadows, standard corners, and proper spacing - **Business Icons**: Conservative Bootstrap icons for
professional appearance - **Responsive Design**: Optimized for all screen sizes and devices - **Accessible Design**: Proper
contrast ratios and accessibility features - **Clean Typography**: Professional font choices optimized for readability ## Color
Scheme - Primary: #003366 (Corporate Blue) - Secondary: #f8f9fa (Light Gray) - Accent: #1a365d (Dark Blue) - Light: #e9ecef
(Light Gray) - Dark: #2d3748 (Dark Gray) - Blue: #0066cc (Corporate Blue) - Gray: #6c757d (Medium Gray) ## Visual Design -
Clean, minimal design approach - Professional color combinations - Standard button and form styling - Conservative hover
effects - Business-appropriate layouts - Proper spacing and typography - Subtle shadows and borders ## Theme Structure ```
corporativo/ ├── base.j2 ├── header.j2 -> Custom js and css files to include in the head of all pages ├── home.js -> [OPTIONAL]
A custom home page for your site, if not exists the default home will be served ├── local_style.j2 -> Local basic css style
with Corporate theme enhancements ├── navbar.j2 -> Corporate themed navbar with professional styling ├── notify.j2 -> Custom
notify html markup ├── pagination.j2 -> Custom pagination code ``` ## Requirements The NOW - LMS frontend requires Bootstrap 5,
so include those resources in your header: ```html
<head>
    <!-- Bootstrap core CSS -->
    <link rel="stylesheet" href="/static/node_modules/bootstrap/dist/css/bootstrap.css" />
    <script src="/static/node_modules/bootstrap/dist/js/bootstrap.bundle.js"></script>

    <!-- Bootstrap Font -->
    <link rel="stylesheet" href="/static/node_modules/bootstrap-icons/font/bootstrap-icons.css" />
</head>
``` This theme provides a professional, business-appropriate design while maintaining the functionality and structure of the
default NOW LMS interface. Perfect for corporate training environments and professional development platforms.
