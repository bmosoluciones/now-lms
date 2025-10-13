# Release a new version of NOW - LMS.

NOW - LMS uses [pypi](https://pypi.org/) as the final releases host, the release proccess is done
via a github action than will publish to pypi commits that start with the `release: v` text and are
made to the main branch of the project. The `main` branch is protected to avoid unwanted releases.

Commits should be marked as final releases only after continuous integration testing proccess are
pased.

Release history can be found here: [https://pypi.org/project/now-lms/#history](https://pypi.org/project/now-lms/#history)

Change log can be found in the [change log file](https://github.com/bmosoluciones/now-lms/blob/main/CHANGELOG.md).

Source code is hosted at [github](https://github.com/bmosoluciones/now-lms).

## Version 1.0.0 - First Stable Release

Version 1.0.0 represents the first stable release of NOW LMS. This release has been validated through:

- Comprehensive automated testing (880+ tests with 99% pass rate)
- Multi-database backend validation (SQLite, PostgreSQL, MySQL, MariaDB)
- Security testing and code quality verification
- Manual testing of all major features
- Performance testing with concurrent users

The system is ready for production deployment. Default credentials should be changed immediately in production environments.
