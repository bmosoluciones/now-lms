# NOW - Learning Management System

![PyPI - License](https://img.shields.io/pypi/l/now_lms?color=brightgreen&logo=apache&logoColor=white)
![PyPI](https://img.shields.io/pypi/v/now_lms?color=brightgreen&label=version&logo=python&logoColor=white)
![PyPI - Wheel](https://img.shields.io/pypi/wheel/now_lms?logo=python&logoColor=white)
[![Docker Repository on Quay](https://quay.io/repository/bmosoluciones/now_lms/status "Docker Repository on Quay")](https://quay.io/repository/bmosoluciones/now_lms)
[![codecov](https://codecov.io/github/bmosoluciones/now-lms/graph/badge.svg?token=SFVXF6Y3R3)](https://codecov.io/github/bmosoluciones/now-lms)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=bmosoluciones_now-lms&metric=alert_status)](https://sonarcloud.io/dashboard?id=bmosoluciones_now-lms)
[![Code style: black](https://img.shields.io/badge/Python%20code%20style-black-000000.svg)](https://github.com/psf/black)
[![Code style: Prettier](https://img.shields.io/badge/HTML%20code%20style-prettier-ff69b4.svg)](https://github.com/prettier/prettier)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Join the chat at https://gitter.im/now-lms/community](https://badges.gitter.im/now-lms/community.svg)](https://gitter.im/now-lms/community?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

![Logo](https://github.com/bmosoluciones/now-lms/blob/main/now_lms/static/icons/logo/logo_large.png?raw=true)

A simple-to-{install, use, configure, monetize, and maintain} learning management system.

![ScreenShot](https://raw.githubusercontent.com/bmosoluciones/now-lms/main/docs/images/screenshot.png)

## Documentation

-   Course Creators, refer to the [ourse creation doc](https://bmosoluciones.github.io/now-lms/course-creator/).
-   System Administrators, refer to the [documentation](https://bmosoluciones.github.io/now-lms/index.html).

Live demo: https://now-lms-demo.onrender.com/

```
User: lms-admin
Password: lms-admin
```

Data in the live demo is reset on every deployment. Please wait for the free Render instance to wake up.


## Getting Started

Thanks for your interest in the NOW - LMS project (the project).

### Stack

- Backend: Python with Flask microframework
- Frontend: Boostrap with Alpine.js
- ORM: Sqlalchemy

### Dependencies

-   Requires python >= 3.11
-   Requires minimal resources to run

### Quick Start

To start a local server, simply execute:

```
python3 -m venv venv
source venv/bin/activate
python -m pip install now_lms
python -m now_lms
```

Visit `http://127.0.0.1:8080/` in your browser, the default user and password are `lms-admin`.
Note: the default server binds only to localhost. You can test the software locally. If you want to deploy NOW-LMS for production use, please check the [user manual](https://bmosoluciones.github.io/now-lms/setup.html).

### Features

NOW - LMS is designed to be simple yet powerful. Here are its key features:

- **Clean codebase**: Python and HTML5.
- **Compatible with multiple databases**: SQLite, PostgreSQL, and MySQL.
- **Complete course creation functionality**, allowing full curriculum setup.
- **Courses are organized into sections**, which group resources in a logical manner.
- **Flexible resource types** within a course section:
  - YouTube videos
  - PDFs
  - Images
  - Audio files
  - Rich text content
  - External HTML pages
  - Slide presentations
  - External resource links
- **Course types**:
  - Free or paid
  - Self-paced, synchronous (with tutor), or time-limited
- **Paid courses support an audit mode**, allowing limited access without evaluations or a certificate.
- **Certificate generation** upon course completion, exportable as PDF.
  - Includes **QR code validation** for authenticity.
- **Role-based access control**:
  - Admin
  - Instructor
  - Moderator
  - Student
- **Internal messaging system** for students to contact instructors and course moderators.
- **Discussion forums** integrated per course.
- **Announcement system** for course-wide notifications.
- **Assessment tools** for quizzes and evaluations.
- **Basic blog functionality** for content publishing.
- **Courses can be grouped into programs**.
- **Payment integration via PayPal**.
- **Monetization of free courses** through Google AdSense.
- **Theming and customization**:
  - Easily switch themes
  - Fully override the home page if needed
- **Email notification system** for important events and updates.

## Licence

**Apache License 2.0**: a permissive open-source license that allows anyone to freely use, modify, and distribute software, including for commercial purposes, as long as copyright and license notices are preserved. It also provides an explicit patent grant to protect users from patent claims but terminates rights if you sue over patents. While you can combine Apache-licensed code with proprietary software, you cannot use Apache trademarks or logos without permission, and you must give proper attribution to the original authors.

## Contributing

Thanks for your interest in contributing to the NOW-LMS project. Please note that this is an open-source project, so your contribution will be available to others for free under the terms of the Apache License. Refer to the [CONTRIBUTING](https://github.com/bmosoluciones/now-lms/blob/main/docs/CONTRIBUTING.md) file to get started.

## Logo

The NOW - LMS logo was developed by  [Muhammad Nabeel A.](https://www.freelancer.es/projects/logo-design/Logo-desing-for-Open-Source/).

-----------------------------------
Made with ❤️ and [gallo pinto](https://es.wikipedia.org/wiki/Gallo_pinto) in Nicaragua 🇳🇮
