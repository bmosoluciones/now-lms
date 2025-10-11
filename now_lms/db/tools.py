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

from __future__ import annotations

# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------
from dataclasses import dataclass
from os import path, remove

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------
from flask import flash
from flask_login import current_user
from pg8000.dbapi import ProgrammingError as PGProgrammingError
from pg8000.exceptions import DatabaseError
from sqlalchemy import func
from sqlalchemy.exc import MultipleResultsFound, NoResultFound, OperationalError, ProgrammingError
from sqlalchemy.inspection import inspect

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms.cache import cache
from now_lms.config import DIRECTORIO_UPLOAD_IMAGENES
from now_lms.db import (
    AdSense,
    Categoria,
    CategoriaCurso,
    CategoriaPrograma,
    Certificacion,
    Certificado,
    Configuracion,
    Curso,
    CursoRecurso,
    CursoRecursoAvance,
    CursoSeccion,
    DocenteCurso,
    EstudianteCurso,
    Etiqueta,
    EtiquetaCurso,
    EtiquetaPrograma,
    MailConfig,
    ModeradorCurso,
    Pago,
    PaypalConfig,
    Programa,
    ProgramaCurso,
    ProgramaEstudiante,
    Style,
    Usuario,
    database,
)
from now_lms.i18n import _
from now_lms.logs import log

# < --------------------------------------------------------------------------------------------- >
# Funciones auxiliares relacionadas a consultas de la base de datos.


def verifica_docente_asignado_a_curso(id_curso: str | None = None) -> bool:
    """Si el usuario no esta asignado como docente al curso devuelve None."""
    if current_user.is_authenticated:
        if database.session.execute(
            database.select(DocenteCurso).filter(DocenteCurso.usuario == current_user.usuario, DocenteCurso.curso == id_curso)
        ).scalar_one_or_none():
            return True
        return False
    return False


def verifica_moderador_asignado_a_curso(id_curso: str | None = None) -> bool:
    """Si el usuario no esta asignado como moderador al curso devuelve None."""
    if current_user.is_authenticated:
        if database.session.execute(
            database.select(ModeradorCurso).filter(
                ModeradorCurso.usuario == current_user.usuario, ModeradorCurso.curso == id_curso
            )
        ).scalar_one_or_none():
            return True
        return False
    return False


def verifica_estudiante_asignado_a_curso(id_curso: str | None = None) -> bool:
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
                return False
            return False
        return False
    return False


def crear_configuracion_predeterminada() -> None:
    """Crea configuración predeterminada de la aplicación."""
    from os import environ, urandom

    from now_lms.i18n import is_testing_mode

    # Use Spanish for testing/CI mode, English for production
    default_lang = environ.get("NOW_LMS_LANG") or ("es" if is_testing_mode() else "en")
    default_currency = environ.get("NOW_LMS_CURRENCY") or "USD"
    default_timezone = environ.get("NOW_LMS_TIMEZONE") or "UTC"

    config = Configuracion()
    config.titulo = "NOW LMS"
    config.descripcion = _("Sistema de aprendizaje en linea.")
    config.moneda = default_currency
    config.r = urandom(16)
    config.enable_programs = False
    config.enable_masterclass = False
    config.enable_resources = False
    config.enable_blog = False
    config.enable_file_uploads = False
    config.lang = default_lang
    config.time_zone = default_timezone
    config.eslogan = _("Aprende a tu ritmo.")
    config.titulo_html = _("NOW LMS - Aprende a tu ritmo.")
    config.hero = ""
    config.custom_text1 = ""
    config.custom_text2 = ""
    config.custom_text3 = ""
    config.custom_text4 = ""

    mail_config = MailConfig()
    mail_config.MAIL_USE_TLS = False
    mail_config.MAIL_USE_SSL = False
    mail_config.email_verificado = False

    adsense_config = AdSense()
    adsense_config.meta_tag_include = False
    adsense_config.add_leaderboard = ""
    adsense_config.add_medium_rectangle = ""
    adsense_config.add_large_rectangle = ""
    adsense_config.add_mobile_banner = ""
    adsense_config.add_wide_skyscraper = ""
    adsense_config.add_skyscraper = ""
    adsense_config.add_large_skyscraper = ""
    adsense_config.add_billboard = ""

    paypal_config = PaypalConfig()
    paypal_config.enable = False

    theme = Style()
    theme.theme = "now_lms"
    theme.custom_logo = False
    theme.custom_favicon = False

    for item in [config, mail_config, adsense_config, paypal_config, theme]:
        database.session.add(item)
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
        return 0
    return 0


