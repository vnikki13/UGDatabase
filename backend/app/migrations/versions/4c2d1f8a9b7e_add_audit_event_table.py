"""add audit_event table

Revision ID: 4c2d1f8a9b7e
Revises: b7c9d1e2f3a4
Create Date: 2026-04-26 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "4c2d1f8a9b7e"
down_revision: Union[str, None] = "b7c9d1e2f3a4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "audit_event",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("occurred_at", sa.DateTime(), nullable=False),
        sa.Column("request_id", sa.String(), nullable=True),
        sa.Column("actor_email", sa.String(), nullable=True),
        sa.Column("actor_source", sa.String(), nullable=False),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("entity_type", sa.String(), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("before_json", sa.JSON(), nullable=True),
        sa.Column("after_json", sa.JSON(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_audit_event_id"), "audit_event", ["id"], unique=False)
    op.create_index(
        op.f("ix_audit_event_occurred_at"),
        "audit_event",
        ["occurred_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_audit_event_request_id"),
        "audit_event",
        ["request_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_audit_event_actor_email"),
        "audit_event",
        ["actor_email"],
        unique=False,
    )
    op.create_index(
        op.f("ix_audit_event_action"), "audit_event", ["action"], unique=False
    )
    op.create_index(
        op.f("ix_audit_event_entity_type"),
        "audit_event",
        ["entity_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_audit_event_entity_id"),
        "audit_event",
        ["entity_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_audit_event_entity_id"), table_name="audit_event")
    op.drop_index(op.f("ix_audit_event_entity_type"), table_name="audit_event")
    op.drop_index(op.f("ix_audit_event_action"), table_name="audit_event")
    op.drop_index(op.f("ix_audit_event_actor_email"), table_name="audit_event")
    op.drop_index(op.f("ix_audit_event_request_id"), table_name="audit_event")
    op.drop_index(op.f("ix_audit_event_occurred_at"), table_name="audit_event")
    op.drop_index(op.f("ix_audit_event_id"), table_name="audit_event")
    op.drop_table("audit_event")
