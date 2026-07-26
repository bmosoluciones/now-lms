"""Rename static_pages table to custom_pages

Revision ID: 20260726_000000
Revises: 20260725_130000
Create Date: 2026-07-26 00:00:00

This migration:
1. Renames the static_pages table to custom_pages.
2. Handles both SQLite (batch rename) and other databases.
"""

from alembic import op
import sqlalchemy as sa

revision = "20260726_000000"
down_revision = "20260725_130000"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if "static_pages" in existing_tables and "custom_pages" not in existing_tables:
        op.rename_table("static_pages", "custom_pages")


def downgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if "custom_pages" in existing_tables and "static_pages" not in existing_tables:
        op.rename_table("custom_pages", "static_pages")
