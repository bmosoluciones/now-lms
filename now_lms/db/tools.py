# Copyright 2022 - 2024 BMO Soluciones, S.A.
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

"""Definición de base de datos."""


# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------
from os import path, remove
from typing import NamedTuple, Union

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------
from flask import flash
from flask_login import current_user
from pg8000.dbapi import ProgrammingError as PGProgrammingError
from pg8000.exceptions import DatabaseError
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy import func

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms.cache import cache
from now_lms.config import DIRECTORIO_UPLOAD_IMAGENES
from now_lms.db import (
    AdSense,
    CategoriaCurso,
    Certificado,
    Configuracion,
    Curso,
    CursoRecurso,
    CursoRecursoAvance,
    CursoSeccion,
    DocenteCurso,
    EstudianteCurso,
    EtiquetaCurso,
    MailConfig,
    ModeradorCurso,
    Pago,
    PaypalConfig,
    Programa,
    ProgramaCurso,
    Style,
    Usuario,
    database,
)
from now_lms.i18n import _
from now_lms.logs import log

# < --------------------------------------------------------------------------------------------- >
# Funciones auxiliares relacionadas a consultas de la base de datos.


def verifica_docente_asignado_a_curso(id_curso: Union[None, str] = None):
    """Si el usuario no esta asignado como docente al curso devuelve None."""
    if current_user.is_authenticated:
        query = database.session.execute(
            database.select(DocenteCurso).filter(DocenteCurso.usuario == current_user.usuario, DocenteCurso.curso == id_curso)
        ).scalar_one_or_none()
        if query:
            return query
        else:
            return False
    else:
        return False


def verifica_moderador_asignado_a_curso(id_curso: Union[None, str] = None):
    """Si el usuario no esta asignado como moderador al curso devuelve None."""
    if current_user.is_authenticated:
        query = database.session.execute(
            database.select(ModeradorCurso).filter(
                ModeradorCurso.usuario == current_user.usuario, ModeradorCurso.curso == id_curso
            )
        ).scalar_one_or_none()
        if query:
            return True
        else:
            return False
    else:
        return False


def verifica_estudiante_asignado_a_curso(id_curso: Union[None, str] = None):
    """Si el usuario no esta asignado como estudiante al curso devuelve None."""
    if current_user.is_authenticated:
        regitro = (
            (
                database.session.execute(
                    database.select(EstudianteCurso).filter(
                        EstudianteCurso.usuario == current_user.usuario, EstudianteCurso.curso == id_curso
                    )
                )
            )
            .scalars()
            .first()
        )
        if regitro:
            pago = database.session.execute(database.select(Pago).filter(Pago.id == regitro.pago)).scalars().first()
            if pago:
                if pago.estado == "completed" or pago.audit:
                    return True
                else:
                    return False
            else:
                return False
        else:
            return False
    else:
        return False


def crear_configuracion_predeterminada():
    """Crea configuración predeterminada de la aplicación."""

    from os import urandom

    config = Configuracion(
        titulo="NOW LMS",
        descripcion=_("Sistema de aprendizaje en linea."),
        moneda="C$",
        r=urandom(16),
        enable_programs=False,
        enable_masterclass=False,
        enable_resources=False,
    )
    mail_config = MailConfig(
        MAIL_USE_TLS=False,
        MAIL_USE_SSL=False,
        email_verificado=False,
    )
    adsense_config = AdSense(
        meta_tag_include=False,
        add_leaderboard="",
        add_medium_rectangle="",
        add_large_rectangle="",
        add_mobile_banner="",
        add_wide_skyscraper="",
        add_skyscraper="",
        add_large_skyscraper="",
        add_billboard="",
    )
    paypal_config = PaypalConfig(enable=False)
    theme = Style(
        theme="now_lms",
        custom_logo=False,
    )

    database.session.add(config)
    database.session.add(mail_config)
    database.session.add(adsense_config)
    database.session.add(paypal_config)
    database.session.add(theme)
    database.session.commit()


def verificar_avance_recurso(recurso: str, usuario: str) -> int:
    """Devuelve el porcentaje de avance de un estudiante para un recurso dado."""

    if recurso and usuario:
        if (
            (
                consulta := database.session.execute(
                    database.select(CursoRecursoAvance).filter(
                        CursoRecursoAvance.recurso == recurso, CursoRecursoAvance.usuario == usuario
                    )
                )
            )
            .scalars()
            .first()
        ):
            return consulta.avance
        else:
            return 0
    else:
        return 0


