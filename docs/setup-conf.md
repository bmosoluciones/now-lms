# Configuring NOW-LMS

There are several options to set the system configuration, for example if your are running NOW-LMS in a dedicated server most of the time system administrator prefer to save configuration options in a file saved in the file system, for administrator of the system using a container based enviroment or a server less setup setting up configuration via enviroment variables can be handy.

## Enviroment variables:

NOW-LMS can load its configuration from enviroment variables, when running in a container enviroment it is usefull to set the configuration with enviroment variables than can be set via command line, Dockerfile o Containerfile archive or vía a grafical user interface like Cockpit [<sup>1</sup>](https://ciq.com/blog/how-to-deploy-podman-containers-with-cockpit/) [<sup>2</sup>](https://docs.oracle.com/en/operating-systems/oracle-linux/cockpit/podman_container_mgmt.html#topic_lkh_bgx_yxb), also enviroment variables can be set in a systemd unit file.

### Setting enviroments variables in bash:

```
# Example of setting up variables in bash shell
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

## Configuration from file:

NOW-LMS can load its configuration from a init like file placed in `/etc/nowlms.conf` or `$home/.config/nowlms.conf` or a file named `nowlms.conf` in the current directory of the main proccess. Save the configuration in a plain text is common for unix like operative systems administrators.

```
# Example minimal configuration file in `/etc/nowlms.conf`
SECRET_KEY=set_a_very_secure_secret_key_with_[\w\[\]`!@#$%\^&*()={}:;<>+'-]*
SQLALCHEMY_DATABASE_URI=postgresql+pg8000://scott:tiger@localhost/mydatabase
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

## List of options:

You can use the following options to configure NOW-LMS:

-   **SECRET_KEY** (required): A secure string used to secure the login proccess and form validation.
-   **SQLALCHEMY_DATABASE_URI** (required): A valid SQLAlchemy conextion string, SQLite, MySQL version 8 and a resent version of PostgreSQL
    must work out of the box, MariaDB ans MS SQLServer should work but we not test the release versus this database engines. Checkout the
    [SQLAlchemy docs](https://docs.sqlalchemy.org/en/20/core/engines.html) to valid examples to conections strings, the PyMSQL and PG800 database drivers are installed as normal dependencies, other database engines may requiere manual drivers setup.
-   **DATABASE_URL** (alias): User friendly alias to `SQLALCHEMY_DATABASE_URI`.
-   **CACHE_REDIS_URL** (optional): Connection string to use [Redis](https://redis.io/) as cache backend. Example to connect to a Redis
    instance running in the same host is: `redis://localhost:6379/0`.
-   **REDIS_URL** (alias): User friendly alias to `CACHE_REDIS_URL`.
-   **CACHE_MEMCACHED_SERVERS** (optional): Connection string to use [Mencached](https://memcached.org/) as cache backend.
-   **UPLOAD_FILES_DIR** (recomended): Directory to save user uploaded files, must be writable. Note that this variable can be set AD-HOC
    because the order we parse the configuration options upload file directorios must be set before the initial import of the app, any
    overwritte we do can lead to unexpected results. It is better to set this option as enviroment variable before the firts run of the app. Note that if you migrate your instalation to a diferent host must edit this value so database records can match fisical file storage.
