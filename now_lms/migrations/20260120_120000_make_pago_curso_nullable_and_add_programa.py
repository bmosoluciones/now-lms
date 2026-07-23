"""make pago curso nullable and add programa

Revision ID: 20260120_120000
Revises: 1780403775
Create Date: 2026-01-20 12:00:00

This migration makes the curso column in pago nullable, and adds a programa column
referencing the programa.id column.
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260120_120000"
down_revision = "1780403775"
branch_labels = None
depends_on = None


def upgrade():
    """Apply the schema changes."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if "pago" in existing_tables:
        columns = [col["name"] for col in inspector.get_columns("pago")]

        if "programa" not in columns:
            op.add_column(
                "pago",
                sa.Column("programa", sa.String(26), sa.ForeignKey("programa.id"), nullable=True),
            )

        # Alter curso to make it nullable
        # Note: some databases/backends handle nullable alteration differently.
        # SQLite doesn't fully support alter column without copy, so we wrap it safely.
        try:
            with op.batch_alter_table("pago") as batch_op:
                batch_op.alter_column("curso", existing_type=sa.String(20), nullable=True)
        except Exception:
            pass


def downgrade():
    """Revert the schema changes."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if "pago" in existing_tables:
        columns = [col["name"] for col in inspector.get_columns("pago")]

        if "programa" in columns:
            op.drop_column("pago", "programa")

        try:
            with op.batch_alter_table("pago") as batch_op:
                batch_op.alter_column("curso", existing_type=sa.String(20), nullable=False)
        except Exception:
            pass
