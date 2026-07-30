# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.

"""The dedup half of the unique-enrollment migration.

Existing installs are likely to hold duplicate (usuario, curso) rows already, so
the migration collapses them before adding the constraint. These tests drive
``upgrade()`` through a real Alembic operations context against a throwaway
SQLite database, which covers the keeper-selection and child-repoint logic.

Constraint *behaviour* — that the database then refuses a duplicate, that a
re-run is a no-op, that downgrade drops it cleanly — is verified separately
against real PostgreSQL, because SQLite is too permissive about constraints and
foreign keys for a green run here to prove it. See PR #234 for that run.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations

MIGRATION_PATH = (
    Path(__file__).resolve().parent.parent
    / "now_lms"
    / "migrations"
    / "20260730_000000_unique_enrollment_per_student_and_course.py"
)

SCHEMA = [
    """
    CREATE TABLE estudiante_curso (
        id VARCHAR(26) PRIMARY KEY,
        curso VARCHAR(20) NOT NULL,
        usuario VARCHAR(150) NOT NULL,
        vigente BOOLEAN,
        pago VARCHAR(26)
    )
    """,
    """
    CREATE TABLE remote_enrollment_requests (
        id VARCHAR(26) PRIMARY KEY,
        request_id VARCHAR(100) NOT NULL UNIQUE,
        enrollment_id VARCHAR(26) REFERENCES estudiante_curso(id),
        status VARCHAR(50) NOT NULL
    )
    """,
]


@pytest.fixture()
def migration():
    spec = importlib.util.spec_from_file_location("mig_unique_enrollment", MIGRATION_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def engine(tmp_path):
    eng = sa.create_engine(f"sqlite:///{tmp_path / 'dedup.db'}")
    with eng.begin() as conn:
        for statement in SCHEMA:
            conn.execute(sa.text(statement))
    yield eng
    eng.dispose()


def _enroll(conn, row_id, usuario, curso, vigente=True, pago=None):
    conn.execute(
        sa.text(
            "INSERT INTO estudiante_curso (id, curso, usuario, vigente, pago) "
            "VALUES (:id, :curso, :usuario, :vigente, :pago)"
        ),
        {"id": row_id, "curso": curso, "usuario": usuario, "vigente": vigente, "pago": pago},
    )


def _run_upgrade(engine, migration):
    with engine.begin() as conn:
        ctx = MigrationContext.configure(conn)
        with Operations.context(ctx):
            migration.upgrade()


def _ids(engine, usuario="dup@example.test", curso="DUP"):
    with engine.connect() as conn:
        return [
            r[0]
            for r in conn.execute(
                sa.text("SELECT id FROM estudiante_curso WHERE usuario = :u AND curso = :c"),
                {"u": usuario, "c": curso},
            )
        ]


def test_duplicates_collapse_to_one_row(engine, migration):
    with engine.begin() as conn:
        _enroll(conn, "A", "dup@example.test", "DUP")
        _enroll(conn, "B", "dup@example.test", "DUP")
        _enroll(conn, "C", "dup@example.test", "DUP")

    _run_upgrade(engine, migration)

    assert len(_ids(engine)) == 1


def test_the_row_with_a_payment_is_kept(engine, migration):
    """Keeper preference: a paid enrollment outranks an unpaid one."""
    with engine.begin() as conn:
        _enroll(conn, "AAA_unpaid", "dup@example.test", "DUP", pago=None)
        _enroll(conn, "ZZZ_paid", "dup@example.test", "DUP", pago="P1")

    _run_upgrade(engine, migration)

    # ZZZ sorts last by id, so an id-only rule would have kept AAA.
    assert _ids(engine) == ["ZZZ_paid"]


def test_an_active_row_outranks_an_inactive_one(engine, migration):
    """Second preference, when neither row carries a payment."""
    with engine.begin() as conn:
        _enroll(conn, "AAA_inactive", "dup@example.test", "DUP", vigente=False)
        _enroll(conn, "ZZZ_active", "dup@example.test", "DUP", vigente=True)

    _run_upgrade(engine, migration)

    assert _ids(engine) == ["ZZZ_active"]


def test_oldest_wins_when_nothing_else_separates_them(engine, migration):
    """Last resort: lowest id, which is the oldest ULID."""
    with engine.begin() as conn:
        _enroll(conn, "AAA_older", "dup@example.test", "DUP")
        _enroll(conn, "ZZZ_newer", "dup@example.test", "DUP")

    _run_upgrade(engine, migration)

    assert _ids(engine) == ["AAA_older"]


def test_a_child_request_is_repointed_not_orphaned(engine, migration):
    """A remote_enrollment_request pointing at a discarded row must follow the keeper."""
    with engine.begin() as conn:
        _enroll(conn, "KEEP", "dup@example.test", "DUP", pago="P1")
        _enroll(conn, "DROP_ME", "dup@example.test", "DUP", pago=None)
        conn.execute(
            sa.text(
                "INSERT INTO remote_enrollment_requests (id, request_id, enrollment_id, status) "
                "VALUES ('R1', 'req-1', 'DROP_ME', 'processed')"
            )
        )

    _run_upgrade(engine, migration)

    with engine.connect() as conn:
        pointed_at = conn.execute(
            sa.text("SELECT enrollment_id FROM remote_enrollment_requests WHERE request_id = 'req-1'")
        ).scalar()
    assert pointed_at == "KEEP"


def test_unrelated_enrollments_are_left_alone(engine, migration):
    with engine.begin() as conn:
        _enroll(conn, "A", "dup@example.test", "DUP")
        _enroll(conn, "B", "dup@example.test", "DUP")
        _enroll(conn, "OTHER_COURSE", "dup@example.test", "OTHER")
        _enroll(conn, "OTHER_USER", "someone@example.test", "DUP")

    _run_upgrade(engine, migration)

    with engine.connect() as conn:
        total = conn.execute(sa.text("SELECT count(*) FROM estudiante_curso")).scalar()
    assert total == 3  # one survivor for the duplicated pair, plus the two untouched rows


def test_upgrade_is_a_no_op_without_duplicates(engine, migration):
    with engine.begin() as conn:
        _enroll(conn, "ONLY", "dup@example.test", "DUP")

    _run_upgrade(engine, migration)

    assert _ids(engine) == ["ONLY"]


def test_upgrade_survives_a_missing_child_table(tmp_path, migration):
    """An install without remote_enrollment_requests must still migrate."""
    eng = sa.create_engine(f"sqlite:///{tmp_path / 'nochild.db'}")
    with eng.begin() as conn:
        conn.execute(sa.text(SCHEMA[0]))
        _enroll(conn, "A", "dup@example.test", "DUP")
        _enroll(conn, "B", "dup@example.test", "DUP")

    _run_upgrade(eng, migration)

    with eng.connect() as conn:
        remaining = conn.execute(sa.text("SELECT count(*) FROM estudiante_curso")).scalar()
    eng.dispose()
    assert remaining == 1
