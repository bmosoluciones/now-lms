# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""Command line interface for NOW LMS."""

from __future__ import annotations

# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------
from os import environ
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
from now_lms.cache import cache as cache_instance
from now_lms.config import DESARROLLO
from now_lms.db import database as db
from now_lms.db import eliminar_base_de_datos_segura
from now_lms.db.info import config_info, course_info
from now_lms.i18n import _
from now_lms.logs import log
from now_lms.version import CODE_NAME, VERSION

WAITRESS_INSTALL_MESSAGE = "Waitress is not installed. Install it with: pip install waitress"
ENTER_USERNAME_PROMPT = "Enter username"
PASSWORDS_MISMATCH_MESSAGE = "Passwords do not match."
NOT_CONFIGURED_LABEL = "Not configured"


# ---------------------------------------------------------------------------------------
# Interfaz de linea de comandos.
# ---------------------------------------------------------------------------------------
@click.group(
    cls=FlaskGroup, create_app=lambda: lms_app, help=_("Interfaz de linea de comandos para la administración de NOW LMS.")
)
def command() -> None:
    """Linea de comandos para administración de la aplicacion."""


@lms_app.cli.group()
def database():
    """Database administration tools."""


@database.command()
@click.option("--with-examples", is_flag=True, default=False, help="Load example data at setup.")
@click.option("--with-testdata", is_flag=True, default=False, help="Load data for testing.")
def init(with_examples=False, with_testdata=False):
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
def backup():
    """Make a backup of system data."""
    from now_lms.db.backup import db_backup

    db_backup()


@database.command()
@click.argument(
    "backup_sql_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True, path_type=Path),
)
def restore(backup_sql_file: Path):
    """Restore the system from a backup."""
    from now_lms.db.backup import db_backup_restore

    click.echo(f"Processing back un from: {backup_sql_file}")
    db_backup_restore(backup_sql_file)


@database.command()
def migrate():
    """Update dabatase schema."""
    alembic.upgrade()


def _reporte_paginas_predeterminadas(reporte) -> int:
    """Print a default-page sync report and return how many rows are correctable."""
    etiquetas = {
        "faltante": "missing, would be created",
        "al-dia": "up to date",
        "desactualizada": "untouched default, still in {idioma}",
        "personalizada": "edited here, will not be touched",
    }
    for registro in reporte:
        etiqueta = etiquetas[registro["estado"]].format(idioma=registro["idioma"])
        titulo = registro["titulo"] or "-"
        click.echo(f"  {registro['slug']:<16} {titulo:<28} {etiqueta}")
    return len([r for r in reporte if r["estado"] in ("faltante", "desactualizada")])


@database.command("sync-default-pages")
@click.option("--apply", "aplicar", is_flag=True, default=False, help="Rewrite the stale pages instead of only reporting.")
def sync_default_pages(aplicar: bool) -> None:
    """Report, and with --apply repair, default pages left in a stale language.

    The default pages are seeded once and never revisited, so changing the site
    language afterwards leaves About Us and Privacy Policy in the language the
    site was first seeded in. Without --apply this writes nothing: it is a safe
    way to read what the pages actually say on a running deployment.

    A page is only ever rewritten when its stored title and content are byte
    identical to a default this version ships. A page edited here is reported
    and left alone.
    """
    from now_lms.db.initial_data import sincronizar_paginas_predeterminadas

    with lms_app.app_context():
        reporte = sincronizar_paginas_predeterminadas()
        click.echo("Default custom pages:")
        pendientes = _reporte_paginas_predeterminadas(reporte)

        if not aplicar:
            if pendientes:
                click.echo(f"\n{pendientes} page(s) can be synchronised. Re-run with --apply to do it.")
            else:
                click.echo("\nNothing to do.")
            return

        if not pendientes:
            click.echo("\nNothing to do.")
            return

        click.confirm(f"\nRewrite {pendientes} default page(s)?", abort=True)
        sincronizar_paginas_predeterminadas(aplicar=True)
        click.echo("Done. Re-reading:")
        _reporte_paginas_predeterminadas(sincronizar_paginas_predeterminadas())


@database.command()
def drop():
    """Delete database schema and all the data in it."""
    with lms_app.app_context():
        if click.confirm("This will delete the database and all the data on it. Do you want to continue?", abort=True):
            eliminar_base_de_datos_segura()