class RecursoInfo(NamedTuple):
    """Contiene la información necesaria para generar una URL para un recurso."""

    curso_id: Union[None, str] = None
    resource_type: Union[None, str] = None
    codigo: Union[None, str] = None


class RecursoIndex(NamedTuple):
    """Clase auxiliar para determinar el orden de un curso."""

    has_prev: bool = False
    has_next: bool = False
    prev_is_alternative: bool = False
    next_is_alternative: bool = False
    prev_resource: Union[None, RecursoInfo] = None
    next_resource: Union[None, RecursoInfo] = None


def crear_indice_recurso(recurso: str) -> NamedTuple:
    """Devuelve el indice de un recurso para determinar elemento previo y posterior."""

    has_next: bool = False
    has_prev: bool = False
    prev_is_alternative: bool = False
    next_is_alternative: bool = False
    next_resource: Union[None, CursoRecurso] = None
    prev_resource: Union[None, CursoRecurso] = None

    # Obtenemos el recurso actual de la base de datos.
    recurso_from_db: Union[None, CursoRecurso] = database.session.get(CursoRecurso, recurso)

    if recurso_from_db:
        seccion_from_db: Union[None, CursoRecurso] = database.session.get(CursoSeccion, recurso_from_db.seccion)
        # Verifica si existe un recurso anterior o posterior en la misma sección.
        recurso_anterior = (
            (
                database.session.execute(
                    database.select(CursoRecurso).filter(
                        CursoRecurso.seccion == recurso_from_db.seccion,
                        CursoRecurso.indice == recurso_from_db.indice - 1,
                    )
                )
            )
            .scalars()
            .first()
        )
        recurso_posterior = (
            (
                database.session.execute(
                    database.select(CursoRecurso).filter(
                        CursoRecurso.seccion == recurso_from_db.seccion,
                        CursoRecurso.indice == recurso_from_db.indice + 1,
                    )
                )
            )
            .scalars()
            .first()
        )
    else:
        seccion_from_db = None
        recurso_anterior = None
        recurso_posterior = None

    if recurso_anterior:
        has_prev = True
        prev_is_alternative = recurso_anterior.requerido == 3
        prev_resource = RecursoInfo(recurso_anterior.curso, recurso_anterior.tipo, recurso_anterior.id)  # type: ignore[assignment]
    elif seccion_from_db:
        seccion_anterior = (
            database.session.execute(database.select(CursoSeccion).filter(CursoSeccion.indice == seccion_from_db.indice - 1))
            .scalars()
            .first()
        )
        if seccion_anterior:
            recurso_de_seccion_anterior = (
                (
                    database.session.execute(
                        database.select(CursoRecurso)
                        .filter(CursoRecurso.seccion == seccion_anterior.id)
                        .order_by(CursoRecurso.indice.desc())
                    )
                )
                .scalars()
                .first()
            )
            if recurso_de_seccion_anterior:
                has_prev = True
                prev_is_alternative = recurso_de_seccion_anterior.requerido == 3
                prev_resource = RecursoInfo(recurso_de_seccion_anterior.curso, recurso_de_seccion_anterior.tipo, recurso_de_seccion_anterior.id)  # type: ignore[assignment]

    if recurso_posterior:
        has_next = True
        next_is_alternative = recurso_posterior.requerido == 3
        next_resource = RecursoInfo(recurso_posterior.curso, recurso_posterior.tipo, recurso_posterior.id)  # type: ignore[assignment]
    elif seccion_from_db:
        seccion_posterior = (
            database.session.execute(database.select(CursoSeccion).filter(CursoSeccion.indice == seccion_from_db.indice + 1))
            .scalars()
            .first()
        )
        if seccion_posterior:
            recurso_de_seccion_posterior = (
                (
                    database.session.execute(
                        database.select(CursoRecurso)
                        .filter(CursoRecurso.seccion == seccion_posterior.id)
                        .order_by(CursoRecurso.indice)
                    )
                )
                .scalars()
                .first()
            )
            if recurso_de_seccion_posterior:
                has_next = True
                next_is_alternative = recurso_de_seccion_posterior.requerido == 3
                next_resource = RecursoInfo(recurso_de_seccion_posterior.curso, recurso_de_seccion_posterior.tipo, recurso_de_seccion_posterior.id)  # type: ignore[assignment]

    return RecursoIndex(has_prev, has_next, prev_is_alternative, next_is_alternative, prev_resource, next_resource)


