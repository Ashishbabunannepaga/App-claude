"""ops review of low-confidence policy readings

Revision ID: 0006
Revises: 0005
Create Date: 2026-11-19 15:00:00

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("policies", sa.Column("review_outcome", sa.String(length=20), nullable=True))
    op.add_column("policies", sa.Column("review_note", sa.String(length=500), nullable=True))
    op.add_column("policies", sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_policies_reviewed_at", "policies", ["reviewed_at"])


def downgrade() -> None:
    op.drop_index("ix_policies_reviewed_at", table_name="policies")
    op.drop_column("policies", "reviewed_at")
    op.drop_column("policies", "review_note")
    op.drop_column("policies", "review_outcome")
