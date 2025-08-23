# NOW Learning Management System (LMS)

NOW LMS is a Flask-based Learning Management System written in Python with Bootstrap 5 frontend. The system supports course creation, user management, evaluations, certifications, and multiple database backends.

**ALWAYS reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.**

## Working Effectively

### Bootstrap, Build, and Test the Repository

Always follow these exact steps in order:

1. **Create Python virtual environment**:

    ```bash
    python3 -m venv venv
    ```

2. **Activate virtual environment**:

    ```bash
    # Linux/Mac:
    source venv/bin/activate
    # Windows:
    venv\Scripts\activate.bat
    ```

3. **Install Python dependencies**:

    ```bash
    python3 -m pip install --upgrade pip
    python3 -m pip install -r development.txt
    ```

    **Timing**: Takes ~2 minutes. NEVER CANCEL. Set timeout to 5+ minutes.
    **Note**: If network timeouts occur, retry the command. Some environments may have slower PyPI access.

4. **Install frontend dependencies (root)**:

    ```bash
    npm install
    ```

    **Timing**: Takes ~5 seconds. Set timeout to 2+ minutes.

5. **Install frontend dependencies (static)**:
    ```bash
    cd now_lms/static && npm install && cd ../..
    ```
    **Timing**: Takes ~3 seconds. Set timeout to 2+ minutes.

### Run Tests

**CRITICAL**: Always run tests to validate any code changes.

```bash
# Run full test suite (recommended)
python -m pytest tests/ -v --exitfirst
```

**Timing**: Takes ~57 seconds. NEVER CANCEL. Set timeout to 15+ minutes.

```bash
# Run specific test for debugging
python -m pytest tests/test_all_routes_comprehensive.py -v
```

```bash
# Run tests with coverage
CI=True pytest -v --exitfirst --cov=now_lms
```

```bash
# Alternative: Use development test script (includes linting)
./dev/test.sh
```

**Timing**: Takes ~76 seconds. NEVER CANCEL. Set timeout to 15+ minutes.

### Run the Application

**Production Mode (Recommended for Validation)**:

```bash
python -m now_lms
```

**Timing**: Starts in ~2 seconds. Application runs on http://127.0.0.1:8080/

- Default user: `lms-admin`
- Default password: `lms-admin`

**Development Mode** (Flask dev server - requires database initialization):

```bash
# First initialize the database
FLASK_APP=now_lms python -c "from now_lms import init_app; init_app()"

# Then run development server
FLASK_APP=now_lms LOG_LEVEL=TRACE flask run --debug --reload --port 8080
```

**Note**: Development mode has some known route issues. Use production mode for validation.

### Linting and Code Quality

**ALWAYS run these before committing changes**:

```bash
# Format Python code
black -v now_lms
```

**Timing**: Takes ~1 second.

```bash
# Lint Python code
flake8 --max-line-length=120 --ignore=E501,E203,E266,W503,E722 now_lms
```

**Timing**: Takes ~1 second.

```bash
# Check with ruff
python -m ruff check --fix now_lms
```

**Timing**: Takes <1 second.

```bash
# Type checking (first run installs types)
python -m mypy now_lms --install-types --non-interactive --ignore-missing-imports
```

**Timing**: First run ~36 seconds (installs types), subsequent runs ~3 seconds.

```bash
# Format HTML templates
./node_modules/.bin/prettier --write now_lms/templates/ --parser=html "**/*.j2"
```

## Validation

### Quick Validation After Setup

**Verify installation is working**:

```bash
# Test basic import and functionality
python -m pytest tests/test_basicos.py::TestBasicos::test_importable -v
```

Should pass in ~1 second.

```bash
# Test application startup (production mode)
python -m now_lms &
sleep 3
curl -I http://127.0.0.1:8080/
pkill -f "python -m now_lms"
```

Should return HTTP 200 OK.

**ALWAYS test these scenarios after making changes**:

1. **Basic Application Startup**:

    ```bash
    python -m now_lms
    curl -I http://127.0.0.1:8080/
    ```

    Should return HTTP 200 with valid HTML.

