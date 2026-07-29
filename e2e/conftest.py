"""Browser-E2E harness (L6): boots the real app against a scratch DB and seeds
the exact data shape production carries.

The seeded member is enrolled WITH NO PAYMENT RECORD (``pago=None``) on a free
course — the shape every bulk-provisioned member has, and the shape that
locked all 49 founding members out on 2026-07-28 (fork finding U12). If that
regression ever returns, ``test_member_journey.py`` fails in the browser the
way a member would experience it.

DB selection: ``E2E_DATABASE_URL`` env (CI passes PostgreSQL) or a throwaway
SQLite file. The app server runs as a real waitress subprocess on a free port;
Playwright drives real HTTP.
"""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

E2E_MEMBER = "e2e-member@example.test"
E2E_MEMBER_PASSWORD = "e2e-member-password"
E2E_COURSE = "E2E-C"

_ENV = {
    "SECRET_KEY": "e2e-secret-key-0123456789abcdef0123456789abcdef",
    "ADMIN_USER": "e2e-admin",
    "ADMIN_PSWD": "e2e-admin-password-123",
    "LOG_LEVEL": "WARNING",
}


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _database_url(tmpdir: str) -> str:
    return os.environ.get("E2E_DATABASE_URL") or f"sqlite:///{tmpdir}/e2e.db"


def _seed(database_url: str) -> None:
    """Initialize the app DB in-process and plant the member + course."""
    os.environ.update(_ENV)
    os.environ["DATABASE_URL"] = database_url

    from now_lms import initial_setup, lms_app
    from now_lms.auth import proteger_passwd
    from now_lms.db import (
        Curso,
        CursoRecurso,
        CursoSeccion,
        EstudianteCurso,
        Usuario,
        database,
    )

    with lms_app.app_context():
        initial_setup()
        s = database.session
        curso = Curso(
            codigo=E2E_COURSE,
            nombre="E2E journey course",
            descripcion_corta="Course used by the browser E2E layer.",
            descripcion="Course used by the browser E2E layer.",
            estado="open",
            publico=False,
            pagado=False,
            certificado=False,
            modalidad="self_paced",
            foro_habilitado=False,
            creado_por="e2e-admin",
        )
        s.add(curso)
        s.flush()
        seccion = CursoSeccion(
            curso=E2E_COURSE,
            nombre="Section one",
            descripcion="First section.",
            indice=1,
            estado=True,
            creado_por="e2e-admin",
        )
        s.add(seccion)
        s.flush()
        recurso = CursoRecurso(
            curso=E2E_COURSE,
            seccion=seccion.id,
            tipo="text",
            nombre="Lesson one",
            descripcion="First lesson.",
            text="# Lesson one\n\nE2E lesson body.",
            indice=1,
            publico=False,
            requerido="required",
            creado_por="e2e-admin",
        )
        s.add(recurso)
        member = Usuario(
            usuario=E2E_MEMBER,
            acceso=proteger_passwd(E2E_MEMBER_PASSWORD),
            nombre="E2E",
            apellido="Member",
            correo_electronico=E2E_MEMBER,
            tipo="student",
            activo=True,
            visible=True,
            correo_electronico_verificado=True,
            creado_por="e2e-admin",
        )
        s.add(member)
        # THE U12 SHAPE: enrollment with no pago row. Must grant access on a
        # free course — this is the founding-member lockout regression pin.
        s.add(
            EstudianteCurso(
                curso=E2E_COURSE,
                usuario=E2E_MEMBER,
                vigente=True,
                pago=None,
                creado_por="e2e-admin",
            )
        )
        s.commit()


@pytest.fixture(scope="session")
def app_server() -> str:
    """Seed a scratch DB, launch the real app, yield its base URL."""
    tmpdir = tempfile.mkdtemp(prefix="now-lms-e2e-")
    database_url = _database_url(tmpdir)

    # Seed in a child process so the server subprocess (and this pytest
    # process) never fight over module-level app state.
    seed_code = (
        "import sys; sys.path.insert(0, %r); "
        "from e2e.conftest import _seed; _seed(%r)" % (str(REPO_ROOT), database_url)
    )
    env = {**os.environ, **_ENV, "DATABASE_URL": database_url}
    subprocess.run(
        [sys.executable, "-c", seed_code], env=env, cwd=REPO_ROOT, check=True, timeout=180
    )

    port = _free_port()
    server = subprocess.Popen(
        [sys.executable, str(REPO_ROOT / "run.py")],
        env={**env, "PORT": str(port), "WSGI_SERVER": "waitress", "NOW_LMS_FORCE_HTTPS": "0"},
        cwd=REPO_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )
    base = f"http://127.0.0.1:{port}"
    try:
        for _ in range(60):
            try:
                if urllib.request.urlopen(f"{base}/health", timeout=2).status == 200:
                    break
            except Exception:
                time.sleep(1)
        else:
            raise RuntimeError("app server never became healthy")
        yield base
    finally:
        server.terminate()
        server.wait(timeout=15)