@database.command()
def reset(with_examples=False, with_tests=False) -> None:
    """Drop the system database and populate with init a new one."""
    with lms_app.app_context():
        if click.confirm("This will delete the current database and all the data on it. Do you want to continue?", abort=True):
            cache_instance.clear()
            eliminar_base_de_datos_segura()
            initial_setup(with_examples, with_tests)


@database.command()
def engine():
    """Return the database engine."""
    with lms_app.app_context():
        db_engine = lms_app.config["SQLALCHEMY_DATABASE_URI"]
        click.echo(f"Database Engine: {db_engine}")


@database.group()
def session():
    """Session management tools."""


@session.command("clear")
def session_clear():
    """Delete expired sessions from the database."""
    with lms_app.app_context():
        from datetime import datetime, timezone

        # Check if session type is SQLAlchemy
        session_type = lms_app.config.get("SESSION_TYPE")

        if session_type != "sqlalchemy":
            click.echo(
                f"Session backend is '{session_type}', not 'sqlalchemy'. This command only works with SQLAlchemy session backend."
            )
            return

        # Get the session table name
        table_name = lms_app.config.get("SESSION_SQLALCHEMY_TABLE", "flask_sessions")

        try:
            # Query and delete expired sessions
            from sqlalchemy import text

            now_utc = datetime.now(timezone.utc)
            result = db.session.execute(text(f"DELETE FROM {table_name} WHERE expiry <= :now"), {"now": now_utc})
            deleted_count = result.rowcount
            db.session.commit()

            click.echo(f"Deleted {deleted_count} expired session(s) from {table_name} table.")
            log.info(f"Cleared {deleted_count} expired sessions")

        except Exception as e:
            db.session.rollback()
            click.echo(f"Error clearing expired sessions: {e}")
            log.error(f"Error clearing expired sessions: {e}")
            raise


@session.command("stats")
def session_stats():
    """Return the number of active sessions."""
    with lms_app.app_context():
        from datetime import datetime, timezone

        # Check if session type is SQLAlchemy
        session_type = lms_app.config.get("SESSION_TYPE")

        if session_type != "sqlalchemy":
            click.echo(
                f"Session backend is '{session_type}', not 'sqlalchemy'. This command only works with SQLAlchemy session backend."
            )
            return

        # Get the session table name
        table_name = lms_app.config.get("SESSION_SQLALCHEMY_TABLE", "flask_sessions")

        try:
            # Count active sessions (not expired)
            from sqlalchemy import text

            now_utc = datetime.now(timezone.utc)
            result = db.session.execute(text(f"SELECT COUNT(*) FROM {table_name} WHERE expiry > :now"), {"now": now_utc})
            active_count = result.scalar()

            # Count total sessions
            total_result = db.session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            total_count = total_result.scalar()

            click.echo(f"Session statistics for {table_name} table:")
            click.echo(f"  Active sessions: {active_count}")
            click.echo(f"  Expired sessions: {total_count - active_count}")
            click.echo(f"  Total sessions: {total_count}")

        except Exception as e:
            click.echo(f"Error retrieving session statistics: {e}")
            log.error(f"Error retrieving session statistics: {e}")
            raise


@lms_app.cli.command()
def version():
    """Return the current version of the software."""
    click.echo("NOW - Learning Management Sytem")
    click.echo(f" Code Name: {CODE_NAME}")
    click.echo(f" Version: {VERSION}")


@lms_app.cli.group()
def info():
    """General informacion about the system setup."""


@info.command()
@click.argument("course_name", type=str, required=False)
def course(course_name):
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
def system():
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
def path():
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


def _get_port():
    """Return the port from environment variables, defaulting to 8080."""
    return environ.get("LMS_PORT") or environ.get("PORT") or 8080


def _get_workers_threads():
    """Return (workers, threads) based on environment."""
    if DESARROLLO:
        return 1, 1
    from now_lms.worker_config import get_worker_config_from_env

    return get_worker_config_from_env()


def _run_waitress(port, threads):
    """Start the Waitress WSGI server. Raises ImportError if not installed."""
    from waitress import serve as waitress_serve

    log.info(f"Starting Waitress WSGI server on port {port} with {threads} threads")
    waitress_serve(
        lms_app,
        host="0.0.0.0",
        port=port,
        threads=threads,
        channel_timeout=120,
        cleanup_interval=30,
        _quiet=False,
    )


