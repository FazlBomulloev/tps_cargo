"""unresolved_parcels.shelf

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-24 14:30:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "unresolved_parcels",
        sa.Column("shelf", sa.String(length=20), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("unresolved_parcels", "shelf")
