# The original NOW Learning Management System template Vanilla Boostrap 5 templease used as base. You can use this template as
base for your own theme. The theme structure is as follow: ``` theme_dir: |- base.j2 |- header.j2 -> Custom js and css files to
include in the head of all pages. |- home.js -> [OPTIONAL] A cusmtom home page for your site, if not existe the default home
will be served. |- local_style.j2 -> Local basic css style |- navbar.j2 -> This is the navbar the most visible part of your
theme. |- notify.j2 -> Custom notify html makup |- pagination.j2 -> Custom pagination code. ``` Note that the NOW - LMS
frontend requires Bootstrap 5 so include those resources in your header. ```
<head>
    <!-- Bootstrap core CSS -->
    <link rel="stylesheet" href="/static/node_modules/bootstrap/dist/css/bootstrap.css" />
    <script src="/static/node_modules/bootstrap/dist/js/bootstrap.bundle.js"></script>

    <!-- Bootstrap Font -->
    <link rel="stylesheet" href="/static/node_modules/bootstrap-icons/font/bootstrap-icons.css" />
</head>
```
