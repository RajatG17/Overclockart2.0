from sqlalchemy import Column, Integer, String, Float, JSON
from database import Base
from pydantic import BaseModel

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    product_id = Column(Integer, nullable=False)
    quantity = Column(Integer, nullable=False)
    status = Column(String, default="PENDING", nullable=False)

class OutboxEvent(Base):
    __tablename__ = "outbox_events"

    id = Column(Integer, primary_key=True, index=True)
    aggregate_type = Column(String, nullable=False)
    aggregate_id = Column(String, nullable=False)
    event_type = Column(String, nullable=False)
    payload = Column(JSON, nullable=False)
    status = Column(String, default="PENDING", nullable=False) # PENDING or PROCESSED

class OrderCreate(BaseModel):
    user_id: int
    product_id: int
    quantity: int

class OrderResponse(BaseModel):
    id: int
    user_id: int
    product_id: int
    quantity: int
    status: str

    class Config:
        from_attributes = True
