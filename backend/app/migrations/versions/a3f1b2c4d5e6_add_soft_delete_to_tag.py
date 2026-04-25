"""Add timestamps and soft delete to tag

Revision ID: a3f1b2c4d5e6
Revises: f3a7d2b891cc
Create Date: 2026-04-25 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a3f1b2c4d5e6"
down_revision: Union[str, None] = "f3a7d2b891cc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "tag",
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
    )
    op.add_column("tag", sa.Column("updated_at", sa.DateTime(), nullable=True))
    op.add_column("tag", sa.Column("deleted_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("tag", "deleted_at")
    op.drop_column("tag", "updated_at")
    op.drop_column("tag", "created_at")
