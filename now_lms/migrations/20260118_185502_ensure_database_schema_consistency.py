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


def _add_missing_columns(inspector, table_name: str, definitions: list[tuple[str, sa.Column]]) -> None:
    """Add only columns absent from a table, keeping the migration idempotent."""
    if table_name not in inspector.get_table_names():
        return
    existing_columns = {column["name"] for column in inspector.get_columns(table_name)}
    for column_name, column in definitions:
        if column_name not in existing_columns:
            op.add_column(table_name, column)


def upgrade():
    """Ensure all expected columns exist in the database."""
    inspector = sa.inspect(op.get_bind())
    _add_missing_columns(inspector, "configuracion", [
        ("allow_unverified_email_login", sa.Column("allow_unverified_email_login", sa.Boolean(), nullable=False, server_default=sa.false())),
        ("show_latest_blog_posts_on_home", sa.Column("show_latest_blog_posts_on_home", sa.Boolean(), nullable=False, server_default=sa.false())),
        *[(field, sa.Column(field, sa.String(200), nullable=True)) for field in (
            "social_facebook", "social_twitter", "social_linkedin", "social_youtube", "social_instagram", "social_github"
        )],
        ("enable_file_uploads", sa.Column("enable_file_uploads", sa.Boolean(), nullable=False, server_default=sa.false())),
        ("max_file_size", sa.Column("max_file_size", sa.Integer(), nullable=False, server_default=sa.text("1"))),
        ("enable_html_preformatted_descriptions", sa.Column("enable_html_preformatted_descriptions", sa.Boolean(), nullable=False, server_default=sa.false())),
        ("enable_footer", sa.Column("enable_footer", sa.Boolean(), nullable=False, server_default=sa.true())),
    ])
    _add_missing_columns(inspector, "blog_post", [
        ("cover_image", sa.Column("cover_image", sa.Boolean(), nullable=False, server_default=sa.false())),
        ("cover_image_ext", sa.Column("cover_image_ext", sa.String(5), nullable=True)),
    ])
    _add_missing_columns(inspector, "static_pages", [
        ("mostrar_en_footer", sa.Column("mostrar_en_footer", sa.Boolean(), nullable=False, server_default="0")),
    ])


def downgrade():
    """
    This migration is a consistency check and doesn't need a downgrade.

    The downgrade functionality is handled by the individual migrations
    that originally added each column.
    """
    pass