@cache.cached(timeout=60, key_prefix="cached_logo")
def logo_perzonalizado():
    """Devuelve configuracion predeterminada."""

    consulta = database.session.execute(database.select(Style)).first()
    if consulta:
        consulta = consulta[0]
        return consulta.custom_logo
    else:
        return False


@cache.cached(timeout=60, key_prefix="cached_favicon")
def favicon_perzonalizado():
    """Devuelve configuracion predeterminada."""

    consulta = database.session.execute(database.select(Style)).first()
    if consulta:
        consulta = consulta[0]
        return consulta.custom_logo
    else:
        return False


def elimina_logo_perzonalizado():
    """Elimina logo tipo perzonalizado."""
    from now_lms.vistas._helpers import get_site_logo

    consulta = database.session.execute(database.select(Style)).first()[0]
    consulta.custom_logo = False

    LOGO = path.join(DIRECTORIO_UPLOAD_IMAGENES, get_site_logo())

    try:
        remove(LOGO)
        database.session.commit()
    except FileNotFoundError:  # pragma: no cover
        pass


def elimina_logo_perzonalizado_curso(course_code: str):
    """Elimina logo tipo perzonalizado."""
    from now_lms.vistas._helpers import get_current_course_logo

    LOGO = path.join(DIRECTORIO_UPLOAD_IMAGENES, course_code, get_current_course_logo(course_code))
    remove(LOGO)

    curso = database.session.execute(database.select(Curso).filter_by(codigo=course_code)).scalars().first()
    curso.portada = False
    database.session.commit()


def elimina_logo_perzonalizado_programa(course_code: str):
    """Elimina logo tipo perzonalizado de un programa."""

    programa = database.session.execute(database.select(Programa).filter_by(id=course_code)).scalars().first()
    programa.logo = False

    database.session.commit()

    LOGO = path.join(DIRECTORIO_UPLOAD_IMAGENES, "program" + programa.codigo, "logo.jpg")

    remove(LOGO)


def elimina_imagen_usuario(ulid: str):
    """Elimina imagen de usuario."""

    usuario = database.session.execute(database.select(Usuario).filter_by(id=ulid)).scalars().first()
    usuario.portada = False

    database.session.commit()

    LOGO = path.join(DIRECTORIO_UPLOAD_IMAGENES, "usuarios", usuario.id + ".jpg")

    try:  # pragma: no cover
        remove(LOGO)
        flash("Imagen de usuario eliminada correctamente.", "success")
    except FileNotFoundError:  # pragma: no cover
        flash("Imagen de usuario no existe.", "error")


def cursos_por_etiqueta(tag: str) -> int:
    """Devuelve el numero de cursos en una etiqueta"""
    return database.session.execute(
        database.select(func.count(EtiquetaCurso.id)).filter(EtiquetaCurso.etiqueta == tag)
    ).scalar()


def cursos_por_categoria(tag: str) -> int:
    """Devuelve el numero de cursos en una Categoria"""
    return database.session.execute(
        database.select(func.count(CategoriaCurso.id)).filter(CategoriaCurso.categoria == tag)
    ).scalar()


def cuenta_cursos_por_programa(codigo_programa: str) -> int:
    """Devuelve el número de programas que tiene un curso."""
    return database.session.execute(
        database.select(func.count(ProgramaCurso.id)).filter(ProgramaCurso.programa == codigo_programa)
    ).scalar()


def get_addsense_meta():
    """AdSense metatags."""
    try:
        query = database.session.execute(database.select(AdSense)).first()
    except AttributeError:
        return False
    except OperationalError:
        query = None

    if query:
        data = query[0]
        if data.meta_tag_include:
            return data.meta_tag
        else:
            return ""
    else:
        return ""


