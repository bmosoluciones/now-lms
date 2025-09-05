# Changelog

All notable changes to this project will be documented in this file.

- The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
- This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
- This project also follows [Conventional Commits](https://www.conventionalcommits.org/).


## [ unreleased ]

### Changed:
 - Improved user dashboards.

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
