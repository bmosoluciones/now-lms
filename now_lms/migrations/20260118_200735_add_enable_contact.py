"""Add enable_contact column to configuracion table

Revision ID: 20260118_200735
Revises: 20260118_185502
Create Date: 2026-01-18 20:07:35

This migration adds the enable_contact column to the configuracion table
to allow system administrators to show or hide the Contact page in the navbar.

The column defaults to False to maintain backward compatibility.
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260118_200735"
down_revision = "20260118_185502"
branch_labels = None
depends_on = None


def upgrade():
    """Add enable_contact column to configuracion table."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if "configuracion" in existing_tables:
        columns = [col["name"] for col in inspector.get_columns("configuracion")]

        if "enable_contact" not in columns:
            op.add_column(
                "configuracion",
                sa.Column("enable_contact", sa.Boolean(), nullable=False, server_default=sa.false()),
            )


def downgrade():
    """Remove enable_contact column from configuracion table."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if "configuracion" in existing_tables:
        columns = [col["name"] for col in inspector.get_columns("configuracion")]

        if "enable_contact" in columns:
            op.drop_column("configuracion", "enable_contact")
