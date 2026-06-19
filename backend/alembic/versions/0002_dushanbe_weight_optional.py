"""parcels_dushanbe.weight_kg → nullable

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-19 10:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "parcels_dushanbe", "weight_kg",
        existing_type=sa.Numeric(10, 3),
        nullable=True,
    )


def downgrade() -> None:
    op.execute("UPDATE parcels_dushanbe SET weight_kg = 0 WHERE weight_kg IS NULL")
    op.alter_column(
        "parcels_dushanbe", "weight_kg",
        existing_type=sa.Numeric(10, 3),
        nullable=False,
    )
