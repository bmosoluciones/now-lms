"""Ensure mostrar_en_footer column exists in static_pages table

Revision ID: 20260118_184906
Revises: 20260110_150324
Create Date: 2026-01-18 18:49:06

This migration ensures that the mostrar_en_footer column exists in the
static_pages table. This is a safety migration to handle cases where:
1. The static_pages table was created without this column
2. Previous migrations were run in an inconsistent state
3. The column addition in 20260110_150324 failed for any reason

The migration verifies the table exists before checking/adding the column,
preventing NoSuchTableError exceptions.
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260118_184906"
down_revision = "20260110_150324"
branch_labels = None
depends_on = None


def upgrade():
    """Ensure mostrar_en_footer column exists in static_pages table."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # First, check if the static_pages table exists
    existing_tables = inspector.get_table_names()

    if "static_pages" in existing_tables:
        # Table exists, check if the column exists
        static_pages_columns = [col["name"] for col in inspector.get_columns("static_pages")]

        if "mostrar_en_footer" not in static_pages_columns:
            # Column doesn't exist, add it
            op.add_column("static_pages", sa.Column("mostrar_en_footer", sa.Boolean(), nullable=False, server_default="0"))
        # If column already exists, do nothing (idempotent)
    # If table doesn't exist, do nothing (it will be created by another migration)


def downgrade():
    """Remove mostrar_en_footer column from static_pages table if it exists."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # First, check if the static_pages table exists
    existing_tables = inspector.get_table_names()

    if "static_pages" in existing_tables:
        # Table exists, check if the column exists
        static_pages_columns = [col["name"] for col in inspector.get_columns("static_pages")]

        if "mostrar_en_footer" in static_pages_columns:
            # Column exists, drop it
            op.drop_column("static_pages", "mostrar_en_footer")
        # If column doesn't exist, do nothing (already removed or never existed)
    # If table doesn't exist, do nothing
