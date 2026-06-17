"""add staff_users.password_changed_at (JWT revocation support, BE-006)

Revision ID: ff532c4506b0
Revises: ccec0dee8aac
Create Date: 2026-06-17 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'ff532c4506b0'
down_revision: Union[str, None] = 'ccec0dee8aac'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'staff_users',
        sa.Column(
            'password_changed_at',
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_column('staff_users', 'password_changed_at')
