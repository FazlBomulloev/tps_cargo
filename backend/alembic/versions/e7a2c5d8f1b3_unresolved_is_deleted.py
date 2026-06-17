"""BE-31: add is_deleted to unresolved_parcels (separate from resolved)

Revision ID: e7a2c5d8f1b3
Revises: d4f1c9a7b2e6
Create Date: 2026-06-17 00:00:00.000000

resolved=True meant "linked to a client parcel". Deleting an unresolved
item used to also set resolved=True, conflating the two states. This adds
a dedicated is_deleted flag.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'e7a2c5d8f1b3'
down_revision: Union[str, None] = 'd4f1c9a7b2e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'unresolved_parcels',
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')),
    )


def downgrade() -> None:
    op.drop_column('unresolved_parcels', 'is_deleted')
