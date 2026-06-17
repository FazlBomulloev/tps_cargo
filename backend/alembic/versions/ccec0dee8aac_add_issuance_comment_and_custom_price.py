"""add issuance_items.custom_price (comment column already in initial)

Revision ID: ccec0dee8aac
Revises: 7488a0137a83
Create Date: 2026-06-12 15:14:09.535875

Originally added both `issuance_orders.comment` and
`issuance_items.custom_price`. The rewritten initial schema
(7488a0137a83) already includes `comment`, so only `custom_price`
needs adding here.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "ccec0dee8aac"
down_revision: Union[str, None] = "7488a0137a83"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "issuance_items",
        sa.Column("custom_price", sa.Numeric(precision=10, scale=2), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("issuance_items", "custom_price")
