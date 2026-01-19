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

import io
import os


from now_lms.vistas.courses.helpers import (
    sanitize_filename,
    validate_downloadable_file,
    get_course_library_path,
    ensure_course_library_directory,
    markdown2html,
    get_site_config,
    _get_course_evaluations_and_attempts,
    _get_user_resource_progress,
)


class FakeFile(io.BytesIO):
    def __init__(self, data: bytes, filename: str | None):
        super().__init__(data)
        self.filename = filename


def test_sanitize_filename_basic():
    assert sanitize_filename("My File (final).PDF") == "My_File_final.pdf"
    assert sanitize_filename("archive.v1.tar.gz") == "archive.v1.tar.gz"
    assert sanitize_filename("") == ""


def test_validate_downloadable_file_no_file():
    ok, msg = validate_downloadable_file(None)
    assert ok is False and "No se ha seleccionado" in msg


def test_validate_downloadable_file_dangerous():
    f = FakeFile(b"data", "run.exe")
    ok, msg = validate_downloadable_file(f)
    assert ok is False and "no permitido" in msg


def test_validate_downloadable_file_unsupported():
    f = FakeFile(b"data", "file.unsupported")
    ok, msg = validate_downloadable_file(f)
    assert ok is False and "no soportado" in msg


def test_validate_downloadable_file_size_limit():
    # 1 MB + 1 byte
    big = FakeFile(b"x" * (1024 * 1024 + 1), "file.pdf")
    ok, msg = validate_downloadable_file(big)
    assert ok is False and "demasiado grande" in msg


def test_validate_downloadable_file_ok():
    small = FakeFile(b"x" * 10, "file.pdf")
    ok, msg = validate_downloadable_file(small)
    assert ok is True and msg == ""


def test_get_course_library_path_structure():
    from now_lms.config import DIRECTORIO_ARCHIVOS_PUBLICOS

    p = get_course_library_path("curso123")
    assert p.startswith(str(DIRECTORIO_ARCHIVOS_PUBLICOS))
    assert p.replace("\\", "/").endswith("files/curso123/library")


def test_ensure_course_library_directory_creates(tmp_path, monkeypatch):
    # Redefinir la constante usada en helpers directamente para evitar reload
    import now_lms.vistas.courses.helpers as helpers_mod

    monkeypatch.setattr(helpers_mod, "DIRECTORIO_ARCHIVOS_PUBLICOS", str(tmp_path))
    p = ensure_course_library_directory("cursoABC")
    assert os.path.isdir(p)


def test_markdown2html_sanitizes():
    html = markdown2html("<script>alert(1)</script> [link](http://example.com)")
    # No debe haber etiquetas script reales
    assert "<script" not in html.lower()
    # El enlace debe estar presente y seguro
    assert "href=" in html


def test_get_site_config_returns_config(db_session):
    from now_lms.db import Configuracion

    cfg = get_site_config()
    assert isinstance(cfg, Configuracion)
    assert isinstance(cfg.titulo, str)
    assert cfg.titulo != ""


def test_get_course_evaluations_and_attempts_empty(db_session):
    evaluaciones, attempts = _get_course_evaluations_and_attempts("cursoX")
    assert isinstance(evaluaciones, list)
    assert isinstance(attempts, dict)


def test_get_user_resource_progress(db_session):
    from now_lms.db import CursoRecursoAvance

    avance = CursoRecursoAvance(curso="curso1", recurso="1", usuario="user1", completado=True, requerido="required")
    db_session.add(avance)
    db_session.commit()

    progress = _get_user_resource_progress("curso1", "user1")
    assert progress.get("1", {}).get("completado") is True
