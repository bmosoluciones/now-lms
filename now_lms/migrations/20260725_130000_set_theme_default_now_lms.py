"""Set theme column to NOT NULL with default now_lms

Revision ID: 20260725_130000
Revises: 20260725_120000
Create Date: 2026-07-25 13:00:00

This migration:
1. Updates any NULL theme values to 'now_lms'.
2. Sets the theme column to NOT NULL with a server default of 'now_lms'.
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260725_130000"
down_revision = "20260725_120000"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if "style" in inspector.get_table_names():
        columns = {col["name"]: col for col in inspector.get_columns("style")}
        if "theme" in columns:
            # Update any NULL theme values to the default
            conn.execute(sa.text("UPDATE style SET theme = 'now_lms' WHERE theme IS NULL"))

            # Set NOT NULL and server default
            with op.batch_alter_table("style") as batch_op:
                batch_op.alter_column(
                    "theme",
                    existing_type=sa.String(40),
                    nullable=False,
                    server_default="now_lms",
                )


def downgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if "style" in inspector.get_table_names():
        columns = {col["name"]: col for col in inspector.get_columns("style")}
        if "theme" in columns:
            # Revert to nullable with no default
            with op.batch_alter_table("style") as batch_op:
                batch_op.alter_column(
                    "theme",
                    existing_type=sa.String(40),
                    nullable=True,
                    server_default=None,
                )
