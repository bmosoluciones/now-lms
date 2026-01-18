# Copyright 2025 BMO Soluciones, S.A.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Add cover image fields to blog_post table.

Revision ID: add_blog_cover_image
Revises: 20260109_205100
Create Date: 2026-01-10 03:55:05.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260110_035505"
down_revision = "20260109_205100"
branch_labels = None
depends_on = None


def upgrade():
    """Add cover_image and cover_image_ext columns to blog_post table."""
    # Check if columns already exist before adding them
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if "blog_post" in existing_tables:
        columns = [col["name"] for col in inspector.get_columns("blog_post")]

        if "cover_image" not in columns:
            # Add cover_image boolean column with default False for backward compatibility
            op.add_column(
                "blog_post",
                sa.Column("cover_image", sa.Boolean(), nullable=False, server_default=sa.false()),
            )

        if "cover_image_ext" not in columns:
            # Add cover_image_ext string column
            op.add_column("blog_post", sa.Column("cover_image_ext", sa.String(length=5), nullable=True))


def downgrade():
    """Remove cover_image columns from blog_post table."""
    # Check if columns exist before dropping them
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if "blog_post" in existing_tables:
        columns = [col["name"] for col in inspector.get_columns("blog_post")]

        if "cover_image_ext" in columns:
            op.drop_column("blog_post", "cover_image_ext")

        if "cover_image" in columns:
            op.drop_column("blog_post", "cover_image")
