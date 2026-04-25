"""Remove media_storage_path from question table

Revision ID: f3a7d2b891cc
Revises: e61962afe482
Create Date: 2026-04-25 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes

# revision identifiers, used by Alembic.
revision: str = "f3a7d2b891cc"
down_revision: Union[str, None] = "e61962afe482"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("question", "media_storage_path")


def downgrade() -> None:
    op.add_column(
        "question",
        sa.Column(
            "media_storage_path", sqlmodel.sql.sqltypes.AutoString(), nullable=True
        ),
    )
