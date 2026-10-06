"""reward events (coin ledger)

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-06 10:00:00

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "reward_events",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("kind", sa.String(length=30), nullable=False),
        sa.Column("ref", sa.String(length=64), nullable=False),
        sa.Column("coins", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "kind", "ref", name="uq_reward_event"),
    )
    op.create_index(op.f("ix_reward_events_user_id"), "reward_events", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_reward_events_user_id"), table_name="reward_events")
    op.drop_table("reward_events")
