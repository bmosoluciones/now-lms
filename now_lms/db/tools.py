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
# Contributors:
# - William José Moreno Reyes

"""Definición de base de datos."""
from os import path, remove

# ---------------------------------------------------------------------------------------
# Libreria estandar
# ---------------------------------------------------------------------------------------
from typing import NamedTuple, Union

# ---------------------------------------------------------------------------------------
# Librerias de terceros
# ---------------------------------------------------------------------------------------
from flask import current_app, flash
from flask_login import current_user

from now_lms.cache import cache
from now_lms.config import DIRECTORIO_UPLOAD_IMAGENES

# ---------------------------------------------------------------------------------------
# Recursos locales
# ---------------------------------------------------------------------------------------
from now_lms.db import (
    AdSense,
    CategoriaCurso,
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
    Programa,
    ProgramaCurso,
    Usuario,
    database,
)

# pylint: disable=E1101


# < --------------------------------------------------------------------------------------------- >
# Funciones auxiliares relacionadas a contultas de la base de datos.


def verifica_docente_asignado_a_curso(id_curso: Union[None, str] = None):
    """Si el usuario no esta asignado como docente al curso devuelve None."""
    if current_user.is_authenticated:
        return DocenteCurso.query.filter(DocenteCurso.usuario == current_user.usuario, DocenteCurso.curso == id_curso)
    else:
        return False


def verifica_moderador_asignado_a_curso(id_curso: Union[None, str] = None):
    """Si el usuario no esta asignado como moderador al curso devuelve None."""
    if current_user.is_authenticated:
        return ModeradorCurso.query.filter(ModeradorCurso.usuario == current_user.usuario, ModeradorCurso.curso == id_curso)
    else:
        return False


def verifica_estudiante_asignado_a_curso(id_curso: Union[None, str] = None):
    """Si el usuario no esta asignado como estudiante al curso devuelve None."""
    if current_user.is_authenticated:
        return EstudianteCurso.query.filter(EstudianteCurso.usuario == current_user.usuario, EstudianteCurso.curso == id_curso)
    else:
        return False


def crear_configuracion_predeterminada():
    """Crea configuración predeterminada de la aplicación."""

    from os import urandom

    config = Configuracion(
        titulo="NOW LMS",
        descripcion="Sistema de aprendizaje en linea.",
        modo="mooc",
        style="dark",
        custom_logo=False,
        moneda="C$",
        r=urandom(16),
    )
    mail_config = MailConfig(
        email=True,
        MAIL_USE_TLS=False,
        MAIL_USE_SSL=False,
        email_verificado=False,
    )
    adsense_config = AdSense(meta_tag_include=False)

    database.session.add(config)
    database.session.add(mail_config)
    database.session.add(adsense_config)
    database.session.commit()


def verificar_avance_recurso(recurso: str, usuario: str) -> int:
    """Devuelve el porcentaje de avance de un estudiante para un recurso dado."""

    if recurso and usuario:
        if consulta := CursoRecursoAvance.query.filter(
            CursoRecursoAvance.recurso == recurso, CursoRecursoAvance.usuario == usuario
        ).first():
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


