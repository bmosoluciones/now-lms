# Welcome to the NOW - Learning Management System documentation.

The main objetive of NOW - LMS is to be a simple to {install, use, configure,
mantain} learning management system (LMS).

![Logo](images/logo.svg)

Online education can be used as a primary source of knowledge or as a reinforcement method.

!!! info
NOW LMS version 1.0.0 is the first stable release, ready for production use.

## First Steps

NOW-LMS is available as a Python Package in [Pypi](https://pypi.org/project/now-lms/), to run it you just have a recent Python interpreter and run the following commands:

```
# Python >= 3.11
python3 -m venv venv
venv/bin/pip install now_lms
venv/bin/lmsctl database init
venv/bin/lmsctl serve
```

Visit `http://127.0.0.1:8080` in your browser and login with the default user and password: `lms-admin`.

This will install NOW - LMS from the [Python Package Index](https://pypi.org/project/now-lms/) with a local WSGI server and SQlite as database backend, for really tiny septups or testing this can work, for a most robust deployment suitable for many users refers to the [setup guide](setup.md).

## Server Administration

For production deployments, comprehensive server administration best practices are available:

- **[Ubuntu/Debian Server Administration](server-admin-ubuntu.md)** - Complete guide for Ubuntu and Debian-based systems including security hardening, monitoring, backup strategies, and performance optimization.

- **[RHEL/Alma/Rocky/Fedora Server Administration](server-admin-rhel.md)** - Comprehensive guide for Red Hat Enterprise Linux, AlmaLinux, Rocky Linux, Amazon Linux, and Fedora systems with SELinux configuration, firewalld setup, and enterprise security practices.

- **[Rocky Linux Quick Setup](rocky.md)** - Quick deployment guide for EL9 systems.

NOW-LMS aims to offers a full online learning experience and is influenced by [others project](references.md).
