"""Increase programa nombre and codigo column lengths

Revision ID: 20260724_120000
Revises: 20260120_120000
Create Date: 2026-07-24 12:00:00

The programa.nombre column was limited to 20 characters and programa.codigo
to 10 characters, which is too restrictive for real program names and codes
(for reference, curso.nombre allows 150 characters and curso.codigo 20).
This migration increases programa.nombre to 150 characters, programa.codigo
to 20 characters, and the referencing programa_curso.programa foreign key
column to 20 characters to keep foreign key types consistent.

This migration is idempotent and safe to run multiple times.
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260724_120000"
down_revision = "20260120_120000"
branch_labels = None
depends_on = None


def _column_length(inspector, table: str, column: str):
    """Return the current length of a string column, or None."""
    if table not in inspector.get_table_names():
        return None
    for col in inspector.get_columns(table):
        if col["name"] == column:
            return getattr(col["type"], "length", None)
    return None


def upgrade():
    """Increase programa nombre/codigo lengths and keep FK types consistent."""
    inspector = sa.inspect(op.get_bind())

    if "programa" in inspector.get_table_names():
        with op.batch_alter_table("programa") as batch_op:
            if _column_length(inspector, "programa", "nombre") != 150:
                batch_op.alter_column("nombre", existing_type=sa.String(20), type_=sa.String(150), existing_nullable=False)
            if _column_length(inspector, "programa", "codigo") != 20:
                batch_op.alter_column("codigo", existing_type=sa.String(10), type_=sa.String(20), existing_nullable=False)

    if "programa_curso" in inspector.get_table_names():
        with op.batch_alter_table("programa_curso") as batch_op:
            if _column_length(inspector, "programa_curso", "programa") != 20:
                batch_op.alter_column("programa", existing_type=sa.String(10), type_=sa.String(20), existing_nullable=False)


def downgrade():
    """Restore programa nombre/codigo lengths to their previous sizes."""
    inspector = sa.inspect(op.get_bind())

    if "programa_curso" in inspector.get_table_names():
        with op.batch_alter_table("programa_curso") as batch_op:
            batch_op.alter_column("programa", existing_type=sa.String(20), type_=sa.String(10), existing_nullable=False)

    if "programa" in inspector.get_table_names():
        with op.batch_alter_table("programa") as batch_op:
            batch_op.alter_column("nombre", existing_type=sa.String(150), type_=sa.String(20), existing_nullable=False)
            batch_op.alter_column("codigo", existing_type=sa.String(20), type_=sa.String(10), existing_nullable=False)
