"""Rename r to csrf_seed and increase theme column length to 40

Revision ID: 20260725_120000
Revises: 20260724_180000
Create Date: 2026-07-25 12:00:00

This migration:
1. Renames the 'r' column on 'configuracion' table to 'csrf_seed'.
   If 'r' does not exist but 'csrf_seed' is also missing, 'csrf_seed' is created.
2. Increases the 'theme' column on 'style' table to 40 characters instead of 15 or 10.
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260725_120000"
down_revision = "20260724_180000"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # 1. Handle configuracion table (rename r to csrf_seed or add csrf_seed)
    if "configuracion" in inspector.get_table_names():
        columns = {col["name"]: col for col in inspector.get_columns("configuracion")}

        if "r" in columns and "csrf_seed" in columns:
            # Some installations received csrf_seed from an earlier local
            # migration while retaining the legacy r column. Preserve any
            # values that were only stored in r, then remove the obsolete
            # duplicate so the schema matches the model.
            conn.execute(sa.text("UPDATE configuracion SET csrf_seed = COALESCE(csrf_seed, r) WHERE r IS NOT NULL"))
            with op.batch_alter_table("configuracion") as batch_op:
                batch_op.drop_column("r")
        elif "r" in columns:
            # Rename r to csrf_seed
            with op.batch_alter_table("configuracion") as batch_op:
                batch_op.alter_column("r", new_column_name="csrf_seed", existing_type=sa.LargeBinary(), existing_nullable=True)
        elif "csrf_seed" not in columns:
            # Add csrf_seed as a new column
            with op.batch_alter_table("configuracion") as batch_op:
                batch_op.add_column(sa.Column("csrf_seed", sa.LargeBinary(), nullable=True))

    # 2. Handle style table (increase theme column length to 40)
    if "style" in inspector.get_table_names():
        columns = {col["name"]: col for col in inspector.get_columns("style")}
        if "theme" in columns:
            current_type = columns["theme"]["type"]
            current_length = getattr(current_type, "length", None)

            # If current length is not already 40, alter the column
            if current_length != 40:
                with op.batch_alter_table("style") as batch_op:
                    batch_op.alter_column(
                        "theme", existing_type=sa.String(current_length or 15), type_=sa.String(40), existing_nullable=True
                    )


def downgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # 1. Handle configuracion table (rename csrf_seed back to r)
    if "configuracion" in inspector.get_table_names():
        columns = {col["name"]: col for col in inspector.get_columns("configuracion")}
        if "csrf_seed" in columns:
            with op.batch_alter_table("configuracion") as batch_op:
                batch_op.alter_column("csrf_seed", new_column_name="r", existing_type=sa.LargeBinary(), existing_nullable=True)

    # 2. Handle style table (restore theme column length back to 15)
    if "style" in inspector.get_table_names():
        columns = {col["name"]: col for col in inspector.get_columns("style")}
        if "theme" in columns:
            current_type = columns["theme"]["type"]
            current_length = getattr(current_type, "length", None)

            if current_length != 15:
                with op.batch_alter_table("style") as batch_op:
                    batch_op.alter_column(
                        "theme", existing_type=sa.String(current_length or 40), type_=sa.String(15), existing_nullable=True
                    )
