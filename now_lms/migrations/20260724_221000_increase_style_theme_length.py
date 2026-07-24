"""Increase style.theme column length to 40 characters

Revision ID: 20260724_221000
Revises: 20260724_220000
Create Date: 2026-07-24 22:10:00

The style.theme column was originally defined as String(15) which is
too short for some theme names.  This migration increases it to
String(40).
"""

from alembic import op
import sqlalchemy as sa

revision = "20260724_221000"
down_revision = "20260724_220000"
branch_labels = None
depends_on = None


def upgrade():
    inspector = sa.inspect(op.get_bind())

    if "style" not in inspector.get_table_names():
        return

    columns = {col["name"]: col for col in inspector.get_columns("style")}

    if "theme" not in columns:
        return

    current_type = columns["theme"]["type"]
    current_length = getattr(current_type, "length", None)

    if current_length == 40:
        return

    with op.batch_alter_table("style") as batch_op:
        batch_op.alter_column(
            "theme",
            existing_type=sa.String(current_length),
            type_=sa.String(40),
            existing_nullable=True,
        )


def downgrade():
    inspector = sa.inspect(op.get_bind())

    if "style" not in inspector.get_table_names():
        return

    columns = {col["name"]: col for col in inspector.get_columns("style")}

    if "theme" not in columns:
        return

    with op.batch_alter_table("style") as batch_op:
        batch_op.alter_column(
            "theme",
            existing_type=sa.String(40),
            type_=sa.String(15),
            existing_nullable=True,
        )
