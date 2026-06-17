from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class ExpenseCreate(BaseModel):
    amount: Decimal = Field(gt=0)
    category: str
    comment: str | None = None


class ExpenseResponse(BaseModel):
    id: int
    amount: Decimal
    category: str
    comment: str | None = None
    created_by: int
    created_by_name: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