def _run_flask_dev_server(port):
    """Spawn a Flask development server via subprocess."""
    import subprocess
    import sys

    log.info("Falling back to Flask development server.")
    cmd_ = [
        sys.executable,
        "-m",
        "flask",
        "run",
        "--host=0.0.0.0",
        f"--port={port}",
    ]
    if DESARROLLO:
        cmd_.append("--debug")

    environ["FLASK_APP"] = "now_lms"
    try:
        subprocess.run(cmd_, check=True)
    except KeyboardInterrupt:
        log.info("Server stopped by user.")
    except subprocess.CalledProcessError as e:
        log.error(f"Failed to start Flask development server: {e}")
        raise


def _run_gunicorn(port, workers, threads):
    """Start the Gunicorn WSGI server. Raises ImportError if not installed."""
    from gunicorn.app.base import BaseApplication
    from now_lms.session_config import reset_connections_after_fork

    class StandaloneApplication(BaseApplication):
        """Gunicorn application class for NOW LMS."""

        def __init__(self, app, options=None):
            self.options = options or {}
            self.application = app
            super().__init__()

        def load_config(self):
            for key, value in self.options.items():
                if key in self.cfg.settings and value is not None:
                    self.cfg.set(key.lower(), value)

        def load(self):
            return self.application

    options = {
        "bind": f"0.0.0.0:{port}",
        "workers": workers,
        "threads": threads,
        "worker_class": "gthread" if threads > 1 else "sync",
        "preload_app": True,
        "post_fork": reset_connections_after_fork,
        "timeout": 120,
        "graceful_timeout": 30,
        "keepalive": 5,
        "accesslog": "-",
        "errorlog": "-",
        "loglevel": "info",
    }

    log.info(f"Starting Gunicorn WSGI server on port {port} with {workers} workers and {threads} threads per worker.")

    StandaloneApplication(lms_app, options).run()


def _start_waitress_or_fallback(port, threads):
    """Try Waitress, fall back to Flask dev server on ImportError."""
    try:
        _run_waitress(port, threads)
    except ImportError:
        log.error(WAITRESS_INSTALL_MESSAGE)
        _run_flask_dev_server(port)


@lms_app.cli.command()
@click.option(
    "--wsgi-server",
    type=click.Choice(["waitress", "gunicorn"], case_sensitive=False),
    default="waitress",
    help="WSGI server to use (default: waitress)",
)
def serve(wsgi_server):
    """Serve NOW LMS with the specified WSGI server."""
    import platform

    from now_lms.session_config import ensure_session_storage

    port = _get_port()
    workers, threads = _get_workers_threads()

    ensure_session_storage(lms_app)

    wsgi_server = wsgi_server.lower()

    if wsgi_server == "waitress":
        _start_waitress_or_fallback(port, threads)
        return

    if wsgi_server == "gunicorn" and platform.system() == "Windows":
        log.error("Gunicorn is not supported on Windows. Use waitress instead or run on Linux/containers.")
        log.info("Starting Waitress WSGI server instead.")
        try:
            _run_waitress(port, threads)
        except ImportError:
            log.error(WAITRESS_INSTALL_MESSAGE)
            raise
        return

    try:
        _run_gunicorn(port, workers, threads)
    except ImportError:
        log.error("Gunicorn is not installed. Install it with: pip install gunicorn")
        _start_waitress_or_fallback(port, threads)


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


@settings.command()
def lang_get():
    """Get the current language setting."""
    from now_lms.db import Configuracion

    with lms_app.app_context():
        conf = db.session.execute(select(Configuracion)).scalars().first()
        click.echo(f"Current language: {conf.lang}")


@settings.command()
def lang_set():
    """Set the current language."""
    from now_lms.db import Configuracion
    from now_lms.db.initial_data import sincronizar_paginas_predeterminadas

    with lms_app.app_context():
        lang_ = click.prompt("Enter the language code", type=str)
        confg = db.session.execute(select(Configuracion)).scalars().first()
        confg.lang = lang_
        db.session.commit()

        # The default pages are seeded once and never revisited, so this commit
        # leaves them in the previous language with nothing to say so.
        rezagadas = [r for r in sincronizar_paginas_predeterminadas() if r["estado"] == "desactualizada"]
        if rezagadas:
            slugs = ", ".join(r["slug"] for r in rezagadas)
            click.echo(f"Warning: {len(rezagadas)} default page(s) are still in their original language: {slugs}")
            click.echo("Run 'lmsctl database sync-default-pages' to see them, or add --apply to update them.")


