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

"""Funciones auxiliares para vistas de cursos."""

from __future__ import annotations

# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------
from datetime import datetime, timezone
from os import makedirs, path
from os.path import splitext
import re
from typing import Any, Sequence

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------
from bleach import clean, linkify
from flask import flash
from flask_login import current_user
from markdown import markdown
from sqlalchemy import func

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms.config import DIRECTORIO_ARCHIVOS_PUBLICOS
from now_lms.db import (
    Certificacion,
    Configuracion,
    Curso,
    CursoRecurso,
    CursoRecursoAvance,
    CursoSeccion,
    CursoUsuarioAvance,
    Evaluation,
    EvaluationAttempt,
    database,
    select,
)
from now_lms.misc import HTML_TAGS
from now_lms.logs import log
from now_lms.vistas.evaluation_helpers import can_user_receive_certificate
from .data import SAFE_FILE_EXTENSIONS, DANGEROUS_FILE_EXTENSIONS


def validate_downloadable_file(file, max_size_mb: int = 1) -> tuple[bool, str]:
    """Valida archivo subido para recursos descargables."""
    if not file or not getattr(file, "filename", None):
        return False, "No se ha seleccionado ningún archivo"

    filename = str(file.filename or "").lower()
    file_ext = splitext(filename)[1].lower()

    if file_ext in DANGEROUS_FILE_EXTENSIONS:
        return False, f"Tipo de archivo no permitido por seguridad: {file_ext}"

    if file_ext not in SAFE_FILE_EXTENSIONS:
        return False, f"Tipo de archivo no soportado: {file_ext}"

    # Calcular tamaño en bytes
    try:
        file.seek(0, 2)
        file_size = file.tell()
        file.seek(0)
    except Exception:
        # Si no es un stream, asumir 0
        file_size = 0

    max_size_bytes = max_size_mb * 1024 * 1024
    if file_size > max_size_bytes:
        return False, f"El archivo es demasiado grande. Máximo permitido: {max_size_mb}MB"

    return True, ""


def get_site_config() -> Configuracion:
    """Obtiene la configuración del sitio."""
    row = database.session.execute(database.select(Configuracion)).first()
    if row is None:
        raise ValueError("No configuration found")
    return row[0]


def sanitize_filename(filename: str) -> str:
    """Sanitiza nombre de archivo para subidas a la librería."""
    if not filename:
        return ""

    base_name, extension = splitext(filename)
    safe_base = re.sub(r"[^a-zA-Z0-9._-]", "_", base_name)
    safe_base = re.sub(r"_+", "_", safe_base)
    safe_base = safe_base.strip("_")

    return safe_base + extension.lower()


def get_course_library_path(course_code: str) -> str:
    """Devuelve el directorio de librería para un curso."""
    return path.join(DIRECTORIO_ARCHIVOS_PUBLICOS, "files", course_code, "library")


def ensure_course_library_directory(course_code: str) -> str:
    """Asegura que exista el directorio de librería del curso y devuelve su ruta."""
    library_path = get_course_library_path(course_code)
    if not path.exists(library_path):
        makedirs(library_path, exist_ok=True)
    return library_path


def markdown2html(text: str) -> str:
    """Convierte texto en markdown a HTML, sanitizado."""
    allowed_tags = HTML_TAGS
    allowed_attrs = {"*": ["class"], "a": ["href", "rel"], "img": ["src", "alt"]}

    html = markdown(text)
    html_limpio = clean(linkify(html), tags=allowed_tags, attributes=allowed_attrs)
    return html_limpio


def _get_course_evaluations_and_attempts(
    curso_id: str, usuario: str | None = None
) -> tuple[Sequence[Evaluation], dict[Any, Sequence[EvaluationAttempt]]]:
    """Obtiene las evaluaciones del curso y los intentos del usuario."""
    # Obtener las secciones del curso
    secciones = database.session.execute(select(CursoSeccion).filter_by(curso=curso_id)).scalars().all()
    section_ids = [s.id for s in secciones]

    # Obtener evaluaciones de todas las secciones del curso
    evaluaciones = database.session.execute(select(Evaluation).filter(Evaluation.section_id.in_(section_ids))).scalars().all()

    evaluation_attempts: dict[Any, Sequence[EvaluationAttempt]] = {}
    if usuario:
        # Obtener intentos del usuario para cada evaluación
        for evaluation in evaluaciones:
            attempts = (
                database.session.execute(
                    select(EvaluationAttempt)
                    .filter_by(evaluation_id=evaluation.id, user_id=usuario)
                    .order_by(EvaluationAttempt.started_at)
                )
                .scalars()
                .all()
            )
            evaluation_attempts[evaluation.id] = attempts

    return evaluaciones, evaluation_attempts


