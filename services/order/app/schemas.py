import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from .models import OrderStatus


class OrderItemCreateRequest(BaseModel):
    product_id: uuid.UUID
    quantity: int = Field(gt=0)
    unit_price: Decimal = Field(gt=0)

class OrderCreateRequest(BaseModel):
    user_id: uuid.UUID
    items: list[OrderItemCreateRequest] = Field(
        min_length=1
    )

class OrderItemResponse(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    quantity: int
    unit_price: Decimal

    model_config = ConfigDict(
        from_attributes=True
    )

class OrderResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    status: OrderStatus
    total: Decimal
    created_at: datetime
    updated_at: datetime
    items: list[OrderItemResponse]

    model_config = ConfigDict(
        from_attributes=True
    )


