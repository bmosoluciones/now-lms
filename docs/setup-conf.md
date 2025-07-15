# Configuring NOW-LMS

There are several options to set the system configuration, for example if your are running NOW-LMS in a dedicated server most of the time system administrator prefer to save configuration options in a file saved in the file system, for administrator of the system using a container based enviroment or a server less setup setting up configuration via enviroment variables can be handy.

## Enviroment variables:

NOW-LMS load its configuration from enviroment variables by default, you can set enviroment variables via command line but this is not recomended, you can set your enviroments variables via:

1. A Dockerfile o Containerfile archive.
2. In a systemd unit file.
3. In a start scritps.

### Setting enviroments variables in bash:

```
# Example of setting up variables in bash shell
export FLASK_APP=now_lms
export SECRET_KEY=set_a_very_secure_secret_key
export DATABASE_URL=postgresql+pg8000://scott:tiger@localhost/mydatabase
lmsctl serve
```

### Example systemd unit file:

In most modern Linux distribution systemd is the init service, you can set your own services writing a unit file:

```
[Unit]
Description=NOW - Learning Management System

[Service]
Enviroment=FLASK_APP=now_lms
Environment=SECRET_KEY=set_a_very_secure_secret_key
Environment=DATABASE_URL=postgresql+pg8000://scott:tiger@localhost/mydatabase
ExecStart=/usr/bin/lmsctl serve

[Install]
WantedBy=multi-user.target
```

### Dockerfile enviroment variables:

Most of the time you will want to save Docker enviroment varibles in a `compose.yml` file:

```
services:
  web:
    image: quay.io/bmosoluciones/now_lms
    environment:
    - SECRET_KEY=set_a_very_secure_secret_key
    - DATABASE_URL=postgresql+pg8000://scott:tiger@localhost/mydatabase
    ports:
      - '8080:8080'

```

## Ad hoc configuration:

You can can also configure NOW-LMS at run time setting configuration values in the `config` dictionary of the main Flask app.

```
from now_lms import lms_app

# Configure your app:
lms_app.config["SECRET_KEY"] = "set_a_very_secure_secret_key"
lms_app.config["SQLALCHEMY_DATABASE_URI"] = "database_uri"

app = lms_app
```

Note that initial log messages will refer to the default options because you are overwritten options before the initial import of the app.

## Configuration options:

You can use the following options to configure NOW-LMS:

-   **SECRET_KEY** (<span style="color:red">required</span>): A secure string used to secure the login proccess, form
    validation, jwt tokens and other sensible data.
-   **DATABASE_URL** (<span style="color:red">required</span>): Note that this is a user friendly alias to
    `SQLALCHEMY_DATABASE_URI`, must be a valid SQLAlchemy conextion string. Supported databases are SQLite, MySQL and
    PostgreSQL. MariaDB should work out of the box but we not test the release versus this database engines. Checkout the
    [SQLAlchemy docs](https://docs.sqlalchemy.org/en/20/core/engines.html) to valid examples to conections strings, the
    PyMSQL (MySQL) and PG800 (Postgresql) database drivers are installed as dependencies, other database engines may
    requiere manual
    drivers setup.
-   **REDIS_URL** (<span style="color:green">optional</span>): User friendly alias to `CACHE_REDIS_URL`. Connection
    string to use [Redis](https://redis.io/) as cache backend, for example `redis://localhost:6379/0`.
-   **CUSTOM_DATA_DIR** (<span style="color:purple">recomended</span>): Directory to save system, must be writable by the
    main app proccess. Note that this variable can NOT be set AD-HOC because the order we parse the configuration
    options, so you must set this options before the app starts. You MUST have backups this directory in the same way
    you make backups of the system database.
-   **CUSTOM_THEMES_DIR** (<span style="color:purple">recomended</span>): Directory to save custom user themes, note
    that `STATIC` files like .js or .css are not served from the `THEMES` and should be places in the directory
    "static/files/public/themes" most of the times.
-   **LOG_LEVEL** (<span style="color:purple">recomended</span>): Available log level are: `TRACE`, `DEBUG`, `INFO`,
    `WARNING`, `ERROR`. Logs are send to the standar output by default.
-   **ADMIN_USER** and **ADMIN_PSWD** (<span style="color:yellow">temporal</span>): Only used at database initial
    setup to set the administrator user and password.
