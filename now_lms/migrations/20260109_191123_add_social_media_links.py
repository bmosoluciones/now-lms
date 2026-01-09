"""Add social media links to Configuracion

Revision ID: 20260109_191123
Revises: 20260109_152700
Create Date: 2026-01-09 19:11:23

This migration adds social media link fields to the Configuracion table
to allow administrators to configure social media URLs that will be displayed
in the footer of all themes.

Supported platforms: Facebook, Twitter, LinkedIn, YouTube, Instagram, GitHub
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260109_191123"
down_revision = "20260109_152700"
branch_labels = None
depends_on = None


def upgrade():
    """Add social media link columns to configuracion table."""
    # Check if columns already exist before adding them
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col["name"] for col in inspector.get_columns("configuracion")]

    # Add social media columns if they don't exist
    social_fields = [
        "social_facebook",
        "social_twitter",
        "social_linkedin",
        "social_youtube",
        "social_instagram",
        "social_github",
    ]

    for field in social_fields:
        if field not in columns:
            op.add_column("configuracion", sa.Column(field, sa.String(200), nullable=True))


def downgrade():
    """Remove social media link columns from configuracion table."""
    # Check if columns exist before dropping them
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col["name"] for col in inspector.get_columns("configuracion")]

    # Drop social media columns if they exist
    social_fields = [
        "social_facebook",
        "social_twitter",
        "social_linkedin",
        "social_youtube",
        "social_instagram",
        "social_github",
    ]

    for field in social_fields:
        if field in columns:
            op.drop_column("configuracion", field)
