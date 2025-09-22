---
draft: false
date: 2025-09-19
slug: environment-variable-validation
authors:
  - admin
categories:
  - Configuration
  - Features
---

# Environment Variable Validation for Custom Directories

**Date**: September 19, 2025
**Feature**: Custom Data and Theme Directory Support

## Overview

NOW-LMS now properly validates and respects the `NOW_LMS_DATA_DIR` and `NOW_LMS_THEMES_DIR` environment variables, allowing for custom directory configurations for system data and themes. This feature enhances deployment flexibility and supports containerized environments.

## Environment Variables Supported

### `NOW_LMS_DATA_DIR`
- **Purpose**: Specifies a custom directory for application data files
- **Default**: `now_lms/static` (relative to application directory)
- **Example**: `export NOW_LMS_DATA_DIR=/var/lib/now-lms/data`

### `NOW_LMS_THEMES_DIR`
- **Purpose**: Specifies a custom directory for theme templates
- **Default**: `now_lms/templates` (relative to application directory)
- **Example**: `export NOW_LMS_THEMES_DIR=/var/lib/now-lms/themes`

## How It Works

1. **Environment Detection**: The system checks for these environment variables at startup
2. **Directory Creation**: If custom directories are specified, they are automatically created
3. **Content Population**: Default data and themes are copied to custom directories if they don't exist or are empty
4. **Automatic Initialization**: The populate functions run at every app startup when environment variables are detected

## Implementation Details

### Populate Functions

The system includes two key functions that handle directory population:

- `populate_custmon_data_dir()`: Copies default static files to custom data directory
- `populate_custom_theme_dir()`: Copies default templates to custom theme directory

### Integration with App Initialization

The `init_app()` function now calls these populate functions whenever:
- The database is already initialized
- Custom environment variables are detected
- This ensures custom directories are always properly populated

## Testing and Validation

### Comprehensive Test Suite

New tests have been added to validate:
- Custom data directory creation and population
- Custom theme directory creation and population
- Integration with the app initialization process
- Environment variable cleanup for testing

### Test Environment Safety

The test environment properly unsets environment variables to prevent test interference:
- `dev/test.sh` now clears all environment variables before running tests
- Individual tests use isolated environments with proper cleanup

## Usage Examples

### Docker Deployment
```dockerfile
ENV NOW_LMS_DATA_DIR=/app/data
ENV NOW_LMS_THEMES_DIR=/app/themes
VOLUME ["/app/data", "/app/themes"]
```

### Systemd Service
```ini
[Service]
Environment="NOW_LMS_DATA_DIR=/var/lib/now-lms/data"
Environment="NOW_LMS_THEMES_DIR=/var/lib/now-lms/themes"
ExecStart=/usr/bin/lmsctl serve
```

### Development Setup
```bash
export NOW_LMS_DATA_DIR="$HOME/lms-dev/data"
export NOW_LMS_THEMES_DIR="$HOME/lms-dev/themes"
lmsctl serve
```

## Benefits

1. **Deployment Flexibility**: Support for containerized and multi-tenant deployments
2. **Data Separation**: Clean separation between application code and user data
3. **Theme Customization**: Easy theme customization without modifying application files
4. **Backup and Migration**: Simplified data backup and migration procedures
5. **Security**: Better file system security with dedicated directories

## Directory Structure

When custom directories are used, the following structure is created:

```
$NOW_LMS_DATA_DIR/
├── files/
│   ├── public/
│   └── private/
├── img/
├── icons/
└── examples/

$NOW_LMS_THEMES_DIR/
├── admin/
├── blog/
├── course/
├── evaluation/
└── [other template directories]
```

## Backward Compatibility

This feature maintains full backward compatibility:
- Systems without environment variables continue to use default directories
- Existing installations are unaffected
- No configuration changes required for current deployments

## Future Enhancements

Potential future improvements include:
- Support for additional directory customizations
- Configuration validation and error reporting
- Directory migration tools
- Performance optimization for large custom directories

---

This enhancement provides NOW-LMS with enterprise-grade deployment flexibility while maintaining simplicity for development and testing environments.