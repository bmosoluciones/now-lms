# Configuring NOW-LMS

There are several options to set the system configuration. For example, if you are running NOW-LMS on a dedicated server, most of the time system administrators prefer to save configuration options in a file saved on the file system. For administrators using a container-based environment or a serverless setup, setting up configuration via environment variables can be more convenient.

## Environment Variables:

NOW-LMS loads its configuration from environment variables by default. You can set environment variables via command line, but this is not recommended for production. You can set your environment variables via:

1. A Dockerfile or Containerfile.
2. In a systemd unit file.
3. In a startup script.

### Setting Environment Variables in Bash:

```bash
# Example of setting up variables in bash shell
export FLASK_APP=now_lms
export SECRET_KEY=set_a_very_secure_secret_key
export DATABASE_URL=postgresql+pg8000://scott:tiger@localhost/mydatabase
lmsctl serve
```

### Example systemd Unit File:

In most modern Linux distributions, systemd is the init service. You can set your own services by writing a unit file:

```ini
[Unit]
Description=NOW - Learning Management System

[Service]
Environment=FLASK_APP=now_lms
Environment=SECRET_KEY=set_a_very_secure_secret_key
Environment=DATABASE_URL=postgresql+pg8000://scott:tiger@localhost/mydatabase
ExecStart=/usr/bin/lmsctl serve

[Install]
WantedBy=multi-user.target
```

### Dockerfile Environment Variables:

Most of the time you will want to save Docker environment variables in a `compose.yml` file:

```yaml
services:
    web:
        image: quay.io/bmosoluciones/now_lms
        environment:
            - SECRET_KEY=set_a_very_secure_secret_key
            - DATABASE_URL=postgresql+pg8000://scott:tiger@localhost/mydatabase
        ports:
            - "8080:8080"
```

## Configuration via Config File (ConfigObj):

