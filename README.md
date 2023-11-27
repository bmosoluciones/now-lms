# NOW - Learning Management System

![PyPI - License](https://img.shields.io/pypi/l/now_lms?color=brightgreen&logo=apache&logoColor=white)
![PyPI](https://img.shields.io/pypi/v/now_lms?color=brightgreen&label=version&logo=python&logoColor=white)
![PyPI - Wheel](https://img.shields.io/pypi/wheel/now_lms?logo=python&logoColor=white)
[![Docker Repository on Quay](https://quay.io/repository/bmosoluciones/now_lms/status "Docker Repository on Quay")](https://quay.io/repository/bmosoluciones/now_lms)
[![Code style: black](https://img.shields.io/badge/Python%20code%20style-black-000000.svg)](https://github.com/psf/black)
[![Code style: Prettier](https://img.shields.io/badge/HTML%20code%20style-prettier-ff69b4.svg)](https://github.com/prettier/prettier)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![codecov](https://codecov.io/gh/bmosoluciones/now-lms/branch/main/graph/badge.svg?token=SFVXF6Y3R3)](https://codecov.io/gh/bmosoluciones/now-lms)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=bmosoluciones_now-lms&metric=alert_status)](https://sonarcloud.io/dashboard?id=bmosoluciones_now-lms)
[![Join the chat at https://gitter.im/now-lms/community](https://badges.gitter.im/now-lms/community.svg)](https://gitter.im/now-lms/community?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

![Logo](https://github.com/bmosoluciones/now-lms/blob/main/now_lms/static/icons/logo/logo_large.png?raw=true)

Simple to {install, use, configure and maintain} learning management system.

![ScreenShot](https://raw.githubusercontent.com/bmosoluciones/now-lms/main/docs/images/screenshot.png)

## Documentation

[![Documentation Status](https://readthedocs.org/projects/now-lms-manual/badge/?version=latest)](https://now-lms-manual.readthedocs.io/en/latest/?badge=latest)

-   Users please refer to the [user manual](https://now-lms-manual.readthedocs.io/en/latest/).
-   System Administrators refer to the [documentation](https://bmosoluciones.github.io/now-lms/index.html).
-   Live demo at: https://now-lms-demo.onrender.com/index

Data in the live demo is reset in every deployment, user and password are: `lms-admin`

## Getting Started

Thanks for your interest in the NOW - LMS project (the project).

### Dependencies

-   Requires python >= 3.8
-   Runs on Linux and Windows
-   Requires very low resources to run

### Quick Start

To star a local server just execute:

```
python3 -m venv venv
# Linux:
source venv/bin/activate
# Windows
venv\Scripts\activate.bat
# Install NOW Learning Managenet System
python -m pip install now_lms
# Execute the build in server
python -m now_lms
```

Visit http://127.0.0.1:8080/ in your browser, the default user and password are `lms-admin`, note that the default server is only bind to the localhost. You can test the software in your local machine, if you want to deploy NOW-LMS for production use please check de [user manual](https://bmosoluciones.github.io/now-lms/setup.html).

## Contributing

Thanks for your interest in contributing with the NOW-LMS project, please note that this is a open source projects so your contribution will be available to others for free under the terns of the Apache License, please refers to the [CONTRIBUTING](https://github.com/bmosoluciones/now-lms/blob/main/docs/CONTRIBUTING.md) file to start.

## Logo

The NOW - LMS logo was developeb by [Muhammad Nabeel A.](https://www.freelancer.es/projects/logo-design/Logo-desing-for-Open-Source/).
