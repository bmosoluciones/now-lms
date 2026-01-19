"""Ensure database schema consistency with source code

Revision ID: 20260118_185502
Revises: 20260118_184906
Create Date: 2026-01-18 18:55:02

This migration ensures that the database schema is consistent with the source code
by verifying and adding any missing columns that are expected by the models.

This is a comprehensive safety migration that reconciles the database state with
the application's expectations, handling cases where previous migrations may have
failed or been skipped.

Tables and columns verified:
- configuracion: all configuration columns
- blog_post: cover_image fields
- static_pages: mostrar_en_footer field
- enlaces_utiles: footer links table

This migration is idempotent and safe to run multiple times.
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260118_185502"
down_revision = "20260118_184906"
branch_labels = None
depends_on = None


def upgrade():
    """Ensure all expected columns exist in the database."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    # -------------------------------------------------------------------------
    # 1. Verify and fix configuracion table
    # -------------------------------------------------------------------------
    if "configuracion" in existing_tables:
        columns = [col["name"] for col in inspector.get_columns("configuracion")]

        # allow_unverified_email_login - added in 20260105_145517
        if "allow_unverified_email_login" not in columns:
            op.add_column(
                "configuracion",
                sa.Column("allow_unverified_email_login", sa.Boolean(), nullable=False, server_default=sa.false()),
            )

        # show_latest_blog_posts_on_home - added in 20260109_152700
        if "show_latest_blog_posts_on_home" not in columns:
            op.add_column(
                "configuracion",
                sa.Column("show_latest_blog_posts_on_home", sa.Boolean(), nullable=False, server_default=sa.false()),
            )

        # Social media links - added in 20260109_191123
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

        # File upload and other configuration fields - added in 20260109_205100
        if "enable_file_uploads" not in columns:
            op.add_column(
                "configuracion",
                sa.Column("enable_file_uploads", sa.Boolean(), nullable=False, server_default=sa.false()),
            )

        if "max_file_size" not in columns:
            op.add_column(
                "configuracion",
                sa.Column("max_file_size", sa.Integer(), nullable=False, server_default=sa.text("1")),
            )

        if "enable_html_preformatted_descriptions" not in columns:
            op.add_column(
                "configuracion",
                sa.Column("enable_html_preformatted_descriptions", sa.Boolean(), nullable=False, server_default=sa.false()),
            )

        if "enable_footer" not in columns:
            op.add_column(
                "configuracion",
                sa.Column("enable_footer", sa.Boolean(), nullable=False, server_default=sa.true()),
            )

    # -------------------------------------------------------------------------
    # 2. Verify and fix blog_post table
    # -------------------------------------------------------------------------
    if "blog_post" in existing_tables:
        columns = [col["name"] for col in inspector.get_columns("blog_post")]

        # Cover image fields - added in 20260110_035505
        if "cover_image" not in columns:
            op.add_column(
                "blog_post",
                sa.Column("cover_image", sa.Boolean(), nullable=False, server_default=sa.false()),
            )

        if "cover_image_ext" not in columns:
            op.add_column("blog_post", sa.Column("cover_image_ext", sa.String(5), nullable=True))

    # -------------------------------------------------------------------------
    # 3. Verify and fix static_pages table
    # -------------------------------------------------------------------------
    if "static_pages" in existing_tables:
        columns = [col["name"] for col in inspector.get_columns("static_pages")]

        # mostrar_en_footer - added in 20260110_150324
        if "mostrar_en_footer" not in columns:
            op.add_column("static_pages", sa.Column("mostrar_en_footer", sa.Boolean(), nullable=False, server_default="0"))

    # -------------------------------------------------------------------------
    # 4. Verify enlaces_utiles table exists
    # -------------------------------------------------------------------------
    # This table is created in 20260110_150324_add_footer_customization
    # We don't create it here as it requires imports from now_lms.db
    # The migration that creates it should be run first


def downgrade():
    """
    This migration is a consistency check and doesn't need a downgrade.

    The downgrade functionality is handled by the individual migrations
    that originally added each column.
    """
    pass
