"""Add missing columns to Configuracion

Revision ID: 20260109_205100
Revises: 20260109_152700
Create Date: 2026-01-09 20:51:00

This migration adds missing columns to the Configuracion table that were
added to the model but did not have a corresponding migration:
- enable_file_uploads: Boolean flag to enable/disable file upload feature
- max_file_size: Maximum file size in megabytes for uploads
- enable_html_preformatted_descriptions: Boolean flag to enable HTML preformatted descriptions
- enable_footer: Boolean flag to show/hide footer

These columns were introduced between versions 1.1.0 and 1.1.2.
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260109_205100"
down_revision = "20260109_152700"
branch_labels = None
depends_on = None


def upgrade():
    """Add missing columns to configuracion table."""
    # Check if columns already exist before adding them
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col["name"] for col in inspector.get_columns("configuracion")]

    if "enable_file_uploads" not in columns:
        # Add column with default value False for backward compatibility
        op.add_column(
            "configuracion",
            sa.Column("enable_file_uploads", sa.Boolean(), nullable=False, server_default=sa.false()),
        )

    if "max_file_size" not in columns:
        # Add column with default value 1 (MB) for backward compatibility
        op.add_column(
            "configuracion",
            sa.Column("max_file_size", sa.Integer(), nullable=False, server_default=sa.text("1")),
        )

    if "enable_html_preformatted_descriptions" not in columns:
        # Add column with default value False for backward compatibility
        op.add_column(
            "configuracion",
            sa.Column("enable_html_preformatted_descriptions", sa.Boolean(), nullable=False, server_default=sa.false()),
        )

    if "enable_footer" not in columns:
        # Add column with default value True for backward compatibility
        op.add_column(
            "configuracion",
            sa.Column("enable_footer", sa.Boolean(), nullable=False, server_default=sa.true()),
        )


def downgrade():
    """Remove missing columns from configuracion table."""
    # Check if columns exist before dropping them
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col["name"] for col in inspector.get_columns("configuracion")]

    # Drop columns in reverse order
    if "enable_footer" in columns:
        op.drop_column("configuracion", "enable_footer")

    if "enable_html_preformatted_descriptions" in columns:
        op.drop_column("configuracion", "enable_html_preformatted_descriptions")

    if "max_file_size" in columns:
        op.drop_column("configuracion", "max_file_size")

    if "enable_file_uploads" in columns:
        op.drop_column("configuracion", "enable_file_uploads")
