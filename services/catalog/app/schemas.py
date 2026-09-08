import uuid
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

class ProductCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    price: Decimal = Field(gt=0)
    initial_quantity: int = Field(ge=0)

class ProductResponse(BaseModel):
    id: uuid.UUID
    name: str
    price: Decimal

    model_config = ConfigDict(from_attributes=True)

class InventoryResponse(BaseModel):
    product_id: uuid.UUID
    available_quantity: int
    reserved_quantity: int

    model_config = ConfigDict(from_attributes=True)

class InventoryOperationRequest(BaseModel):
    quantity: int = Field(gt=0)

    