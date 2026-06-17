"""initial schema — full snapshot via Base.metadata.create_all

Revision ID: 0001
Revises:
Create Date: 2026-06-17 00:00:00.000000

History wiped (no production data to preserve). Single consolidated
migration that:
  1. Creates pg_trgm extension.
  2. Runs Base.metadata.create_all() against the current models —
     guaranteed to match the SQLAlchemy schema 1:1, no hand-edited
     drift.
  3. Adds two index types autogenerate can't infer from models:
       - partial index ix_parcels_dushanbe_notified_pending
       - GIN gin_trgm_ops indexes on clients (full_name, phone, tps_code)
"""
from typing import Sequence, Union

from alembic import op

from app.database import Base
import app.models  # noqa: F401  — registers every model on Base.metadata


revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    Base.metadata.create_all(bind)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_parcels_dushanbe_notified_pending "
        "ON parcels_dushanbe (notified_at) "
        "WHERE notified_at IS NULL AND is_deleted = false"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_clients_full_name_trgm "
        "ON clients USING gin (full_name gin_trgm_ops)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_clients_phone_trgm "
        "ON clients USING gin (phone gin_trgm_ops)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_clients_tps_code_trgm "
        "ON clients USING gin (tps_code gin_trgm_ops)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_clients_tps_code_trgm")
    op.execute("DROP INDEX IF EXISTS ix_clients_phone_trgm")
    op.execute("DROP INDEX IF EXISTS ix_clients_full_name_trgm")
    op.execute("DROP INDEX IF EXISTS ix_parcels_dushanbe_notified_pending")
    bind = op.get_bind()
    Base.metadata.drop_all(bind)