# Lineas muy largas por los comentarios para ignorar errores de tipo.
# pylint: disable=C0301
# flake8: noqa
def crear_indice_recurso(recurso: str) -> NamedTuple:
    """Devuelve el indice de un recurso para determinar elemento previo y posterior."""

    has_next: bool = False
    has_prev: bool = False
    prev_is_alternative: bool = False
    next_is_alternative: bool = False
    next_resource: Union[None, CursoRecurso] = None
    prev_resource: Union[None, CursoRecurso] = None

    # Obtenemos el recurso actual de la base de datos.
    recurso_from_db: Union[None, CursoRecurso] = CursoRecurso.query.get(recurso)

    if recurso_from_db:
        seccion_from_db: Union[None, CursoRecurso] = CursoSeccion.query.get(recurso_from_db.seccion)
        # Verifica si existe un recurso anterior o posterior en la misma sección.
        recurso_anterior = CursoRecurso.query.filter(
            CursoRecurso.seccion == recurso_from_db.seccion, CursoRecurso.indice == recurso_from_db.indice - 1
        ).first()
        recurso_posterior = CursoRecurso.query.filter(
            CursoRecurso.seccion == recurso_from_db.seccion, CursoRecurso.indice == recurso_from_db.indice + 1
        ).first()
    else:
        seccion_from_db = None
        recurso_anterior = None
        recurso_posterior = None

    if recurso_anterior:
        has_prev = True
        prev_is_alternative = recurso_anterior.requerido == 3
        prev_resource = RecursoInfo(recurso_anterior.curso, recurso_anterior.tipo, recurso_anterior.id)  # type: ignore[assignment]
    elif seccion_from_db:
        seccion_anterior = CursoSeccion.query.filter(CursoSeccion.indice == seccion_from_db.indice - 1).first()
        if seccion_anterior:
            recurso_de_seccion_anterior = (
                CursoRecurso.query.filter(CursoRecurso.seccion == seccion_anterior.id)
                .order_by(CursoRecurso.indice.desc())
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
        seccion_posterior = CursoSeccion.query.filter(CursoSeccion.indice == seccion_from_db.indice + 1).first()
        if seccion_posterior:
            recurso_de_seccion_posterior = (
                CursoRecurso.query.filter(CursoRecurso.seccion == seccion_posterior.id).order_by(CursoRecurso.indice).first()
            )
            if recurso_de_seccion_posterior:
                has_next = True
                next_is_alternative = recurso_de_seccion_posterior.requerido == 3
                next_resource = RecursoInfo(recurso_de_seccion_posterior.curso, recurso_de_seccion_posterior.tipo, recurso_de_seccion_posterior.id)  # type: ignore[assignment]

    return RecursoIndex(has_prev, has_next, prev_is_alternative, next_is_alternative, prev_resource, next_resource)


@cache.cached(timeout=60, key_prefix="cached_style")
def obtener_estilo_actual() -> str:
    """Retorna el estilo actual de la base de datos."""

    consulta = Configuracion.query.first()

    return consulta.style


@cache.cached(timeout=60, key_prefix="cached_logo")
def logo_perzonalizado():
    """Devuelve configuracion predeterminada."""

    consulta = Configuracion.query.first()

    return consulta.custom_logo


def elimina_logo_perzonalizado():
    """Elimina logo tipo perzonalizado."""

    consulta = Configuracion.query.first()
    consulta.custom_logo = False

    database.session.commit()

    LOGO = path.join(DIRECTORIO_UPLOAD_IMAGENES, "logotipo.jpg")

    try:
        remove(LOGO)
    except FileNotFoundError:  # pragma: no cover
        pass


def elimina_logo_perzonalizado_curso(course_code: str):
    """Elimina logo tipo perzonalizado."""

    curso = Curso.query.filter_by(codigo=course_code).first()
    curso.portada = False

    database.session.commit()

    LOGO = path.join(DIRECTORIO_UPLOAD_IMAGENES, course_code, "logo.jpg")

    remove(LOGO)


def elimina_logo_perzonalizado_programa(course_code: str):
    """Elimina logo tipo perzonalizado de un programa."""

    programa = Programa.query.filter_by(id=course_code).first()
    programa.logo = False

    database.session.commit()

    LOGO = path.join(DIRECTORIO_UPLOAD_IMAGENES, "program" + programa.codigo, "logo.jpg")

    remove(LOGO)


def elimina_imagen_usuario(ulid: str):
    """Elimina imagen de usuario."""

    usuario = Usuario.query.filter_by(id=ulid).first()
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
    return EtiquetaCurso.query.filter(EtiquetaCurso.etiqueta == tag).count()


def cursos_por_categoria(tag: str) -> int:
    """Devuelve el numero de cursos en una Categoria"""
    return CategoriaCurso.query.filter(CategoriaCurso.categoria == tag).count()


def cuenta_cursos_por_programa(codigo_programa: str) -> int:
    """Devuelve el número de programas que tiene un curso."""
    return ProgramaCurso.query.filter(ProgramaCurso.programa == codigo_programa).count()


def get_addsense_meta():
    """AdSense metatags."""
    try:
        query = database.session.execute(database.select(AdSense)).first()
    except:
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
    except:
        query = None

    if query:
        data = query[0]
        if data.meta_tag_include:
            return data.add_code
        else:
            return ""
    else:
        return ""


def database_is_populated():
    """Check is database is populated."""

    query = database.execute(database.select(Configuracion)).first()

    if query:
        return True

    else:
        return False

    

