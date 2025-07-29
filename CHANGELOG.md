# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),  
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

> This project also follows [Conventional Commits](https://www.conventionalcommits.org/), using prefixes such as:  
> `fix:`, `feat:`, `refactor:`, `release:`, `docs:`, `build:`, `ci:` to clearly describe changes.


## [v0.0.1a2.dev20250729] - 2025-07-29

### Added
- Full integration with Google AdSense across public-facing pages (homepage, course pages, and student dashboard)
- Initial implementation of PayPal Checkout for paid course enrollment (in sandbox/testing mode)
- System automatically creates and confirms PayPal orders, registers successful enrollments, and issues receipts

### Changed
- Minor UI refactors to support advertisement blocks and sponsored content
- Theme rendering updated to accommodate monetization components

### In Progress
- Manual and automated testing of PayPal payment flow
- Google AdSense optimization and responsive behavior

### Notes
- This release focuses on enabling revenue generation features
- Monetization functionality is currently in an experimental state

---

## [v0.0.1a1.dev20250728] - 2025-07-28

### Added
- 7 functional themes added to the application: `cambridge_classic`, `corporative_finance`, `harvard`, `now_lms`, `ocean_blue`, `oxford`, `rose_pink`

---

## [v0.0.1a1.dev20250725] - 2025-07-25

### Added
- Complete rework of the theming system
- Documentation for graphic designers to create custom themes
- End-to-end testing setup for core application flows

---

## [v0.0.1a1.dev20250724] - 2025-07-24

### Added
- Users can change their password from their profile
- Password reset flow via email token if email is verified
- 5 additional visual themes for homepage customization

### Changed
- Upgraded SQLAlchemy to the latest stable version
- Code coverage improved from ~70% to 74%

### Fixed
- Course creation form error when cover image not attached
- Course edit page now displays the cover ima


## [v0.0.1a1.dev20250720] - 2025-07-20

### Added
- Functional user registration with email confirmation and secure login
- Role-based access control (Admin, Instructor, Moderator, Student)
- Instructor panel for course creation and editing (with reusable template)
- Public course viewer for students
- Enrollment flow for free courses
- Course content viewer with progress tracking by resource
- Support for video, audio, PDF, plain text, embedded HTML, and Google Meet
- File upload support for course resources
- Full theming support for homepage and application skin
- Automatic certificate issuance upon 100% course completion
- Online certificate viewer and downloadable PDF with QR validation
- End-to-end test: full flow from registration to certification
- Code coverage setup with ~70% test coverage via unit tests

### Fixed
- Restricted access to role-specific views (e.g. students can't access admin pages)
- Account activation required for login (blocked unverified users)

### Upcoming
- MySQL database support
- Integration with PayPal for paid course enrollments
- Workflow for enrollment in paid courses
- Instructor dashboard and analytics
- Student dashboard with progress overview
- Support for quizzes, assignments, forums, and downloadable materials
- Improved file storage system and moderation tools

---
