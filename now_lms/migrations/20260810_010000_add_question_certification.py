"""Add certification_key and certification_name to question

Revision ID: 20260810_010000
Revises: 20260810_020000
Create Date: 2026-08-10 01:00:00

Records which certification each question prepares for, so practice can be
organised by credential rather than by course. A single course carries questions
for more than one certification — CCA-F's sections hold both Architect
Foundations and Architect Professional material — so the course is the wrong key
for a practice surface. Both columns are nullable for the same reason the domain
columns are.

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
revision = "20260810_010000"
down_revision = "20260810_020000"
branch_labels = None
depends_on = None

TABLE = "question"
INDEX_NAME = "ix_question_certification_key"


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

    if "certification_key" not in existing:
        op.add_column(TABLE, sa.Column("certification_key", sa.String(50), nullable=True))
    if "certification_name" not in existing:
        op.add_column(TABLE, sa.Column("certification_name", sa.String(150), nullable=True))

    # Re-inspect: the index can only be built once the column exists.
    inspector = sa.inspect(conn)
    if "certification_key" in _column_names(inspector) and INDEX_NAME not in _index_names(inspector):
        op.create_index(INDEX_NAME, TABLE, ["certification_key"])


def downgrade():
    """Drop the index and both columns."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if TABLE not in inspector.get_table_names():
        return

    if INDEX_NAME in _index_names(inspector):
        op.drop_index(INDEX_NAME, table_name=TABLE)

    existing = _column_names(inspector)
    if "certification_name" in existing:
        op.drop_column(TABLE, "certification_name")
    if "certification_key" in existing:
        op.drop_column(TABLE, "certification_key")