def get_addsense_code():
    """AdSense metatags."""
    try:
        query = database.session.execute(database.select(AdSense)).first()
    except AttributeError:
        return False
    except OperationalError:
        query = None

    if query:
        data = query[0]
        if data.meta_tag_include:
            return data.add_code
        else:
            return ""
    else:
        return ""


def get_adsense_enabled():
    """Check if ads are globally enabled."""
    try:
        query = database.session.execute(database.select(AdSense)).first()
    except (AttributeError, OperationalError):
        return False

    if query:
        data = query[0]
        return data.show_ads
    return False


def get_ad_leaderboard():
    """Get leaderboard ad code (728x90)."""
    try:
        query = database.session.execute(database.select(AdSense)).first()
    except (AttributeError, OperationalError):
        return ""

    if query:
        data = query[0]
        if data.show_ads and data.add_leaderboard:
            return data.add_leaderboard
    return ""


def get_ad_medium_rectangle():
    """Get medium rectangle ad code (300x250)."""
    try:
        query = database.session.execute(database.select(AdSense)).first()
    except (AttributeError, OperationalError):
        return ""

    if query:
        data = query[0]
        if data.show_ads and data.add_medium_rectangle:
            return data.add_medium_rectangle
    return ""


def get_ad_large_rectangle():
    """Get large rectangle ad code (336x280)."""
    try:
        query = database.session.execute(database.select(AdSense)).first()
    except (AttributeError, OperationalError):
        return ""

    if query:
        data = query[0]
        if data.show_ads and data.add_large_rectangle:
            return data.add_large_rectangle
    return ""


def get_ad_mobile_banner():
    """Get mobile banner ad code (300x50)."""
    try:
        query = database.session.execute(database.select(AdSense)).first()
    except (AttributeError, OperationalError):
        return ""

    if query:
        data = query[0]
        if data.show_ads and data.add_mobile_banner:
            return data.add_mobile_banner
    return ""


def get_ad_wide_skyscraper():
    """Get wide skyscraper ad code (160x600)."""
    try:
        query = database.session.execute(database.select(AdSense)).first()
    except (AttributeError, OperationalError):
        return ""

    if query:
        data = query[0]
        if data.show_ads and data.add_wide_skyscraper:
            return data.add_wide_skyscraper
    return ""


def get_ad_skyscraper():
    """Get skyscraper ad code (120x600)."""
    try:
        query = database.session.execute(database.select(AdSense)).first()
    except (AttributeError, OperationalError):
        return ""

    if query:
        data = query[0]
        if data.show_ads and data.add_skyscraper:
            return data.add_skyscraper
    return ""


def get_ad_large_skyscraper():
    """Get large skyscraper ad code (300x600)."""
    try:
        query = database.session.execute(database.select(AdSense)).first()
    except (AttributeError, OperationalError):
        return ""

    if query:
        data = query[0]
        if data.show_ads and data.add_large_skyscraper:
            return data.add_large_skyscraper
    return ""


def get_ad_billboard():
    """Get billboard ad code (970x250)."""
    try:
        query = database.session.execute(database.select(AdSense)).first()
    except (AttributeError, OperationalError):
        return ""

    if query:
        data = query[0]
        if data.show_ads and data.add_billboard:
            return data.add_billboard
    return ""


def database_select_version(app):
    """Return SQL select query."""
    if "postgresql" in app.config["SQLALCHEMY_DATABASE_URI"]:
        return "SELECT FROM pg_tables WHERE tablename  = 'curso';"

    elif "mysql" in app.config["SQLALCHEMY_DATABASE_URI"]:
        return "SHOW TABLES LIKE 'curso';"

    elif "sqlite" in app.config["SQLALCHEMY_DATABASE_URI"]:
        return "SELECT name FROM sqlite_master WHERE type='table' AND name='curso';"

    else:
        return None


def get_paypal_id() -> str:
    """Return pay ID"""

    query = database.session.execute(database.select(PaypalConfig)).first()
    query = query[0]

    if query.sandbox:
        return query.sandbox
    else:
        return query.paypal_id


