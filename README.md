![Logo](https://raw.githubusercontent.com/bmosoluciones/now-lms/main/now_lms/static/icons/logo_small.png)

# NOW - Learning Management System
[![codecov](https://codecov.io/gh/bmosoluciones/now-lms/branch/main/graph/badge.svg?token=SFVXF6Y3R3)](https://codecov.io/gh/bmosoluciones/now-lms)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=bmosoluciones_now-lms&metric=alert_status)](https://sonarcloud.io/dashboard?id=bmosoluciones_now-lms)

Simple to {install, use, configure, mantain} learning management system.

## Getting Started

### Dependencies

* Requires python >= 3.7
* Runs on Linux and Windows

### Installing

```
python3 -m venv venv
# Linux:
source venv/bin/activate

pip install now_lms

```

### Executing program

You can use the lmsctl command to star the system.

```
export LMS_USER=ADMINUSER  # default: lms-admin
export LMS_PSWD=ADMINPASSWORD  # default: lms-admin
export LMS_KEY=v3rys3cr3tkey!d0n0tsh@are
lmsctl setup
lmsctl serve
```
Visit http://127.0.0.1:8080/ in your browser, note that the default server is olny bind to localhost.
