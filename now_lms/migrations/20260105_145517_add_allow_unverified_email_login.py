"""Add allow_unverified_email_login to Configuracion

Revision ID: 20260105_145517
Revises:
Create Date: 2026-01-05 14:55:17

This migration adds the 'allow_unverified_email_login' field to the
Configuracion table to allow administrators to enable restricted access
for users who have not verified their email addresses.

The default value is False to maintain backward compatibility.
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260105_145517"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Add allow_unverified_email_login column to configuracion table."""
    # Check if column already exists before adding it
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col["name"] for col in inspector.get_columns("configuracion")]

    if "allow_unverified_email_login" not in columns:
        # Add column with default value False for backward compatibility
        op.add_column(
            "configuracion", sa.Column("allow_unverified_email_login", sa.Boolean(), nullable=False, server_default=sa.false())
        )


def downgrade():
    """Remove allow_unverified_email_login column from configuracion table."""
    # Check if column exists before dropping it
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col["name"] for col in inspector.get_columns("configuracion")]

    if "allow_unverified_email_login" in columns:
        op.drop_column("configuracion", "allow_unverified_email_login")
