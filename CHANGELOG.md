# Changelog

All notable changes to this project will be documented in this file.

- The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
- This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
- This project also follows [Conventional Commits](https://www.conventionalcommits.org/).


## [unreleased]

## [2.0.2] - 2026-07-31

### Added:
 - Enforce one enrollment per student and course (DB unique constraint).
 - Consolidate admin panel: redirect admin users from `/home/panel` to `/admin/panel`.

### Fixed:
 - Grant free-course access when the enrollment has no payment record.
 - Render country field as text input instead of empty select in enrollment forms.
 - Stop requiring a billing address for free enrollments.
 - Stop a repeat enrollment from adding a second enrollment row.
 - Link overlapping SQLAlchemy course relationships with `back_populates`.
 - Stat card contrast ratios for accessibility (WCAG AA).

### Changed:
 - Unify section colors across all role panels.
 - Moderator panel header from red to green, sections uniform success.
 - Drop unused ionicons CDN loads from bundled themes.

### i18n:
 - Make form labels lazy and keep them extractable.
 - Declare `_n:1,2` for extraction so the documented plural helper works.

### Testing:
 - Cover unique-enrollment migration dedup.

## [2.0.1] - 2026-07-29

### Added:
 - Confirm and complete UI translation catalogs (EN, PT_BR).
 - Harden system security with HTTP Security Headers (CSP, HSTS).
 - Support Waitress reverse proxy via `NOW_LMS_TRUSTED_PROXY`.
 - Populate bundled frontend assets when `node_modules` is missing.

### Fixed:
 - MAIL_USE_TLS/MAIL_USE_SSL coercion bug where `str.capitalize()` mismatch prevented match arms from firing.
 - Missing `%(title)s` / `%(url)s` format specifiers in three English translations.
 - ProxyFix `NameError` in WSGI initialization.

### Dependencies:
 - bleach: 6.3.0 → 6.4.0
 - redis: 7.4.0 → 8.0.1
 - weasyprint: 68.1 → 69.0
 - flask-reuploaded: 1.5.0 → 1.6.0
 - ruff: 0.15.22 → 0.16.0

## [2.0.0] - 2026-07-26

> **BREAKING: This release requires manual migration. Existing installations will fail at runtime if themes are not updated. See [Migration Guide](https://bmosoluciones.github.io/now-lms/blog/2026/07/26/page-refactoring-breaking-changes/).**

### Added:
 - Admin-managed custom pages with full CRUD (create, edit, activate/deactivate, delete).
 - Direct access to custom pages from admin panel tools.
 - Theme validation via `theme.yml` presence.
 - Theme overrides for `course_take`, `resource_list`, `resource_view`.
 - Contact form and footer links as separate blueprints.
 - Alembic migration to rename `static_pages` table to `custom_pages`.
 - Documentation for custom pages and static pages.
 - Comprehensive tests for custom pages, contact, and footer links.

### Breaking Changes — Database:
 - DB table `static_pages` renamed to `custom_pages`.
 - Alembic migration renames the table only — does **not** update templates, URLs, or custom themes.
 - `StaticPage` model renamed to `CustomPage`.

### Breaking Changes — Routes:
 - Admin-managed pages: `/static/<slug>` → `/page/<slug>`.
 - Theme-defined pages: new route `/static/<page>`.
 - Contact endpoint: `static_pages.contact` → `contact.contact_form`.

### Breaking Changes — Python API:
 - `get_footer_pages()` → `get_custom_pages()`.
 - `StaticPageFooterForm` → `CustomPageFooterForm`.
 - Blueprint `static_pages` split into `custom_pages`, `contact`, `footer_links`.

### Breaking Changes — Templates:
 - `admin/static_pages.html` → `admin/custom_pages.html`.
 - `admin/edit_static_page.html` → `admin/edit_custom_page.html`.
 - `page_info/static_page.html` → `page_info/custom_page.html`.

### Breaking Changes — Theme directories:
 - `templates/themes/<theme>/custom_pages/` → `templates/themes/<theme>/static_pages/`.
 - Every theme footer/navbar must update: `get_footer_pages()` → `get_custom_pages()`, `static_pages.view_page` → `custom_pages.view_page`, `static_pages.contact` → `contact.contact_form`.
 - Old themes using previous function names or endpoints will fail at runtime (Jinja `UndefinedError`/`BuildError`).

### Migration:
 1. Put the application in maintenance mode.
 2. Back up both databases and all theme directories.
 3. Run `flask db upgrade` (or `alembic upgrade head`).
 4. Rename theme `custom_pages/` directories to `static_pages/`.
 5. Update theme footer/navbar templates for new endpoints and helpers.
 6. Clear application and Redis caches.
 7. Restart application services.
 8. Verify: home, navbar, footer, `/page/<slug>`, `/static/<page>`, `/contact`, blog, courses, admin custom-page CRUD.
 - Check logs for `BuildError`, `UndefinedError`, migration errors, missing-template errors.

### Changed:
 - Renamed inverted nomenclature: DB-driven admin pages are now `custom_pages`, filesystem theme templates are now `static_pages`.

### Fixed:
 - Custom pages now work correctly with default theme.
 - Theme macro fallback works for all macros in `current_theme()`.
 - Theme defaults to `now_lms` when NULL.

## [1.3.3] - 2026-07-25

### Fixed:
 - Rate-limit counters `ResponseError: value is not an integer or out of range` in Redis. `cache.cache.inc()` sent pickled byte-strings to Redis INCR which expects plain integers. Now uses Redis native `INCR` via `cache_incr()` for atomic counter increments, with get+set fallback for non-Redis backends.

## [1.3.2] - 2026-07-25

### Fixed:
 - Rate-limit counter `AttributeError: 'Cache' object has no attribute 'inc'` in login and public API endpoints. Flask-Caching 2.4.0 does not expose `inc()` on its `Cache` wrapper; now accesses the underlying cachelib backend via `cache.cache.inc()`.

## [1.3.1] - 2026-07-25

### Added:
 - Direct role access links to admin panel: new 'Acceso a Roles' card with direct links to Instructor and Moderator panels.

### Fixed:
 - Correct blueprint name in `url_for` for `nuevo_recurso_html` endpoint (was using 'course' instead of 'resources').
 - Handle both `r` and `csrf_seed` columns in database migration.

## [1.3.0] - 2026-07-25

### Added:
 - Payment receipt generation: automatically sends a beautiful HTML receipt via email when PayPal payments are completed (if SMTP is configured).
 - Student payment history: a new `/payments` dashboard where students can view their transaction history, and download a simple PDF copy of their receipt using Weasyprint.
 - i18n and l10n improvements: wrapped untranslated strings in `gettext()` across all views and templates, completed missing EN/PT_BR translations.
 - Comprehensive form testing suite (`tests/test_forms_comprehensive.py`).
 - Alembic migration validation test (`tests/test_alembic_upgrade.py`).
 - `pool_pre_ping` enabled on SQLAlchemy engine options.
 - `invalidar_cache_curso()` and `invalidar_cache_programa()` functions for targeted cache invalidation.

### Changed:
 - `mysql-connector-python` is now the recommended driver for MySQL/MariaDB connections (`DATABASE_URL` with `mysql://` is corrected to `mysql+mysqlconnector://`).
 - Test suite: pytest fixtures now create an isolated Flask application per test for multi-database stability.
 - Increased Programa.nombre column length from 20 to 150.
 - Increased Style.theme column length from 15 to 40.
 - Renamed Configuracion.r column to csrf_seed.
 - Universal cache invalidation for courses and programs on mutations.
 - Prevent caching of authenticated routes with CSRF protection.
 - Black formatting applied to recently modified files.

### Fixed:
 - Apply the database URL driver correction also when `DATABASE_URL` is overridden via environment variable in the application factory.
 - Fixed foreign key violation when creating certificate templates: the `usuario` field now correctly stores the username instead of the user ULID.
 - Fixed several tests that assigned the user ULID to foreign keys that reference `usuario.usuario` (username).
 - Fixed WTForms validation flow replacing `form.validate_on_submit() or request.method == "POST"` with strict `form.validate_on_submit()` in course, section, resource and program forms.
 - Fixed MasterClassForm template validation bypass when template ID was empty due to WTForms Optional validator.
 - Fixed Pago.monto precision/scale to prevent MySQL rounding (Numeric(10,2)).
 - Fixed certificate foreign key storing username in Certificado.usuario, Certificacion.usuario, ProgramaEstudiante.usuario and BlogPost.author_id.

## [1.2.4] - 2026-05-12

### Changed:
 - Maintenance release: update Python and JavaScript dependencies.

## [1.2.3] - 2026-01-19

### Changed:
 - Add unread messages in admin dashboard.
 - Updated contact form.

**IMPORTANT**: This version includes a database schema change. After updating, run database migrations:

```bash
# Using lmsctl (recommended)
lmsctl database migrate

# Or enable automatic migrations on startup
NOW_LMS_AUTO_MIGRATE=1 lmsctl serve

# Or using Flask-Alembic directly
flask db upgrade
```

## [1.2.2] - 2026-01-18

### Fixed:
 - Jinja2 errors in templates related to contac messages.

### Added:
 - Configuration toggle for Contact page in navbar: Admins can now enable/disable the Contact link in the navigation menu via System Configuration.
 - New `enable_contact` boolean field in `Configuracion` model (defaults to `False` for backward compatibility).
 - Cached helper function `is_contact_enabled()` to check Contact page visibility status.

### Changed:
 - Updated navbar template to conditionally render Contact link based on configuration setting.
 - Extended admin configuration UI with Contact toggle in Navigation Configuration section.

**IMPORTANT**: This version includes a database schema change. After updating, run database migrations:

```bash
# Using lmsctl (recommended)
lmsctl database migrate

# Or enable automatic migrations on startup
NOW_LMS_AUTO_MIGRATE=1 lmsctl serve

# Or using Flask-Alembic directly
flask db upgrade
```

## [1.2.1] - 2026-01-18

### Added:
 - Footer customization: Static pages can now be marked to appear in footer via `mostrar_en_footer` field.
 - Customizable footer links via "Enlaces Útiles" (Useful Links) admin interface.

### Fixed:
 - Fixed Alembic migrations not being loaded due to incorrect relative path configuration.
 - Fixed missing `mostrar_en_footer` field in default static pages creation.
 - Fixed `/admin/pages` route failing when database schema is outdated.

### Changed:
 - Updated Alembic configuration to use absolute path for migrations directory.
 - Updated CHANGELOG to document database schema changes introduced in v1.2.0.

**IMPORTANT**: This version fixes a critical bug where `alembic.upgrade()` would not execute migrations. If you upgraded to v1.2.0 and encountered errors accessing `/admin/pages`, upgrade to v1.2.1 and the migrations will run automatically if you have `NOW_LMS_AUTO_MIGRATE=1` set, or run:

```bash
# Using lmsctl (recommended)
lmsctl database migrate

# Or enable automatic migrations on startup
NOW_LMS_AUTO_MIGRATE=1 lmsctl serve

# Or using Flask-Alembic directly
flask db upgrade
```

## [1.2.0] - 2026-01-18

### Changed:
 - Refactor course module (no changes to user experience)

## [1.1.8] - 2026-01-16

### Fixed:
 - Fix course image display for non-JPG formats in admin and edit routes.

### Changed:
 - Auto-redirect to next resource after marking completion.
 - Add caching to blog views with automatic invalidation on content changes.


## [1.1.7.post1] - 2026-01-10

### Fixed:
 - Fix failing migrations
 - Added a unit that validates all migrations runs in all database engines

After updating, you must run database migrations:

```bash
# Using lmsctl:
lmsctl db upgrade

# Using alembic API:
from now_lms import lms_app, alembic
with lms_app.app_context():
    alembic.upgrade()
```

References:
 - https://github.com/bmosoluciones/now-lms/blob/main/docs/blog/posts/2026-01-10-alembic-sincronizacion-y-reinicio.md


## [1.1.7] - 2026-01-10

### Fixed
 - Fix failing migrations

## [1.1.6] - 2026-01-10

### Changed
 - Improved footer

## [1.1.5] - 2026-01-10

### Fixed
 - Fixed database migration.

**IMPORTANT**: This version includes a migration fix. After updating, you must run database migrations:
```bash
# Using lmsctl
lmsctl database upgrade

# Or using Fla directly
flask db upgrade
```

## [1.1.4] - 2026-01-10

### Changed
 - Collape course descrption in mobile view.
 - Update footer implementation.
 - Improve blog visual desing.


## [1.1.3] - 2026-01-09

### Fixed
 - Add missing database migration for `configuracion` table columns: `enable_file_uploads`, `max_file_size`, `enable_html_preformatted_descriptions`, and `enable_footer`

**IMPORTANT**: This version includes a migration fix. After updating, you must run database migrations:
```bash
# Using lmsctl
lmsctl database upgrade

# Or using Flask-Alembic directly
flask db upgrade
```

## [1.1.2] - 2025-01-09

### Added
 - Configurable social media links
 - Footer with static pages

### Changed
 - Improved admin menu

### Fixes
 - HTML errores


## [1.1.1] - 2025-01-05

### Fixes
 - Add missing `allow_unverified_email_login` in config menu

## [1.1.0] - 2025-01-05

### Added
- **Configurable Restricted Access for Unverified Email Users**
  - New administrator configuration option `allow_unverified_email_login` enables controlled access for users with unverified email addresses
  - When enabled, users can log in without email verification but with the following restrictions:
    - **Allowed**: Enroll in free courses, access course resources, complete evaluations, and earn certificates
    - **Restricted**: Enroll in paid courses, use discount coupons (including 100% off), post in forums, or send private messages
  - Flash messages inform users about their limited access status during login
  - Administrators can manually verify user emails from `/admin/users/list_inactive` via the new verification button
  - Manual verification by admin immediately activates the account and grants full access
  - Default behavior unchanged: unverified users are blocked by default (backward compatible, non-breaking change)

### Changed
- Login flow enhanced to support conditional access for unverified users based on system configuration
- Admin inactive users list now includes email verification functionality

### Database Migration Required
**IMPORTANT**: This version introduces database schema changes. After updating, you must run database migrations:
```bash
# Using lmsctl
lmsctl database upgrade

# Or using Flask-Alembic directly
flask db upgrade
```

Migration file: `now_lms/migrations/20260105_145517_add_allow_unverified_email_login.py`

The migration adds the `allow_unverified_email_login` column to the `configuracion` table with a default value of `False` to maintain backward compatibility.

## [1.0.5] - 2025-12-27

### Fixed
- Fix validation error when editing a course
- Fix HTML errors introduced in release 1.0.4

## [1.0.4] - 2025-11-23

### Changed:
 - Improved fedback in errors in forms

## [1.0.3] - 2025-10-29

### Changed
 - Updated default waitress setup.
 - Move to SQLAlchemy as flask-session backend.

## [1.0.2] - 2025-10-23

### Changed
- Uses waitress as the defaulf WSGI server.

## [1.0.1] - 2025-10-18

### Fixed
- Resolved session persistence issue in multi-process WSGI servers (Gunicorn, Waitress).
  Flask-Logins now initialized after Flask-Session to ensure proper session binding.

---------------------

## [1.0.0] - 2025-10-12

### Summary

NOW LMS version 1.0.0 is the first stable release. This release provides a complete learning management system built with Flask and Bootstrap 5, supporting course creation, user management, assessments, and certificates.

### Core Features

#### Course Management
- Course creation with section-based organization
- Multiple resource types: YouTube videos, PDFs, images, audio files, rich text, external HTML, slide presentations, and external links
- Support for free and paid courses
- Self-paced, instructor-led, and time-limited course modes
- Audit mode for paid courses (limited access without evaluations or certificates)
- Course grouping into programs
- Course library for browsing available courses

#### User Management and Access Control
- Role-based access control (Administrator, Instructor, Moderator, Student)
- User authentication with email confirmation
- User dashboards tailored by role
- Administrative user enrollment in courses and programs
- User profile management

#### Assessment and Certification
- Evaluation system with date-based availability
- Automatic grading and result display
- Certificate generation upon course completion
- QR code validation for certificate authenticity
- Support for course and program certificates
- Multiple certificate templates

#### Communication and Collaboration
- Internal messaging between students and instructors
- Course-specific discussion forums
- Announcement system for course-wide notifications
- Blog functionality with moderation and commenting

#### Calendar and Events
- User calendar showing course dates, live sessions, and evaluation deadlines
- Event detail pages with resource links
- Event export to iCalendar format
- Automatic event updates when resource dates change

#### Payment and Monetization
- PayPal payment integration
- Google AdSense support for free course monetization

#### Customization and Theming
- Multiple built-in themes
- Theme switching capability
- Custom favicon support
- Homepage override capability

#### Technical Features
- Database support: SQLite, PostgreSQL, MySQL, and MariaDB
- Configuration via environment variables or config files
- CLI tools for database initialization and user management
- Cache support: SimpleCache, NullCache, Redis, and Memcached
- Email notification system
- Health check endpoint
- Session management with multiple backend options
- Internationalization support (English, Spanish, Portuguese)
- Security features: CSRF protection, Argon2 password hashing, SQL injection prevention

### Quality Assurance

The release has been validated through:

- Test suite with 880+ automated tests (99% pass rate)
- Manual testing of all major features
- Multi-database backend validation
- Security testing for authentication and authorization
- Performance testing with concurrent users
- Code quality checks using Black, Flake8, and Ruff
- HTML validation and accessibility review

### System Requirements

- Python 3.11 or higher
- Compatible with Linux
- Supported databases: SQLite (included), PostgreSQL, MySQL, or MariaDB

### Known Limitations

- Audit mode for paid courses is partially implemented
- Some advanced reporting features are planned for future releases
- There is a problem handling the user session witg gunicorn, use waitress as WSGI server until the issue is fixed.

### Deployment

This release is available on PyPI and can be deployed using pip, Docker, or from source. Default credentials should be changed immediately in production environments.

-------------------

## Development History (Pre-1.0.0)

The entries below document the development history leading to version 1.0.0. These entries are archived for reference.

-------------------

## [ 0.0.1-rc02 ] - unreleased

### Fixed:
 - Administrative user enrollment.

### Changed:
 - Added a option to change the user type in the adminstrative user list.

### Added:
 - Course library.

-------------------

## [ 0.0.1-rc02 ] - 2025-09-18

### Changed:
 - Comprensive themes review.
 - Improved type hints.
 - Improved docs.

### Fixed:
 - HTML Errors.

-------------------

## [ 0.0.1-rc01 ] - 2025-09-13

### Changed:
 - Updated certificate validation page.
 - Added blog entry in navbar.

### Fixed:
 - Fixed access error to student certificates issued list.
 - Error en translation .po file.

-------------------

## [ 0.0.1b19.dev20250903 ] - 2025-09-10

### Changed:
 - Improved user dashboards.
 - Improved user profiles.
 - Improved project translation

### Notes:

Comprehensive verification that NOW LMS is ready for Release Candidate status by implementing systematic testing of all critical system components and documenting the readiness assessment.

#### What was verified

##### Core System Verification

- **Application startup**: Verified successful startup on Linux environments with proper initialization
- **Configuration system**: Tested environment variable loading, config file parsing, and override mechanisms
- **Database support**: Validated SQLite, PostgreSQL, MySQL, and MariaDB URL parsing and connection handling
- **Logging system**: Confirmed all logging levels (DEBUG, INFO, WARNING, ERROR, TRACE) work correctly
- **Cache backends**: Tested SimpleCache, NullCache, Redis, and Memcached fallback mechanisms

##### Functional Testing Results

- **Test suite performance**: 884/892 tests passed (99.1% success rate)
- **Code coverage**: 55% on core functionality with comprehensive route testing
- **User management**: Verified default admin user creation, authentication, and role-based access control
- **Course management**: Confirmed course creation, enrollment, and content delivery systems
- **Content systems**: Validated blog, forum, messaging, announcements, and certificate generation
- **Security**: Verified CSRF protection, password hashing (Argon2), and SQL injection prevention

##### Production Readiness Assessment

- **Performance**: Average response time < 200ms with stable concurrent request handling
- **CLI tools**: Verified Flask CLI integration with database and user management commands
- **Configuration flexibility**: Tested environment variables and config file loading from multiple locations
- **Code quality**: 100% compliance with Black formatting and Flake8 linting standards

##### Key Findings

The system demonstrates enterprise-grade stability with:

- Comprehensive test coverage (884 tests) with 99.1% pass rate
- Multi-database backend support with proper URL handling
- Flexible configuration system supporting both environment variables and config files
- Robust security implementation with modern password hashing and CSRF protection
- Well-documented CLI tools for administration and deployment
- Clean, maintainable codebase following Python best practices

-------------------

## [ release: v0.0.1b18.dev20250831 ] - 2025-08-31

### Fixed:
 - Fixed a critical error in the access logic to course resources, see: https://github.com/bmosoluciones/now-lms/issues/111

-------------------

## [ release: v0.0.1b17.dev20250831 ] - 2025-08-31

### Changed:
 - Improved courses page.
 - Improved programs page.
 - Improved administrative lists.

-------------------

## [ release: v0.0.1b19.dev20250903 ] - 2025-09-03

### Changed:
 - Custom HTML5 audio player with suppot for up to 2 subtitles files in .vtt format. See: 4b3460c729558990f65c38c851119c17c891f22a
 - Improved file uploads. See 1726f68891195ad2b34b08cd8bb0815ee620ed1e

-------------------

## [ release: v0.0.1b18.dev20250831 ] - 2025-08-31

### Fixed:
 - Fixed a critical error in the access logic to course resources, see: https://github.com/bmosoluciones/now-lms/issues/111

-------------------

## [ release: v0.0.1b17.dev20250831 ] - 2025-08-31

### Changed:
 - Improved courses page.
 - Improved programs page.
 - Improved administrative lists.

-------------------

## [ release: v0.0.1b17.dev20250831 ] - 2025-08-31

### Changed:
 - Improved courses page.
 - Improved programs page.
 - Improved administrative lists.

-------------------

## [ release: v0.0.1b16.dev20250830 ] - 2025-08-30

### Added:
 - Administrative user enrollment in programs and courses.

### Changed:
 - Improved course page.
 - Improved resources pages.
 - Improved list pages, see: 51fd1534c34f56479564a77b73899ea655f89e8

-------------------

## [ release: v0.0.1b15.dev20250830 ] - 2025-08-30

### Added:
 - View counter in blog posts.

### Fixed
 - Babel translation directory discovery.

-------------------

## [ release: v0.0.1b14.dev20250828 ] - 2025-08-28

### Added:
 - Define TESTING
 - Define FORCE_HTTPS

### Changed:
 - Merge alembic command group (db) into database

-------------------

## [release: v0.0.1b13.dev20250824] - 2025-08-24

### Fixed:
 - Fixed a issue system was issuing certificates without evaluations completions, see: 0f1947ca98340aa00c7e9303319afd1ce2cabd76
 - Fixed a issuer with the evaluation logic not checking certificate issuing after completing a evaluation, see: 7d7b1bf547011ed76b682eaa41e1e3013f7f5e04
 - Fixed blog editor with `mde` fields.
 - Fixed announcements delete route.

### Added:
 - Aditional certificate template

### Changed:
 - Configuration ca be loaded from a file.
 - `NOW_LMS_MEMORY_CACHE` can force the system to use a in memory shared cache.
 - In `/blog` strip HTML tags.
 - Updated admin page.

### Notes:

-------------------

## [release: v0.0.1b12.dev20250823] - 2025-08-23

### Added:
 - Page info route

### Changed:
 - Refactor meet and link resource pages
 - Manage certificate templates by tipe (program or course)
 - Improve CLI interface

### Fixed:
 - Fixed course admin navigation in small screens
 - Fixed missing get slideshow iid in jinja globls
 - Fixed navigation issues in resource administration
 - Fixed navegation in text resource type

### Notes
 - Updated docs
 - Updated tests
 - Many pylint issues fixed

-------------------

## [release: v0.0.1b11.dev20250822] - 2025-08-22

### Fixed:
 - Fixed a bug in the certificate implementation
 - Fixed a bug resources creation

### Notes:
 - Included pylint as defensive tool
 - 698 tests passed / 83% code coverage

-------------------

## [v0.0.1b10.dev20250822] -2025-08-22

Unreleased

-------------------

## [v0.0.1b9.dev20250818] -2025-08-18

### Added:
- Self learning course.
- Default blog post.
- `get_one_from_db` Jinja global
- `get_all_from_db` Jinja global
- Demo courses: HTML, Python and Postgresql


### Changed:
- Force tests to always run on memory.
- Better audit trial
- Updated code base to use Python 3.11 features
- Tags and categories improved.
- Programs feature review.

### Notes:
- 509 tests passed / 4 skpped / 77% code coverage

-------------------

## [v0.0.1b8.dev20250816] - 2025-08-17

### NOW-LMS Smoke Test Checklist (Release Candidate)

#### Authentication & Access Control
* [x] Login with valid credentials works correctly.
* [x] Login with invalid credentials shows an appropriate error.
* [x] Logout works and ends the session.
* [x] New user registration with email confirmation works.
* [x] Roles (Admin, Instructor, Student, Moderator) have correct access to views.

#### Courses & Enrollment
* [x] Instructor can create a new course with sections and resources.
* [x] Student can enroll in a free course.
* [x] Student cannot access a paid course without payment.
* [x] Enrolled courses appear correctly in the student dashboard.
* [x] Course resources (PDF, video, external links, images) load correctly.

#### Calendar & Events
* [x] Enrolling in a course generates calendar events (meets, evaluation deadlines).
* [x] Events appear in `/user/calendar` with correct timezone.
* [x] Upcoming events appear in the user dashboard.
* [x] If a meet or evaluation resource date changes, the user calendar reflects the update.
* [x] Exporting events as `.ics` works and keeps events private.
* [x] Event detail page correctly shows event type (Meet/Evaluation) and link to resource.

#### Evaluations
* [x] Student can access an active evaluation.
* [x] Student cannot access an evaluation outside its valid date.
* [x] Evaluation submission is graded correctly and results are displayed.

#### Certificates
* [x] Certificate is generated upon course completion.
* [x] QR code on the certificate validates successfully.

#### Communication
* [x] Internal messaging works between student ↔ instructor.
* [x] Course discussion forums allow creating and replying to threads.
* [x] Course announcements are visible to all enrolled users.

#### Payments & Monetization
* [x] PayPal payment for paid course works in sandbox mode.
* [ ] “Audit mode” for paid courses limits access to evaluations/certificates.
* [x] Google AdSense loads in free courses (if configured).

#### UI & Theming
* [x] Homepage loads with the active theme.
* [x] Changing the theme in settings applies correctly.

#### System & Stability
* [x] `/health` page responds with 200 (if available).
* [x] Cache works (repeated loads are faster).
* [x] Logs are generated without unexpected errors.
* [x] Basic navigation (Home → Login → Dashboard → Course → Resource) works without 500 errors.

### Changed:
- Improved markdown to hmtl.
- Update default MySQL driver.
- `/health` check status route.
- Conditional check `is_blog_enabled`.
- Add `default` certificate template.

-------------------

## [v0.0.1b6.dev20250815] - 2025-08-15

### Added:
- **Golden Theme**: A yellow/orange based theme.
- **Custom Favicon**: Can set a custom favicon in themes.
- **Golden Theme**: A yellow/orange based theme.
- **Custom Favicon**: Can set a custom favicon in themes.

-------------------

## [v0.0.1b5.dev20250810] - 2025-08-10

### Added:
- **User Calendar** feature: Users can now view key course dates such as live sessions (`meet`) and evaluation deadlines in a personal monthly calendar view (`/user/calendar`).
- Event detail page displaying information based on type (`meet` or `evaluation`) with a direct link to the associated resource.
- Automatic event updates when a resource or evaluation date changes, executed in the background using lightweight threads to improve performance and avoid external dependencies.

### Changed:
- Added Calendar feature

### Code Quality:
- Python code formatted with **Black**.
- HTML templates formatted with **Prettier**.
- Current test coverage: **70%** (`174 passed`, `4 skipped`, `12 warnings`).

### Notes:
- Ongoing validation

-------------------

## [v0.0.1b3.dev20250809] - 2025-08-09

### Added
- Implemented **Master Class** module with full support for creation, enrollment, and content delivery.
- Integrated Master Class access control for enrolled students only.
- Added unit tests for Master Class registration and access flows.

### Changed
- Expanded test suite to **131 unit tests** (**4 skipped**, **5 warnings**), execution time **26.79s**.
- Increased code coverage to **70%**.
- Prioritized testing for authentication, payments, enrollment, and content access modules.

### Notes
- Project remains in **Beta** — no new features will be added except for Master Class (special exception).
- Focus remains on testing and system stability before the stable release.

-------------------

## [v0.0.1b2.dev20250808] - 2025-08-08

### Added:
- NOW - LMS has reached **Beta** status. The system now includes all planned features for the initial release:
  - Complete course management: creation, organization by sections, and multiple resource types (video, PDF, audio, external HTML, rich text, etc.).
  - Automatic certificate generation upon course completion, with QR code validation.
  - Course types: free or paid, self-paced, synchronous, or time-limited.
  - Audit mode for paid courses, providing limited access without certificate eligibility.
  - Role-based access control: administrator, instructor, moderator, and student.
  - Internal messaging system between students and instructors.
  - Course-specific discussion forums.
  - Announcement system.
  - Assessment and certification tools.
  - Blog functionality with administrator moderation.
  - Course grouping into programs.
  - PayPal payment integration.
  - Monetization of free courses via Google AdSense.
  - Theming system for portal customization.
  - Email notification system.

### Changed:
- Final consolidation and review of all features for the initial release.
- No new features will be added until the stable release.

### Status:
- The system enters **testing phase** (beta). Focus is on quality assurance, manual and automated testing to ensure system stability.
