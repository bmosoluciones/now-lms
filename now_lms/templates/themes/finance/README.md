# Finance Theme A professional financial theme for NOW LMS inspired by the green and gray colors of US dollar bills, designed
for financial and business education. ## Features - **Financial Color Palette**: Green and gray tones inspired by US currency -
**Professional Business Navbar**: Corporate styling suitable for financial institutions - **Money-Inspired Button Styles**:
Elegant buttons with financial color schemes - **Corporate Card Design**: Professional styling with subtle financial touches -
**Business Icons**: Bootstrap icons appropriate for financial education - **Responsive Design**: Optimized for all screen sizes
- **Professional Look**: High-end appearance suitable for financial courses - **Corporate Typography**: Professional,
trustworthy font choices ## Color Scheme - Primary: #006747 (Dollar Green) - Secondary: #2E4A3B (Dark Green) - Accent: #4CAF50
(Medium Green) - Light: #F0F2F0 (Light Gray) - Dark: #2E2E2E (Dark Gray) ## Visual Enhancements - Professional financial
styling - Subtle currency-inspired effects - Corporate modal dialogs - Business form styling - Financial card layouts -
Professional shadow effects ## Theme Structure ``` finance/ ├── base.j2 ├── header.j2 -> Custom js and css files to include in
the head of all pages ├── home.js -> [OPTIONAL] A custom home page for your site, if not exists the default home will be served
├── local_style.j2 -> Local basic css style with Finance theme enhancements ├── navbar.j2 -> Finance themed navbar with
professional business styling ├── notify.j2 -> Custom notify html markup ├── pagination.j2 -> Custom pagination code ``` ##
Requirements The NOW - LMS frontend requires Bootstrap 5, so include those resources in your header: ```html
<head>
    <!-- Bootstrap core CSS -->
    <link rel="stylesheet" href="/static/node_modules/bootstrap/dist/css/bootstrap.css" />
    <script src="/static/node_modules/bootstrap/dist/js/bootstrap.bundle.js"></script>

    <!-- Bootstrap Font -->
    <link rel="stylesheet" href="/static/node_modules/bootstrap-icons/font/bootstrap-icons.css" />
</head>
``` This theme provides a professional financial experience perfect for business and financial education while maintaining the
functionality and structure of the default NOW LMS interface.
