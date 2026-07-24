"""Increase programa.nombre column length to 150

Revision ID: 20260724_120000
Revises: 20260120_120000
Create Date: 2026-07-24 12:00:00

The programa.nombre column was limited to 20 characters, which is too
restrictive for real program names (for reference, curso.nombre allows
150 characters). This migration increases the limit to 150 characters.

programa.codigo remains String(10) — code identifiers are intentionally
short. New databases created via create_all() will inherit the schema
from the model directly.
"""

from alembic import op
import sqlalchemy as sa

revision = "20260724_120000"
down_revision = "20260120_120000"
branch_labels = None
depends_on = None


def upgrade():
    """Increase programa.nombre length to 150 characters."""
    inspector = sa.inspect(op.get_bind())
    if "programa" not in inspector.get_table_names():
        return
    columns = {col["name"]: col for col in inspector.get_columns("programa")}
    nombre = columns.get("nombre")
    if nombre is not None and getattr(nombre["type"], "length", None) != 150:
        with op.batch_alter_table("programa") as batch_op:
            batch_op.alter_column("nombre", existing_type=sa.String(20), type_=sa.String(150), existing_nullable=False)


def downgrade():
    """Restore programa.nombre length to 20 characters."""
    inspector = sa.inspect(op.get_bind())
    if "programa" not in inspector.get_table_names():
        return
    with op.batch_alter_table("programa") as batch_op:
        batch_op.alter_column("nombre", existing_type=sa.String(150), type_=sa.String(20), existing_nullable=False)