def database_is_populated(app):
    """Check is database is populated."""
    from sqlalchemy.exc import ResourceClosedError

    with app.app_context():
        from sqlalchemy.sql import text

        try:
            QUERY = database_select_version(app)
            if QUERY:
                version = database.session.execute(text(QUERY)).first()
                if version:
                    log.debug("Database connection verified.")
                    log.trace("Checking if database is populated.")
                    check = True
                else:
                    check = False
                if check:
                    log.trace("Database populated.")
                else:
                    log.trace("Database not populated.")
                    log.info("Database not populated, creating default configuration.")
                return check
            else:
                return False
        except AttributeError:
            return False
        except OperationalError:
            return False
        except ProgrammingError:
            return False
        except PGProgrammingError:
            return False
        except DatabaseError:
            return False
        except ResourceClosedError:
            return False


def database_select_version_query(app):
    """Returns the query to get version of the database."""

    if "postgresql" in app.config["SQLALCHEMY_DATABASE_URI"]:
        return "SELECT version() AS version;"
    elif "mysql" in app.config["SQLALCHEMY_DATABASE_URI"]:
        return "SELECT VERSION() AS version;"
    elif "mariadb" in app.config["SQLALCHEMY_DATABASE_URI"]:
        return "SELECT VERSION() AS version;"
    elif "sqlite" in app.config["SQLALCHEMY_DATABASE_URI"]:
        return "SELECT sqlite_version() AS version;"
    else:
        return None


def check_db_access(app):
    """Verifica acceso a la base de datos."""

    with app.app_context():
        from sqlalchemy.sql import text

        log.trace("Verifying database access.")
        try:
            QUERY = database_select_version_query(app)
            if QUERY:
                consulta = database.session.execute(text(QUERY)).first()
                if consulta:
                    log.trace("Database access verified.")
                    return True
                else:
                    return False
        except OperationalError:
            return False
        except ProgrammingError:
            return False
        except PGProgrammingError:
            return False
        except DatabaseError:
            return False
        except AttributeError:
            return False


def get_current_theme() -> str:
    """Devuelve el tema actual de la base de datos."""
    try:
        consulta = database.session.execute(database.select(Style)).first()
        if consulta:
            data = consulta[0]
            return data.theme
        else:
            return "now_lms"
    except AttributeError:
        return "now_lms"
    except OperationalError:
        return "now_lms"


def generate_user_choices():

    usuarios = database.session.execute(database.select(Usuario)).all()
    choices = []
    for usuario in usuarios:
        choices.append((usuario[0].usuario, usuario[0].nombre + " " + usuario[0].apellido))
    return choices


def generate_cource_choices():

    cursos = database.session.execute(database.select(Curso)).all()
    choices = []
    for curso in cursos:
        choices.append((curso[0].codigo, curso[0].nombre))
    return choices


def generate_masterclass_choices():
    """Generate choices for master class selection."""
    from now_lms.db import MasterClass

    master_classes = database.session.execute(database.select(MasterClass)).all()
    choices = []
    for mc in master_classes:
        choices.append((mc[0].id, mc[0].title))
    return choices


def generate_template_choices():

    templates = database.session.execute(database.select(Certificado)).all()
    choices = []
    for template in templates:
        choices.append((template[0].code, template[0].titulo))
    return choices


# Navigation configuration helpers
@cache.cached(timeout=300, key_prefix="nav_programs_enabled")
def is_programs_enabled():
    """Check if programs are enabled in navigation."""
    try:
        config = database.session.execute(database.select(Configuracion)).first()
        if config:
            return config[0].enable_programs
        return True  # Default to enabled if no config found
    except (OperationalError, ProgrammingError, PGProgrammingError, DatabaseError, AttributeError):
        return True


@cache.cached(timeout=300, key_prefix="nav_masterclass_enabled")
def is_masterclass_enabled():
    """Check if master class is enabled in navigation."""
    try:
        config = database.session.execute(database.select(Configuracion)).first()
        if config:
            return config[0].enable_masterclass
        return True  # Default to enabled if no config found
    except (OperationalError, ProgrammingError, PGProgrammingError, DatabaseError, AttributeError):
        return True


@cache.cached(timeout=300, key_prefix="nav_resources_enabled")
def is_resources_enabled():
    """Check if resources are enabled in navigation."""
    try:
        config = database.session.execute(database.select(Configuracion)).first()
        if config:
            return config[0].enable_resources
        return True  # Default to enabled if no config found
    except (OperationalError, ProgrammingError, PGProgrammingError, DatabaseError, AttributeError):
        return True
