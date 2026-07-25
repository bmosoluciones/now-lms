# The original NOW Learning Management System template

Vanilla Bootstrap 5 theme used as base. You can use this template as a base for your own theme.

## Theme Structure

```
now_lms/
├── base.j2
├── header.j2          # Custom JS and CSS files to include in the head of all pages
├── local_style.j2     # Local basic CSS style
├── navbar.j2          # Navbar, the most visible part of your theme
├── notify.j2          # Custom notify HTML markup
├── pagination.j2      # Custom pagination code
├── js.j2              # JavaScript libraries
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
