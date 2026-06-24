"""intake_groups + parcels_dushanbe.intake_group_id

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-24 12:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "intake_groups",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("client_id", sa.Integer(), sa.ForeignKey("clients.id"), nullable=False),
        sa.Column("delivery_method", sa.String(length=20), nullable=False),
        sa.Column("weight_kg", sa.Numeric(10, 3), nullable=True),
        sa.Column("volume_m3", sa.Numeric(10, 4), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("shelf", sa.String(length=20), nullable=True),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("staff_users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.add_column(
        "parcels_dushanbe",
        sa.Column(
            "intake_group_id",
            sa.Integer(),
            sa.ForeignKey("intake_groups.id"),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_parcels_dushanbe_intake_group_id",
        "parcels_dushanbe",
        ["intake_group_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_parcels_dushanbe_intake_group_id", table_name="parcels_dushanbe")
    op.drop_column("parcels_dushanbe", "intake_group_id")
    op.drop_table("intake_groups")
