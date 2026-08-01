# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.

"""Enforce one enrollment per (usuario, curso).

A second EstudianteCurso row for the same student and course has never meant
anything — it just inflates every enrollment count that reads the table. The
enrollment paths upsert now, and this stops a bug or a double-submit from
getting past them.

Existing databases very likely already contain duplicates, so this migration
cleans up before adding the constraint. For each duplicated pair it keeps one
row, preferring (in order) a row that carries a payment, then an active one,
then the oldest — and repoints anything referencing a discarded row at the
keeper rather than orphaning it.

Revision ID: 20260730_000000
Revises: 20260726_000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260730_000000"
down_revision = "20260726_000000"
branch_labels = None
depends_on = None

CONSTRAINT_NAME = "uq_estudiante_curso_usuario_curso"


def _duplicate_groups(bind) -> list[tuple[str, str]]:
    """Return the (usuario, curso) pairs that have more than one enrollment row."""
    rows = bind.execute(
        sa.text("SELECT usuario, curso FROM estudiante_curso " "GROUP BY usuario, curso HAVING COUNT(*) > 1")
    ).fetchall()
    return [(row[0], row[1]) for row in rows]


def _rows_for(bind, usuario: str, curso: str) -> list[tuple[str, str | None, bool | None]]:
    """Return (id, pago, vigente) for one pair, best keeper first.

    Preference order: a row with a payment, then an active row, then the oldest.
    Ordering happens in Python so the same rule applies on every backend —
    boolean and NULL ordering differ between SQLite, PostgreSQL and MySQL.
    """
    rows = bind.execute(
        sa.text("SELECT id, pago, vigente FROM estudiante_curso " "WHERE usuario = :usuario AND curso = :curso"),
        {"usuario": usuario, "curso": curso},
    ).fetchall()
    return sorted(rows, key=lambda r: (r[1] is None, not bool(r[2]), r[0]))


def _table_exists(inspector, name: str) -> bool:
    return name in inspector.get_table_names()


def upgrade() -> None:
    """Collapse duplicate enrollments, then add the unique constraint."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not _table_exists(inspector, "estudiante_curso"):
        return

    has_remote_requests = _table_exists(inspector, "remote_enrollment_requests")

    for usuario, curso in _duplicate_groups(bind):
        ordered = _rows_for(bind, usuario, curso)
        keeper_id = ordered[0][0]
        discarded = [row[0] for row in ordered[1:]]
        if not discarded:
            continue

        if has_remote_requests:
            # Do not orphan a request that points at a row we are about to drop.
            for discarded_id in discarded:
                bind.execute(
                    sa.text(
                        "UPDATE remote_enrollment_requests SET enrollment_id = :keeper " "WHERE enrollment_id = :discarded"
                    ),
                    {"keeper": keeper_id, "discarded": discarded_id},
                )

        for discarded_id in discarded:
            bind.execute(
                sa.text("DELETE FROM estudiante_curso WHERE id = :discarded"),
                {"discarded": discarded_id},
            )

    existing = {uc.get("name") for uc in inspector.get_unique_constraints("estudiante_curso")}
    if CONSTRAINT_NAME not in existing:
        with op.batch_alter_table("estudiante_curso") as batch_op:
            batch_op.create_unique_constraint(CONSTRAINT_NAME, ["usuario", "curso"])


def downgrade() -> None:
    """Drop the constraint. The collapsed duplicate rows are not restored."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not _table_exists(inspector, "estudiante_curso"):
        return

    existing = {uc.get("name") for uc in inspector.get_unique_constraints("estudiante_curso")}
    if CONSTRAINT_NAME in existing:
        with op.batch_alter_table("estudiante_curso") as batch_op:
            batch_op.drop_constraint(CONSTRAINT_NAME, type_="unique")
