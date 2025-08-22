# Copyright 2025 BMO Soluciones, S.A.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


"""Command line interface for NOW LMS."""

# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------
from os import cpu_count, environ
from pathlib import Path

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------
import click
from flask.cli import FlaskGroup
from sqlalchemy import select

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms import alembic, initial_setup, lms_app
from now_lms.cache import cache
from now_lms.config import DESARROLLO
from now_lms.db import database as db
from now_lms.db import eliminar_base_de_datos_segura
from now_lms.db.info import config_info, course_info
from now_lms.logs import log
from now_lms.version import CODE_NAME, VERSION


# ---------------------------------------------------------------------------------------
# Interfaz de linea de comandos.
# ---------------------------------------------------------------------------------------
@click.group(
    cls=FlaskGroup, create_app=lambda: lms_app, help="Interfaz de linea de comandos para la administración de NOW LMS."
)
def command() -> None:  # pragma: no cover
    """Linea de comandos para administración de la aplicacion."""


@lms_app.cli.group()
def database():
    """Database administration tools."""


@database.command()
@click.option("--with-examples", is_flag=True, default=False, help="Load example data at setup.")
@click.option("--with-testdata", is_flag=True, default=False, help="Load data for testing.")
def init(with_examples=False, with_testdata=False):  # pragma: no cover
    """Init a new database."""
    with lms_app.app_context():
        from now_lms.db.tools import database_is_populated

        if not database_is_populated(lms_app):

            initial_setup(with_examples)
            if with_testdata:
                from now_lms.db.data_test import crear_data_para_pruebas

                crear_data_para_pruebas()
        else:
            log.info("Database already initialised.")


@database.command()
def seed():
    """Set up a new develoment database."""
    from now_lms.db.data_test import crear_data_para_pruebas

    with lms_app.app_context():
        initial_setup(with_examples=True)
        crear_data_para_pruebas()


@database.command()
def backup():  # pragma: no cover
    """Make a backup of system data."""
    from now_lms.db.backup import db_backup

    db_backup()


@database.command()
@click.argument(
    "backup_sql_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True, path_type=Path),
)
def restore(backup_sql_file: Path):  # pragma: no cover
    """Restore the system from a backup."""
    from now_lms.db.backup import db_backup_restore

    click.echo(f"Processing back un from: {backup_sql_file}")
    db_backup_restore(backup_sql_file)


@database.command()
def migrate():  # pragma: no cover
    """Update dabatase schema."""
    alembic.upgrade()


@database.command()
def drop():  # pragma: no cover
    """Delete database schema and all the data in it."""
    with lms_app.app_context():
        if click.confirm("This will delete the database and all the data on it. Do you want to continue?", abort=True):
            eliminar_base_de_datos_segura()


@database.command()
def reset(with_examples=False, with_tests=False) -> None:  # pragma: no cover
    """Drop the system database and populate with init a new one."""
    with lms_app.app_context():
        if click.confirm("This will delete the current database and all the data on it. Do you want to continue?", abort=True):
            cache.clear()
            eliminar_base_de_datos_segura()
            initial_setup(with_examples, with_tests)


@lms_app.cli.command()
def version():  # pragma: no cover
    """Return the current version of the software."""
    click.echo(f"NOW - Learning Management Sytem Code Name: {CODE_NAME} Release: {VERSION}")


@lms_app.cli.group()
def info():
    """General informacion about the system setup."""


@info.command()
@click.argument("course_name", type=str, required=False)
def course(course_name):  # pragma: no cover
    """Return information about the given course."""
    if course_name:
        with lms_app.app_context():
            course_info_data = course_info(course_name)
            click.echo(f"Course: {course_info_data.course.nombre}")
            click.echo(f"Resources count: {course_info_data.resources_count}")
            click.echo(f"Sections count: {course_info_data.sections_count}")
            click.echo(f"Students count: {course_info_data.student_count}")
    else:
        click.echo("No course code provided.")


@info.command()
def system():  # pragma: no cover
    """Return information about the system."""
    with lms_app.app_context():
        config_info_data = config_info()
        click.echo("NOW LMS System Information:")
        click.echo(f"  NOW LMS version: {VERSION}")
        click.echo(f"  Python version: {config_info_data.sys._python_version}")
        click.echo(f"  Python implementation: {config_info_data.sys._python_implementation}")
        click.echo(f"  Database engine: {config_info_data._dbengine}")
        click.echo(f"  Cache type: {config_info_data._cache_type}")

        click.echo("Host Information:")
        click.echo(f"  Operating System: {config_info_data.sys._system}")
        click.echo(f"  OS Version: {config_info_data.sys._system_version}")
        click.echo(f"  Architecture: {config_info_data.sys._arch[0]}")


@info.command()
def path():  # pragma: no cover
    """Directorios used by the current setup."""
    with lms_app.app_context():
        config_info_data = config_info()
        click.echo("Application directories:")
        click.echo(f"  Application Directory: {config_info_data._app_dir}")
        click.echo(f"  Base Files Directory: {config_info_data._base_files_dir}")
        click.echo(f"  Private Files Directory: {config_info_data._private_files_dir}")
        click.echo(f"  Public Files Directory: {config_info_data._public_files_dir}")
        click.echo(f"  Templates Directory: {config_info_data._templates_dir}")


@info.command()
def routes():
    """List all the routes defined in the application."""
    with lms_app.app_context():
        for rule in lms_app.url_map.iter_rules():
            click.echo(f"{rule.endpoint} -> {rule.rule}")


@lms_app.cli.command()
def serve():  # pragma: no cover
    """Serve NOW LMS with the default WSGi server."""
    from waitress import serve as server

    if environ.get("LMS_PORT"):
        PORT = environ.get("LMS_PORT")
    elif environ.get("PORT"):
        PORT = environ.get("PORT")
    else:
        PORT = 8080

    if DESARROLLO:
        THREADS = 4
    else:
        if environ.get("LMS_THREADS"):
            THREADS = environ.get("LMS_THREADS")
        else:
            THREADS = (cpu_count() * 2) + 1

    log.info(f"Starting WSGI server on port {PORT} with {THREADS} threads.")

    with lms_app.app_context():
        server(app=lms_app, port=int(PORT), threads=THREADS)


@lms_app.cli.group()
def settings():
    """Set administration tools."""


@settings.command()
def theme_set():
    """Set the current theme."""
    from now_lms.db import Style

    with lms_app.app_context():
        theme = click.prompt("Enter the theme name", type=str)
        style = db.session.execute(select(Style)).scalars().first()
        style.theme = theme
        db.session.commit()


@settings.command()
def theme_get():
    """Get the current theme."""
    from now_lms.db import Style

    with lms_app.app_context():
        style = db.session.execute(select(Style)).scalars().first()
        click.echo(f"Current theme: {style.theme}")


@settings.command()
def theme_list():
    """List all the themes available."""
    from now_lms.themes import list_themes

    for theme in list_themes():
        click.echo(theme)
