"""performance indexes, expense soft-delete, pg_trgm, tariff snapshot jsonb (Phase 5)

Revision ID: d4f1c9a7b2e6
Revises: b1d4a7e2c903
Create Date: 2026-06-17 00:00:00.000000

IN-021/22, BO-25: indexes on FK / created_at columns that were full-scanned
by reports (expenses, issuance_orders, issuance_items, audit_logs,
notification_logs) + a partial index for unsent dushanbe notifications.

BE-32: soft-delete columns for expenses.

BE-24: pg_trgm GIN indexes for ilike search on clients.

IN-25: tariff_snapshot_data JSONB columns (parcels_dushanbe, issuance_items)
to carry {kg, m3, currency} alongside the legacy price_per_kg-only column.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = 'd4f1c9a7b2e6'
down_revision: Union[str, None] = 'b1d4a7e2c903'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── IN-021/22, BO-25: индексы на горячих таблицах ──
    op.create_index('ix_expenses_created_at', 'expenses', ['created_at'])
    op.create_index('ix_expenses_category', 'expenses', ['category'])
    op.create_index('ix_issuance_orders_issued_at', 'issuance_orders', ['issued_at'])
    op.create_index('ix_issuance_orders_client_id', 'issuance_orders', ['client_id'])
    op.create_index('ix_issuance_items_order_id', 'issuance_items', ['issuance_order_id'])
    op.create_index('ix_audit_logs_staff_id', 'audit_logs', ['staff_id'])
    op.create_index('ix_audit_logs_created_at', 'audit_logs', ['created_at'])
    op.create_index('ix_audit_logs_entity', 'audit_logs', ['entity_type', 'entity_id'])
    op.create_index('ix_notification_logs_client_id', 'notification_logs', ['client_id'])
    op.create_index('ix_notification_logs_sent_at', 'notification_logs', ['sent_at'])

    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_parcels_dushanbe_notified_pending "
        "ON parcels_dushanbe(notified_at) "
        "WHERE notified_at IS NULL AND is_deleted = false"
    )

    # ── BE-32: soft-delete для Expense ──
    op.add_column('expenses', sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.add_column('expenses', sa.Column('deleted_at', sa.DateTime(), nullable=True))
    op.add_column('expenses', sa.Column('deleted_by', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_expenses_deleted_by', 'expenses', 'staff_users', ['deleted_by'], ['id'])

    # ── BE-24: pg_trgm для поиска клиентов ──
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute("CREATE INDEX IF NOT EXISTS ix_clients_full_name_trgm ON clients USING gin (full_name gin_trgm_ops)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_clients_phone_trgm ON clients USING gin (phone gin_trgm_ops)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_clients_tps_code_trgm ON clients USING gin (tps_code gin_trgm_ops)")

    # ── IN-25: tariff_snapshot_data JSONB ──
    op.add_column('parcels_dushanbe', sa.Column('tariff_snapshot_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('issuance_items', sa.Column('tariff_snapshot_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    op.drop_column('issuance_items', 'tariff_snapshot_data')
    op.drop_column('parcels_dushanbe', 'tariff_snapshot_data')

    op.execute("DROP INDEX IF EXISTS ix_clients_tps_code_trgm")
    op.execute("DROP INDEX IF EXISTS ix_clients_phone_trgm")
    op.execute("DROP INDEX IF EXISTS ix_clients_full_name_trgm")
    # Extension не дропаем — могут зависеть другие объекты.

    op.drop_constraint('fk_expenses_deleted_by', 'expenses', type_='foreignkey')
    op.drop_column('expenses', 'deleted_by')
    op.drop_column('expenses', 'deleted_at')
    op.drop_column('expenses', 'is_deleted')

    op.execute("DROP INDEX IF EXISTS ix_parcels_dushanbe_notified_pending")

    op.drop_index('ix_notification_logs_sent_at', table_name='notification_logs')
    op.drop_index('ix_notification_logs_client_id', table_name='notification_logs')
    op.drop_index('ix_audit_logs_entity', table_name='audit_logs')
    op.drop_index('ix_audit_logs_created_at', table_name='audit_logs')
    op.drop_index('ix_audit_logs_staff_id', table_name='audit_logs')
    op.drop_index('ix_issuance_items_order_id', table_name='issuance_items')
    op.drop_index('ix_issuance_orders_client_id', table_name='issuance_orders')
    op.drop_index('ix_issuance_orders_issued_at', table_name='issuance_orders')
    op.drop_index('ix_expenses_category', table_name='expenses')
    op.drop_index('ix_expenses_created_at', table_name='expenses')
