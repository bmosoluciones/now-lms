"""Add prior_credentials table

Revision ID: 20260731_120500
Revises: 20260726_000000
Create Date: 2026-07-31 12:05:00

Adds the table backing learner-reported prior credentials — certificates earned
elsewhere, recorded with a verification URL and an optional image attachment.

The table is created only when absent. A fresh install builds the full current-model
schema with `database.create_all()` and then stamps the migration head, so this
revision must be a no-op there and do real work only on an existing database.
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260731_120500"
down_revision = "20260726_000000"
branch_labels = None
depends_on = None


def upgrade():
    """Create the prior_credentials table if it does not already exist."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if "prior_credentials" in inspector.get_table_names():
        return

    op.create_table(
        "prior_credentials",
        sa.Column("id", sa.String(26), nullable=False, index=True),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("creado", sa.Date(), nullable=False),
        sa.Column("creado_por", sa.String(150), nullable=True),
        sa.Column("modificado", sa.DateTime(), nullable=True),
        sa.Column("modificado_por", sa.String(150), nullable=True),
        sa.Column("usuario", sa.String(150), nullable=False, index=True),
        sa.Column("credential_key", sa.String(50), nullable=False, index=True),
        sa.Column("credential_name", sa.String(150), nullable=False),
        sa.Column("credential_id", sa.String(100), nullable=True),
        sa.Column("verification_url", sa.String(500), nullable=False),
        sa.Column("issued_on", sa.Date(), nullable=True),
        sa.Column("image_file", sa.String(200), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, index=True),
        sa.Column("admin_notes", sa.Text(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("reviewed_by", sa.String(150), nullable=True),
        sa.ForeignKeyConstraint(["usuario"], ["usuario.usuario"]),
        sa.ForeignKeyConstraint(["reviewed_by"], ["usuario.usuario"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("usuario", "credential_key", name="prior_credential_unico_por_usuario"),
    )


def downgrade():
    """Drop the prior_credentials table."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if "prior_credentials" in inspector.get_table_names():
        op.drop_table("prior_credentials")
