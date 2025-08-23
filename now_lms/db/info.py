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

"""System information utilities for NOW LMS."""

import platform

# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------
from types import SimpleNamespace
from typing import TYPE_CHECKING, Union

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------
from flask import current_app

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms.db import BlogPost, database

if TYPE_CHECKING:
    from flask import Flask


def app_info(flask_app: "Flask") -> dict:
    """Return application information."""
    from now_lms.cache import CTYPE

    DBURL: str
    DBENGINE: Union[str, None]

    if flask_app.config.get("SQLALCHEMY_DATABASE_URI"):
        DBURL = str(flask_app.config.get("SQLALCHEMY_DATABASE_URI"))
        if "postgresql" in DBURL:
            DBENGINE = "PostgreSQL"
        elif "mysql" in DBURL:
            DBENGINE = "MySQL"
        elif "mariadb" in DBURL:
            DBENGINE = "MariaDB"
        elif "sqlite" in DBURL:
            DBENGINE = "SQLite"
        else:
            DBENGINE = "Otra"
    else:
        DBENGINE = None

    return {"DBENGINE": DBENGINE, "CACHE": CTYPE}


def course_info(course_code: str) -> SimpleNamespace:
    """Return a SimpleNamespace with course information."""
    from sqlalchemy import func

    from now_lms.db import Curso, CursoRecurso, CursoSeccion, EstudianteCurso, Evaluation

    curso = database.session.execute(database.select(Curso).where(Curso.codigo == course_code)).first()[0]
    resources_count = database.session.execute(
        database.select(func.count()).select_from(CursoRecurso).where(CursoRecurso.curso == course_code)
    ).scalar_one()
    sections_count = database.session.execute(
        database.select(func.count()).select_from(CursoSeccion).where(CursoSeccion.curso == course_code)
    ).scalar_one()
    student_count = database.session.execute(
        database.select(func.count()).select_from(EstudianteCurso).where(EstudianteCurso.curso == course_code)
    ).scalar_one()
    evaluations_count = database.session.execute(
        database.select(func.count()).select_from(Evaluation).join(CursoSeccion).where(CursoSeccion.curso == course_code)
    ).scalar_one()

    return SimpleNamespace(
        course=curso,
        resources_count=resources_count,
        sections_count=sections_count,
        student_count=student_count,
        evaluations_count=evaluations_count,
    )


def lms_info() -> SimpleNamespace:
    """Return a SimpleNamespace with LMS information."""
    from sqlalchemy import func

    from now_lms.db import Certificacion, Curso, EstudianteCurso, Evaluation, MasterClass, Programa, Usuario

    courses_count = database.session.execute(database.select(func.count()).select_from(Curso)).scalar_one()
    students_count = database.session.execute(
        database.select(func.count()).select_from(Usuario).where(Usuario.tipo == "student")
    ).scalar_one()
    teachers_count = database.session.execute(
        database.select(func.count()).select_from(Usuario).where(Usuario.tipo == "instructor")
    ).scalar_one()
    moderators_count = database.session.execute(
        database.select(func.count()).select_from(Usuario).where(Usuario.tipo == "moderator")
    ).scalar_one()

    # Additional metrics for enhanced user experience
    enrollments_count = database.session.execute(database.select(func.count()).select_from(EstudianteCurso)).scalar_one()

    certificates_count = database.session.execute(database.select(func.count()).select_from(Certificacion)).scalar_one()

    programs_count = database.session.execute(database.select(func.count()).select_from(Programa)).scalar_one()

    evaluations_count = database.session.execute(database.select(func.count()).select_from(Evaluation)).scalar_one()

    blog_posts_count = database.session.execute(database.select(func.count()).select_from(BlogPost)).scalar_one()

    master_classes_count = database.session.execute(database.select(func.count()).select_from(MasterClass)).scalar_one()

    return SimpleNamespace(
        courses_count=courses_count,
        students_count=students_count,
        teachers_count=teachers_count,
        moderators_count=moderators_count,
        enrollments_count=enrollments_count,
        certificates_count=certificates_count,
        programs_count=programs_count,
        evaluations_count=evaluations_count,
        blog_posts_count=blog_posts_count,
        master_classes_count=master_classes_count,
    )


def _obtener_info_sistema():
    info = SimpleNamespace(
        _system=platform.system(),
        _system_version=platform.version(),
        _arch=platform.architecture(),
        _python_version=platform.python_version(),
        _python_implementation=platform.python_implementation(),
    )
    return info


def config_info() -> SimpleNamespace:
    """Return a SimpleNamespace with system information."""
    with current_app.app_context():
        from now_lms.config import (
            DIRECTORIO_APP,
            DIRECTORIO_ARCHIVOS_BASE,
            DIRECTORIO_ARCHIVOS_PRIVADOS,
            DIRECTORIO_ARCHIVOS_PUBLICOS,
        )
        from now_lms.db import Configuracion
        from now_lms.themes import DIRECTORIO_TEMAS as TEMPLATES_DIR

        configuracion = database.session.execute(database.select(Configuracion)).scalar_one_or_none()

    return SimpleNamespace(
        sys=_obtener_info_sistema(),
        _dbengine=app_info(current_app)["DBENGINE"],
        _cache_type=app_info(current_app)["CACHE"],
        _app_dir=DIRECTORIO_APP,
        _base_files_dir=DIRECTORIO_ARCHIVOS_BASE,
        _private_files_dir=DIRECTORIO_ARCHIVOS_PRIVADOS,
        _public_files_dir=DIRECTORIO_ARCHIVOS_PUBLICOS,
        _templates_dir=TEMPLATES_DIR,
        _time_zone=configuracion.time_zone,
        _language=configuracion.lang,
    )
