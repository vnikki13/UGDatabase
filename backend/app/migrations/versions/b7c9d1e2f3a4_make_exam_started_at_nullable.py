"""Make exam started_at nullable

Revision ID: b7c9d1e2f3a4
Revises: a3f1b2c4d5e6
Create Date: 2026-04-25 00:00:01.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "b7c9d1e2f3a4"
down_revision: Union[str, None] = "a3f1b2c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "exam",
        "started_at",
        existing_type=postgresql.TIMESTAMP(),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "exam",
        "started_at",
        existing_type=postgresql.TIMESTAMP(),
        nullable=False,
    )
