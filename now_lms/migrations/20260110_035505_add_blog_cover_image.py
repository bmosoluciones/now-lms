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
Revises:
Create Date: 2026-01-10 03:55:05.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "add_blog_cover_image"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Add cover_image and cover_image_ext columns to blog_post table."""
    # Add cover_image boolean column with default False
    op.add_column("blog_post", sa.Column("cover_image", sa.Boolean(), nullable=True))
    # Set default value for existing rows
    op.execute("UPDATE blog_post SET cover_image = 0 WHERE cover_image IS NULL")
    # Make column not nullable
    op.alter_column("blog_post", "cover_image", nullable=False, server_default="0")

    # Add cover_image_ext string column
    op.add_column("blog_post", sa.Column("cover_image_ext", sa.String(length=5), nullable=True))


def downgrade():
    """Remove cover_image columns from blog_post table."""
    op.drop_column("blog_post", "cover_image_ext")
    op.drop_column("blog_post", "cover_image")
