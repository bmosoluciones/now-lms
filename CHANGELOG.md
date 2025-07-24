# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),  
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

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

