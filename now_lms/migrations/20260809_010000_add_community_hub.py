"""Add the Community Hub tables

Revision ID: 20260809_010000
Revises: 20260810_000000
Create Date: 2026-08-09 01:00:00

Three tables backing the Community Hub (ADR-10, 000-docs/017-AT-ADEC, which
supersedes ADR-8): posts and replies, reactions, and the append-only moderation
trail. The Hub owns its own content, so nothing here references ``foro_mensaje``
and the native course forums are untouched.

A fresh install builds the full current-model schema with ``database.create_all()``
and then stamps the migration head, so this revision must be a no-op there and do
real work only on an existing database.
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260809_010000"
down_revision = "20260810_000000"
branch_labels = None
depends_on = None

AUDIT_COLUMNS = (
    ("id", sa.String(26), {"nullable": False, "index": True}),
    ("timestamp", sa.DateTime(), {"nullable": False}),
    ("creado", sa.Date(), {"nullable": False}),
    ("creado_por", sa.String(150), {"nullable": True}),
    ("modificado", sa.DateTime(), {"nullable": True}),
    ("modificado_por", sa.String(150), {"nullable": True}),
)


def _audit():
    return [sa.Column(name, type_, **kwargs) for name, type_, kwargs in AUDIT_COLUMNS]


def upgrade():
    """Create the three Community Hub tables, each only when absent."""
    conn = op.get_bind()
    existing = set(sa.inspect(conn).get_table_names())

    if "comunidad_publicacion" not in existing:
        op.create_table(
            "comunidad_publicacion",
            *_audit(),
            # Self-referential: NULL parent is a root post, non-NULL is a reply.
            sa.Column("parent_id", sa.String(26), nullable=True, index=True),
            sa.Column("usuario", sa.String(150), nullable=False, index=True),
            sa.Column("contenido", sa.Text(), nullable=False),
            sa.Column("fecha_creacion", sa.DateTime(), nullable=False, index=True),
            # Root-post fields, NULL on replies.
            sa.Column("titulo", sa.String(160), nullable=True),
            sa.Column("tipo", sa.String(20), nullable=True, index=True),
            sa.Column("enlace_build", sa.String(500), nullable=True),
            sa.Column("fijado", sa.Boolean(), nullable=False),
            sa.Column("estado_moderacion", sa.String(20), nullable=False, index=True),
            sa.Column("estado", sa.String(20), nullable=False),
            sa.Column("reportes_abiertos", sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(["parent_id"], ["comunidad_publicacion.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["usuario"], ["usuario.usuario"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "ix_comunidad_publicacion_tipo_estado", "comunidad_publicacion", ["tipo", "estado_moderacion"]
        )
        op.create_index(
            "ix_comunidad_publicacion_parent_fecha", "comunidad_publicacion", ["parent_id", "fecha_creacion"]
        )

    if "comunidad_reaccion" not in existing:
        op.create_table(
            "comunidad_reaccion",
            *_audit(),
            sa.Column("publicacion_id", sa.String(26), nullable=False, index=True),
            sa.Column("usuario", sa.String(150), nullable=False, index=True),
            sa.ForeignKeyConstraint(["publicacion_id"], ["comunidad_publicacion.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["usuario"], ["usuario.usuario"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            # The constraint the whole feature rests on: one member, one like.
            sa.UniqueConstraint("publicacion_id", "usuario", name="uq_comunidad_reaccion_una_por_miembro"),
        )

    if "comunidad_evento_moderacion" not in existing:
        op.create_table(
            "comunidad_evento_moderacion",
            *_audit(),
            sa.Column("publicacion_id", sa.String(26), nullable=False, index=True),
            sa.Column("tipo", sa.String(20), nullable=False),
            sa.Column("actor", sa.String(150), nullable=False, index=True),
            sa.Column("motivo", sa.String(500), nullable=True),
            sa.Column("ocurrido_en", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["publicacion_id"], ["comunidad_publicacion.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["actor"], ["usuario.usuario"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "ix_comunidad_evento_publicacion_fecha", "comunidad_evento_moderacion", ["publicacion_id", "ocurrido_en"]
        )


def downgrade():
    """Drop the three tables. Nothing outside the Hub is touched."""
    conn = op.get_bind()
    existing = set(sa.inspect(conn).get_table_names())

    if "comunidad_evento_moderacion" in existing:
        op.drop_index("ix_comunidad_evento_publicacion_fecha", table_name="comunidad_evento_moderacion")
        op.drop_table("comunidad_evento_moderacion")
    if "comunidad_reaccion" in existing:
        op.drop_table("comunidad_reaccion")
    if "comunidad_publicacion" in existing:
        op.drop_index("ix_comunidad_publicacion_parent_fecha", table_name="comunidad_publicacion")
        op.drop_index("ix_comunidad_publicacion_tipo_estado", table_name="comunidad_publicacion")
        op.drop_table("comunidad_publicacion")
