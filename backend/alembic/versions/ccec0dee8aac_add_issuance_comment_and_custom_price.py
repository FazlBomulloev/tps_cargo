"""add issuance comment and custom_price (no-op, kept for chain integrity)

Revision ID: ccec0dee8aac
Revises: 7488a0137a83
Create Date: 2026-06-12 15:14:09.535875

Originally added `issuance_orders.comment` and `issuance_items.custom_price`,
but the rewritten initial schema (7488a0137a83) already includes both
columns. This migration is now a no-op; it stays in the chain so existing
prod databases that already have it stamped don't break.
"""
from typing import Sequence, Union


revision: str = "ccec0dee8aac"
down_revision: Union[str, None] = "7488a0137a83"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