@settings.command()
def timezone_get():
    """Get the current timezone setting."""
    from now_lms.db import Configuracion

    with lms_app.app_context():
        conf_ = db.session.execute(select(Configuracion)).scalars().first()
        click.echo(f"Current language: {conf_.time_zone}")


@settings.command()
def timezone_set():
    """Set the current timezone."""
    from now_lms.db import Configuracion

    with lms_app.app_context():
        timezone_ = click.prompt("Enter the timezone", type=str)
        confg_ = db.session.execute(select(Configuracion)).scalars().first()
        confg_.time_zone = timezone_
        db.session.commit()


@lms_app.cli.group()
def admin():
    """Administration tools for managing users and system."""


@admin.command()
def reset_password():
    """Reset a user's password."""
    from now_lms.auth import proteger_passwd
    from now_lms.db import Usuario

    with lms_app.app_context():
        username = click.prompt(ENTER_USERNAME_PROMPT, type=str)

        # Find user by username or email
        usuario = db.session.execute(select(Usuario).filter_by(usuario=username)).scalar_one_or_none()
        if not usuario:
            usuario = db.session.execute(select(Usuario).filter_by(correo_electronico=username)).scalar_one_or_none()

        if not usuario:
            click.echo(f"User '{username}' not found.")
            return

        # Prompt for new password with confirmation
        password = click.prompt("Enter new password", type=str, hide_input=True)
        confirm_password = click.prompt("Confirm new password", type=str, hide_input=True)

        if password != confirm_password:
            click.echo(PASSWORDS_MISMATCH_MESSAGE)
            return

        # Update password
        usuario.acceso = proteger_passwd(password)
        db.session.commit()

        click.echo(f"Password updated successfully for user '{usuario.usuario}'.")


@admin.command()
def set_admin():
    """Disable all admin users and create a new one."""
    from now_lms.auth import proteger_passwd
    from now_lms.db import Usuario

    with lms_app.app_context():
        # Security confirmation
        click.echo("WARNING: This command will disable ALL existing admin users and create a new one.")
        click.echo("This is an emergency security measure.")
        if not click.confirm("Do you want to continue?", abort=True):
            return

        # Find all admin users
        admin_users = db.session.execute(select(Usuario).filter_by(tipo="admin")).scalars().all()

        if admin_users:
            click.echo(f"Found {len(admin_users)} admin user(s) to disable:")
            for admin_user in admin_users:
                click.echo(f"  - {admin_user.usuario} ({admin_user.correo_electronico})")

        if not click.confirm("Proceed to disable these admin users and create a new one?", abort=True):
            return

        # Disable all existing admin users
        disabled_count = 0
        for admin_user in admin_users:
            admin_user.activo = False
            disabled_count += 1
            click.echo(f"Disabled admin user: {admin_user.usuario}")

        # Commit the disabled users changes
        db.session.commit()

        # Prompt for new admin user details
        click.echo("\nCreating new admin user:")
        username = click.prompt("Enter new admin username", type=str)

        # Check if username already exists
        existing_user = db.session.execute(select(Usuario).filter_by(usuario=username)).scalar_one_or_none()
        if existing_user:
            click.echo(f"Username '{username}' already exists.")
            return

        # Prompt for other required fields
        nombre = click.prompt("Enter first name", type=str)
        apellido = click.prompt("Enter last name", type=str)
        correo_electronico = click.prompt("Enter email", type=str)

        # Check if email already exists
        existing_email = db.session.execute(
            select(Usuario).filter_by(correo_electronico=correo_electronico)
        ).scalar_one_or_none()
        if existing_email:
            click.echo(f"Email '{correo_electronico}' already exists.")
            return

        # Prompt for password
        password = click.prompt("Enter password", type=str, hide_input=True)
        confirm_password = click.prompt("Confirm password", type=str, hide_input=True)

        if password != confirm_password:
            click.echo(PASSWORDS_MISMATCH_MESSAGE)
            return

        # Create new admin user
        nuevo_admin = Usuario(
            usuario=username,
            acceso=proteger_passwd(password),
            nombre=nombre,
            apellido=apellido,
            correo_electronico=correo_electronico,
            tipo="admin",
            activo=True,
            correo_electronico_verificado=False,
            visible=True,
        )

        db.session.add(nuevo_admin)
        db.session.commit()

        click.echo("\nSecurity reset completed:")
        click.echo(f"  - Disabled {disabled_count} existing admin user(s)")
        click.echo(f"  - Created new admin user: '{username}'")
        click.echo("Emergency admin reset successful.")


