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

        with op.batch_alter_table("pago") as batch_op:
            if "programa" not in columns:
                batch_op.add_column(
                    sa.Column("programa", sa.String(26), sa.ForeignKey("programa.id", name="fk_pago_programa_id"), nullable=True),
                )
            batch_op.alter_column("curso", existing_type=sa.String(20), nullable=True)

        try:
            op.create_index("ix_pago_programa", "pago", ["programa"])
        except Exception:
            pass


def downgrade():
    """Revert the schema changes."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if "pago" in existing_tables:
        columns = [col["name"] for col in inspector.get_columns("pago")]

        # Drop index first to prevent "no such column: programa" during batch recreate
        try:
            op.drop_index("ix_pago_programa", table_name="pago")
        except Exception:
            pass

        with op.batch_alter_table("pago") as batch_op:
            if "programa" in columns:
                batch_op.drop_column("programa")
            batch_op.alter_column("curso", existing_type=sa.String(20), nullable=False)
