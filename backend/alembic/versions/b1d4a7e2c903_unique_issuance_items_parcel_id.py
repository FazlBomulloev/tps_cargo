"""unique constraint on issuance_items.parcel_id (BE-008 defense in depth)

Revision ID: b1d4a7e2c903
Revises: ff532c4506b0
Create Date: 2026-06-17 00:00:00.000000

Application-level fix (SELECT ... FOR UPDATE in create_issuance) prevents
the double-issuance race in the normal path. This constraint is the last
line of defense if the app ever runs without the lock or across multiple
processes without shared row locks.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'b1d4a7e2c903'
down_revision: Union[str, None] = 'ff532c4506b0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint(
        'uq_issuance_items_parcel_id',
        'issuance_items',
        ['parcel_id'],
    )


def downgrade() -> None:
    op.drop_constraint(
        'uq_issuance_items_parcel_id',
        'issuance_items',
        type_='unique',
    )
