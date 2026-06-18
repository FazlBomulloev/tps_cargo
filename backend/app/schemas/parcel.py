from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, model_validator


class ParcelChinaCreate(BaseModel):
    track_id: str


class ParcelChinaBulk(BaseModel):
    track_ids: list[str]


class ParcelChinaResponse(BaseModel):
    id: int
    track_id: str
    warehouse_id: int | None = None
    created_by: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ParcelDushanbeCreate(BaseModel):
    track_id: str
    tps_code: str | None = None
    weight_kg: Decimal
    volume_m3: Decimal | None = None
    delivery_method: str
    comment: str | None = None
    shelf: str | None = None

    @model_validator(mode="after")
    def _validate_truck_volume(self):
        # truck без volume_m3 → недосчёт денег в max(byKg, byM3).
        if self.delivery_method == "truck" and (
            self.volume_m3 is None or self.volume_m3 <= 0
        ):
            raise ValueError(
                "volume_m3 обязателен и должен быть > 0 для delivery_method='truck'"
            )
        return self


class ParcelDushanbeBulk(BaseModel):
    """Групповая приёмка в Душанбе: один клиент (TPS) и общие
    вес/метод доставки на всю партию треков."""

    tps_code: str | None = None
    track_ids: list[str]
    weight_kg: Decimal
    delivery_method: str
    volume_m3: Decimal | None = None
    comment: str | None = None
    shelf: str | None = None

    @model_validator(mode="after")
    def _validate_truck_volume(self):
        if self.delivery_method == "truck" and (
            self.volume_m3 is None or self.volume_m3 <= 0
        ):
            raise ValueError(
                "volume_m3 обязателен и должен быть > 0 для delivery_method='truck'"
            )
        return self


class ParcelDushanbeResponse(BaseModel):
    id: int
    track_id: str
    client_id: int
    status: str
    weight_kg: Decimal
    volume_m3: Decimal | None = None
    delivery_method: str
    warehouse_id: int | None = None
    amount_due: Decimal | None = None
    tariff_snapshot: Decimal | None = None
    has_china_registration: bool
    comment: str | None = None
    notified_at: datetime | None = None
    created_by: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MyParcelResponse(BaseModel):
    """Расширенная карточка посылки для клиента (бот /my).

    Поля заполняются по мере прохождения этапов; пустые
    (None) бот не отображает.
    """

    track_id: str
    status: str
    # Дата принятия в Китае (parcels_china.created_at).
    china_at: datetime | None = None
    # Дата прибытия в Душанбе (parcels_dushanbe.created_at).
    arrived_at: datetime
    weight_kg: Decimal | None = None
    amount_due: Decimal | None = None
    # Дата выдачи (issuance_orders.issued_at).
    issued_at: datetime | None = None
    # Полка на складе в Душанбе.
    shelf: str | None = None


class ParcelStatusUpdate(BaseModel):
    status: str


class ParcelUpdate(BaseModel):
    weight_kg: Decimal | None = None
    volume_m3: Decimal | None = None
    delivery_method: str | None = None
    comment: str | None = None
    status: str | None = None
