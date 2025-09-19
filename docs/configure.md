# Configure NOW - Learning Management System

NOW-LMS provides flexible configuration options to meet different deployment needs. This guide covers all configuration methods and available options.

## Configuration Methods

NOW-LMS supports multiple configuration approaches:

1. **Environment Variables** (recommended for containers/cloud)
2. **Configuration Files** (recommended for traditional servers)
3. **Runtime Configuration** (for advanced integrations)

### Configuration Priority

The configuration loading follows this priority order (highest to lowest):

1. **Runtime overrides** (programmatic overrides)
2. **Environment variables** (highest priority for runtime)
3. **Configuration file** (if found in search paths)
4. **Default values** (built-in defaults)

This means environment variables will always override file configuration, allowing administrators to selectively override specific settings without modifying configuration files.

## Environment Variables

For a complete list of all available environment variables, see the [Configuration Setup Guide](setup-conf.md#configuration-options).

## Configuration Files (ConfigObj)

NOW-LMS supports loading **core configuration** from files using the [ConfigObj](http://configobj.readthedocs.io/) library. This provides flexibility for system administrators who prefer file-based configuration management in Linux environments.

**Important Note**: Only core configuration variables can be set via configuration files. Many application-specific options (navigation features, email settings, localization, etc.) must be configured exclusively through environment variables.

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
# Core Configuration (Supported in config files)
SECRET_KEY = set_a_very_secure_secret_key
DATABASE_URL = postgresql+pg8000://scott:tiger@localhost/mydatabase

# Application Behavior (Requires environment variables only)
# NOW_LMS_AUTO_MIGRATE = 1
# NOW_LMS_FORCE_HTTPS = 0
# LOG_LEVEL = INFO

# Cache Configuration (Core - supported in config files)
REDIS_URL = redis://localhost:6379/0
CACHE_MEMCACHED_SERVERS = 127.0.0.1:11211

# File Storage (Core - supported in config files)
CUSTOM_DATA_DIR = /var/lib/now-lms/data
CUSTOM_THEMES_DIR = /var/lib/now-lms/themes

# Localization (Requires environment variables only)
# NOW_LMS_LANG = en
# NOW_LMS_TIMEZONE = UTC
# NOW_LMS_CURRENCY = USD

# Email Configuration (Requires environment variables only)
# MAIL_SERVER = smtp.example.com
# MAIL_PORT = 587
# MAIL_USERNAME = noreply@example.com
# MAIL_PASSWORD = email_password
# MAIL_USE_TLS = True
# MAIL_DEFAULT_SENDER = noreply@example.com
```

**Variables that require environment variables only** (commented out above):

- All `NOW_LMS_*` variables
- All `MAIL_*` variables
- All `LMS_*` variables
- LOG_LEVEL and other application-specific settings

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
LOG_LEVEL = INFO
CUSTOM_DATA_DIR = /var/lib/now-lms/data
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

## Runtime Configuration

You can also configure NOW-LMS at runtime by setting configuration values in the `config` dictionary of the main Flask app:

```python
from now_lms import lms_app

# Configure your app:
lms_app.config["SECRET_KEY"] = "set_a_very_secure_secret_key"
lms_app.config["SQLALCHEMY_DATABASE_URI"] = "database_uri"

app = lms_app
```

Note that initial log messages will refer to the default options because you are overwriting options after the initial import of the app.

## Database Configuration

NOW-LMS automatically corrects database URI formats to ensure compatibility:

### PostgreSQL

```bash
# These formats are automatically converted:
postgres://user:pass@host:port/db        → postgresql+pg8000://user:pass@host:port/db
postgresql://user:pass@host:port/db      → postgresql+pg8000://user:pass@host:port/db

# Heroku PostgreSQL with SSL (automatic detection):
postgres://user:pass@host:port/db        → postgresql://user:pass@host:port/db?sslmode=require
```

### MySQL/MariaDB

```bash
# These formats are automatically converted:
mysql://user:pass@host:port/db           → mysql+mysqlconnector://user:pass@host:port/db
mariadb://user:pass@host:port/db         → mariadb+mariadbconnector://user:pass@host:port/db
```

### SQLite

```bash
# Local file database:
sqlite:///path/to/database.db

# In-memory database (testing only):
sqlite://
```

## Next Steps

- For deployment-specific configuration, see the [Setup Guide](setup.md)
- For database setup, see the [Database Configuration](db.md)
- For server deployment, see the platform-specific guides
