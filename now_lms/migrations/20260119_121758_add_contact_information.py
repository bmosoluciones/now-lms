"""Add contact information fields to configuracion table

Revision ID: 20260119_121758
Revises: 20260118_200735
Create Date: 2026-01-19 12:17:58

This migration adds contact information fields to the configuracion table
to allow system administrators to store and display business contact details
(address, email, phone, mobile, WhatsApp) on the contact page.

The columns are nullable to maintain backward compatibility with existing installations.
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260119_121758"
down_revision = "20260118_200735"
branch_labels = None
depends_on = None


def upgrade():
    """Add contact information fields to configuracion table."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if "configuracion" in existing_tables:
        columns = [col["name"] for col in inspector.get_columns("configuracion")]

        if "contact_address" not in columns:
            op.add_column(
                "configuracion",
                sa.Column("contact_address", sa.String(500), nullable=True),
            )

        if "contact_email" not in columns:
            op.add_column(
                "configuracion",
                sa.Column("contact_email", sa.String(150), nullable=True),
            )

        if "contact_phone" not in columns:
            op.add_column(
                "configuracion",
                sa.Column("contact_phone", sa.String(50), nullable=True),
            )

        if "contact_mobile" not in columns:
            op.add_column(
                "configuracion",
                sa.Column("contact_mobile", sa.String(50), nullable=True),
            )

        if "contact_whatsapp" not in columns:
            op.add_column(
                "configuracion",
                sa.Column("contact_whatsapp", sa.String(50), nullable=True),
            )


def downgrade():
    """Remove contact information fields from configuracion table."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if "configuracion" in existing_tables:
        columns = [col["name"] for col in inspector.get_columns("configuracion")]

        if "contact_whatsapp" in columns:
            op.drop_column("configuracion", "contact_whatsapp")

        if "contact_mobile" in columns:
            op.drop_column("configuracion", "contact_mobile")

        if "contact_phone" in columns:
            op.drop_column("configuracion", "contact_phone")

        if "contact_email" in columns:
            op.drop_column("configuracion", "contact_email")

        if "contact_address" in columns:
            op.drop_column("configuracion", "contact_address")
