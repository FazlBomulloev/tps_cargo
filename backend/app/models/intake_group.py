from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class IntakeGroup(Base):
    """Партия, добавленная одной групповой приёмкой на складе Душанбе.

    Хранит общий вес/объём партии. У каждой ParcelDushanbe одной партии
    указывается intake_group_id; weight_kg посылки = group.weight_kg / count,
    чтобы суммы математически сходились в статистике и при выдаче.
    """

    __tablename__ = "intake_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    client_id: Mapped[int] = mapped_column(Integer, ForeignKey("clients.id"), nullable=False)
    delivery_method: Mapped[str] = mapped_column(String(20), nullable=False)
    weight_kg: Mapped[Decimal | None] = mapped_column(Numeric(10, 3), nullable=True)
    volume_m3: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    shelf: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_by: Mapped[int] = mapped_column(Integer, ForeignKey("staff_users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