2. **Key Routes Validation**:

    ```bash
    # Homepage (public)
    curl -I http://127.0.0.1:8080/

    # Blog (public)
    curl -I http://127.0.0.1:8080/blog

    # Login page
    curl -I http://127.0.0.1:8080/user/login

    # Protected route (should redirect to login)
    curl -I http://127.0.0.1:8080/category/list
    ```

3. **Route Testing**:
    ```bash
    # Test comprehensive routes (discovers all 207 routes)
    python -m pytest tests/test_all_routes_comprehensive.py -v
    ```

### Database Support

- **Default**: SQLite (created as `now_lms.db` in repository root)
- **PostgreSQL**: Set `DATABASE_URL=postgresql+pg8000://user:pass@host:port/db`
- **MySQL**: Set `DATABASE_URL=mysql+mysqldb://user:pass@host:port/db`
- **In-memory testing**: Automatically uses SQLite in-memory for tests

## Common Tasks

### Development Scripts Location

All development scripts are in the `dev/` directory:

- `dev/test.sh` - Complete test and lint pipeline
- `dev/server.sh` - Start development server (Flask debug mode)
- `dev/lint.sh` - Format Python and HTML code

### Key Project Structure

```
now-lms/
├── now_lms/                 # Main application code
│   ├── vistas/             # Flask views/routes
│   ├── db/                 # Database models and utilities
│   ├── forms/              # WTForms form definitions
│   ├── templates/          # Jinja2 templates
│   ├── static/             # Static assets (CSS, JS, images)
│   │   └── package.json    # Frontend dependencies
│   └── config/             # Application configuration
├── tests/                  # Test suite (305 tests)
├── docs/                   # Documentation
├── dev/                    # Development scripts
├── requirements.txt        # Production dependencies
├── development.txt         # Development dependencies (includes test.txt)
├── test.txt               # Testing dependencies
├── package.json           # Root npm dependencies (prettier, etc.)
└── pyproject.toml         # Python project configuration
```

### Database Models Location

- `now_lms/db/__init__.py` - Main database models
- `now_lms/db/data_test.py` - Test data creation
- `now_lms/db/initial_data.py` - Default data setup

### Common Code Patterns

- **Views**: Located in `now_lms/vistas/` (Spanish for "views")
- **Forms**: Use WTForms in `now_lms/forms/`
- **Authentication**: Role-based (admin, instructor, moderator, student)
- **Routes**: Comprehensive route testing covers all 207 routes automatically

### Environment Variables

- `SECRET_KEY` - Application secret (defaults to "dev")
- `DATABASE_URL` - Database connection string
- `LOG_LEVEL` - Logging level (TRACE, DEBUG, INFO, WARNING, ERROR)
- `FLASK_APP` - Set to "now_lms" for Flask commands
- `CI` - Set to "True" for testing mode (uses in-memory database)

### Troubleshooting

**Database Issues**: Delete `now_lms.db` and restart application to recreate fresh database.

**Missing Dependencies**: Run `python -m pip install -r development.txt` again.

**Network Timeouts During Install**: Retry pip install commands. Some environments have slower PyPI access.

**Frontend Issues**: Run `npm install` in both repository root and `now_lms/static/`.

**Route 404 Errors**: Many routes require authentication. Test with proper login or use comprehensive route tests.

### CI/CD Pipeline

The `.github/workflows/python.yml` workflow:

- Tests on Python 3.11, 3.12, 3.13
- Runs pytest with coverage
- Performs linting with flake8, black, mypy, and ruff
- Builds and validates Python package

## Available Session Fixtures

Use those fictures to improved tests time execution.

1. **session_basic_db_setup**: Minimal database setup with basic configuration and certificates
2. **session_full_db_setup**: Full database setup with users, courses, and test data
3. **session_full_db_setup_with_examples**: Full setup including example data
4. **isolated_db_session**: Function-scoped session for modifying data while using session fixtures

**ALWAYS ensure your changes pass all these checks locally before committing.**