NOW-LMS supports loading **core configuration** from files using the [ConfigObj](http://configobj.readthedocs.io/) library. This provides flexibility for system administrators who prefer file-based configuration management in Linux environments.

**Important Note**: Only core configuration variables can be set via configuration files. Many application-specific options must be configured exclusively through environment variables.

### File Search Order

NOW-LMS searches for configuration files in the following order, using the first file found:

1. **Environment variable**: `NOW_LMS_CONFIG=/path/to/config.conf`
2. **System-wide config**: `/etc/now-lms/now-lms.conf`
3. **Alternative system config**: `/etc/now-lms.conf`
4. **User config**: `~/.config/now-lms/now-lms.conf`
5. **Local config**: `./now-lms.conf` (current directory)

### Configuration File Format

Configuration files use a simple INI-like format supported by ConfigObj and can contain **core configuration variables only**:

```ini
# Core configuration (supported in config files)
SECRET_KEY = set_a_very_secure_secret_key
DATABASE_URL = postgresql+pg8000://scott:tiger@localhost/mydatabase

# Cache configuration (supported in config files)
REDIS_URL = redis://localhost:6379/0
CACHE_MEMCACHED_SERVERS = 127.0.0.1:11211

# Note: Directory paths (NOW_LMS_DATA_DIR, NOW_LMS_THEMES_DIR), application-specific
# variables (NOW_LMS_*), MAIL_*, LMS_*, and LOG_LEVEL must be set as environment
# variables only because they are read during early module initialization before
# the config file is loaded.
```

### Configuration Priority

The configuration loading follows this priority order (highest to lowest):

1. **config_overrides** (programmatic overrides)
2. **Environment variables** (highest priority for runtime)
3. **Configuration file** (if found in search paths)
4. **Default values** (built-in defaults)

This means environment variables will always override file configuration, allowing administrators to selectively override specific settings without modifying configuration files.

### Alias Support

For convenience, the following aliases are supported in configuration files:

- `DATABASE_URL` → automatically mapped to `SQLALCHEMY_DATABASE_URI`
- `REDIS_URL` → automatically mapped to `CACHE_REDIS_URL`

Both the alias and the canonical name will be available in the application configuration.

### Example Usage

```bash
# Create system-wide configuration
sudo mkdir -p /etc/now-lms
sudo tee /etc/now-lms/now-lms.conf > /dev/null << EOF
SECRET_KEY = your_secure_secret_key
DATABASE_URL = postgresql+pg8000://nowlms:password@localhost/nowlms_db
EOF

# Set appropriate permissions
sudo chmod 600 /etc/now-lms/now-lms.conf
sudo chown now-lms:now-lms /etc/now-lms/now-lms.conf

# Start NOW-LMS (will automatically load the config file)
lmsctl serve
```

### Security Considerations

- **File Permissions**: Set configuration files to mode `0600` (readable only by owner) to protect sensitive values like `SECRET_KEY`
- **Environment Override**: Use environment variables to override sensitive settings in production without modifying files
- **Optional Dependency**: ConfigObj is an optional dependency; the system works normally without it using environment variables

### Logging

When a configuration file is loaded, NOW-LMS will log an informational message:

```
INFO: Loading configuration from file: /etc/now-lms/now-lms.conf
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

### Core Configuration (Required)

- **SECRET_KEY** (<span style="color:red">required</span>): A secure string used to secure the login process, form
  validation, JWT tokens and other sensitive data. Must be unique and kept secret.
- **DATABASE_URL** (<span style="color:red">required</span>): Note that this is a user friendly alias to
  `SQLALCHEMY_DATABASE_URI`, must be a valid SQLAlchemy connection string. Supported databases are SQLite, MySQL and
  PostgreSQL. MariaDB should work out of the box but we do not test the release against this database engine. Check the
  [SQLAlchemy docs](https://docs.sqlalchemy.org/en/20/core/engines.html) for valid connection string examples. The
  PyMySQL (MySQL) and pg8000 (PostgreSQL) database drivers are installed as dependencies, other database engines may
  require manual driver setup.

### Cache Configuration (Optional)

- **REDIS_URL** (<span style="color:green">optional</span>): User friendly alias to `CACHE_REDIS_URL`. Connection
  string to use [Redis](https://redis.io/) as cache backend, for example `redis://localhost:6379/0`.
- **CACHE_REDIS_URL** (<span style="color:green">optional</span>): Direct Redis cache configuration. If both `REDIS_URL` and this are set, this takes precedence.
- **SESSION_REDIS_URL** (<span style="color:green">optional</span>): Redis connection string specifically for session storage in multi-worker environments (Gunicorn). If not set, falls back to `CACHE_REDIS_URL` or `REDIS_URL` for session storage.
- **CACHE_MEMCACHED_SERVERS** (<span style="color:green">optional</span>): Connection string to use [Memcached](https://memcached.org/) as cache backend, for example `127.0.0.1:11211`.
- **NOW_LMS_MEMORY_CACHE** (<span style="color:green">optional</span>): Set to `1` to enable in-memory caching (not recommended for production).

### Application Behavior

- **NOW_LMS_AUTO_MIGRATE** (<span style="color:green">optional</span>): Set to `1` to run database migrations at app startup.
- **NOW_LMS_FORCE_HTTPS** (<span style="color:green">optional</span>): Set to `1` to force the app to run in HTTPS mode.
- **NOW_LMS_DEMO_MODE** (<span style="color:yellow">development</span>): Set to `1` to enable demo mode for testing and demonstrations.

### File Storage and Directories

- **NOW_LMS_DATA_DIR** (<span style="color:purple">recommended</span>): Directory to save user-uploaded files and system data, must be writable by the main app process. **IMPORTANT**: This variable MUST be set as an environment variable and CANNOT be set in config files because it is read during early module initialization before config files are loaded. You MUST backup this directory in the same way you backup the system database.
- **NOW_LMS_THEMES_DIR** (<span style="color:purple">recommended</span>): Directory to save custom user themes. **IMPORTANT**: This variable MUST be set as an environment variable and CANNOT be set in config files because it is read during early module initialization. Note that static files like .js or .css are not served from the themes directory and should be placed in the directory "static/files/public/themes" most of the time.

### Localization and Regional Settings

- **NOW_LMS_LANG** (<span style="color:green">optional</span>): Default language for the system. Available options: `en` (English), `es` (Spanish), `pt_BR` (Portuguese Brazil). Defaults to `en` in production, `es` in testing.
- **NOW_LMS_TIMEZONE** (<span style="color:green">optional</span>): Default timezone for the system. Must be a valid timezone identifier (e.g., `UTC`, `America/New_York`, `Europe/Madrid`). Defaults to `UTC`.
- **NOW_LMS_CURRENCY** (<span style="color:green">optional</span>): Default currency for paid courses. Uses standard currency codes (e.g., `USD`, `EUR`, `MXN`). Defaults to `USD`.

### Email Configuration

- **MAIL_SERVER** (<span style="color:green">optional</span>): SMTP server hostname for sending emails.
- **MAIL_PORT** (<span style="color:green">optional</span>): SMTP server port (typically 25, 465, or 587).
- **MAIL_USERNAME** (<span style="color:green">optional</span>): Username for SMTP authentication.
- **MAIL_PASSWORD** (<span style="color:green">optional</span>): Password for SMTP authentication.
- **MAIL_USE_TLS** (<span style="color:green">optional</span>): Set to `True` to use TLS encryption.
- **MAIL_USE_SSL** (<span style="color:green">optional</span>): Set to `True` to use SSL encryption.
- **MAIL_DEFAULT_SENDER** (<span style="color:green">optional</span>): Default email address for system emails.

### Server Configuration

- **LMS_PORT** (<span style="color:green">optional</span>): Port number for the LMS server (when using lmsctl).
- **PORT** (<span style="color:green">optional</span>): Alternative port configuration (used in cloud environments like Heroku).
- **NOW_LMS_WORKERS** / **WORKERS** (<span style="color:green">optional</span>): Number of worker processes for Gunicorn (when using lmsctl). If not set, automatically calculated based on available RAM and CPU cores. The calculation uses the formula: `min((cpu_count * 2) + 1, available_ram_mb / worker_memory_mb)`, adjusted by thread count if threads > 1. See [RAM Optimization Guide](blog/posts/ram-optimization.md) for detailed examples.
- **NOW_LMS_THREADS** / **THREADS** (<span style="color:green">optional</span>): Number of threads per Gunicorn worker. Defaults to 1. When threads > 1, the worker count is automatically reduced to compensate for memory usage (workers = optimal_workers / threads). Uses `gthread` worker class when threads > 1. See [RAM Optimization Guide](blog/posts/ram-optimization.md) for best practices.
- **NOW_LMS_WORKER_MEMORY_MB** / **WORKER_MEMORY_MB** (<span style="color:green">optional</span>): Estimated memory usage per worker in MB (default: 200). Used in automatic worker calculation to ensure system doesn't run out of RAM. Measure actual usage and adjust accordingly. See [RAM Optimization Guide](blog/posts/ram-optimization.md) for measurement techniques.

### Development and Debugging

- **LOG_LEVEL** (<span style="color:purple">recommended</span>): Available log levels are: `TRACE`, `DEBUG`, `INFO`,
  `WARNING`, `ERROR`. Logs are sent to standard output by default. Defaults to `INFO`.
- **CI** (<span style="color:yellow">development</span>): Set to enable testing mode (uses in-memory database).
- **DEBUG** (<span style="color:yellow">development</span>): Enable Flask debug mode.
- **FLASK_ENV** (<span style="color:yellow">development</span>): Flask environment setting.

### Initial Setup (Temporary)

- **ADMIN_USER** (<span style="color:yellow">initial setup only</span>): Username for the initial administrator account. Only used during database initial setup. Defaults to `lms-admin`.
- **ADMIN_PSWD** (<span style="color:yellow">initial setup only</span>): Password for the initial administrator account. Only used during database initial setup. Defaults to `lms-admin`.
- **LMS_USER** (<span style="color:yellow">initial setup only</span>): Alternative to `ADMIN_USER` for backward compatibility.
- **LMS_PSWD** (<span style="color:yellow">initial setup only</span>): Alternative to `ADMIN_PSWD` for backward compatibility.

### Special Environment Detection

- **DYNO** (<span style="color:blue">automatic</span>): Automatically detected in Heroku environments to adjust database configuration.
- **PYTEST_CURRENT_TEST** (<span style="color:blue">automatic</span>): Automatically detected during testing to use in-memory database.

### Configuration File Support

- **NOW_LMS_CONFIG** (<span style="color:green">optional</span>): Path to custom configuration file. When set, NOW-LMS will load configuration from this file instead of searching default locations.
