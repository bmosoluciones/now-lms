"""Add configuracion csrf_seed column

Revision ID: 20260724_220000
Revises: 20260724_180000
Create Date: 2026-07-24 22:00:00

The Configuracion.csrf_seed column was added to the model but no
Alembic migration was created.  On existing databases the column may
still be named ``r`` (from the original rename in e083d66), so this
migration handles all three states:

  1. Column is still named ``r``  → rename it to ``csrf_seed``.
  2. Column is already ``csrf_seed`` → no-op.
  3. Column is missing entirely   → add it.
"""

from alembic import op
import sqlalchemy as sa

revision = "20260724_220000"
down_revision = "20260724_180000"
branch_labels = None
depends_on = None


def upgrade():
    inspector = sa.inspect(op.get_bind())

    if "configuracion" not in inspector.get_table_names():
        return

    columns = {col["name"] for col in inspector.get_columns("configuracion")}

    if "csrf_seed" in columns:
        return
    if "r" in columns:
        with op.batch_alter_table("configuracion") as batch_op:
            batch_op.alter_column("r", new_column_name="csrf_seed", existing_type=sa.LargeBinary())
        return

    with op.batch_alter_table("configuracion") as batch_op:
        batch_op.add_column("csrf_seed", sa.LargeBinary(), nullable=True)


def downgrade():
    inspector = sa.inspect(op.get_bind())

    if "configuracion" not in inspector.get_table_names():
        return

    columns = {col["name"] for col in inspector.get_columns("configuracion")}

    if "r" in columns:
        return
    if "csrf_seed" in columns:
        with op.batch_alter_table("configuracion") as batch_op:
            batch_op.alter_column("csrf_seed", new_column_name="r", existing_type=sa.LargeBinary())
