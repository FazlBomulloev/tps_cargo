from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, field_validator

MAX_CUSTOM_PRICE = Decimal("1000000")


class IssuanceCreate(BaseModel):
    client_id: int
    parcel_ids: list[int]
    payment_method: str | None = None
    payment_status: str
    comment: str | None = None
    custom_prices: dict[int, Decimal] | None = None

    @field_validator("custom_prices")
    @classmethod
    def _validate_custom_prices(cls, value):
        if value is None:
            return value
        for parcel_id, amount in value.items():
            if amount < 0:
                raise ValueError(
                    f"custom_prices[{parcel_id}] не может быть отрицательным"
                )
            if amount >= MAX_CUSTOM_PRICE:
                raise ValueError(
                    f"custom_prices[{parcel_id}] превышает допустимый максимум"
                )
        return value


class IssuanceItemResponse(BaseModel):
    id: int
    parcel_id: int
    track_id: str | None = None
    weight_kg: Decimal
    volume_m3: Decimal | None = None
    delivery_method: str
    tariff_applied: Decimal
    custom_price: Decimal | None = None
    amount: Decimal

    model_config = {"from_attributes": True}


class IssuanceResponse(BaseModel):
    id: int
    client_id: int
    client_name: str | None = None
    tps_code: str | None = None
    staff_id: int
    total_weight: Decimal
    total_amount: Decimal
    payment_status: str
    payment_method: str | None = None
    comment: str | None = None
    issued_at: datetime
    items: list[IssuanceItemResponse] = []

    model_config = {"from_attributes": True}
