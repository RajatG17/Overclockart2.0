from sqlalchemy import Column, Integer, String, Float
from database import Base
from pydantic import BaseModel

# SQLAlchemy Models
class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(String)
    price = Column(Float, nullable=False)
    stock = Column(Integer, default=0, nullable=False)

# Pydantic Models
class ProductCreate(BaseModel):
    name: str
    description: str | None = None
    price: float
    stock: int = 0

class ProductResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    price: float
    stock: int

    class Config:
        from_attributes = True