def _get_user_resource_progress(curso_id: str, usuario: str | None = None) -> dict[int, dict[str, bool]]:
    """Obtiene el progreso del usuario en todos los recursos del curso."""
    if not usuario:
        return {}

    progress_data = (
        database.session.execute(select(CursoRecursoAvance).filter_by(usuario=usuario, curso=curso_id)).scalars().all()
    )

    return {p.recurso: {"completado": p.completado} for p in progress_data}


def _crear_indice_avance_curso(course_code: str) -> None:
    """Crea el índice de avance del curso para el usuario actual."""
    recursos = (
        database.session.execute(
            database.select(CursoRecurso).filter(CursoRecurso.curso == course_code).order_by(CursoRecurso.indice)
        )
        .scalars()
        .all()
    )
    usuario = current_user.usuario

    if recursos:
        for recurso in recursos:
            avance = CursoRecursoAvance(
                usuario=usuario,
                curso=course_code,
                recurso=recurso.id,
                completado=False,
                requerido=recurso.requerido,
            )
            database.session.add(avance)
            database.session.commit()


def _emitir_certificado(curso_id: str, usuario: str, plantilla: str) -> None:
    """Emite un certificado de finalización para un curso."""
    certificado = Certificacion(
        curso=curso_id,
        usuario=usuario,
        certificado=plantilla,
    )
    certificado.creado = datetime.now(timezone.utc).date()
    certificado.creado_por = current_user.usuario if current_user.is_authenticated else "system"
    database.session.add(certificado)
    database.session.commit()
    flash("Certificado de finalización emitido.", "success")


def _actualizar_avance_curso(curso_id: str, usuario: str) -> None:
    """Actualiza porcentaje de avance y emite certificado si corresponde."""
    _avance = (
        database.session.execute(
            select(CursoUsuarioAvance).filter(CursoUsuarioAvance.curso == curso_id, CursoUsuarioAvance.usuario == usuario)
        )
        .scalars()
        .first()
    )

    if not _avance:
        _avance = CursoUsuarioAvance(
            curso=curso_id,
            usuario=usuario,
            recursos_requeridos=0,
            recursos_completados=0,
        )
        database.session.add(_avance)
        database.session.commit()

    _recursos_requeridos = database.session.execute(
        select(func.count(CursoRecurso.id)).filter(CursoRecurso.curso == curso_id, CursoRecurso.requerido == "required")
    ).scalar()

    _recursos_completados = database.session.execute(
        select(func.count(CursoRecursoAvance.id)).filter(
            CursoRecursoAvance.curso == curso_id,
            CursoRecursoAvance.usuario == usuario,
            CursoRecursoAvance.completado.is_(True),
            CursoRecursoAvance.requerido == "required",
        )
    ).scalar()
    log.warning("Required resources: %s, Completed: %s", _recursos_requeridos, _recursos_completados)

    _avance.recursos_requeridos = _recursos_requeridos or 0
    _avance.recursos_completados = _recursos_completados or 0
    _avance.avance = ((_recursos_completados or 0) / (_recursos_requeridos or 1)) * 100
    if _avance.avance >= 100:
        _avance.completado = True
        flash("Curso completado", "success")
        _curso = database.session.execute(select(Curso).filter(Curso.codigo == curso_id)).scalars().first()
        log.warning(_curso)
        if _curso and _curso.certificado:
            can_receive, reason = can_user_receive_certificate(curso_id, usuario)
            if can_receive:
                _emitir_certificado(curso_id, usuario, _curso.plantilla_certificado)
            else:
                log.info(f"Certificate not issued for user {usuario} in course {curso_id}: {reason}")
    database.session.commit()
