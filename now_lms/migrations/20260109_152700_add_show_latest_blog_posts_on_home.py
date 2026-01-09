"""Add show_latest_blog_posts_on_home to Configuracion

Revision ID: 20260109_152700
Revises: 20260109_152634
Create Date: 2026-01-09 15:27:00

This migration adds the 'show_latest_blog_posts_on_home' field to the
Configuracion table to allow administrators to display the latest 3 blog
posts on the homepage.

The default value is False to maintain backward compatibility.
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260109_152700"
down_revision = "20260109_152634"
branch_labels = None
depends_on = None


def upgrade():
    """Add show_latest_blog_posts_on_home column to configuracion table."""
    # Check if column already exists before adding it
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col["name"] for col in inspector.get_columns("configuracion")]

    if "show_latest_blog_posts_on_home" not in columns:
        # Add column with default value False for backward compatibility
        op.add_column(
            "configuracion",
            sa.Column("show_latest_blog_posts_on_home", sa.Boolean(), nullable=False, server_default=sa.false()),
        )


def downgrade():
    """Remove show_latest_blog_posts_on_home column from configuracion table."""
    # Check if column exists before dropping it
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col["name"] for col in inspector.get_columns("configuracion")]

    if "show_latest_blog_posts_on_home" in columns:
        op.drop_column("configuracion", "show_latest_blog_posts_on_home")
