"""Fix Pago.monto column precision and scale

Revision ID: 20260724_180000
Revises: 20260724_120000
Create Date: 2026-07-24 18:00:00

The Pago.monto column was defined as Numeric(asdecimal=True) without
explicit precision and scale, which in MySQL defaults to DECIMAL(10,0),
causing fractional amounts like 99.99 to be rounded to 100.
This migration alters the column to Numeric(10, 2) to preserve cents.
"""

from alembic import op
import sqlalchemy as sa


revision = "20260724_180000"
down_revision = "20260724_120000"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if "pago" not in inspector.get_table_names():
        return

    columns = {col["name"]: col for col in inspector.get_columns("pago")}
    if "monto" not in columns:
        return

    current_type = columns["monto"]["type"]
    current_precision = getattr(current_type, "precision", None)
    current_scale = getattr(current_type, "scale", None)

    if current_precision == 10 and current_scale == 2:
        return

    with op.batch_alter_table("pago") as batch_op:
        batch_op.alter_column(
            "monto",
            existing_type=sa.Numeric(precision=current_precision, scale=current_scale, asdecimal=True),
            type_=sa.Numeric(10, 2, asdecimal=True),
            existing_nullable=True,
        )


def downgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if "pago" not in inspector.get_table_names():
        return

    columns = {col["name"]: col for col in inspector.get_columns("pago")}
    if "monto" not in columns:
        return

    with op.batch_alter_table("pago") as batch_op:
        batch_op.alter_column(
            "monto",
            existing_type=sa.Numeric(10, 2, asdecimal=True),
            type_=sa.Numeric(asdecimal=True),
            existing_nullable=True,
        )