@dataclass
class RecursoInfo:
    """Contiene la información necesaria para generar una URL para un recurso.

    Python 3.7+ dataclass provides better functionality than NamedTuple:
    - Mutable fields for runtime configuration updates
    - Default values and field validation
    - Rich comparison and hashing support
    """

    curso_id: str | None = None
    resource_type: str | None = None
    codigo: str | None = None


@dataclass
class RecursoIndex:
    """Clase auxiliar para determinar el orden de un curso.

    Python 3.7+ dataclass replaces NamedTuple for better flexibility:
    - Allows runtime modification
    - Better IDE support and introspection
    - Cleaner initialization and validation
    """

    has_prev: bool = False
    has_next: bool = False
    prev_is_alternative: bool = False
    next_is_alternative: bool = False
    prev_resource: RecursoInfo | None = None
    next_resource: RecursoInfo | None = None


def _is_recurso_alternativo(requerido) -> bool:
    """Check if a resource is alternative (supports both numeric and string values)."""
    return str(requerido) in {"3", "substitute"}


def _check_consecutive_alternatives(recurso_actual: CursoRecurso) -> bool:
    """Check if there are consecutive alternative resources after the given resource.

    Returns True if the next resource in the same section is also alternative.
    """
    if not _is_recurso_alternativo(recurso_actual.requerido):
        return False

    recurso_siguiente = (
        database.session.execute(
            database.select(CursoRecurso).filter(
                CursoRecurso.seccion == recurso_actual.seccion,
                CursoRecurso.indice == recurso_actual.indice + 1,
            )
        )
        .scalars()
        .first()
    )

    return recurso_siguiente is not None and _is_recurso_alternativo(recurso_siguiente.requerido)


