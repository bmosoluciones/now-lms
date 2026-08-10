# SPDX-License-Identifier: Apache-2.0
"""Repair user_events foreign keys on databases that already ran 20260109_152634.

WHY THIS EXISTS

`Curso.user_events` relies on the database cascading the delete, and the model now
declares `passive_deletes="all"` on that basis. The constraints that make it true
are created by migration `20260109_152634`, whose `op.create_table` calls are
guarded by ``if "user_events" not in existing_tables``. That guard is correct — it
is what lets the migration run against a schema built by `create_all()` — but it
also means editing that file only ever fixes databases that have NOT yet created
the table.

Any deployment that ran `20260109_152634` for real still carries the original
constraints, without ON DELETE CASCADE. On those, deleting a course with calendar
events fails on the foreign key instead of cascading, which is precisely the bug
the model change was meant to close.

So the historical migration stays as it is, and this one repairs what it cannot
reach. Found by Greptile on PR #78, and matching a caveat already recorded when
that model change was written.

WHAT IT DOES

Discovers the live constraint names through the inspector rather than assuming
them, because they are auto-generated and differ between backends and between
databases. Drops and recreates only the four that should cascade, leaving
``user_id -> usuario.usuario`` alone: a user is deactivated, never hard-deleted
alongside their history.

Idempotent by construction. A constraint already carrying the right rule is left
untouched, so this is a no-op on a freshly created schema and safe to re-run.

Revision ID: 20260810_000000
Revises: 20260730_000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20260810_000000"
down_revision = "20260730_000000"
branch_labels = None
depends_on = None

TABLA = "user_events"

# column -> (referenced table, referenced column). user_id is deliberately absent.
CASCADAS = {
    "course_id": ("curso", "codigo"),
    "section_id": ("curso_seccion", "id"),
    "resource_id": ("curso_recurso", "id"),
    "evaluation_id": ("evaluation", "id"),
}


def _fks_actuales(inspector) -> dict[str, dict]:
    """Map constrained column -> its live foreign key definition."""
    encontrados: dict[str, dict] = {}
    for fk in inspector.get_foreign_keys(TABLA):
        columnas = fk.get("constrained_columns") or []
        if len(columnas) == 1:
            encontrados[columnas[0]] = fk
    return encontrados


def _aplicar(ondelete: str | None) -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if TABLA not in inspector.get_table_names():
        # Nothing to repair. A deployment that never created the table will get the
        # correct constraints from 20260109_152634 when it does.
        return

    actuales = _fks_actuales(inspector)

    for columna, (tabla_ref, columna_ref) in CASCADAS.items():
        fk = actuales.get(columna)
        if fk is None:
            continue  # column or constraint absent; leave the schema alone

        regla_actual = (fk.get("options") or {}).get("ondelete")
        if (regla_actual or None) == (ondelete or None):
            continue  # already correct — keeps this migration a no-op on fresh schemas

        nombre = fk.get("name")
        if not nombre:
            # An unnamed constraint cannot be dropped portably. Skip rather than
            # guess a name and fail the whole upgrade on one table.
            continue

        with op.batch_alter_table(TABLA) as batch:
            batch.drop_constraint(nombre, type_="foreignkey")
            batch.create_foreign_key(nombre, tabla_ref, [columna], [columna_ref], ondelete=ondelete)


def upgrade():
    """Add ON DELETE CASCADE to the four child foreign keys."""
    _aplicar("CASCADE")


def downgrade():
    """Return the four foreign keys to no delete rule."""
    _aplicar(None)
