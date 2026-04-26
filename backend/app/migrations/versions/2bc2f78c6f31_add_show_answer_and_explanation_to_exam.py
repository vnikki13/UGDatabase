"""Add tutor to exam

Revision ID: 2bc2f78c6f31
Revises: 5274e0efe28c
Create Date: 2026-04-26 12:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "2bc2f78c6f31"
down_revision: Union[str, None] = "5274e0efe28c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "exam",
        sa.Column(
            "tutor",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.alter_column("exam", "tutor", server_default=None)


def downgrade() -> None:
    op.drop_column("exam", "tutor")
