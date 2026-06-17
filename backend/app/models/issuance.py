from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class IssuanceOrder(Base):
    __tablename__ = "issuance_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    client_id: Mapped[int] = mapped_column(Integer, ForeignKey("clients.id"), nullable=False)
    staff_id: Mapped[int] = mapped_column(Integer, ForeignKey("staff_users.id"), nullable=False)
    total_weight: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    payment_status: Mapped[str] = mapped_column(String(20), nullable=False)
    payment_method: Mapped[str | None] = mapped_column(String(20), nullable=True)
    comment: Mapped[str | None] = mapped_column(
        Text, nullable=True,
    )
    issued_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    client: Mapped["Client"] = relationship("Client", lazy="raise")
    items: Mapped[list["IssuanceItem"]] = relationship(
        "IssuanceItem", back_populates="order", lazy="raise",
    )

    __table_args__ = (
        Index("ix_issuance_orders_issued_at", "issued_at"),
        Index("ix_issuance_orders_client_id", "client_id"),
    )


class IssuanceItem(Base):
    __tablename__ = "issuance_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    issuance_order_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("issuance_orders.id"), nullable=False
    )
    # parcel_id references parcels_dushanbe only — china stock is not directly issued.
    parcel_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("parcels_dushanbe.id"), nullable=False
    )
    weight_kg: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    volume_m3: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    delivery_method: Mapped[str] = mapped_column(String(20), nullable=False)
    tariff_applied: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    custom_price: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    # IN-25: новый полный снапшот тарифа {"kg", "m3", "currency"}, см. parcel_dushanbe.tariff_snapshot_data.
    tariff_snapshot_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    order: Mapped["IssuanceOrder"] = relationship(
        "IssuanceOrder", back_populates="items", lazy="raise",
    )
    parcel: Mapped["ParcelDushanbe"] = relationship("ParcelDushanbe", lazy="raise")

    __table_args__ = (
        Index("ix_issuance_items_order_id", "issuance_order_id"),
    )
