"""Add missing tables from previous commit

Revision ID: 20260109_152634
Revises: 20260105_145517
Create Date: 2026-01-09 15:26:34

This migration adds tables that were introduced in a previous commit
but were not migrated: CourseLibrary, UserEvent, StaticPage, ContactMessage.

These tables were added to the database models but the migration was
accidentally omitted.
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260109_152634"
down_revision = "20260105_145517"
branch_labels = None
depends_on = None


def upgrade():
    """Add missing tables."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    # Create course_library table if it doesn't exist
    if "course_library" not in existing_tables:
        op.create_table(
            "course_library",
            sa.Column("id", sa.String(26), nullable=False, index=True),
            sa.Column("timestamp", sa.DateTime(), nullable=False),
            sa.Column("creado", sa.Date(), nullable=False),
            sa.Column("creado_por", sa.String(150), nullable=True),
            sa.Column("modificado", sa.DateTime(), nullable=True),
            sa.Column("modificado_por", sa.String(150), nullable=True),
            sa.Column("curso", sa.String(20), nullable=False, index=True),
            sa.Column("filename", sa.String(255), nullable=False, index=True),
            sa.Column("original_filename", sa.String(255), nullable=False),
            sa.Column("nombre", sa.String(255), nullable=False),
            sa.Column("descripcion", sa.String(1000), nullable=False),
            sa.Column("file_size", sa.Integer(), nullable=False),
            sa.Column("mime_type", sa.String(100), nullable=True),
            sa.ForeignKeyConstraint(["curso"], ["curso.codigo"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("curso", "filename", name="course_library_unique_file"),
        )

    # Create user_events table if it doesn't exist
    if "user_events" not in existing_tables:
        op.create_table(
            "user_events",
            sa.Column("id", sa.String(26), nullable=False, index=True),
            sa.Column("timestamp", sa.DateTime(), nullable=False),
            sa.Column("creado", sa.Date(), nullable=False),
            sa.Column("creado_por", sa.String(150), nullable=True),
            sa.Column("modificado", sa.DateTime(), nullable=True),
            sa.Column("modificado_por", sa.String(150), nullable=True),
            sa.Column("user_id", sa.String(150), nullable=False, index=True),
            sa.Column("course_id", sa.String(20), nullable=False, index=True),
            sa.Column("section_id", sa.String(26), nullable=True, index=True),
            sa.Column("resource_id", sa.String(26), nullable=True, index=True),
            sa.Column("evaluation_id", sa.String(26), nullable=True, index=True),
            sa.Column("resource_type", sa.String(20), nullable=False, index=True),
            sa.Column("title", sa.String(255), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("start_time", sa.DateTime(), nullable=False, index=True),
            sa.Column("end_time", sa.DateTime(), nullable=True),
            sa.Column("timezone", sa.String(50), nullable=True),
            sa.Column("status", sa.String(20), nullable=False, index=True, server_default="pending"),
            sa.ForeignKeyConstraint(["user_id"], ["usuario.usuario"]),
            sa.ForeignKeyConstraint(["course_id"], ["curso.codigo"]),
            sa.ForeignKeyConstraint(["section_id"], ["curso_seccion.id"]),
            sa.ForeignKeyConstraint(["resource_id"], ["curso_recurso.id"]),
            sa.ForeignKeyConstraint(["evaluation_id"], ["evaluation.id"]),
            sa.PrimaryKeyConstraint("id"),
        )

    # Create static_pages table if it doesn't exist
    if "static_pages" not in existing_tables:
        op.create_table(
            "static_pages",
            sa.Column("id", sa.String(26), nullable=False, index=True),
            sa.Column("timestamp", sa.DateTime(), nullable=False),
            sa.Column("creado", sa.Date(), nullable=False),
            sa.Column("creado_por", sa.String(150), nullable=True),
            sa.Column("modificado", sa.DateTime(), nullable=True),
            sa.Column("modificado_por", sa.String(150), nullable=True),
            sa.Column("slug", sa.String(50), nullable=False, unique=True, index=True),
            sa.Column("title", sa.String(200), nullable=False),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.PrimaryKeyConstraint("id"),
        )

    # Create contact_messages table if it doesn't exist
    if "contact_messages" not in existing_tables:
        op.create_table(
            "contact_messages",
            sa.Column("id", sa.String(26), nullable=False, index=True),
            sa.Column("timestamp", sa.DateTime(), nullable=False),
            sa.Column("creado", sa.Date(), nullable=False),
            sa.Column("creado_por", sa.String(150), nullable=True),
            sa.Column("modificado", sa.DateTime(), nullable=True),
            sa.Column("modificado_por", sa.String(150), nullable=True),
            sa.Column("name", sa.String(150), nullable=False),
            sa.Column("email", sa.String(150), nullable=False),
            sa.Column("subject", sa.String(200), nullable=False),
            sa.Column("message", sa.Text(), nullable=False),
            sa.Column("status", sa.String(20), nullable=False, index=True, server_default="not_seen"),
            sa.Column("admin_notes", sa.Text(), nullable=True),
            sa.Column("answered_at", sa.DateTime(), nullable=True),
            sa.Column("answered_by", sa.String(150), nullable=True),
            sa.ForeignKeyConstraint(["answered_by"], ["usuario.usuario"]),
            sa.PrimaryKeyConstraint("id"),
        )


def downgrade():
    """Remove missing tables."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    # Drop tables in reverse order due to foreign key dependencies
    if "contact_messages" in existing_tables:
        op.drop_table("contact_messages")

    if "static_pages" in existing_tables:
        op.drop_table("static_pages")

    if "user_events" in existing_tables:
        op.drop_table("user_events")

    if "course_library" in existing_tables:
        op.drop_table("course_library")
