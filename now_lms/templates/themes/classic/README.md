# Classic Theme A traditional, academic theme for NOW LMS inspired by Moodle's classic color palette with educational-focused
design. ## Features - **Educational Color Palette**: Traditional academic blue and orange combinations - **Clean Academic
Navbar**: Professional styling suitable for educational institutions - **Traditional Button Styles**: Standard buttons with
academic color schemes - **Academic Card Design**: Clean, traditional styling with subtle enhancements - **Educational Icons**:
Bootstrap icons appropriate for learning environments - **Responsive Design**: Optimized for all screen sizes - **Accessibility
Focused**: High contrast and clear typography for learning - **Classic Typography**: Traditional, readable font choices for
educational content ## Color Scheme - Primary: #0F6CBF (Moodle Blue) - Secondary: #FF7043 (Academic Orange) - Accent: #1177D1
(Light Blue) - Light: #F8F9FA (Light Gray) - Dark: #495057 (Dark Gray) ## Visual Enhancements - Traditional academic styling -
Subtle hover effects - Clean modal dialogs - Standard form styling - Classic card layouts - Minimal shadow effects ## Theme
Structure ``` classic/ ├── base.j2 ├── header.j2 -> Custom js and css files to include in the head of all pages ├── home.js ->
[OPTIONAL] A custom home page for your site, if not exists the default home will be served ├── local_style.j2 -> Local basic
css style with Classic theme enhancements ├── navbar.j2 -> Classic academic themed navbar ├── notify.j2 -> Custom notify html
markup ├── pagination.j2 -> Custom pagination code ``` ## Requirements The NOW - LMS frontend requires Bootstrap 5, so include
those resources in your header: ```html
<head>
    <!-- Bootstrap core CSS -->
    <link rel="stylesheet" href="/static/node_modules/bootstrap/dist/css/bootstrap.css" />
    <script src="/static/node_modules/bootstrap/dist/js/bootstrap.bundle.js"></script>

    <!-- Bootstrap Font -->
    <link rel="stylesheet" href="/static/node_modules/bootstrap-icons/font/bootstrap-icons.css" />
</head>
``` This theme provides a traditional educational experience while maintaining the functionality and structure of the default
NOW LMS interface.
