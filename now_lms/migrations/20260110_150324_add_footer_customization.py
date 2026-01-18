"""Add footer customization features

Revision ID: 20260110_150324
Revises: 20260110_035505
Create Date: 2026-01-10 15:03:24

This migration adds:
1. A new table 'enlaces_utiles' for customizable footer links
2. A new field 'mostrar_en_footer' to static_pages table to control
   which static pages are displayed in the footer's "Acerca de" section

This enables administrators to fully customize the footer content.
"""

from alembic import op
import sqlalchemy as sa
from now_lms.db import utc_now
from datetime import date


# revision identifiers, used by Alembic.
revision = "20260110_150324"
down_revision = "20260110_035505"
branch_labels = None
depends_on = None


def upgrade():
    """Add footer customization features."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # 1. Create enlaces_utiles table if it doesn't exist
    existing_tables = inspector.get_table_names()

    if "enlaces_utiles" not in existing_tables:
        op.create_table(
            "enlaces_utiles",
            sa.Column("id", sa.String(26), primary_key=True, nullable=False, index=True),
            sa.Column("timestamp", sa.DateTime, nullable=False, default=utc_now),
            sa.Column("creado", sa.Date, nullable=False, default=date.today),
            sa.Column("creado_por", sa.String(150), nullable=True),
            sa.Column("modificado", sa.DateTime, nullable=True),
            sa.Column("modificado_por", sa.String(150), nullable=True),
            sa.Column("titulo", sa.String(100), nullable=False),
            sa.Column("url", sa.String(500), nullable=False),
            sa.Column("orden", sa.Integer(), nullable=False, default=0),
            sa.Column("activo", sa.Boolean(), nullable=False, default=True),
        )

    # 2. Add mostrar_en_footer column to static_pages table if it doesn't exist
    if "static_pages" in existing_tables:
        static_pages_columns = [col["name"] for col in inspector.get_columns("static_pages")]

        if "mostrar_en_footer" not in static_pages_columns:
            op.add_column("static_pages", sa.Column("mostrar_en_footer", sa.Boolean(), nullable=False, server_default="0"))


def downgrade():
    """Remove footer customization features."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # 1. Drop enlaces_utiles table if it exists
    existing_tables = inspector.get_table_names()

    if "enlaces_utiles" in existing_tables:
        op.drop_table("enlaces_utiles")

    # 2. Drop mostrar_en_footer column from static_pages if it exists
    if "static_pages" in existing_tables:
        static_pages_columns = [col["name"] for col in inspector.get_columns("static_pages")]

        if "mostrar_en_footer" in static_pages_columns:
            op.drop_column("static_pages", "mostrar_en_footer")
