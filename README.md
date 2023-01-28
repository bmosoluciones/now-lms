![Logo](https://raw.githubusercontent.com/bmosoluciones/now-lms/main/now_lms/static/icons/logo/logo_small.png)

# NOW - Learning Management System
![PyPI - License](https://img.shields.io/pypi/l/now_lms?color=brightgreen&logo=apache&logoColor=white)
![PyPI](https://img.shields.io/pypi/v/now_lms?color=brightgreen&label=version&logo=python&logoColor=white)
![PyPI - Wheel](https://img.shields.io/pypi/wheel/now_lms?logo=python&logoColor=white)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![linting: pylint](https://img.shields.io/badge/linting-pylint-yellow)](https://github.com/PyCQA/pylint)
[![codecov](https://codecov.io/gh/bmosoluciones/now-lms/branch/main/graph/badge.svg?token=SFVXF6Y3R3)](https://codecov.io/gh/bmosoluciones/now-lms)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=bmosoluciones_now-lms&metric=alert_status)](https://sonarcloud.io/dashboard?id=bmosoluciones_now-lms)
[![Join the chat at https://gitter.im/now-lms/community](https://badges.gitter.im/now-lms/community.svg)](https://gitter.im/now-lms/community?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

Simple to {install, use, configure and maintain} learning management system.

Students and Educators using NOW-LMS please refer the [user manual](https://bmosoluciones.github.io/now-lms/).

## Getting Started
Thanks for your interest in the Now - LMS project (the project).

### Dependencies

* Requires python >= 3.7
* Runs on Linux and Windows
* Requires very low resources to run

### Quick Start

To star a local server just execute:

```
python3 -m venv venv
# Linux:
source venv/bin/activate
# Windows
venv\Scripts\activate.bat
python -m pip install now_lms
python -m now_lms
```

Visit http://127.0.0.1:8080/ in your browser, default user and password are `lms-admin`, note that the default server is only bind to the localhost. You can test the software in your local machine, if you want to deploy NOW-LMS for production use please check de [user manual](https://bmosoluciones.github.io/now-lms/).

### Other deployment options

There are templates available to deploy Now - LMS to these [PAID] services:

[![Deploy to DO](https://img.shields.io/badge/DO-Deploy%20to%20DO-blue "Deploy as Digital Ocean App")](https://cloud.digitalocean.com/apps/new?repo=https://github.com/bmosoluciones/now-lms/tree/main)
[![Deploy to Heroku](https://img.shields.io/badge/Heroku-Deploy%20to%20Heroku-blueviolet "Deploy to Heroku")](https://heroku.com/deploy?template=https://github.com/bmosoluciones/now-lms/tree/heroku)

On [render](https://render.com/) you can host NOW-LMS for free, just set your project settings as follow:

```
Build Command: pip install -r requirements.txt && cd now_lms/static/ && npm install
Start Command: python -m now_lms
```

Important: You can test NOW-LMS for free on Render, but with the default configuration NOW LMS will use a SQLite database as data store, this database is not goin to persist after system upgrades, to keep your data safe ve sure to set the next enviroment variables:

```
NO_RESET_DATABASE=True
DATABASE_URL=proper_db_connet_string
```

Note that you can host a tiny up to 20MB PostgreSQL database for free in [elephantsql](https://customer.elephantsql.com/instance).


### OCI Image

[![Docker Repository on Quay](https://quay.io/repository/bmosoluciones/now_lms/status "Docker Repository on Quay")](https://quay.io/repository/bmosoluciones/now_lms)

There is also a OCI image disponible if you prefer to user containers, in this example we use [podman](https://podman.io/):

```
# <---------------------------------------------> #
# Install the podman command line tool.
# DNF family (CentOS, Rocky, Alma):
sudo dnf -y install podman

# APT family (Debian, Ubuntu):
sudo apt install -y podman

# OpenSUSE:
sudo zypper in podman


# <---------------------------------------------> #
# Run the software.
# Create a new pod:
podman pod create --name now-lms -p 80:80 -p 443:443

# Database:
podman run --pod now-lms --rm --name now-lms-db --volume now-lms-postgresql-backup:/var/lib/postgresql/data -e POSTGRES_DB=nowlearning -e POSTGRES_USER=nowlearning -e POSTGRES_PASSWORD=nowlearning -d postgres:13

# App:
podman run --pod now-lms --rm --name now-lms-app -e LMS_KEY=nsjksldknsdlkdsljdnsdjñasññqldñaas554dlkallas -e LMS_DB=postgresql+pg8000://nowlearning:nowlearning@localhost:5432/nowlearning -e LMS_USER=administrator -e LMS_PSWD=administrator -d quay.io/bmosoluciones/now-lms

# Web Server
# Download nginx configuration template:
cd
mkdir now_lms_dir
cd now_lms_dir
curl -O https://raw.githubusercontent.com/bmosoluciones/now-lms/main/docs/nginx.conf

# In the same directoy run the web server pod:
podman run --pod now-lms --name now-lms-server --rm -v $PWD/nginx.conf:/etc/nginx/nginx.conf:ro -d nginx:stable 

```

NOW-LMS also will work with MySQL or MariaDB just change the image of the database container and set the correct connect string. SQLite also will work if you will serve a few users.

## Contributing
Thanks for your interest in contributing with the NOW-LMS project, please note that this is a open source projects so your contribution will be available to others for free under the terns of the Apache License, please refers to the [CONTRIBUTING](https://github.com/bmosoluciones/now-lms/blob/main/docs/CONTRIBUTING.md) file to start.
