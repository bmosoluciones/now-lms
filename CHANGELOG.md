# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),  
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

> This project also follows [Conventional Commits](https://www.conventionalcommits.org/), using prefixes such as:  
> `fix:`, `feat:`, `refactor:`, `release:`, `docs:`, `build:`, `ci:` to clearly describe changes.

## [unreleased]

- Update default MySQL driver

## [v0.0.1b6.dev20250815] - 2025-08-15

### Added
- **Golden Theme**: A yellow/orange based theme.
- **Custom Favicon**: Can set a custom favicon in themes.

## [v0.0.1b5.dev20250810] - 2025-08-10

### Added
- **User Calendar** feature: Users can now view key course dates such as live sessions (`meet`) and evaluation deadlines in a personal monthly calendar view (`/user/calendar`).
- Event detail page displaying information based on type (`meet` or `evaluation`) with a direct link to the associated resource.
- Automatic event updates when a resource or evaluation date changes, executed in the background using lightweight threads to improve performance and avoid external dependencies.

### Changed
- Added Calendar feature

### Code Quality
- Python code formatted with **Black**.
- HTML templates formatted with **Prettier**.
- Current test coverage: **70%** (`174 passed`, `4 skipped`, `12 warnings`).

### Notes
- Ongoing validation

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


## [v0.0.1b2.dev20250808] - 2025-08-08

### Added
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

### Changed
- Final consolidation and review of all features for the initial release.
- No new features will be added until the stable release.

### Status
- The system enters **testing phase** (beta). Focus is on quality assurance, manual and automated testing to ensure system stability.

