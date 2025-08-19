# Welcome to the NOW - Learning Management System documentation.

The main objetive of NOW - LMS is to be a simple to {install, use, configure,
mantain} learning management system (LMS).

![Logo](images/logo.svg)

Online education can be used as a primary source of knowledge or as a reinforcement method.

!!! warning
    This is alpha software!

## First Steps

NOW-LMS is available as a Python Package in [Pypi](https://pypi.org/project/now-lms/), to run it you just have a recent Python interpreter and run the following commands:

```
# Python >= 3.11
python3 -m venv venv
source venv/bin/activate
python -m pip install now_lms
python -m now_lms
```

Visit `http://127.0.0.1:8080` in your browser and login with the default user and password: `lms-admin`.

This will install NOW - LMS from the [Python Package Index](https://pypi.org/project/now-lms/) with a local WSGI server and SQlite as database backend, for really tiny septups or testing this can work, for a most robust deployment suitable for many users refers to the [setup guide](setup.md).

NOW-LMS aims to offers a full online learning experience and is influenced by [others project](references.md).
