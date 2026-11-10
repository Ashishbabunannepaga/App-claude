"""contact consent for CapitUp's team (leads)

Revision ID: 0005
Revises: 0004
Create Date: 2026-11-10 23:00:00

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("contact_consent_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("contact_consent_version", sa.String(length=20), nullable=True))
    op.add_column("users", sa.Column("contact_consent_withdrawn_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_users_contact_consent_at", "users", ["contact_consent_at"])
    op.create_index("ix_users_contact_consent_withdrawn_at", "users", ["contact_consent_withdrawn_at"])


def downgrade() -> None:
    op.drop_index("ix_users_contact_consent_withdrawn_at", table_name="users")
    op.drop_index("ix_users_contact_consent_at", table_name="users")
    op.drop_column("users", "contact_consent_withdrawn_at")
    op.drop_column("users", "contact_consent_version")
    op.drop_column("users", "contact_consent_at")
