from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ParcelChina(Base):
    __tablename__ = "parcels_china"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    track_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    warehouse_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("warehouses.id"), nullable=True
    )
    created_by: Mapped[int] = mapped_column(Integer, ForeignKey("staff_users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    is_deleted: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    deleted_by: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("staff_users.id"), nullable=True
    )

    __table_args__ = (
        Index("ix_parcels_china_track_id", "track_id", unique=True),
        Index("ix_parcels_china_created_at", "created_at"),
    )