@lms_app.cli.group()
def user():
    """User management tools."""


@user.command()
def new():
    """Create a new user."""
    from now_lms.auth import proteger_passwd
    from now_lms.db import Usuario

    with lms_app.app_context():
        # Prompt for required fields
        username = click.prompt(ENTER_USERNAME_PROMPT, type=str)

        # Check if username already exists
        existing_user = db.session.execute(select(Usuario).filter_by(usuario=username)).scalar_one_or_none()
        if existing_user:
            click.echo(f"Username '{username}' already exists.")
            return

        # Prompt for user type with validation
        valid_types = ["student", "moderator", "instructor", "admin"]
        tipo = click.prompt(f"Enter user type ({'/'.join(valid_types)})", type=click.Choice(valid_types))

        # Prompt for other required/optional fields
        nombre = click.prompt("Enter first name", type=str)
        apellido = click.prompt("Enter last name", type=str)
        correo_electronico = click.prompt("Enter email", type=str)

        # Check if email already exists
        existing_email = db.session.execute(
            select(Usuario).filter_by(correo_electronico=correo_electronico)
        ).scalar_one_or_none()
        if existing_email:
            click.echo(f"Email '{correo_electronico}' already exists.")
            return

        # Prompt for password
        password = click.prompt("Enter password", type=str, hide_input=True)
        confirm_password = click.prompt("Confirm password", type=str, hide_input=True)

        if password != confirm_password:
            click.echo(PASSWORDS_MISMATCH_MESSAGE)
            return

        # Create new user
        nuevo_usuario = Usuario(
            usuario=username,
            acceso=proteger_passwd(password),
            nombre=nombre,
            apellido=apellido,
            correo_electronico=correo_electronico,
            tipo=tipo,
            activo=True,
            correo_electronico_verificado=False,
            visible=True,
        )

        db.session.add(nuevo_usuario)
        db.session.commit()

        click.echo(f"User '{username}' created successfully with type '{tipo}'.")


@user.command()
def set_password():
    """Set a user's password."""
    from now_lms.auth import proteger_passwd
    from now_lms.db import Usuario

    with lms_app.app_context():
        username = click.prompt(ENTER_USERNAME_PROMPT, type=str)

        # Find user by username or email
        usuario = db.session.execute(select(Usuario).filter_by(usuario=username)).scalar_one_or_none()
        if not usuario:
            usuario = db.session.execute(select(Usuario).filter_by(correo_electronico=username)).scalar_one_or_none()

        if not usuario:
            click.echo(f"User '{username}' not found.")
            return

        # Prompt for new password with confirmation
        password = click.prompt("Enter new password", type=str, hide_input=True)
        confirm_password = click.prompt("Confirm new password", type=str, hide_input=True)

        if password != confirm_password:
            click.echo(PASSWORDS_MISMATCH_MESSAGE)
            return

        # Update password
        usuario.acceso = proteger_passwd(password)
        db.session.commit()

        click.echo(f"Password updated successfully for user '{usuario.usuario}'.")


@lms_app.cli.group()
def cache():
    """Cache management tools."""