def crear_indice_recurso(recurso: str) -> RecursoIndex:
    """Devuelve el indice de un recurso para determinar elemento previo y posterior."""
    has_next: bool = False
    has_prev: bool = False
    prev_is_alternative: bool = False
    next_is_alternative: bool = False
    next_resource: CursoRecurso | None = None
    prev_resource: CursoRecurso | None = None

    # Obtenemos el recurso actual de la base de datos.
    recurso_from_db: CursoRecurso | None = database.session.get(CursoRecurso, recurso)

    if recurso_from_db:
        seccion_from_db: CursoSeccion | None = database.session.get(CursoSeccion, recurso_from_db.seccion)
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
        # Check if prev resource is alternative and if current resource is also alternative (consecutive)
        prev_is_alternative = (
            _is_recurso_alternativo(recurso_anterior.requerido)
            and recurso_from_db is not None
            and _is_recurso_alternativo(recurso_from_db.requerido)
        )
        prev_resource = RecursoInfo(
            recurso_anterior.curso, recurso_anterior.tipo, recurso_anterior.id
        )  # type: ignore[assignment]
    elif seccion_from_db and recurso_from_db:
        # Filter by course to prevent cross-course navigation
        seccion_anterior = (
            database.session.execute(
                database.select(CursoSeccion).filter(
                    CursoSeccion.curso == recurso_from_db.curso,
                    CursoSeccion.indice == seccion_from_db.indice - 1,
                )
            )
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
                # Check if prev resource is alternative and if current resource is also alternative (consecutive)
                # When crossing sections, we don't treat it as consecutive alternatives
                prev_is_alternative = False
                prev_resource = RecursoInfo(
                    recurso_de_seccion_anterior.curso, recurso_de_seccion_anterior.tipo, recurso_de_seccion_anterior.id
                )  # type: ignore[assignment]

    if recurso_posterior:
        has_next = True
        # Check if next resource is alternative and if there's another alternative after it (consecutive)
        next_is_alternative = _check_consecutive_alternatives(recurso_posterior)
        next_resource = RecursoInfo(
            recurso_posterior.curso, recurso_posterior.tipo, recurso_posterior.id
        )  # type: ignore[assignment]
    elif seccion_from_db and recurso_from_db:
        # Filter by course to prevent cross-course navigation
        seccion_posterior = (
            database.session.execute(
                database.select(CursoSeccion).filter(
                    CursoSeccion.curso == recurso_from_db.curso,
                    CursoSeccion.indice == seccion_from_db.indice + 1,
                )
            )
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
                # When crossing sections, check if there are consecutive alternatives at the start of next section
                next_is_alternative = _check_consecutive_alternatives(recurso_de_seccion_posterior)
                next_resource = RecursoInfo(
                    recurso_de_seccion_posterior.curso, recurso_de_seccion_posterior.tipo, recurso_de_seccion_posterior.id
                )  # type: ignore[assignment]

    return RecursoIndex(has_prev, has_next, prev_is_alternative, next_is_alternative, prev_resource, next_resource)


@cache.cached(timeout=60, key_prefix="cached_logo")
def logo_perzonalizado():
    """Devuelve configuracion predeterminada."""
    consulta = database.session.execute(database.select(Style)).first()
    if consulta:
        consulta = consulta[0]
        return consulta.custom_logo
    return False


@cache.cached(timeout=60, key_prefix="cached_favicon")
def favicon_perzonalizado():
    """Devuelve configuracion predeterminada."""
    consulta = database.session.execute(database.select(Style)).first()
    if consulta:
        consulta = consulta[0]
        return consulta.custom_logo
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
    except FileNotFoundError:
        pass


def elimina_logo_perzonalizado_curso(course_code: str):
    """Elimina logo tipo perzonalizado."""
    from now_lms.vistas._helpers import get_current_course_logo

    logo_name = get_current_course_logo(course_code)
    if logo_name is None:
        return  # No logo to delete

    LOGO = path.join(DIRECTORIO_UPLOAD_IMAGENES, course_code, logo_name)
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

    try:
        remove(LOGO)
        flash(_("Imagen de usuario eliminada correctamente."), "success")
    except FileNotFoundError:
        flash(_("Imagen de usuario no existe."), "error")


def cursos_por_etiqueta(tag: str) -> int:
    """Devuelve el numero de cursos en una etiqueta."""
    result = database.session.execute(
        database.select(func.count(EtiquetaCurso.id)).filter(EtiquetaCurso.etiqueta == tag)
    ).scalar()
    return result or 0


def cursos_por_categoria(tag: str) -> int:
    """Devuelve el numero de cursos en una Categoria."""
    result = database.session.execute(
        database.select(func.count(CategoriaCurso.id)).filter(CategoriaCurso.categoria == tag)
    ).scalar()
    return result or 0


def programas_por_etiqueta(tag: str) -> int:
    """Devuelve el numero de programas en una etiqueta."""
    result = database.session.execute(
        database.select(func.count(EtiquetaPrograma.id)).filter(EtiquetaPrograma.etiqueta == tag)
    ).scalar()
    return result or 0


def programas_por_categoria(tag: str) -> int:
    """Devuelve el numero de programas en una Categoria."""
    result = database.session.execute(
        database.select(func.count(CategoriaPrograma.id)).filter(CategoriaPrograma.categoria == tag)
    ).scalar()
    return result or 0


def cuenta_cursos_por_programa(codigo_programa: str) -> int:
    """Devuelve el número de programas que tiene un curso."""
    result = database.session.execute(
        database.select(func.count(ProgramaCurso.id)).filter(ProgramaCurso.programa == codigo_programa)
    ).scalar()
    return result or 0


def obtener_cursos_de_programa(codigo_programa: str):
    """Obtiene todos los cursos de un programa."""
    return (
        database.session.execute(database.select(ProgramaCurso).filter(ProgramaCurso.programa == codigo_programa))
        .scalars()
        .all()
    )


def obtener_cursos_completados_en_programa(usuario: str, codigo_programa: str):
    """Obtiene la lista de cursos completados por un usuario en un programa específico."""
    cursos_programa = obtener_cursos_de_programa(codigo_programa)
    cursos_completados = []

    for curso_programa in cursos_programa:
        # Check if user has completed this course (has a certificate)
        certificacion = database.session.execute(
            database.select(Certificacion).filter(
                Certificacion.usuario == usuario, Certificacion.curso == curso_programa.curso
            )
        ).scalar_one_or_none()

        if certificacion:
            cursos_completados.append(curso_programa.curso)

    return cursos_completados


def verificar_programa_completo(usuario: str, codigo_programa: str) -> bool:
    """Verifica si un usuario ha completado todos los cursos de un programa."""
    total_cursos = cuenta_cursos_por_programa(codigo_programa)
    cursos_completados = len(obtener_cursos_completados_en_programa(usuario, codigo_programa))

    return total_cursos > 0 and cursos_completados == total_cursos


def verificar_usuario_inscrito_programa(usuario: str, codigo_programa: str) -> bool:
    """Verifica si un usuario está inscrito en un programa."""
    # First get the program by codigo to get its ID
    programa = database.session.execute(
        database.select(Programa).filter(Programa.codigo == codigo_programa)
    ).scalar_one_or_none()

    if not programa:
        return False

    inscripcion = database.session.execute(
        database.select(ProgramaEstudiante).filter(
            ProgramaEstudiante.usuario == usuario, ProgramaEstudiante.programa == programa.id
        )
    ).scalar_one_or_none()

    return inscripcion is not None


def obtener_progreso_programa(usuario: str, codigo_programa: str):
    """Obtiene el progreso de un usuario en un programa."""
    total_cursos = cuenta_cursos_por_programa(codigo_programa)
    cursos_completados = len(obtener_cursos_completados_en_programa(usuario, codigo_programa))

    if total_cursos == 0:
        return {"total": 0, "completados": 0, "porcentaje": 0}

    porcentaje = (cursos_completados / total_cursos) * 100
    return {"total": total_cursos, "completados": cursos_completados, "porcentaje": round(porcentaje, 1)}


def obtener_cursos_completados_en_programa_por_id(usuario: str, programa_id: str):
    """Obtiene la lista de cursos completados por un usuario en un programa específico (por ID)."""
    # First get the program by ID to get its codigo
    programa = database.session.execute(database.select(Programa).filter(Programa.id == programa_id)).scalar_one_or_none()

    if not programa:
        return []

    return obtener_cursos_completados_en_programa(usuario, programa.codigo)


def get_addsense_meta():
    """Adsense metatags."""
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
        return ""
    return ""


def get_addsense_code():
    """Adsense metatags."""
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
        return ""
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

    if "mysql" in app.config["SQLALCHEMY_DATABASE_URI"]:
        return "SHOW TABLES LIKE 'curso';"

    if "sqlite" in app.config["SQLALCHEMY_DATABASE_URI"]:
        return "SELECT name FROM sqlite_master WHERE type='table' AND name='curso';"

    return None


def get_paypal_id() -> str:
    """Return pay ID."""
    row = database.session.execute(database.select(PaypalConfig)).first()
    if row is None:
        return ""
    query = row[0]

    if query.sandbox:
        return query.sandbox
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
                    return check
                log.trace("Database not populated.")
                log.info("Database not populated, creating default configuration.")
                return check
            return False
        except (AttributeError, OperationalError, ProgrammingError, PGProgrammingError, DatabaseError, ResourceClosedError):
            return False


def database_select_version_query(app):
    """Return the query to get version of the database."""
    if "postgresql" in app.config["SQLALCHEMY_DATABASE_URI"]:
        return "SELECT version() AS version;"
    if "mysql" in app.config["SQLALCHEMY_DATABASE_URI"]:
        return "SELECT VERSION() AS version;"
    if "mariadb" in app.config["SQLALCHEMY_DATABASE_URI"]:
        return "SELECT VERSION() AS version;"
    if "sqlite" in app.config["SQLALCHEMY_DATABASE_URI"]:
        return "SELECT sqlite_version() AS version;"
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
                return False
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
        if consulta := database.session.execute(database.select(Style)).first():
            data = consulta[0]
            return data.theme
        return "now_lms"
    except (AttributeError, OperationalError):
        return "now_lms"


def generate_user_choices():
    """Generate list of user choices for forms."""
    usuarios = database.session.execute(database.select(Usuario)).all()
    choices = []
    for usuario in usuarios:
        nombre = usuario[0].nombre or ""
        apellido = usuario[0].apellido or ""
        display_name = f"{nombre} {apellido}".strip() or usuario[0].usuario
        choices.append((usuario[0].usuario, display_name))
    return choices


def generate_cource_choices():
    """Generate list of course choices for forms."""
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
    """Generate list of template choices for forms."""
    templates = database.session.execute(database.select(Certificado).filter(Certificado.tipo == "course")).all()
    choices = []
    for template in templates:
        choices.append((template[0].code, template[0].titulo))
    return choices


def generate_template_choices_program():
    """Generate list of template choices for forms."""
    templates = database.session.execute(database.select(Certificado).filter(Certificado.tipo == "program")).all()
    choices = []
    for template in templates:
        choices.append((template[0].code, template[0].titulo))
    return choices


def generate_category_choices():
    """Generate choices for category selection fields."""
    categories = database.session.execute(database.select(Categoria)).all()
    choices = [("", "-- Seleccionar categoría --")]  # Empty option
    for category in categories:
        choices.append((category[0].id, category[0].nombre))
    return choices


def generate_tag_choices():
    """Generate choices for tag selection fields."""
    tags = database.session.execute(database.select(Etiqueta)).all()
    choices = []
    for tag in tags:
        choices.append((tag[0].id, tag[0].nombre))
    return choices


def get_program_category(programa_id: str):
    """Get the current category assignment for a program."""
    categoria_programa = database.session.execute(
        database.select(CategoriaPrograma).filter(CategoriaPrograma.programa == programa_id)
    ).scalar_one_or_none()
    return categoria_programa.categoria if categoria_programa else None


def get_program_tags(programa_id: str):
    """Get the current tag assignments for a program."""
    etiquetas_programa = (
        database.session.execute(database.select(EtiquetaPrograma).filter(EtiquetaPrograma.programa == programa_id))
        .scalars()
        .all()
    )
    return [ep.etiqueta for ep in etiquetas_programa]


def get_course_category(curso_codigo: str):
    """Get the current category assignment for a course."""
    categoria_curso = database.session.execute(
        database.select(CategoriaCurso).filter(CategoriaCurso.curso == curso_codigo)
    ).scalar_one_or_none()
    return categoria_curso.categoria if categoria_curso else None


def get_course_tags(curso_codigo: str):
    """Get the current tag assignments for a course."""
    etiquetas_curso = (
        database.session.execute(database.select(EtiquetaCurso).filter(EtiquetaCurso.curso == curso_codigo)).scalars().all()
    )
    return [ec.etiqueta for ec in etiquetas_curso]


# Navigation configuration helpers
@cache.cached(timeout=10, key_prefix="global_config")
def _get_global_config():
    try:
        if query := database.session.execute(database.select(Configuracion)).first():
            return query[0]
        return None
    except (OperationalError, ProgrammingError, PGProgrammingError, DatabaseError, AttributeError):
        return None


@cache.cached(timeout=300, key_prefix="nav_programs_enabled")
def is_programs_enabled():
    """Check if programs are enabled in navigation."""
    if config := _get_global_config():
        return config.enable_programs
    return False


@cache.cached(timeout=300, key_prefix="nav_masterclass_enabled")
def is_masterclass_enabled():
    """Check if master class is enabled in navigation."""
    if config := _get_global_config():
        return config.enable_masterclass
    return False


@cache.cached(timeout=300, key_prefix="nav_resources_enabled")
def is_resources_enabled():
    """Check if resources are enabled in navigation."""
    if config := _get_global_config():
        return config.enable_resources
    return False


@cache.cached(timeout=300, key_prefix="nav_blog_enabled")
def is_blog_enabled():
    """Check if blog are enabled in navigation."""
    if config := _get_global_config():
        return config.enable_blog
    return False


def get_course_sections(course_code: str):
    """Get all sections for a given course code.

    Args:
        course_code (str): The course code to get sections for

    Returns:
        list: List of CursoSeccion objects ordered by indice, or empty list if none found
    """
    if not course_code:
        return []

    try:
        sections = (
            database.session.execute(
                database.select(CursoSeccion).filter(CursoSeccion.curso == course_code).order_by(CursoSeccion.indice)
            )
            .scalars()
            .all()
        )

        return sections
    except (OperationalError, ProgrammingError, PGProgrammingError, DatabaseError, AttributeError):
        return []


def get_one_record(table_name: str, value, column_name: str | None = None):
    """Devuelve exactamente un registro de la tabla indicada por nombre.

    Retorna None si la tabla/columna no existe o si no hay coincidencia única.

    :param table_name: nombre del modelo (clase) de SQLAlchemy
    :param value: valor a buscar
    :param column_name: nombre de la columna opcional (string)
    :return: instancia del modelo encontrada o None
    """
    db = database
    # Buscar el modelo en el registro de clases de SQLAlchemy
    model_class = db.Model.registry._class_registry.get(table_name)
    if model_class is None or not isinstance(model_class, type):
        return None  # Tabla no encontrada

    # Determinar la columna a usar
    if column_name is None:
        # Usar la primary key
        pk_column = inspect(model_class).primary_key[0]
        column = pk_column
    else:
        # Buscar la columna por nombre
        if not hasattr(model_class, column_name):
            return None  # Columna no encontrada
        column = getattr(model_class, column_name)

    # Ejecutar la query y capturar errores
    try:
        query = db.session.query(model_class).filter(column == value)
        return query.one()
    except (NoResultFound, MultipleResultsFound):
        return None


def get_all_records(table_name: str, filters: dict[str, object] | None = None):
    """Devuelve todos los registros de una tabla.

    :param table_name: nombre del modelo
    :param filters: diccionario con {columna: valor} para filtrar
    :return: lista de instancias o []
    """
    db = database
    model_class = db.Model.registry._class_registry.get(table_name)
    if model_class is None or not isinstance(model_class, type):
        return None

    query = db.session.query(model_class)

    if filters:
        for col, val in filters.items():
            if hasattr(model_class, col):
                query = query.filter(getattr(model_class, col) == val)

    return query.all()


def get_slideshowid(resource_id: str) -> str | None:
    """Get the slideshow ID for a given resource ID.

    :param resource_id: ID of the course resource
    :return: slideshow ID (external_code) or None if not found
    """
    try:
        if (recurso := database.session.get(CursoRecurso, resource_id)) and recurso.tipo == "slides" and recurso.external_code:
            return recurso.external_code
        return None
    except (AttributeError, OperationalError):
        return None
