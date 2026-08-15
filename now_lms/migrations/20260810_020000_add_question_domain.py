"""Add domain_key and domain_name to question

Revision ID: 20260810_020000
Revises: 20260809_010000
Create Date: 2026-08-10 00:00:00

Records which part of the syllabus each question examines, so a result can be
scored per domain and a bank can be drilled one domain at a time. Both columns
are nullable: every question that already exists has no domain, and a question
authored by hand in the instructor UI still does not need one.

The columns are added only when absent. A fresh install builds the full
current-model schema with `database.create_all()` and then stamps the migration
head, so this revision must be a no-op there and do real work only on a database
that ran the earlier history.

The index is created here rather than left to the model, because a model's
`index=True` only takes effect through `create_all()` — on an existing database
nothing would build it, and grouping a result by domain is the whole point.
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20260810_020000"
down_revision = "20260809_010000"
branch_labels = None
depends_on = None

TABLE = "question"
INDEX_NAME = "ix_question_domain_key"


def _column_names(inspector) -> set:
    return {column["name"] for column in inspector.get_columns(TABLE)}


def _index_names(inspector) -> set:
    return {index["name"] for index in inspector.get_indexes(TABLE)}


def upgrade():
    """Add the two domain columns and the index used to group by them."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if TABLE not in inspector.get_table_names():
        return

    existing = _column_names(inspector)

    if "domain_key" not in existing:
        op.add_column(TABLE, sa.Column("domain_key", sa.String(50), nullable=True))
    if "domain_name" not in existing:
        op.add_column(TABLE, sa.Column("domain_name", sa.String(150), nullable=True))

    # Re-inspect: the index can only be built once the column exists.
    inspector = sa.inspect(conn)
    if "domain_key" in _column_names(inspector) and INDEX_NAME not in _index_names(inspector):
        op.create_index(INDEX_NAME, TABLE, ["domain_key"])


def downgrade():
    """Drop the index and both columns."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if TABLE not in inspector.get_table_names():
        return

    if INDEX_NAME in _index_names(inspector):
        op.drop_index(INDEX_NAME, table_name=TABLE)

    existing = _column_names(inspector)
    if "domain_name" in existing:
        op.drop_column(TABLE, "domain_name")
    if "domain_key" in existing:
        op.drop_column(TABLE, "domain_key")