@cache.command()  # type: ignore[no-redef]
def info():  # type: ignore[no-redef]
    """Show cache configuration and status."""
    from now_lms.cache import CACHE_CONFIG, CTYPE

    with lms_app.app_context():
        click.echo("Cache Configuration:")
        click.echo(f"  Type: {CTYPE}")
        click.echo(f"  Key Prefix: {CACHE_CONFIG.get('CACHE_KEY_PREFIX', 'None')}")
        click.echo(f"  Default Timeout: {CACHE_CONFIG.get('CACHE_DEFAULT_TIMEOUT', 'None')} seconds")

        if CTYPE == "RedisCache":
            redis_url = CACHE_CONFIG.get("CACHE_REDIS_URL", NOT_CONFIGURED_LABEL)
            # Mask password in URL for security
            if redis_url and redis_url != NOT_CONFIGURED_LABEL:
                from urllib.parse import urlparse

                parsed_url = urlparse(redis_url)
                if parsed_url.password:
                    masked_url = redis_url.replace(parsed_url.password, "***")
                    click.echo(f"  Redis URL: {masked_url}")
                else:
                    click.echo(f"  Redis URL: {redis_url}")
            else:
                click.echo(f"  Redis URL: {redis_url}")
        elif CTYPE == "MemcachedCache":
            servers = CACHE_CONFIG.get("CACHE_MEMCACHED_SERVERS", NOT_CONFIGURED_LABEL)
            click.echo(f"  Memcached Servers: {servers}")
        elif CTYPE == "NullCache":
            click.echo("  Note: NullCache is active - no actual caching is performed")


@cache.command()
def clear():
    """Clear all cached data."""
    from now_lms.cache import CTYPE

    with lms_app.app_context():
        if CTYPE == "NullCache":
            click.echo("NullCache is active - no cached data to clear.")
            return

        try:
            cache_instance.clear()
            click.echo("Cache cleared successfully.")
        except Exception as e:
            click.echo(f"Error clearing cache: {e}")


def _print_redis_stats(cache_backend):
    """Print Redis cache statistics."""
    click.echo("Cache Statistics (Redis):")
    try:
        if not cache_backend._read_clients:
            click.echo("  No Redis connection available for statistics.")
            return

        redis_info = cache_backend._read_clients[0].info()
        click.echo(f"  Connected clients: {redis_info.get('connected_clients', 'N/A')}")
        click.echo(f"  Used memory: {redis_info.get('used_memory_human', 'N/A')}")
        click.echo(f"  Total commands processed: {redis_info.get('total_commands_processed', 'N/A')}")
        click.echo(f"  Keyspace hits: {redis_info.get('keyspace_hits', 'N/A')}")
        click.echo(f"  Keyspace misses: {redis_info.get('keyspace_misses', 'N/A')}")

        hits = redis_info.get("keyspace_hits", 0)
        misses = redis_info.get("keyspace_misses", 0)
        if hits + misses > 0:
            hit_ratio = (hits / (hits + misses)) * 100
            click.echo(f"  Hit ratio: {hit_ratio:.2f}%")
    except Exception as redis_error:
        click.echo(f"  Error getting Redis statistics: {redis_error}")


_REDIS_KEYS = {"get_hits", "get_misses", "cmd_get", "cmd_set", "bytes", "curr_items"}


def _print_memcached_stats(cache_backend):
    """Print Memcached cache statistics."""
    click.echo("Cache Statistics (Memcached):")
    try:
        if not hasattr(cache_backend._client, "get_stats"):
            click.echo("  Statistics not supported by this Memcached client.")
            return

        memcached_stats = cache_backend._client.get_stats()
        if not memcached_stats:
            click.echo("  No statistics available from Memcached.")
            return

        for server, server_stats in memcached_stats:
            click.echo(f"  Server {server}:")
            for key, value in server_stats.items():
                if key in _REDIS_KEYS:
                    click.echo(f"    {key}: {value}")
    except Exception as memcached_error:
        click.echo(f"  Error getting Memcached statistics: {memcached_error}")


@cache.command()
def stats():
    """Show cache statistics (when supported by backend)."""
    from now_lms.cache import CTYPE

    with lms_app.app_context():
        if CTYPE == "NullCache":
            click.echo("NullCache is active - no statistics available.")
            return

        try:
            cache_backend = cache_instance.cache

            if hasattr(cache_backend, "_read_clients") and hasattr(cache_backend, "_write_clients"):
                _print_redis_stats(cache_backend)
            elif hasattr(cache_backend, "_client"):
                _print_memcached_stats(cache_backend)
            else:
                click.echo("Statistics not available for this cache backend.")
                click.echo(f"Backend type: {type(cache_backend)}")

        except Exception as e:
            click.echo(f"Error retrieving cache statistics: {e}")
