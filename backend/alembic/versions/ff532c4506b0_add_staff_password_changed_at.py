"""add staff_users.password_changed_at — no-op (already in initial)

Revision ID: ff532c4506b0
Revises: ccec0dee8aac
Create Date: 2026-06-17 00:00:00.000000

Rewritten initial schema (7488a0137a83) already includes
staff_users.password_changed_at. Kept in the chain so existing
deployments that were already stamped at this revision don't break.
"""
from typing import Sequence, Union


revision: str = "ff532c4506b0"
down_revision: Union[str, None] = "ccec0dee8aac"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
