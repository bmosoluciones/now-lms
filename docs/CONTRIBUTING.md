# Contributing with NOW Learning Management System.

[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](http://makeapullrequest.com)
![GitHub top language](https://img.shields.io/github/languages/top/bmosoluciones/now-lms)
![GitHub language count](https://img.shields.io/github/languages/count/bmosoluciones/now-lms)
![GitHub contributors](https://img.shields.io/github/contributors/bmosoluciones/now-lms)
![GitHub last commit](https://img.shields.io/github/last-commit/bmosoluciones/now-lms)
![GitHub issues](https://img.shields.io/github/issues/bmosoluciones/now-lms)
![GitHub pull requests](https://img.shields.io/github/issues-pr-raw/bmosoluciones/now-lms)

[![SonarCloud](https://sonarcloud.io/images/project_badges/sonarcloud-black.svg)](https://sonarcloud.io/dashboard?id=bmosoluciones_now-lms)

Thank you for your interest in collaborating with NOW Learning Management System. (the project).

## Project License.

NOW LMS is free and open source software released under the Apache Version 2 license (the [license](https://github.com/bmosoluciones/now-lms/blob/main/LICENSE) of the proyect), this means that project users can:

* Use the project for profit or not.
* Modify the project to fit theirs specific needs (clearly defining the changes made to the original project).

However, users cannot:

* Make use of the project trademarks without explicit permission.
* Require warranties of any kind; the project is distributed as is without guarantees that it may be useful for any specific purpose.

## Certify the origin of your contributions.

To incorporate your contributions to the project we require that you certify that the contribution or contributions are your property or that you have permission from third parties to incorporate the contribution or contributions to the project, following the [developer certificate of origin](https://developercertificate.org/).

We recommend running:

```bash
git commit -s
```

And an appropriate signature will be added to the commit, not included in the commits project without the corresponding Sing-Off.

## Collaborating with the project:

### Ways to collaborate.

You can collaborate in different ways:

* As a developer.
* As a Quality Assurance (QA).
* [Writing and improving documentation](https://bmosoluciones.github.io/now-lms/).
* [Contributing ideas of new characteristics.](https://github.com/bmosoluciones/now-lms/discussions)
* [Reporting bugs.](https://github.com/bmosoluciones/now-lms/issues)
* Translating.
* Providing guidance and support to other users.
* Sharing the project with others.

### Collaborating with the development of the project:

The development is cross-platform, you can use both Windows, Linux or Mac to contribute the project, to collaborate with the project you need:

  * [GIT](https://git-scm.com/)
  * [Yarn](https://yarnpkg.com/lang/en/)
  * [Python](https://www.python.org/downloads/)

Minimal Python version is: >=3.6

Technologies used:

* Backend: [Flask](https://flask.palletsprojects.com/en/1.1.x/).
* Frontend: [Bootstrap 5](https://v5.getbootstrap.com/).
* ORM: [SQLAlchemy](https://www.sqlalchemy.org/).

Development is done in the branch ```development```, once the project is released for production the branch ```main``` will contain the latest version suitable for use in production.

### Getting the source code

```
git clone https://github.com/bmosoluciones/now-lms.git
```
### Create a python virtual env

```
python3 -m venv venv
# Linux:
source venv/bin/activate
# Windows
venv\Scripts\activate.bat
```
### Install python deps

```
python3 - m pip install -r development.txt
```

### Install Boostrap

```
 cd now_lms/static/
 npm install
```

### Start a development server

```
hupper -m now_lms
```
Please note that we use waitress as WSGI server because gunicorn do not work on Windows, hupper will live reload the WSGI server as you save changes in the source code so you will be able to work with your changes as you work, please note that changes to the jinja templates will not trigger the server reload, only changes to python files.

Default user and password are ```lms-admin```, default url to work with th server will be ```http://127.0.0.1:8080/```.

Note that the reloader will setpup a new database with any code change, if you do not want a fresh database any time you save a change you can set to True the ```NO_RESET_DATABASE``` as follow:

```
NO_RESET_DATABASE=True hupper -m now_lms
```

#### Style Guide:

[PEP8](https://www.python.org/dev/peps/pep-0008/) with a maximum line length of 127 characters.
